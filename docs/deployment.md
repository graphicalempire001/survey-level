# Deployment Guide

## Option 1 – Railway (Recommended for start)

1. Create account at https://railway.app
2. New Project → Deploy from GitHub repo
3. Add the environment variables from `.env.example`
4. Railway will detect Python and run `python -m src.main`

## Option 2 – Render

1. Create a new Web Service
2. Connect the GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python -m src.main`
5. Add environment variables

## Option 3 – Cheap VPS (Hetzner / Contabo / DigitalOcean)

```bash
# On the server
git clone <your-repo>
cd lumi-telegram-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env
python -m src.main
```

Use `systemd` or `pm2` to keep it running.

## Option 4 – Vercel (not recommended)

Possible with webhooks, but cold starts and timeouts make it painful for image + LLM workflows. Avoid for production.
