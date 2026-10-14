import os
import logging
import re
from telegram import Update
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am the Project Lumiere answering bot.\n\n"
        "Send me a technical question (with or without an image) and I will answer "
        "in the rigorous step-by-step style of the golden examples.\n\n"
        "Supported domains: Computer Science, Microelectronics, Mechanical & Civil Engineering.\n\n"
        "─── Admin only ───\n"
        "To add new knowledge: upload a PDF and put this in the caption:\n"
        "`admin <password> topic: <Domain Name>`\n"
        "Example: `admin secret123 topic: Computer Science`"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Normal Q&A (text or photo)."""
    message = update.message
    if not message:
        return

    user = message.from_user
    chat_id = message.chat_id
    text = message.text or message.caption or ""
    has_image = bool(message.photo)

    thinking = await message.reply_text("Analysing... please wait.")

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
            telegram_chat_id=chat_id,
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


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF uploads for knowledge ingestion (admin only)."""
    message = update.message
    if not message or not message.document:
        return

    doc = message.document
    caption = message.caption or ""

    # Only accept PDFs
    if doc.mime_type != "application/pdf" and not (doc.file_name or "").lower().endswith(".pdf"):
        await message.reply_text("Please upload a PDF file.")
        return

    # Parse caption: admin <password> topic: <topic>
    # Supports both "admin secret topic: Computer Science" and "admin secret topic Computer Science"
    match = re.search(
        r"admin\s+(\S+)\s+topic[:\s]+(.+)",
        caption,
        re.IGNORECASE,
    )

    if not match:
        await message.reply_text(
            "To add knowledge you must include the admin password and topic in the caption.\n\n"
            "Format:\n`admin <password> topic: <Domain Name>`\n\n"
            "Example:\n`admin mypassword topic: Mechanical Engineering`"
        )
        return

    password = match.group(1).strip()
    topic = match.group(2).strip()

    if not ADMIN_PASSWORD or password != ADMIN_PASSWORD:
        await message.reply_text("❌ Incorrect admin password.")
        return

    # Download the PDF
    status = await message.reply_text("📥 Downloading PDF and extracting knowledge… this may take a minute.")

    try:
        file = await context.bot.get_file(doc.file_id)
        pdf_bytes = await file.download_as_bytearray()

        success, msg = ingest_pdf(bytes(pdf_bytes), topic=topic)

        await status.edit_text(msg)

    except Exception as e:
        logger.exception("PDF ingestion failed")
        await status.edit_text(f"❌ Error while processing PDF:\n{str(e)[:300]}")


def create_application(token: str) -> Application:
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    return application
