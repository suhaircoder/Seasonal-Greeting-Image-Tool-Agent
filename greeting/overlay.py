"""Pillow text overlay for greeting cards."""

from __future__ import annotations

import os
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

_WIN_FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

_FONT_FILES: dict[str, list[str]] = {
    "Georgia": ["georgia.ttf", "Georgia.ttf"],
    "Georgia Bold": ["georgiab.ttf", "georgiaz.ttf"],
    "Palatino": ["pala.ttf", "Palatino.ttf"],
    "Constantia": ["constan.ttf"],
    "Gabriola": ["Gabriola.ttf", "gabriola.ttf"],
    "Times New Roman": ["times.ttf", "Times.ttf"],
    "Times Bold": ["timesbd.ttf"],
    "Calibri": ["calibri.ttf", "Calibri.ttf"],
    "Calibri Bold": ["calibrib.ttf"],
    "Segoe UI": ["segoeui.ttf"],
    "Segoe Script": ["segoesc.ttf"],
    "Segoe Print": ["segoepr.ttf"],
    "Ink Free": ["Inkfree.ttf", "inkfree.ttf"],
    "Lucida Calligraphy": ["LCALLIG.TTF", "lcallig.ttf"],
    "Arial": ["arial.ttf"],
    "Arial Bold": ["arialbd.ttf"],
    "Impact": ["impact.ttf"],
    "DejaVu Sans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ],
}

POSITIONS = ("Top", "Upper", "Center", "Lower", "Bottom")
ALIGNMENTS = ("Left", "Center", "Right")


@dataclass
class TextStyle:
    message: str
    subtitle: str = ""
    font_name: str = "Georgia"
    font_size: int = 72
    color: str | tuple = "#FFF8EA"
    position: str = "Center"
    align: str = "Center"
    outline: bool = True
    panel: bool = True


def list_fonts() -> list[str]:
    found = [name for name, files in _FONT_FILES.items() if _first_existing(files)]
    return found or ["Default"]


def apply_text(image: Image.Image, style: TextStyle) -> Image.Image:
    message = " ".join((style.message or "").split())
    if not message:
        raise ValueError("Enter a message to put on the card.")
    subtitle = " ".join((style.subtitle or "").split())
    canvas = image.convert("RGBA")
    width, height = canvas.size
    max_text_width = int(width * 0.72)
    max_text_height = int(height * 0.46)
    draw = ImageDraw.Draw(canvas)
    font, lines = _fit_block(draw, message, style.font_name, style.font_size, max_text_width, max_text_height)
    sub_font = load_font(style.font_name, max(22, int(font.size * 0.38)))
    sub_lines = _wrap(draw, subtitle, sub_font, max_text_width) if subtitle else []

    line_gap = int(font.size * 0.18)
    sub_gap = int(sub_font.size * 0.2)
    message_height = _block_height(font, len(lines), line_gap)
    subtitle_height = _block_height(sub_font, len(sub_lines), sub_gap) if sub_lines else 0
    gap = int(font.size * 0.35) if sub_lines else 0
    block_height = message_height + gap + subtitle_height
    y = _position_y(style.position, height, block_height)

    fill = _parse_color(style.color)
    stroke = (20, 16, 12, 210) if _luminance(fill) > 150 else (255, 248, 234, 210)
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    pen = ImageDraw.Draw(overlay)

    if style.panel:
        _draw_panel(pen, draw, font, sub_font, lines, sub_lines, width, y, line_gap, sub_gap, gap, style.align, max_text_width)

    _draw_lines(pen, lines, font, width, y, line_gap, style.align, max_text_width, fill, stroke if style.outline else None)
    if sub_lines:
        sub_y = y + message_height + gap
        sub_fill = fill[:3] + (min(255, fill[3]),)
        _draw_lines(
            pen,
            sub_lines,
            sub_font,
            width,
            sub_y,
            sub_gap,
            style.align,
            max_text_width,
            sub_fill,
            stroke if style.outline else None,
        )
    return Image.alpha_composite(canvas, overlay).convert("RGB")


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = _first_existing(_FONT_FILES.get(name, []))
    if path:
        return ImageFont.truetype(path, size=max(12, int(size)))
    for files in _FONT_FILES.values():
        fallback = _first_existing(files)
        if fallback:
            return ImageFont.truetype(fallback, size=max(12, int(size)))
    return ImageFont.load_default()


def _first_existing(files: list[str]) -> str | None:
    for name in files:
        path = name if os.path.isabs(name) else os.path.join(_WIN_FONTS, name)
        if os.path.exists(path):
            return path
    return None


