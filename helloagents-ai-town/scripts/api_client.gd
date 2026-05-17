# API客户端 - 与FastAPI后端通信
extends Node

# 信号定义
signal chat_response_received(npc_name: String, message: String, emotion: String, emotion_label: String)
signal chat_error(error_message: String)
signal npc_status_received(dialogues: Dictionary)
signal npc_list_received(npcs: Array)
signal emotion_received(npc_name: String, emotion: String, emotion_label: String)
signal affinity_received(npc_name: String, affinity: float, level: String, change_amount: float)
signal dialogue_history_received(npc_name: String, history: Array)

# HTTP请求节点
var http_chat: HTTPRequest
var http_status: HTTPRequest
var http_npcs: HTTPRequest
var http_emotion: HTTPRequest
var http_affinity: HTTPRequest
var http_history: HTTPRequest

func _ready():
	http_chat = HTTPRequest.new()
	http_status = HTTPRequest.new()
	http_npcs = HTTPRequest.new()
	http_emotion = HTTPRequest.new()
	http_affinity = HTTPRequest.new()
	http_history = HTTPRequest.new()

	add_child(http_chat)
	add_child(http_status)
	add_child(http_npcs)
	add_child(http_emotion)
	add_child(http_affinity)
	add_child(http_history)

	http_chat.request_completed.connect(_on_chat_request_completed)
	http_status.request_completed.connect(_on_status_request_completed)
	http_npcs.request_completed.connect(_on_npcs_request_completed)
	http_emotion.request_completed.connect(_on_emotion_request_completed)
	http_affinity.request_completed.connect(_on_affinity_request_completed)
	http_history.request_completed.connect(_on_history_request_completed)

	print("[INFO] API客户端初始化完成")

func _npc_path_segment(npc_name: String) -> String:
	"""对路径中的 NPC 名称做 URL 编码（支持中文）"""
	return npc_name.uri_encode()

# ==================== 对话API ====================
func send_chat(npc_name: String, message: String) -> void:
	var data = {
		"npc_name": npc_name,
		"message": message
	}

	var json_string = JSON.stringify(data)
	var headers = ["Content-Type: application/json"]

	print("[API] POST /chat -> ", data)

	var error = http_chat.request(
		Config.API_CHAT,
		headers,
		HTTPClient.METHOD_POST,
		json_string
	)

	if error != OK:
		print("[ERROR] 发送对话请求失败: ", error)
		chat_error.emit("网络请求失败")

func _on_chat_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		print("[ERROR] 对话请求失败: HTTP ", response_code)
		chat_error.emit("服务器错误: " + str(response_code))
		return

	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())

	if parse_result != OK:
		print("[ERROR] 解析响应失败")
		chat_error.emit("响应解析失败")
		return

	var response = json.data

	if response.has("success") and response["success"]:
		var npc_name = response["npc_name"]
		var msg = response["message"]
		var emotion = response.get("emotion", "neutral")
		var emotion_label = response.get("emotion_label", "平静")
		var affinity = float(response.get("affinity", Config.AFFINITY_DEFAULT))
		var affinity_level = response.get("affinity_level", "友好")
		var affinity_change = float(response.get("affinity_change", 0.0))
		print("[INFO] 收到NPC回复: ", npc_name, " -> ", msg)
		print("[INFO] 情绪: ", emotion_label, " | 好感度: ", affinity, " (", affinity_level, ")")
		affinity_received.emit(npc_name, affinity, affinity_level, affinity_change)
		chat_response_received.emit(npc_name, msg, emotion, emotion_label)
	else:
		chat_error.emit("对话失败")

# ==================== 对话历史 API ====================
func get_dialogue_history(npc_name: String, limit: int = Config.DIALOGUE_HISTORY_LIMIT) -> void:
	var encoded = _npc_path_segment(npc_name)
	var url = Config.API_NPC_DIALOGUE_HISTORY % encoded
	if limit > 0:
		url += "?limit=" + str(limit)
	print("[API] GET ", url)

	var error = http_history.request(url)
	if error != OK:
		print("[ERROR] 获取对话历史失败: ", error)
		dialogue_history_received.emit(npc_name, [])

