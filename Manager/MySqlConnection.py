#!/usr/bin/python
import pymysql

try:
    db = pymysql.connect(host="db4free.net", 
                    port=3306,
                    user="herawannight", 
                    password="gru*8*X3raFTy!A",  
                    db="herawannight",
                    cursorclass=pymysql.cursors.DictCursor)
except Exception as e: 
    print("Errore di connessione " + str(e))    
#gru*8*X3raFTy!A