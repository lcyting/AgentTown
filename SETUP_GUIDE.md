# 赛博小镇 - 安装配置指南

## 系统要求

- **操作系统:** Windows 10/11、macOS 或 Linux
- **Godot:** 4.2+（推荐 4.3+，当前工程为 4.6）
- **Python:** 3.10+
- **Git:**（可选，用于克隆仓库）

## 安装步骤

### 步骤 1：获取项目

**方法 A：Git**

```bash
git clone https://github.com/lcyting/AgentTown.git
cd AgentTown
```

**方法 B：** 下载 ZIP 并解压。

### 步骤 2：安装 Godot

1. 打开 [Godot 官网](https://godotengine.org/download) 下载 4.x
2. 安装或解压后启动编辑器

### 步骤 3：配置 Python 后端

#### 3.1 创建虚拟环境

```bash
cd backend
python -m venv venv
```

#### 3.2 激活虚拟环境

**Windows（PowerShell / CMD）：**

```bash
venv\Scripts\activate
```

**macOS / Linux：**

```bash
source venv/bin/activate
```

#### 3.3 安装依赖

```bash
pip install -r requirements.txt
```

`hello-agents` 已通过 `requirements.txt` 安装，无需单独克隆 HelloAgents 源码（除非你要改框架本身）。

可选：情景记忆需要 `qdrant-client` 与 `sentence-transformers`（已在 requirements 中）；未配置 Qdrant 时自动回退为**仅工作记忆**。

### 步骤 4：配置环境变量

```bash
cd backend
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux
```

编辑 `backend/.env`，至少配置 LLM（示例为 ModelScope）：

```env
LLM_API_KEY=your-api-key-here
LLM_MODEL_ID=Qwen/Qwen2.5-72B-Instruct
LLM_BASE_URL=https://api-inference.modelscope.cn/v1/
```

可选（情景记忆向量库，见 `.env.example` 内注释）：

```env
QDRANT_URL=https://xxxx.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=xxxxx
```

未设置 `LLM_API_KEY` 时：服务仍可启动，对话与头顶台词使用预设/模拟模式。

`NPC_UPDATE_INTERVAL` 在 `config.py` 中默认为 **30** 秒，一般无需写入 `.env`。

可选（NPC 行为配置）：

```env
# 自定义 YAML 路径（默认 backend/npc_config/npcs.yaml）
# NPC_CONFIG_PATH=D:/path/to/npcs.yaml

# 开发时强制用 YAML 重写初始记忆（会先清空 working/episodic）
# NPC_MEMORY_FORCE_RESEED=1
```

### 步骤 4.5：自定义 NPC 行为（可选）

无需编程即可调整 NPC：

1. 用文本编辑器打开 `backend/npc_config/npcs.yaml`（对照 `npcs.example.yaml` 中的注释）
2. 修改 `personality`、`style`、`initial_memories`、`baselines`、`ambient_dialogues` 等
3. **重启后端**（`python main.py`）

| 修改项 | 额外操作 |
|--------|----------|
| 性格 / 环境台词 | 重启即可 |
| `initial_memories` | 清空 `backend/memory_data/{NPC名}/` 或 `DELETE /npcs/{名}/memories`，再重启 |
| `baselines` | 重启后对新对话会话生效 |

新增 NPC 时：在 YAML 添加 `npcs` 条目 + 四时段 `ambient_dialogues`，在 Godot 放置 `npc.tscn` 并设置 `npc_name` 与 YAML 键名一致。详见 [backend/README.md](backend/README.md)。

### 步骤 5：启动后端

```bash
cd backend
python main.py
```

或使用 `start.ps1`（Windows，会调用 venv 内 Python）。

预期输出包含对话日志路径、LLM 配置提示、API 地址 `http://0.0.0.0:8000` 与文档 `http://localhost:8000/docs`。

### 步骤 6：打开 Godot 项目

1. 启动 Godot → **导入**
2. 选择 `helloagents-ai-town/project.godot`
3. **导入并编辑**
4. 主场景为 `scenes/office.tscn`；可在办公室、咖啡厅、图书馆之间通过门传送

### 步骤 7：运行游戏

1. 确保后端已运行
2. Godot 中按 **F5** 运行
3. **WASD** 移动，**E** 与 NPC 交互，**Enter** 发送消息，**ESC** 关闭对话框

## 游戏操作

| 按键 | 功能 |
|------|------|
| WASD / 方向键 | 移动 |
| E | 与附近 NPC 交互 |
| Enter | 发送对话 |
| ESC | 关闭对话框 |

## 测试

### 自动化（后端）

```bash
cd backend
python -m pytest tests/ -v
```

覆盖：情绪管理器、情绪 API（mock）、好感度分析 JSON 解析、NPC YAML 配置加载。

### API 文档

浏览器打开：http://localhost:8000/docs

### 对话日志

```bash
cd backend
python view_logs.py tail    # 实时
python view_logs.py view    # 今日全文
python view_logs.py list    # 列出所有日志文件
```

## 常见问题

### Q1：后端启动失败？

检查：Python ≥ 3.10、已激活 venv、`pip install -r requirements.txt` 成功、`backend/.env` 路径正确。

### Q2：Godot 无法打开项目？

检查 Godot 版本 ≥ 4.2，`helloagents-ai-town/project.godot` 存在。

### Q3：能进游戏但无法对话？

1. 后端是否在 `http://localhost:8000` 运行  
2. `helloagents-ai-town/scripts/config.gd` 中 `API_BASE_URL` 是否与后端一致  
3. 查看 Godot **输出** 面板与后端终端报错  

### Q4：NPC 记不住对话？

- 查看启动日志是否「记忆系统已启用」  
- 未配置 Qdrant 时仅有工作记忆，重启后工作记忆也会清空（好感/情绪同样仅内存）  
- 情景记忆目录：`backend/memory_data/{NPC名}/`

### Q5：好感度 / 情绪重启后归零？

运行时数值在内存中，**服务重启后**会按 `npc_config/npcs.yaml` 里 `baselines` 恢复默认（如好感 50、情绪 neutral）；与玩家当次会话中已变化的值无关。记忆文件目录可单独保留。

### Q6：修改了 npcs.yaml 不生效？

1. 确认已**重启后端**（不支持热重载）  
2. 改 `initial_memories` 时需清空该 NPC 记忆后再启动  
3. 启动失败时查看终端中文校验错误，对照 `npcs.example.yaml`

## 开始体验

启动后端 → 运行 Godot → 在办公室找到程码、林案或苏绘，按 **E** 开始对话。
