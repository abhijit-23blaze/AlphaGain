from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any, Optional
import json
import logging
import uuid
import re
import time
from datetime import date, timedelta
import os

# Import the finance agent
from agents.agno_finance_agent import run_agent, convert_messages, get_stock_chart_data

router = APIRouter(tags=["WebSocket"])

# Logger for WebSocket operations
logger = logging.getLogger("websocket")

# Simple cache for API responses to avoid rate limiting
api_cache = {}
# Rate limiting tracking
last_api_call_time = 0
API_CALL_DELAY = 5  # seconds between API calls to avoid rate limiting

# User connection class to store user information
class UserConnection:
    def __init__(self, websocket: WebSocket, user_id: str, username: str):
        self.websocket = websocket
        self.user_id = user_id
        self.username = username

# Active WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[UserConnection] = []

    async def connect(self, websocket: WebSocket, user_id: str, username: str) -> UserConnection:
        await websocket.accept()
        user_connection = UserConnection(websocket, user_id, username)
        self.active_connections.append(user_connection)
        logger.info(f"New user {username} connected. Active connections: {len(self.active_connections)}")
        return user_connection

    def disconnect(self, websocket: WebSocket):
        # Find the user connection
        user_connection = next((conn for conn in self.active_connections if conn.websocket == websocket), None)
        if user_connection:
            username = user_connection.username
            self.active_connections.remove(user_connection)
            logger.info(f"User {username} disconnected. Remaining connections: {len(self.active_connections)}")
            return username
        return None

    async def send_personal_message(self, message: Dict, user_connection: UserConnection):
        await user_connection.websocket.send_json(message)

    async def broadcast(self, message: Dict, exclude: Optional[UserConnection] = None):
        for connection in self.active_connections:
            if exclude is None or connection.websocket != exclude.websocket:
                await connection.websocket.send_json(message)

    def get_active_users(self):
        return [{"user_id": conn.user_id, "username": conn.username} for conn in self.active_connections]

    def get_connection_by_id(self, user_id: str) -> Optional[UserConnection]:
        return next((conn for conn in self.active_connections if conn.user_id == user_id), None)

manager = ConnectionManager()

