"""Telegram bot entrypoint for Shinony character generation."""

from __future__ import annotations


import html

import logging
import os
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
from telegram.helpers import escape_markdown


def _patch_python_telegram_bot() -> None:
    """Work around python-telegram-bot <21 bug on Python 3.13."""

    try:  # pragma: no cover - depends on optional dependency internals
        from telegram.ext import _applicationbuilder as _appbuilder
        from telegram.ext import _updater as _updater_module
    except Exception:  # library missing or layout changed
        return

    updater_cls = getattr(_updater_module, "Updater", None)
    if updater_cls is None:
        return

    slots = getattr(updater_cls, "__slots__", ())
    if not isinstance(slots, tuple):
        return

    # python-telegram-bot 20.x forgets to declare this slot, which became
    # fatal on Python 3.13 because attribute assignment now errors out.
    missing_slot = "_Updater__polling_cleanup_cb"
    if missing_slot in slots:
        return

    patched_updater = type(  # type: ignore[valid-type]
        "Updater",
        (updater_cls,),
        {
            "__slots__": (missing_slot,),
            "__module__": updater_cls.__module__,
        },
    )

    _updater_module.Updater = patched_updater
    if hasattr(_appbuilder, "Updater"):
        _appbuilder.Updater = patched_updater

    builder_cls = getattr(_appbuilder, "ApplicationBuilder", None)
    if builder_cls is not None and hasattr(builder_cls, "_updater_cls"):
        builder_cls._updater_cls = patched_updater  # type: ignore[attr-defined]


_patch_python_telegram_bot()

if __package__ in (None, ""):
    import sys
    from importlib import import_module
    from pathlib import Path

    package_dir = Path(__file__).resolve().parent
    sys.path.append(str(package_dir.parent))
    CharacterGenerator = import_module(
        f"{package_dir.name}.generator"
    ).CharacterGenerator  # type: ignore[attr-defined]
else:
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
    escaped = html.escape(formatted)
    await update.message.reply_text(
        f"<pre>{escaped}</pre>",
        parse_mode=ParseMode.HTML,
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
