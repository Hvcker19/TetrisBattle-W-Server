# OPTIMIZED VERSION - Enhanced server with better error handling
"""
Tetris Battle Multiplayer Server
Handles authentication, matchmaking, and real-time gameplay
"""

import asyncio
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError
import json
import sqlite3
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Server configuration
HOST = "0.0.0.0"
PORT = 8765
DB_FILE = "tetris_battle.db"

class Database:
    """Handle database operations for user management"""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                total_games INTEGER DEFAULT 0,
                rating INTEGER DEFAULT 1000
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Game history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_id INTEGER NOT NULL,
                player2_id INTEGER NOT NULL,
                winner_id INTEGER,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration INTEGER,
                FOREIGN KEY (player1_id) REFERENCES users (user_id),
                FOREIGN KEY (player2_id) REFERENCES users (user_id),
                FOREIGN KEY (winner_id) REFERENCES users (user_id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str, email: str = None) -> tuple:
        """Register a new user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                (username, password_hash, email)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            logger.info(f"User registered: {username}")
            return True, user_id, "Registration successful"
        except sqlite3.IntegrityError as e:
            conn.close()
            if "username" in str(e):
                return False, None, "Username already exists"
            elif "email" in str(e):
                return False, None, "Email already registered"
            return False, None, "Registration failed"
    
    def login_user(self, username: str, password: str) -> tuple:
        """Login user and create session"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT user_id, username, wins, losses, rating FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        result = cursor.fetchone()
        
        if result:
            user_id, username, wins, losses, rating = result
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)
            
            cursor.execute(
                "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)",
                (session_id, user_id, expires_at)
            )
            
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"User logged in: {username}")
            return True, {
                "session_id": session_id,
                "user_id": user_id,
                "username": username,
                "stats": {
                    "wins": wins,
                    "losses": losses,
                    "rating": rating
                }
            }, "Login successful"
        else:
            conn.close()
            return False, None, "Invalid username or password"
    
    def validate_session(self, session_id: str) -> tuple:
        """Validate session and return user info"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.user_id, u.username, u.wins, u.losses, u.rating
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_id = ? AND s.expires_at > CURRENT_TIMESTAMP
        """, (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_id, username, wins, losses, rating = result
            return True, {
                "user_id": user_id,
                "username": username,
                "stats": {
                    "wins": wins,
                    "losses": losses,
                    "rating": rating
                }
            }
        return False, None
    
    def update_game_result(self, player1_id: int, player2_id: int, winner_id: int, duration: int):
        """Update game results and player stats"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Record game
        cursor.execute("""
            INSERT INTO game_history (player1_id, player2_id, winner_id, duration)
            VALUES (?, ?, ?, ?)
        """, (player1_id, player2_id, winner_id, duration))
        
        # Update winner stats
        cursor.execute("""
            UPDATE users 
            SET wins = wins + 1, total_games = total_games + 1, rating = rating + 25
            WHERE user_id = ?
        """, (winner_id,))
        
        # Update loser stats
        loser_id = player2_id if winner_id == player1_id else player1_id
        cursor.execute("""
            UPDATE users 
            SET losses = losses + 1, total_games = total_games + 1, rating = rating - 15
            WHERE user_id = ?
        """, (loser_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"Game result recorded: Winner {winner_id}")


class Player:
    """Represents a connected player"""
    
    def __init__(self, websocket, user_id: int, username: str, stats: dict):
        self.websocket = websocket
        self.user_id = user_id
        self.username = username
        self.stats = stats
        self.in_game = False
        self.game_room = None
    
    async def send(self, message: dict):
        """Send message to player"""
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending to {self.username}: {e}")


class GameRoom:
    """Represents a game between two players"""
    
    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2
        self.game_id = f"{player1.user_id}_{player2.user_id}_{int(time.time())}"
        self.start_time = time.time()
        self.ended = False
        
        player1.in_game = True
        player1.game_room = self
        player2.in_game = True
        player2.game_room = self
        
        logger.info(f"Game created: {player1.username} vs {player2.username}")
    
    async def start_game(self):
        """Send game start messages to both players"""
        game_info = {
            "type": "game_start",
            "opponent": {
                "username": self.player2.username,
                "stats": self.player2.stats
            },
            "player_id": 0
        }
        await self.player1.send(game_info)
        
        game_info = {
            "type": "game_start",
            "opponent": {
                "username": self.player1.username,
                "stats": self.player1.stats
            },
            "player_id": 1
        }
        await self.player2.send(game_info)
    
    async def relay_game_state(self, from_player: Player, game_state: dict):
        """Relay game state from one player to opponent"""
        to_player = self.player2 if from_player == self.player1 else self.player1
        
        message = {
            "type": "game_state",
            "state": game_state
        }
        await to_player.send(message)
    
    async def end_game(self, winner: Player, db: Database):
        """End game and update stats"""
        if self.ended:
            return
        
        self.ended = True
        duration = int(time.time() - self.start_time)
        
        # Update database
        db.update_game_result(
            self.player1.user_id,
            self.player2.user_id,
            winner.user_id,
            duration
        )
        
        # Notify both players immediately
        loser = self.player2 if winner == self.player1 else self.player1
        
        # Send to winner
        await winner.send({
            "type": "game_end",
            "result": "win",
            "duration": duration
        })
        
        # Send to loser
        await loser.send({
            "type": "game_end",
            "result": "lose",
            "duration": duration
        })
        
        # Clean up
        self.player1.in_game = False
        self.player1.game_room = None
        self.player2.in_game = False
        self.player2.game_room = None
        
        logger.info(f"Game ended: {winner.username} won against {loser.username}")
        
        # Small delay to ensure messages are sent
        await asyncio.sleep(0.1)


class Matchmaking:
    """Handle player matchmaking queue"""
    
    def __init__(self):
        self.queue: list[Player] = []
        self.lock = asyncio.Lock()
    
    async def add_player(self, player: Player) -> Optional[Player]:
        """Add player to queue and try to find match"""
        async with self.lock:
            # Simple matchmaking - pair with first available player
            if len(self.queue) > 0:
                opponent = self.queue.pop(0)
                logger.info(f"Match found: {player.username} vs {opponent.username}")
                return opponent
            else:
                self.queue.append(player)
                logger.info(f"Player {player.username} added to queue")
                await player.send({
                    "type": "matchmaking_status",
                    "status": "searching",
                    "queue_position": len(self.queue)
                })
                return None
    
    async def remove_player(self, player: Player):
        """Remove player from queue"""
        async with self.lock:
            if player in self.queue:
                self.queue.remove(player)
                logger.info(f"Player {player.username} removed from queue")


class TetrisBattleServer:
    """Main server class"""
    
    def __init__(self):
        self.db = Database(DB_FILE)
        self.matchmaking = Matchmaking()
        self.players: Dict[int, Player] = {}  # user_id -> Player
        self.game_rooms: list[GameRoom] = []
    
    async def handle_client(self, websocket):
        """Handle client connection"""
        player = None
        remote_address = websocket.remote_address if hasattr(websocket, 'remote_address') else 'unknown'
        logger.info(f"New connection from {remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "register":
                        await self.handle_register(websocket, data)
                    
                    elif msg_type == "login":
                        player = await self.handle_login(websocket, data)
                    
                    elif msg_type == "validate_session":
                        player = await self.handle_validate_session(websocket, data)
                    
                    elif msg_type == "find_match":
                        if player:
                            await self.handle_find_match(player)
                    
                    elif msg_type == "cancel_match":
                        if player:
                            await self.handle_cancel_match(player)
                    
                    elif msg_type == "game_state":
                        if player and player.in_game:
                            await self.handle_game_state(player, data)
                    
                    elif msg_type == "game_end":
                        if player and player.in_game:
                            await self.handle_game_end_from_client(player, data)
                    
                    elif msg_type == "disconnect":
                        break
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {remote_address}: {e}")
                except Exception as e:
                    logger.error(f"Error processing message from {remote_address}: {e}")
        
        except ConnectionClosedOK:
            logger.info(f"Connection closed normally: {remote_address}")
        except ConnectionClosedError as e:
            logger.warning(f"Connection closed with error from {remote_address}: {e}")
        except ConnectionClosed as e:
            logger.info(f"Connection closed from {remote_address}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error handling client {remote_address}: {e}")
        finally:
            if player:
                await self.cleanup_player(player)
            logger.info(f"Connection handler finished for {remote_address}")
    
    async def handle_register(self, websocket, data):
        """Handle user registration"""
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        
        success, user_id, message = self.db.register_user(username, password, email)
        
        response = {
            "type": "register_response",
            "success": success,
            "message": message
        }
        
        await websocket.send(json.dumps(response))
    
    async def handle_login(self, websocket, data) -> Optional[Player]:
        """Handle user login"""
        username = data.get("username")
        password = data.get("password")
        
        success, user_data, message = self.db.login_user(username, password)
        
        if success:
            player = Player(
                websocket,
                user_data["user_id"],
                user_data["username"],
                user_data["stats"]
            )
            self.players[player.user_id] = player
            
            response = {
                "type": "login_response",
                "success": True,
                "session_id": user_data["session_id"],
                "user": {
                    "user_id": user_data["user_id"],
                    "username": user_data["username"],
                    "stats": user_data["stats"]
                },
                "message": message
            }
        else:
            response = {
                "type": "login_response",
                "success": False,
                "message": message
            }
            player = None
        
        await websocket.send(json.dumps(response))
        return player
    
    async def handle_validate_session(self, websocket, data) -> Optional[Player]:
        """Handle session validation"""
        session_id = data.get("session_id")
        
        valid, user_data = self.db.validate_session(session_id)
        
        if valid:
            player = Player(
                websocket,
                user_data["user_id"],
                user_data["username"],
                user_data["stats"]
            )
            self.players[player.user_id] = player
            
            response = {
                "type": "session_valid",
                "success": True,
                "user": user_data
            }
        else:
            response = {
                "type": "session_valid",
                "success": False,
                "message": "Session expired or invalid"
            }
            player = None
        
        await websocket.send(json.dumps(response))
        return player
    
    async def handle_find_match(self, player: Player):
        """Handle matchmaking request"""
        opponent = await self.matchmaking.add_player(player)
        
        if opponent:
            # Create game room
            game_room = GameRoom(player, opponent)
            self.game_rooms.append(game_room)
            await game_room.start_game()
    
    async def handle_cancel_match(self, player: Player):
        """Handle cancel matchmaking"""
        await self.matchmaking.remove_player(player)
        await player.send({
            "type": "matchmaking_cancelled"
        })
    
    async def handle_game_state(self, player: Player, data):
        """Handle game state update from player"""
        if player.game_room:
            await player.game_room.relay_game_state(player, data.get("state"))
    
    async def handle_game_end_from_client(self, player: Player, data):
        """Handle game end notification from client"""
        if player.game_room and not player.game_room.ended:
            result = data.get("result")  # "win" or "lose"
            
            if result == "win":
                await player.game_room.end_game(player, self.db)
            elif result == "lose":
                opponent = (player.game_room.player2 
                           if player == player.game_room.player1 
                           else player.game_room.player1)
                await player.game_room.end_game(opponent, self.db)
    
    async def cleanup_player(self, player: Player):
        """Clean up player on disconnect"""
        # Remove from matchmaking
        await self.matchmaking.remove_player(player)
        
        # Handle game disconnect
        if player.in_game and player.game_room:
            # Opponent wins by forfeit
            opponent = (player.game_room.player2 
                       if player == player.game_room.player1 
                       else player.game_room.player1)
            await player.game_room.end_game(opponent, self.db)
            
            await opponent.send({
                "type": "opponent_disconnected"
            })
        
        # Remove from players dict
        if player.user_id in self.players:
            del self.players[player.user_id]
        
        logger.info(f"Player {player.username} cleaned up")
    
    async def start(self):
        """Start the server"""
        logger.info(f"Starting Tetris Battle Server on {HOST}:{PORT}")
        
        async with websockets.serve(self.handle_client, HOST, PORT):
            logger.info("Server is running. Press Ctrl+C to stop.")
            await asyncio.Future()  # run forever


if __name__ == "__main__":
    server = TetrisBattleServer()
    asyncio.run(server.start())