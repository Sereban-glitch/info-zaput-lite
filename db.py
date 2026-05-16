import sqlite3
import os

# Путь к базе данных в корне проекта
DB_PATH = "info_zaput.db"

def init_db():
    """Инициализация базы данных: создание таблиц для логов и статусов."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                chat_id INTEGER,
                user_id INTEGER,
                recipient_name TEXT,
                recipient_email TEXT,
                subject TEXT,
                status TEXT DEFAULT 'sent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reply_received_at TIMESTAMP
            )
        ''')
        conn.commit()

def log_request(message_id, chat_id, user_id, recipient_name, recipient_email, subject):
    """Логирование отправленного запроса."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO requests (message_id, chat_id, user_id, recipient_name, recipient_email, subject)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, chat_id, user_id, recipient_name, recipient_email, subject))
        conn.commit()

def mark_replied(message_id):
    """Пометка запроса как получившего ответ."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE requests 
            SET status = 'replied', reply_received_at = CURRENT_TIMESTAMP 
            WHERE message_id = ?
        ''', (message_id,))
        conn.commit()

def get_pending_requests():
    """Получение списка запросов, на которые еще нет ответа."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message_id, recipient_email FROM requests WHERE status = 'sent'")
        return cursor.fetchall()
