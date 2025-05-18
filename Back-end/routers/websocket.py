from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any
import json
import logging

# Import the finance agent
from agents.finance_agent import run_agent, convert_messages

router = APIRouter(tags=["WebSocket"])

# Logger for WebSocket operations
logger = logging.getLogger("websocket")

# Active WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def send_json(self, websocket: WebSocket, data: Dict):
        await websocket.send_json(data)

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Wait for a message from the client
            data = await websocket.receive_text()
            
            # Parse the client message
            try:
                request_data = json.loads(data)
                messages = request_data.get("messages", [])
                
                # Validate messages format
                if not isinstance(messages, list) or not messages:
                    raise ValueError("Invalid or empty messages array")
                
                # Convert to message objects
                message_objects = convert_messages([
                    {
                        "role": msg.get("role", ""),
                        "content": msg.get("content", ""),
                        "id": msg.get("id", ""),
                        "tool_calls": msg.get("tool_calls", None),
                    }
                    for msg in messages
                ])
                
                # Process with the finance agent
                try:
                    # Stream the response back to the client
                    async for chunk in await run_agent(message_objects):
                        if "output" in chunk:
                            await manager.send_json(websocket, {
                                "type": "content",
                                "content": chunk["output"]
                            })
                    
                    # Signal completion
                    await manager.send_json(websocket, {"type": "done"})
                    
                except Exception as e:
                    logger.error(f"Agent execution error: {str(e)}")
                    await manager.send_json(
                        websocket, 
                        {"type": "error", "error": f"Agent execution error: {str(e)}"}
                    )
                
            except json.JSONDecodeError:
                await manager.send_json(
                    websocket, 
                    {"type": "error", "error": "Invalid JSON format"}
                )
            except ValueError as ve:
                await manager.send_json(
                    websocket, 
                    {"type": "error", "error": str(ve)}
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket request: {str(e)}")
                await manager.send_json(
                    websocket, 
                    {"type": "error", "error": f"Error processing request: {str(e)}"}
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket) 