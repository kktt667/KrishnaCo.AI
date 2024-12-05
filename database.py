import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import os
from contextlib import contextmanager
from psycopg2 import sql
import urllib.parse

# Get the database URL and add SSL requirement
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

@contextmanager
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

@contextmanager
def get_db_cursor(commit=False):
    """Context manager for database cursors"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=DictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()

def init_db():
    """Initialize database tables"""
    with get_db_cursor(commit=True) as cursor:
        # Create chats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                title TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, username)
            )
        ''')

        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats (chat_id) ON DELETE CASCADE
            )
        ''')

def save_chat(username, chat_id, chat_data):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if chat exists
                cur.execute(
                    "SELECT id FROM chats WHERE chat_id = %s AND username = %s",
                    (chat_id, username)
                )
                result = cur.fetchone()
                
                if result:
                    # Update existing chat
                    cur.execute(
                        """
                        UPDATE chats 
                        SET chat_data = %s, updated_at = NOW()
                        WHERE chat_id = %s AND username = %s
                        """,
                        (json.dumps(chat_data), chat_id, username)
                    )
                else:
                    # Insert new chat
                    cur.execute(
                        """
                        INSERT INTO chats (chat_id, username, chat_data)
                        VALUES (%s, %s, %s)
                        """,
                        (chat_id, username, json.dumps(chat_data))
                    )
                conn.commit()
    except Exception as e:
        print(f"Error saving chat: {e}")
        raise

def get_user_chats(username):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT chat_id, chat_data
                    FROM chats
                    WHERE username = %s
                    ORDER BY updated_at DESC
                    """,
                    (username,)
                )
                results = cur.fetchall()
                
                chats = {}
                for chat_id, chat_data in results:
                    chats[chat_id] = json.loads(chat_data)
                return chats
    except Exception as e:
        print(f"Error getting chats: {e}")
        raise
        
def delete_old_chats(username):
    """Delete oldest chats keeping only the most recent 20"""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute('''
            WITH old_chats AS (
                SELECT chat_id
                FROM chats
                WHERE username = %s
                ORDER BY updated_at DESC
                OFFSET 20
            )
            DELETE FROM chats
            WHERE chat_id IN (SELECT chat_id FROM old_chats)
        ''', (username,))