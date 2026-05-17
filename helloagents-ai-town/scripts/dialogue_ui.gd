# 对话UI脚本
extends CanvasLayer

# 节点引用
@onready var panel: Panel = $Panel
@onready var npc_name_label: Label = $Panel/NPCName
@onready var npc_title_label: Label = $Panel/NPCTitle
@onready var emotion_status_label: Label = $Panel/EmotionLabel
@onready var affinity_status_label: Label = $Panel/AffinityLabel
@onready var dialogue_text: RichTextLabel = $Panel/DialogueText
@onready var player_input: LineEdit = $Panel/PlayerInput
@onready var send_button: Button = $Panel/SendButton
@onready var close_button: Button = $Panel/CloseButton

# 当前对话的NPC
var current_npc_name: String = ""

# 本会话对话缓存（记忆系统未启用时的兜底）
var _session_history: Dictionary = {}

# API客户端引用
var api_client: Node = null

func _ready():
	# 添加到对话系统组
	add_to_group("dialogue_system")

	# 初始隐藏
	visible = false

	# 连接按钮信号
	send_button.pressed.connect(_on_send_button_pressed)
	close_button.pressed.connect(_on_close_button_pressed)
	player_input.gui_input.connect(_on_player_input_gui_input)

	# 获取API客户端
	api_client = get_node_or_null("/root/APIClient")
	if api_client:
		api_client.chat_response_received.connect(_on_chat_response_received)
		api_client.chat_error.connect(_on_chat_error)
		api_client.emotion_received.connect(_on_emotion_received)
		api_client.affinity_received.connect(_on_affinity_received)
		api_client.dialogue_history_received.connect(_on_dialogue_history_received)

	print("[INFO] 对话UI初始化完成")

# ⭐ 处理对话框快捷键
func _input(event: InputEvent):
	# 如果对话框不可见,不处理
	if not visible:
		return

	if event is InputEventKey and event.pressed and not event.echo:
		# ESC键 - 关闭对话框 
		if event.keycode == KEY_ESCAPE:
			hide_dialogue()
			get_viewport().set_input_as_handled()
			print("[DEBUG] ESC键关闭对话框")
			return

		# 回车发送（输入框无焦点时，例如刚点过对话区域）
		if event.keycode == KEY_ENTER or event.keycode == KEY_KP_ENTER:
			send_message()
			get_viewport().set_input_as_handled()
			return

		# 屏蔽移动键和交互键,防止触发游戏操作 ⭐ WASD键
		if event.keycode in [KEY_E, KEY_SPACE, KEY_W, KEY_A, KEY_S, KEY_D]:
			get_viewport().set_input_as_handled()
			# 只在第一次屏蔽时打印,避免刷屏
			match event.keycode:
				KEY_E:
					print("[DEBUG] 对话框中屏蔽了E键输入")
				KEY_SPACE:
					print("[DEBUG] 对话框中屏蔽了空格键输入")
				KEY_W:
					print("[DEBUG] 对话框中屏蔽了W键输入")
				KEY_A:
					print("[DEBUG] 对话框中屏蔽了A键输入")
				KEY_S:
					print("[DEBUG] 对话框中屏蔽了S键输入")
				KEY_D:
					print("[DEBUG] 对话框中屏蔽了D键输入")

func start_dialogue(npc_name: String):
	"""开始与NPC对话"""
	current_npc_name = npc_name

	# 通知NPC进入交互状态 (停止移动) 
	var npc = get_npc_by_name(npc_name)
	if npc and npc.has_method("set_interacting"):
		npc.set_interacting(true)

	# 设置NPC信息
	npc_name_label.text = npc_name
	var title: String = Config.NPC_TITLES.get(npc_name, "")
	var world_name: String = Config.NPC_WORLD_NAMES.get(npc_name, "")
	if not world_name.is_empty() and not title.is_empty():
		npc_title_label.text = world_name + " · " + title
	elif not world_name.is_empty():
		npc_title_label.text = world_name
	else:
		npc_title_label.text = title

	# 清空对话内容，等待历史加载
	dialogue_text.clear()
	dialogue_text.append_text("[color=gray]正在加载对话记录...[/color]\n")

	# 清空输入框
	player_input.text = ""

	# 情绪、好感度先显示加载中
	_update_emotion_display(Config.EMOTION_DEFAULT_KEY, "加载中...")
	_update_affinity_display(Config.AFFINITY_DEFAULT, "加载中...", 0.0)

	if api_client:
		api_client.get_dialogue_history(npc_name)
		api_client.get_npc_emotion(npc_name)
		api_client.get_npc_affinity(npc_name)

	# 显示对话框
	show_dialogue()

	# 聚焦输入框
	player_input.grab_focus()

	print("[INFO] 开始对话: ", npc_name)

func show_dialogue():
	"""显示对话框"""
	visible = true

	# 通知玩家进入交互状态 (禁用移动)
	var player = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_interacting"):
		player.set_interacting(true)

func hide_dialogue():
	"""隐藏对话框"""
	visible = false

	# 通知NPC退出交互状态 (恢复移动) 
	if current_npc_name != "":
		var npc = get_npc_by_name(current_npc_name)
		if npc and npc.has_method("set_interacting"):
			npc.set_interacting(false)

	current_npc_name = ""

	# 通知玩家退出交互状态 (启用移动)
	var player = get_tree().get_first_node_in_group("player")
	if player and player.has_method("set_interacting"):
		player.set_interacting(false)

func _on_send_button_pressed():
	"""发送按钮点击"""
	send_message()

func _on_player_input_gui_input(event: InputEvent) -> void:
	"""输入框内回车（优先于全局 _input，避免被其它脚本拦截）"""
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ENTER or event.keycode == KEY_KP_ENTER:
			send_message()
			player_input.accept_event()

