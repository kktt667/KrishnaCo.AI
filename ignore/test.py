import streamlit as st
import datetime
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config must be the first Streamlit command
st.set_page_config(page_title="AI Chat App", layout="wide")

# Custom CSS for better aesthetics
st.markdown("""
<style>
    /* Color variables */
    :root {
        --primary-pink: #FF69B4;
        --secondary-pink: #FFB6C1;
        --background-pink: #FFF0F5;
        --dark-pink: #DB7093;
        --text-color: #4A4A4A;
    }

    /* Modern chat bubbles */
    .user-message {
        background-color: var(--primary-pink);
        color: white;
        padding: 12px 16px;
        border-radius: 20px;
        margin: 8px 0;
        margin-left: 20%;
        margin-right: 5%;
        border-bottom-right-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background-color: var(--secondary-pink);
        color: var(--text-color);
        padding: 12px 16px;
        border-radius: 20px;
        margin: 8px 0;
        margin-right: 20%;
        margin-left: 5%;
        border-bottom-left-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .stSidebar {
        background-color: var(--background-pink);
        padding: 1rem;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        padding: 8px 12px;
        border: 1px solid var(--dark-pink);
        background-color: var(--primary-pink);
        color: white;
        margin: 2px 0;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: var(--dark-pink);
        border-color: var(--primary-pink);
    }
    
    /* Chat container */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: calc(100vh - 80px);
        position: relative;
        background-color: var(--background-pink);
        padding: 1rem;
        border-radius: 10px;
    }
    
    /* Messages area */
    .messages-area {
        flex-grow: 1;
        overflow-y: auto;
        padding: 10px;
        margin-bottom: 60px;  /* Space for input box */
    }
    
    /* Input container */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 350px;  /* Adjust based on sidebar width */
        right: 0;
        padding: 1rem;
        background-color: white;
        border-top: 1px solid var(--secondary-pink);
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    
    /* Input field styling */
    .stTextInput>div>div>input {
        background-color: white;
        color: var(--text-color);
        border-radius: 20px;
        border: 2px solid var(--secondary-pink);
        padding: 8px 16px;
        font-size: 16px;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: var(--primary-pink);
        box-shadow: 0 0 0 2px rgba(255,105,180,0.2);
    }
    
    /* Title styling */
    .chat-title {
        color: var(--text-color);
        font-size: 1.5em;
        margin-bottom: 1rem;
        padding: 0.5rem;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: var(--primary-pink) !important;
    }
    
    /* Select box styling */
    .stSelectbox select {
        background-color: white;
        border: 2px solid var(--secondary-pink);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Simple credentials
USERS = {
    "jsmith": {"password": "abc123", "name": "John Smith"},
    "rbriggs": {"password": "def456", "name": "Rebecca Briggs"}
}

# RedPill API configuration
REDPILL_API_ENDPOINT = os.getenv('REDPILL_API_ENDPOINT')
REDPILL_API_KEY = os.getenv('REDPILL_API_KEY')

class ChatApp:
    def __init__(self):
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.name = None
        if 'chats' not in st.session_state:
            st.session_state.chats = {}
        if 'current_chat_id' not in st.session_state:
            st.session_state.current_chat_id = None
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = None
        if 'user_input' not in st.session_state:
            st.session_state.user_input = ""
        if 'editing_chat_id' not in st.session_state:
            st.session_state.editing_chat_id = None
        if 'chat_counter' not in st.session_state:
            st.session_state.chat_counter = 1

    def authenticate(self, username: str, password: str) -> bool:
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.name = USERS[username]["name"]
            return True
        return False

    def logout(self):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    def get_available_models(self):
        # For now, return a static list of available models
        available_models = ['o1-preview', 'o1-preview-2024-09-12', 'o1-mini', 'o1-mini-2024-09-12', 'gpt-4o-mini', 'gpt-4o-mini-2024-07-18', 'gpt-4o', 'gpt-4o-2024-08-06', 'gpt-4o-2024-05-13', 'gpt-4', 'gpt-4-1106-preview', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09', 'gpt-3.5-turbo', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-instruct', 'llama-2-7b-chat-fp16', 'llama-3.1-8b-instruct', 'llama-3-8b-instruct', 'llama-3-8b-instruct-awq', 'mistral-7b-instruct-v0.1', 'mistral-7b-instruct-v0.2', 'qwen1.5-0.5b-chat', 'qwen1.5-7b-chat-awq', 'qwen1.5-1.8b-chat', 'qwen1.5-14b-chat-awq', 'gemma-2b-it-lora', 'gemma-7b-it-lora', 'gemma-7b-it', 'claude-3-5-sonnet-20241022', 'claude-3-5-sonnet-20240620', 'claude-3-opus-20240229', 'claude-3-haiku-20240307', 'claude-3-sonnet-20240229', 'text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002', 'mistralai/ministral-8b', 'mistralai/ministral-3b', 'qwen/qwen-2.5-7b-instruct', 'nvidia/llama-3.1-nemotron-70b-instruct', 'x-ai/grok-2', 'inflection/inflection-3-productivity', 'inflection/inflection-3-pi', 'google/gemini-flash-1.5-8b', 'liquid/lfm-40b', 'liquid/lfm-40b:free', 'thedrummer/rocinante-12b', 'eva-unit-01/eva-qwen-2.5-14b', 'anthracite-org/magnum-v2-72b', 'meta-llama/llama-3.2-3b-instruct:free', 'meta-llama/llama-3.2-3b-instruct', 'meta-llama/llama-3.2-1b-instruct:free', 'meta-llama/llama-3.2-1b-instruct', 'meta-llama/llama-3.2-90b-vision-instruct', 'meta-llama/llama-3.2-11b-vision-instruct:free', 'meta-llama/llama-3.2-11b-vision-instruct', 'perplexity/llama-3.1-sonar-small-128k-chat', 'qwen/qwen-2.5-72b-instruct', 'qwen/qwen-2-vl-72b-instruct', 'neversleep/llama-3.1-lumimaid-8b', 'openai/o1-mini-2024-09-12', 'openai/o1-mini', 'openai/o1-preview-2024-09-12', 'openai/o1-preview', 'mistralai/pixtral-12b', 'cohere/command-r-plus-08-2024', 'cohere/command-r-08-2024', 'meta-llama/llama-3.1-70b-instruct:free', 'anthropic/claude-2', 'qwen/qwen-2-vl-7b-instruct', 'google/gemini-flash-1.5-8b-exp', 'sao10k/l3.1-euryale-70b', 'google/gemini-flash-1.5-exp', 'ai21/jamba-1-5-large', 'ai21/jamba-1-5-mini', 'microsoft/phi-3.5-mini-128k-instruct', 'nousresearch/hermes-3-llama-3.1-70b', 'nousresearch/hermes-3-llama-3.1-405b:free', 'nousresearch/hermes-3-llama-3.1-405b', 'nousresearch/hermes-3-llama-3.1-405b:extended', 'perplexity/llama-3.1-sonar-huge-128k-online', 'openai/chatgpt-4o-latest', 'sao10k/l3-lunaris-8b', 'aetherwiing/mn-starcannon-12b', 'openai/gpt-4o-2024-08-06', 'meta-llama/llama-3.1-405b', 'nothingiisreal/mn-celeste-12b', 'google/gemini-pro-1.5-exp', 'perplexity/llama-3.1-sonar-large-128k-online', 'perplexity/llama-3.1-sonar-large-128k-chat', 'perplexity/llama-3.1-sonar-small-128k-online', 'meta-llama/llama-3.1-70b-instruct', 'meta-llama/llama-3.1-8b-instruct:free', 'meta-llama/llama-3.1-405b-instruct:free', 'meta-llama/llama-3.1-405b-instruct', 'mistralai/codestral-mamba', 'mistralai/mistral-nemo', 'openai/gpt-4o-mini-2024-07-18', 'openai/gpt-4o-mini', 'qwen/qwen-2-7b-instruct:free', 'qwen/qwen-2-7b-instruct', 'mistralai/mistral-tiny', 'google/gemma-2-27b-it', 'alpindale/magnum-72b', 'nousresearch/hermes-2-theta-llama-3-8b', 'google/gemma-2-9b-it:free', 'google/gemma-2-9b-it', 'ai21/jamba-instruct', 'sao10k/l3-euryale-70b', 'cognitivecomputations/dolphin-mixtral-8x22b', 'meta-llama/llama-3-70b-instruct', 'qwen/qwen-2-72b-instruct', 'nousresearch/hermes-2-pro-llama-3-8b', 'mistralai/mistral-7b-instruct-v0.3', 'mistralai/mistral-7b-instruct:free', 'mistralai/mistral-7b-instruct', 'mistralai/mistral-7b-instruct:nitro', 'microsoft/phi-3-mini-128k-instruct:free', 'microsoft/phi-3-mini-128k-instruct', 'microsoft/phi-3-medium-128k-instruct:free', 'microsoft/phi-3-medium-128k-instruct', 'neversleep/llama-3-lumimaid-70b', 'google/gemini-flash-1.5', 'openai/gpt-4-0314', 'deepseek/deepseek-chat', 'perplexity/llama-3-sonar-large-32k-online', 'perplexity/llama-3-sonar-large-32k-chat', 'perplexity/llama-3-sonar-small-32k-chat', 'meta-llama/llama-guard-2-8b', 'openai/gpt-4o-2024-05-13', 'openai/gpt-4o', 'openai/gpt-4o:extended', 'qwen/qwen-72b-chat', 'qwen/qwen-110b-chat', 'neversleep/llama-3-lumimaid-8b', 'neversleep/llama-3-lumimaid-8b:extended', 'sao10k/fimbulvetr-11b-v2', 'meta-llama/llama-3-70b-instruct:nitro', 'meta-llama/llama-3-8b-instruct:free', 'meta-llama/llama-3-8b-instruct:nitro', 'meta-llama/llama-3-8b-instruct:extended', 'mistralai/mixtral-8x22b-instruct', 'microsoft/wizardlm-2-7b', 'microsoft/wizardlm-2-8x22b', 'google/gemini-pro-1.5', 'openai/gpt-4-turbo', 'cohere/command-r-plus', 'cohere/command-r-plus-04-2024', 'databricks/dbrx-instruct', 'sophosympatheia/midnight-rose-70b', 'cohere/command-r', 'cohere/command', 'anthropic/claude-3-haiku', 'anthropic/claude-3-haiku:beta', 'anthropic/claude-3-sonnet:beta', 'anthropic/claude-3-opus', 'anthropic/claude-3-opus:beta', 'cohere/command-r-03-2024', 'mistralai/mistral-large', 'openai/gpt-4-turbo-preview', 'openai/gpt-3.5-turbo-0613', 'nousresearch/nous-hermes-2-mixtral-8x7b-dpo', 'mistralai/mistral-medium', 'mistralai/mistral-small', 'cognitivecomputations/dolphin-mixtral-8x7b', 'google/gemini-pro', 'google/gemini-pro-vision', 'mistralai/mixtral-8x7b-instruct', 'mistralai/mixtral-8x7b-instruct:nitro', 'mistralai/mixtral-8x7b', 'gryphe/mythomist-7b:free', 'gryphe/mythomist-7b', 'openchat/openchat-7b:free', 'openchat/openchat-7b', 'neversleep/noromaid-20b', 'anthropic/claude-instant-1.1', 'anthropic/claude-2.1', 'anthropic/claude-2.1:beta', 'anthropic/claude-2:beta', 'teknium/openhermes-2.5-mistral-7b', 'openai/gpt-4-vision-preview', 'lizpreciatior/lzlv-70b-fp16-hf', 'alpindale/goliath-120b', 'undi95/toppy-m-7b:free', 'undi95/toppy-m-7b', 'undi95/toppy-m-7b:nitro', 'openrouter/auto', 'openai/gpt-4-1106-preview', 'openai/gpt-3.5-turbo-1106', 'google/palm-2-codechat-bison-32k', 'google/palm-2-chat-bison-32k', 'jondurbin/airoboros-l2-70b', 'xwin-lm/xwin-lm-70b', 'openai/gpt-3.5-turbo-instruct', 'pygmalionai/mythalion-13b', 'openai/gpt-4-32k-0314', 'openai/gpt-4-32k', 'openai/gpt-3.5-turbo-16k', 'nousresearch/nous-hermes-llama2-13b', 'huggingfaceh4/zephyr-7b-beta:free', 'mancer/weaver', 'anthropic/claude-instant-1.0', 'anthropic/claude-1.2', 'anthropic/claude-1', 'anthropic/claude-instant-1', 'anthropic/claude-instant-1:beta', 'anthropic/claude-2.0', 'anthropic/claude-2.0:beta', 'undi95/remm-slerp-l2-13b', 'undi95/remm-slerp-l2-13b:extended', 'google/palm-2-codechat-bison', 'google/palm-2-chat-bison', 'gryphe/mythomax-l2-13b:free', 'gryphe/mythomax-l2-13b', 'gryphe/mythomax-l2-13b:nitro', 'gryphe/mythomax-l2-13b:extended', 'meta-llama/llama-2-13b-chat', 'openai/gpt-4', 'openai/gpt-3.5-turbo-0125', 'openai/gpt-3.5-turbo', 'anthropic/claude-3.5-sonnet:beta', 'openai/gpt-4-turbo-2024-04-09', 'meta-llama/llama-2-7b-chat-fp16', 'meta-llama/llama-3.1-8b-instruct', 'meta-llama/llama-3-8b-instruct', 'meta-llama/llama-3-8b-instruct-awq', 'mistralai/mistral-7b-instruct-v0.1', 'mistralai/mistral-7b-instruct-v0.2', 'qwen/qwen1.5-0.5b-chat', 'qwen/qwen1.5-7b-chat-awq', 'qwen/qwen1.5-1.8b-chat', 'qwen/qwen1.5-14b-chat-awq', 'google/gemma-2b-it-lora', 'anthropic/claude-3-5-sonnet', 'google/gemma-7b-it-lora', 'google/gemma-7b-it', 'anthropic/claude-3-5-sonnet-20240620', 'anthropic/claude-3-sonnet']
        return available_models

    def generate_response(self, model: str, messages: list) -> str:
        headers = {
            "Authorization": f"Bearer {REDPILL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Create the request body according to the API specifications
        data = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,  # You can adjust these parameters
            "max_tokens": 1000,  # as needed
            "n": 1,             # Number of completions to generate
            "stream": False     # Set to False for synchronous responses
        }

        try:
            
            response = requests.post(
                REDPILL_API_ENDPOINT,
                headers=headers,
                json=data,
                timeout=30
            )
            

            if response.status_code != 200:
                error_message = f"API Error: {response.status_code} - {response.text}"
                st.error(error_message)
                return error_message

            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            error_message = f"Request Error: {str(e)}"
            st.error(error_message)
            return error_message
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            st.error(error_message)
            return error_message

    def create_new_chat(self):
        chat_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        chat_name = f"Chat {st.session_state.chat_counter}"
        st.session_state.chat_counter += 1
        
        st.session_state.chats[chat_id] = {
            "title": chat_name,
            "model": st.session_state.selected_model,
            "messages": [],
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return chat_id

    def delete_chat(self, chat_id):
        if chat_id == st.session_state.current_chat_id:
            st.session_state.current_chat_id = None
        del st.session_state.chats[chat_id]

    def handle_input(self):
        if st.session_state.user_input:
            user_message = st.session_state.user_input
            current_chat = st.session_state.chats[st.session_state.current_chat_id]
            
            # Add user message
            current_chat['messages'].append({
                'role': 'user',
                'content': user_message
            })

            # Get AI response
            ai_response = self.generate_response(
                current_chat['model'],
                current_chat['messages']
            )
            
            # Add AI response
            current_chat['messages'].append({
                'role': 'assistant',
                'content': ai_response
            })

            # Clear input
            st.session_state.user_input = ""
            # Remove the st.rerun() from here
            
    def display_message(self, role: str, content: str):
            if role == "user":
                st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)

    def run(self):
        if not st.session_state.authenticated:
            # Login form in sidebar
            with st.sidebar:
                st.title("Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Login"):
                    if self.authenticate(username, password):
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        else:
            # User is authenticated
            with st.sidebar:
                st.title(f"Welcome {st.session_state.name}")
                if st.button("Logout", key="logout"):
                    self.logout()

                st.divider()

                # Model selection
                models = self.get_available_models()
                st.session_state.selected_model = st.selectbox(
                    "Select Model",
                    models,
                    key="model_selector"
                )

                # New Chat button
                if st.button("New Chat"):
                    st.session_state.current_chat_id = self.create_new_chat()
                    st.session_state.editing_chat_id = None
                    st.rerun()

                st.divider()

                # Chat history
                st.subheader("Your Chats")
                for chat_id, chat_data in st.session_state.chats.items():
                    if st.session_state.editing_chat_id == chat_id:
                        # Edit mode
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            edited_name = st.text_input(
                                "Edit name",
                                value=chat_data['title'],
                                max_chars=30,
                                key=f"edit_{chat_id}"
                            )
                            if edited_name != chat_data['title']:
                                chat_data['title'] = edited_name
                                st.session_state.editing_chat_id = None
                                st.rerun()
                        with col2:
                            if st.button("✓", key=f"save_{chat_id}"):
                                st.session_state.editing_chat_id = None
                                st.rerun()
                    else:
                        # Display mode
                        col1, col2, col3 = st.columns([6, 1, 1])
                        with col1:
                            if st.button(chat_data['title'], key=f"chat_{chat_id}"):
                                st.session_state.current_chat_id = chat_id
                                st.rerun()
                        with col2:
                            if st.button("✏️", key=f"edit_{chat_id}"):
                                st.session_state.editing_chat_id = chat_id
                                st.rerun()
                        with col3:
                            if st.button("🗑️", key=f"delete_{chat_id}"):
                                self.delete_chat(chat_id)
                                st.rerun()

            # Main chat interface
            if st.session_state.current_chat_id:
                current_chat = st.session_state.chats[st.session_state.current_chat_id]
                
                # Container for the entire chat interface
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                
                # Title area
                st.markdown(f'<div class="chat-title">{current_chat["title"]}<br><small>Using {current_chat["model"]}</small></div>', unsafe_allow_html=True)
                
                # Messages area
                st.markdown('<div class="messages-area">', unsafe_allow_html=True)
                messages_container = st.container()
                with messages_container:
                    for message in current_chat['messages']:
                        self.display_message(message['role'], message['content'])
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Input area
                st.markdown('<div class="input-container">', unsafe_allow_html=True)
                if 'previous_input' not in st.session_state:
                    st.session_state.previous_input = ""
                
                user_input = st.text_input(
                    "",
                    placeholder="Type your message here... (Press Enter to send)",
                    key="user_input"
                )
                
                if user_input and user_input != st.session_state.previous_input:
                    with st.spinner("Generating response..."):
                        # Your existing message handling code...
                        current_chat['messages'].append({
                            'role': 'user',
                            'content': user_input
                        })
                        
                        ai_response = self.generate_response(
                            current_chat['model'],
                            current_chat['messages']
                        )
                        
                        current_chat['messages'].append({
                            'role': 'assistant',
                            'content': ai_response
                        })
                        
                        st.session_state.previous_input = user_input
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    app = ChatApp()
    app.run()
    