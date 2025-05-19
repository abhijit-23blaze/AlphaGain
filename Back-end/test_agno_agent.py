import os
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the agent
from agents.agno_finance_agent import polygon_stock_tool, polygon_news_tool, finance_agent

async def test_polygon_tools():
    """Test the Polygon API tools directly"""
    print("Testing Polygon Stock Tool...")
    stock_result = polygon_stock_tool.run("AAPL")
    print(json.dumps(json.loads(stock_result), indent=2))
    
    print("\nTesting Polygon News Tool...")
    news_result = polygon_news_tool.run("AAPL", 3)
    print(json.dumps(json.loads(news_result), indent=2))

def test_agno_agent():
    """Test the full Agno agent"""
    print("\nTesting Agno Agent with Polygon tools...")
    query = "What is the current stock price of AAPL and any recent news?"
    response = finance_agent.run(query)
    print("\nAgent Response:")
    print(response)

if __name__ == "__main__":
    # Check if Polygon API key is set
    if not os.getenv("POLYGON_API_KEY"):
        print("ERROR: POLYGON_API_KEY environment variable not set!")
        print("Please set this variable before running the test.")
        exit(1)
        
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY environment variable not set!")
        print("The Agno agent test will likely fail.")
    
    # Run the polygon tools test
    asyncio.run(test_polygon_tools())
    
    # Run the agent test
    test_agno_agent() 