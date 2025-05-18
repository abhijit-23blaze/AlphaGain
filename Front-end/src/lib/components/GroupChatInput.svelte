<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let onSendMessage: (content: string, aiToggle: boolean) => void;
  export let isLoading: boolean = false;
  export let aiToggle: boolean = true;
  
  let message = '';
  
  const dispatch = createEventDispatcher();
  
  function handleSubmit() {
    if (message.trim()) {
      onSendMessage(message, aiToggle);
      message = '';
    }
  }
  
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }
  
  function toggleAI() {
    aiToggle = !aiToggle;
    console.log('AI toggle changed to:', aiToggle);
  }
  
  // For debugging
  $: console.log('Current aiToggle value:', aiToggle);
  
  function handleTyping() {
    dispatch('typing');
  }
</script>

<div class="chat-input">
  <form on:submit|preventDefault={handleSubmit}>
    <button 
      type="button" 
      class="ai-toggle-button" 
      class:active={aiToggle} 
      on:click={toggleAI}
      title="Toggle AI responses"
    >
      AI {aiToggle ? 'On' : 'Off'}
    </button>
    
    <textarea 
      bind:value={message} 
      on:keydown={handleKeyDown}
      on:input={handleTyping}
      placeholder={aiToggle ? "Ask FinanceGPT or chat with the group..." : "Chat with the group..."}
      rows="1"
      disabled={isLoading}
    ></textarea>
    
    <button type="submit" disabled={!message.trim() || isLoading} aria-label="Send message">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
      </svg>
    </button>
  </form>
</div>

<style>
  .chat-input {
    padding: 1rem;
    border-top: 1px solid #eee;
    background-color: white;
  }
  
  form {
    display: flex;
    gap: 0.5rem;
    align-items: flex-end;
  }
  
  textarea {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    resize: none;
    font-family: inherit;
    font-size: 1rem;
    min-height: 20px;
    max-height: 150px;
    overflow-y: auto;
  }
  
  textarea:focus {
    outline: none;
    border-color: #0066cc;
  }
  
  textarea:disabled {
    background-color: #f5f5f5;
    color: #999;
  }
  
  button[type="submit"] {
    background-color: #0066cc;
    color: white;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  button[type="submit"]:hover {
    background-color: #0055aa;
  }
  
  button[type="submit"]:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  
  button[type="submit"] svg {
    width: 18px;
    height: 18px;
  }
  
  .ai-toggle-button {
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid #ddd;
    background-color: #f5f5f5;
    color: #666;
    transition: all 0.2s;
  }
  
  .ai-toggle-button.active {
    background-color: #0066cc;
    color: white;
    border-color: #0055aa;
  }
  
  .ai-toggle-button:hover {
    opacity: 0.9;
  }
</style> 