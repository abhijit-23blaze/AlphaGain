<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  
  export let symbol = "SPY"; // Default to S&P 500 ETF
  export let timeRange = "1M"; // Options: 1D, 1W, 1M, 3M, 1Y, 5Y
  
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
  
  // Time range selector entries with proper format
  const timeRanges = [
    { id: "1D", label: "1D" },
    { id: "1W", label: "1W" },
    { id: "1M", label: "1M" },
    { id: "3M", label: "3M" },
    { id: "1Y", label: "1Y" },
    { id: "5Y", label: "5Y" }
  ];
  
  // Function to request chart data from the backend
  const requestChartData = (ticker: string, timeframe: string) => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      // If socket not open, try to use mock data
      setMockData(ticker, timeframe);
      return;
    }
    
    isLoading = true;
    error = null;
    
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
      
      if (data.type === 'chart_data') {
        const chartResult = data.data;
        
        if (chartResult.error) {
          error = chartResult.error;
          isLoading = false;
          return;
        }
        
        if (chartResult.ticker) {
          symbol = chartResult.ticker;
        }
        
        if (chartResult.timeframe) {
          timeRange = chartResult.timeframe;
        }
        
        chartData = chartResult.data || [];
        renderChart();
        isLoading = false;
      }
    } catch (err) {
      console.error('Error processing websocket message:', err);
    }
  };
  
  // Generate mock data as a fallback
  const setMockData = (ticker: string, timeframe: string) => {
    symbol = ticker;
    timeRange = timeframe;
    
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
    if (!chartData || !chartData.length) return;
    
    // Get chart dimensions
    const canvas = document.getElementById('stock-chart') as HTMLCanvasElement;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
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
    ctx.stroke();
    
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
  
  const handleTimeRangeChange = (range: string) => {
    timeRange = range;
    requestChartData(symbol, timeRange);
  };
  
  export function updateStockData(newSymbol: string, newTimeRange: string = timeRange) {
    // Normalize ticker symbol
    newSymbol = newSymbol.toUpperCase().trim();
    
    // Ensure timeRange is one of the allowed values
    const validTimeframe = timeRanges.find(t => t.id === newTimeRange);
    const timeframe = validTimeframe ? validTimeframe.id : "1M";
    
    // Request new chart data
    if (newSymbol) {
      requestChartData(newSymbol, timeframe);
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
        setMockData(symbol, timeRange);
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
        requestChartData(symbol, timeRange);
      }
    } catch (err) {
      console.error('Error setting up websocket for chart:', err);
      // Fall back to mock data
      setMockData(symbol, timeRange);
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
          canvas.width = container.clientWidth;
          canvas.height = Math.max(container.clientHeight - 40, 200);
          
          if (chartData) {
            renderChart();
          }
        }
      }
    };
    
    window.addEventListener('resize', resizeCanvas);
    setTimeout(resizeCanvas, 0); // Initial sizing after DOM update
    
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      observer.disconnect();
    };
  });
</script>

<div class="stock-chart-widget">
  <div class="chart-header">
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
    
    <div class="time-range-selector">
      {#each timeRanges as range}
        <button 
          class="tab-button {timeRange === range.id ? 'active' : ''}"
          on:click={() => handleTimeRangeChange(range.id)}
        >
          {range.label}
        </button>
      {/each}
    </div>
  </div>
  
  <div class="chart-container">
    {#if isLoading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading chart data...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p>Error loading chart: {error}</p>
      </div>
    {:else}
      <canvas id="stock-chart"></canvas>
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
  
  .time-range-selector {
    display: flex;
    gap: 0.25rem;
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
</style> 