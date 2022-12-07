import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import hashlib
import time
class Evento:
    def __init__(self, user_id):
        self.id = user_id
        self.timestamp = datetime.now()
        self.nome = ''
        self.citta = ''
        self.via = ''
        self.lat = ''
        self.lon = ''
        self.datainizio = ''
        self.datafine = ''
        self.categoria = ''
        self.prezzo = 0
        self.note = ''
        self.orario_inizio = ''
        self.orario_fine = ''

def retriveLatLon(citta):
    response = requests.request("GET", f"https://www.geonames.org/search.html?q={citta}")
    country = re.findall("/countries.*\.html", response.text)[0].strip(".html").split("/")[-1]
    data = response.text
    soup = BeautifulSoup(data,"html.parser")
    long = soup.find('span', {'class': 'longitude'})
    lat = soup.find('span', {'class': 'latitude'})
    if(lat != None and long != None and country == 'italy'):
        print(citta, "- Lat : " + lat.text + " Long : " + long.text)
        return lat.text, long.text
    else:
        raise Exception("Nessuna città trovata")

def retriveVia(citta, via):
    response = requests.request("GET", f" https://nominatim.openstreetmap.org/search.php?street={via}&city={citta}&format=json")
    for campo in json.loads(response.text):
        if(campo['lat'] and campo['lon']):
            latitudine_via = campo['lat']
            longitudine_via = campo['lon']
            return latitudine_via, longitudine_via
    else:
        raise Exception("Nessuna via trovata")

def compareDate(date1, op, date2):
    date1 = datetime.strptime(str(date1), "%d/%m/%Y")
    date2 = datetime.strptime(str(date2), "%d/%m/%Y")
    if(op == '>='):
        if(date1 >= date2):
            return True
        else:
            return False
    if(op == '<'):
        if(date1 < date2):
            return True
        else:
            return False
    if(op == '<='):
        if(date1 <= date2):
            return True
        else:
            return False
    if(op == '>'):
        if(date1 > date2):
            return True
        else:
            return False

def isPast(date):
    try:
        past = datetime.strptime(date, "%d/%m/%Y")
        present = datetime.now()
        return past.date() < present.date()
    except:
        raise Exception("Data non riconosciuta")

def less_than_2_years(date):
    try:
        date = datetime.strptime(date, "%d/%m/%Y")
        present = datetime.now()
        present = present.replace(year=present.year + 2)
        print(present)
        return date.date() < present.date()
    except:
        raise Exception("Data maggiore di 2 anni")


def get_current_user_event(buffer, id_current_user) -> Evento:
    for e in buffer:
        if (str(e.id) == str(id_current_user)):
            return e

def delete_event_from_buffer(buffer, id_current_user):
    for e in buffer:
        if (str(e.id) == str(id_current_user)):
            buffer.remove(e)

def generate_captions_from_event(object: Evento):
    caption = ''
    citta = ''
    for k, v in list(object.__dict__.items()):
        if(not v == '' and k != 'id'):
            if(k == 'nome'):
                caption += '*' + v + '*\n \n'
            elif(k == 'citta'):
                caption += '🏙 Città: ' + v + '\n'
                citta = v
            elif(k == 'via'):
                caption += '📍 Posizione: ' + generate_google_maps_link(object.via, citta) + '\n'
            elif(k == 'datainizio'):
                caption += '\U0001F4C6 Data di inizio: ' + v + '\n'
            elif(k == 'orario_inizio'):
                caption += '🕒 Orario di inizio: ' + v + '\n'
            elif(k == 'datafine'):
                caption += '\U0001F4C6 Data di fine: ' + v + '\n'
            elif(k == 'orario_fine'):
                caption += '🕕 Orario di fine: ' + v + '\n'
            elif(k == 'categoria'):
                caption += '🎛 Categoria: ' + v + '\n'
            elif(k == 'prezzo' and float(v) > 0):
                caption += '\U0001F4B0 Prezzo: ' + str(v).replace(".", "," ) + '€\n'          
            elif(k == 'note'):
                caption += '\U0001F4D4 Note: ' + v + '\n'
    return caption


def generate_google_maps_link(via, citta):
    s = str(via+","+citta)
    return "[link](https://maps.google.com/?q="+s+")"


def checkString(string):
        return "✔ "+string

def crea_nome_locandina(evento: Evento):
    stringa = evento.nome + evento.datainizio + evento.citta
    sha_signature = hashlib.sha256(stringa.encode()).hexdigest()
    return str(sha_signature)


def text_to_orario(ora_text):
    try:
        time.strptime(ora_text, '%H:%M')
        return True
    except:
        return False