func send_message():
	"""发送消息"""
	var message = player_input.text.strip_edges()
	
	if message.is_empty():
		return
	
	if current_npc_name.is_empty():
		print("[ERROR] 没有选择NPC")
		return
	
	_append_session_message(current_npc_name, "player", message)

	# 显示玩家消息
	dialogue_text.append_text("\n[color=cyan]玩家:[/color] " + message + "\n")
	
	# 清空输入框
	player_input.text = ""
	
	# 显示等待提示
	dialogue_text.append_text("[color=gray]等待回复...[/color]\n")
	
	# 发送API请求
	if api_client:
		api_client.send_chat(current_npc_name, message)
	else:
		print("[ERROR] API客户端未找到")

func _on_chat_response_received(npc_name: String, message: String, emotion: String = "neutral", emotion_label: String = "平静"):
	"""收到NPC回复"""
	if npc_name != current_npc_name:
		return
	
	# 移除"等待回复..."
	var text = dialogue_text.get_parsed_text()
	if text.ends_with("等待回复...\n"):
		# 清除最后一行
		dialogue_text.clear()
		var lines = text.split("\n")
		for i in range(lines.size() - 2):
			dialogue_text.append_text(lines[i] + "\n")
	
	_append_session_message(npc_name, "npc", message)

	# 显示NPC回复
	dialogue_text.append_text("[color=yellow]" + npc_name + ":[/color] " + message + "\n")
	
	# 更新情绪显示
	_update_emotion_display(emotion, emotion_label)
	
	# 滚动到底部
	dialogue_text.scroll_to_line(dialogue_text.get_line_count() - 1)

func _on_chat_error(error_message: String):
	"""对话错误"""
	dialogue_text.append_text("[color=red]错误: " + error_message + "[/color]\n")

func _on_emotion_received(npc_name: String, emotion: String, emotion_label_text: String):
	"""收到NPC情绪"""
	if npc_name != current_npc_name:
		return
	_update_emotion_display(emotion, emotion_label_text)

func _on_affinity_received(npc_name: String, affinity: float, level: String, change_amount: float):
	"""收到NPC好感度"""
	if npc_name != current_npc_name:
		return
	_update_affinity_display(affinity, level, change_amount)

func _on_dialogue_history_received(npc_name: String, history: Array):
	"""收到对话历史"""
	if npc_name != current_npc_name:
		return

	if not history.is_empty():
		_session_history[npc_name] = []
		for entry in history:
			if entry is Dictionary:
				_session_history[npc_name].append({
					"role": entry.get("role", ""),
					"content": entry.get("content", ""),
				})

	var display_history = history
	if display_history.is_empty() and _session_history.has(npc_name):
		display_history = _session_history[npc_name]

	_render_dialogue_history(npc_name, display_history, not history.is_empty())

func _render_dialogue_history(npc_name: String, history: Array, from_server: bool) -> void:
	dialogue_text.clear()
	if history.is_empty():
		dialogue_text.append_text("[color=gray]与 " + npc_name + " 的对话开始...[/color]\n")
	else:
		var header = "—— 历史对话 ——" if from_server else "—— 本次对话 ——"
		dialogue_text.append_text("[color=gray]" + header + "[/color]\n")
		for entry in history:
			if not entry is Dictionary:
				continue
			var role = entry.get("role", "")
			var content = entry.get("content", "")
			if content.is_empty():
				continue
			if role == "player":
				dialogue_text.append_text("[color=cyan]玩家:[/color] " + content + "\n")
			else:
				dialogue_text.append_text("[color=yellow]" + npc_name + ":[/color] " + content + "\n")
		dialogue_text.append_text("[color=gray]—— 继续对话 ——[/color]\n")

	dialogue_text.scroll_to_line(dialogue_text.get_line_count() - 1)

func _append_session_message(npc_name: String, role: String, content: String) -> void:
	if not _session_history.has(npc_name):
		_session_history[npc_name] = []
	_session_history[npc_name].append({"role": role, "content": content})

func _update_emotion_display(emotion_key: String, label_text: String):
	"""更新情绪标签显示（Label 不支持 BBCode，使用字体颜色）"""
	var font_color = Config.EMOTION_FONT_COLORS.get(emotion_key, Config.EMOTION_FONT_COLORS["neutral"])
	emotion_status_label.add_theme_color_override("font_color", font_color)
	emotion_status_label.text = "情绪: " + label_text
	print("[INFO] 情绪更新: ", label_text, " (", emotion_key, ")")

func _update_affinity_display(affinity: float, level: String, change_amount: float) -> void:
	var font_color = Config.AFFINITY_LEVEL_COLORS.get(level, Color(0.7, 0.7, 0.7))
	affinity_status_label.add_theme_color_override("font_color", font_color)
	var text = "好感度: %d/%d (%s)" % [int(round(affinity)), int(Config.AFFINITY_MAX), level]
	if abs(change_amount) >= 0.5:
		if change_amount > 0:
			text += " [+%d]" % int(round(change_amount))
		else:
			text += " [%d]" % int(round(change_amount))
	affinity_status_label.text = text
	print("[INFO] 好感度更新: ", affinity, " ", level)

func _on_close_button_pressed():
	"""关闭按钮点击"""
	hide_dialogue()

# ⭐ 根据名字获取NPC节点
func get_npc_by_name(npc_name: String) -> Node:
	"""根据名字获取NPC节点"""
	var npcs = get_tree().get_nodes_in_group("npcs")
	for npc in npcs:
		if npc.npc_name == npc_name:
			return npc
	return null
