# Seasonal Greeting Image Tool

A local web app for personalized greeting cards. It draws a seasonal background (or asks an image API for one), lays your message on top, and can send the result by email, WhatsApp, or X.

## What you can do

- Pick an occasion and generate a background from built-in artwork, OpenAI DALL-E, or a free no-key image API.
- Set the message, second line, font, size, color, alignment, and position.
- Preview and download the PNG.
- Send it with Python's `smtplib`, Twilio WhatsApp, or the X API when you add your own credentials.

Built-in templates do not need an API key. Free AI tries Pollinations, then the public [AI Horde](https://aihorde.net/) queue, which needs no key and can take about a minute. DALL-E needs your own OpenAI key.

## Setup

1. Install Python 3.10 or newer.
2. In this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

3. Open http://127.0.0.1:7860

`run.bat` creates the virtual environment, installs the libraries, and starts the app.

## Credentials

Leave the form fields blank to read the value from `.env`. Nothing in the form is written back to disk.

| Service | Used for | Variables |
| --- | --- | --- |
| OpenAI | DALL-E backgrounds | `OPENAI_API_KEY` |
| SMTP | Email with the PNG attached | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` |
| Twilio | WhatsApp | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` |
| X | Post the image | `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET` |

Gmail needs an app password and `smtp.gmail.com` on port 587. Twilio can only attach an image from a public URL, so **Attach the image** uploads that PNG to a temporary public file host for the send. Leave it off to send the greeting text only. **Open WhatsApp** and **Open X compose** share the words in the browser; they do not upload the file.

## Project layout

- `app.py` — Gradio interface
- `greeting/backgrounds.py` — templates, DALL-E, and free AI
- `greeting/overlay.py` — Pillow text
- `greeting/sharing.py` — email, WhatsApp, and X
- `outputs/` — saved cards (not committed)

## Suggested post

Just completed my Seasonal Greeting Image Tool Agent! Generate, customize, and share festive greetings with AI—quick and easy! #rehancodingwithai #codingwithai
