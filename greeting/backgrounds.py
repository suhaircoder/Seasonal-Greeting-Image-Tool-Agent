"""Backgrounds from seasonal artwork, DALL-E, or a free image API."""

from __future__ import annotations

import math
import os
import random
import time
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFilter

from greeting.net import http_call
from greeting.presets import OCCASIONS

CANVAS = (1024, 1024)
OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"
HORDE_URL = "https://aihorde.net/api/v2/generate/async"
HORDE_AGENT = "seasonal-greeting-image-tool:1.0:local"

SOURCES = (
    "Seasonal template",
    "DALL-E",
    "Free AI",
)


def generate_background(
    source: str,
    occasion: str,
    prompt: str,
    api_key: str = "",
    seed: int = 1,
    on_status=None,
) -> Image.Image:
    """Return a 1024x1024 RGB background with no lettering."""
    clean_prompt = (prompt or "").strip() or OCCASIONS.get(occasion, {}).get("prompt", "")
    if source == "Seasonal template":
        return render_template(occasion, seed)
    if source == "DALL-E":
        return _cover(render_dalle(clean_prompt, api_key))
    if source == "Free AI":
        return _cover(render_free(clean_prompt, seed, on_status))
    raise ValueError(f"Unknown background source: {source}")


def render_template(occasion: str, seed: int) -> Image.Image:
    rng = random.Random(seed)
    painter = _PAINTERS.get(occasion, _paint_holiday)
    image = painter(rng, CANVAS)
    return image.convert("RGB")


def render_dalle(prompt: str, api_key: str) -> Image.Image:
    key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
    if not key:
        raise ValueError(
            "DALL-E needs an OpenAI API key. Enter one in the form or set OPENAI_API_KEY. "
            "Seasonal templates and Free AI work without that key."
        )
    guarded = (
        f"{prompt} Square greeting-card illustration, no text, no letters, "
        "no watermark, no logo, no people."
    )
    response = http_call(
        "POST",
        OPENAI_IMAGES_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "dall-e-3",
            "prompt": guarded[:3900],
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json",
        },
        timeout=120,
    )
    if response.status_code >= 400:
        detail = _api_detail(response)
        raise ValueError(f"DALL-E request failed ({response.status_code}): {detail}")
    payload = response.json()
    data = (payload.get("data") or [{}])[0]
    if data.get("b64_json"):
        import base64

        raw = base64.b64decode(data["b64_json"])
        return Image.open(BytesIO(raw)).convert("RGB")
    if data.get("url"):
        image_response = http_call("GET", data["url"], timeout=60)
        image_response.raise_for_status()
        return Image.open(BytesIO(image_response.content)).convert("RGB")
    raise ValueError("DALL-E returned no image.")


def render_free(prompt: str, seed: int, on_status=None) -> Image.Image:
    """Try Pollinations, then the anonymous AI Horde queue."""
    _status(on_status, "Contacting the free image service...")
    try:
        return render_pollinations(prompt, seed)
    except Exception:
        _status(on_status, "Waiting for a free image worker. This can take a minute.")
        return render_horde(prompt)


def render_pollinations(prompt: str, seed: int) -> Image.Image:
    """Fast free generator. It often refuses traffic when the public queue is full."""
    response = http_call(
        "GET",
        POLLINATIONS_URL + requests.utils.quote(prompt[:500]),
        params={"width": 1024, "height": 1024, "seed": int(seed), "nologo": "true", "model": "flux"},
        timeout=25,
        headers={"User-Agent": "seasonal-greeting-image-tool"},
    )
    if response.status_code >= 400 or not response.content or "json" in response.headers.get("content-type", ""):
        raise ValueError("The fast free image service is busy.")
    try:
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as exc:
        raise ValueError("The fast free image service did not return an image.") from exc


