# NPC 记忆系统使用指南

## 概述

每个 NPC 拥有独立的 **MemoryManager**（HelloAgents），在对话时检索相关记忆并写入新记忆，使 NPC 能引用近期或语义相关的历史内容。

**存储路径：** `backend/memory_data/{NPC名}/`（如 `程码/`）。  
**可选：** 配置 Qdrant 后启用情景记忆的向量检索；失败时自动**仅工作记忆**。  
**配置种子：** 在 [`backend/npc_config/npcs.yaml`](backend/npc_config/npcs.yaml) 的 `initial_memories` 中定义开局记忆，启动时若该 NPC 记忆库为空则自动写入。

---

## 核心功能

### 1. 工作记忆（Working Memory）

- 容量默认 **10** 条
- 用于当前对话上下文，检索快
- 服务重启后是否保留取决于 HelloAgents 本地存储实现

### 2. 情景记忆（Episodic Memory）

- 容量默认 **100** 条
- 需 Qdrant（`QDRANT_URL` 等，见 `backend/.env.example`）
- 语义检索：`retrieve_memories(..., memory_types=["working","episodic"], limit=5, min_importance=0.3)`
- `enable_semantic=False`、`enable_perceptual=False`（当前未启用语义/感知记忆模块）

### 3. 记忆隔离

- 每名 NPC 独立目录与 `user_id`
- NPC 之间不共享记忆
- `player_id` 写入 metadata（默认 `"player"`）

### 4. 初始记忆（YAML 配置）

在 `npc_config/npcs.yaml` 中为每名 NPC 配置 `initial_memories`：

```yaml
initial_memories:
  - content: 最近在优化多智能体系统的性能
    type: episodic      # working | episodic
    importance: 0.6     # 0.0–1.0
```

- **写入时机：** `NPCAgentManager` 创建记忆管理器后，若 working + episodic 总数为 0 则种子写入
- **metadata：** `source: config_seed`
- **更新配置后：** 删除 `memory_data/{NPC名}/` 或 `DELETE /npcs/{名}/memories`，或设置环境变量 `NPC_MEMORY_FORCE_RESEED=1` 后重启

---

## 使用示例

```
玩家: "你好，你是做什么的？"
程码: "你好！我是 Python 工程师……"

（稍后）
玩家: "还记得我刚才问你什么吗？"
程码: （结合检索到的工作/情景记忆回答）
```

与其他 NPC（如陈读）对话时，对方不知道你与程码聊过的内容。

---

## 技术实现

### 流程（`agents.py` → `chat()`）

**启动时：** `_create_memory_manager()` → `_seed_initial_memories()`（空库时，来自 YAML）

**每轮对话：**

1. `retrieve_memories(query, ["working", "episodic"], limit=5, min_importance=0.3)`
2. `_build_memory_context()` 拼入 prompt
3. `SimpleAgent.run(enhanced_message)`（已含好感、情绪上下文）
4. `_save_conversation_to_memory()`：玩家与 NPC 各一条 working 记忆，metadata 含好感、情绪等

### 目录结构

```
backend/memory_data/
├── 程码/
│   └── （SQLite / Qdrant 由 HelloAgents 管理）
├── 林案/
├── 苏绘/
├── 小林/
└── 陈读/
```

旧存档目录名（如 `张三/`）不会自动映射到新 NPC 名，需手动重命名或清空。

### 记忆 metadata 示例

```python
{
    "speaker": "player" | "npc",
    "player_id": "player",
    "context": {
        "interaction_type": "dialogue",
        "npc_name": "程码"
    },
    "affinity": 55.0,
    "emotion": "happy",
    "emotion_label": "开心"
}
```

### 配置（`_memory_config`）

```python
MemoryConfig(
    storage_path=memory_dir,
    working_memory_capacity=10,
    working_memory_tokens=2000,
    episodic_memory_capacity=100,
    enable_forgetting=True,
    forgetting_threshold=0.3,
)
```

---

## API 接口

### 对话

```http
POST /chat
{"npc_name": "程码", "message": "你好"}
```

响应除 `message` 外还包含 `emotion`、`affinity` 等（见好感度/情绪文档）。

### 获取记忆

```http
GET /npcs/程码/memories?limit=10
```

```json
{
  "npc_name": "程码",
  "memories": [...],
  "total": 10
}
```

### 清空记忆（测试）

```http
DELETE /npcs/程码/memories
DELETE /npcs/程码/memories?memory_type=working
DELETE /npcs/程码/memories?memory_type=episodic
```

### 对话历史

```http
GET /npcs/程码/dialogue-history?player_id=player&limit=30
```

从记忆中筛选 `interaction_type=dialogue` 的记录；Godot `dialogue_ui` 开对话时会拉取并展示。

---

## 测试方法

### API 文档

http://localhost:8000/docs → `POST /chat` 两轮 → `GET .../memories`

### Godot

运行游戏，与同一名 NPC 多轮对话，询问「刚才说了什么」。

### 依赖检查

启动时若缺少 `qdrant-client`，终端会提示安装；情景记忆不可用但工作记忆仍可用。

---

## 参数调优

| 参数 | 默认 | 说明 |
|------|------|------|
| working_memory_capacity | 10 | 近期对话条数 |
| working_memory_tokens | 2000 | 工作记忆 token 上限 |
| episodic_memory_capacity | 100 | 情景记忆条数 |
| forgetting_threshold | 0.3 | 低于此重要性的记忆可被遗忘 |
| retrieve limit | 5 | 每轮检索条数 |
| min_importance | 0.3 | 检索过滤阈值 |

---

## 常见问题

**Q：NPC 记不住？**  
未配置 LLM 时回复为模拟文本；记忆仍可能写入但内容有限。检查日志「记忆系统已初始化」与 `memory_data` 目录权限。

**Q：只有工作记忆？**  
Qdrant 未配置或连接失败时会打印回退提示。

**Q：占用空间大？**  
降低 `episodic_memory_capacity` 或 `DELETE` 清空；勿提交 `memory_data/` 到公开仓库。

**Q：改了 YAML 里的 initial_memories 没变化？**  
种子仅在记忆库为空时执行；先清空记忆再重启，或使用 `NPC_MEMORY_FORCE_RESEED=1`。

---

## 相关文档

- [AFFINITY_SYSTEM_GUIDE.md](AFFINITY_SYSTEM_GUIDE.md)
- [DIALOGUE_LOG_GUIDE.md](DIALOGUE_LOG_GUIDE.md)
- [backend/README.md](backend/README.md)（NPC YAML 配置说明）
