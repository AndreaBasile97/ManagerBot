#!/usr/bin/python
import pymysql

try:
    db = pymysql.connect(host="localhost", 
                    user="root", 
                    password="root",  
                    db="hera",
                    cursorclass=pymysql.cursors.DictCursor)
except:
    print("Errore di connessione")    
