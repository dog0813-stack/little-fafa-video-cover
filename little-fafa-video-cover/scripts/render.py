"""Render the two calibrated cover layouts. Input is a UTF-8 JSON file."""

import argparse
import json
import os
import re
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ASSETS = Path(__file__).resolve().parents[1] / "assets"
WIDTH, HEIGHT = 4284, 5712
PINK = "#ff0096"


@dataclass(frozen=True)
class Slot:
    x: float
    baseline: float
    size: float
    leading: float
    track: float
    stroke: int
    fill: str
    edge: str
    limits: tuple
    centered: bool = False
    center_ink: bool = False


# Coordinates are in the layered Photoshop original, before the black bars.
SLOTS = {
    "opinion": {
        "top": Slot(158.24, 627.57, 547.87, 499.96, -.075, 24, "white", "black", (3340, 2820, 1780)),
        "main": Slot(2250.80, 4943.18, 585.93, 534.68, -.05, 101, PINK, "white", (4250, 4250), True),
    },
    "contrast": {
        "top": Slot(139.24, 648.49, 594.84, 542.84, -.05, 0, "white", "white", (3330, 2800)),
        "middle": Slot(136.86, 1759.86, 296.45, 270.53, -.05, 13, PINK, "white", (1810, 1810, 1810)),
        "main": Slot(2174.55, 4822.65, 906.57, 827.29, -.05, 73, PINK, "white", (4250, 4250), True),
    },
}

# The large edition reserves the lower part of the photo for the hook.
# Center its actual ink so punctuation cannot shift short lines off center.
SLOTS["opinion-large"] = {
    "top": SLOTS["opinion"]["top"],
    "main": Slot(WIDTH / 2, 4598, 1130, 960, -.052, 87, PINK, "white",
                 (4234, 4234), centered=True, center_ink=True),
}


def get_font_file(given):
    if given:
        return Path(given).expanduser().resolve(strict=True)
    for folder in (ASSETS, Path.cwd()):
        files = sorted(folder.glob("*优设标题黑*.ttf"))
        if len(files) == 1:
            return files[0]
    raise ValueError("请用 --font 指向优设标题黑 TTF，或把该字体放入技能的 assets 文件夹。")


def glyph_positions(line, font, slot):
    tracking = slot.track * font.size
    advances = [font.getlength(char) + tracking for char in line]
    start = slot.x
    if slot.centered:
        start -= sum(advances) / 2
        start += tracking
    for char, advance in zip(line, advances):
        yield char, round(start)
        start += advance


def layout_lines(lines, slot, font_file):
    if (not isinstance(lines, list) or not 1 <= len(lines) <= len(slot.limits)
            or not all(isinstance(s, str) and s.strip() and len(s) <= 48
                       and not any(ord(c) < 32 for c in s) for s in lines)):
        raise ValueError("每个文字区须提供分行后的非空短句，请核对行数和文案长度。")
    for percent in range(100, 66, -1):
        scale = percent / 100
        font = ImageFont.truetype(str(font_file), round(slot.size * scale))
        stroke = round(slot.stroke * scale)
        rows = []
        for i, line in enumerate(lines):
            index = i + (len(slot.limits) - len(lines) if slot.centered else 0)
            # Keep the bottom headline anchored to the original last baseline.
            if slot.centered:
                y = slot.baseline + (len(slot.limits) - 1) * slot.leading
                y -= (len(lines) - 1 - i) * slot.leading * scale
            else:
                y = slot.baseline - (slot.size - font.size) * .71 + i * slot.leading * scale
            positions = list(glyph_positions(line, font, slot))
            spans = []
            for char, x in positions:
                glyph, offset = font.getmask2(char, anchor="ls")
                box = glyph.getbbox()
                if box:
                    spans.append((x + offset[0] + box[0], x + offset[0] + box[2]))
            if not spans:
                raise ValueError("请检查是否输入了不可见字符。")
            left = min(a for a, _ in spans) - stroke
            right = max(b for _, b in spans) + stroke
            if slot.center_ink:
                offset = round(slot.x - (left + right) / 2)
                positions = [(char, x + offset) for char, x in positions]
                left += offset
                right += offset
            if left < 8 or right > slot.limits[index]:
                break
            rows.append((round(y), positions))
        if len(rows) == len(lines):
            return font, stroke, rows
    raise ValueError("文字超出模板范围。请按语义重新断行，若需删改已定文案，请先向用户确认。")


