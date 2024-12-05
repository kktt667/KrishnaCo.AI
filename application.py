from flask import Flask, render_template, request, jsonify, session
import datetime
import os
from dotenv import load_dotenv
from database import (
    init_db, save_chat, get_user_chats, 
    delete_old_chats, get_db_connection
)
from contextlib import contextmanager
import functools

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
load_dotenv()

# Configuration
app.secret_key = os.getenv('FLASK_SECRET_KEY')
REDPILL_API_ENDPOINT = os.getenv('REDPILL_API_ENDPOINT')
REDPILL_API_KEY = os.getenv('REDPILL_API_KEY')

# Initialize database
try:
    init_db()
except Exception as e:
    print(f"Database initialization error: {e}")

# Load user credentials
USERS = {}
for i in range(1, 21):
    user_num = f"{i:02d}"
    username = f"user{user_num}"
    USERS[username] = {
        "password": os.getenv(f"USER{user_num}_PASSWORD"),
        "name": os.getenv(f"USER{user_num}_NAME"),
    }

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated_function

class ChatApp:
    def __init__(self):
        self.chat_counter = 1

    def authenticate(self, username, password):
        return (username in USERS and 
                USERS[username]["password"] == password)

    def generate_response(self, model, messages):
        import requests
        
        headers = {
            "Authorization": f"Bearer {REDPILL_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "n": 1,
            "stream": False
        }

        try:
            response = requests.post(
                REDPILL_API_ENDPOINT,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        except requests.RequestException as e:
            print(f"API request error: {e}")
            return f"Error: Unable to generate response"

    def get_available_models(self):
        # Your existing models list...
        return ['model1', 'model2', 'model3']  # Shortened for brevity

# Routes
@app.route('/')
def index():
    if 'authenticated' not in session or not session['authenticated']:
        return render_template('login.html')
    return render_template(
        'chat.html',
        name=session['name'],
        models=ChatApp().get_available_models()
    )

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        chat_app = ChatApp()
        if chat_app.authenticate(data['username'], data['password']):
            session['authenticated'] = True
            session['username'] = data['username']
            session['name'] = USERS[data['username']]["name"]
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.get_json()
        chat_app = ChatApp()
        response = chat_app.generate_response(data['model'], data['messages'])
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_chat', methods=['POST'])
@login_required
def save_chat_route():
    try:
        data = request.get_json()
        username = session['username']
        chat_id = data['chatId']
        chat_data = data['chatData']

        save_chat(username, chat_id, chat_data)
        delete_old_chats(username)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_chats', methods=['GET'])
@login_required
def get_chats():
    try:
        username = session['username']
        chats = get_user_chats(username)
        return jsonify({'chats': chats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "ok"})

@app.route('/delete_chat', methods=['POST'])
@login_required
def delete_chat():
    try:
        data = request.get_json()
        chat_id = data.get('chatId')
        username = session['username']

        if not chat_id:
            return jsonify({'error': 'No chat ID provided'}), 400

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Delete messages
                cur.execute(
                    '''
                    DELETE FROM messages 
                    WHERE chat_id = %s AND chat_id IN (
                        SELECT chat_id FROM chats WHERE username = %s
                    )
                    ''',
                    (chat_id, username)
                )

                # Delete chat
                cur.execute(
                    '''
                    DELETE FROM chats 
                    WHERE chat_id = %s AND username = %s
                    ''',
                    (chat_id, username)
                )
                conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_ENV') == 'development')