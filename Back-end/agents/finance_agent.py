import os
import json
import logging
from datetime import date
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Import directly from Google Generative AI instead of LangChain
import google.generativeai as genai
from langchain.tools import StructuredTool

# Use simple classes for messages instead of importing from langchain
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finance_agent")

# Load environment variables
load_dotenv()

# Configure Google Generative AI
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

# Configure the Google Genai API
genai.configure(api_key=api_key)

# Maintains a session memory of conversations - keyed by client IP address
conversation_sessions = {}

# Define helpers for polygon.io API calls
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
if not POLYGON_API_KEY:
    logger.warning("POLYGON_API_KEY not set. Financial data tools will not work properly.")

async def get_financials(ticker: str) -> str:
    """Retrieves financial data for a given stock ticker."""
    if not POLYGON_API_KEY:
        return json.dumps({"error": "Polygon API key not configured"})
        
    try:
        url = f"https://api.polygon.io/v2/reference/financials/{ticker}?apiKey={POLYGON_API_KEY}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return json.dumps(response.json())
    except Exception as e:
        logger.error(f"Error fetching financials for {ticker}: {str(e)}")
        return json.dumps({"error": f"Failed to fetch financials: {str(e)}"})

async def get_news(ticker: str) -> str:
    """Retrieves news articles for a given stock ticker."""
    if not POLYGON_API_KEY:
        return json.dumps({"error": "Polygon API key not configured"})
        
    try:
        url = f"https://api.polygon.io/v2/reference/news?ticker={ticker}&apiKey={POLYGON_API_KEY}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return json.dumps(response.json())
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {str(e)}")
        return json.dumps({"error": f"Failed to fetch news: {str(e)}"})

async def get_stock_price_history(ticker: str, from_date: str, to_date: str) -> str:
    """Retrieves historical stock price data for a given period."""
    if not POLYGON_API_KEY:
        return json.dumps({"error": "Polygon API key not configured"})
        
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}?apiKey={POLYGON_API_KEY}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return json.dumps(response.json())
    except Exception as e:
        logger.error(f"Error fetching stock price history for {ticker}: {str(e)}")
        return json.dumps({"error": f"Failed to fetch stock price history: {str(e)}"})

# Define a system prompt for the finance agent
system_prompt = f"""
You are a highly capable financial assistant named FinanceGPT. Your purpose is to provide insightful and concise analysis to help users make informed financial decisions.

When a user asks a question, follow these steps:
1. Identify the relevant financial data needed to answer the query.
2. Use the available tools to retrieve the necessary data, such as stock financials, news, or aggregate data.
3. Analyze the retrieved data and any generated charts to extract key insights and trends.
4. Formulate a concise response that directly addresses the user's question, focusing on the most important findings from your analysis.

Remember:
- Today's date is {date.today().strftime('%Y-%m-%d')}.
- Pay attention to the conversation history and remember details the user has shared (like their name).
- If the user refers to something mentioned earlier in the conversation, use that context in your response.
- Maintain a consistent, helpful tone throughout the conversation.
- Avoid simply regurgitating the raw data from the tools. Instead, provide a thoughtful interpretation and summary.
- If the query cannot be satisfactorily answered using the available tools, kindly inform the user and suggest alternative resources or information they may need.

Your ultimate goal is to empower users with clear, actionable insights to navigate the financial landscape effectively.
"""

# Define tools
tools = [
    StructuredTool.from_function(
        func=get_financials,
        name="getFinancials",
        description="Retrieves financial data for a given stock ticker",
        args_schema={"ticker": str}
    ),
    StructuredTool.from_function(
        func=get_news,
        name="getNews",
        description="Retrieves news articles for a given stock ticker. Use this information to answer concisely",
        args_schema={"ticker": str}
    ),
    StructuredTool.from_function(
        func=get_stock_price_history,
        name="getStockPriceHistory",
        description="Retrieves historical stock price data for a given stock ticker over a specified time period",
        args_schema={"ticker": str, "from_date": str, "to_date": str}
    )
]

# Create a streaming implementation
async def run_agent(messages):
    """
    Run the agent with Google Generative AI with streaming and conversation memory.
    """
    # Create a unique session key based on the first message to identify the conversation
    # This is a simple approach - in production you might use user authentication
    session_key = str(hash(str(messages[0]))) if messages else "default"
    
    # Initialize or get conversation history for this session
    if session_key not in conversation_sessions:
        conversation_sessions[session_key] = []
    
    # Extract all previous messages for context
    all_messages = []
    for msg in messages:
        # Extract role and content, with proper fallbacks
        if hasattr(msg, 'role'):
            role = msg.role
        else:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
        
        content = msg.content if hasattr(msg, 'content') else str(msg)
        
        all_messages.append({"role": role, "content": content})
    
    # Update conversation history with all messages from this session
    # We'll replace the entire history to ensure it's in sync
    conversation_sessions[session_key] = all_messages
    
    # Extract the last message as the current query
    last_message = all_messages[-1]["content"] if all_messages else ""
    
    # Format the conversation for the model
    formatted_conversation = ""
    for msg in conversation_sessions[session_key][:-1]:  # All messages except the last one
        role_label = "User" if msg["role"] == "user" else "Assistant"
        formatted_conversation += f"{role_label}: {msg['content']}\n\n"
    
    # Create the prompt with the conversation history and current question
    full_prompt = f"{system_prompt}\n\n"
    
    if formatted_conversation:
        full_prompt += f"Previous conversation:\n{formatted_conversation}\n"
    
    full_prompt += f"User: {last_message}\nAssistant:"
    
    logger.info(f"Session {session_key}: Processing message with conversation history of {len(conversation_sessions[session_key])} messages")
    
    # Function to yield chunks token by token
    async def generate_response():
        try:
            # Use Gemini's capabilities
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Generate response with the full conversation context
            response = await asyncio.to_thread(
                model.generate_content,
                full_prompt
            )
            
            full_text = response.text
            
            # Add the assistant's response to the conversation history
            conversation_sessions[session_key].append({
                "role": "assistant",
                "content": full_text
            })
            
            # Limit the conversation history to prevent it from growing too large
            if len(conversation_sessions[session_key]) > 20:  # Keep last 10 exchanges (20 messages)
                conversation_sessions[session_key] = conversation_sessions[session_key][-20:]
            
            # Log the conversation size after update
            logger.info(f"Session {session_key}: Updated conversation history, now has {len(conversation_sessions[session_key])} messages")
            
            # Yield character by character for a token-by-token feel
            for char in full_text:
                yield {"output": char}
                # Small delay for natural typing effect
                await asyncio.sleep(0.01)
                
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
        
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
        elif role == "system":
            result.append(SystemMessage(content=content))
        elif role == "tool":
            result.append(ToolMessage(
                content=content,
                tool_call_id=msg.get("id", "")
            ))
    
    return result 