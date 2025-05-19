<script lang="ts">
  import { onMount } from 'svelte';
  export let newsSource = "global"; // global, specific ticker, etc.
  
  interface NewsItem {
    title: string;
    source: string;
    date: string;
    snippet: string;
    url: string;
  }
  
  let newsItems: NewsItem[] = [];
  let isLoading = true;
  let error: string | null = null;
  
  // Sample news articles for testing
  const sampleNews: NewsItem[] = [
    {
      title: "Markets rally on positive economic data",
      source: "Financial Times",
      date: "12m ago",
      snippet: "Global markets rose sharply following better-than-expected employment and inflation data.",
      url: "#"
    },
    {
      title: "Tech stocks lead gains as investors shift focus",
      source: "Wall Street Journal",
      date: "1h ago",
      snippet: "Technology sector outperforms broader market as investors anticipate interest rate decision.",
      url: "#"
    },
    {
      title: "Central bank signals potential rate cut in coming months",
      source: "Bloomberg",
      date: "2h ago",
      snippet: "Officials hint at easing monetary policy as inflation pressures show signs of abating.",
      url: "#"
    },
    {
      title: "Oil prices drop amid supply chain concerns",
      source: "Reuters",
      date: "3h ago",
      snippet: "Crude oil futures fell as traders worry about potential disruptions to global distribution channels.",
      url: "#"
    }
  ];
  
  onMount(() => {
    // In a real implementation, this would make an API call
    // For now we'll use sample data
    setTimeout(() => {
      newsItems = sampleNews;
      isLoading = false;
    }, 1000);
  });
  
  export function updateNews(ticker: string | null = null) {
    isLoading = true;
    
    // In a real implementation, this would make an API call with the ticker
    // For now, we'll just update the sample data
    setTimeout(() => {
      if (ticker) {
        // If we have a ticker, filter for news specific to that ticker
        newsItems = sampleNews.filter(item => 
          Math.random() > 0.5 // Randomly display some news for demonstration
        );
        
        if (newsItems.length === 0) {
          newsItems = [{
            title: `No recent news found for ${ticker}`,
            source: "FinanceGPT",
            date: "just now",
            snippet: "Try another ticker or check back later for updates.",
            url: "#"
          }];
        }
      } else {
        // Otherwise show global news
        newsItems = sampleNews;
      }
      
      isLoading = false;
    }, 800);
  }
</script>

<div class="news-widget card">
  <div class="card-header">
    <h3>
      {#if newsSource === 'global'}
        Market News
      {:else}
        {newsSource} News
      {/if}
    </h3>
  </div>
  
  <div class="card-body">
    {#if isLoading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading news...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p>Error loading news: {error}</p>
      </div>
    {:else if newsItems.length === 0}
      <div class="empty-state">
        <p>No news articles available</p>
      </div>
    {:else}
      <ul class="news-list">
        {#each newsItems as item}
          <li class="news-item">
            <a href={item.url} target="_blank" rel="noopener noreferrer">
              <h4 class="news-title">{item.title}</h4>
              <div class="news-meta">
                <span class="news-source">{item.source}</span>
                <span class="news-date">{item.date}</span>
              </div>
              <p class="news-snippet">{item.snippet}</p>
            </a>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .news-widget {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .card-body {
    flex-grow: 1;
    overflow-y: auto;
  }
  
  .loading-state, .empty-state, .error-state {
    padding: 1.5rem;
    text-align: center;
    color: var(--gray-500);
  }
  
  .loading-spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--gray-200);
    border-top: 2px solid var(--primary-color);
    border-radius: 50%;
    margin: 0 auto 1rem auto;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .news-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .news-item {
    padding: 0;
    border-bottom: 1px solid var(--gray-200);
  }
  
  .news-item:last-child {
    border-bottom: none;
  }
  
  .news-item a {
    display: block;
    padding: 0.75rem;
    text-decoration: none;
    color: inherit;
    transition: background-color 0.15s ease;
  }
  
  .news-item a:hover {
    background-color: var(--hover-bg);
  }
  
  .news-title {
    margin: 0 0 0.25rem 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--gray-600);
    line-height: 1.3;
  }
  
  .news-meta {
    display: flex;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--gray-400);
    margin-bottom: 0.25rem;
  }
  
  .news-source {
    font-weight: 500;
    color: var(--primary-color);
  }
  
  .news-date {
    white-space: nowrap;
  }
  
  .news-snippet {
    margin: 0.25rem 0 0 0;
    font-size: 0.85rem;
    color: var(--gray-500);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.4;
  }
</style> 