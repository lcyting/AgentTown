# 赛博小镇 - 全局配置
extends Node

# ==================== API配置 ====================
const API_BASE_URL = "http://localhost:8000"
const API_CHAT = API_BASE_URL + "/chat"
const API_NPCS = API_BASE_URL + "/npcs"
const API_NPC_STATUS = API_BASE_URL + "/npcs/status"
const API_NPC_EMOTION = API_BASE_URL + "/npcs/%s/emotion"
const API_NPC_DIALOGUE_HISTORY = API_BASE_URL + "/npcs/%s/dialogue-history"
const API_NPC_AFFINITY = API_BASE_URL + "/npcs/%s/affinity"
const API_ALL_EMOTIONS = API_BASE_URL + "/emotions"
const DIALOGUE_HISTORY_LIMIT = 30

# ==================== 场景配置 ====================
const SCENE_IDS = ["office", "cafe", "library"]
const SCENE_DISPLAY_NAMES = {
	"office": "办公室",
	"cafe": "咖啡厅",
	"library": "图书馆",
}

# ==================== NPC配置 ====================
const NPC_NAMES = ["程码", "林案", "苏绘", "小林", "陈读"]
const NPC_TITLES = {
	"程码": "Python工程师",
	"林案": "产品经理",
	"苏绘": "UI设计师",
	"小林": "咖啡师",
	"陈读": "图书管理员",
}
const NPC_WORLD_NAMES = {
	"程码": "赛博小镇办公室",
	"林案": "赛博小镇办公室",
	"苏绘": "赛博小镇办公室",
	"小林": "赛博小镇咖啡厅",
	"陈读": "赛博小镇图书馆",
}

# ==================== 情绪配置 ====================
const EMOTION_LABELS = {
	"happy": "开心",
	"sad": "难过",
	"angry": "生气",
	"excited": "兴奋",
	"neutral": "平静"
}
const EMOTION_COLORS = {
	"happy": "[color=yellow]",
	"sad": "[color=lightblue]",
	"angry": "[color=red]",
	"excited": "[color=orange]",
	"neutral": "[color=gray]"
}
const EMOTION_FONT_COLORS = {
	"happy": Color(1.0, 0.85, 0.2),
	"sad": Color(0.55, 0.75, 1.0),
	"angry": Color(1.0, 0.35, 0.35),
	"excited": Color(1.0, 0.6, 0.2),
	"neutral": Color(0.6, 0.6, 0.6)
}
const EMOTION_DEFAULT_KEY = "neutral"
const EMOTION_DEFAULT_LABEL = "平静"

# ==================== 好感度配置 ====================
const AFFINITY_MAX = 100.0
const AFFINITY_DEFAULT = 50.0
const AFFINITY_LEVEL_COLORS = {
	"挚友": Color(1.0, 0.45, 0.75),
	"亲密": Color(1.0, 0.65, 0.35),
	"友好": Color(0.45, 0.85, 0.55),
	"熟悉": Color(0.55, 0.75, 1.0),
	"陌生": Color(0.65, 0.65, 0.65),
}

# ==================== 游戏配置 ====================
const PLAYER_SPEED = 200.0  # 玩家移动速度
const INTERACTION_DISTANCE = 80.0  # 交互距离
const NPC_STATUS_UPDATE_INTERVAL = 30.0  # NPC状态更新间隔(秒)

# ==================== UI配置 ====================
const DIALOGUE_FADE_TIME = 0.3  # 对话框淡入淡出时间
const NPC_LABEL_OFFSET = Vector2(0, -60)  # NPC名字标签偏移

# ==================== 调试配置 ====================
const DEBUG_MODE = true  # 调试模式
const SHOW_INTERACTION_RANGE = true  # 显示交互范围

# ==================== 工具函数 ====================
func log_info(message: String) -> void:
	if DEBUG_MODE:
		print("[INFO] ", message)

func log_error(message: String) -> void:
	print("[ERROR] ", message)

func log_api(endpoint: String, data: Dictionary) -> void:
	if DEBUG_MODE:
		print("[API] ", endpoint, " -> ", JSON.stringify(data))