def _fit_block(draw, text, font_name, start_size, max_width, max_height):
    size = max(28, int(start_size))
    font = load_font(font_name, size)
    lines = _wrap(draw, text, font, max_width)
    while size > 28:
        gap = int(size * 0.18)
        height = _block_height(font, len(lines), gap)
        widest = max((_text_width(draw, line, font) for line in lines), default=0)
        if widest <= max_width and height <= max_height and len(lines) <= 5:
            return font, lines
        size -= 2
        font = load_font(font_name, size)
        lines = _wrap(draw, text, font, max_width)
    return font, lines


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if _text_width(draw, trial, font) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines or [text]


def _text_width(draw, text: str, font) -> float:
    if hasattr(draw, "textlength"):
        return draw.textlength(text, font=font)
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _block_height(font, count: int, gap: int) -> int:
    if count <= 0:
        return 0
    return count * int(font.size * 1.15) + (count - 1) * gap


def _position_y(position: str, height: int, block_height: int) -> int:
    margin = 88
    if position == "Top":
        return margin
    if position == "Upper":
        return int(height * 0.2)
    if position == "Lower":
        return int(height * 0.58)
    if position == "Bottom":
        return max(margin, height - block_height - margin)
    return max(margin, (height - block_height) // 2)


def _draw_lines(draw, lines, font, width, y, gap, align, max_width, fill, stroke) -> None:
    cursor = y
    step = int(font.size * 1.15) + gap
    for line in lines:
        line_width = _text_width(draw, line, font)
        x = _align_x(align, width, line_width, max_width)
        if stroke:
            draw.text((x, cursor), line, font=font, fill=fill, stroke_width=2, stroke_fill=stroke)
        else:
            draw.text((x, cursor), line, font=font, fill=fill)
        cursor += step


def _align_x(align: str, width: int, line_width: float, max_width: int) -> float:
    if align == "Left":
        return (width - max_width) / 2
    if align == "Right":
        return (width + max_width) / 2 - line_width
    return (width - line_width) / 2


def _draw_panel(pen, measure, font, sub_font, lines, sub_lines, width, y, line_gap, sub_gap, gap, align, max_width) -> None:
    message_height = _block_height(font, len(lines), line_gap)
    subtitle_height = _block_height(sub_font, len(sub_lines), sub_gap) if sub_lines else 0
    block_height = message_height + (gap if sub_lines else 0) + subtitle_height
    widest = 0
    for line, face in [(line, font) for line in lines] + [(line, sub_font) for line in sub_lines]:
        widest = max(widest, _text_width(measure, line, face))
    if align == "Center":
        left = (width - widest) / 2
    elif align == "Right":
        left = (width + max_width) / 2 - widest
    else:
        left = (width - max_width) / 2
    pad_x, pad_y = 36, 28
    box = [left - pad_x, y - pad_y, left + widest + pad_x, y + block_height + pad_y]
    pen.rounded_rectangle(box, radius=28, fill=(12, 10, 14, 168))


def _parse_color(value) -> tuple[int, int, int, int]:
    if isinstance(value, (tuple, list)) and len(value) >= 3:
        channels = []
        for channel in list(value)[:3]:
            number = float(channel)
            channels.append(int(number * 255) if 0 <= number <= 1 else int(number))
        alpha = 255
        if len(value) > 3:
            raw_alpha = float(value[3])
            alpha = int(raw_alpha * 255) if 0 <= raw_alpha <= 1 else int(raw_alpha)
        return channels[0], channels[1], channels[2], alpha
    text = str(value or "").strip()
    if text.startswith("#"):
        hex_color = text[1:]
        if len(hex_color) == 3:
            hex_color = "".join(ch * 2 for ch in hex_color)
        if len(hex_color) == 6:
            rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            return rgb + (255,)
    if text.lower().startswith("rgba"):
        numbers = text[text.find("(") + 1 : text.find(")")].split(",")
        if len(numbers) >= 3:
            red, green, blue = (int(float(numbers[0])), int(float(numbers[1])), int(float(numbers[2])))
            alpha = int(float(numbers[3]) * 255) if len(numbers) > 3 and float(numbers[3]) <= 1 else 255
            return red, green, blue, alpha
    if text.lower().startswith("rgb"):
        numbers = text[text.find("(") + 1 : text.find(")")].split(",")
        if len(numbers) >= 3:
            return int(float(numbers[0])), int(float(numbers[1])), int(float(numbers[2])), 255
    return (255, 248, 234, 255)


def _luminance(color: tuple[int, int, int, int]) -> float:
    red, green, blue = color[:3]
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue
