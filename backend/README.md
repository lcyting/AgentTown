# 赛博小镇 - FastAPI 后端

基于 [hello-agents](https://pypi.org/project/hello-agents/)（PyPI）的 AI NPC 对话、记忆、好感度、情绪与批量头顶台词服务。

## 功能特性

| 模块 | 说明 |
|------|------|
| 实时对话 | `POST /chat`，注入记忆 + 好感 + 情绪上下文 |
| 批量头顶台词 | 每 30s 按场景 `office`/`cafe`/`library` 各调一次 LLM（或预设） |
| 记忆 | 工作记忆 + 可选情景记忆（Qdrant） |
| 好感度 | LLM 分析，5 级关系，内存存储 |
| 情绪 | 与好感同次分析，5 种情绪，内存存储 |
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
├── agents.py
├── relationship_manager.py
├── emotion_manager.py
├── batch_generator.py
├── state_manager.py
├── logger.py
├── view_logs.py
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
| `QDRANT_*` | 见 .env.example | 情景记忆（可选） |

## 批量台词设计

`state_manager` 对每个 `scene_id` 调用 `batch_generator.generate_batch_dialogues(scene_id=...)`，合并到 `current_dialogues`。相比「每个 NPC 单独请求」，同场景内一次 LLM 调用生成该场景全部 NPC 台词，降低成本。

## 持久化说明

| 数据 | 持久化 |
|------|--------|
| 记忆 | `memory_data/{npc}/` |
| 好感 / 情绪 / 头顶台词缓存 | 仅内存，重启丢失 |
| 对话日志 | `logs/dialogue_*.log` |

## 开发提示

- 新 NPC：在 `agents.py` 的 `NPC_ROLES` 与 `batch_generator.preset_dialogues` 中添加，Godot `npc_name` 与键名一致
- 自定义人设：修改 `create_system_prompt`
- 批量 prompt：`batch_generator._build_batch_prompt`

## 故障排查

| 现象 | 处理 |
|------|------|
| 未设置 LLM_API_KEY | 警告 + 预设/模拟模式 |
| 情景记忆不可用 | 安装 qdrant-client，配置 QDRANT；或接受仅工作记忆 |
| CORS | `config.py` 中 `CORS_ORIGINS` |

## 许可证

与 HelloAgents 教材案例一致。
