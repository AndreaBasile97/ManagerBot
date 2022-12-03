import os
import re
from MySqlConnection import db
from typing import Dict
from datetime import datetime, timedelta
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update, MessageEntity, constants)
from telegram import __version__ as TG_VER
from telegram.ext import (Application, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters, CallbackQueryHandler)
from utils import retriveLatLon, compareDate, isPast, get_current_user_event, delete_event_from_buffer, retriveVia, generate_captions_from_event, crea_nome_locandina, text_to_orario
from queries import *
import threading
class Evento:
    def __init__(self, user_id):
        self.id = user_id
        self.timestamp = datetime.now()
        self.nome = ''
        self.citta = ''
        self.via = ''
        self.datainizio = ''
        self.datafine = ''
        self.categoria = ''
        self.prezzo = 0
        self.note = ''
        self.lat = ''
        self.lon = ''
        self.orario_inizio = ''
        self.orario_fine = ''

buffer = []

SCELTA, NOME_EVENTO, LUOGO, DATA, INFORMAZIONI_AGGIUNTIVE, DATAF, PREZZO, PHOTO, NOTE, CATEGORIA, VIA, ORARIO_INIZIO, ORARIO_FINE  = range(13)

datafine = "Data Fine \U0001F4C6"
locandina = "Locandina \U0001F5BC"
prezzo = "Prezzo \U0001F4B0"
note = "Note \U0001F4D4"
categoria = "Categoria 🎛"
via = "Via Esatta 📍"
orario_inizio = "Orario Inizio 🕒"
orario_fine = "Orario Fine 🕕"

reply_keyboard = [
    
    [datafine, locandina],
    [prezzo, note],
    [categoria, via],
    [orario_inizio, orario_fine],
    ["Elimina Evento ⛔", "Conferma Evento \u2705"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""
    reply_keyboard = [["Crea Evento ✨"], ["I miei eventi 🔍"]]

    risposta = await update.message.reply_text(
        "Ciao! Dimmi cosa vuoi fare!",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Clicca un'azione"
        ),
    )
    return SCELTA


async def scelta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    delete_event_from_buffer(buffer, user['id'])
    if(update.message.text == "Crea Evento ✨"):
        buffer.append(Evento(user['id'])) 
        risposta = await update.message.reply_text(
            "Perfetto, come si chiama l'evento che vuoi creare?",
            reply_markup=ReplyKeyboardRemove(),
        )
        return NOME_EVENTO
    elif(update.message.text == "I miei eventi 🔍"):
        eventi = read_events_by_id(db, user['id'])
        if len(eventi) > 0:
            for e in eventi:
                k = [
                    [InlineKeyboardButton("❌ Elimina " + e.nome , callback_data=e.id )],
                ]
                button = InlineKeyboardMarkup(k)
                caption = generate_captions_from_event(e)
                try: #con immagine
                    nome_locandina = crea_nome_locandina(e) + ".jpg"
                    await context.bot.send_photo(chat_id=update.message.chat_id ,photo=open('locandine/'+str(user['id'])+'/'+nome_locandina, 'rb'), caption=str(caption), reply_markup= button, parse_mode=constants.ParseMode.MARKDOWN_V2)
                except:
                    caption = generate_captions_from_event(e)
                    await update.message.reply_text(caption, reply_markup = button, parse_mode=constants.ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(
            "Nessun evento da mostrare"
            )
            return SCELTA

# Comandi di inserimento
async def inserisci_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    get_current_user_event(buffer, user['id']).nome = update.message.text
    riposta = await update.message.reply_text("Wow sembra interessante! In che città si terrà questo evento?")    
    return LUOGO

async def inserisci_luogo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    citta = update.message.text
    try:
        lat, lon = retriveLatLon(citta)
        get_current_user_event(buffer, user['id']).citta = citta
        get_current_user_event(buffer, user['id']).lat = lat
        get_current_user_event(buffer, user['id']).lon = lon
        risposta = await update.message.reply_text("Sono stato qualche volta a "+citta+"! Quando? gg/mm/aaaa ")    
        return DATA
    except:
        await update.message.reply_text("Non ho mai sentito parlare di questa città...inserisci una realmente esistente")
        return LUOGO


async def inserisci_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    data = update.message.text
    try:
        if(not isPast(data)):
            get_current_user_event(buffer, user['id']).datainizio = data
            await update.message.reply_text(
                "Adesso puoi inserire informazioni aggiuntive:",
                reply_markup=markup,
            )
            return INFORMAZIONI_AGGIUNTIVE
        else:
            await update.message.reply_text(
                "La data che hai inserito è già passata, puoi solo inserire le date correnti o future"
            )
            return DATA
    except:
            await update.message.reply_text(
                "Hai inserito una data non valida! Riprova..."
            )
            return DATA


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])

