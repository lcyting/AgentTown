# 场景传送门
extends Area2D

@export var target_scene_id: String = "cafe"
@export var spawn_id: String = "Spawn_from_office"
@export var require_interact_key: bool = false

var _player_inside: bool = false
var _transitioning: bool = false

@onready var _hint: Label = get_node_or_null("DoorHint")


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	_style_door_hint()

func _on_body_entered(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	_player_inside = true
	if not require_interact_key:
		_try_transition()

func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		_player_inside = false

func _unhandled_input(event: InputEvent) -> void:
	if not require_interact_key or not _player_inside:
		return
	if event.is_action_pressed("ui_accept"):
		_try_transition()
		get_viewport().set_input_as_handled()

func _try_transition() -> void:
	if _transitioning or not WorldManager.can_use_doors():
		return
	_transitioning = true
	WorldManager.transition_to(target_scene_id, spawn_id)


func _style_door_hint() -> void:
	if _hint == null:
		return
	var place: String = Config.SCENE_DISPLAY_NAMES.get(target_scene_id, target_scene_id)
	_hint.text = "→ %s" % place
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint.add_theme_font_size_override("font_size", 13)
	var colors := {
		"office": {"fg": Color(0.85, 0.95, 1.0), "bg": Color(0.08, 0.14, 0.2, 0.88)},
		"cafe": {"fg": Color(1.0, 0.9, 0.75), "bg": Color(0.24, 0.12, 0.06, 0.88)},
		"library": {"fg": Color(0.88, 0.9, 1.0), "bg": Color(0.1, 0.1, 0.2, 0.88)},
	}
	var theme: Dictionary = colors.get(target_scene_id, colors["office"])
	_hint.add_theme_color_override("font_color", theme["fg"])
	_hint.add_theme_color_override("font_shadow_color", theme["bg"])
	_hint.add_theme_constant_override("shadow_offset_x", 1)
	_hint.add_theme_constant_override("shadow_offset_y", 1)
	var backdrop := get_node_or_null("DoorHintBackdrop") as ColorRect
	if backdrop == null:
		backdrop = ColorRect.new()
		backdrop.name = "DoorHintBackdrop"
		backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(backdrop)
		move_child(backdrop, 0)
	backdrop.color = theme["bg"]
	backdrop.position = Vector2(_hint.offset_left - 6, _hint.offset_top - 4)
	backdrop.size = Vector2(
		_hint.offset_right - _hint.offset_left + 12,
		_hint.offset_bottom - _hint.offset_top + 8,
	)
