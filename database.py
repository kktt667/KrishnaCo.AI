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
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()

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
    """Save or update a chat and its messages"""
    with get_db_cursor(commit=True) as cursor:
        now = datetime.now()

        # Insert or update chat using UPSERT
        cursor.execute('''
            INSERT INTO chats (chat_id, username, title, model, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (chat_id, username) DO UPDATE SET
                title = EXCLUDED.title,
                model = EXCLUDED.model,
                updated_at = EXCLUDED.updated_at
        ''', (
            chat_id,
            username,
            chat_data.get('title', 'New Chat'),
            chat_data.get('model', 'gpt-3.5-turbo'),
            chat_data.get('created_at', now),
            now
        ))

        # Efficiently update messages
        cursor.execute('DELETE FROM messages WHERE chat_id = %s', (chat_id,))
        
        # Batch insert messages
        messages_data = [(
            chat_id,
            msg['role'],
            msg['content'],
            now
        ) for msg in chat_data.get('messages', [])]
        
        if messages_
            psycopg2.extras.execute_batch(cursor, '''
                INSERT INTO messages (chat_id, role, content, timestamp)
                VALUES (%s, %s, %s, %s)
            ''', messages_data)

def get_user_chats(username):
    """Get all chats and their messages for a user"""
    with get_db_cursor() as cursor:
        # Get all chats for the user with a single query
        cursor.execute('''
            SELECT c.chat_id, c.title, c.model, c.created_at,
                   json_agg(
                       json_build_object(
                           'role', m.role,
                           'content', m.content,
                           'timestamp', m.timestamp
                       ) ORDER BY m.timestamp
                   ) as messages
            FROM chats c
            LEFT JOIN messages m ON c.chat_id = m.chat_id
            WHERE c.username = %s
            GROUP BY c.chat_id, c.title, c.model, c.created_at
            ORDER BY c.updated_at DESC
            LIMIT 20
        ''', (username,))
        
        results = cursor.fetchall()
        
        return {
            row['chat_id']: {
                'id': row['chat_id'],
                'title': row['title'],
                'model': row['model'],
                'messages': row['messages'] if row['messages'][0] is not None else [],
                'created_at': row['created_at']
            }
            for row in results
        }

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