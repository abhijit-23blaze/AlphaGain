<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  export let isLoading = false;
  
  const dispatch = createEventDispatcher();
  
  let username = '';
  let error = '';
  
  function handleSubmit() {
    if (!username.trim()) {
      error = 'Please enter a username';
      return;
    }
    
    if (username.trim().length < 3) {
      error = 'Username must be at least 3 characters';
      return;
    }
    
    error = '';
    dispatch('login', { username });
  }
</script>

<div class="login-container">
  <div class="login-card">
    <h2>Join AlphaGain Chat</h2>
    <p class="subtitle">Connect with others and get financial insights from our AI assistant</p>
    
    <form on:submit|preventDefault={handleSubmit}>
      <div class="form-group">
        <label for="username">Your Name</label>
        <input 
          type="text" 
          id="username" 
          bind:value={username}
          placeholder="Enter your name"
          autocomplete="off"
          disabled={isLoading}
        />
        {#if error}
          <p class="error">{error}</p>
        {/if}
      </div>
      
      <button type="submit" class="login-button" disabled={isLoading}>
        {#if isLoading}
          <div class="spinner"></div>
          Connecting...
        {:else}
          Join Chat
        {/if}
      </button>
    </form>
  </div>
</div>

<style>
  .login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background-color: var(--primary-darkest);
  }
  
  .login-card {
    background-color: var(--primary-dark);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    padding: 2rem;
    width: 100%;
    max-width: 400px;
    border: 1px solid var(--border-color);
  }
  
  h2 {
    font-size: 1.75rem;
    color: var(--primary-light);
    margin: 0 0 0.5rem 0;
    text-align: center;
    font-weight: 500;
  }
  
  .subtitle {
    text-align: center;
    margin-bottom: 2rem;
    color: var(--text-muted);
    font-size: 0.9rem;
  }
  
  .form-group {
    margin-bottom: 1.5rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-light);
  }
  
  input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 1rem;
    transition: border-color 0.2s;
    background-color: var(--primary-darkest);
    color: var(--text-light);
  }
  
  input:focus {
    border-color: var(--primary-light);
    outline: none;
    box-shadow: 0 0 0 1px var(--primary-medium);
  }
  
  input:disabled {
    background-color: #1a1a1a;
    cursor: not-allowed;
  }
  
  input::placeholder {
    color: var(--text-muted);
    opacity: 0.7;
  }
  
  .error {
    color: #e57373;
    font-size: 0.85rem;
    margin-top: 0.5rem;
    margin-bottom: 0;
  }
  
  .login-button {
    width: 100%;
    padding: 0.75rem;
    background-color: var(--primary-medium);
    color: var(--text-light);
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.5rem;
  }
  
  .login-button:hover {
    background-color: var(--primary-light);
  }
  
  .login-button:disabled {
    background-color: var(--primary-medium);
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(224, 224, 224, 0.3);
    border-radius: 50%;
    border-top-color: var(--text-light);
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style> 