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
    <div class="ai-toggle">
      <label class="toggle-label">
        <input
          type="checkbox"
          bind:checked={aiToggle}
          on:change={toggleAI}
        />
        <span class="toggle-slider"></span>
      </label>
      <span class="toggle-text" class:active={aiToggle}>AI {aiToggle ? 'On' : 'Off'}</span>
    </div>
    
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
  
  .ai-toggle {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    margin-right: 0.5rem;
  }
  
  .toggle-label {
    position: relative;
    display: inline-block;
    width: 36px;
    height: 20px;
  }
  
  .toggle-label input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .4s;
    border-radius: 34px;
  }
  
  .toggle-slider:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 2px;
    bottom: 2px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
  }
  
  input:checked + .toggle-slider {
    background-color: #0066cc;
  }
  
  input:checked + .toggle-slider:before {
    transform: translateX(16px);
  }
  
  .toggle-text {
    font-size: 0.8rem;
    font-weight: 600;
    color: #999;
  }
  
  .toggle-text.active {
    color: #0066cc;
  }
</style> 