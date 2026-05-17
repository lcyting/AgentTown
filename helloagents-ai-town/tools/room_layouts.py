"""
室内布局唯一数据源。
与办公室一致：使用 Japanese_Home 整张预览图中的已衔接房间区域，
放大为 1280x720，避免从精灵图散贴造成凌乱。
修改后运行: python tools/bake_room_previews.py
"""
from __future__ import annotations

SHEETS = {
    "japanese_home": "Japanese_Home_1_preview_48x48.png",
    "generic": "1_Generic_48x48.png",
    "conference": "13_Conference_Hall_48x48.png",
    "room_builder": "Room_Builder_48x48.png",
}


def _col(pos: tuple[int, int], size: tuple[int, int], name: str = "") -> dict:
    return {"name": name, "pos": list(pos), "size": list(size)}


# 茶室区：矮桌 + 坐垫 + 玄关（咖啡厅）
CAFE_ROOM = {"sheet": "japanese_home", "rect": [0, 360, 456, 282]}

# 办公室右侧：书桌 + 右侧双扇拉门（与 office.tscn 同区域）
LIBRARY_ROOM = {"sheet": "japanese_home", "rect": [456, 200, 456, 360]}

# 日式榻榻米地砖（用于咖啡厅底部补全）
JH_FLOOR_CELLS = [(4, 7), (5, 7), (6, 7), (7, 7), (4, 8), (5, 8), (6, 8), (7, 8)]

CAFE_LAYOUT: dict = {
    "scene_id": "cafe",
    "preview": "Cafe_1_preview_1280x720.png",
    "base_color": [42, 30, 22, 255],
    "tint": [255, 210, 150, 8],
    "base_crop": CAFE_ROOM,
    "bottom_fill_from_y": 540,
    "bottom_fill_cells": JH_FLOOR_CELLS,
    "props": [],
    "collisions": [
        _col((0, 0), (1280, 80), "wall_top"),
        _col((0, 0), (80, 720), "wall_left"),
        _col((1200, 0), (80, 720), "wall_right"),
        _col((280, 200), (320, 200), "table_zone"),
        _col((0, 560), (220, 160), "door_left"),
        _col((1060, 560), (220, 160), "door_right"),
    ],
    "npc_position": [640, 320],
}

LIBRARY_LAYOUT: dict = {
    "scene_id": "library",
    "preview": "Library_1_preview_1280x720.png",
    "base_color": [34, 32, 46, 255],
    "tint": [120, 140, 200, 8],
    "base_crop": LIBRARY_ROOM,
    "props": [],
    "collisions": [
        _col((0, 0), (1280, 80), "wall_top"),
        _col((0, 0), (80, 720), "wall_left"),
        _col((1200, 0), (80, 720), "wall_right"),
        _col((480, 300), (320, 140), "desk_zone"),
        _col((0, 520), (220, 200), "door_left"),
        _col((1060, 520), (220, 200), "door_right"),
        # 与 office.tscn MiddleWall 对齐（映射到本裁剪区 1280x720）
        _col((0, 0), (328, 128), "wall_mid_upper"),
        _col((210, 178), (574, 118), "wall_mid_right"),
        _col((904, 182), (248, 116), "wall_mid_far_right"),
    ],
    "npc_position": [280, 200],
}

LAYOUTS = {
    "cafe": CAFE_LAYOUT,
    "library": LIBRARY_LAYOUT,
}
