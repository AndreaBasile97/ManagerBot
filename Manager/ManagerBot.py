import os
import re
from typing import Dict
from datetime import datetime, timedelta
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update, MessageEntity, constants)
from telegram import __version__ as TG_VER
from telegram.ext import (Application, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters, CallbackQueryHandler)
from validators import validate
from utils import retriveMeteo, retriveLatLon, compareDate, isPast, get_current_user_event, delete_event_from_buffer, retriveVia, generate_captions_from_event, crea_nome_locandina, text_to_orario
from queries import *
from MySqlConnection import connection
import threading
from functools import partial
from strings import success_msg, fail_msg
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
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

SCELTA, EDIT_DELETE, NOME_EVENTO, LUOGO, DATA, INFORMAZIONI_AGGIUNTIVE, DATAF, PREZZO, PHOTO, NOTE, CATEGORIA, VIA, ORARIO_INIZIO, ORARIO_FINE  = range(14)

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

db = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global db 
    db = connection()
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
                    [InlineKeyboardButton("✏️ Modifica ", callback_data=[e, user['id'], 'M'] ), InlineKeyboardButton("❌ Elimina ", callback_data=[e, user['id'], 'D'])],
                ]
                button = InlineKeyboardMarkup(k)
                caption = generate_captions_from_event(e)
                try: #con immagine
                    nome_locandina = crea_nome_locandina(e) + ".jpg"
                    await context.bot.send_photo(chat_id=update.message.chat_id ,photo=open('locandine/'+str(user['id'])+'/'+nome_locandina, 'rb'), caption=str(caption), reply_markup= button, parse_mode=constants.ParseMode.MARKDOWN_V2)
                except:
                    caption = generate_captions_from_event(e)
                    await update.message.reply_text(caption, reply_markup = button, parse_mode=constants.ParseMode.MARKDOWN_V2)
            return EDIT_DELETE
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

async def insert(update: Update, context: ContextTypes.DEFAULT_TYPE, attribute, succ_state, fail_state, keyboard = '') -> int:
    user = update.message.from_user
    value = update.message.text
    try:
        warnings = await warn(attribute, user['id'], value)
        if warnings:
            await update.message.reply_text(warnings, reply_markup='')
    except Exception as e:
        print("nothing to warn" + str(e))
    if validate(attribute, value, buffer, user):
        await update.message.reply_text(success_msg[attribute], reply_markup=keyboard)
        return succ_state
    else:
        await update.message.reply_text(fail_msg[attribute])
        return fail_state


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])

