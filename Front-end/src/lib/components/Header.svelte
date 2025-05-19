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
    <div class="tagline">
      Your AI financial assistant
    </div>
    {#if username}
      <div class="user-greeting">
        <span>👋 Hello, <strong>{username}</strong>!</span>
      </div>
    {/if}
  </div>
</header>

<style>
  header {
    display: flex;
    justify-content: center;
    padding: 1rem;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: var(--text-light);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid var(--gray-200);
  }
  
  .header-content {
    display: flex;
    align-items: center;
    width: 100%;
    max-width: 1600px;
    position: relative;
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .logo-icon {
    font-size: 1.5rem;
  }
  
  h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  }
  
  .tagline {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-left: 1rem;
  }
  
  .user-greeting {
    margin-left: auto;
    font-size: 0.95rem;
    background-color: rgba(0, 0, 0, 0.2);
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .user-greeting strong {
    font-weight: 600;
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