# Lumi Telegram Bot – Project Lumiere Style

A Telegram bot that answers technical questions in the rigorous **Project Lumiere** style (detailed step-by-step solutions, precise image reading, exact answer formats).

## Features

- Accepts text + images (photos, diagrams, circuits, grids, etc.)
- Uses **Google Gemini Flash** (free tier, excellent vision)
- Stores all golden examples + conversations in **Supabase**
- Continuous learning: verified answers can be promoted to golden examples
- **Admin PDF upload**: upload a PDF + admin password + topic → automatically extracts knowledge and adds it to the database
- Clean architecture ready for expansion

## Stack

- Python 3.11+
- `python-telegram-bot` (async)
- Google Gemini API (vision)
- Supabase (PostgreSQL + Storage)
- Ready for Railway / Render / VPS

## Quick Start

1. Clone the repo
2. Copy `.env.example` → `.env` and fill in the values
3. Install dependencies: `pip install -r requirements.txt`
4. Run the SQL in `sql/schema.sql` inside your Supabase project
5. Start the bot: `python -m src.main`

## Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
GEMINI_API_KEY=your_google_ai_studio_key
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_key
ADMIN_PASSWORD=your_strong_admin_password_here
```

## Hosting Recommendations

- **Development / low traffic**: Railway or Render (free tier is enough)
- **Production / heavy use**: Cheap VPS (Hetzner CX22 ~€4/month is excellent)
- Vercel is possible with webhooks but not recommended (cold starts + timeouts)

## Project Structure

```
lumi-telegram-bot/
├── src/
│   ├── main.py              # Entry point
│   ├── bot.py               # Telegram handlers (Q&A + PDF admin)
│   ├── llm.py               # Gemini client + prompt building
│   ├── knowledge.py         # PDF extraction + structuring + DB insert
│   ├── db.py                # Supabase client
│   └── prompts.py           # System prompt + few-shot logic
├── sql/
│   └── schema.sql           # Database schema
├── docs/
│   └── deployment.md
├── .env.example
├── requirements.txt
└── README.md
```

## Continuous Learning

Every conversation is saved. Later you can mark good answers and promote them into the `golden_examples` table so the bot becomes stronger over time.

## Admin: Adding New Knowledge via PDF

1. Set a strong `ADMIN_PASSWORD` in your `.env`.
2. In Telegram, **upload a PDF**.
3. **Reply** to that PDF message with:

```
/add yourpassword Computer Science
```

or

```
/add yourpassword Microelectronics
```

4. The bot will:
   - Check the password
   - Extract all text from the PDF
   - Ask Gemini to structure it as a golden example
   - Save it into the `golden_examples` table under the topic you specified

The new knowledge is immediately available for future answers.

You can also open the clean menu with `/menu`.
