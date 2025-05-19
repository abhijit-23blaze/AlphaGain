import os
import logging
import json
from datetime import date
from typing import List, Dict, Any, Optional

from polygon import RESTClient
from agno.agent import Agent
from agno.tools import tool
from agno.models.openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agno_finance_agent")

# Load API keys from environment
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not POLYGON_API_KEY:
    logger.warning("POLYGON_API_KEY not set. Financial data tools will not work properly.")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. Using default model which might not work properly.")

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

# Custom Polygon Tools for Stock Data and News
class PolygonStockTool(tool.Tool):
    name = "PolygonStockTool"
    description = "Fetches real-time stock price and summary data from Polygon.io"
    
    def __init__(self, api_key):
        self.client = RESTClient(api_key)
    
    def run(self, ticker: str):
        """Fetches the latest stock price information for a given ticker symbol.
        
        Args:
            ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
            
        Returns:
            A formatted string containing stock information
        """
        try:
            # Get the last trade for the ticker symbol
            last_trade = self.client.get_last_trade(ticker)
            price = last_trade.price
            timestamp = last_trade.timestamp
            
            # Get company details
            try:
                company = self.client.get_ticker_details(ticker)
                name = company.name
                market_cap = company.market_cap
            except:
                name = ticker.upper()
                market_cap = "Not available"
            
            # Get day's change
            try:
                previous_close = self.client.get_previous_close(ticker)
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

class PolygonNewsTool(tool.Tool):
    name = "PolygonNewsTool"
    description = "Fetches the latest news articles for a given stock ticker from Polygon.io"
    
    def __init__(self, api_key):
        self.client = RESTClient(api_key)
    
    def run(self, ticker: str, limit: int = 5):
        """Fetches the latest news articles for a given ticker symbol.
        
        Args:
            ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
            limit: Maximum number of news articles to return (default: 5)
            
        Returns:
            JSON string containing news articles
        """
        try:
            # Get news for the ticker
            news = self.client.get_ticker_news(ticker.upper(), limit=limit)
            
            articles = []
            for article in news:
                articles.append({
                    "title": article.title,
                    "author": article.author,
                    "published_utc": article.published_utc,
                    "article_url": article.article_url,
                    "tickers": article.tickers,
                    "description": article.description
                })
            
            return json.dumps({"articles": articles})
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {str(e)}")
            return json.dumps({"error": f"Failed to fetch news for {ticker}: {str(e)}"})

# Initialize Polygon tools
polygon_stock_tool = PolygonStockTool(POLYGON_API_KEY)
polygon_news_tool = PolygonNewsTool(POLYGON_API_KEY)

# Define system prompt for the finance agent
system_prompt = f"""
You are FinanceGPT, a highly capable financial assistant. Your purpose is to provide insightful and concise financial analysis to help users make informed decisions.

Today's date is {date.today().strftime('%Y-%m-%d')}.

When a user asks a finance-related question, follow these steps:
1. Identify the relevant financial data needed to answer the query
2. Use your tools to retrieve necessary data like stock prices or news
3. Analyze the data and extract key insights
4. Provide a concise, helpful response

Always maintain a helpful, professional tone and focus on giving accurate information.
"""

# Create the Agno agent
llm = OpenAI(api_key=OPENAI_API_KEY)

finance_agent = Agent(
    name="Finance Chatbot",
    role="Provide financial insights using real-time market data",
    model=llm,
    tools=[polygon_stock_tool, polygon_news_tool],
    instructions=[
        system_prompt,
        "Use the PolygonStockTool to fetch real-time stock data when asked about stock prices.",
        "Use the PolygonNewsTool to fetch recent news about companies when relevant.",
        "Format numeric data clearly with appropriate units and decimal places.",
        "Respond in a clear, concise manner focusing on the most relevant information."
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
            
            response = finance_agent.run(query)
            
            # Add the assistant's response to the conversation history
            conversation_sessions[user_id].append({
                "role": "assistant",
                "content": response,
                "username": "FinanceGPT"
            })
            
            # Limit the conversation history to prevent it from growing too large
            if len(conversation_sessions[user_id]) > 20:  # Keep last 10 exchanges
                conversation_sessions[user_id] = conversation_sessions[user_id][-20:]
            
            # Log the conversation size after update
            logger.info(f"User {user_id}: Updated conversation history, now has {len(conversation_sessions[user_id])} messages")
            
            # Yield character by character for a token-by-token feel
            for char in response:
                yield {"output": char}
                
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
            message.username = "FinanceGPT"
            result.append(message)
        elif role == "system":
            result.append(SystemMessage(content=content))
        elif role == "tool":
            result.append(ToolMessage(
                content=content,
                tool_call_id=msg.get("id", "")
            ))
    
    return result 