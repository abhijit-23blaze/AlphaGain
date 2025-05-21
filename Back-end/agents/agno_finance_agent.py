import os
import logging
import json
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import uuid
import re

from polygon import RESTClient
from agno.agent import Agent
from agno.tools import tool
from agno.models.google.gemini import Gemini

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agno_finance_agent")

# Load API keys from environment
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not POLYGON_API_KEY:
    logger.warning("POLYGON_API_KEY not set. Financial data tools will not work properly.")

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set. The Agno Gemini agent will not function correctly.")

# Message conversion helpers for compatibility
class Message:
    """Base message class"""
    def __init__(self, content):
        self.content = content

class SystemMessage(Message):
    """System message"""
    pass

class HumanMessage(Message):
    """Human message"""
    pass

class AIMessage(Message):
    """AI message"""
    pass

class ToolMessage(Message):
    """Tool message"""
    def __init__(self, content, tool_call_id=None):
        super().__init__(content)
        self.tool_call_id = tool_call_id

# Initialize Polygon API client
polygon_client = RESTClient(POLYGON_API_KEY)

# Define Polygon API tools using the @tool decorator
@tool(name="PolygonStockTool", 
      description="Fetches real-time stock price and summary data from Polygon.io")
def get_stock_data(ticker: str):
    """Fetches the latest stock price information for a given ticker symbol.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
        
    Returns:
        A formatted string containing stock information
    """
    try:
        # Get the last trade for the ticker symbol
        last_trade = polygon_client.get_last_trade(ticker)
        price = last_trade.price
        timestamp = last_trade.timestamp
        
        # Get company details
        try:
            company = polygon_client.get_ticker_details(ticker)
            name = company.name
            market_cap = company.market_cap
        except:
            name = ticker.upper()
            market_cap = "Not available"
        
        # Get day's change
        try:
            previous_close = polygon_client.get_previous_close(ticker)
            prev_close_price = previous_close.results[0].c
            day_change = price - prev_close_price
            day_change_percent = (day_change / prev_close_price) * 100
        except:
            day_change = "N/A"
            day_change_percent = "N/A"
        
        response = {
            "ticker": ticker.upper(),
            "name": name,
            "price": price,
            "change": day_change if isinstance(day_change, str) else round(day_change, 2),
            "change_percent": day_change_percent if isinstance(day_change_percent, str) else round(day_change_percent, 2),
            "market_cap": market_cap,
            "timestamp": timestamp
        }
        
        return json.dumps(response)
    except Exception as e:
        logger.error(f"Error fetching stock data for {ticker}: {str(e)}")
        return json.dumps({"error": f"Failed to fetch stock data for {ticker}: {str(e)}"})

@tool(name="PolygonStockChartTool", 
      description="Fetches historical stock price data for charting from Polygon.io")
def get_stock_chart_data(ticker: str, timeframe: str = "1M"):
    """Fetches historical stock price data for a chart display.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
        timeframe: Time period for the chart - options: '1D', '1W', '1M', '3M', '1Y', '5Y'
        
    Returns:
        JSON string with price data for the specified timeframe
    """
    try:
        # Convert ticker to uppercase
        ticker = ticker.upper()
        
        # Calculate date range based on the timeframe
        end_date = date.today()
        
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
        
        # Make the request
        import httpx
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
        
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
            
            result = {
                "ticker": ticker,
                "timeframe": timeframe,
                "data": chart_data
            }
            return json.dumps(result)
        else:
            return json.dumps({
                "error": f"No data available for {ticker} in the specified timeframe",
                "ticker": ticker,
                "timeframe": timeframe,
                "data": []
            })
            
    except Exception as e:
        logger.error(f"Error fetching chart data for {ticker}: {str(e)}")
        return json.dumps({
            "error": f"Failed to fetch chart data for {ticker}: {str(e)}",
            "ticker": ticker,
            "timeframe": timeframe
        })

@tool(name="PolygonNewsTool", 
      description="Fetches the latest news articles for a given stock ticker from Polygon.io")
