"""Telegram bot entrypoint for Shinony character generation."""

from __future__ import annotations

import logging
import os
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown

from .generator import CharacterGenerator

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with basic usage instructions."""
    await update.message.reply_text(
        "Привет! Отправь /generate, чтобы получить случайного шиноби.",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with help information."""
    await update.message.reply_text(
        "Команды:\n"
        "/generate — создать нового персонажа;\n"
        "/start — краткая справка."
    )


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a new character sheet and send it to the user."""
    generator = CharacterGenerator(base_path=context.bot_data.get("base_path", "."))
    sheet = generator.generate()
    formatted = generator.format_sheet(sheet)
    escaped = escape_markdown(formatted, version=2)
    await update.message.reply_text(
        f"```\n{escaped}\n```",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


def main(token: Optional[str] = None, base_path: str = ".") -> None:
    """Run the Telegram bot."""
    token = token or os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is required to run the bot."
        )
    application: Application = ApplicationBuilder().token(token).build()
    application.bot_data["base_path"] = base_path

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate))

    logger.info("Starting Shinony bot")
    application.run_polling()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