def render_horde(prompt: str) -> Image.Image:
    """Anonymous AI Horde job. No personal API key."""
    headers = {"apikey": "0000000000", "Client-Agent": HORDE_AGENT}
    payload = {
        "prompt": f"{prompt[:800]} no text, no letters, no watermark, no logo",
        "params": {"width": 1024, "height": 1024, "steps": 20, "n": 1},
        "nsfw": False,
        "censor_nsfw": True,
        "r2": True,
    }
    response = http_call("POST", HORDE_URL, headers=headers, json=payload, timeout=40)
    if response.status_code == 400:
        payload["params"]["width"] = 512
        payload["params"]["height"] = 512
        response = http_call("POST", HORDE_URL, headers=headers, json=payload, timeout=40)
    if response.status_code >= 400:
        raise ValueError(f"Free AI could not start an image ({response.status_code}).")
    job_id = str((response.json() or {}).get("id") or "")
    if not job_id:
        raise ValueError("Free AI did not return a job id.")

    deadline = time.monotonic() + 100
    status_url = f"https://aihorde.net/api/v2/generate/status/{job_id}"
    while time.monotonic() < deadline:
        status = http_call("GET", status_url, headers=headers, timeout=30)
        if status.status_code >= 400:
            raise ValueError("Free AI lost the image job. Try again.")
        body = status.json()
        if body.get("faulted"):
            raise ValueError("The free image worker failed. Try again.")
        if body.get("done"):
            generations = body.get("generations") or []
            if not generations:
                raise ValueError("Free AI finished without an image.")
            return _open_horde_image(str(generations[0].get("img") or ""))
        time.sleep(3)
    http_call("DELETE", status_url, headers=headers, timeout=20)
    raise ValueError("The free image queue is busy. Try again, or use a seasonal template.")


def _open_horde_image(image_ref: str) -> Image.Image:
    if image_ref.startswith("http"):
        downloaded = http_call("GET", image_ref, timeout=60)
        if downloaded.status_code >= 400 or not downloaded.content:
            raise ValueError("Free AI created an image, but the download failed.")
        raw = downloaded.content
    else:
        import base64

        raw = base64.b64decode(image_ref)
    try:
        return Image.open(BytesIO(raw)).convert("RGB")
    except Exception as exc:
        raise ValueError("Free AI returned an unreadable image.") from exc


def _status(on_status, message: str) -> None:
    if on_status is not None:
        on_status(message)


def _api_detail(response: requests.Response) -> str:
    try:
        body = response.json()
    except Exception:
        return response.text[:300]
    error = body.get("error", body)
    if isinstance(error, dict):
        return str(error.get("message") or error)[:300]
    return str(error)[:300]


def _cover(image: Image.Image, size: tuple[int, int] = CANVAS) -> Image.Image:
    image = image.convert("RGB")
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def _gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        blend = y / max(1, height - 1)
        color = tuple(int(top[i] * (1 - blend) + bottom[i] * blend) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    return image.convert("RGBA")


def _glow(size: tuple[int, int], color: tuple[int, int, int], alpha: int, radius: float = 0.62) -> Image.Image:
    width, height = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = width / 2, height / 2
    max_r = math.hypot(cx, cy) * radius
    steps = 36
    for step in range(steps, 0, -1):
        ratio = step / steps
        reach = int(max_r * ratio)
        fade = int(alpha * (1 - ratio) ** 1.7)
        draw.ellipse(
            [cx - reach, cy - reach * 0.82, cx + reach, cy + reach * 0.82],
            fill=color + (fade,),
        )
    return overlay.filter(ImageFilter.GaussianBlur(18))


def _vignette(size: tuple[int, int], strength: int = 140) -> Image.Image:
    return _glow(size, (0, 0, 0), strength, radius=1.15).transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def _composite(base: Image.Image, *layers: Image.Image) -> Image.Image:
    image = base.convert("RGBA")
    for layer in layers:
        image = Image.alpha_composite(image, layer)
    return image


def _new_layer(size: tuple[int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    return layer, ImageDraw.Draw(layer)


def _edge_point(rng: random.Random, size: tuple[int, int], margin: int = 210) -> tuple[int, int]:
    width, height = size
    for _ in range(24):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        if abs(x - width / 2) > margin or abs(y - height / 2) > margin:
            return x, y
    return x, y


def _frame(draw: ImageDraw.ImageDraw, size: tuple[int, int], color: tuple[int, int, int, int]) -> None:
    width, height = size
    inset = 34
    draw.rectangle([inset, inset, width - inset, height - inset], outline=color, width=3)
    inner = inset + 10
    draw.rectangle([inner, inner, width - inner, height - inner], outline=color[:3] + (max(40, color[3] - 70),), width=1)


def _bokeh(rng: random.Random, size: tuple[int, int], colors: list[tuple[int, int, int]], count: int = 18) -> Image.Image:
    layer, draw = _new_layer(size)
    for _ in range(count):
        x, y = _edge_point(rng, size, 160)
        radius = rng.randint(18, 78)
        color = rng.choice(colors)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color + (rng.randint(28, 70),))
    return layer.filter(ImageFilter.GaussianBlur(6))


def _snowflake(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, color: tuple[int, int, int, int]) -> None:
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        draw.line(
            [(x, y), (x + radius * math.cos(rad), y + radius * math.sin(rad))],
            fill=color,
            width=2,
        )
    draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color)


def _heart(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, fill: tuple[int, int, int, int]) -> None:
    points = []
    for degree in range(0, 360, 10):
        t = math.radians(degree)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        points.append((cx + x * scale, cy - y * scale))
    draw.polygon(points, fill=fill)


def _star(draw: ImageDraw.ImageDraw, cx: int, cy: int, outer: int, fill: tuple[int, int, int, int], points: int = 5) -> None:
    coords = []
    inner = outer * 0.42
    for index in range(points * 2):
        radius = outer if index % 2 == 0 else inner
        angle = math.radians(-90 + index * 180 / points)
        coords.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    draw.polygon(coords, fill=fill)


def _scatter_dots(rng: random.Random, draw: ImageDraw.ImageDraw, size: tuple[int, int], color: tuple[int, int, int], count: int) -> None:
    for _ in range(count):
        x, y = _edge_point(rng, size, 180)
        radius = rng.randint(1, 3)
        alpha = rng.randint(120, 220)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color + (alpha,))


