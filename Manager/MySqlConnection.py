#!/usr/bin/python
import pymysql

def connection():
    try:
        db = pymysql.connect(host="db4free.net", 
                        port=3306,
                        user="herawannight", 
                        password="gru*8*X3raFTy!A",  
                        db="herawannight",
                        cursorclass=pymysql.cursors.DictCursor,
                        connect_timeout=31536000)
    except Exception as e: 
        return("Errore di connessione " + str(e))
    return db    
    #gru*8*X3raFTy!A
