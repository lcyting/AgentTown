#!/usr/bin/env python3
"""
根据 tools/room_layouts.py 烘焙 1280x720 静态预览图，并导出 Godot 碰撞 JSON。
修改布局后运行: python tools/bake_room_previews.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from room_layouts import LAYOUTS, SHEETS  # noqa: E402

TS = 48
W, H = 1280, 720
ROOT = Path(__file__).resolve().parents[1]
INTERIORS = ROOT / "assets" / "interiors"
LAYOUT_JSON_DIR = ROOT / "assets" / "room_layouts"

WALL_TOP = [(45, 61), (46, 61), (47, 61), (48, 61)]
WALL_CAP = [(45, 62), (46, 62), (47, 62), (48, 62)]


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def paste_cell(canvas: Image.Image, sheet: Image.Image, cell: tuple[int, int], x: int, y: int) -> None:
    cx, cy = cell
    tile = sheet.crop((cx * TS, cy * TS, cx * TS + TS, cy * TS + TS))
    canvas.paste(tile, (x, y), tile)


def paste_prop(canvas: Image.Image, sheet: Image.Image, prop: dict) -> None:
    rx, ry, rw, rh = prop["region"]
    block = sheet.crop((rx, ry, rx + rw, ry + rh))
    if prop.get("flip_h"):
        block = block.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if prop.get("flip_v"):
        block = block.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    px, py = prop["pos"]
    canvas.paste(block, (px, py), block)


def fill_floor(canvas: Image.Image, sheet: Image.Image, cells: list[tuple[int, int]]) -> None:
    n = len(cells)
    ty = 0
    for y in range(0, H, TS):
        tx = 0
        for x in range(0, W, TS):
            paste_cell(canvas, sheet, cells[(tx + ty) % n], x, y)
            tx += 1
        ty += 1


def paste_base_crop(canvas: Image.Image, crop: dict) -> None:
    sheet = load_rgba(INTERIORS / SHEETS[crop["sheet"]])
    x, y, w, h = crop["rect"]
    block = sheet.crop((x, y, x + w, y + h))
    block = block.resize((W, H), Image.Resampling.NEAREST)
    canvas.paste(block, (0, 0), block)


def patch_wall_rects(
    canvas: Image.Image,
    sheet: Image.Image,
    patches: list[dict],
) -> None:
    for patch in patches:
        px, py, pw, ph = patch["rect"]
        cells = [tuple(c) for c in patch["cells"]]
        if not cells:
            continue
        for y in range(py, py + ph, TS):
            for x in range(px, px + pw, TS):
                cell = cells[((x - px) // TS + (y - py) // TS) % len(cells)]
                paste_cell(canvas, sheet, cell, x, y)


def fill_transparent_bottom(
    canvas: Image.Image,
    sheet: Image.Image,
    cells: list[tuple[int, int]],
    y_start: int,
) -> None:
    """用地砖填补预览图下半部透明区域，避免露出底色。"""
    if not cells:
        return
    for y in range(y_start, H, TS):
        for x in range(0, W, TS):
            region = canvas.crop((x, y, min(x + TS, W), min(y + TS, H)))
            pixels = list(region.getdata())
            if not any(p[3] < 200 for p in pixels):
                continue
            cell = cells[((x // TS) + (y // TS)) % len(cells)]
            paste_cell(canvas, sheet, cell, x, y)


def draw_wall_border(canvas: Image.Image, sheet: Image.Image) -> None:
    top_i = 0
    for x in range(0, W, TS):
        for y, flip_v in ((0, False), (H - TS * 2, True)):
            for cell, dy in ((WALL_TOP[top_i % 4], 0), (WALL_CAP[top_i % 4], TS)):
                tile = sheet.crop((cell[0] * TS, cell[1] * TS, cell[0] * TS + TS, cell[1] * TS + TS))
                if flip_v:
                    tile = tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                canvas.paste(tile, (x, y + dy), tile)
        top_i += 1
    row = 0
    for y in range(TS * 2, H - TS * 2, TS):
        for x, flip_h in ((0, False), (W - TS, True)):
            for cell, dy in ((WALL_TOP[row % 4], 0), (WALL_CAP[row % 4], TS)):
                tile = sheet.crop((cell[0] * TS, cell[1] * TS, cell[0] * TS + TS, cell[1] * TS + TS))
                if flip_h:
                    tile = tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                canvas.paste(tile, (x, y + dy), tile)
        row += 1


def bake_layout(layout: dict) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), tuple(layout["base_color"]))

    if "base_crop" in layout:
        paste_base_crop(canvas, layout["base_crop"])
        fill_y = layout.get("bottom_fill_from_y")
        fill_cells = layout.get("bottom_fill_cells")
        if fill_y is not None and fill_cells:
            sheet = load_rgba(INTERIORS / SHEETS[layout["base_crop"]["sheet"]])
            cells = [tuple(c) for c in fill_cells]
            fill_transparent_bottom(canvas, sheet, cells, int(fill_y))
    else:
        floor_sheet = load_rgba(INTERIORS / SHEETS[layout["floor_sheet"]])
        cells = [tuple(c) for c in layout["floor_cells"]]
        fill_floor(canvas, floor_sheet, cells)

    if layout.get("use_wall_border", False):
        wall_sheet = load_rgba(INTERIORS / SHEETS["room_builder"])
        draw_wall_border(canvas, wall_sheet)

    for prop in layout["props"]:
        sheet = load_rgba(INTERIORS / SHEETS[prop["sheet"]])
        paste_prop(canvas, sheet, prop)

    for patch in layout.get("wall_patches", []):
        sheet = load_rgba(INTERIORS / SHEETS[patch["sheet"]])
        patch_wall_rects(canvas, sheet, [patch])

    tint = Image.new("RGBA", (W, H), tuple(layout["tint"]))
    canvas.alpha_composite(tint)
    return canvas


def export_layout_json(layout: dict, out_path: Path) -> None:
    payload = {
        "version": 2,
        "scene_id": layout["scene_id"],
        "preview": f"res://assets/interiors/{layout['preview']}",
        "npc_position": layout["npc_position"],
        "collisions": layout["collisions"],
    }
    if layout.get("zone_passages"):
        payload["zone_passages"] = layout["zone_passages"]
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    INTERIORS.mkdir(parents=True, exist_ok=True)
    LAYOUT_JSON_DIR.mkdir(parents=True, exist_ok=True)

    for scene_id, layout in LAYOUTS.items():
        preview_path = INTERIORS / layout["preview"]
        bake_layout(layout).save(preview_path)
        json_path = LAYOUT_JSON_DIR / f"{scene_id}.json"
        export_layout_json(layout, json_path)
        print("Wrote", preview_path)
        print("Wrote", json_path)

    print("Done. 布局源: tools/room_layouts.py")


if __name__ == "__main__":
    main()
