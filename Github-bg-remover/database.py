import sqlite3
from sqlite3 import Error

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        return conn
    except Error as e:
        print(e)
    return conn

def initialize_database():
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                tokens INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
    finally:
        if conn:
            conn.close()

def get_tokens(user_id):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT tokens FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()

def add_user(user_id):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    finally:
        conn.close()

def update_tokens(user_id, amount):
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, tokens)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET tokens = tokens + ?
        ''', (user_id, amount, amount))
        conn.commit()
    finally:
        conn.close()

# Initialize database when module loads
initialize_database()