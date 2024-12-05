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

            # Extract the response content from the API response
            response_content = response.json()["choices"][0]["message"]["content"]

            # Enhance the HTML formatting for a more appealing display
            formatted_response = f"""
            <div style="background-color: #f3f4f6; border-radius: 10px; padding: 20px; margin: 20px 0;">
                <h2 style="color: #333; font-weight: bold; margin-bottom: 10px; font-size: 1.3em;">AI Response:</h2>
                <div style="border: 1px solid #ccc; padding: 15px; border-radius: 5px;">
                    {response_content}
                </div>
            </div>
            """

            return formatted_response

        except requests.RequestException as e:
            print(f"API request error: {e}")
            return f"Error: Unable to generate response"

    def get_available_models(self):
        return ['o1-preview', 'o1-preview-2024-09-12', 'o1-mini', 'o1-mini-2024-09-12', 'gpt-4o-mini', 'gpt-4o-mini-2024-07-18', 'gpt-4o', 'gpt-4o-2024-08-06', 'gpt-4o-2024-05-13', 'gpt-4', 'gpt-4-1106-preview', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-3.5-turbo', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-instruct', 'llama-2-7b-chat-fp16', 'llama-3.1-8b-instruct', 'llama-3-8b-instruct', 'llama-3-8b-instruct-awq', 'mistral-7b-instruct-v0.1', 'mistral-7b-instruct-v0.2', 'qwen1.5-0.5b-chat', 'qwen1.5-7b-chat-awq', 'qwen1.5-1.8b-chat', 'qwen1.5-14b-chat-awq', 'gemma-2b-it-lora', 'gemma-7b-it-lora', 'gemma-7b-it', 'claude-3-5-sonnet-20241022', 'claude-3-5-sonnet-20240620', 'claude-3-opus-20240229', 'claude-3-haiku-20240307', 'claude-3-sonnet-20240229', 'text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002', 'mistralai/ministral-8b', 'mistralai/ministral-3b', 'qwen/qwen-2.5-7b-instruct', 'nvidia/llama-3.1-nemotron-70b-instruct', 'x-ai/grok-2', 'inflection/inflection-3-productivity', 'inflection/inflection-3-pi', 'google/gemini-flash-1.5-8b', 'liquid/lfm-40b', 'liquid/lfm-40b:free', 'thedrummer/rocinante-12b', 'eva-unit-01/eva-qwen-2.5-14b', 'anthracite-org/magnum-v2-72b', 'meta-llama/llama-3.2-3b-instruct:free', 'meta-llama/llama-3.2-3b-instruct', 'meta-llama/llama-3.2-1b-instruct:free', 'meta-llama/llama-3.2-1b-instruct', 'meta-llama/llama-3.2-90b-vision-instruct', 'meta-llama/llama-3.2-11b-vision-instruct:free', 'meta-llama/llama-3.2-11b-vision-instruct', 'perplexity/llama-3.1-sonar-small-128k-chat', 'qwen/qwen-2.5-72b-instruct', 'qwen/qwen-2-vl-72b-instruct', 'neversleep/llama-3.1-lumimaid-8b', 'openai/o1-mini-2024-09-12', 'openai/o1-mini', 'openai/o1-preview-2024-09-12', 'openai/o1-preview', 'mistralai/pixtral-12b', 'cohere/command-r-plus-08-2024', 'cohere/command-r-08-2024', 'meta-llama/llama-3.1-70b-instruct:free', 'anthropic/claude-2', 'qwen/qwen-2-vl-7b-instruct', 'google/gemini-flash-1.5-8b-exp', 'sao10k/l3.1-euryale-70b', 'google/gemini-flash-1.5-exp', 'ai21/jamba-1-5-large', 'ai21/jamba-1-5-mini', 'microsoft/phi-3.5-mini-128k-instruct', 'nousresearch/hermes-3-llama-3.1-70b', 'nousresearch/hermes-3-llama-3.1-405b:free', 'nousresearch/hermes-3-llama-3.1-405b', 'nousresearch/hermes-3-llama-3.1-405b:extended', 'perplexity/llama-3.1-sonar-huge-128k-online', 'openai/chatgpt-4o-latest', 'sao10k/l3-lunaris-8b', 'aetherwiing/mn-starcannon-12b', 'openai/gpt-4o-2024-08-06', 'meta-llama/llama-3.1-405b', 'nothingiisreal/mn-celeste-12b', 'google/gemini-pro-1.5-exp', 'perplexity/llama-3.1-sonar-large-128k-online', 'perplexity/llama-3.1-sonar-large-128k-chat', 'perplexity/llama-3.1-sonar-small-128k-online', 'meta-llama/llama-3.1-70b-instruct', 'meta-llama/llama-3.1-8b-instruct:free', 'meta-llama/llama-3.1-405b-instruct:free', 'meta-llama/llama-3.1-405b-instruct', 'mistralai/codestral-mamba', 'mistralai/mistral-nemo', 'openai/gpt-4o-mini-2024-07-18', 'openai/gpt-4o-mini', 'qwen/qwen-2-7b-instruct:free', 'qwen/qwen-2-7b-instruct', 'mistralai/mistral-tiny', 'google/gemma-2-27b-it', 'alpindale/magnum-72b', 'nousresearch/hermes-2-theta-llama-3-8b', 'google/gemma-2-9b-it:free', 'google/gemma-2-9b-it', 'ai21/jamba-instruct', 'sao10k/l3-euryale-70b', 'cognitivecomputations/dolphin-mixtral-8x22b', 'meta-llama/llama-3-70b-instruct', 'qwen/qwen-2-72b-instruct', 'nousresearch/hermes-2-pro-llama-3-8b', 'mistralai/mistral-7b-instruct-v0.3', 'mistralai/mistral-7b-instruct:free', 'mistralai/mistral-7b-instruct', 'mistralai/mistral-7b-instruct:nitro', 'microsoft/phi-3-mini-128k-instruct:free', 'microsoft/phi-3-mini-128k-instruct', 'microsoft/phi-3-medium-128k-instruct:free', 'microsoft/phi-3-medium-128k-instruct', 'neversleep/llama-3-lumimaid-70b', 'google/gemini-flash-1.5', 'openai/gpt-4-0314', 'deepseek/deepseek-chat', 'perplexity/llama-3-sonar-large-32k-online', 'perplexity/llama-3-sonar-large-32k-chat', 'perplexity/llama-3-sonar-small-32k-chat', 'meta-llama/llama-guard-2-8b', 'openai/gpt-4o-2024-05-13', 'openai/gpt-4o', 'openai/gpt-4o:extended', 'qwen/qwen-72b-chat', 'qwen/qwen-110b-chat', 'neversleep/llama-3-lumimaid-8b', 'neversleep/llama-3-lumimaid-8b:extended', 'sao10k/fimbulvetr-11b-v2', 'meta-llama/llama-3-70b-instruct:nitro', 'meta-llama/llama-3-8b-instruct:free', 'meta-llama/llama-3-8b-instruct:nitro', 'meta-llama/llama-3-8b-instruct:extended', 'mistralai/mixtral-8x22b-instruct', 'microsoft/wizardlm-2-7b', 'microsoft/wizardlm-2-8x22b', 'google/gemini-pro-1.5', 'openai/gpt-4-turbo', 'cohere/command-r-plus', 'cohere/command-r-plus-04-2024', 'databricks/dbrx-instruct', 'sophosympatheia/midnight-rose-70b', 'cohere/command-r', 'cohere/command', 'anthropic/claude-3-haiku', 'anthropic/claude-3-haiku:beta', 'anthropic/claude-3-sonnet:beta', 'anthropic/claude-3-opus', 'anthropic/claude-3-opus:beta', 'cohere/command-r-03-2024', 'mistralai/mistral-large', 'openai/gpt-4-turbo-preview', 'openai/gpt-3.5-turbo-0613', 'nousresearch/nous-hermes-2-mixtral-8x7b-dpo', 'mistralai/mistral-medium', 'mistralai/mistral-small', 'cognitivecomputations/dolphin-mixtral-8x7b', 'google/gemini-pro', 'google/gemini-pro-vision', 'mistralai/mixtral-8x7b-instruct', 'mistralai/mixtral-8x7b-instruct:nitro', 'mistralai/mixtral-8x7b', 'gryphe/mythomist-7b:free', 'gryphe/mythomist-7b', 'openchat/openchat-7b:free', 'openchat/openchat-7b', 'neversleep/noromaid-20b', 'anthropic/claude-instant-1.1', 'anthropic/claude-2.1', 'anthropic/claude-2.1:beta', 'anthropic/claude-2:beta', 'teknium/openhermes-2.5-mistral-7b', 'openai/gpt-4-vision-preview', 'lizpreciatior/lzlv-70b-fp16-hf', 'alpindale/goliath-120b', 'undi95/toppy-m-7b:free', 'undi95/toppy-m-7b', 'undi95/toppy-m-7b:nitro', 'openrouter/auto', 'openai/gpt-4-1106-preview', 'openai/gpt-3.5-turbo-1106', 'google/palm-2-codechat-bison-32k', 'google/palm-2-chat-bison-32k', 'jondurbin/airoboros-l2-70b', 'xwin-lm/xwin-lm-70b', 'openai/gpt-3.5-turbo-instruct', 'pygmalionai/mythalion-13b', 'openai/gpt-4-32k-0314', 'openai/gpt-4-32k', 'openai/gpt-3.5-turbo-16k', 'nousresearch/nous-hermes-llama2-13b', 'huggingfaceh4/zephyr-7b-beta:free', 'mancer/weaver', 'anthropic/claude-instant-1.0', 'anthropic/claude-1.2', 'anthropic/claude-1', 'anthropic/claude-instant-1', 'anthropic/claude-instant-1:beta', 'anthropic/claude-2.0', 'anthropic/claude-2.0:beta', 'undi95/remm-slerp-l2-13b', 'undi95/remm-slerp-l2-13b:extended', 'google/palm-2-codechat-bison', 'google/palm-2-chat-bison', 'gryphe/mythomax-l2-13b:free', 'gryphe/mythomax-l2-13b', 'gryphe/mythomax-l2-13b:nitro', 'gryphe/mythomax-l2-13b:extended', 'meta-llama/llama-2-13b-chat', 'openai/gpt-4', 'openai/gpt-3.5-turbo-0125', 'openai/gpt-3.5-turbo', 'anthropic/claude-3.5-sonnet:beta', 'openai/gpt-4-turbo-2024-04-09', 'meta-llama/llama-2-7b-chat-fp16', 'meta-llama/llama-3.1-8b-instruct', 'meta-llama/llama-3-8b-instruct', 'meta-llama/llama-3-8b-instruct-awq', 'mistralai/mistral-7b-instruct-v0.1', 'mistralai/mistral-7b-instruct-v0.2', 'qwen/qwen1.5-0.5b-chat', 'qwen/qwen1.5-7b-chat-awq', 'qwen/qwen1.5-1.8b-chat', 'qwen/qwen1.5-14b-chat-awq', 'google/gemma-2b-it-lora', 'anthropic/claude-3-5-sonnet', 'google/gemma-7b-it-lora', 'google/gemma-7b-it', 'anthropic/claude-3-5-sonnet-20240620', 'anthropic/claude-3-sonnet']  

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