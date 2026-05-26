from __future__ import annotations

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")

import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown

from app.agent import get_agent
from app.formatter import format_deal_card, format_no_deals, format_plain_list, format_results_header

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    name = update.effective_user.first_name if update.effective_user else "there"
    safe_name = escape_markdown(name, version=1)
    await update.message.reply_text(
        f"👋 Hey {safe_name}! I'm *Deal Cracker* — your Glasgow deals assistant.\n\n"
        "Message me naturally and I'll find live offers:\n"
        "• blacksheep coffee\n"
        "• student offers at Starbucks\n"
        "• Primark offers\n"
        "• ticket to the airport\n\n"
        "Type /help for more.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "🔍 *Deal Cracker*\n\n"
        "Just type what you want — I'll find the best deals with links.\n\n"
        "*Examples*\n"
        "• Cheap burgers nearby\n"
        "• Any cinema deals?\n"
        "• Need shoes under £50\n\n"
        "Commands: /start /help",
        parse_mode=ParseMode.MARKDOWN,
    )


async def _send_deal_cards(update: Update, headline: str, deals: list, query: str = "") -> None:
    if not update.message:
        return
    if not deals:
        await update.message.reply_text(
            format_no_deals(query),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await update.message.reply_text(
        format_results_header(headline, len(deals)),
        parse_mode=ParseMode.MARKDOWN,
    )

    for deal in deals:
        card = format_deal_card(deal)
        try:
            await update.message.reply_text(card, parse_mode=ParseMode.MARKDOWN)
        except Exception as exc:
            logger.warning("Markdown send failed, using plain text: %s", exc)
            plain = format_plain_list([deal], "")
            await update.message.reply_text(plain)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    logger.info("User message: %s", user_text)

    if not user_text:
        await update.message.reply_text(
            "👋 Ask me about coffee, food, fashion, cinema, or travel deals!"
        )
        return

    await update.message.reply_text(
        f"🔍 Searching for *{escape_markdown(user_text, version=1)}*...",
        parse_mode=ParseMode.MARKDOWN,
    )

    agent = get_agent()
    response = await agent.process_message_async(user_text)

    if response.openclaw_intro:
        await update.message.reply_text(
            response.openclaw_intro,
            parse_mode=ParseMode.MARKDOWN,
        )

    await _send_deal_cards(update, response.headline, response.deals, response.query)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set.")
        sys.exit(1)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Deal Cracker bot is running (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