def _paint_holiday(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (10, 48, 58), (18, 24, 48))
    glow = _glow(size, (244, 214, 150), 90)
    lights, draw = _new_layer(size)
    _scatter_dots(rng, draw, size, (255, 236, 190), 70)
    _frame(draw, size, (232, 196, 120, 180))
    return _composite(base, glow, _bokeh(rng, size, [(232, 196, 120), (180, 220, 210), (255, 255, 255)], 16), lights)


def _paint_christmas(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (8, 42, 36), (28, 12, 22))
    glow = _glow(size, (186, 214, 186), 70)
    decor, draw = _new_layer(size)
    for _ in range(26):
        x, y = _edge_point(rng, size, 200)
        _snowflake(draw, x, y, rng.randint(8, 18), (255, 255, 255, rng.randint(140, 220)))
    _tree(draw, 170, 760, 210)
    _tree(draw, 860, 790, 160)
    _frame(draw, size, (226, 188, 110, 190))
    return _composite(base, glow, _bokeh(rng, size, [(255, 255, 255), (226, 188, 110)], 12), decor)


def _tree(draw: ImageDraw.ImageDraw, cx: int, base_y: int, height: int) -> None:
    foliage = (22, 92, 64, 230)
    for index, ratio in enumerate((1.0, 0.72, 0.46)):
        half = int(height * 0.28 * ratio)
        top = base_y - int(height * (0.42 + index * 0.22))
        bottom = top + int(height * 0.34 * ratio)
        draw.polygon([(cx, top), (cx - half, bottom), (cx + half, bottom)], fill=foliage)
    draw.rectangle([cx - 12, base_y - 20, cx + 12, base_y + 28], fill=(92, 58, 32, 230))
    _star(draw, cx, base_y - height + 8, 16, (245, 214, 120, 240))
    for dx, dy, color in (
        (-28, -40, (196, 48, 58, 230)),
        (24, -70, (232, 196, 90, 230)),
        (-8, -110, (70, 130, 180, 230)),
    ):
        draw.ellipse([cx + dx - 7, base_y + dy - 7, cx + dx + 7, base_y + dy + 7], fill=color)