def round_outline(mask, radius):
    """Expand the merged ink, including into narrow counters in the typeface."""
    solid = mask.point(lambda value: 255 if value >= 128 else 0)
    boundary = ImageChops.subtract(solid, solid.filter(ImageFilter.MinFilter(3)))
    draw = ImageDraw.Draw(solid)
    for point in re.finditer(b"\xff", boundary.tobytes()):
        y, x = divmod(point.start(), mask.width)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
    return solid.filter(ImageFilter.GaussianBlur(.55))


def draw_slot(canvas, slot, lines, font_file, layout):
    font, stroke, rows = layout_lines(lines, slot, font_file)
    tofu = bytes(font.getmask(chr(0x10ffff)))
    for char in set("".join(lines).replace(" ", "")):
        if bytes(font.getmask(char)) == tofu:
            raise ValueError(f"原字体缺少字形「{char}」，请核对。")
    margin = stroke + (260 if slot.centered else 5)
    top = max(0, rows[0][0] - font.size - margin)
    bottom = min(HEIGHT, rows[-1][0] + round(font.size * .3) + margin)
    mask = Image.new("L", (WIDTH, bottom - top))
    fill_draw = ImageDraw.Draw(mask)
    for baseline, positions in rows:
        for char, x in positions:
            xy = x, baseline - top
            fill_draw.text(xy, char, font=font, anchor="ls", fill=255)
    region = canvas.crop((0, top, WIDTH, bottom))
    if stroke:
        edge = round_outline(mask, stroke)
        if slot.centered:
            glow = edge.filter(ImageFilter.GaussianBlur(75)).point(lambda v: v * .17)
            region.paste("#fff0a3" if layout == "contrast" else "black", (0, 0), glow)
        region.paste(slot.edge, (0, 0), edge)
    region.paste(slot.fill, (0, 0), mask)
    canvas.paste(region, (0, top))
    return top + mask.getbbox()[1] - stroke, font.size


def render(data, font_file, output):
    layout = data.get("layout", "opinion-large")
    if layout not in SLOTS:
        raise ValueError("layout 应为 opinion、opinion-large 或 contrast。")
    fields = set(data) - {"layout"}
    expected = set(SLOTS[layout])
    has_lead = layout == "opinion-large" and "lead" in data
    if has_lead:
        expected.add("lead")
    if fields != expected:
        raise ValueError(f"本款需要文字区 {', '.join(SLOTS[layout])}。")
    if output.suffix.lower() != ".png":
        raise ValueError("高清封面请以 .png 保存。")
    if output.exists():
        raise ValueError(f"同名文件已存在，请改用新版本文件名：{output.name}")
    with Image.open(ASSETS / "stage.png") as base:
        profile = base.info.get("icc_profile")
        canvas = base.convert("RGB")
    if canvas.size != (WIDTH, HEIGHT):
        raise ValueError("底图尺寸与模板不符。")
    for name, slot in SLOTS[layout].items():
        ink_top, actual_size = draw_slot(canvas, slot, data[name], font_file, layout)
        if has_lead and name == "main":
            lead = replace(slot, size=round(actual_size * .47), baseline=ink_top - 108,
                           stroke=round(actual_size * .043), limits=(4000,))
            draw_slot(canvas, lead, [data["lead"]], font_file, layout)
    if layout in ("opinion", "opinion-large"):
        with Image.open(ASSETS / "accent.png") as accent:
            canvas.paste(accent, (3382, 169), accent.getchannel("A"))
    full = Image.new("RGB", (4500, 8000), "black")
    full.paste(canvas.resize((4500, 6000), Image.Resampling.LANCZOS), (0, 1000))
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(f".{output.stem}-{uuid4().hex}.tmp")
    try:
        full.save(tmp, format="PNG", compress_level=5, icc_profile=profile)
        with output.open("xb"):
            pass
        try:
            os.replace(tmp, output)
        except OSError:
            output.unlink(missing_ok=True)
            raise
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("copy", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--font")
    args = parser.parse_args()
    try:
        render(json.loads(args.copy.read_text(encoding="utf-8-sig")), get_font_file(args.font), args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
