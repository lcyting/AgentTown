# 赛博小镇 - GDScript 脚本说明

## 脚本列表

```
scripts/
├── config.gd           # 全局配置（API、场景、NPC、情绪/好感 UI 常量）
├── api_client.gd       # API 通信（AutoLoad: APIClient）
├── world_manager.gd    # 多场景切换（AutoLoad: WorldManager）
├── world_scene.gd      # office / cafe / library 共用逻辑
├── door.gd             # 跨场景传送门
├── room_collisions.gd  # 从 room_layouts JSON 加载碰撞
├── player.gd           # 玩家移动与 E 交互
├── npc.gd              # NPC 巡逻、交互区、头顶台词
└── dialogue_ui.gd      # 对话面板、历史、情绪/好感 Label
```

---

## config.gd

```gdscript
const API_BASE_URL = "http://localhost:8000"
const SCENE_IDS = ["office", "cafe", "library"]
const NPC_NAMES = ["程码", "林案", "苏绘", "小林", "陈读"]
const EMOTION_FONT_COLORS = { ... }
const AFFINITY_LEVEL_COLORS = { ... }
```

修改后端地址时只改 `API_BASE_URL`。

NPC 人格、记忆种子、情绪/好感基线、头顶预设台词由后端 [`backend/npc_config/npcs.yaml`](../../backend/npc_config/npcs.yaml) 配置；`NPC_TITLES` / `NPC_WORLD_NAMES` 仅用于对话 UI 展示，键名须与 YAML 及场景 `npc_name` 一致。

---

## api_client.gd

### 方法

| 方法 | 后端 |
|------|------|
| `send_chat(npc_name, message)` | `POST /chat` |
| `get_npc_status(scene_id)` | `GET /npcs/status?scene_id=` |
| `get_npc_list()` | `GET /npcs` |
| `get_npc_emotion(npc_name)` | `GET /npcs/{name}/emotion` |
| `get_npc_affinity(npc_name)` | `GET /npcs/{name}/affinity` |
| `get_dialogue_history(npc_name)` | `GET /npcs/{name}/dialogue-history` |

NPC 名含中文时使用 `uri_encode()` 拼路径。

### 信号

| 信号 | 说明 |
|------|------|
| `chat_response_received(npc, message, emotion, emotion_label)` | 对话回复 |
| `affinity_received(npc, affinity, level, change_amount)` | 好感（chat 响应内也会 emit） |
| `emotion_received(npc, emotion, emotion_label)` | 开对话时查询情绪 |
| `dialogue_history_received(npc, history)` | 历史记录 |
| `npc_status_received(dialogues)` | 头顶批量台词 |
| `chat_error(msg)` | 错误 |

**未对接的后端接口：** `GET /emotions`、`GET /affinities`、`GET/DELETE /memories`、`POST /npcs/status/refresh`（可按需在 `api_client` 扩展）。

---

## world_manager.gd

- `current_scene_id`：`office` | `cafe` | `library`
- `transition_to(scene_id, spawn_id)`：切换场景并放置玩家到对应 `Marker2D`

---

## world_scene.gd

- `_ready`：同步 `WorldManager.current_scene_id`
- 定时 `get_npc_status(current_scene_id)`
- 遍历 `"npcs"` 组，按 `npc_name` 更新 `DialogueLabel`（无硬编码旧名）

---

## dialogue_ui.gd

- `EmotionLabel` / `AffinityLabel`：开对话时请求 emotion + affinity；每轮 chat 更新
- `get_dialogue_history` 填充历史区
- 调用：`get_tree().call_group("dialogue_system", "start_dialogue", "程码")`

---

## player.gd / npc.gd

- 玩家：**WASD**，**E** 与范围内 NPC 交互
- NPC：`@export npc_name`（须与后端 `npc_config/npcs.yaml` 中键名一致）、`interaction_hint_text`

---

## AutoLoad 配置

`Project → Project Settings → AutoLoad`：

| 脚本 | 名称 |
|------|------|
| config.gd | Config |
| api_client.gd | APIClient |
| world_manager.gd | WorldManager |

---

## 信号流程（对话）

```
player E 键 → dialogue_ui.start_dialogue
  → api get_npc_emotion / affinity / dialogue-history
  → 玩家输入 → api send_chat
  → chat_response_received → 更新文本、情绪、好感
```

---

## 添加新 NPC

1. 在 [`backend/npc_config/npcs.yaml`](../../backend/npc_config/npcs.yaml) 添加 `npcs` 条目（含 `scene_id`、`personality`、`baselines`、`initial_memories`）
2. 在同一文件的 `ambient_dialogues` 下为 `morning` / `noon` / `afternoon` / `evening` 各写一句预设头顶台词
3. 在目标 `.tscn` 的 `NPCs` 下实例化 `npc.tscn`，`npc_name` 与 YAML 键名**完全一致**
4. 在 `config.gd` 补充 `NPC_TITLES`、`NPC_WORLD_NAMES`（对话 UI 展示用）
5. 重启后端

---

## 调试

- Godot **输出** 面板：`[INFO]` / `[API]` 日志
- `config.gd`：`DEBUG_MODE`、`SHOW_INTERACTION_RANGE`

---

## 参考

- [Godot 文档](https://docs.godotengine.org/)
- [项目 SETUP_GUIDE.md](../../SETUP_GUIDE.md)
- [backend/README.md](../../backend/README.md)
