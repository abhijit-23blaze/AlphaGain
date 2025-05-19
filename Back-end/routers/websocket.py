from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any, Optional
import json
import logging
import uuid
import re

# Import the finance agent
from agents.agno_finance_agent import run_agent, convert_messages, get_stock_chart_data

router = APIRouter(tags=["WebSocket"])

# Logger for WebSocket operations
logger = logging.getLogger("websocket")

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
    try:
        # Check if the function is callable directly
        if callable(get_stock_chart_data):
            return get_stock_chart_data(ticker, timeframe)
        # Check if it's a function reference with an implementation attribute
        elif hasattr(get_stock_chart_data, 'implementation') and callable(get_stock_chart_data.implementation):
            return get_stock_chart_data.implementation(ticker, timeframe)
        else:
            # If the real function isn't available, use mock data instead
            logger.warning(f"Chart function is not callable: {type(get_stock_chart_data)}. Using mock data.")
            return generate_mock_chart_data(ticker, timeframe)
    except Exception as e:
        logger.error(f"Error in chart wrapper: {str(e)}. Falling back to mock data.")
        return generate_mock_chart_data(ticker, timeframe)

# Generate mock chart data
def generate_mock_chart_data(ticker, timeframe="1M"):
    """Generate mock chart data for testing purposes"""
    import random
    from datetime import datetime, timedelta
    
    # Determine time points based on timeframe
    now = datetime.now()
    if timeframe == "1D":
        points = 24  # Hourly for a day
        start_date = now - timedelta(days=1)
        interval = timedelta(hours=1)
    elif timeframe == "1W":
        points = 7  # Daily for a week
        start_date = now - timedelta(weeks=1)
        interval = timedelta(days=1)
    elif timeframe == "1M":
        points = 30  # Daily for a month
        start_date = now - timedelta(days=30)
        interval = timedelta(days=1)
    elif timeframe == "3M":
        points = 90  # Daily for 3 months
        start_date = now - timedelta(days=90)
        interval = timedelta(days=1)
    elif timeframe == "1Y":
        points = 52  # Weekly for a year
        start_date = now - timedelta(weeks=52)
        interval = timedelta(weeks=1)
    elif timeframe == "5Y":
        points = 60  # Monthly for 5 years
        start_date = now - timedelta(days=365*5)
        interval = timedelta(days=30)
    else:
        # Default to 1 month
        points = 30
        start_date = now - timedelta(days=30)
        interval = timedelta(days=1)
    
    # Generate random starting price based on ticker
    # Use the sum of ASCII values of ticker to create a consistent but random-looking base price
    base_price = sum(ord(c) for c in ticker) % 100 + 50  # Between 50 and 150
    
    # Generate price data with some randomness but following a trend
    trend = random.choice([-1, 1])  # Upward or downward trend
    volatility = random.uniform(0.5, 2.0)  # How much the price fluctuates
    
    chart_data = []
    current_price = base_price
    current_date = start_date
    
    for i in range(points):
        # Add some randomness to the price, but follow the trend
        change = (random.random() * volatility - volatility/2) + (trend * volatility * 0.2)
        current_price = max(current_price + change, 1.0)  # Ensure price doesn't go below 1
        
        # Calculate high, low, open, close
        high = current_price * (1 + random.random() * 0.02)
        low = current_price * (1 - random.random() * 0.02)
        if i > 0:
            open_price = chart_data[-1]["close"]  # Open at previous close
        else:
            open_price = current_price * (1 - random.random() * 0.01)  # First open
        close = current_price
        
        # Generate volume (higher on big price changes)
        volume = int(abs(change) * base_price * 1000 + random.random() * 100000)
        
        # Add data point
        chart_data.append({
            "date": int(current_date.timestamp() * 1000),  # Convert to milliseconds
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": volume
        })
        
        # Move to next time point
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
                            chart_timeframe = "1M"
                            
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
                                            chart_timeframe = args.get("timeframe", "1M")
                                        
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
                            
                            # Send a completion message to signal the end of streaming
                            await manager.broadcast({
                                "type": "ai_complete",
                                "user_id": "ai",
                                "timestamp": message_data.get("timestamp", "")
                            })
                            
                            # If a stock chart was requested by the AI, send the chart data
                            if stock_chart_requested and chart_ticker:
                                try:
                                    chart_data = get_chart_data(chart_ticker, chart_timeframe)
                                    
                                    # Send chart data to all clients
                                    await manager.broadcast({
                                        "type": "chart_data",
                                        "data": json.loads(chart_data),
                                        "ai_requested": True
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
                    timeframe = message_data.get("timeframe", "1M")
                    
                    if not ticker:
                        await manager.send_personal_message(
                            {"type": "error", "content": "No ticker symbol provided"},
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