# Function wrapper for chart data
def get_chart_data(ticker, timeframe="1M"):
    """Wrapper function to safely call get_stock_chart_data"""
    # Check if we have a cached response for this ticker and timeframe
    cache_key = f"{ticker.upper()}_{timeframe}"
    if cache_key in api_cache:
        logger.info(f"Using cached data for {ticker} with timeframe {timeframe}")
        return api_cache[cache_key]
    
    # Check if we need to wait due to rate limiting
    global last_api_call_time
    current_time = time.time()
    time_since_last_call = current_time - last_api_call_time
    
    if time_since_last_call < API_CALL_DELAY:
        logger.warning(f"Rate limiting active - waited only {time_since_last_call:.2f}s of {API_CALL_DELAY}s required")
        # Fall back to mock data if we can't wait
        mock_data = generate_mock_chart_data(ticker, timeframe)
        return mock_data
    
    try:
        import httpx
        
        # Get API key from environment
        POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
        if not POLYGON_API_KEY:
            logger.error("POLYGON_API_KEY not set. Please add your Polygon API key to the .env file.")
            return json.dumps({
                "error": "Polygon API key not configured. Please add your API key to the .env file.",
                "ticker": ticker,
                "timeframe": timeframe,
                "data": []
            })
        
        # Convert ticker to uppercase
        ticker = ticker.upper()
        
        # Calculate date range based on the timeframe
        end_date = date.today()
        
        # Log the request details
        logger.info(f"Making Polygon API request for ticker={ticker}, timeframe={timeframe}")
        
        if timeframe == "1D":
            # For 1-day, we need intraday data (5-minute intervals)
            multiplier = 5
            timespan = "minute"
            start_date = end_date - timedelta(days=1)
        elif timeframe == "1W":
            multiplier = 1
            timespan = "day"
            start_date = end_date - timedelta(weeks=1)
        elif timeframe == "1M":
            multiplier = 1
            timespan = "day"
            start_date = end_date - timedelta(days=30)
        elif timeframe == "3M":
            multiplier = 1
            timespan = "day"
            start_date = end_date - timedelta(days=90)
        elif timeframe == "1Y":
            multiplier = 1
            timespan = "day"
            start_date = end_date - timedelta(days=365)
        elif timeframe == "5Y":
            multiplier = 1
            timespan = "week"
            start_date = end_date - timedelta(days=365*5)
        else:
            # Default to 1 month
            multiplier = 1
            timespan = "day"
            start_date = end_date - timedelta(days=30)
            
        # Format dates for API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Construct API url
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start_date_str}/{end_date_str}?apiKey={POLYGON_API_KEY}"
        
        # Update the last API call time
        last_api_call_time = time.time()
        
        # Make the request
        with httpx.Client() as client:
            logger.info(f"Calling Polygon API: {url.replace(POLYGON_API_KEY, 'API_KEY_HIDDEN')}")
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Polygon API response status: {response.status_code}")
        
        # Process the data for charting
        if "results" in data and data["results"]:
            chart_data = []
            for item in data["results"]:
                chart_data.append({
                    "date": item["t"],  # Timestamp
                    "open": item["o"],  # Open price
                    "high": item["h"],  # High price
                    "low": item["l"],   # Low price
                    "close": item["c"], # Close price
                    "volume": item["v"] # Volume
                })
            
            logger.info(f"Successfully processed {len(chart_data)} data points for {ticker}")
            
            result = {
                "ticker": ticker,
                "timeframe": timeframe,
                "data": chart_data
            }
            
            json_result = json.dumps(result)
            # Cache the result
            api_cache[cache_key] = json_result
            return json_result
        else:
            if "error" in data:
                error_msg = data.get("error", "Unknown error")
                logger.warning(f"Polygon API error: {error_msg}")
                return json.dumps({
                    "error": f"Polygon API error: {error_msg}",
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "data": []
                })
            else:
                logger.warning(f"No data available for {ticker} in the specified timeframe")
                return json.dumps({
                    "error": f"No data available for {ticker} in the specified timeframe",
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "data": []
                })
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            logger.error(f"Authentication error with Polygon API. Check your API key: {str(e)}")
            return json.dumps({
                "error": "Authentication error with Polygon API. Please check your API key.",
                "ticker": ticker,
                "timeframe": timeframe,
                "data": []
            })
        elif e.response.status_code == 429:
            logger.error(f"Rate limit exceeded for Polygon API: {str(e)}")
            # Fall back to mock data for this ticker and timeframe
            mock_data = generate_mock_chart_data(ticker, timeframe)
            # Cache the mock data temporarily
            api_cache[cache_key] = mock_data
            return mock_data
        else:
            logger.error(f"HTTP error calling Polygon API: {str(e)}")
            return json.dumps({
                "error": f"Error calling Polygon API: {str(e)}",
                "ticker": ticker,
                "timeframe": timeframe,
                "data": []
            })
    except Exception as e:
        logger.error(f"Error calling Polygon API directly: {str(e)}")
        return json.dumps({
            "error": f"Error fetching chart data: {str(e)}",
            "ticker": ticker,
            "timeframe": timeframe,
            "data": []
        })

