
import logging
from typing import Dict
from telegram import __version__ as TG_VER
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]
if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)



SCELTA, MODALITA_RICERCA, NOME_EVENTO, LUOGO, DATA, DATAF, PREZZO, PHOTO, NOTE  = range(9)

# comandi di skip
async def skip_datafine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    risposta = await update.message.reply_text(
        "Quanto costa partecipare all'evento? Se è gratis premi /skip"
    )
    return PREZZO

async def skip_prezzo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    risposta = await update.message.reply_text(
        "Vuoi mandare una foto della locandina? Altrimenti clicca /skip."
    )
    return PHOTO

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text(
        "Scrivi altre note...altrimenti clicca /skip."
    )
    return NOTE

async def skip_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    risposta = await update.message.reply_text("Grazie! Il tuo evento è stato creato!")
    return ConversationHandler.END