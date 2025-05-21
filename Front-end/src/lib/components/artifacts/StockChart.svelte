<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  
  export let symbol = "SPY"; // Default to S&P 500 ETF
  export let timeRange = "1W"; // Fixed to 1-week duration
  
  const dispatch = createEventDispatcher();
  
  // Strict list of valid tech firm and popular stock tickers
  const validTickers = [
    'AAPL',  // Apple
    'MSFT',  // Microsoft
    'GOOGL', // Google (Class A)
    'GOOG',  // Google (Class C)
    'AMZN',  // Amazon
    'META',  // Meta Platforms (Facebook)
    'TSLA',  // Tesla
    'NVDA',  // NVIDIA
    'AMD',   // Advanced Micro Devices
    'INTC',  // Intel
    'IBM',   // IBM
    'CSCO',  // Cisco
    'ORCL',  // Oracle
    'ADBE',  // Adobe
    'CRM',   // Salesforce
    'NFLX',  // Netflix
    'PYPL',  // PayPal
    'QCOM',  // Qualcomm
    'TXN',   // Texas Instruments
    'SPY',   // S&P 500 ETF
    'QQQ',   // Nasdaq 100 ETF
    'DIA',   // Dow Jones ETF
    'VTI',   // Vanguard Total Stock Market ETF
    'VOO'    // Vanguard S&P 500 ETF
  ];
  
  interface ChartPoint {
    date: string | number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }
  
  let chartData: ChartPoint[] | null = null;
  let isLoading = true;
  let error: string | null = null;
  let isLightMode = false; // Track light/dark mode
  let websocket: WebSocket | null = null;
  let lastSearchTime = 0; // Track last search time for rate limiting
  let searchCooldown = 15000; // 15 seconds cooldown between searches
  
  // Create default data in case the API fails
  const createDefaultData = (): ChartPoint[] => {
    const result: ChartPoint[] = [];
    const now = new Date();
    
    // Create 7 days of data (1 week)
    for (let i = 6; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Skip weekends for more realistic data
      if (date.getDay() === 0 || date.getDay() === 6) {
        continue; // Skip Saturday and Sunday
      }
      
      // Base price around $100 with some variance
      const basePrice = 100 + (i * 2);
      const open = basePrice - (Math.random() * 2);
      const close = basePrice + (Math.random() * 2);
      const high = Math.max(open, close) + (Math.random() * 1);
      const low = Math.min(open, close) - (Math.random() * 1);
      
      result.push({
        date: date.getTime(),
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume: Math.floor(Math.random() * 1000000)
      });
    }
    
    return result;
  };
  
  // Function to request chart data from the backend
  const requestChartData = (ticker: string) => {
    // Always use 1W timeframe
    const timeframe = "1W";
    
    // Validate ticker symbol against our list
    ticker = ticker.toUpperCase().trim();
    if (!validTickers.includes(ticker)) {
      error = `Invalid ticker symbol: ${ticker}. Please use one of the popular tickers listed below.`;
      return;
    }
    
    // Check if we need to wait due to client-side rate limiting
    const now = Date.now();
    const timeSinceLastSearch = now - lastSearchTime;
    
    if (timeSinceLastSearch < searchCooldown) {
      const remainingCooldown = Math.ceil((searchCooldown - timeSinceLastSearch) / 1000);
      error = `Please wait ${remainingCooldown} seconds before searching again`;
      return;
    }
    
    // Update last search time
    lastSearchTime = now;
    
    // Clear previous error
    error = null;
    
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      // If socket not open, try to use mock data
      setMockData(ticker, timeframe);
      return;
    }
    
    isLoading = true;
    
    try {
      // Send chart request via websocket
      websocket.send(JSON.stringify({
        type: 'chart_request',
        ticker: ticker,
        timeframe: timeframe
      }));
    } catch (err) {
      console.error('Error requesting chart data:', err);
      error = 'Failed to request chart data. Please try again.';
      isLoading = false;
      
      // Fall back to mock data
      setMockData(ticker, timeframe);
    }
  };
  
  // Process websocket message
  const handleWebSocketMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      console.log("WebSocket message received:", data.type);
      
      if (data.type === 'chart_data') {
        const chartResult = data.data;
        console.log("Chart data received:", chartResult);
        
        // Check if this update was requested by the AI
        const wasAiRequested = data.ai_requested === true;
        if (wasAiRequested) {
          console.log("Chart update was requested by the AI");
        }
        
        if (chartResult.error) {
          // Check if it's a rate limiting error
          if (chartResult.error.includes("Rate limit exceeded") || 
              chartResult.error.includes("429")) {
            error = "API rate limit exceeded. Using simulated data for demonstration purposes.";
            // Continue with mock data if provided
            if (chartResult.data && chartResult.data.length > 0) {
              if (chartResult.ticker) {
                symbol = chartResult.ticker;
              }
              
              chartData = chartResult.data;
              console.log("Using provided mock data with", chartData?.length || 0, "points");
              renderChart();
              isLoading = false;
            } else {
              // Create default data if none provided
              setMockData(chartResult.ticker || symbol, "1W");
            }
          } else {
            // For other errors, just show the error message
            error = chartResult.error;
            isLoading = false;
            // Try to fall back to mock data for the ticker
            if (chartResult.ticker) {
              setMockData(chartResult.ticker, "1W");
            }
          }
        } else {
          // Clear any previous errors
          error = null;
          
          if (chartResult.ticker) {
            symbol = chartResult.ticker;
          }
          
          // If chart data is available, update the chart
          if (chartResult.data && Array.isArray(chartResult.data)) {
            chartData = chartResult.data.map((item: any) => ({
              date: item.date,
              open: item.open,
              high: item.high,
              low: item.low,
              close: item.close,
              volume: item.volume
            }));
            
            console.log("Processed chart data with", chartData?.length || 0, "points");
            
            // Ensure we have a properly sized canvas
            setTimeout(() => {
              const canvas = document.getElementById('stock-chart') as HTMLCanvasElement;
              if (canvas) {
                const container = canvas.parentElement;
                if (container) {
                  const containerWidth = container.clientWidth;
                  const containerHeight = Math.max(container.clientHeight - 40, 200);
                  
                  // Adjust for margins
                  canvas.width = containerWidth - 60; // Adjust for left and right margins
                  canvas.height = containerHeight - 30; // Adjust for top and bottom margins
                  
                  console.log(`Canvas resized to ${canvas.width}x${canvas.height}`);
                  
                  // Once data is loaded, render the chart
                  renderChart();
                }
              }
            }, 100);
          } else {
            error = "No chart data available";
            // Create default data for the requested ticker
            setMockData(chartResult.ticker || symbol, "1W");
          }
          
          isLoading = false;
        }
      }
      
      // Also handle direct ticker update requests from the AI
      if (data.type === 'update_chart' && data.ticker) {
        console.log("Received direct chart update request for ticker:", data.ticker);
        updateStockData(data.ticker);
      }
    } catch (err) {
      console.error('Error processing websocket message:', err);
    }
  };
  
  // Generate mock data as a fallback
  const setMockData = (ticker: string, timeframe: string) => {
    symbol = ticker;
    // Always use 1W timeframe
    timeRange = "1W";
    
    const now = new Date();
    const mockData: ChartPoint[] = [];
    let pointCount: number;
    let startDate: Date;
    let baseValue = 100 + Math.random() * 50;
    let volatility: number;
    
    switch(timeframe) {
      case "1D":
        pointCount = 24;
        startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        volatility = 0.5;
        break;
      case "1W":
        pointCount = 7;
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        volatility = 1;
        break;
      case "1M":
        pointCount = 30;
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        volatility = 2;
        break;
      case "3M":
        pointCount = 90;
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        volatility = 5;
        break;
      case "1Y":
        pointCount = 52;
        startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        volatility = 10;
        break;
      case "5Y":
        pointCount = 60;
        startDate = new Date(now.getTime() - 5 * 365 * 24 * 60 * 60 * 1000);
        volatility = 30;
        break;
      default:
        pointCount = 30;
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        volatility = 2;
    }
    
    let currentValue = baseValue;
    
    for (let i = 0; i < pointCount; i++) {
      const pointDate = new Date(startDate.getTime() + ((now.getTime() - startDate.getTime()) * (i / (pointCount - 1))));
      
      // Generate random price movements
      const change = (Math.random() * volatility * 2 - volatility);
      currentValue = Math.max(currentValue + change, baseValue * 0.7);
      
      const high = currentValue * (1 + Math.random() * 0.02);
      const low = currentValue * (1 - Math.random() * 0.02);
      const open = low + Math.random() * (high - low);
      const close = low + Math.random() * (high - low);
      
      mockData.push({
        date: pointDate.getTime(),
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume: Math.floor(Math.random() * 1000000)
      });
    }
    
    chartData = mockData;
    renderChart();
    isLoading = false;
  };
  
  const renderChart = () => {
    if (!chartData || !chartData.length) {
      console.error("Cannot render chart: No chart data available");
      return;
    }
    
    // Get chart dimensions
    const canvas = document.getElementById('stock-chart') as HTMLCanvasElement;
    if (!canvas) {
      console.error("Cannot render chart: Canvas element not found");
      return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      console.error("Cannot render chart: Canvas context not available");
      return;
    }
    
    console.log("Rendering chart with data:", chartData.length, "points");
    
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear previous chart
    ctx.clearRect(0, 0, width, height);
    
    // Find min and max values
    const highValues = chartData.map(point => point.high);
    const lowValues = chartData.map(point => point.low);
    const maxValue = Math.max(...highValues) * 1.005; // Add some padding
    const minValue = Math.min(...lowValues) * 0.995;
    const valueRange = maxValue - minValue;
    
    // Set chart styles
    const firstPoint = chartData[0];
    const lastPoint = chartData[chartData.length - 1];
    const isPositive = lastPoint.close >= firstPoint.open;
    
    // Update chart colors based on theme
    const chartColor = isPositive ? 
      (isLightMode ? '#27ae60' : '#1a5d38') : 
      (isLightMode ? '#e74c3c' : '#c0392b');
    
    // Draw grid
    ctx.beginPath();
    ctx.strokeStyle = isLightMode ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;
    
    // Draw horizontal grid lines
    for (let i = 0; i <= 5; i++) {
      const y = (i / 5) * height;
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
    }
    
    // Draw vertical grid lines (for date intervals)
    const numVerticalLines = Math.min(chartData.length, 6); // Limit to avoid crowding
    for (let i = 0; i <= numVerticalLines; i++) {
      const x = (i / numVerticalLines) * width;
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
    }
    ctx.stroke();
    
    // Draw price labels on y-axis
    ctx.fillStyle = isLightMode ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.6)';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'left';
    
    for (let i = 0; i <= 5; i++) {
      const value = minValue + (valueRange * (i / 5));
      const y = height - ((value - minValue) / valueRange * height);
      ctx.fillText('$' + value.toFixed(2), 5, y - 2);
    }
    
    // Draw date labels on x-axis
    ctx.textAlign = 'center';
    
    for (let i = 0; i <= numVerticalLines; i++) {
      const index = Math.floor((i / numVerticalLines) * (chartData.length - 1));
      const point = chartData[index];
      const x = (i / numVerticalLines) * width;
      
      // Format the date for display
      let dateLabel = '';
      if (typeof point.date === 'number') {
        const date = new Date(point.date);
        if (timeRange === '1D') {
          dateLabel = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } else if (timeRange === '1W' || timeRange === '1M') {
          dateLabel = date.toLocaleDateString([], {month: 'short', day: 'numeric'});
        } else {
          dateLabel = date.toLocaleDateString([], {month: 'short', year: '2-digit'});
        }
      } else {
        dateLabel = String(point.date).substring(0, 10);
      }
      
      ctx.fillText(dateLabel, x, height - 5);
    }
    
    // Function to scale Y values
    const scaleY = (value: number) => {
      return height - ((value - minValue) / valueRange * height);
    };
    
    // Draw price line (using close prices)
    ctx.beginPath();
    ctx.strokeStyle = chartColor;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // Plot each point
    chartData.forEach((point, index) => {
      const x = (index / (chartData!.length - 1)) * width;
      const y = scaleY(point.close);
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    // Stroke the line
    ctx.stroke();
    
    // Draw gradient area under the line
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, chartColor + '33'); // Add transparency
    gradient.addColorStop(1, chartColor + '00'); // Fully transparent
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    
    // Start at bottom left
    ctx.moveTo(0, height);
    
    // Trace the line again
    chartData.forEach((point, index) => {
      const x = (index / (chartData!.length - 1)) * width;
      const y = scaleY(point.close);
      ctx.lineTo(x, y);
    });
    
    // Complete the area by going to bottom right then back to start
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.fill();
  };
  
  // Updated to be more robust
  export function updateStockData(newSymbol: string) {
    // Normalize ticker symbol
    newSymbol = newSymbol.toUpperCase().trim();
    
    console.log(`StockChart.updateStockData called with: ${newSymbol}`);
    
    // Validate against our list of valid tickers
    if (!validTickers.includes(newSymbol)) {
      console.error(`Invalid ticker symbol: ${newSymbol}. Not in validated list.`);
      error = `Invalid ticker symbol: ${newSymbol}. Please use one of the popular tickers.`;
      return;
    }
    
    // If the symbol is the same but we already have an error, try again
    if (newSymbol === symbol && error) {
      console.log(`Retrying fetch for ${newSymbol} due to previous error`);
    }
    
    // Update the symbol state variable
    symbol = newSymbol;
    
    // Request new chart data with fixed 1W timeframe
    requestChartData(newSymbol);
  }
  
  // Ensure chart is rendered - called externally when tab is switched
  export function ensureChartRendered() {
    console.log("ensureChartRendered called");
    if (chartData && chartData.length > 0) {
      // Need to wait a moment for the DOM to update after tab switch
      setTimeout(() => {
        renderChart();
      }, 50);
    } else if (!isLoading) {
      // If we don't have data and aren't loading, request data
      requestChartData(symbol);
    }
  }
  
  // Function to check current theme
  function checkTheme() {
    isLightMode = document.documentElement.classList.contains('light-mode');
    if (chartData) {
      renderChart();
    }
  }
  
  // Initialize chart on mount
  onMount(() => {
    // Check initial theme
    checkTheme();
    
    // Initialize with default data first to ensure something is displayed
    chartData = createDefaultData();
    
    // Get or create websocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname === 'localhost' 
      ? 'localhost:8000' 
      : window.location.host;
      
    try {
      // Try to use the existing websocket if available
      websocket = (window as any).appWebsocket || null;
      
      // If no websocket exists or it's not open, create a new one
      if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        // Use mock data instead
        setMockData(symbol, "1W");
      } else {
        // Add our handler to the existing websocket
        const originalOnMessage = websocket.onmessage;
        
        // Safe type assertion since we've already checked websocket is not null
        if (websocket) {
          websocket.onmessage = (event) => {
            // Call original handler if it exists
            if (typeof originalOnMessage === 'function') {
              originalOnMessage.call(websocket as WebSocket, event);
            }
            
            // Handle our chart messages
            handleWebSocketMessage(event);
          };
        }
        
        // Request initial chart data
        requestChartData(symbol);
      }
    } catch (err) {
      console.error('Error setting up websocket for chart:', err);
      // Fall back to mock data
      setMockData(symbol, "1W");
    }
    
    // Set up theme change detection
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          checkTheme();
        }
      });
    });
    
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });
    
    // Make sure canvas is properly sized
    const resizeCanvas = () => {
      const canvas = document.getElementById('stock-chart') as HTMLCanvasElement;
      if (canvas) {
        const container = canvas.parentElement;
        if (container) {
          const containerWidth = container.clientWidth;
          const containerHeight = Math.max(container.clientHeight - 40, 200);
          
          // Adjust for margins
          canvas.width = containerWidth - 60; // Adjust for left and right margins
          canvas.height = containerHeight - 30; // Adjust for top and bottom margins
          
          console.log(`Canvas resized to ${canvas.width}x${canvas.height}`);
          
          if (chartData && chartData.length > 0) {
            renderChart();
          }
        }
      }
    };
    
    window.addEventListener('resize', resizeCanvas);
    setTimeout(resizeCanvas, 100); // Initial sizing after DOM update
    
    // Dispatch the ready event
    dispatch('chartReady');
    
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      observer.disconnect();
    };
  });
