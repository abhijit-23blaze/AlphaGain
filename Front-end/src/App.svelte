<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Header from './lib/components/Header.svelte';
  import GroupChatMessage from './lib/components/GroupChatMessage.svelte';
  import GroupChatInput from './lib/components/GroupChatInput.svelte';
  import UsersPanel from './lib/components/UsersPanel.svelte';
  import Login from './lib/components/Login.svelte';
  import './app.css';
  import 'highlight.js/styles/github.css';
  
  // App state
  let isLoggedIn = false;
  let isConnecting = false;
  let username = '';
  let userId = '';
  let activeUsers: { user_id: string, username: string }[] = [];
  let messages: any[] = [];
  let websocket: WebSocket | null = null;
  let aiToggle = true;
  
  // Generate a random user ID for this session
  function generateUserId() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }
  
  // Cleanup resources on component destroy
  onDestroy(() => {
    if (websocket) {
      websocket.close();
    }
  });
  
  // Handle user login
  function handleLogin(event: CustomEvent) {
    const { username: newUsername } = event.detail;
    username = newUsername;
    userId = generateUserId();
    isConnecting = true;
    
    // Connect to WebSocket
    connectWebSocket();
  }
  
  // Establish WebSocket connection
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname === 'localhost' 
      ? 'localhost:8000' 
      : window.location.host;
    
    const wsUrl = `${protocol}//${host}/api/chat/${userId}`;
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('WebSocket connection established');
      
      // Send initial connection message with username
      sendWebSocketMessage({
        type: 'connect',
        username: username
      });
      
      isLoggedIn = true;
      isConnecting = false;
    };
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'system':
          // System message (user joined/left)
          messages = [...messages, {
            type: 'system',
            content: data.content,
            timestamp: new Date().toISOString()
          }];
          
          // Update user list if provided
          if (data.users) {
            activeUsers = data.users;
            
            // Add AI to the users list if not already present
            if (!activeUsers.find(u => u.user_id === 'ai')) {
              activeUsers = [...activeUsers, { user_id: 'ai', username: 'FinanceGPT' }];
            }
          }
          break;
          
        case 'chat':
          // Regular chat message
          messages = [...messages, {
            ...data,
            timestamp: data.timestamp || new Date().toISOString()
          }];
          break;
          
        case 'ai_stream':
          // Handle AI token streaming
          const lastMessage = messages[messages.length - 1];
          
          if (lastMessage && lastMessage.user_id === 'ai' && lastMessage.type === 'ai_stream') {
            // Append to the existing streaming message
            lastMessage.content += data.content;
            messages = [...messages.slice(0, -1), lastMessage];
          } else {
            // Create a new streaming message only if one doesn't exist yet
            messages = [...messages, {
              type: 'ai_stream',
              user_id: 'ai',
              username: 'FinanceGPT',
              content: data.content,
              timestamp: new Date().toISOString()
            }];
          }
          
          // Once complete AI response is received, change type to 'chat'
          // We'll handle this in the backend
          break;
          
        case 'ai_complete':
          // Handle the completion of AI streaming
          const streamedMessage = messages.find(msg => msg.user_id === 'ai' && msg.type === 'ai_stream');
          if (streamedMessage) {
            // Convert the streamed message to a regular chat message
            streamedMessage.type = 'chat';
            // Force a UI update
            messages = [...messages];
          }
          break;
          
        case 'typing':
          // Handle typing indicators (could implement in future)
          break;
          
        case 'error':
          console.error('WebSocket error:', data.content);
          break;
      }
      
      // Auto-scroll to bottom on new messages
      setTimeout(() => {
        const messagesDiv = document.querySelector('.message-list');
        if (messagesDiv) {
          messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
      }, 0);
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      isConnecting = false;
    };
    
    websocket.onclose = () => {
      console.log('WebSocket connection closed');
      if (isLoggedIn) {
        // Could implement reconnection logic here
      }
    };
  }
  
  // Send a message through the WebSocket
  function sendWebSocketMessage(message: any) {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }
  
  // Handle sending a message
  function handleSendMessage(content: string, aiToggleState: boolean) {
    if (!content.trim() || !websocket) return;
    
    console.log('Sending message with AI toggle:', aiToggleState);
    
    // Make sure to update the local state too
    aiToggle = aiToggleState;
    
    sendWebSocketMessage({
      type: 'chat',
      content,
      ai_toggle: aiToggleState,
      timestamp: new Date().toISOString()
    });
  }
  
  // Handle typing event
  function handleTyping() {
    sendWebSocketMessage({
      type: 'typing'
    });
  }
</script>

<main>
  {#if !isLoggedIn}
    <Login 
      isLoading={isConnecting} 
      on:login={handleLogin} 
    />
  {:else}
    <div class="chat-container">
      <Header />
      
      <div class="chat-content">
        <div class="message-panel">
          <div class="message-list">
            {#each messages as message (message.timestamp + (message.user_id || ''))}
              {#if message.type === 'system'}
                <div class="system-message">
                  {message.content}
                </div>
              {:else if message.type === 'chat' || message.type === 'ai_stream'}
                <GroupChatMessage 
                  {message}
                  currentUserId={userId}
                  isAiMessage={message.user_id === 'ai'}
                />
              {/if}
            {/each}
  </div>
          
          <GroupChatInput 
            onSendMessage={handleSendMessage}
            isLoading={false}
            bind:aiToggle={aiToggle}
            on:typing={handleTyping}
          />
  </div>

        <UsersPanel 
          users={activeUsers}
          currentUserId={userId}
        />
      </div>
    </div>
  {/if}
</main>

<style>
  main {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: #f5f7fa;
  }
  
  .chat-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    margin: 0 auto;
    width: 100%;
    max-width: 1600px;
    background-color: #fff;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  }
  
  .chat-content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  
  .message-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .message-list {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .system-message {
    padding: 0.5rem 1rem;
    background-color: #f5f5f5;
    border-radius: 4px;
    font-size: 0.85rem;
    color: #666;
    text-align: center;
    margin: 0.5rem 0;
    max-width: 80%;
    align-self: center;
  }
  
  @media (max-width: 768px) {
    .chat-content {
      flex-direction: column;
    }
    
    .users-panel {
      width: 100%;
      height: 200px;
      border-left: none;
      border-top: 1px solid #eee;
    }
  }
</style>
