from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any, Optional
import json
import logging
import uuid

# Import the finance agent
from agents.finance_agent import run_agent, convert_messages

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
                    
                    logger.info(f"Received message from {username} with AI toggle: {ai_toggle}")
                    
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
                            }
                        ])
                        
                        # Create a message to show AI is typing
                        typing_message = {
                            "type": "typing",
                            "user_id": "ai",
                            "username": "FinanceGPT"
                        }
                        await manager.broadcast(typing_message)
                        
                        try:
                            # Accumulate the AI response
                            ai_response = ""
                            
                            # Stream the response back to all clients
                            async for chunk in await run_agent(message_objects):
                                if "output" in chunk:
                                    ai_response += chunk["output"]
                                    await manager.broadcast({
                                        "type": "ai_stream",
                                        "user_id": "ai",
                                        "username": "FinanceGPT",
                                        "content": chunk["output"]
                                    })
                            
                            # Send a completion message to signal the end of streaming
                            await manager.broadcast({
                                "type": "ai_complete",
                                "user_id": "ai",
                                "timestamp": message_data.get("timestamp", "")
                            })
                            
                        except Exception as e:
                            logger.error(f"Agent execution error: {str(e)}")
                            await manager.broadcast({
                                "type": "error",
                                "content": f"AI response error: {str(e)}"
                            })
                
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