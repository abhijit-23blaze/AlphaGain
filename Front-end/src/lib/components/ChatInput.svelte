<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let onSendMessage: (content: string) => void;
  
  let message = '';
  
  function handleSubmit() {
    if (message.trim()) {
      onSendMessage(message);
      message = '';
    }
  }
  
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }
</script>

<div class="chat-input">
  <form on:submit|preventDefault={handleSubmit}>
    <textarea 
      bind:value={message} 
      on:keydown={handleKeyDown}
      placeholder="Ask something about finance..."
      rows="1"
    ></textarea>
    <button type="submit" disabled={!message.trim()} aria-label="Send message">
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
  
  button {
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
  
  button:hover {
    background-color: #0055aa;
  }
  
  button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  
  button svg {
    width: 18px;
    height: 18px;
  }
</style> 