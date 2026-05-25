"""
Deal Cracker Telegram bot entry point.

Run from project root:
    python app/telegram_bot.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure deal-cracker root is on sys.path when run as script
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.agent import get_agent

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "👋 Welcome to Deal Cracker!\n\n"
            "I find the best nearby deals nearby for you.\n\n"
            "Try:\n"
            "• I want coffee\n"
            "• Cheap burgers nearby\n"
            "• Any cinema deals?\n"
            "• Need shoes under £50\n"
            "• Best pizza offers tonight"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "📖 Deal Cracker help\n\n"
            "Just message me naturally — I'll detect what you need and show "
            "the top 3 cheapest nearby offers.\n\n"
            "Categories: coffee, burgers, food, pizza, cinema, shopping, fashion.\n\n"
            "Commands: /start /help"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    logger.info("User message: %s", user_text)

    agent = get_agent()
    reply = await agent.process_message_async(user_text)
    await update.message.reply_text(reply)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print(
            "ERROR: TELEGRAM_BOT_TOKEN is not set.\n"
            "Copy .env.example to .env and add your bot token from @BotFather."
        )
        sys.exit(1)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Deal Cracker bot is running (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
