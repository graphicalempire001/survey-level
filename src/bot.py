import os
import logging
import re
from telegram import Update, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from .llm import ask_gemini
from .db import save_conversation
from .knowledge import ingest_pdf

logger = logging.getLogger(__name__)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


# ───────────────────────── Helpers ─────────────────────────

def is_admin(password: str) -> bool:
    return bool(ADMIN_PASSWORD) and password == ADMIN_PASSWORD


async def set_bot_commands(application: Application):
    """Register clean menu commands that appear when user types / """
    commands = [
        BotCommand("start", "Start the bot & show help"),
        BotCommand("help", "How to use the bot"),
        BotCommand("menu", "Show control panel"),
        BotCommand("add", "Admin: add PDF knowledge (reply to a PDF)"),
    ]
    await application.bot.set_my_commands(commands)


# ───────────────────────── Commands ─────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📚 Help"), KeyboardButton("🎛️ Menu")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Hello! I am the **Project Lumiere** answering bot.\n\n"
        "Just send me a technical question (with or without an image) and I will answer "
        "in the rigorous step-by-step style.\n\n"
        "Supported domains:\n"
        "• Computer Science\n"
        "• Microelectronics / Electrical\n"
        "• Mechanical Engineering\n"
        "• Civil Engineering\n\n"
        "Type /menu for the control panel.",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use*\n\n"
        "1. Send any technical question as text\n"
        "2. Or send a photo/diagram + question in the caption\n"
        "3. I will reply with a detailed step-by-step solution\n\n"
        "─── *Admin only* ───\n"
        "To add new knowledge from a PDF:\n"
        "1. Upload the PDF\n"
        "2. *Reply* to that PDF message with:\n"
        "`/add <password> <topic>`\n\n"
        "Example:\n"
        "`/add MySecret123 Computer Science`",
        parse_mode="Markdown",
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📚 Help"), KeyboardButton("ℹ️ About")],
        [KeyboardButton("➕ Add Knowledge (Admin)")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🎛️ *Control Panel*\n\n"
        "Choose an option below or just send a question.",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Project Lumiere Bot*\n\n"
        "Answers technical questions in the rigorous golden-example style "
        "(detailed step-by-step + precise image reading).\n\n"
        "Powered by Gemini 3.8 Flash + Supabase knowledge base.",
        parse_mode="Markdown",
    )


# ───────────────────────── Admin: Add knowledge ─────────────────────────

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command.
    Usage (as a reply to a PDF):
        /add <password> <topic>
    Example:
        /add MySecret123 Mechanical Engineering
    """
    message = update.message
    if not message:
        return

    # Must be a reply to a document
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text(
            "⚠️ Please *reply* to a PDF message with this command.\n\n"
            "Usage:\n`/add <password> <topic>`\n\n"
            "Example:\n`/add MySecret123 Computer Science`",
            parse_mode="Markdown",
        )
        return

    doc = message.reply_to_message.document
    is_pdf = (
        doc.mime_type == "application/pdf"
        or (doc.file_name or "").lower().endswith(".pdf")
    )
    if not is_pdf:
        await message.reply_text("The replied message must be a PDF file.")
        return

    # Parse arguments: /add <password> <topic...>
    args = context.args
    if not args or len(args) < 2:
        await message.reply_text(
            "Usage:\n`/add <password> <topic>`\n\n"
            "Example:\n`/add MySecret123 Computer Science`",
            parse_mode="Markdown",
        )
        return

    password = args[0]
    topic = " ".join(args[1:]).strip()

    if not is_admin(password):
        await message.reply_text("❌ Incorrect admin password.")
        return

    status = await message.reply_text(
        "📥 Downloading PDF and extracting knowledge… this may take a minute."
    )

    try:
        file = await context.bot.get_file(doc.file_id)
        pdf_bytes = await file.download_as_bytearray()

        success, msg = ingest_pdf(bytes(pdf_bytes), topic=topic)
        await status.edit_text(msg)

    except Exception as e:
        logger.exception("PDF ingestion failed")
        await status.edit_text(f"❌ Error while processing PDF:\n{str(e)[:300]}")


# ───────────────────────── Normal Q&A ─────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle normal text / photo questions + keyboard buttons."""
    message = update.message
    if not message:
        return

    text = (message.text or message.caption or "").strip()

    # Handle keyboard buttons
    if text in ["📚 Help", "Help"]:
        await help_command(update, context)
        return
    if text in ["🎛️ Menu", "Menu"]:
        await menu_command(update, context)
        return
    if text in ["ℹ️ About", "About"]:
        await about_command(update, context)
        return
    if text in ["➕ Add Knowledge (Admin)", "Add Knowledge (Admin)"]:
        await message.reply_text(
            "To add knowledge:\n"
            "1. Upload a PDF\n"
            "2. Reply to that PDF with:\n"
            "`/add <password> <topic>`\n\n"
            "Example:\n`/add MySecret123 Computer Science`",
            parse_mode="Markdown",
        )
        return

    # Normal question
    user = message.from_user
    has_image = bool(message.photo)

    thinking = await message.reply_text("Analysing… please wait.")

    image_bytes = None
    mime_type = "image/jpeg"

    if has_image:
        photo = message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

    try:
        reply = await ask_gemini(text, image_bytes, mime_type)

        save_conversation(
            telegram_user_id=user.id,
            telegram_chat_id=message.chat_id,
            message_id=message.message_id,
            user_text=text,
            has_image=has_image,
            image_url=None,
            bot_reply=reply,
        )

        await thinking.edit_text(reply)

    except Exception as e:
        logger.exception("Error processing message")
        await thinking.edit_text(
            f"Sorry, an error occurred while processing your request.\n\nDetails: {str(e)[:200]}"
        )


# ───────────────────────── Application setup ─────────────────────────

def create_application(token: str) -> Application:
    application = Application.builder().token(token).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("add", add_command))

    # Normal messages & photos
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    # Register menu on startup
    application.post_init = set_bot_commands

    return application
