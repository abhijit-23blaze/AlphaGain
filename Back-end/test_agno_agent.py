import os
import json
from polygon import RESTClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the agent
from agents.agno_finance_agent import finance_agent

def test_polygon_api():
    """Test the Polygon API directly"""
    # Get the Polygon API key
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        print("ERROR: POLYGON_API_KEY environment variable not set!")
        return
        
    # Create a Polygon client
    client = RESTClient(api_key)
    
    # Test stock data
    print("Testing Polygon Stock API...")
    ticker = "AAPL"
    try:
        # Get the last trade
        last_trade = client.get_last_trade(ticker)
        
        # Get company details
        company = client.get_ticker_details(ticker)
        
        print(f"Stock: {company.name} ({ticker})")
        print(f"Price: ${last_trade.price}")
        print(f"Timestamp: {last_trade.timestamp}")
        
        # Get news
        print("\nTesting Polygon News API...")
        news = client.get_ticker_news(ticker, limit=3)
        
        for i, article in enumerate(news, 1):
            print(f"\nArticle {i}:")
            print(f"Title: {article.title}")
            print(f"Published: {article.published_utc}")
            print(f"URL: {article.article_url}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

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
        
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set!")
        print("The Agno agent test will likely fail.")
        exit(1)
    
    # Run the polygon API test
    test_polygon_api()
    
    # Run the agent test
    test_agno_agent() 