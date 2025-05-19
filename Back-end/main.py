import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")

# Load environment variables
load_dotenv()

# Import routers
from routers import chat, websocket

# Create FastAPI app
app = FastAPI(
    title="FinanceGPT API",
    description="Financial analysis and insights powered by Gemini and Agno",
    version="1.0.0"
)

# Check for required API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set. Gemini features will not function correctly.")

if not POLYGON_API_KEY:
    logger.warning("POLYGON_API_KEY not set. Financial data tools will not work properly.")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set. Agno features will not function correctly.")

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")

@app.get("/")
async def root():
    status = "warning" if not GEMINI_API_KEY or not POLYGON_API_KEY or not OPENAI_API_KEY else "ok"
    
    message = "FinanceGPT API is running"
    if not GEMINI_API_KEY:
        message += " (WARNING: GEMINI_API_KEY not set)"
    if not POLYGON_API_KEY:
        message += " (WARNING: POLYGON_API_KEY not set)"
    if not OPENAI_API_KEY:
        message += " (WARNING: OPENAI_API_KEY not set)"
    
    return JSONResponse(
        content={"status": status, "message": message}
    )

@app.get("/healthcheck")
async def healthcheck():
    """Basic health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True) 