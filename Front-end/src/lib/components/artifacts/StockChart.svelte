<script lang="ts">
  import { onMount } from 'svelte';
  
  export let symbol = "SPY"; // Default to S&P 500 ETF
  export let timeRange = "1d"; // Options: 1d, 1w, 1m, 3m, 1y, 5y
  
  interface ChartPoint {
    date: string;
    value: number;
  }
  
  let chartData: ChartPoint[] | null = null;
  let isLoading = true;
  let error: string | null = null;
  
  // Sample data for mock chart
  const generateMockData = (range: string): ChartPoint[] => {
    const now = new Date();
    const data: ChartPoint[] = [];
    let pointCount: number;
    let startDate: Date;
    let baseValue = 450 + Math.random() * 50; // S&P 500 around this range
    let volatility: number;
    
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
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        error = errorMessage;
        isLoading = false;
      }
    }, 800);
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
    const values = chartData.map(point => point.value);
    const minValue = Math.min(...values) * 0.995; // Add some padding
    const maxValue = Math.max(...values) * 1.005;
    const valueRange = maxValue - minValue;
    
    // Set chart styles
    const startValue = chartData[0]?.value ?? 0;
    const endValue = chartData[chartData.length - 1]?.value ?? 0;
    const isPositive = endValue >= startValue;
    
    const chartColor = isPositive ? '#948979' : '#bc6c25';
    
    ctx.strokeStyle = chartColor;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // Start drawing
    ctx.beginPath();
    
    // Plot each point
    chartData.forEach((point, index) => {
      const x = (index / (chartData!.length - 1)) * width;
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
      const x = (index / (chartData!.length - 1)) * width;
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
  
  const handleTimeRangeChange = (range: string) => {
    timeRange = range;
    updateChart();
  };
  
  export function updateStock(newSymbol: string) {
    if (newSymbol && newSymbol !== symbol) {
      symbol = newSymbol;
      updateChart();
    }
  }
  
  // Initialize chart on mount
  onMount(() => {
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
    
    updateChart();
    
    return () => {
      window.removeEventListener('resize', resizeCanvas);
    };
  });
</script>

<div class="stock-chart-widget">
  <div class="chart-header">
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
    background-color: rgba(148, 137, 121, 0.25);
    color: #DFD0B8;
  }
  
  .price-change.negative {
    background-color: rgba(188, 108, 37, 0.25);
    color: #DFD0B8;
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
    background-color: rgba(57, 62, 70, 0.85);
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