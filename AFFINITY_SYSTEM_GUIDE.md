# NPC 好感度系统使用指南

## 概述

赛博小镇 NPC 拥有**好感度系统**：根据与玩家的对话自动调整好感度，影响后续回复风格。好感度分析与**情绪**在同一次 LLM 调用中完成（见 `relationship_manager.py`），避免额外 API 费用。

**存储说明：** 好感度保存在 `RelationshipManager` 内存中；**服务重启后**按 [`backend/npc_config/npcs.yaml`](backend/npc_config/npcs.yaml) 中 `baselines.affinity` 作为首次见面默认值（未配置则为 50）。与记忆文件目录独立。

---

## 核心功能

### 1. 自动情感分析

- 使用 `SimpleAgent`（`AffinityAnalyzer`）分析玩家消息与 NPC 回复
- 输出 JSON：是否调整好感、`change_amount`、`reason`、`sentiment`、**`emotion`**
- `_parse_analysis()` 支持 JSON / 正则回退（见 `tests/test_analyzer_parse.py`）

### 2. 好感度动态调整

- 友好对话提升（约 +1～+10）
- 批评或冲突降低（约 -3～-15）
- 数值限制在 0～100

### 3. 关系等级

| 等级 | 数值范围 | 表现倾向 |
|------|----------|----------|
| 陌生 | 0～20 | 冷淡疏离 |
| 熟悉 | 20～40 | 礼貌略生疏 |
| 友好 | 40～60 | 正常交流（YAML 默认基线常为 50） |
| 亲密 | 60～80 | 更热情、愿多聊 |
| 挚友 | 80～100 | 像老朋友一样亲切 |

### 4. 对话风格调整

`get_affinity_modifier(affinity)` 在 `chat()` 中拼入 `enhanced_message`，与情绪修饰词一并注入。

### 5. Godot 客户端

- `dialogue_ui.gd`：`AffinityLabel` 显示数值、等级与本轮变化（↑/↓）
- 开对话时 `GET /npcs/{name}/affinity`；每轮 `POST /chat` 响应中的 `affinity` / `affinity_level` / `affinity_change` 也会更新 UI

---

## 使用示例

### 好感度提升

```
初始好感度: 50 (友好)

玩家: "你好，很高兴认识你！"
程码: "你好！我也很高兴认识你。"
→ 好感度可能上升，情绪可能为 happy

玩家: "你的代码写得真棒！"
→ 好感度继续上升，等级可能升至「亲密」
```

### 对话风格变化

低好感时回答更短；高好感时更愿意展开技术细节或主动提问（由 LLM + modifier 共同决定）。

---

## 技术实现

### 架构

```
RelationshipManager (relationship_manager.py)
├── default_affinities: 来自 npc_config/npcs.yaml baselines
├── affinity_scores: Dict[npc][player_id] -> float
├── analyzer_agent: SimpleAgent
├── get_affinity / analyze_and_update_affinity
├── get_affinity_level / get_affinity_modifier
└── 分析结果含 emotion → EmotionManager.set_emotion()

NPCAgentManager.chat() (agents.py)
├── 读取好感 + 情绪 → enhanced_message
├── agent.run()
├── analyze_and_update_affinity()
└── 返回 message, affinity*, emotion*
```

### 分析器输出格式（当前实现）

```json
{
  "should_change": true,
  "change_amount": 5,
  "reason": "友好问候",
  "sentiment": "positive",
  "emotion": "happy"
}
```

`emotion` 取值：`happy` | `sad` | `angry` | `excited` | `neutral`。

### 好感度变化参考

| 对话类型 | 变化量（参考） |
|---------|----------------|
| 赞美、感谢、请教 | +3～+8 |
| 友好问候 | +1～+3 |
| 普通闲聊 | 0 |
| 批评、质疑 | -3～-8 |
| 侮辱、攻击 | -8～-15 |

---

## API 接口

### 获取单个 NPC 好感度

```http
GET /npcs/程码/affinity?player_id=player
```

```json
{
  "npc_name": "程码",
  "player_id": "player",
  "affinity": 65.0,
  "level": "亲密",
  "modifier": "友好热情,愿意多聊,会主动关心对方"
}
```

### 获取全部好感度

```http
GET /affinities?player_id=player
```

### 对话（含好感度字段）

```http
POST /chat
Content-Type: application/json

{"npc_name": "程码", "message": "你好"}
```

```json
{
  "npc_name": "程码",
  "npc_title": "Python工程师",
  "message": "...",
  "emotion": "happy",
  "emotion_label": "开心",
  "affinity": 55.0,
  "affinity_level": "友好",
  "affinity_change": 5.0,
  "success": true
}
```

### 设置好感度（测试）

```http
PUT /npcs/程码/affinity?affinity=80&player_id=player
```

---

## 测试方法

### pytest（推荐，无需 API Key）

```bash
cd backend
python -m pytest tests/test_analyzer_parse.py -v
```

### Swagger / 真实对话

1. `python main.py`
2. http://localhost:8000/docs
3. `POST /chat` 后 `GET /npcs/程码/affinity`

### 查看日志

```bash
cd backend
python view_logs.py tail
```

日志中含 `log_affinity`、`log_affinity_change` 等。

---

## 调试

- 终端 / `backend/logs/dialogue_YYYY-MM-DD.log` 查看好感度变化与原因
- 好感不变：对话过中性、分析器 `should_change: false` 或 JSON 解析失败
- 调整敏感度：修改 `relationship_manager.py` 中 analyzer 的 prompt 与 `change_amount` 范围

---

## 与记忆、情绪的关系

- 每轮对话写入 working 记忆，metadata 含 `affinity`、`emotion`、`emotion_label`
- `GET /npcs/{name}/dialogue-history` 可从记忆中整理历史
- 情绪详情见 [NPC_EMOTION_SYSTEM_PLAN.md](NPC_EMOTION_SYSTEM_PLAN.md)

---

## 常见问题

**Q：好感度为什么没变化？**  
对话过中性、分析判定不调整，或 LLM 未配置导致走模拟逻辑。

**Q：重启后好感度丢失？**  
对话过程中变化的好感存在内存里，重启后会丢失；新会话的**起始值**由 YAML `baselines.affinity` 决定。若需固定开局好感，编辑 `npc_config/npcs.yaml` 后重启。

**Q：如何设置某 NPC 开局好感更高？**  
在 `npcs.yaml` 对应角色下设置 `baselines.affinity`（如 `70`），重启后端。

**Q：Godot 没显示好感度？**  
确认后端运行且 `API_BASE_URL` 正确；打开对话框时应请求 affinity 接口。

---

**版本说明：** 文档已与 `relationship_manager.py`、`agents.py`、`npc_config/npcs.yaml`、`dialogue_ui.gd` 实现对齐（5 名 NPC，多场景）。