# Generate mock chart data
def generate_mock_chart_data(ticker, timeframe="1M"):
    """Generate realistic mock chart data for testing purposes"""
    import random
    from datetime import datetime, timedelta
    
    # Map common tickers to realistic starting prices
    ticker_prices = {
        "AAPL": 175.0,  # Apple
        "MSFT": 330.0,  # Microsoft
        "AMZN": 135.0,  # Amazon
        "GOOGL": 140.0, # Google
        "META": 315.0,  # Meta (Facebook)
        "TSLA": 180.0,  # Tesla
        "NVDA": 430.0,  # NVIDIA
        "JPM": 180.0,   # JPMorgan Chase
        "V": 270.0,     # Visa
        "WMT": 60.0,    # Walmart
        "PG": 160.0,    # Procter & Gamble
        "JNJ": 150.0,   # Johnson & Johnson
        "UNH": 450.0,   # UnitedHealth
        "HD": 330.0,    # Home Depot
        "BAC": 36.0,    # Bank of America
        "PFE": 27.0,    # Pfizer
        "SPY": 463.0,   # S&P 500 ETF
        "QQQ": 415.0,   # Nasdaq ETF
        "DIA": 380.0,   # Dow Jones ETF
    }
    
    # Determine time points based on timeframe
    now = datetime.now()
    if timeframe == "1D":
        points = 24  # Hourly for a day
        start_date = now - timedelta(days=1)
        interval = timedelta(hours=1)
        volatility_factor = 0.2
    elif timeframe == "1W":
        points = 7  # Daily for a week
        start_date = now - timedelta(weeks=1)
        interval = timedelta(days=1)
        volatility_factor = 0.5
    elif timeframe == "1M":
        points = 22  # Trading days in a month
        start_date = now - timedelta(days=30)
        interval = timedelta(days=1)
        volatility_factor = 1.0
    elif timeframe == "3M":
        points = 65  # Trading days in 3 months
        start_date = now - timedelta(days=90)
        interval = timedelta(days=1)
        volatility_factor = 2.0
    elif timeframe == "1Y":
        points = 52  # Weekly for a year
        start_date = now - timedelta(weeks=52)
        interval = timedelta(weeks=1)
        volatility_factor = 4.0
    elif timeframe == "5Y":
        points = 60  # Monthly for 5 years
        start_date = now - timedelta(days=365*5)
        interval = timedelta(days=30)
        volatility_factor = 8.0
    else:
        # Default to 1 month
        points = 22
        start_date = now - timedelta(days=30)
        interval = timedelta(days=1)
        volatility_factor = 1.0
    
    # Get a realistic base price for the ticker or use a random price
    ticker = ticker.upper()
    base_price = ticker_prices.get(ticker)
    
    if base_price is None:
        # For unknown tickers, use hash of ticker name for consistent price
        ticker_hash = sum(ord(c) for c in ticker)
        base_price = 50 + (ticker_hash % 300)
    
    # Generate a realistic market trend (slightly biased toward up)
    trend_direction = 1 if random.random() > 0.4 else -1
    trend_strength = random.uniform(0.1, 0.3) * volatility_factor * trend_direction
    
    # Volatility based on ticker and adjusts with price
    volatility = base_price * 0.01 * volatility_factor  # 1% of base price * volatility factor
    
    # For shorter timeframes, reduce volatility
    if timeframe == "1D":
        volatility *= 0.3
    
    chart_data = []
    current_price = base_price
    current_date = start_date
    
    # Generate some "market events" for realistic volatility spikes
    event_days = []
    if points > 10:
        num_events = random.randint(1, min(3, points // 10))
        event_days = [random.randint(1, points - 1) for _ in range(num_events)]
    
    for i in range(points):
        # Basic trend component
        trend_change = current_price * trend_strength * 0.01
        
        # Random volatility component
        random_change = random.normalvariate(0, volatility)
        
        # Special "event" volatility
        event_change = 0
        if i in event_days:
            event_change = random.choice([-1, 1]) * volatility * random.uniform(2, 5)
        
        # Calculate the day's price change
        day_change = trend_change + random_change + event_change
        
        # Ensure price doesn't go too low
        current_price = max(current_price + day_change, base_price * 0.5)
        
        # Generate realistic OHLC data
        # For opening price, use previous day's close or a slight change from current price
        if i > 0:
            open_price = chart_data[-1]["close"]
        else:
            open_price = current_price * (1 + random.normalvariate(0, 0.003))
        
        # High and low should be more extreme than open/close
        daily_volatility = volatility * 0.5
        high = max(open_price, current_price) + abs(random.normalvariate(0, daily_volatility))
        low = min(open_price, current_price) - abs(random.normalvariate(0, daily_volatility))
        
        # Ensure high is always higher than open and close
        high = max(high, open_price * 1.001, current_price * 1.001)
        
        # Ensure low is always lower than open and close
        low = min(low, open_price * 0.999, current_price * 0.999)
        
        # Generate volume (higher on event days and big price changes)
        base_volume = base_price * 10000  # Higher priced stocks have higher volume
        volume_multiplier = 1 + (abs(day_change) / base_price) * 10  # More volume on big moves
        
        if i in event_days:
            volume_multiplier *= 3  # Much higher volume on event days
        
        volume = int(base_volume * volume_multiplier * random.uniform(0.8, 1.2))
        
        # Add data point with proper rounding
        chart_data.append({
            "date": int(current_date.timestamp() * 1000),  # Convert to milliseconds
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(current_price, 2),
            "volume": volume
        })
        
        # Move to next time point, skipping weekends for daily data
        if interval.days == 1 and timeframe != "5Y":
            current_date += interval
            # Skip weekends
            while current_date.weekday() > 4:  # 5=Saturday, 6=Sunday
                current_date += timedelta(days=1)
        else:
            current_date += interval
    
    result = {
        "ticker": ticker,
        "timeframe": timeframe,
        "data": chart_data
    }
    
    return json.dumps(result)

@router.websocket("/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    user_connection = None
    try:
        # Accept the connection first
        await websocket.accept()
        
        # Wait for the initial connection message with the username
        data = await websocket.receive_text()
        connect_data = json.loads(data)
        username = connect_data.get("username", f"User-{user_id[:6]}")
        
        # Create user connection object (without accepting again)
        user_connection = UserConnection(websocket, user_id, username)
        manager.active_connections.append(user_connection)
        logger.info(f"New user {username} connected. Active connections: {len(manager.active_connections)}")
        
        # Notify all users that a new user has joined
        join_message = {
            "type": "system",
            "content": f"{username} has joined the chat",
            "users": manager.get_active_users()
        }
        await manager.broadcast(join_message)
        
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            
            # Parse the client message
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "")
                
                if message_type == "chat":
                    # Regular chat message
                    content = message_data.get("content", "")
                    ai_toggle = message_data.get("ai_toggle", False)
                    
                    logger.info(f"Received message from {username} with AI toggle: {ai_toggle}, raw data: {message_data}")
                    
                    if not content.strip():
                        continue
                    
                    # Broadcast the user's message to all clients
                    user_message = {
                        "type": "chat",
                        "user_id": user_id,
                        "username": username,
                        "content": content,
                        "timestamp": message_data.get("timestamp", "")
                    }
                    await manager.broadcast(user_message)
                    
                    # If AI toggle is on, generate AI response
                    if ai_toggle:
                        # Convert to message objects for the AI
                        message_objects = convert_messages([
                            {
                                "role": "user",
                                "content": content,
                                "user_id": user_id,
                                "username": username
                            }
                        ])
                        
                        # Create a message to show AI is typing
                        typing_message = {
                            "type": "typing",
                            "user_id": "ai",
                            "username": "AlphaGain"
                        }
                        await manager.broadcast(typing_message)
                        
                        try:
                            # Accumulate the AI response
                            ai_response = ""
                            stock_chart_requested = False
                            chart_ticker = None
                            chart_timeframe = "1W"
                            
                            # Improved regex patterns for ticker detection
                            ticker_patterns = [
                                r'for\s+([A-Z]{1,5})\b',  # "for AAPL"
                                r'about\s+([A-Z]{1,5})\b', # "about MSFT"
                                r'([A-Z]{1,5})\s+(?:stock|ticker|price|shares)\b', # "AAPL stock"
                                r'([A-Z]{1,5})\s+is\s+(?:trading|priced|currently)', # "AAPL is trading"
                                r'stock\s+(?:symbol|ticker)\s+([A-Z]{1,5})\b', # "stock symbol AAPL"
                                r'ticker\s+(?:symbol)?\s+([A-Z]{1,5})\b', # "ticker AAPL"
                                r'(?:price of|looking at)\s+([A-Z]{1,5})\b', # "price of AAPL"
                            ]
                            
                            # Major tech firms and popular stocks only
                            # Explicitly listing tech firms and popular stocks to avoid partial matches
                            valid_tickers = [
                                'AAPL',  # Apple
                                'MSFT',  # Microsoft
                                'GOOGL', # Google (Class A)
                                'GOOG',  # Google (Class C)
                                'AMZN',  # Amazon
                                'META',  # Meta Platforms (Facebook)
                                'TSLA',  # Tesla
                                'NVDA',  # NVIDIA
                                'AMD',   # Advanced Micro Devices
                                'INTC',  # Intel
                                'IBM',   # IBM
                                'CSCO',  # Cisco
                                'ORCL',  # Oracle
                                'ADBE',  # Adobe
                                'CRM',   # Salesforce
                                'NFLX',  # Netflix
                                'PYPL',  # PayPal
                                'QCOM',  # Qualcomm
                                'TXN',   # Texas Instruments
                                'SPY',   # S&P 500 ETF
                                'QQQ',   # Nasdaq 100 ETF
                                'DIA',   # Dow Jones ETF
                                'VTI',   # Vanguard Total Stock Market ETF
                                'VOO'    # Vanguard S&P 500 ETF
                            ]
                            
                            # Stream the response back to all clients
                            try:
                                async for chunk in await run_agent(message_objects):
                                    if "output" in chunk:
                                        output = chunk["output"]
                                        ai_response += output
                                        
                                        # Send the actual text chunk
                                        await manager.broadcast({
                                            "type": "ai_stream",
                                            "user_id": "ai",
                                            "username": "AlphaGain",
                                            "content": output
                                        })
                                    
                                    # Handle tool call notifications from the agent
                                    elif "tool_call" in chunk:
                                        tool_call = chunk["tool_call"]
                                        tool_name = tool_call.get("name", "")
                                        
                                        # Extract ticker if available
                                        args = tool_call.get("arguments", {})
                                        ticker = args.get("ticker", "unknown")
                                        
                                        # For chart tools, track the data we need
                                        if tool_name == "PolygonStockChartTool":
                                            stock_chart_requested = True
                                            chart_ticker = ticker
                                            chart_timeframe = args.get("timeframe", "1W")
                                        
                                        # Send a tool call notification to the frontend
                                        await manager.broadcast({
                                            "type": "tool_call",
                                            "user_id": "ai",
                                            "username": "AlphaGain",
                                            "tool_name": tool_name,
                                            "status": "started",
                                            "ticker": ticker
                                        })
                                    
                                    # Handle tool completion notifications from the agent
                                    elif "tool_result" in chunk:
                                        tool_result = chunk["tool_result"]
                                        tool_name = tool_result.get("name", "")
                                        
                                        # Send a tool completion notification
                                        await manager.broadcast({
                                            "type": "tool_call",
                                            "user_id": "ai",
                                            "username": "AlphaGain",
                                            "tool_name": tool_name,
                                            "status": "completed"
                                        })
                            except Exception as stream_err:
                                # Log the error
                                logger.error(f"Error streaming response: {str(stream_err)}")
                                
                                # Send error notification to clients
                                await manager.broadcast({
                                    "type": "error",
                                    "content": f"Error generating response: {str(stream_err)}"
                                })
                            
                            # After processing the complete response, check for stock tickers if none were found yet
                            if not stock_chart_requested and ai_response:
                                logger.info("Checking complete response for stock ticker mentions")
                                
                                found_ticker = None
                                
                                # Try each pattern until we find a match
                                for pattern in ticker_patterns:
                                    ticker_matches = re.findall(pattern, ai_response)
                                    for potential_ticker in ticker_matches:
                                        # Only accept tickers that are in our valid_tickers list
                                        if potential_ticker in valid_tickers:
                                            found_ticker = potential_ticker
                                            chart_ticker = found_ticker
                                            stock_chart_requested = True
                                            logger.info(f"Detected valid ticker: {chart_ticker}")
                                            break
                                    
                                    if found_ticker:
                                        break
                            
                            # Send a completion message to signal the end of streaming
                            await manager.broadcast({
                                "type": "ai_complete",
                                "user_id": "ai",
                                "timestamp": message_data.get("timestamp", "")
                            })
                            
                            # If a stock chart was requested by the AI, send the chart data
                            if stock_chart_requested and chart_ticker:
                                try:
                                    # Always use 1W timeframe regardless of what was requested
                                    chart_data = get_chart_data(chart_ticker, "1W")
                                    
                                    # Send chart data to all clients
                                    await manager.broadcast({
                                        "type": "chart_data",
                                        "data": json.loads(chart_data),
                                        "ai_requested": True
                                    })
                                    
                                    # Also send a direct update request in case the chart component missed the data
                                    await manager.broadcast({
                                        "type": "update_chart",
                                        "ticker": chart_ticker
                                    })
                                    
                                except Exception as chart_err:
                                    logger.error(f"Error fetching AI-requested chart data: {str(chart_err)}")
                            
                        except Exception as e:
                            logger.error(f"Agent execution error: {str(e)}")
                            await manager.broadcast({
                                "type": "error",
                                "content": f"AI response error: {str(e)}"
                            })
                
                elif message_type == "chart_request":
                    # Handle direct chart request from frontend
                    ticker = message_data.get("ticker", "").strip().upper()
                    # Always use 1W timeframe regardless of what's requested
                    timeframe = "1W"
                    
                    if not ticker:
                        await manager.send_personal_message(
                            {"type": "error", "content": "No ticker symbol provided"},
                            user_connection
                        )
                        continue
                    
                    # Validate ticker against the list of valid tickers
                    if ticker not in valid_tickers:
                        await manager.send_personal_message(
                            {"type": "error", "content": f"Invalid ticker symbol: {ticker}. Please use one of the valid tickers."},
                            user_connection
                        )
                        continue
                    
                    try:
                        # Use the polygon chart tool directly
                        chart_data = get_chart_data(ticker, timeframe)
                        
                        # Send chart data to the client
                        await manager.broadcast({
                            "type": "chart_data",
                            "data": json.loads(chart_data),
                            "requested_by": user_id
                        })
                        
                    except Exception as e:
                        logger.error(f"Error fetching chart data: {str(e)}")
                        await manager.send_personal_message(
                            {"type": "error", "content": f"Error fetching chart data: {str(e)}"},
                            user_connection
                        )
                
                elif message_type == "typing":
                    # User is typing notification
                    await manager.broadcast({
                        "type": "typing",
                        "user_id": user_id,
                        "username": username
                    }, exclude=user_connection)
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "content": "Invalid JSON format"},
                    user_connection
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket request: {str(e)}")
                await manager.send_personal_message(
                    {"type": "error", "content": f"Error processing request: {str(e)}"},
                    user_connection
                )
                
    except WebSocketDisconnect:
        # Handle disconnect
        if user_connection:
            username = manager.disconnect(websocket)
            # Notify other users that this user has left
            if username:
                await manager.broadcast({
                    "type": "system",
                    "content": f"{username} has left the chat",
                    "users": manager.get_active_users()
                })
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if user_connection:
            manager.disconnect(websocket) 