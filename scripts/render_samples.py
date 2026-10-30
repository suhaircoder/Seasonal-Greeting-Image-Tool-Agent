"""Render one card per occasion so the artwork can be checked locally."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from greeting.backgrounds import generate_background
from greeting.overlay import TextStyle, apply_text, list_fonts
from greeting.presets import OCCASIONS
from greeting.sharing import send_email, whatsapp_link, x_intent_link

OUT = Path(__file__).resolve().parents[1] / "outputs"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    print("fonts", ", ".join(list_fonts()))
    last = None
    for name, preset in OCCASIONS.items():
        background = generate_background("Seasonal template", name, "", "", seed=7)
        card = apply_text(
            background,
            TextStyle(
                message=preset["message"],
                subtitle=preset["subtitle"],
                font_name="Georgia",
                font_size=76,
            ),
        )
        slug = name.lower().replace("'", "").replace(" ", "_")
        card.save(OUT / f"{slug}.png")
        last = background
        print(f"{name}: {card.size[0]}x{card.size[1]}")

    try:
        apply_text(last, TextStyle(message="   "))
    except ValueError as exc:
        print(f"empty message: {exc}")
    try:
        generate_background("DALL-E", "Christmas", "tree", "", 1)
    except ValueError as exc:
        print(f"dalle without key: {exc}")
    try:
        send_email("", "", 587, "", "", "", "", "", "")
    except ValueError as exc:
        print(f"email without image: {exc}")
    print(whatsapp_link("Hello there"))
    print(x_intent_link("Hello there"))


if __name__ == "__main__":
    main()
