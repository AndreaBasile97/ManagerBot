from datetime import datetime, timedelta

class Evento:
    def __init__(self):
        self.id = ''
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


def insert_event(db, evento, nome_organizzatore):
    # fare in modo che ci sia anche l'orario inizio e fine
    if(evento.orario_inizio):
        whole_date_i = str(evento.datainizio +" "+evento.orario_inizio+":00")
    else:
        whole_date_i = evento.datainizio+" "+"00:00:00"

    
    di = datetime.strptime(whole_date_i, "%d/%m/%Y %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S')
    if(evento.datafine):
        if(evento.orario_fine):
            whole_date_f = str(evento.datafine +" "+evento.orario_fine+":00")
        else:
            whole_date_f = evento.datafine+" "+"23:59:59"
        df = datetime.strptime(whole_date_f, "%d/%m/%Y %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S')
    else:
        if(evento.orario_fine):
            whole_date_f = str(evento.datainizio +" "+evento.orario_fine+":00")
            df = datetime.strptime(whole_date_f, "%d/%m/%Y %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S')
        else:
            whole_date_f = str(evento.datainizio +" "+"23:59:59")
            df = datetime.strptime(whole_date_f, "%d/%m/%Y %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S')

    with db.cursor() as cursor:
        print(evento.categoria)
        cursor.callproc('inserisci_evento', [evento.nome, di, df, evento.citta, evento.via, float(evento.prezzo), evento.note, evento.lat, evento.lon, nome_organizzatore, evento.id, evento.categoria])
        # print results
        result = cursor.fetchall()
        return str(result)


def read_events_by_id(db, id):
    eventi = []
    with db.cursor() as cursor:
        selezione_eventi = "SELECT evento.id, evento.nome, evento.descrizione, evento.data_inizio, evento.data_fine, evento.prezzo, evento.nome_comune, evento.indirizzo, categoria.nome FROM evento JOIN organizzazione ON organizzazione.id_evento = evento.id JOIN categoria ON organizzazione.id_categoria = categoria.id WHERE organizzazione.id_organizzatore = %s"
        cursor.execute(selezione_eventi, (id,))
        result = cursor.fetchall()
        for evento in result:
            ev = Evento()
            ev.id = evento.get('id')
            ev.nome = evento.get('nome')
            ev.note = evento.get('descrizione')
            ev.datainizio = datetime.strptime(str(evento.get('data_inizio')), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
            ev.datafine = datetime.strptime(str(evento.get('data_fine')), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
            ev.orario_inizio = datetime.strptime(str(evento.get('data_inizio')), "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
            ev.orario_fine = datetime.strptime(str(evento.get('data_fine')), "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
            ev.prezzo = evento.get('prezzo')
            ev.citta = evento.get('nome_comune')
            ev.via = evento.get('indirizzo')
            ev.categoria = evento.get('categoria.nome')
            eventi.append(ev)
        return eventi

def elimina(db, id):
    with db.cursor() as cursor:
        selezione_eventi = "DELETE FROM evento WHERE id = %s"
        cursor.execute(selezione_eventi, (id,)) 
        db.commit()
