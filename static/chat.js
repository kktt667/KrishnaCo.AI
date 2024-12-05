let currentModel = 'gpt-3.5-turbo';
let currentChat = null;
let chats = {};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize marked.js configuration
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true
    });

    setupEventListeners();
    loadChats();
});

function setupEventListeners() {
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.getElementById('new-chat-btn').addEventListener('click', createNewChat);
    document.getElementById('user-input').addEventListener('keypress', handleInputKeypress);
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('model-select').addEventListener('change', handleModelChange);
    document.getElementById('user-input').addEventListener('input', autoResizeTextarea);
}

async function loadChats() {
    try {
        const response = await fetch('/get_chats');
        const data = await response.json();
        chats = data.chats || {};
        updateChatList();
        
        // If there are chats, select the most recent one
        const chatIds = Object.keys(chats);
        if (chatIds.length > 0) {
            switchChat(chatIds[0]);
        }
    } catch (error) {
        console.error('Error loading chats:', error);
    }
}

function handleModelChange(e) {
    currentModel = e.target.value;
    if (currentChat) {
        chats[currentChat].model = currentModel;
        saveChat(currentChat, chats[currentChat]);
    }
}

async function handleLogout() {
    try {
        const response = await fetch('/logout', {
            method: 'POST',
        });
        
        if (response.ok) {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error logging out:', error);
    }
}

async function createNewChat() {
    const chatId = Date.now().toString();
    const chat = {
        id: chatId,
        title: 'New Chat',
        model: currentModel,
        messages: [],
        created_at: new Date().toISOString()
    };
    
    chats[chatId] = chat;
    currentChat = chatId;
    
    await saveChat(chatId, chat);
    updateChatList();
    clearMessages();
}

async function saveChat(chatId, chatData) {
    try {
        await fetch('/save_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chatId: chatId,
                chatData: chatData
            }),
        });
    } catch (error) {
        console.error('Error saving chat:', error);
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('user-input');
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

function updateChatList() {
    const chatList = document.getElementById('chat-list');
    chatList.innerHTML = '';
    
    // Sort chats by created_at in descending order
    const sortedChats = Object.entries(chats)
        .sort(([,a], [,b]) => {
            const dateA = new Date(a.created_at || 0);
            const dateB = new Date(b.created_at || 0);
            return dateB - dateA;
        });

    sortedChats.forEach(([id, chat]) => {
        const chatElement = document.createElement('div');
        chatElement.className = 'chat-item';
        if (currentChat === id) {
            chatElement.classList.add('active');
        }

        // Create container for title and buttons
        const contentContainer = document.createElement('div');
        contentContainer.className = 'chat-item-content';

        // Chat title
        const titleElement = document.createElement('span');
        titleElement.className = 'chat-title';
        titleElement.textContent = chat.title || 'New Chat';
        contentContainer.appendChild(titleElement);

        // Button container
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'chat-item-buttons';

        // Edit button
        const editButton = document.createElement('button');
        editButton.innerHTML = '✏️';
        editButton.className = 'chat-edit-btn';
        editButton.onclick = (e) => {
            e.stopPropagation();
            enableChatEditing(titleElement, id);
        };

        // Delete button
        const deleteButton = document.createElement('button');
        deleteButton.innerHTML = '🗑️';
        deleteButton.className = 'chat-delete-btn';
        deleteButton.onclick = (e) => deleteChat(id, e);

        buttonContainer.appendChild(editButton);
        buttonContainer.appendChild(deleteButton);
        contentContainer.appendChild(buttonContainer);
        chatElement.appendChild(contentContainer);

        chatElement.onclick = () => {
            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
            });
            chatElement.classList.add('active');
            switchChat(id);
        };

        chatList.appendChild(chatElement);
    });
}

function switchChat(chatId) {
    currentChat = chatId;
    const chat = chats[chatId];
    currentModel = chat.model;
    document.getElementById('model-select').value = currentModel;
    displayMessages(chat.messages);
}

