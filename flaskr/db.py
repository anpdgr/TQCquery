import click
from flask import current_app, g
from flask.cli import with_appcontext
import cx_Oracle

def get_db():

    dsn_string = """(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.19.195.170)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=TQCPRD)))"""
    if 'db' not in g:
        # g.db = sqlite3.connect(
        #     current_app.config['DATABASE'],
        #     detect_types=sqlite3.PARSE_DECLTYPES
        # )
        g.db = cx_Oracle.connect(user="QAQCAPPO", password="QAQCAPPO#123", dsn=dsn_string, encoding="UTF-8")
         
        #g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()