async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.message.from_user
    context.user_data["choice"] = text
    if (re.search("(\.*\s?)+(Data Fine)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci la data di fine")
        return DATAF
    if (re.search("(\.*\s?)+(Locandina)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci l'immagine della Locandina \U0001F5BC")
        return PHOTO
    if (re.search("(\.*\s?)+(Prezzo)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci il Prezzo (specifica solo la cifra) \U0001F4B0")
        return PREZZO
    if (re.search("(\.*\s?)+(Note)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci alcune note")
        return NOTE
    if (re.search("(\.*\s?)+(Categoria)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci la categoria dell'evento")
        return CATEGORIA
    if (re.search("(\.*\s?)+(Via Esatta)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci la via! ")
        return VIA
    if (re.search("(\.*\s?)+(Orario Inizio)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci l'orario di inizio dell'evento hh:mm")
        return ORARIO_INIZIO
    if (re.search("(\.*\s?)+(Orario Fine)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci l'orario di fine dell'evento hh:mm")
        return ORARIO_FINE
    if (re.search("(\.*\s?)+(Conferma Evento)\s(\.*)", text)):
        try: #con immagine
            caption = generate_captions_from_event(get_current_user_event(buffer, user['id']))
            nome_locandina = crea_nome_locandina(get_current_user_event(buffer, user['id'])) + ".jpg"
            await context.bot.send_photo(chat_id=update.message.chat_id ,photo=open('locandine/'+str(user['id'])+'/'+nome_locandina, 'rb'), caption=str(caption), reply_markup= ReplyKeyboardRemove(), parse_mode=constants.ParseMode.MARKDOWN_V2)
        except  Exception as e: #senza immagine
            print(e)
            caption = generate_captions_from_event(get_current_user_event(buffer, user['id']))
            await update.message.reply_text(caption, reply_markup=ReplyKeyboardMarkup(
            [["Crea Evento ✨"], ["I miei eventi 🔍"]], one_time_keyboard=True, input_field_placeholder="Clicca un'azione"
        ), parse_mode=constants.ParseMode.MARKDOWN_V2)
        print(get_current_user_event(buffer, user['id']).__dict__)
        insert_event(db, get_current_user_event(buffer, user['id']), user['username'])
        delete_event_from_buffer(buffer, user['id'])
        return SCELTA
        
async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    await update.message.reply_text(
        text,
        reply_markup=markup,
    )
    return INFORMAZIONI_AGGIUNTIVE


#Opzionali
async def inserisci_orario_inizio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.message.from_user

    if text_to_orario(text):
        get_current_user_event(buffer, user['id']).orario_inizio = text
        await update.message.reply_text("Orario di inizio 🕒 inserito!", reply_markup=markup)
        return INFORMAZIONI_AGGIUNTIVE
    else:
        await update.message.reply_text("Inserisci un vero orario o usa i due punti tra le ore e i minuti : . Riprova!")
        return ORARIO_INIZIO

async def inserisci_orario_fine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.message.from_user

    if text_to_orario(text):
        get_current_user_event(buffer, user['id']).orario_fine = text
        await update.message.reply_text("Orario di fine 🕕 inserito!", reply_markup=markup)
        return INFORMAZIONI_AGGIUNTIVE
    else:
        await update.message.reply_text("Inserisci un vero orario o usa i due punti tra le ore e i minuti :. Riprova!")
        return ORARIO_FINE

async def inserisci_prezzo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.message.from_user
    try:
        float(text)
        get_current_user_event(buffer, user['id']).prezzo = text
        await update.message.reply_text("Prezzo \U0001F4B0 inserito!", reply_markup=markup)
        return INFORMAZIONI_AGGIUNTIVE
    except:
        await update.message.reply_text("Devi inserire solo il prezzo. Usa il punto invece della virgola per i valori decimali.")
        return PREZZO

async def inserisci_datafine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.message.from_user
    try:
        if(compareDate(text, '>=', get_current_user_event(buffer, user['id']).datainizio)):
            get_current_user_event(buffer, user['id']).datafine = text
            await update.message.reply_text("Data di fine evento inserita!", reply_markup=markup)
            return INFORMAZIONI_AGGIUNTIVE
        else:
            await update.message.reply_text("Hai inserito una data di fine piu piccola della data di inizio! Inseriscila di nuovo")
            return DATAF
    except:
            await update.message.reply_text("Non sembra proprio una data ciò che hai inserito, riprova!")
            return DATAF

async def inserisci_prezzo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.message.from_user
    try:
        float(text)
        get_current_user_event(buffer, user['id']).prezzo = text
        await update.message.reply_text("Prezzo \U0001F4B0 inserito!", reply_markup=markup)
        return INFORMAZIONI_AGGIUNTIVE
    except:
        await update.message.reply_text("Devi inserire solo il prezzo. Usa il punto invece della virgola per i valori decimali.")
        return PREZZO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    if(not os.path.exists('locandine/'+str(user['id']))):
        os.mkdir('locandine/'+str(user['id']))
    await photo_file.download('locandine/'+str(user['id'])+"/"+crea_nome_locandina(get_current_user_event(buffer, user['id']))+".jpg")
    await update.message.reply_text("Locandina \U0001F5BC caricata!", reply_markup=markup)
    return INFORMAZIONI_AGGIUNTIVE

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    text = update.message.text
    get_current_user_event(buffer, user['id']).note = text
    await update.message.reply_text("Note inserite!", reply_markup=markup)
    return INFORMAZIONI_AGGIUNTIVE

async def categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    text = update.message.text
    get_current_user_event(buffer, user['id']).categoria = text
    await update.message.reply_text("Categoria inserita!", reply_markup=markup)
    return INFORMAZIONI_AGGIUNTIVE

async def via(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    via = update.message.text
    citta = get_current_user_event(buffer, user['id']).citta
    try:
        retriveVia(citta, via)
        get_current_user_event(buffer, user['id']).via = via
        await update.message.reply_text("Via inserita!", reply_markup=markup)
        return INFORMAZIONI_AGGIUNTIVE
    except:
        await update.message.reply_text("Non credo esista questa via in "+ citta +"...inserisci una vita realmente esistente")
        return VIA

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    delete_event_from_buffer(buffer, user['id'])
    await update.message.reply_text(
        "Ho annullato ciò stavi facendo! Vuoi tornare al menu? clicca qui /menu", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def eliminatore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    elimina(db, {query.data})
    await query.answer()
    try:
        await query.edit_message_text(text=f"Evento eliminato")
    except:
        await query.edit_message_caption(caption=f"Evento eliminato")
    return ConversationHandler.END

def main() -> None:
    pulisci_buffer()
    print("Bot avviato...")
    application = Application.builder().token("1475797612:AAEAoqIB6P9O8URMrJVCBQ7-ncRvsV_QuYA").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("menu", start), CommandHandler("start", start)],
        states={
            SCELTA: [MessageHandler(filters.Regex("^(Crea Evento ✨|I miei eventi 🔍)$"), scelta)],
            NOME_EVENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_nome)],
            LUOGO : [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_luogo)],
            DATA : [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_data)],
            INFORMAZIONI_AGGIUNTIVE : [
                MessageHandler(filters.Regex("(\.*\s?)+(Data Fine)\s(\.*)"), regular_choice),
                MessageHandler(filters.Regex("(\.*\s?)+(Locandina)\s(\.*)"), regular_choice),
                MessageHandler(filters.Regex("(\.*\s?)+(Prezzo)\s(\.*)"), regular_choice),
                MessageHandler(filters.Regex("(\.*\s?)+(Note)\s(\.*)"), regular_choice),
                MessageHandler(filters.Regex("(\.*\s?)+(Conferma Evento)\s(\.*)"), regular_choice),
                MessageHandler(filters.Regex("(\.*\s?)+(Categoria)\s(\.*)"), regular_choice),
                MessageHandler(filters.Regex("(\.*\s?)+(Via Esatta)\s(\.*)"), regular_choice),
                MessageHandler(filters.Regex("(\.*\s?)+(Orario Inizio)\s(\.*)"), regular_choice),
                MessageHandler(filters.Regex("(\.*\s?)+(Orario Fine)\s(\.*)"), regular_choice),
            ],
            DATAF: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_datafine)],
            PREZZO : [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_prezzo)],
            PHOTO: [MessageHandler(filters.PHOTO & ~filters.COMMAND, photo)],
            NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, note)],
            CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, categoria)],
            VIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, via)],
            ORARIO_INIZIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_orario_inizio)],
            ORARIO_FINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_orario_fine)],
        },
        fallbacks=[CommandHandler("cancel", cancel),CommandHandler("menu", start)]
    )
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(eliminatore))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

#Pulizia buffer ogni tre ore
def pulisci_buffer():
    threading.Timer(10800.0, pulisci_buffer).start()
    print("Pulizia buffer")
    for e in buffer:
        if(datetime.now() > e.timestamp + timedelta(hours=24)):
            buffer.remove(e)


if __name__ == "__main__":
    main()


# async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Stores the location and asks for some info about the user."""
#     user = update.message.from_user
#     user_location = update.message.location
#     logger.info(
#         "Location of %s: %f / %f", user.first_name, user_location.latitude, user_location.longitude
#     )
#     await update.message.reply_text(
#         "Maybe I can visit you sometime! At last, tell me something about yourself."
#     )

#     return NOTE


# async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Skips the location and asks for info about the user."""
#     user = update.message.from_user
#     logger.info("User %s did not send a location.", user.first_name)
#     await update.message.reply_text(
#         "You seem a bit paranoid! At last, tell me something about yourself."
#     )

#     return NOTE