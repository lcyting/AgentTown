# 对话日志系统使用指南

## 概述

对话过程会同时输出到：

- **控制台** — 实时调试
- **日志文件** — `backend/logs/dialogue_YYYY-MM-DD.log`

实现见 `backend/logger.py`，在 `agents.py` 的 `chat()` 流程中调用。

---

## 记录内容

- 对话开始 / 结束
- 玩家消息
- 当前好感度与等级
- **当前情绪**（`log_emotion`）
- 检索到的相关记忆
- NPC 回复
- 好感度分析结果与等级变化
- **情绪变化**（`log_emotion_change`，若本轮改变）
- 记忆保存确认

---

## 文件结构

```
backend/
├── logger.py
├── view_logs.py
├── agents.py          # 集成日志调用
└── logs/
    └── dialogue_YYYY-MM-DD.log
```

---

## 使用方法

### 启动后端（自动记录）

```bash
cd backend
python main.py
```

启动时会打印当日日志文件完整路径。

### 实时查看

另开终端：

```bash
cd backend
python view_logs.py tail
```

按 `Ctrl+C` 退出 tail。

### 查看今日全文 / 列表

```bash
python view_logs.py view
python view_logs.py list
```

---

## 日志格式示例

```
14:30:25 - ============================================================
14:30:25 - 💬 对话开始: 程码 <-> 玩家
14:30:25 - ============================================================
14:30:25 - 📝 玩家消息: 你好，很高兴认识你！
14:30:25 - 💖 当前好感度: 50.0/100 (友好)
14:30:25 - 😊 当前情绪: 平静 (neutral)
14:30:25 - 🧠 检索到0条相关记忆
14:30:26 - 🤖 正在生成回复...
14:30:28 - 💬 程码回复: 你好！我也很高兴认识你……
14:30:28 - 📊 正在分析好感度变化...
14:30:30 - 📈 好感度变化: 50.0 -> 56.0 (+6.0)
14:30:30 -   原因: 友好问候
14:30:30 -   情感: positive
14:30:30 - 😊 情绪变化: 平静 -> 开心
14:30:30 -   💾 对话已保存到程码的记忆中
14:30:30 - ============================================================
14:30:30 - ✅ 对话完成
```

---

## 技术实现

`logger.py` 使用 `logging` 双 handler（File + Stream）。`agents.py` 导入例如：

- `log_dialogue_start`, `log_affinity`, `log_memory_retrieval`
- `log_emotion`, `log_emotion_change`
- `log_npc_response`, `log_affinity_change`, `log_memory_saved`, `log_dialogue_end`

---

## 常见问题

**Q：日志在哪？**  
`backend/logs/dialogue_YYYY-MM-DD.log`，启动时终端会打印路径。

**Q：文件会很大吗？**  
单次对话约 0.5～1 KB，一般单日 < 1 MB。

**Q：如何看历史日期？**  
`python view_logs.py list` 后打开对应文件。

---

## 快速体验

1. `cd backend && python main.py`
2. Godot 运行游戏，与 NPC 对话
3. 另开终端：`python view_logs.py tail`