def _paint_new_year(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (7, 14, 40), (18, 10, 32))
    glow = _glow(size, (255, 220, 150), 80, 0.5)
    decor, draw = _new_layer(size)
    for corner in ((150, 150), (870, 170), (160, 860), (880, 840)):
        _firework(draw, rng, corner[0], corner[1], rng.choice([(255, 214, 120), (255, 255, 255), (140, 190, 255)]))
    _scatter_dots(rng, draw, size, (255, 236, 200), 80)
    _frame(draw, size, (232, 196, 120, 170))
    return _composite(base, glow, decor)


def _firework(draw: ImageDraw.ImageDraw, rng: random.Random, x: int, y: int, color: tuple[int, int, int]) -> None:
    radius = rng.randint(50, 90)
    for angle in range(0, 360, 18):
        rad = math.radians(angle + rng.randint(-4, 4))
        end = (x + radius * math.cos(rad), y + radius * math.sin(rad))
        draw.line([(x, y), end], fill=color + (180,), width=2)
        orb = rng.randint(2, 4)
        draw.ellipse([end[0] - orb, end[1] - orb, end[0] + orb, end[1] + orb], fill=color + (230,))


def _paint_birthday(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (78, 28, 78), (46, 18, 48))
    glow = _glow(size, (255, 196, 214), 100)
    decor, draw = _new_layer(size)
    _balloon(draw, 150, 210, (232, 84, 122, 230), (255, 214, 120, 230))
    _balloon(draw, 230, 160, (92, 150, 214, 220), (255, 255, 255, 180))
    _balloon(draw, 860, 190, (244, 176, 74, 230), (255, 244, 214, 200))
    _balloon(draw, 790, 250, (126, 86, 176, 220), (255, 214, 230, 180))
    for _ in range(40):
        x, y = _edge_point(rng, size, 190)
        color = rng.choice([(255, 214, 120), (255, 150, 180), (140, 200, 255), (255, 255, 255)])
        draw.rectangle([x, y, x + rng.randint(6, 12), y + rng.randint(3, 7)], fill=color + (200,))
    _frame(draw, size, (245, 214, 170, 170))
    return _composite(base, glow, decor)


def _balloon(draw: ImageDraw.ImageDraw, x: int, y: int, fill: tuple[int, int, int, int], knot: tuple[int, int, int, int]) -> None:
    draw.ellipse([x - 36, y - 48, x + 36, y + 42], fill=fill)
    draw.polygon([(x - 8, y + 40), (x + 8, y + 40), (x, y + 54)], fill=knot)
    draw.line([(x, y + 54), (x + 10, y + 130)], fill=(255, 255, 255, 160), width=2)


def _paint_eid(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (8, 48, 46), (14, 22, 38))
    glow = _glow(size, (226, 196, 130), 70)
    decor, draw = _new_layer(size)
    draw.arc([700, 90, 900, 290], 200, 520, fill=(245, 220, 160, 230), width=8)
    _star(draw, 860, 150, 18, (245, 220, 160, 240))
    for index, x in enumerate((120, 220, 800, 900)):
        _lantern(draw, x, 800 if index < 2 else 820, 0.8 if index % 2 == 0 else 0.65)
    _scatter_dots(rng, draw, size, (245, 220, 160), 40)
    _frame(draw, size, (226, 196, 130, 180))
    return _composite(base, glow, decor)


def _lantern(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float) -> None:
    w, h = int(28 * scale), int(48 * scale)
    gold = (232, 196, 120, 230)
    draw.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=12, outline=gold, width=3)
    draw.line([(cx, cy - h), (cx, cy - h - 18)], fill=gold, width=2)
    draw.ellipse([cx - 5, cy - h - 26, cx + 5, cy - h - 16], outline=gold, width=2)
    draw.line([(cx - w + 6, cy), (cx + w - 6, cy)], fill=gold, width=2)


def _paint_diwali(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (18, 10, 48), (48, 18, 28))
    glow = _glow(size, (255, 176, 80), 110, 0.55)
    decor, draw = _new_layer(size)
    for x in (140, 250, 770, 890):
        _diya(draw, x, 860)
    for _ in range(50):
        x, y = _edge_point(rng, size, 200)
        _star(draw, x, y, rng.randint(3, 7), (255, 220, 150, rng.randint(140, 230)), points=4)
    _frame(draw, size, (244, 196, 110, 180))
    return _composite(base, glow, decor)


