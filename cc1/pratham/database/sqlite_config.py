import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "parking.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT,
            owner_name TEXT,
            vehicle_type TEXT,
            entry_time TEXT,
            exit_time TEXT,
            status TEXT DEFAULT 'parked',
            duration_hours INTEGER,
            total_fee REAL,
            created_by TEXT
        );

        CREATE TABLE IF NOT EXISTS parking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT,
            owner_name TEXT,
            vehicle_type TEXT,
            entry_time TEXT,
            exit_time TEXT,
            duration_hours INTEGER,
            total_fee REAL,
            processed_by TEXT
        );
    ''')
    conn.commit()
    conn.close()

init_db()