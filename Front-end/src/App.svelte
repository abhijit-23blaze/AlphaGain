<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Header from './lib/components/Header.svelte';
  import GroupChatMessage from './lib/components/GroupChatMessage.svelte';
  import GroupChatInput from './lib/components/GroupChatInput.svelte';
  import UsersPanel from './lib/components/UsersPanel.svelte';
  import Login from './lib/components/Login.svelte';
  import NewsWidget from './lib/components/artifacts/NewsWidget.svelte';
  import StockChart from './lib/components/artifacts/StockChart.svelte';
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
  
  // Artifact state
  let currentTab = 'chart'; // 'chart', 'news', 'users'
  
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
  
  // Change artifact tab
  function setTab(tab: string) {
    currentTab = tab;
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
      <Header username={username} />
      
      <div class="main-content">
        <div class="chat-panel">
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

        <div class="artifacts-panel">
          <div class="tab-container">
            <button 
              class="tab-button {currentTab === 'chart' ? 'active' : ''}" 
              on:click={() => setTab('chart')}
            >
              📈 Charts
            </button>
            <button 
              class="tab-button {currentTab === 'news' ? 'active' : ''}" 
              on:click={() => setTab('news')}
            >
              📰 News
            </button>
            <button 
              class="tab-button {currentTab === 'users' ? 'active' : ''}" 
              on:click={() => setTab('users')}
            >
              👥 Users
            </button>
          </div>
          
          <div class="artifact-container card">
            {#if currentTab === 'chart'}
              <StockChart />
            {:else if currentTab === 'news'}
              <NewsWidget />
            {:else if currentTab === 'users'}
              <UsersPanel 
                users={activeUsers}
                currentUserId={userId}
              />
            {/if}
          </div>
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  main {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--primary-darkest);
  }
  
  .chat-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    width: 100%;
    background-color: var(--primary-dark);
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.2);
  }
  
  .main-content {
    flex: 1;
    display: flex;
    overflow: hidden;
    padding: 0 0.5rem;
  }
  
  .chat-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border-right: 1px solid var(--border-color);
    margin-right: 0.5rem;
  }
  
  .message-list {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .artifacts-panel {
    width: 40%;
    min-width: 350px;
    display: flex;
    flex-direction: column;
    padding: 1rem;
    overflow-y: auto;
    background-color: var(--primary-dark);
  }
  
  .artifact-container {
    flex: 1;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
  }
  
  .system-message {
    padding: 0.5rem 1rem;
    background-color: var(--primary-medium);
    border-radius: 4px;
    font-size: 0.85rem;
    color: var(--text-muted);
    text-align: center;
    margin: 0.5rem 0;
    max-width: 80%;
    align-self: center;
  }
  
  @media (max-width: 1024px) {
    .main-content {
      flex-direction: column;
      padding: 0;
    }
    
    .artifacts-panel {
      width: 100%;
      min-width: 0;
      max-height: 40%;
    }
    
    .chat-panel {
      border-right: none;
      border-bottom: 1px solid var(--border-color);
      margin-right: 0;
    }
  }
</style>