</script>

<div class="stock-chart-widget">
  <div class="chart-header">
    <div class="search-form">
      <form on:submit|preventDefault={() => requestChartData(symbol)}>
        <input 
          type="text" 
          bind:value={symbol} 
          placeholder="Enter ticker symbol (e.g., AAPL)" 
          class="ticker-input" 
        />
        <button type="submit" class="search-button">
          Search
        </button>
      </form>
      <div class="search-hint">
        Tech tickers: AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, AMD, INTC, IBM
        <div class="search-hint-secondary">
          Also: CSCO, ORCL, ADBE, CRM, NFLX, PYPL, QCOM, TXN, SPY, QQQ
        </div>
        <div class="cooldown-hint">Limited to 1 search per 15 seconds (free API tier)</div>
      </div>
    </div>
    
    <div class="symbol-info">
      <h3>{symbol}</h3>
      {#if chartData && chartData.length > 0}
        <div class="price-info">
          <span class="current-price">${chartData[chartData.length - 1].close.toFixed(2)}</span>
          
          {#if chartData.length > 1}
            {@const startPrice = chartData[0].open}
            {@const endPrice = chartData[chartData.length - 1].close}
            {@const change = endPrice - startPrice}
            {@const percentChange = (change / startPrice) * 100}
            
            <span class="price-change {change >= 0 ? 'positive' : 'negative'}">
              {change >= 0 ? '+' : ''}{change.toFixed(2)} ({change >= 0 ? '+' : ''}{percentChange.toFixed(2)}%)
            </span>
          {/if}
        </div>
      {/if}
    </div>
  </div>
  
  <div class="chart-container">
    {#if isLoading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading chart data...</p>
      </div>
    {:else if error}
      <div class="error-state {error.includes('API rate limit') || error.includes('simulated data') ? 'warning' : ''}">
        <p>{error}</p>
        {#if error.includes('API rate limit') || error.includes('simulated data')}
          <p class="small-note">Free API tier has limited requests. Chart shows simulated data.</p>
          {#if chartData && chartData.length > 0}
            <canvas id="stock-chart"></canvas>
          {/if}
        {/if}
      </div>
    {:else if chartData && chartData.length > 0}
      <canvas id="stock-chart"></canvas>
      <div class="chart-info">
        <p class="chart-time">1-Week Chart</p>
        <p class="data-points">{chartData.length} data points</p>
      </div>
    {:else}
      <div class="no-data">
        <p>No chart data available. Search for a stock symbol above.</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .stock-chart-widget {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--card-bg);
  }
  
  .chart-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .search-form {
    margin-bottom: 0.5rem;
  }
  
  .search-form form {
    display: flex;
    gap: 0.5rem;
  }
  
  .ticker-input {
    flex: 1;
    padding: 0.5rem;
    border-radius: 4px;
    border: 1px solid var(--border-color);
    background-color: var(--primary-dark);
    color: var(--text-light);
    font-size: 0.9rem;
  }
  
  .search-button {
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
    background-color: var(--primary-light);
    color: var(--text-dark);
    font-size: 0.9rem;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .search-button:hover {
    background-color: var(--accent-light);
  }
  
  .symbol-info {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
  }
  
  .symbol-info h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-light);
  }
  
  .current-price {
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--text-light);
  }
  
  .price-change {
    font-size: 0.8rem;
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
  }
  
  .price-change.positive {
    background-color: rgba(39, 174, 96, 0.2);
    color: var(--primary-light);
  }
  
  .price-change.negative {
    background-color: rgba(231, 76, 60, 0.2);
    color: var(--text-light);
  }
  
  .chart-container {
    flex-grow: 1;
    position: relative;
    min-height: 200px;
    padding: 0.75rem;
  }
  
  #stock-chart {
    display: block;
    width: 100%;
    height: 100%;
    margin-top: 10px; /* Add margin for price labels at top */
    margin-bottom: 20px; /* Add margin for date labels at bottom */
    margin-left: 50px; /* Add margin for price labels at left */
    margin-right: 10px; /* Add margin at right */
    max-width: calc(100% - 60px); /* Adjust for the margins */
    max-height: calc(100% - 30px); /* Adjust for the margins */
  }
  
  .loading-state, .error-state {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    background-color: var(--primary-dark);
    z-index: 1;
    color: var(--text-muted);
  }
  
  .loading-spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--primary-dark);
    border-top: 2px solid var(--primary-light);
    border-radius: 50%;
    margin-bottom: 1rem;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .search-hint {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
    text-align: center;
  }
  
  .search-hint-secondary {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.1rem;
    font-style: italic;
  }
  
  .cooldown-hint {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.1rem;
    font-style: italic;
  }
  
  .error-state.warning {
    background-color: rgba(255, 152, 0, 0.1);
    color: var(--text-light);
    border-left: 3px solid var(--warning-color);
  }
  
  .small-note {
    font-size: 0.75rem;
    margin-top: 0.5rem;
    opacity: 0.8;
  }
  
  .chart-info {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-align: center;
    margin-top: 0.5rem;
  }
  
  .chart-time {
    font-weight: 500;
    margin-bottom: 0.2rem;
  }
  
  .data-points {
    font-size: 0.7rem;
    opacity: 0.8;
  }
  
  .no-data {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-muted);
    font-style: italic;
    text-align: center;
    padding: 2rem;
  }
</style> 