def _diya(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.ellipse([x - 34, y - 10, x + 34, y + 16], fill=(120, 62, 28, 230))
    draw.pieslice([x - 34, y - 18, x + 34, y + 14], 200, 340, fill=(168, 92, 40, 240))
    draw.polygon([(x, y - 48), (x - 10, y - 8), (x + 10, y - 8)], fill=(255, 186, 70, 230))
    draw.ellipse([x - 6, y - 22, x + 6, y - 8], fill=(255, 244, 200, 240))


def _paint_hanukkah(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (10, 32, 78), (8, 16, 40))
    glow = _glow(size, (190, 220, 255), 80)
    decor, draw = _new_layer(size)
    _star(draw, 160, 170, 48, (220, 230, 245, 210), points=6)
    _star(draw, 870, 800, 36, (220, 230, 245, 180), points=6)
    for index, x in enumerate(range(360, 700, 48)):
        height = 70 if index == 3 else 48
        draw.rectangle([x, 860 - height, x + 8, 868], fill=(236, 232, 214, 220))
        draw.ellipse([x - 3, 852 - height, x + 11, 866 - height], fill=(255, 206, 110, 230))
    _scatter_dots(rng, draw, size, (220, 230, 255), 40)
    _frame(draw, size, (186, 206, 230, 180))
    return _composite(base, glow, decor)


def _paint_halloween(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (24, 10, 42), (42, 18, 12))
    glow = _glow(size, (255, 140, 48), 60, 0.45)
    decor, draw = _new_layer(size)
    draw.ellipse([760, 80, 940, 260], fill=(255, 168, 72, 230))
    draw.ellipse([800, 100, 960, 250], fill=(24, 10, 42, 255))
    for bx, by in ((150, 180), (230, 250), (860, 760)):
        _bat(draw, bx, by, rng.randint(28, 42))
    _scatter_dots(rng, draw, size, (255, 190, 110), 30)
    _frame(draw, size, (232, 140, 64, 170))
    return _composite(base, glow, decor)


def _bat(draw: ImageDraw.ImageDraw, x: int, y: int, scale: int) -> None:
    body = (150, 110, 190, 230)
    draw.ellipse([x - scale * 0.18, y - scale * 0.12, x + scale * 0.18, y + scale * 0.16], fill=body)
    draw.polygon(
        [(x, y), (x - scale, y - scale * 0.15), (x - scale * 0.45, y + scale * 0.05), (x - scale * 0.2, y)],
        fill=body,
    )
    draw.polygon(
        [(x, y), (x + scale, y - scale * 0.15), (x + scale * 0.45, y + scale * 0.05), (x + scale * 0.2, y)],
        fill=body,
    )


def _paint_thanksgiving(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (74, 36, 16), (32, 16, 10))
    glow = _glow(size, (232, 164, 86), 100)
    decor, draw = _new_layer(size)
    for cx, cy, scale in ((140, 160, 1), (200, 240, 0.7), (880, 180, 0.9), (820, 820, 1), (150, 840, 0.8)):
        _leaf(draw, cx, cy, scale, rng.choice([(196, 84, 36, 220), (212, 140, 48, 220), (150, 72, 32, 210)]))
    _frame(draw, size, (226, 176, 110, 170))
    return _composite(base, glow, decor)


def _leaf(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float, fill: tuple[int, int, int, int]) -> None:
    draw.polygon(
        [
            (x, y - 40 * scale),
            (x + 22 * scale, y - 8 * scale),
            (x + 10 * scale, y + 28 * scale),
            (x - 10 * scale, y + 28 * scale),
            (x - 22 * scale, y - 8 * scale),
        ],
        fill=fill,
    )
    draw.line([(x, y - 30 * scale), (x, y + 24 * scale)], fill=(92, 42, 18, 180), width=2)


def _paint_valentine(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (82, 18, 48), (40, 8, 28))
    glow = _glow(size, (255, 170, 190), 100)
    decor, draw = _new_layer(size)
    for cx, cy, scale in ((150, 170, 2.2), (220, 250, 1.3), (870, 180, 2.0), (800, 820, 1.6), (160, 840, 1.4)):
        _heart(draw, cx, cy, scale, (214, 64, 104, 210))
    _scatter_dots(rng, draw, size, (255, 214, 224), 36)
    _frame(draw, size, (244, 190, 200, 170))
    return _composite(base, glow, decor)


def _paint_easter(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (186, 214, 176), (232, 220, 186))
    glow = _glow(size, (255, 252, 240), 120, 0.5)
    decor, draw = _new_layer(size)
    for cx, cy in ((140, 180), (240, 140), (860, 200), (780, 140), (160, 860), (880, 820)):
        draw.ellipse([cx - 16, cy - 10, cx + 16, cy + 10], fill=(255, 255, 255, 160))
        draw.ellipse([cx - 8, cy - 22, cx + 10, cy], fill=(244, 196, 214, 180))
    _scatter_dots(rng, draw, size, (255, 255, 255), 30)
    _frame(draw, size, (120, 110, 70, 140))
    return _composite(base, glow, decor)


def _paint_wedding(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (64, 24, 36), (28, 14, 22))
    glow = _glow(size, (255, 236, 214), 130, 0.58)
    decor, draw = _new_layer(size)
    for cx, cy in ((150, 170), (880, 180), (160, 850), (870, 830)):
        _sprig(draw, cx, cy, (244, 220, 190, 200))
    _frame(draw, size, (226, 196, 150, 180))
    return _composite(base, glow, _bokeh(rng, size, [(255, 236, 214), (226, 196, 150)], 10), decor)


def _sprig(draw: ImageDraw.ImageDraw, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    draw.line([(x, y + 50), (x, y - 50)], fill=color, width=2)
    for offset in (-30, -10, 10, 30):
        draw.ellipse([x - 16, y + offset - 6, x - 2, y + offset + 6], fill=color)
        draw.ellipse([x + 2, y + offset - 6, x + 16, y + offset + 6], fill=color)


def _paint_graduation(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (12, 28, 64), (10, 16, 36))
    glow = _glow(size, (226, 196, 120), 80)
    decor, draw = _new_layer(size)
    _mortarboard(draw, 160, 180)
    _mortarboard(draw, 860, 820, 0.8)
    for _ in range(30):
        x, y = _edge_point(rng, size, 200)
        color = rng.choice([(226, 196, 120), (255, 255, 255), (140, 180, 230)])
        draw.rectangle([x, y, x + 8, y + 4], fill=color + (190,))
    _frame(draw, size, (226, 196, 120, 180))
    return _composite(base, glow, decor)


def _mortarboard(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1) -> None:
    gold = (226, 196, 120, 230)
    w, h = int(54 * scale), int(16 * scale)
    draw.polygon([(x, y - h), (x + w, y), (x, y + h), (x - w, y)], outline=gold, width=3)
    draw.rectangle([x - 10, y, x + 10, y + int(36 * scale)], outline=gold, width=3)
    draw.line([(x + w - 8, y), (x + w + 8, y + int(40 * scale))], fill=gold, width=2)


def _paint_thanks(rng: random.Random, size: tuple[int, int]) -> Image.Image:
    base = _gradient(size, (28, 58, 48), (18, 32, 30))
    glow = _glow(size, (214, 206, 170), 110)
    decor, draw = _new_layer(size)
    for cx, cy in ((150, 180), (880, 200), (170, 840), (850, 820)):
        _sprig(draw, cx, cy, (186, 206, 170, 210))
    _scatter_dots(rng, draw, size, (236, 228, 196), 24)
    _frame(draw, size, (206, 196, 150, 160))
    return _composite(base, glow, decor)


_PAINTERS = {
    "Christmas": _paint_christmas,
    "New Year": _paint_new_year,
    "Birthday": _paint_birthday,
    "Eid": _paint_eid,
    "Diwali": _paint_diwali,
    "Hanukkah": _paint_hanukkah,
    "Halloween": _paint_halloween,
    "Thanksgiving": _paint_thanksgiving,
    "Valentine's Day": _paint_valentine,
    "Easter": _paint_easter,
    "Wedding": _paint_wedding,
    "Graduation": _paint_graduation,
    "Thank You": _paint_thanks,
}
