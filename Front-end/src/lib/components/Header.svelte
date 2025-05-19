<script lang="ts">
  // Header component for AlphaGain
  import ThemeToggle from './ThemeToggle.svelte';
  export let username: string | null = null;
</script>

<header>
  <div class="header-content">
    <div class="logo">
      <span class="logo-icon">🐺</span>
      <h1>AlphaGain</h1>
    </div>
    
    <div class="header-right">
      <ThemeToggle />
      
      {#if username}
        <div class="user-greeting">
          <span>Hello, <strong>{username}</strong></span>
        </div>
      {/if}
    </div>
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
    justify-content: space-between;
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
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .user-greeting {
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
    
    .header-right {
      width: 100%;
      justify-content: space-between;
    }
    
    .user-greeting {
      margin-left: 0;
    }
  }
</style> 