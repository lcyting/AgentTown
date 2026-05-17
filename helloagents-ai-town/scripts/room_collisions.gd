# 从 assets/room_layouts/*.json 加载与静态预览图一致的家具碰撞（仅碰撞，不渲染）
extends Node2D

@export_file("*.json") var layout_file: String = ""


func _ready() -> void:
	if layout_file.is_empty():
		push_error("[RoomCollisions] 未设置 layout_file")
		return
	var data: Variant = _load_json(layout_file)
	if data == null or not data is Dictionary:
		return
	for item in data.get("collisions", []):
		if not item is Dictionary:
			continue
		var name: String = str(item.get("name", ""))
		if name.begins_with("door_"):
			continue
		_add_collision(item)


func _load_json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		push_error("[RoomCollisions] 找不到布局文件: %s" % path)
		return null
	var text := FileAccess.get_file_as_string(path)
	return JSON.parse_string(text)


func _add_collision(item: Dictionary) -> void:
	var pos_arr: Array = item.get("pos", [0, 0])
	var size_arr: Array = item.get("size", [48, 48])
	var pos := Vector2(float(pos_arr[0]), float(pos_arr[1]))
	var size := Vector2(float(size_arr[0]), float(size_arr[1]))

	var body := StaticBody2D.new()
	body.name = str(item.get("name", "Furniture"))
	var shape_node := CollisionShape2D.new()
	var rect_shape := RectangleShape2D.new()
	rect_shape.size = size
	shape_node.shape = rect_shape
	shape_node.position = pos + size * 0.5
	body.add_child(shape_node)
	add_child(body)
