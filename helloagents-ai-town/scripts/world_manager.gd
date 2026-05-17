# 多场景世界管理器 (AutoLoad)
extends Node

var current_scene_id: String = "office"
var pending_spawn_id: String = ""
var _changing_scene: bool = false
var _ignore_doors_until_msec: int = 0

const DOOR_GRACE_MS: int = 900

const SCENE_PATHS: Dictionary = {
	"office": "res://scenes/office.tscn",
	"cafe": "res://scenes/cafe.tscn",
	"library": "res://scenes/library.tscn",
}

func can_use_doors() -> bool:
	return not _changing_scene and Time.get_ticks_msec() >= _ignore_doors_until_msec


func transition_to(scene_id: String, spawn_id: String = "") -> void:
	if scene_id not in SCENE_PATHS:
		push_error("[WorldManager] 未知场景: " + scene_id)
		return
	if not can_use_doors():
		return
	if scene_id == current_scene_id and spawn_id.is_empty():
		return

	_changing_scene = true
	var from_scene := current_scene_id
	pending_spawn_id = spawn_id
	current_scene_id = scene_id
	Config.log_info("切换场景: %s -> %s (spawn: %s)" % [from_scene, scene_id, spawn_id])
	# 门触发于 body_entered 物理回调中，须延迟切场景
	call_deferred("_change_scene", scene_id)


func _change_scene(scene_id: String) -> void:
	get_tree().change_scene_to_file(SCENE_PATHS[scene_id])

func clear_transition_lock() -> void:
	_changing_scene = false
	_ignore_doors_until_msec = Time.get_ticks_msec() + DOOR_GRACE_MS


func apply_spawn(player: Node2D) -> void:
	if player == null:
		clear_transition_lock()
		return
	if pending_spawn_id.is_empty():
		return

	var scene_root := get_tree().current_scene
	if scene_root == null:
		clear_transition_lock()
		return

	var marker := _find_spawn_marker(scene_root, pending_spawn_id)
	if marker:
		player.global_position = marker.global_position
		Config.log_info("玩家出生点: " + pending_spawn_id)
	else:
		push_warning("[WorldManager] 未找到出生点: " + pending_spawn_id)

	pending_spawn_id = ""
	clear_transition_lock()


func _find_spawn_marker(scene_root: Node, spawn_id: String) -> Node2D:
	for path in [spawn_id, "Spawns/" + spawn_id]:
		var node := scene_root.get_node_or_null(path)
		if node is Node2D:
			return node
	var found := scene_root.find_child(spawn_id, true, false)
	if found is Node2D:
		return found
	return null
