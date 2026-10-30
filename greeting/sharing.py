"""Share a greeting by email, WhatsApp, or X (Twitter)."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

from greeting.net import http_call


def send_email(
    image_path: str,
    host: str,
    port: int,
    username: str,
    password: str,
    sender: str,
    recipients: str,
    subject: str,
    body: str,
) -> str:
    path = _require_image(image_path)
    smtp_host = _pick(host, "SMTP_HOST") or "smtp.gmail.com"
    smtp_port = int(_pick(str(port or ""), "SMTP_PORT") or 587)
    smtp_user = _pick(username, "SMTP_USERNAME")
    smtp_password = _pick(password, "SMTP_PASSWORD")
    from_addr = _pick(sender, "SMTP_FROM") or smtp_user
    to_list = _split_addresses(recipients)
    if not smtp_user or not smtp_password or not from_addr:
        raise ValueError("Email needs an SMTP username, password, and from address.")
    if not to_list:
        raise ValueError("Enter at least one recipient email address.")

    message = EmailMessage()
    message["Subject"] = subject.strip() or "A greeting for you"
    message["From"] = from_addr
    message["To"] = ", ".join(to_list)
    message.set_content(body.strip() or "Sending you this greeting.")
    message.add_attachment(
        path.read_bytes(),
        maintype="image",
        subtype="png",
        filename="greeting.png",
    )
    with smtplib.SMTP(smtp_host, smtp_port, timeout=40) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)
    return f"Email sent to {len(to_list)} recipient{'s' if len(to_list) != 1 else ''}."


def send_whatsapp(
    image_path: str,
    account_sid: str,
    auth_token: str,
    from_number: str,
    recipients: str,
    body: str,
    attach_image: bool,
) -> str:
    path = _require_image(image_path)
    sid = _pick(account_sid, "TWILIO_ACCOUNT_SID")
    token = _pick(auth_token, "TWILIO_AUTH_TOKEN")
    sender = _whatsapp_addr(_pick(from_number, "TWILIO_WHATSAPP_FROM"))
    numbers = [_whatsapp_addr(item) for item in _split_addresses(recipients)]
    if not sid or not token:
        raise ValueError("WhatsApp needs a Twilio Account SID and Auth Token.")
    if not sender:
        raise ValueError("Enter the Twilio WhatsApp sender number, including the country code.")
    if not numbers:
        raise ValueError("Enter at least one WhatsApp number, including the country code.")

    media_url = _upload_temp(path) if attach_image else ""
    endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    sent = 0
    errors: list[str] = []
    for number in numbers:
        payload = {"From": sender, "To": number, "Body": body.strip() or "A greeting for you"}
        if media_url:
            payload["MediaUrl"] = media_url
        response = http_call("POST", endpoint, data=payload, auth=(sid, token), timeout=40)
        if response.status_code >= 400:
            errors.append(f"{number}: {_response_message(response)}")
        else:
            sent += 1
    if errors and not sent:
        raise ValueError("WhatsApp send failed. " + " ".join(errors))
    summary = f"WhatsApp message sent to {sent} recipient{'s' if sent != 1 else ''}."
    if media_url:
        summary += " The image was attached from a temporary public link."
    else:
        summary += " Text only — turn on image attach to include the card."
    if errors:
        summary += " Some numbers failed: " + " ".join(errors)
    return summary


def post_to_x(image_path: str, caption: str, api_key: str, api_secret: str, access_token: str, access_secret: str) -> str:
    path = _require_image(image_path)
    key = _pick(api_key, "TWITTER_API_KEY")
    secret = _pick(api_secret, "TWITTER_API_SECRET")
    token = _pick(access_token, "TWITTER_ACCESS_TOKEN")
    token_secret = _pick(access_secret, "TWITTER_ACCESS_TOKEN_SECRET")
    if not all([key, secret, token, token_secret]):
        raise ValueError(
            "Posting to X needs an API key, API secret, access token, and access token secret "
            "from a user-context app."
        )
    text = (caption or "").strip()
    if not text:
        raise ValueError("Enter a caption for the post.")
    if len(text) > 280:
        raise ValueError("Captions on X must be 280 characters or fewer.")

    auth = OAuth1(key, secret, token, token_secret)
    with path.open("rb") as image_file:
        upload = http_call(
            "POST",
            "https://upload.twitter.com/1.1/media/upload.json",
            auth=auth,
            files={"media": image_file},
            timeout=60,
        )
    if upload.status_code >= 400:
        raise ValueError(f"Image upload failed ({upload.status_code}): {_response_message(upload)}")
    media_id = str(upload.json().get("media_id_string") or upload.json().get("media_id") or "")
    if not media_id:
        raise ValueError("X accepted the upload but did not return a media id.")
    tweet = http_call(
        "POST",
        "https://api.twitter.com/2/tweets",
        auth=auth,
        json={"text": text, "media": {"media_ids": [media_id]}},
        timeout=40,
    )
    if tweet.status_code >= 400:
        raise ValueError(f"Post failed ({tweet.status_code}): {_response_message(tweet)}")
    tweet_id = (tweet.json().get("data") or {}).get("id", "")
    return f"Posted to X. Tweet id: {tweet_id or 'created'}."


def whatsapp_link(message: str) -> str:
    text = requests.utils.quote((message or "A greeting for you").strip())
    return f"https://wa.me/?text={text}"


def x_intent_link(caption: str) -> str:
    text = requests.utils.quote((caption or "").strip())
    return f"https://twitter.com/intent/tweet?text={text}"


def _upload_temp(path: Path) -> str:
    """Twilio must fetch media from a public URL, so the card is uploaded for that send."""
    with path.open("rb") as image_file:
        response = http_call(
            "POST",
            "https://0x0.st",
            files={"file": (path.name, image_file, "image/png")},
            timeout=60,
            headers={"User-Agent": "seasonal-greeting-image-tool"},
        )
    if response.status_code >= 400 or not response.text.strip().startswith("http"):
        raise ValueError(
            "Could not publish the image for WhatsApp. Send text only, or try the attach option again."
        )
    return response.text.strip()


def _require_image(image_path: str) -> Path:
    path = Path(image_path or "")
    if not path.is_file():
        raise ValueError("Create a greeting image before sharing it.")
    return path


def _pick(value: str, env_name: str) -> str:
    text = (value or "").strip()
    return text or os.getenv(env_name, "").strip()


def _split_addresses(raw: str) -> list[str]:
    chunks = raw.replace(";", ",").replace("\n", ",").split(",")
    return [item.strip() for item in chunks if item.strip()]


def _whatsapp_addr(value: str) -> str:
    text = (value or "").strip().replace(" ", "")
    if not text:
        return ""
    if text.startswith("whatsapp:"):
        return text
    if not text.startswith("+"):
        text = "+" + text
    return f"whatsapp:{text}"


def _response_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except Exception:
        return response.text[:240]
    if isinstance(body, dict):
        message = body.get("message") or body.get("detail")
        if not message and isinstance(body.get("errors"), list) and body["errors"]:
            message = body["errors"][0].get("message")
        if not message and isinstance(body.get("error"), dict):
            message = body["error"].get("message")
        return str(message or body)[:240]
    return str(body)[:240]
