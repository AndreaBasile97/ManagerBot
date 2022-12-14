from datetime import datetime, timedelta
from utils import less_than_2_years, retriveLatLon, compareDate, isPast, get_current_user_event, delete_event_from_buffer, retriveVia, generate_captions_from_event, crea_nome_locandina, text_to_orario


def validate(attribute, attribute_value, buffer, user):
    if(attribute == 'luogo'):
        return validate_citta(attribute_value, buffer, user)
    if(attribute == 'data_inizio'):
        return validate_data_inizio(attribute_value, buffer, user)
    if(attribute == 'orario_inizio'):
        return validate_orario_inizio(attribute_value, buffer, user)
    if(attribute == 'data_fine'):
        return validate_data_fine(attribute_value, buffer, user)
    if(attribute == 'orario_fine'):
        return validate_orario_fine(attribute_value, buffer, user)
    if(attribute == 'prezzo'):
        return validate_prezzo(attribute_value, buffer, user)
    if(attribute == 'via'):
        return validate_via(attribute_value, buffer, user)
    if(attribute == 'note'):
        get_current_user_event(buffer, user['id']).note = attribute_value
        return True
    if(attribute == 'categoria'):
        get_current_user_event(buffer, user['id']).categoria = attribute_value
        return True
    else:
        print("Nessun Validator Disponibile")
        return False

def validate_citta(citta, buffer, user):
    try:
        lat, lon = retriveLatLon(citta)
        get_current_user_event(buffer, user['id']).citta = citta
        get_current_user_event(buffer, user['id']).lat = lat
        get_current_user_event(buffer, user['id']).lon = lon
        return True
    except:
        return False

def validate_data_inizio(data, buffer, user):
    try:
        if(not isPast(data) and less_than_2_years(data)):
            get_current_user_event(buffer, user['id']).datainizio = data
            return True
        else:
            return False
    except:
        return False

def validate_data_fine(data, buffer, user):
    try:
        if(compareDate(data, '>=', get_current_user_event(buffer, user['id']).datainizio)):
            get_current_user_event(buffer, user['id']).datafine = data
            return True
        else:
            return False
    except:
            return False

def validate_orario_inizio(orario, buffer, user):
    try:
        orario_fine = str(get_current_user_event(buffer, user['id']).orario_fine).split(":")[0]
    except:
        print("Orario di fine non inserito")
    if text_to_orario(orario):
        get_current_user_event(buffer, user['id']).orario_inizio = orario
        if not(orario_fine == '') and str(orario).split(":")[0] > orario_fine and (get_current_user_event(buffer, user['id']).datafine == '' or get_current_user_event(buffer, user['id']).datafine == get_current_user_event(buffer, user['id']).datainizio):
            data = get_current_user_event(buffer, user['id']).datainizio
            data_incremented = datetime.strptime(data, '%d/%m/%Y') + timedelta(days=1)
            string_data_incremented = datetime.strptime(str(data_incremented), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            print(orario_fine, str(orario).split(":")[0], data, data_incremented, string_data_incremented)
            get_current_user_event(buffer, user['id']).datafine = string_data_incremented
        return True
    else:
        return False

def validate_orario_fine(orario, buffer, user):
    try:
        orario_inizio = str(get_current_user_event(buffer, user['id']).orario_inizio).split(":")[0]
    except:
        print("Orario di inizio non inserito")
    if text_to_orario(orario):
        get_current_user_event(buffer, user['id']).orario_fine = orario
        if not(orario_inizio == '') and str(orario).split(":")[0] < orario_inizio and (get_current_user_event(buffer, user['id']).datafine == '' or get_current_user_event(buffer, user['id']).datafine == get_current_user_event(buffer, user['id']).datainizio):
            data = get_current_user_event(buffer, user['id']).datainizio
            data_incremented = datetime.strptime(data, '%d/%m/%Y') + timedelta(days=1)
            string_data_incremented = datetime.strptime(str(data_incremented), '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            get_current_user_event(buffer, user['id']).datafine = string_data_incremented
        return True
    else:
        return False

def validate_prezzo(prezzo, buffer, user):
    try:
        float(prezzo)
        get_current_user_event(buffer, user['id']).prezzo = prezzo
        return True
    except:
        return False

def validate_via(via, buffer, user):
    citta = get_current_user_event(buffer, user['id']).citta
    try:
        retriveVia(citta, via)
        get_current_user_event(buffer, user['id']).via = via
        return True
    except:
        return False