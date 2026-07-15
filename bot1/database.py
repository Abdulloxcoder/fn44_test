import psycopg2
import os
from load import DBNAME,USER,PASSWORD,HOST,PORT

def connection():
    return  psycopg2.connect(
        HOST=HOST,
        user=USER,
        password=PASSWORD,
        database=DBNAME,
        port=PORT
    )

def jadval_yaratish():
    conn=connection()
    cur=conn.cursor()
    cur = connection().cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255),
    telegram_id VARCHAR(255),
    )  
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("jadval yaratildi!")


def malumot(fullname, telegram_id):
    conn=connection()
    cur=conn.cursor()
    cur.execute("""INSERT INTO users (full_name,telegram_id) VALUES (%s, %s);""",(fullname,telegram_id))
    conn.commit()
    cur.close()
    conn.close()

# malumot("abdulloh","1")