def get_stock_news(ticker: str, limit: int = 5):
    """Fetches the latest news articles for a given ticker symbol.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
        limit: Maximum number of news articles to return (default: 5)
        
    Returns:
        JSON string containing news articles
    """
    try:
        # Get news for the ticker using the correct method
        news_url = f"https://api.polygon.io/v2/reference/news?ticker={ticker}&limit={limit}&apiKey={POLYGON_API_KEY}"
        import httpx
        
        with httpx.Client() as client:
            response = client.get(news_url)
            response.raise_for_status()
            news_data = response.json()
        
        articles = []
        for article in news_data.get("results", []):
            articles.append({
                "title": article.get("title", ""),
                "author": article.get("author", ""),
                "published_utc": article.get("published_utc", ""),
                "article_url": article.get("article_url", ""),
                "tickers": article.get("tickers", []),
                "description": article.get("description", "")
            })
        
        return json.dumps({"articles": articles})
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {str(e)}")
        return json.dumps({"error": f"Failed to fetch news for {ticker}: {str(e)}"})

# Define system prompt for the finance agent
system_prompt = f"""
You are AlphaGain, a highly capable financial assistant. Your purpose is to provide insightful and concise financial analysis to help users make informed decisions.

Today's date is {date.today().strftime('%Y-%m-%d')}.

When a user asks a finance-related question, follow these steps:
1. Identify the relevant financial data needed to answer the query
2. Use your tools to retrieve necessary data like stock prices or news
3. Analyze the data and extract key insights
4. Provide a concise, helpful response
5. Always mention the name of the main company that we are talking about in terms of its stock market name.

Always maintain a helpful, professional tone and focus on giving accurate information.
"""

# Create the Agno agent with Gemini model
gemini_model = Gemini(api_key=GEMINI_API_KEY)

# Don't try to modify the model configuration as it might not be available
if False and hasattr(gemini_model, 'generation_config') and gemini_model.generation_config is not None:
    logger.info("Setting generation config parameters")
    gemini_model.generation_config.update({
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40
    })
else:
    logger.info("Skipping generation config setup")

finance_agent = Agent(
    name="Finance Chatbot",
    role="Provide financial insights using real-time market data",
    model=gemini_model,
    tools=[get_stock_data, get_stock_chart_data, get_stock_news],
    instructions=[
        system_prompt,
        "Use the PolygonStockTool to fetch real-time stock data when asked about stock prices.",
        "Use the PolygonStockChartTool to generate charts for stock price history when discussing trends or price movements.",
        "Use the PolygonNewsTool to fetch recent news about companies when relevant.",
        "Format numeric data clearly with appropriate units and decimal places.",
        "Respond in a clear, concise manner focusing on the most relevant information.",
        "Always announce when you are about to use a tool so users can understand what you're doing."
    ],
    show_tool_calls=True,
    markdown=True,
)

# Conversation memory
conversation_sessions = {}

