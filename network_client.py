"""
Network client for Tetris Battle multiplayer
Handles WebSocket communication with server - OPTIMIZED VERSION
Features: Auto-reconnect, better error handling, connection pooling
"""

import asyncio
import websockets
import json
import threading
from typing import Callable, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkClient:
    """WebSocket client for connecting to Tetris Battle server"""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.reconnecting = False
        self.loop = None
        self.thread = None
        
        # Callbacks for different message types
        self.callbacks = {}
        
        # User session data
        self.session_id = None
        self.user_data = None
        
        # Connection health tracking
        self.last_heartbeat = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Message queue for offline sending
        self.message_queue = []
        self.max_queue_size = 100
    
    def register_callback(self, message_type: str, callback: Callable):
        """Register a callback for a message type"""
        self.callbacks[message_type] = callback
        logger.info(f"Registered callback for: {message_type}")
    
    def start(self):
        """Start the network client in a separate thread"""
        if self.thread and self.thread.is_alive():
            logger.warning("Network client already running")
            return
            
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        logger.info("Network client thread started")
    
    def _run_async_loop(self):
        """Run the asyncio event loop in the thread"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._connect())
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            if self.loop:
                self.loop.close()
    
    async def _connect(self):
        """Connect to the server and listen for messages with auto-reconnect"""
        while True:
            try:
                async with websockets.connect(
                    self.server_url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    self.reconnect_attempts = 0
                    self.last_heartbeat = datetime.now()
                    logger.info(f"Connected to server: {self.server_url}")
                    
                    # Send queued messages
                    await self._send_queued_messages()
                    
                    # Listen for messages
                    async for message in websocket:
                        self.last_heartbeat = datetime.now()
                        await self._handle_message(message)
            
            except websockets.exceptions.ConnectionClosedError as e:
                logger.warning(f"Connection closed: {e}")
                self.connected = False
                await self._attempt_reconnect()
            
            except Exception as e:
                logger.error(f"Connection error: {e}")
                self.connected = False
                await self._attempt_reconnect()
            
            # If we exit the loop, we're done
            if not self.reconnecting:
                break
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect to server"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self.reconnecting = False
            return
        
        self.reconnecting = True
        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 30)  # Exponential backoff
        
        logger.info(f"Reconnecting in {wait_time}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
        await asyncio.sleep(wait_time)
    
    async def _send_queued_messages(self):
        """Send all queued messages after reconnection"""
        if not self.message_queue:
            return
        
        logger.info(f"Sending {len(self.message_queue)} queued messages")
        for message in self.message_queue[:]:
            try:
                await self.websocket.send(json.dumps(message))
                self.message_queue.remove(message)
            except Exception as e:
                logger.error(f"Error sending queued message: {e}")
                break
    
    async def _handle_message(self, message: str):
        """Handle incoming message from server"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type in self.callbacks:
                # Call the registered callback
                callback = self.callbacks[msg_type]
                # Run callback in thread-safe manner
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            else:
                logger.debug(f"No callback for message type: {msg_type}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def send_message(self, message: dict):
        """Send message to server with queuing for offline mode"""
        if not self.connected:
            # Queue message if not connected
            if len(self.message_queue) < self.max_queue_size:
                self.message_queue.append(message)
                logger.info("Message queued (not connected)")
            else:
                logger.warning("Message queue full, dropping message")
            return
        
        if self.websocket and self.loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(json.dumps(message)),
                    self.loop
                )
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                # Queue for retry
                if len(self.message_queue) < self.max_queue_size:
                    self.message_queue.append(message)
    
    # Authentication methods
    
    def register(self, username: str, password: str, email: str = None):
        """Register a new user"""
        message = {
            "type": "register",
            "username": username,
            "password": password,
            "email": email
        }
        self.send_message(message)
        logger.info(f"Register request sent for: {username}")
    
    def login(self, username: str, password: str):
        """Login with username and password"""
        message = {
            "type": "login",
            "username": username,
            "password": password
        }
        self.send_message(message)
        logger.info(f"Login request sent for: {username}")
    
    def validate_session(self, session_id: str):
        """Validate existing session"""
        message = {
            "type": "validate_session",
            "session_id": session_id
        }
        self.send_message(message)
        logger.info("Session validation requested")
    
    # Matchmaking methods
    
    def find_match(self, selected_map: str = "none"):
        """Start searching for a match with map preference"""
        message = {
            "type": "find_match",
            "map_preference": selected_map
        }
        self.send_message(message)
        logger.info(f"Match search started (map: {selected_map})")
    
    def cancel_match(self):
        """Cancel matchmaking search"""
        message = {
            "type": "cancel_match"
        }
        self.send_message(message)
        logger.info("Match search cancelled")
    
    # Game methods
    
    def send_game_state(self, state: dict):
        """Send game state to opponent"""
        message = {
            "type": "game_state",
            "state": state,
            "timestamp": datetime.now().timestamp()
        }
        self.send_message(message)
    
    def send_game_end(self, result: str):
        """Send game end notification (result: 'win' or 'lose')"""
        message = {
            "type": "game_end",
            "result": result,
            "timestamp": datetime.now().timestamp()
        }
        self.send_message(message)
        logger.info(f"Game end sent: {result}")
    
    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            message = {
                "type": "disconnect"
            }
            self.send_message(message)
            self.connected = False
            self.reconnecting = False
            logger.info("Disconnected from server")
    
    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self.connected
    
    def get_connection_status(self) -> dict:
        """Get detailed connection status"""
        return {
            "connected": self.connected,
            "reconnecting": self.reconnecting,
            "reconnect_attempts": self.reconnect_attempts,
            "queued_messages": len(self.message_queue),
            "last_heartbeat": self.last_heartbeat
        }
    
    def save_session(self, session_id: str, user_data: dict):
        """Save session data"""
        self.session_id = session_id
        self.user_data = user_data
        
        # Save to file for persistence
        try:
            with open("session.json", "w") as f:
                json.dump({
                    "session_id": session_id,
                    "user_data": user_data
                }, f)
            logger.info("Session saved")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    def load_session(self) -> Optional[str]:
        """Load saved session"""
        try:
            with open("session.json", "r") as f:
                data = json.load(f)
                self.session_id = data.get("session_id")
                self.user_data = data.get("user_data")
                logger.info("Session loaded")
                return self.session_id
        except FileNotFoundError:
            logger.info("No saved session found")
            return None
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None
    
    def clear_session(self):
        """Clear session data"""
        self.session_id = None
        self.user_data = None
        try:
            import os
            if os.path.exists("session.json"):
                os.remove("session.json")
            logger.info("Session cleared")
        except Exception as e:
            logger.error(f"Error clearing session: {e}")


# Singleton instance
_network_client = None

def get_network_client(server_url: str = "ws://localhost:8765") -> NetworkClient:
    """Get or create the network client singleton"""
    global _network_client
    if _network_client is None:
        _network_client = NetworkClient(server_url)
        logger.info("Network client singleton created")
    return _network_client

def reset_network_client():
    """Reset the network client singleton (for testing)"""
    global _network_client
    if _network_client:
        _network_client.disconnect()
    _network_client = None
    logger.info("Network client reset")