async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.message.from_user
    context.user_data["choice"] = text
    if (re.search("(\.*\s?)+(Data Fine)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci la data di fine (Premi /skip per annullare l'inserimento) ")
        return DATAF
    if (re.search("(\.*\s?)+(Locandina)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci l'immagine della Locandina \U0001F5BC (Premi /skip per annullare l'inserimento)")
        return PHOTO
    if (re.search("(\.*\s?)+(Prezzo)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci il Prezzo (specifica solo la cifra) \U0001F4B0 (Premi /skip per annullare l'inserimento)")
        return PREZZO
    if (re.search("(\.*\s?)+(Note)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci alcune note. (Premi /skip per annullare l'inserimento) ")
        return NOTE
    if (re.search("(\.*\s?)+(Categoria)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci la categoria dell'evento. (Premi /skip per annullare l'inserimento)")
        return CATEGORIA
    if (re.search("(\.*\s?)+(Via Esatta)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci la via! (Premi /skip per annullare l'inserimento)")
        return VIA
    if (re.search("(\.*\s?)+(Orario Inizio)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci l'orario di inizio dell'evento hh:mm. (Premi /skip per annullare l'inserimento)")
        return ORARIO_INIZIO
    if (re.search("(\.*\s?)+(Orario Fine)\s(\.*)", text)):
        await update.message.reply_text(f"Inserisci l'orario di fine dell'evento hh:mm. (Premi /skip per annullare l'inserimento)")
        return ORARIO_FINE
    if (re.search("(\.*\s?)+(Conferma Evento)\s(\.*)", text)):
        try: #con immagine
            caption = generate_captions_from_event(get_current_user_event(buffer, user['id']))
            nome_locandina = crea_nome_locandina(get_current_user_event(buffer, user['id'])) + ".jpg"
            await context.bot.send_photo(chat_id=update.message.chat_id ,photo=open('locandine/'+str(user['id'])+'/'+nome_locandina, 'rb'), caption=str(caption), reply_markup= ReplyKeyboardRemove(), parse_mode=constants.ParseMode.MARKDOWN_V2)
        except  Exception as e: #senza immagine
            print(e)
            caption = generate_captions_from_event(get_current_user_event(buffer, user['id']))
            await update.message.reply_text(caption, reply_markup=ReplyKeyboardRemove(), parse_mode=constants.ParseMode.MARKDOWN_V2)
        await update.message.reply_text("Se hai terminato, puoi tornare al /menu", reply_markup=ReplyKeyboardRemove(), parse_mode=constants.ParseMode.MARKDOWN_V2)
        print(get_current_user_event(buffer, user['id']).__dict__)
        insert_event(db, get_current_user_event(buffer, user['id']), user['username'])
        delete_event_from_buffer(buffer, user['id'])
        return INFORMAZIONI_AGGIUNTIVE
        
async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    await update.message.reply_text(
        text,
        reply_markup=markup,
    )
    return INFORMAZIONI_AGGIUNTIVE

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    if(not os.path.exists('locandine/'+str(user['id']))):
        os.mkdir('locandine/'+str(user['id']))
    await photo_file.download('locandine/'+str(user['id'])+"/"+crea_nome_locandina(get_current_user_event(buffer, user['id']))+".jpg")
    await update.message.reply_text("Locandina \U0001F5BC caricata!", reply_markup=markup)
    return INFORMAZIONI_AGGIUNTIVE


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
    evento_target = query.data[0]
    user_id = query.data[1]
    modality = query.data[2]
    if modality == 'D':
        try:
            nome_locandina = crea_nome_locandina(evento_target)
            os.remove('locandine/'+str(user_id)+"/"+nome_locandina+".jpg")
        except:
            print("Non sono riuscito a rimuovere: "+ 'locandine/'+str(user_id)+"/"+nome_locandina+".jpg")
        elimina(db, evento_target.id)
        await query.answer()
        try:
            await query.edit_message_text(text=f"Evento eliminato")
        except:
            await query.edit_message_caption(caption=f"Evento eliminato")
    else:
        try:
            delete_event_from_buffer(buffer, user_id)
        except:
            print("No event deleted")
        elimina(db, evento_target.id)
        evento_target.id = user_id
        buffer.append(evento_target)
        await query.edit_message_reply_markup(reply_markup='')
        await query.message.reply_text("Ok! adesso puoi modificare l'evento " + evento_target.nome, reply_markup=markup)
        return INFORMAZIONI_AGGIUNTIVE

async def warn(attribute, id_user, value):
    rainy_days = []
    try:
        if(attribute=='data_inizio'):
            citta = get_current_user_event(buffer, id_user).citta
            di = value
            rainy_days = retriveMeteo(citta, di, '')
        if(attribute=='data_fine'):
            citta = get_current_user_event(buffer, id_user).citta
            di = get_current_user_event(buffer, id_user).datainizio
            df = value
            rainy_days = retriveMeteo(citta, di, df)
    except:
        print("Impossibile osservare il meteo")
    if len(rainy_days)>0:
        text = 'In queste date è previsto mal tempo: '
        for d in rainy_days:
            text += str(d+" ")
        text += ". Sicuro di proseguire?"
        return text

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    await update.message.reply_text(
        "Ok", reply_markup=markup
    )
    return INFORMAZIONI_AGGIUNTIVE

def main() -> None:
    pulisci_buffer()
    print("Bot avviato...")
    application = Application.builder().token("5819293970:AAEgWXRJwz4g2GmFvfEHGszhy4mEWjPtQrw").arbitrary_callback_data(True).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("menu", start), CommandHandler("start", start)],
        states={
            SCELTA: [MessageHandler(filters.Regex("^(Crea Evento ✨|I miei eventi 🔍)$"), scelta)],
            EDIT_DELETE: [CallbackQueryHandler(eliminatore)],
            NOME_EVENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, inserisci_nome)],
            LUOGO : [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='luogo', succ_state = DATA, fail_state = LUOGO))],
            DATA : [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='data_inizio', succ_state = INFORMAZIONI_AGGIUNTIVE, fail_state = DATA, keyboard = markup))],
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
                CallbackQueryHandler(eliminatore)
            ],
            DATAF: [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='data_fine', succ_state = INFORMAZIONI_AGGIUNTIVE, fail_state = DATAF, keyboard = markup)), CommandHandler("skip", skip)],
            PREZZO : [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='prezzo', succ_state = INFORMAZIONI_AGGIUNTIVE, fail_state = PREZZO, keyboard = markup)), CommandHandler("skip", skip)],
            PHOTO: [MessageHandler(filters.PHOTO & ~filters.COMMAND, photo), CommandHandler("skip", skip)],
            NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='note', succ_state = INFORMAZIONI_AGGIUNTIVE, fail_state = NOTE, keyboard = markup)), CommandHandler("skip", skip)],
            CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='categoria', succ_state = INFORMAZIONI_AGGIUNTIVE, fail_state = CATEGORIA, keyboard = markup)), CommandHandler("skip", skip)],
            VIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='via', succ_state = INFORMAZIONI_AGGIUNTIVE, fail_state = VIA, keyboard = markup)), CommandHandler("skip", skip)],
            ORARIO_INIZIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='orario_inizio', succ_state = INFORMAZIONI_AGGIUNTIVE, fail_state = ORARIO_INIZIO, keyboard = markup)), CommandHandler("skip", skip)],
            ORARIO_FINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(insert, attribute='orario_fine', succ_state = INFORMAZIONI_AGGIUNTIVE, fail_state = ORARIO_FINE, keyboard = markup)), CommandHandler("skip", skip)],
        },
        fallbacks=[CommandHandler("cancel", cancel),CommandHandler("menu", start), CommandHandler("start", start)],
        allow_reentry=True
    )
    application.add_handler(conv_handler)
    #application.add_handler(CallbackQueryHandler(eliminatore))

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