async def run_agent(messages):
    """
    Run the agent with conversation memory.
    """
    # Get the user_id from the first message
    user_id = getattr(messages[0], 'user_id', 'default') if messages else 'default'
    
    # Initialize or get conversation history for this user
    if user_id not in conversation_sessions:
        conversation_sessions[user_id] = []
    
    # Extract the current message
    current_message = messages[-1] if messages else None
    if not current_message:
        return
    
    # Create message object for current message
    current_msg_obj = {
        "role": getattr(current_message, 'role', 'user'),
        "content": getattr(current_message, 'content', ''),
        "username": getattr(current_message, 'username', 'User')
    }
    
    # Add current message to conversation history
    conversation_sessions[user_id].append(current_msg_obj)
    
    # Format the conversation for the agent
    formatted_conversation = ""
    for msg in conversation_sessions[user_id][:-1]:  # All messages except the last one
        role_label = msg["username"] if msg["role"] == "user" else "Assistant"
        formatted_conversation += f"{role_label}: {msg['content']}\n\n"
    
    logger.info(f"User {user_id}: Processing message with conversation history of {len(conversation_sessions[user_id])} messages")
    
    # Function to yield chunks token by token
    async def generate_response():
        try:
            # Run Agno agent with the query
            query = current_msg_obj['content']
            
            # Pass in conversation history if it exists
            context = ""
            if formatted_conversation:
                context = f"Previous conversation:\n{formatted_conversation}\n\n"
                query = f"{context}User's question: {query}"
            
            # Stream the response from the finance agent
            try:
                # We'll skip the streaming attempt for now since it's causing issues
                logger.info("Using standard response from Gemini")
                
                # Run the agent
                response = finance_agent.run(query)
                
                # Extract the content from the response object
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
                
                # Check the response for tool usage patterns
                tool_patterns = {
                    "checking stock data": "PolygonStockTool",
                    "retrieving stock information": "PolygonStockTool",
                    "looking up price": "PolygonStockTool",
                    "generating chart": "PolygonStockChartTool",
                    "creating chart": "PolygonStockChartTool",
                    "visualizing price": "PolygonStockChartTool",
                    "checking news": "PolygonNewsTool",
                    "searching for news": "PolygonNewsTool",
                    "fetching news": "PolygonNewsTool"
                }
                
                # Check for stock tickers in the response
                ticker = "unknown"
                ticker_match1 = re.search(r'for\s+([A-Z]{1,5})', response_text)
                ticker_match2 = re.search(r'about\s+([A-Z]{1,5})', response_text)
                
                if ticker_match1:
                    ticker = ticker_match1.group(1)
                elif ticker_match2:
                    ticker = ticker_match2.group(1)
                
                # Check for tool usage patterns
                for pattern, tool in tool_patterns.items():
                    if pattern in response_text.lower():
                        # First emit a tool start event
                        yield {
                            "tool_call": {
                                "name": tool,
                                "arguments": {"ticker": ticker}
                            }
                        }
                        # Let's simulate a delay before tool completion (2 chars)
                        yield {"output": response_text[:2]}
                        # Then emit a tool completion event
                        yield {
                            "tool_result": {
                                "name": tool
                            }
                        }
                        # Don't check for more tools
                        break
                
                # Stream character by character for a token-by-token feel
                # Skip first 2 chars if we already output them above
                start_pos = 2 if any(pattern in response_text.lower() for pattern in tool_patterns) else 0
                for char in response_text[start_pos:]:
                    yield {"output": char}
                
            except Exception as e:
                logger.error(f"Error generating response stream: {str(e)}")
                # Fall back to just returning an error message
                yield {"output": f"Sorry, I encountered an error: {str(e)}"}
                return
            
            # Add the assistant's response to the conversation history
            conversation_sessions[user_id].append({
                "role": "assistant",
                "content": response_text,
                "username": "AlphaGain"
            })
            
            # Limit the conversation history to prevent it from growing too large
            if len(conversation_sessions[user_id]) > 20:  # Keep last 10 exchanges
                conversation_sessions[user_id] = conversation_sessions[user_id][-20:]
            
            # Log the conversation size after update
            logger.info(f"User {user_id}: Updated conversation history, now has {len(conversation_sessions[user_id])} messages")
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            yield {"output": f"Error: {str(e)}"}
    
    return generate_response()

def convert_messages(messages_dict):
    """
    Convert API message format to message objects.
    """
    result = []
    for msg in messages_dict:
        role = msg.get("role", "")
        content = msg.get("content", "")
        user_id = msg.get("user_id", "")
        username = msg.get("username", "User")
        
        if role == "user":
            message = HumanMessage(content=content)
            message.user_id = user_id
            message.username = username
            result.append(message)
        elif role == "assistant":
            message = AIMessage(content=content)
            message.user_id = "ai"
            message.username = "AlphaGain"
            result.append(message)
        elif role == "system":
            result.append(SystemMessage(content=content))
        elif role == "tool":
            result.append(ToolMessage(
                content=content,
                tool_call_id=msg.get("id", "")
            ))
    
    return result 