from flask import g
import cx_Oracle

def get_db():
    dsn_string = """(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.19.195.170)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=TQCPRD)))"""
    
    if 'db' not in g:
        g.db = cx_Oracle.connect(user="QAQCAPPO", password="QAQCAPPO#123", dsn=dsn_string, encoding="UTF-8")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()