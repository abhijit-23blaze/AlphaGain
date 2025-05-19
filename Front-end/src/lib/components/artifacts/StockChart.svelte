<script>
  import { onMount } from 'svelte';
  
  export let symbol = "SPY"; // Default to S&P 500 ETF
  export let timeRange = "1d"; // Options: 1d, 1w, 1m, 3m, 1y, 5y
  
  let chartData = null;
  let isLoading = true;
  let error = null;
  
  // Sample data for mock chart
  const generateMockData = (range) => {
    const now = new Date();
    const data = [];
    let pointCount;
    let startDate;
    let baseValue = 450 + Math.random() * 50; // S&P 500 around this range
    let volatility;
    
    switch(range) {
      case "1d":
        pointCount = 24;
        startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        volatility = 0.5;
        break;
      case "1w":
        pointCount = 7;
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        volatility = 1;
        break;
      case "1m":
        pointCount = 30;
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        volatility = 2;
        break;
      case "3m":
        pointCount = 90;
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        volatility = 5;
        break;
      case "1y":
        pointCount = 52;
        startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        volatility = 10;
        break;
      case "5y":
        pointCount = 60;
        startDate = new Date(now.getTime() - 5 * 365 * 24 * 60 * 60 * 1000);
        volatility = 30;
        break;
      default:
        pointCount = 24;
        startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        volatility = 0.5;
    }
    
    let currentValue = baseValue;
    
    for (let i = 0; i < pointCount; i++) {
      const pointDate = new Date(startDate.getTime() + ((now.getTime() - startDate.getTime()) * (i / (pointCount - 1))));
      
      // Generate random price movements
      currentValue = currentValue + (Math.random() * volatility * 2 - volatility);
      
      // Ensure value doesn't go too low
      if (currentValue < baseValue * 0.7) {
        currentValue = baseValue * 0.7 + Math.random() * 5;
      }
      
      data.push({
        date: pointDate.toISOString(),
        value: parseFloat(currentValue.toFixed(2))
      });
    }
    
    return data;
  };
  
  const updateChart = () => {
    isLoading = true;
    error = null;
    
    // In a real app, this would make an API call
    // For this demo, we'll use generated data
    setTimeout(() => {
      try {
        chartData = generateMockData(timeRange);
        
        // This is where we would render a real chart library
        renderChart();
        
        isLoading = false;
      } catch (err) {
        error = err.message;
        isLoading = false;
      }
    }, 800);
  };
  
  const renderChart = () => {
    if (!chartData || !chartData.length) return;
    
    // Get chart dimensions
    const canvas = document.getElementById('stock-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear previous chart
    ctx.clearRect(0, 0, width, height);
    
    // Find min and max values
    const values = chartData.map(point => point.value);
    const minValue = Math.min(...values) * 0.995; // Add some padding
    const maxValue = Math.max(...values) * 1.005;
    const valueRange = maxValue - minValue;
    
    // Set chart styles
    const positiveColor = 'var(--primary-color)';
    const startValue = chartData[0].value;
    const endValue = chartData[chartData.length - 1].value;
    const chartColor = endValue >= startValue ? positiveColor : '#ef4444';
    
    ctx.strokeStyle = chartColor;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // Start drawing
    ctx.beginPath();
    
    // Plot each point
    chartData.forEach((point, index) => {
      const x = (index / (chartData.length - 1)) * width;
      const y = height - ((point.value - minValue) / valueRange) * height;
      
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
      const x = (index / (chartData.length - 1)) * width;
      const y = height - ((point.value - minValue) / valueRange) * height;
      ctx.lineTo(x, y);
    });
    
    // Complete the area by going to bottom right then back to start
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.fill();
  };
  
  // Time range selector
  const timeRanges = [
    { id: "1d", label: "1D" },
    { id: "1w", label: "1W" },
    { id: "1m", label: "1M" },
    { id: "3m", label: "3M" },
    { id: "1y", label: "1Y" },
    { id: "5y", label: "5Y" }
  ];
  
  const handleTimeRangeChange = (range) => {
    timeRange = range;
    updateChart();
  };
  
  export function updateStock(newSymbol) {
    if (newSymbol && newSymbol !== symbol) {
      symbol = newSymbol;
      updateChart();
    }
  }
  
  // Initialize chart on mount
  onMount(() => {
    // Make sure canvas is properly sized
    const resizeCanvas = () => {
      const canvas = document.getElementById('stock-chart');
      if (canvas) {
        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = Math.max(container.clientHeight, 200);
        
        if (chartData) {
          renderChart();
        }
      }
    };
    
    window.addEventListener('resize', resizeCanvas);
    setTimeout(resizeCanvas, 0); // Initial sizing after DOM update
    
    updateChart();
    
    return () => {
      window.removeEventListener('resize', resizeCanvas);
    };
  });
</script>

<div class="stock-chart-widget card">
  <div class="card-header">
    <div class="symbol-info">
      <h3>{symbol}</h3>
      {#if chartData && chartData.length > 0}
        <div class="price-info">
          <span class="current-price">${chartData[chartData.length - 1].value}</span>
          
          {#if chartData.length > 1}
            {@const startPrice = chartData[0].value}
            {@const endPrice = chartData[chartData.length - 1].value}
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
          class="time-range-button {timeRange === range.id ? 'active' : ''}"
          on:click={() => handleTimeRangeChange(range.id)}
        >
          {range.label}
        </button>
      {/each}
    </div>
  </div>
  
  <div class="chart-container card-body">
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
  }
  
  .card-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .symbol-info {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
  }
  
  .symbol-info h3 {
    margin: 0;
    font-size: 1.1rem;
  }
  
  .current-price {
    font-weight: 600;
    font-size: 1rem;
  }
  
  .price-change {
    font-size: 0.85rem;
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
  }
  
  .price-change.positive {
    background-color: var(--primary-light);
    color: var(--primary-color);
  }
  
  .price-change.negative {
    background-color: #fee2e2;
    color: #ef4444;
  }
  
  .time-range-selector {
    display: flex;
    gap: 0.25rem;
  }
  
  .time-range-button {
    background: none;
    border: none;
    font-size: 0.8rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    color: var(--gray-500);
  }
  
  .time-range-button:hover {
    background-color: var(--gray-100);
  }
  
  .time-range-button.active {
    background-color: var(--primary-light);
    color: var(--primary-color);
    font-weight: 500;
  }
  
  .chart-container {
    flex-grow: 1;
    position: relative;
    min-height: 200px;
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
    background-color: rgba(255, 255, 255, 0.8);
    z-index: 1;
    color: var(--gray-500);
  }
  
  .loading-spinner {
    width: 30px;
    height: 30px;
    border: 3px solid var(--primary-light);
    border-top: 3px solid var(--primary-color);
    border-radius: 50%;
    margin-bottom: 1rem;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
</style> 