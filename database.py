import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import os

# Get the database URL from the environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()

    # Drop existing tables (if required for a clean slate)
    c.execute('DROP TABLE IF EXISTS messages CASCADE')
    c.execute('DROP TABLE IF EXISTS chats CASCADE')

    # Create chats table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            title TEXT,
            model TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            UNIQUE(chat_id, username)
        )
    ''')

    # Create messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (chat_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    c.close()
    conn.close()

def save_chat(username, chat_id, chat_data):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()

    now = datetime.now().isoformat()

    # Insert or update chat
    c.execute('''
        INSERT INTO chats (chat_id, username, title, model, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (chat_id) DO UPDATE SET
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

    # Delete existing messages for this chat to refresh them
    c.execute('DELETE FROM messages WHERE chat_id = %s', (chat_id,))

    # Insert new messages
    for msg in chat_data.get('messages', []):
        c.execute('''
            INSERT INTO messages (chat_id, role, content, timestamp)
            VALUES (%s, %s, %s, %s)
        ''', (chat_id, msg['role'], msg['content'], now))

    conn.commit()
    c.close()
    conn.close()

def get_user_chats(username):
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    c = conn.cursor()

    # Get all chats for the user
    c.execute('''
        SELECT chat_id, title, model, created_at
        FROM chats
        WHERE username = %s
        ORDER BY updated_at DESC
        LIMIT 20
    ''', (username,))

    chats = {}
    for row in c.fetchall():
        chat_id, title, model, created_at = row['chat_id'], row['title'], row['model'], row['created_at']
        # Get messages for each chat
        c.execute('''
            SELECT role, content, timestamp
            FROM messages
            WHERE chat_id = %s
            ORDER BY timestamp
        ''', (chat_id,))
        
        messages = [{'role': role, 'content': content, 'timestamp': timestamp} 
                    for role, content, timestamp in c.fetchall()]
        
        chats[chat_id] = {
            'id': chat_id,
            'title': title,
            'model': model,
            'messages': messages,
            'created_at': created_at
        }

    c.close()
    conn.close()
    return chats

def delete_old_chats(username):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()

    # Get chat IDs ordered by updated_at
    c.execute('''
        SELECT chat_id
        FROM chats
        WHERE username = %s
        ORDER BY updated_at DESC
    ''', (username,))

    chat_ids = [row[0] for row in c.fetchall()]

    # If user has more than 20 chats, delete the oldest ones
    if len(chat_ids) > 20:
        for chat_id in chat_ids[20:]:
            c.execute('DELETE FROM messages WHERE chat_id = %s', (chat_id,))
            c.execute('DELETE FROM chats WHERE chat_id = %s', (chat_id,))

    conn.commit()
    c.close()
    conn.close()

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database and returns the connection object.
    """
    conn = psycopg2.connect(DATABASE_URL)
    return conn
