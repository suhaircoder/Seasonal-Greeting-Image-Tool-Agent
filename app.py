"""Web interface for the Seasonal Greeting Image Tool."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from greeting.backgrounds import SOURCES, generate_background
from greeting.overlay import ALIGNMENTS, POSITIONS, TextStyle, apply_text, list_fonts
from greeting.presets import OCCASIONS, PROJECT_CAPTION, occasion_names
from greeting.sharing import post_to_x, send_email, send_whatsapp, whatsapp_link, x_intent_link

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
load_dotenv(ROOT / ".env")


def build_app() -> gr.Blocks:
    fonts = list_fonts()
    default_occasion = "Christmas"
    preset = OCCASIONS[default_occasion]

    with gr.Blocks(title="Seasonal Greeting Image Tool") as demo:
        gr.Markdown(
            """
            # Seasonal Greeting Image Tool
            Create a festive card, write your own message, then download it or share it
            by email, WhatsApp, or X. Built-in artwork works with no API key.
            """
        )
        image_path = gr.State("")

        with gr.Row():
            with gr.Column(scale=5):
                occasion = gr.Dropdown(occasion_names(), value=default_occasion, label="Occasion")
                source = gr.Radio(
                    list(SOURCES),
                    value="Seasonal template",
                    label="Background",
                    info="Templates are instant and need no key. DALL-E needs your OpenAI key in the field below. Free AI needs internet and can take about a minute.",
                )
                prompt = gr.Textbox(label="Image prompt", lines=3, value=preset["prompt"])
                api_key = gr.Textbox(
                    label="OpenAI API key",
                    type="password",
                    placeholder="Required only for DALL-E. Paste your key here.",
                )
                with gr.Row():
                    seed = gr.Slider(1, 9999, value=7, step=1, label="Design seed")
                    shuffle = gr.Checkbox(label="New variation", value=False)
                message = gr.Textbox(label="Message", value=preset["message"])
                subtitle = gr.Textbox(label="Second line", value=preset["subtitle"])
                with gr.Row():
                    font_name = gr.Dropdown(fonts, value=fonts[0], label="Font")
                    font_size = gr.Slider(28, 120, value=76, step=1, label="Font size")
                with gr.Row():
                    text_color = gr.ColorPicker(value="#FFF8EA", label="Text color")
                    position = gr.Dropdown(list(POSITIONS), value="Center", label="Position")
                    align = gr.Dropdown(list(ALIGNMENTS), value="Center", label="Alignment")
                with gr.Row():
                    outline = gr.Checkbox(value=True, label="Outline")
                    panel = gr.Checkbox(value=True, label="Contrast panel behind text")
                create = gr.Button("Create greeting", variant="primary")
            with gr.Column(scale=6):
                preview = gr.Image(label="Preview", type="pil", height=560, format="png", buttons=["download", "fullscreen"])
                download = gr.File(label="Download PNG")
                status = gr.Textbox(label="Status", interactive=False)

        with gr.Accordion("Share", open=False):
            share_note = gr.Markdown(
                "Create a card first. Leave a credential blank to use the matching value from `.env`."
            )
            share_body = gr.Textbox(label="Message to send with the image", lines=3, value=_share_text(preset["message"], preset["subtitle"]))
            with gr.Tab("Email"):
                with gr.Row():
                    smtp_host = gr.Textbox(label="SMTP host", value=os.getenv("SMTP_HOST", "smtp.gmail.com"))
                    smtp_port = gr.Number(label="Port", value=int(os.getenv("SMTP_PORT", "587")), precision=0)
                with gr.Row():
                    smtp_user = gr.Textbox(label="SMTP username")
                    smtp_password = gr.Textbox(label="SMTP password", type="password")
                smtp_from = gr.Textbox(label="From address")
                email_to = gr.Textbox(label="To", placeholder="friend@example.com, family@example.com")
                email_subject = gr.Textbox(label="Subject", value="A greeting for you")
                send_email_btn = gr.Button("Send email")
            with gr.Tab("WhatsApp"):
                gr.Markdown(
                    "Twilio sends the message. Attaching the image uploads the PNG to a temporary public link so Twilio can fetch it."
                )
                with gr.Row():
                    twilio_sid = gr.Textbox(label="Twilio Account SID")
                    twilio_token = gr.Textbox(label="Twilio Auth Token", type="password")
                twilio_from = gr.Textbox(label="From number", placeholder="whatsapp:+14155238886")
                wa_to = gr.Textbox(label="Recipients", placeholder="+15551234567, +447700900123")
                attach_image = gr.Checkbox(value=False, label="Attach the image (uploads a temporary public copy)")
                with gr.Row():
                    send_wa_btn = gr.Button("Send WhatsApp")
                    open_wa = gr.Button("Open WhatsApp with the message")
                wa_link = gr.Markdown()
            with gr.Tab("X / Twitter"):
                gr.Markdown("Direct posting uses your own X API keys. The browser button opens a compose window with the caption.")
                caption = gr.Textbox(label="Caption", lines=3, value=_share_text(preset["message"], preset["subtitle"]))
                use_project_caption = gr.Button("Use project announcement caption")
                with gr.Row():
                    x_key = gr.Textbox(label="API key")
                    x_secret = gr.Textbox(label="API secret", type="password")
                with gr.Row():
                    x_token = gr.Textbox(label="Access token")
                    x_token_secret = gr.Textbox(label="Access token secret", type="password")
                with gr.Row():
                    post_x_btn = gr.Button("Post image to X")
                    open_x = gr.Button("Open X compose")
                x_link = gr.Markdown()

        occasion.change(_on_occasion, inputs=occasion, outputs=[prompt, message, subtitle, share_body, caption])
        create.click(
            _create,
            inputs=[
                occasion, source, prompt, api_key, seed, shuffle,
                message, subtitle, font_name, font_size, text_color,
                position, align, outline, panel,
            ],
            outputs=[preview, download, image_path, status, share_body, caption],
        )
        send_email_btn.click(
            _email,
            inputs=[image_path, smtp_host, smtp_port, smtp_user, smtp_password, smtp_from, email_to, email_subject, share_body],
            outputs=status,
        )
        send_wa_btn.click(
            _whatsapp,
            inputs=[image_path, twilio_sid, twilio_token, twilio_from, wa_to, share_body, attach_image],
            outputs=status,
        )
        open_wa.click(lambda text: _clickable(whatsapp_link(text), "Open this link in WhatsApp"), inputs=share_body, outputs=wa_link)
        use_project_caption.click(lambda: PROJECT_CAPTION, outputs=caption)
        post_x_btn.click(
            _post_x,
            inputs=[image_path, caption, x_key, x_secret, x_token, x_token_secret],
            outputs=status,
        )
        open_x.click(lambda text: _clickable(x_intent_link(text), "Open this link to compose on X"), inputs=caption, outputs=x_link)
        demo.load(
            _create,
            inputs=[
                occasion, source, prompt, api_key, seed, shuffle,
                message, subtitle, font_name, font_size, text_color,
                position, align, outline, panel,
            ],
            outputs=[preview, download, image_path, status, share_body, caption],
        )

    return demo


def _on_occasion(name: str):
    preset = OCCASIONS.get(name) or next(iter(OCCASIONS.values()))
    text = _share_text(preset["message"], preset["subtitle"])
    return preset["prompt"], preset["message"], preset["subtitle"], text, text


def _create(occasion, source, prompt, api_key, seed, shuffle, message, subtitle, font_name, font_size, text_color, position, align, outline, panel, progress=gr.Progress()):
    try:
        chosen_seed = int(seed)
        if shuffle:
            chosen_seed = int.from_bytes(os.urandom(2), "big") or 1
        background = generate_background(
            source,
            occasion,
            prompt,
            api_key,
            chosen_seed,
            on_status=lambda message: progress(0.4, desc=message),
        )
        card = apply_text(
            background,
            TextStyle(
                message=message,
                subtitle=subtitle,
                font_name=font_name,
                font_size=int(font_size),
                color=text_color or "#FFF8EA",
                position=position,
                align=align,
                outline=bool(outline),
                panel=bool(panel),
            ),
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / f"greeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    card.save(filename, format="PNG")
    share_text = _share_text(message, subtitle)
    return card, str(filename), str(filename), f"Greeting saved. Design seed {chosen_seed}.", share_text, share_text


def _email(image_path, host, port, username, password, sender, recipients, subject, body):
    try:
        return send_email(image_path, host, int(port or 587), username, password, sender, recipients, subject, body)
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def _whatsapp(image_path, sid, token, sender, recipients, body, attach):
    try:
        return send_whatsapp(image_path, sid, token, sender, recipients, body, bool(attach))
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def _post_x(image_path, caption, api_key, api_secret, access_token, access_secret):
    try:
        return post_to_x(image_path, caption, api_key, api_secret, access_token, access_secret)
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def _clickable(url: str, label: str) -> str:
    return f"[{label}]({url})"


def _share_text(message: str, subtitle: str) -> str:
    message = (message or "").strip()
    subtitle = (subtitle or "").strip()
    if message and subtitle:
        return f"{message} — {subtitle}"
    return message or subtitle or "A greeting for you"


if __name__ == "__main__":
    theme = gr.themes.Soft(primary_hue="green", secondary_hue="amber", neutral_hue="stone")
    build_app().launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=False,
        theme=theme,
        show_error=True,
    )
