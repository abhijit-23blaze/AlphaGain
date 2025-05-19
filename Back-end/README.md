# FinanceGPT Backend

A FastAPI backend with WebSocket support for a financial analysis AI assistant powered by Google Gemini, Agno, and Polygon API.

## Setup

### Prerequisites

- Python 3.9+
- [Gemini API Key](https://ai.google.dev/tutorials/setup)
- [Polygon.io API Key](https://polygon.io/) (for financial data)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following content:

```
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
POLYGON_API_KEY=your_polygon_api_key_here

# Server Settings
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
ALLOWED_ORIGINS=*
```

4. Update your `.env` file with your actual API keys.

## Running the Application

Start the FastAPI server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Endpoints

### HTTP Endpoints

- `GET /` - API status check
- `POST /api/chat` - Send a chat request (streaming response)
- `POST /api/chat/json` - Send a chat request (JSON response)

### WebSocket Endpoint

- `ws://localhost:8000/ws/chat` - WebSocket connection for real-time chat

## Message Format

Example request body for `/api/chat`:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What can you tell me about AAPL stock?"
    }
  ]
}
```

## WebSocket Usage Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => {
  const message = {
    messages: [
      {
        role: 'user',
        content: 'What can you tell me about AAPL stock?'
      }
    ]
  };
  ws.send(JSON.stringify(message));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(response);
  
  // Handle different message types
  switch(response.type) {
    case 'content':
      console.log('Agent response:', response.content);
      break;
    case 'tool_call':
      console.log('Tool call:', response.name, response.arguments);
      break;
    case 'tool_response':
      console.log('Tool response:', response.content);
      break;
    case 'done':
      console.log('Conversation complete');
      break;
    case 'error':
      console.error('Error:', response.error);
      break;
  }
};
```

## API Documentation

When the server is running, you can access the Swagger documentation at:
http://localhost:8000/docs

## Troubleshooting

### Google Gemini API Issues

If you encounter errors with the Gemini model, check the available models by running:

```bash
python utils.py
```

This will list all available Gemini models for your API key. Update the model name in `agents/finance_agent.py` to use one of these models.

### LangChain Compatibility Issues

This project uses LangChain for agent orchestration. If you encounter compatibility issues, make sure your installed versions match the requirements:

```bash
python check_dependencies.py
```

## Development

The application structure:

```
back-end/
├── agents/
│   ├── __init__.py
│   ├── finance_agent.py     # LangChain agent with Gemini
│   └── agno_finance_agent.py # Agno agent with Polygon tools
├── routers/
│   ├── __init__.py
│   ├── chat.py              # HTTP endpoints
│   └── websocket.py         # WebSocket endpoint
├── main.py                  # FastAPI application
├── requirements.txt         # Dependencies
├── test_agno_agent.py       # Test script for Agno agent
├── utils.py                 # Utility script to list Gemini models
└── check_dependencies.py    # Verify dependencies are installed correctly
```

## Features

The backend includes two different agent implementations:

1. **Gemini Agent (Original)**: Uses Google's Gemini model with LangChain for financial analysis.

2. **Agno Agent (New)**: Uses the Agno framework with Gemini models and custom Polygon.io tools for:
   - Real-time stock price data
   - Latest company news
   
### Polygon API Tools

The Agno implementation includes custom tools for the Polygon.io API:

- **PolygonStockTool**: Retrieves real-time stock prices, company details, and day change metrics.
- **PolygonNewsTool**: Fetches the latest news articles for a specific stock ticker.

### Testing the Agno Agent

You can test the Agno agent and Polygon tools using the provided test script:

```bash
python test_agno_agent.py
```

This will verify that the Polygon API tools are working correctly and test the full agent with a sample query.

## Switching Agent Implementations

The application is configured to use the Agno agent by default. The WebSocket router imports from `agents.agno_finance_agent`. To switch back to the original Gemini implementation, modify the import in `routers/websocket.py` to use `agents.finance_agent` instead. 