function displayMessages(messages) {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
    
    messages.forEach(message => {
        const formattedMessage = formatMessage(message.content, message.role === 'assistant');
        messagesContainer.insertAdjacentHTML('beforeend', formattedMessage);
    });
    
    // Add copy buttons to code blocks
    messagesContainer.querySelectorAll('pre').forEach(pre => {
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.textContent = 'Copy';
        copyButton.onclick = function() {
            const code = pre.querySelector('code').textContent;
            navigator.clipboard.writeText(code);
            copyButton.textContent = 'Copied!';
            setTimeout(() => copyButton.textContent = 'Copy', 2000);
        };
        pre.appendChild(copyButton);
    });

    // Initialize syntax highlighting for all code blocks
    messagesContainer.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightBlock(block);
    });
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatMessage(content, isAI = false) {
    // First, escape any HTML in the content to prevent XSS
    content = content.replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Process code blocks before other markdown
    content = content.replace(/```([\s\S]*?)```/g, function(match, code) {
        return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Process inline code
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Process bold text
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Process bullet points and numbered lists
    content = content.split('\n').map(line => {
        // Numbered lists
        if (/^\d+\.\s/.test(line)) {
            return line.replace(/^\d+\.\s(.*)$/, '<li>$1</li>');
        }
        // Bullet points
        if (/^[-*]\s/.test(line)) {
            return line.replace(/^[-*]\s(.*)$/, '<li>$1</li>');
        }
        return line;
    }).join('\n');

    // Wrap lists in ul/ol tags
    content = content.replace(/<li>.*?<\/li>/g, match => {
        if (/^\d+\.\s/.test(match)) {
            return `<ol>${match}</ol>`;
        }
        return `<ul>${match}</ul>`;
    });

    const messageClass = isAI ? 'ai-message' : 'user-message';
    const roleLabel = isAI ? 'AI' : 'You';
    
    return `
        <div class="message ${messageClass}">
            <div class="message-header">
                <span class="role-label">${roleLabel}</span>
            </div>
            <div class="message-content markdown">
                ${content}
            </div>
        </div>
    `;
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    
    if (!message || !currentChat) return;
    
    const chat = chats[currentChat];
    input.value = '';
    autoResizeTextarea();

    // Add user message
    chat.messages.push({ role: 'user', content: message });
    displayMessages(chat.messages);
    
    try {
        const response = await fetch('/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: chat.model,
                messages: chat.messages
            }),
        });
        
        const data = await response.json();
        
        if (data.response) {
            // Add assistant message
            chat.messages.push({ role: 'assistant', content: data.response });
            displayMessages(chat.messages);
            
            // Save chat after receiving response
            await saveChat(currentChat, chat);
            
            // Update chat title if it's still the default
            if (chat.title === 'New Chat' && chat.messages.length >= 2) {
                chat.title = chat.messages[0].content.substring(0, 30) + '...';
                updateChatList();
                await saveChat(currentChat, chat);
            }
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('An error occurred while sending the message');
    }
}

function clearMessages() {
    document.getElementById('messages').innerHTML = '';
    document.getElementById('user-input').value = '';
}

function enableChatEditing(chatElement, chatId) {
    const currentTitle = chats[chatId].title;
    const inputElement = document.createElement('input');
    inputElement.type = 'text';
    inputElement.value = currentTitle;
    inputElement.className = 'chat-title-input';
    
    // Prevent click event from bubbling up
    inputElement.onclick = (e) => e.stopPropagation();
    
    inputElement.addEventListener('blur', async () => {
        const newTitle = inputElement.value.trim() || 'New Chat';
        await updateChatTitle(chatId, newTitle);
    });

    inputElement.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const newTitle = inputElement.value.trim() || 'New Chat';
            await updateChatTitle(chatId, newTitle);
        }
    });

    chatElement.textContent = '';
    chatElement.appendChild(inputElement);
    inputElement.focus();
}

async function updateChatTitle(chatId, newTitle) {
    chats[chatId].title = newTitle;
    await saveChat(chatId, chats[chatId]);
    updateChatList();
}

async function deleteChat(chatId, event) {
    event.stopPropagation(); // Prevent chat selection when clicking delete button
    
    if (!confirm('Are you sure you want to delete this chat?')) {
        return;
    }
    
    try {
        const response = await fetch('/delete_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ chatId }),
        });

        if (response.ok) {
            // Remove chat from local storage
            delete chats[chatId];
            
            // If the deleted chat was the current chat
            if (currentChat === chatId) {
                currentChat = null;
                clearMessages();
                
                // Find the next available chat
                const remainingChatIds = Object.keys(chats);
                if (remainingChatIds.length > 0) {
                    // Switch to the most recent chat
                    const nextChatId = remainingChatIds[0];
                    currentChat = nextChatId;
                    switchChat(nextChatId);
                }
            }
            
            // Force update of the chat list
            updateChatList();
            
            // If no chats remain, clear the messages area
            if (Object.keys(chats).length === 0) {
                clearMessages();
            }
        } else {
            throw new Error('Failed to delete chat');
        }
    } catch (error) {
        console.error('Error deleting chat:', error);
        alert('Failed to delete chat');
    }
}


function handleInputKeypress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}