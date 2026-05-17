# 赛博小镇 - FastAPI 后端

基于 [hello-agents](https://pypi.org/project/hello-agents/)（PyPI）的 AI NPC 对话、记忆、好感度、情绪与批量头顶台词服务。

## 功能特性

| 模块 | 说明 |
|------|------|
| **NPC YAML 配置** | `npc_config/npcs.yaml`：人格、初始记忆、情绪/好感基线、环境台词 |
| 实时对话 | `POST /chat`，注入记忆 + 好感 + 情绪上下文 |
| 批量头顶台词 | 每 30s 按场景 `office`/`cafe`/`library` 各调一次 LLM（或 YAML 预设） |
| 记忆 | 工作记忆 + 可选情景记忆（Qdrant）；支持 YAML 初始记忆种子 |
| 好感度 | LLM 分析，5 级关系，内存存储；首次见面默认来自 YAML `baselines.affinity` |
| 情绪 | 与好感同次分析，5 种情绪，内存存储；首次默认来自 YAML `baselines.emotion` |
| 对话历史 | 从记忆整理 `dialogue-history` |
| 日志 | `logger.py` → `logs/dialogue_*.log` |

### NPC（5 人）

| scene_id | 角色 |
|----------|------|
| `office` | 程码、林案、苏绘 |
| `cafe` | 小林 |
| `library` | 陈读 |

## 安装

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt   # 含 hello-agents，无需本地框架源码
copy .env.example .env   # 配置 LLM_API_KEY 等
```

## 启动

```bash
python main.py
# 或 Windows: .\start.ps1
```

- API：http://localhost:8000  
- 文档：http://localhost:8000/docs  

无 `LLM_API_KEY` 时仍可启动，对话与批量台词使用降级逻辑。

## 测试

```bash
python -m pytest tests/ -v
```

| 文件 | 内容 |
|------|------|
| `tests/test_emotion_manager.py` | EmotionManager 单元测试 |
| `tests/test_emotion_api.py` | 情绪与 chat 路由（mock） |
| `tests/test_analyzer_parse.py` | 好感/情绪 JSON 解析 |
| `tests/test_npc_config_loader.py` | YAML 加载、基线、记忆种子 |

> 仓库中**无** `test_api.py`；请使用 pytest 或 Swagger。

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务信息与端点索引 |
| GET | `/health` | 健康检查 |
| POST | `/chat` | 玩家对话 |
| GET | `/npcs` | NPC 列表，`?scene_id=` 可选 |
| GET | `/npcs/status` | 头顶台词，`?scene_id=` 可选 |
| POST | `/npcs/status/refresh` | 强制刷新批量台词 |
| GET | `/npcs/{name}` | NPC 详情 + 当前头顶台词 |
| GET | `/npcs/{name}/memories` | 记忆列表 |
| DELETE | `/npcs/{name}/memories` | 清空记忆，`?memory_type=working\|episodic` |
| GET | `/npcs/{name}/affinity` | 好感度 |
| PUT | `/npcs/{name}/affinity` | 设置好感（测试） |
| GET | `/affinities` | 全部好感 |
| GET | `/npcs/{name}/emotion` | 情绪 |
| PUT | `/npcs/{name}/emotion` | 设置情绪（测试） |
| GET | `/emotions` | 全部情绪 |
| GET | `/npcs/{name}/dialogue-history` | 对话历史 |

### POST /chat 响应字段

`message`, `emotion`, `emotion_label`, `affinity`, `affinity_level`, `affinity_change`, `success`, `timestamp` 等。

## 项目结构

```
backend/
├── main.py
├── config.py
├── models.py
├── npc_config_loader.py  # YAML 加载与 Pydantic 校验
├── agents.py
├── relationship_manager.py
├── emotion_manager.py
├── batch_generator.py
├── state_manager.py
├── logger.py
├── view_logs.py
├── npc_config/
│   ├── npcs.yaml         # NPC 行为唯一数据源（人格/记忆/基线/环境台词）
│   └── npcs.example.yaml # 带注释的编辑模板
├── memory_data/          # 运行时生成
├── logs/                 # 对话日志
├── tests/
├── requirements.txt
├── .env.example
└── start.ps1
```

## 配置（config.py / .env）

| 变量 | 默认 | 说明 |
|------|------|------|
| `LLM_API_KEY` | — | 必填才启用真实 LLM |
| `LLM_MODEL_ID` | Qwen2.5-72B-Instruct | 模型 |
| `LLM_BASE_URL` | ModelScope API | OpenAI 兼容地址 |
| `NPC_UPDATE_INTERVAL` | 30（代码内） | 头顶台词刷新间隔 |
| `NPC_CONFIG_PATH` | `npc_config/npcs.yaml` | NPC 行为 YAML 路径 |
| `NPC_MEMORY_FORCE_RESEED` | — | 设为 `1` 时启动强制重写 `initial_memories` |
| `QDRANT_*` | 见 .env.example | 情景记忆（可选） |

## NPC 行为配置（YAML）

非技术人员可通过编辑 [`npc_config/npcs.yaml`](npc_config/npcs.yaml) 调整 NPC，**无需改 Python**。模板与字段说明见 [`npc_config/npcs.example.yaml`](npc_config/npcs.example.yaml)。

| 配置块 | 作用 |
|--------|------|
| `personality` / `expertise` / `style` / `hobbies` | 写入 system prompt，决定对话人设 |
| `scene_id` / `title` / `location` / `activity` 等 | 场景元数据与 prompt 上下文 |
| `baselines.emotion` | 首次见面默认情绪：`happy` / `sad` / `angry` / `excited` / `neutral` |
| `baselines.affinity` | 首次见面默认好感度（0–100） |
| `initial_memories` | 开局记忆；**仅该 NPC 记忆库为空时**在启动时写入 |
| `ambient_dialogues` | LLM 不可用时的头顶预设台词（`morning` / `noon` / `afternoon` / `evening`） |

**修改后需重启后端。** 生效说明：

- 改 `personality` 等：重启即可
- 改 `initial_memories`：先 `DELETE /npcs/{名}/memories` 或删除 `memory_data/{名}/`，再重启；或设 `NPC_MEMORY_FORCE_RESEED=1`
- 改 `baselines`：重启后对新 `player_id` 的首次查询生效（已有会话仍用内存中的值）
- 校验失败时服务**拒绝启动**，终端会打印中文字段路径错误

加载逻辑见 `npc_config_loader.py`；`agents.py` 在启动时调用 `get_npc_roles()`，`batch_generator` 读取 `ambient_dialogues`。

## 批量台词设计

`state_manager` 对每个 `scene_id` 调用 `batch_generator.generate_batch_dialogues(scene_id=...)`，合并到 `current_dialogues`。相比「每个 NPC 单独请求」，同场景内一次 LLM 调用生成该场景全部 NPC 台词，降低成本。

## 持久化说明

| 数据 | 持久化 |
|------|--------|
| 记忆 | `memory_data/{npc}/` |
| 好感 / 情绪 / 头顶台词缓存 | 仅内存，重启丢失 |
| 对话日志 | `logs/dialogue_*.log` |

## 开发提示

- **新 NPC**：在 `npc_config/npcs.yaml` 的 `npcs` 下添加条目，并在 `ambient_dialogues` 四个时段各写一句；Godot 场景 `npc_name` 与 YAML 键名一致；`config.gd` 补充 `NPC_TITLES` / `NPC_WORLD_NAMES`（UI 展示）
- **自定义人设**：编辑 YAML 中 `personality`、`style`、`hobbies` 等
- **程序化扩展**：`npc_config_loader.load_npc_config()` / `get_npc_roles()`
- 批量 prompt 仍由 `batch_generator._build_batch_prompt` 从已加载角色生成

## 故障排查

| 现象 | 处理 |
|------|------|
| 启动报「NPC 配置文件」错误 | 检查 `npcs.yaml` 语法与必填字段；对照 `npcs.example.yaml` |
| 未设置 LLM_API_KEY | 警告 + YAML 预设头顶台词 / 模拟对话 |
| 情景记忆不可用 | 安装 qdrant-client，配置 QDRANT；或接受仅工作记忆 |
| 改了 initial_memories 没生效 | 记忆库非空会跳过种子；清空记忆或 `NPC_MEMORY_FORCE_RESEED=1` |
| CORS | `config.py` 中 `CORS_ORIGINS` |

## 许可证

与 HelloAgents 教材案例一致。
