import sqlite3

DB = {}

def connect():
    global DB
    # Caminho para o banco de dados
    DB['connection'] = sqlite3.connect('contratos_publicos.db', check_same_thread=False)
    DB['cursor'] = DB['connection'].cursor()
