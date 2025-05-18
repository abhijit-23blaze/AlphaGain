<script lang="ts">
  import { onMount } from 'svelte';
  import ChatMessage from './lib/components/ChatMessage.svelte';
  import ChatInput from './lib/components/ChatInput.svelte';
  import Header from './lib/components/Header.svelte';
  import './app.css';
  import 'highlight.js/styles/github.css';
  import type { Message } from './lib/types';
  import { fetchChatResponse, streamChatResponse } from './lib/api';

  let messages: Message[] = [];
  let isLoading = false;
  let useStreaming = true; // Set to true by default to use streaming
  let abortController: AbortController | null = null;

  // Add a welcome message
  onMount(() => {
    messages = [
      {
        role: 'assistant',
        content: 'Welcome to FinanceGPT! Ask me anything about stocks, financial data, or investment strategies.'
      }
    ];
  });

  // Function to stop the current generation
  function stopGeneration() {
    if (abortController) {
      abortController.abort();
      abortController = null;
      isLoading = false;
    }
  }

  // Handle sending a message
  async function handleSendMessage(content: string) {
    if (!content.trim()) return;
    
    // Add user message to the list
    const userMessage: Message = {
      role: 'user',
      content
    };
    
    messages = [...messages, userMessage];
    isLoading = true;
    
    try {
      if (useStreaming) {
        // Create a new abort controller for this request
        abortController = new AbortController();
        
        // Add an empty assistant message that we'll stream content into
        const assistantMessage: Message = {
          role: 'assistant',
          content: ''
        };
        messages = [...messages, assistantMessage];
        
        // Use generator to stream the response
        streamChatResponse(
          messages.slice(0, -1),
          // On each chunk
          (chunk) => {
            assistantMessage.content += chunk;
            messages = [...messages.slice(0, -1), { ...assistantMessage }];
          },
          // On done
          () => {
            isLoading = false;
            abortController = null;
          },
          // On error
          (error) => {
            if (error.name === 'AbortError') {
              console.log('Request was aborted');
            } else {
              console.error('Error streaming chat response:', error);
              assistantMessage.content += '\n\n(Error: The response was interrupted)';
              messages = [...messages.slice(0, -1), assistantMessage];
            }
            isLoading = false;
            abortController = null;
          },
          // Pass the abort signal
          abortController.signal
        );
      } else {
        // Use non-streaming API
        const response = await fetchChatResponse(messages);
        
        // Add assistant response
        if (response && response.content) {
          messages = [...messages, {
            role: 'assistant',
            content: response.content
          }];
        }
        isLoading = false;
        abortController = null;
      }
    } catch (error) {
      console.error('Error fetching chat response:', error);
      messages = [...messages, {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.'
      }];
      isLoading = false;
      abortController = null;
    }
  }
</script>

<main>
  <div class="chat-container">
    <Header />
    
    <div class="message-list">
      {#each messages as message}
        <ChatMessage {message} />
      {/each}
      
      {#if isLoading}
        <div class="loading">
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <button class="stop-button" on:click={stopGeneration}>
            <span class="stop-icon"></span>
            Stop generating
          </button>
        </div>
      {/if}
    </div>
    
    <ChatInput onSendMessage={handleSendMessage} />
  </div>
</main>

<style>
  main {
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  .chat-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    max-width: 1000px;
    margin: 0 auto;
    width: 100%;
    background-color: #fff;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  }
  
  .message-list {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    gap: 0.5rem;
  }
  
  .loading-dots {
    display: flex;
    align-items: center;
  }
  
  .loading-dots span {
    width: 8px;
    height: 8px;
    margin: 0 4px;
    background-color: #666;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
  }
  
  .loading-dots span:nth-child(1) {
    animation-delay: -0.32s;
  }
  
  .loading-dots span:nth-child(2) {
    animation-delay: -0.16s;
  }
  
  .stop-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background-color: #f2f2f2;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    color: #333;
    transition: background-color 0.2s;
  }
  
  .stop-button:hover {
    background-color: #e0e0e0;
  }
  
  .stop-icon {
    display: block;
    width: 12px;
    height: 12px;
    background-color: #cc0000;
    border-radius: 2px;
  }
  
  @keyframes bounce {
    0%, 80%, 100% {
      transform: scale(0);
    }
    40% {
      transform: scale(1);
    }
  }
</style>
