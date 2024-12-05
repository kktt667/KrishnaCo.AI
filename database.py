import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('chats.db')
    c = conn.cursor()

    # Enable foreign key constraints
    c.execute('PRAGMA foreign_keys = ON')

    # Drop existing tables (if required for a clean slate)
    c.execute('DROP TABLE IF EXISTS messages')
    c.execute('DROP TABLE IF EXISTS chats')

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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (chat_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def save_chat(username, chat_id, chat_data):
    conn = sqlite3.connect('chats.db')
    c = conn.cursor()

    now = datetime.now().isoformat()

    # Insert or update chat
    c.execute('''
        INSERT OR REPLACE INTO chats (chat_id, username, title, model, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        chat_id,
        username,
        chat_data.get('title', 'New Chat'),
        chat_data.get('model', 'gpt-3.5-turbo'),
        chat_data.get('created_at', now),
        now
    ))

    # Delete existing messages for this chat to refresh them
    c.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))

    # Insert new messages
    for msg in chat_data.get('messages', []):
        c.execute('''
            INSERT INTO messages (chat_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, msg['role'], msg['content'], now))

    conn.commit()
    conn.close()

def get_user_chats(username):
    conn = sqlite3.connect('chats.db')
    c = conn.cursor()

    # Get all chats for the user
    c.execute('''
        SELECT chat_id, title, model, created_at
        FROM chats
        WHERE username = ?
        ORDER BY updated_at DESC
        LIMIT 20
    ''', (username,))

    chats = {}
    for chat_id, title, model, created_at in c.fetchall():
        # Get messages for each chat
        c.execute('''
            SELECT role, content, timestamp
            FROM messages
            WHERE chat_id = ?
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

    conn.close()
    return chats

def delete_old_chats(username):
    conn = sqlite3.connect('chats.db')
    c = conn.cursor()

    # Get chat IDs ordered by updated_at
    c.execute('''
        SELECT chat_id
        FROM chats
        WHERE username = ?
        ORDER BY updated_at DESC
    ''', (username,))

    chat_ids = [row[0] for row in c.fetchall()]

    # If user has more than 20 chats, delete the oldest ones
    if len(chat_ids) > 20:
        for chat_id in chat_ids[20:]:
            c.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
            c.execute('DELETE FROM chats WHERE chat_id = ?', (chat_id,))

    conn.commit()
    conn.close()

def get_db_connection():
    """
    Establishes a connection to the SQLite database and returns the connection object.
    """
    conn = sqlite3.connect('chats.db')
    conn.row_factory = sqlite3.Row  # Optional: Makes rows dictionary-like for easier access
    return conn

# Example Usage:
# Uncomment the following lines to test the functions
# init_db()
# save_chat("user1", "chat1", {"title": "First Chat", "messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]})
# print(get_user_chats("user1"))
# delete_old_chats("user1")
