<script lang="ts">
  import { onMount } from 'svelte';
  
  // Store the theme state
  let isLightMode = false;
  
  // Function to toggle theme
  function toggleTheme() {
    isLightMode = !isLightMode;
    
    if (isLightMode) {
      document.documentElement.classList.add('light-mode');
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.classList.remove('light-mode');
      localStorage.setItem('theme', 'dark');
    }
  }
  
  // On component mount, check for saved preference
  onMount(() => {
    // Check if user has a saved preference
    const savedTheme = localStorage.getItem('theme');
    
    // If saved preference is light or system preference is light, set light mode
    if (savedTheme === 'light' || 
        (!savedTheme && window.matchMedia('(prefers-color-scheme: light)').matches)) {
      isLightMode = true;
      document.documentElement.classList.add('light-mode');
    }
  });
</script>

<button 
  class="theme-toggle" 
  on:click={toggleTheme} 
  aria-label={isLightMode ? "Switch to dark mode" : "Switch to light mode"}
>
  {#if isLightMode}
    <!-- Moon icon for dark mode -->
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path>
    </svg>
  {:else}
    <!-- Sun icon for light mode -->
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="4"></circle>
      <path d="M12 2v2"></path>
      <path d="M12 20v2"></path>
      <path d="m4.93 4.93 1.41 1.41"></path>
      <path d="m17.66 17.66 1.41 1.41"></path>
      <path d="M2 12h2"></path>
      <path d="M20 12h2"></path>
      <path d="m6.34 17.66-1.41 1.41"></path>
      <path d="m19.07 4.93-1.41 1.41"></path>
    </svg>
  {/if}
</button> 