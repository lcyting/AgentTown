# 各世界场景共用脚本（替代 main.gd）
extends Node2D

@export var scene_id: String = "office"

var api_client: Node = null
var status_update_timer: float = 0.0

@onready var scene_name_label: Label = get_node_or_null("UI/SceneNameLabel")

func _ready() -> void:
	WorldManager.current_scene_id = scene_id
	_update_scene_label()
	_style_scene_name_ui()
	_build_travel_hints()

	api_client = get_node_or_null("/root/APIClient")
	if api_client:
		if not api_client.npc_status_received.is_connected(_on_npc_status_received):
			api_client.npc_status_received.connect(_on_npc_status_received)
		api_client.get_npc_status(WorldManager.current_scene_id)
	else:
		push_error("[WorldScene] APIClient 未找到")

	call_deferred("_apply_player_spawn")

func _apply_player_spawn() -> void:
	# 等物理帧完成后再移位，避免落在门碰撞区内立刻再次切场景
	await get_tree().physics_frame
	var player := get_tree().get_first_node_in_group("player")
	if player is Node2D:
		WorldManager.apply_spawn(player)
	elif WorldManager.pending_spawn_id != "":
		WorldManager.clear_transition_lock()

func _process(delta: float) -> void:
	status_update_timer += delta
	if status_update_timer >= Config.NPC_STATUS_UPDATE_INTERVAL:
		status_update_timer = 0.0
		if api_client:
			api_client.get_npc_status(WorldManager.current_scene_id)

func _update_scene_label() -> void:
	if scene_name_label:
		var display_name: String = Config.SCENE_DISPLAY_NAMES.get(scene_id, scene_id)
		scene_name_label.text = "赛博小镇 · " + display_name


func _style_scene_name_ui() -> void:
	if not scene_name_label:
		return
	var themes := {
		"cafe": {
			"bg": Color(0.22, 0.12, 0.08, 0.82),
			"fg": Color(1.0, 0.93, 0.82),
			"border": Color(0.55, 0.32, 0.18, 0.9),
		},
		"library": {
			"bg": Color(0.10, 0.10, 0.18, 0.82),
			"fg": Color(0.88, 0.92, 1.0),
			"border": Color(0.35, 0.38, 0.62, 0.9),
		},
		"office": {
			"bg": Color(0.08, 0.12, 0.16, 0.78),
			"fg": Color(0.9, 0.95, 1.0),
			"border": Color(0.25, 0.45, 0.55, 0.85),
		},
	}
	var theme: Dictionary = themes.get(scene_id, themes["office"])
	var ui := scene_name_label.get_parent()
	if ui == null:
		return
	var backdrop := ui.get_node_or_null("SceneNameBackdrop") as ColorRect
	if backdrop == null:
		backdrop = ColorRect.new()
		backdrop.name = "SceneNameBackdrop"
		backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
		ui.add_child(backdrop)
		ui.move_child(backdrop, 0)
	var label_w := scene_name_label.offset_right - scene_name_label.offset_left
	var label_h := scene_name_label.offset_bottom - scene_name_label.offset_top
	backdrop.position = Vector2(scene_name_label.offset_left - 12, scene_name_label.offset_top - 8)
	backdrop.size = Vector2(label_w + 24, label_h + 16)
	backdrop.color = theme["bg"]
	scene_name_label.add_theme_color_override("font_color", theme["fg"])
	scene_name_label.add_theme_color_override("font_shadow_color", theme["border"])
	scene_name_label.add_theme_constant_override("shadow_offset_x", 1)
	scene_name_label.add_theme_constant_override("shadow_offset_y", 1)
	scene_name_label.add_theme_font_size_override("font_size", 20)


func _build_travel_hints() -> void:
	if scene_id == "office":
		return
	var ui := scene_name_label.get_parent() if scene_name_label else null
	if ui == null:
		return
	var existing := ui.get_node_or_null("TravelHint")
	if existing:
		existing.queue_free()
	var hint := Label.new()
	hint.name = "TravelHint"
	hint.text = "走近左右侧出口可前往其他场所"
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.offset_left = 400.0
	hint.offset_top = 680.0
	hint.offset_right = 880.0
	hint.offset_bottom = 708.0
	hint.add_theme_font_size_override("font_size", 13)
	var muted := Color(0.75, 0.75, 0.8, 0.85)
	if scene_id == "cafe":
		muted = Color(0.9, 0.82, 0.7, 0.8)
	elif scene_id == "library":
		muted = Color(0.78, 0.82, 0.95, 0.8)
	hint.add_theme_color_override("font_color", muted)
	ui.add_child(hint)

func _on_npc_status_received(dialogues: Dictionary) -> void:
	Config.log_info("更新场景 %s NPC 台词: %s" % [scene_id, dialogues.keys()])
	for npc in get_tree().get_nodes_in_group("npcs"):
		if not npc.has_method("get_npc_name"):
			continue
		var npc_name: String = npc.get_npc_name()
		if dialogues.has(npc_name) and npc.has_method("update_dialogue"):
			npc.update_dialogue(dialogues[npc_name])
