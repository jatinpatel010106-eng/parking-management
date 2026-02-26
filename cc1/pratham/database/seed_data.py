# database/sqlite_config.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "parking.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE
        );

        CREATE TABLE IF NOT EXISTS parking_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number TEXT,
            is_occupied INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS parking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            slot_id INTEGER,
            check_in TEXT,
            check_out TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(slot_id) REFERENCES parking_slots(id)
        );
    ''')
    
    conn.commit()
    conn.close()

init_db()