func _on_history_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		print("[ERROR] 对话历史请求失败: HTTP ", response_code)
		return

	var json = JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		print("[ERROR] 解析对话历史失败")
		return

	var response = json.data
	var npc_name = response.get("npc_name", "")
	var history = response.get("history", [])
	print("[INFO] 收到对话历史: ", npc_name, " (", history.size(), " 条)")
	dialogue_history_received.emit(npc_name, history)

# ==================== NPC状态API ====================
func get_npc_status(scene_id: String = "") -> void:
	if http_status.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		print("[WARN] NPC状态请求正在处理中,跳过本次请求")
		return

	var url := Config.API_NPC_STATUS
	if not scene_id.is_empty():
		url += "?scene_id=" + scene_id.uri_encode()

	print("[API] GET ", url)

	var error = http_status.request(url)

	if error != OK:
		print("[ERROR] 获取NPC状态失败: ", error)

func _on_status_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		print("[ERROR] NPC状态请求失败: HTTP ", response_code)
		return

	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())

	if parse_result != OK:
		print("[ERROR] 解析NPC状态失败")
		return

	var response = json.data

	if response.has("dialogues"):
		var dialogues = response["dialogues"]
		print("[INFO] 收到NPC状态更新: ", dialogues.size(), "个NPC")
		npc_status_received.emit(dialogues)

# ==================== NPC列表API ====================
func get_npc_list() -> void:
	print("[API] GET /npcs")

	var error = http_npcs.request(Config.API_NPCS)

	if error != OK:
		print("[ERROR] 获取NPC列表失败: ", error)

func _on_npcs_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		print("[ERROR] NPC列表请求失败: HTTP ", response_code)
		return

	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())

	if parse_result != OK:
		print("[ERROR] 解析NPC列表失败")
		return

	var response = json.data

	if response.has("npcs"):
		var npcs = response["npcs"]
		print("[INFO] 收到NPC列表: ", npcs.size(), "个NPC")
		npc_list_received.emit(npcs)

# ==================== 情绪API ====================
func get_npc_emotion(npc_name: String) -> void:
	var url = Config.API_NPC_EMOTION % _npc_path_segment(npc_name)
	print("[API] GET ", url)

	var error = http_emotion.request(url)

	if error != OK:
		print("[ERROR] 获取NPC情绪失败: ", error)

func _on_emotion_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		print("[ERROR] 情绪请求失败: HTTP ", response_code, " body=", body.get_string_from_utf8())
		return

	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())

	if parse_result != OK:
		print("[ERROR] 解析情绪响应失败")
		return

	var response = json.data

	var npc_name = response.get("npc_name", "")
	var emotion = response.get("emotion", "neutral")
	var emotion_label = response.get("emotion_label", "平静")

	print("[INFO] 收到NPC情绪: ", npc_name, " -> ", emotion_label, " (", emotion, ")")
	emotion_received.emit(npc_name, emotion, emotion_label)

# ==================== 好感度 API ====================
func get_npc_affinity(npc_name: String) -> void:
	var url = Config.API_NPC_AFFINITY % _npc_path_segment(npc_name)
	print("[API] GET ", url)

	var error = http_affinity.request(url)
	if error != OK:
		print("[ERROR] 获取NPC好感度失败: ", error)

func _on_affinity_request_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		print("[ERROR] 好感度请求失败: HTTP ", response_code, " body=", body.get_string_from_utf8())
		return

	var json = JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		print("[ERROR] 解析好感度响应失败")
		return

	var response = json.data
	var npc_name = response.get("npc_name", "")
	var affinity = float(response.get("affinity", Config.AFFINITY_DEFAULT))
	var level = response.get("level", "友好")

	print("[INFO] 收到NPC好感度: ", npc_name, " -> ", affinity, " (", level, ")")
	affinity_received.emit(npc_name, affinity, level, 0.0)
