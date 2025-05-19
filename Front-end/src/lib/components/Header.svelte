<script>
  // Header component for FinanceGPT
  export let username = '';
</script>

<header>
  <div class="header-content">
    <div class="logo">
      <span class="logo-icon">💹</span>
      <h1>FinanceGPT</h1>
    </div>
    {#if username}
      <div class="user-greeting">
        <span>Hello, <strong>{username}</strong></span>
      </div>
    {/if}
  </div>
</header>

<style>
  header {
    display: flex;
    justify-content: center;
    padding: 1rem 1.5rem;
    background-color: var(--primary-darkest);
    color: var(--text-light);
    border-bottom: 1px solid var(--border-color);
  }
  
  .header-content {
    display: flex;
    align-items: center;
    width: 100%;
    position: relative;
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .logo-icon {
    font-size: 1.25rem;
  }
  
  h1 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 500;
    letter-spacing: 0.01em;
  }
  
  .user-greeting {
    margin-left: auto;
    font-size: 0.875rem;
    background-color: var(--primary-medium);
    padding: 0.4rem 0.8rem;
    border-radius: 4px;
  }
  
  .user-greeting strong {
    font-weight: 500;
    color: var(--text-light);
  }
  
  @media (max-width: 640px) {
    .header-content {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
    
    .user-greeting {
      margin-left: 0;
      margin-top: 0.5rem;
    }
  }
</style> 