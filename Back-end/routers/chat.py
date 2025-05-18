from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio

# Import the finance agent
from agents.finance_agent import run_agent, convert_messages

router = APIRouter(tags=["Chat"])

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]

class Message(BaseModel):
    role: str
    content: str
    id: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class ChatRequest(BaseModel):
    messages: List[Message]

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Process a chat request and return a streamed response from the finance agent
    """
    try:
        # Convert messages to message objects format
        message_objects = convert_messages([
            {
                "role": msg.role,
                "content": msg.content,
                "id": msg.id,
                "tool_calls": [
                    {"name": tc.name, "arguments": tc.arguments} 
                    for tc in (msg.tool_calls or [])
                ] if msg.tool_calls else None
            }
            for msg in request.messages
        ])
        
        # Process with the finance agent and stream the response
        async def generate():
            try:
                # Stream from agent
                async for chunk in await run_agent(message_objects):
                    if "output" in chunk:
                        # Format as server-sent event with each token
                        yield f"data: {json.dumps({'content': chunk['output']})}\n\n"
                        # Flush immediately to ensure tokens are sent as soon as they're available
                        await asyncio.sleep(0)
                
                # Signal completion
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/chat/json")
async def chat_json(request: ChatRequest):
    """
    Process a chat request and return a complete JSON response (non-streaming)
    """
    try:
        # Convert messages
        message_objects = convert_messages([
            {
                "role": msg.role,
                "content": msg.content,
                "id": msg.id,
                "tool_calls": [
                    {"name": tc.name, "arguments": tc.arguments} 
                    for tc in (msg.tool_calls or [])
                ] if msg.tool_calls else None
            }
            for msg in request.messages
        ])
        
        # Get complete response - run the agent and collect all chunks
        response_chunks = []
        full_text = ""
        
        async for chunk in await run_agent(message_objects):
            if "output" in chunk:
                full_text += chunk["output"]
        
        return {"content": full_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}") 