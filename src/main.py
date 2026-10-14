import os
import logging
from dotenv import load_dotenv
from .bot import create_application

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger = logging.getLogger(__name__)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")

    application = create_application(token)
    logger.info("Starting Lumi Telegram Bot...")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
