# OPTIMIZED VERSION - Enhanced online game with better network handling
"""
Tetris Battle Online - Enhanced Multiplayer Version
Integrates with the multiplayer server for online play with enhanced UI
"""

import pygame
import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from TetrisBattle.tetris_game import TetrisGame, TetrisGameDouble, POS_LIST
from TetrisBattle.tetris import Tetris, Player, Judge
from TetrisBattle.settings import FPS, MAX_TIME, SPEED_UP
from auth_ui import AuthUI
from matchmaking_ui import MatchmakingUI
from network_client import get_network_client

logger = logging.getLogger(__name__)

class TetrisGameOnline(TetrisGameDouble):
    """Online multiplayer Tetris game with enhanced UI"""
    
    def __init__(self):
        # Initialize pygame first
        if not pygame.get_init():
            pygame.init()
        
        super().__init__()
        
        # Ensure width and height are set from parent class or screen
        if not hasattr(self, 'width'):
            self.width = self.screen.get_width()
        if not hasattr(self, 'height'):
            self.height = self.screen.get_height()
        
        # Network client
        self.network = get_network_client()
        
        # Game state
        self.current_screen = "auth"  # "auth", "matchmaking", "game"
        self.auth_ui = None
        self.matchmaking_ui = None
        self.opponent_data = None
        self.player_id = None
        self.selected_map = "none"  # Default map (standard grid)
        
        # Network game state
        self.opponent_state = None
        self.game_started = False
        self.game_ended = False
        self.game_result = None
        
        # Register network callbacks
        self.network.register_callback("game_state", self.handle_opponent_state)
        self.network.register_callback("game_end", self.handle_game_end)
        self.network.register_callback("opponent_disconnected", self.handle_opponent_disconnect)
    
    def handle_opponent_state(self, data):
        """Handle opponent's game state update"""
        self.opponent_state = data.get("state")
    
    def handle_game_end(self, data):
        """Handle game end from server"""
        result = data.get("result")
        self.game_ended = True
        self.game_result = result
        logger.info(f"Game ended with result: {result}")
    
    def handle_opponent_disconnect(self, data):
        """Handle opponent disconnection"""
        # Player wins by forfeit
        self.game_ended = True
        self.game_result = "win"
        logger.info("Opponent disconnected - you win!")
    
    def play(self):
        """Main game loop with enhanced screen management"""
        # Start network client
        self.network.start()
        
        # Wait for connection
        import time
        max_wait = 5
        waited = 0
        while not self.network.is_connected() and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
        
        if not self.network.is_connected():
            print("Failed to connect to server. Please check server is running.")
            return
        
        running = True
        clock = pygame.time.Clock()
        
        # Initialize enhanced auth UI
        self.auth_ui = AuthUI(self.screen)
        self.auth_ui.try_auto_login()
        
        while running:
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
            
            if self.current_screen == "auth":
                # Authentication screen
                self.auth_ui.handle_events(events)
                self.auth_ui.draw()
                
                # Check if logged in
                if self.auth_ui.is_logged_in():
                    user_data = self.auth_ui.get_user_data()
                    self.matchmaking_ui = MatchmakingUI(self.screen, user_data)
                    self.current_screen = "matchmaking"
            
            elif self.current_screen == "matchmaking":
                # Matchmaking screen
                action = self.matchmaking_ui.handle_events(events)
                
                if action == "logout":
                    self.network.clear_session()
                    self.current_screen = "auth"
                    self.auth_ui = AuthUI(self.screen)
                
                self.matchmaking_ui.draw()
                
                # Check if game found
                if self.matchmaking_ui.is_game_found():
                    self.opponent_data = self.matchmaking_ui.get_opponent_data()
                    self.selected_map = self.matchmaking_ui.get_selected_map()
                    self.current_screen = "game"
                    self.start_online_game()
            
            elif self.current_screen == "game":
                # Game screen - handled by start_online_game
                pass
            
            pygame.display.flip()
            clock.tick(60)
        
        # Cleanup
        self.network.disconnect()
        pygame.quit()
    
    def start_online_game(self):
        """Start the online game with selected map"""
        # Reset game state
        self.game_ended = False
        self.game_result = None
        
        # Use selected map with safe fallback
        # Valid gridchoice values: "none" (standard), "classic", or grid file names
        valid_maps = ["none", "classic", "random"]
        if self.selected_map in valid_maps:
            gridchoice = self.selected_map
        else:
            gridchoice = "none"  # Default to standard grid
        
        # Special handling for random
        if gridchoice == "random":
            import random
            gridchoice = random.choice(["none", "classic"])
        
        logger.info(f"Starting game with map: {gridchoice}")
        
        self.timer2p.tick()
        pygame.init()
        
        running = True
        self.renderer.drawByName("gamescreen", 0, 0)
        
        time = MAX_TIME
        
        # Create our player configuration
        my_info_dict = {
            "id": 0,
            "hold": pygame.K_c,
            "drop": pygame.K_SPACE,
            "rotate_right": pygame.K_UP,
            "rotate_left": pygame.K_z,
            "right": pygame.K_RIGHT,
            "left": pygame.K_LEFT,
            "down": pygame.K_DOWN
        }
        
        # Create opponent display configuration
        opponent_info_dict = {
            "id": 1,
            "hold": pygame.K_RSHIFT,
            "drop": pygame.K_KP_ENTER,
            "rotate_right": pygame.K_KP8,
            "rotate_left": pygame.K_KP7,
            "right": pygame.K_KP6,
            "left": pygame.K_KP4,
            "down": pygame.K_KP5
        }
        
        # Create our tetris instance
        my_tetris = Tetris(Player(my_info_dict), gridchoice)
        my_pos = POS_LIST[0]
        
        # Create opponent tetris instance
        opponent_tetris = Tetris(Player(opponent_info_dict), gridchoice)
        opponent_pos = POS_LIST[1]
        
        winner = None
        force_quit = False
        last_sent_time = 0
        
        # Main game loop
        while running:
            import time as time_module
            current_time = time_module.time()
            
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    running = False
                    force_quit = True
                
                # Only process our input
                my_tetris.trigger(evt)
            
            # Update our game
            my_tetris.natural_down()
            my_tetris.move()
            
            # Send game state periodically (every 100ms)
            if current_time - last_sent_time > 0.1:
                self.send_full_game_state(my_tetris, 0)
                last_sent_time = current_time
            
            # Check if our block fell
            if my_tetris.check_fallen():
                scores = my_tetris.clear()
                
                # Send attack to opponent through network
                if scores > 0:
                    self.send_full_game_state(my_tetris, attack=scores)
                
                # Draw effects
                self.renderer.drawCombo(my_tetris, *my_pos["combo"])
                self.renderer.drawTetris(my_tetris, *my_pos["tetris"])
                self.renderer.drawTspin(my_tetris, *my_pos["tspin"])
                self.renderer.drawBack2Back(my_tetris, *my_pos["back2back"])
                
                # Check if we lost
                if my_tetris.check_KO():
                    self.renderer.drawBoard(my_tetris, *my_pos["board"])
                    my_tetris.clear_garbage()
                    pygame.display.flip()
                    
                    # Send game end immediately
                    self.network.send_game_end("lose")
                    
                    running = False
                    winner = 1  # Opponent wins
                
                # Check if we got 3 KOs (we win)
                if my_tetris.KO >= 3:
                    my_tetris.update_ko()
                    self.renderer.drawKO(my_tetris.KO, *my_pos["ko"])
                    
                    # Send game end immediately
                    self.network.send_game_end("win")
                    
                    running = False
                    winner = 0  # We win
                
                my_tetris.new_block()
            
            # Check if game ended from server
            if self.game_ended:
                running = False
                if self.game_result == "win":
                    winner = 0
                elif self.game_result == "lose":
                    winner = 1
                continue
            
            # Update opponent board from network state
            if self.opponent_state:
                self.update_opponent_display(opponent_tetris, self.opponent_state)
                
                # Handle incoming attack
                attack = self.opponent_state.get('attack', 0)
                if attack > 0:
                    my_tetris.add_attacked(attack)
                    self.opponent_state['attack'] = 0
                
                # Check if opponent lost
                if self.opponent_state.get('is_ko', False):
                    running = False
                    winner = 0
                
                # Check if opponent got 3 KOs
                if opponent_tetris.KO >= 3:
                    running = False
                    winner = 1
            
            # Draw game screens
            self.renderer.drawGameScreen(my_tetris)
            self.renderer.drawGameScreen(opponent_tetris)
            
            my_tetris.increment_timer()
            opponent_tetris.increment_timer()
            
            # Draw attack indicators
            if my_tetris.attacked == 0:
                pygame.draw.rect(self.screen, (30, 30, 30), my_pos["attack_clean"])
            else:
                for j in range(my_tetris.attacked):
                    pos_attack_alarm = list(my_pos["attack_alarm"])
                    pos_attack_alarm[1] = pos_attack_alarm[1] - 18 * j
                    pygame.draw.rect(self.screen, (255, 0, 0), pos_attack_alarm)
            
            if opponent_tetris.attacked == 0:
                pygame.draw.rect(self.screen, (30, 30, 30), opponent_pos["attack_clean"])
            else:
                for j in range(opponent_tetris.attacked):
                    pos_attack_alarm = list(opponent_pos["attack_alarm"])
                    pos_attack_alarm[1] = pos_attack_alarm[1] - 18 * j
                    pygame.draw.rect(self.screen, (255, 0, 0), pos_attack_alarm)
            
            # Draw KO counts
            if my_tetris.KO > 0:
                self.renderer.drawKO(my_tetris.KO, *my_pos["big_ko"])
            
            if opponent_tetris.KO > 0:
                self.renderer.drawKO(opponent_tetris.KO, *opponent_pos["big_ko"])
            
            # Draw both game boards
            self.renderer.drawScreen(my_tetris, *my_pos["drawscreen"])
            self.renderer.drawScreen(opponent_tetris, *opponent_pos["drawscreen"])
            
            # Draw map name
            try:
                map_font = pygame.font.Font(None, 24)
                map_text = map_font.render(f"Map: {gridchoice.upper()}", True, (200, 200, 255))
                screen_width = self.screen.get_width()
                self.screen.blit(map_text, (screen_width // 2 - 50, 10))
            except Exception as e:
                logger.error(f"Error drawing map name: {e}")
            
            # Update time
            time, running = self.update_time(time, running)
            
            if not running and winner is None:
                # Time ran out - determine winner by score
                winner = Judge.who_win(my_tetris, opponent_tetris)
            
            self.renderer.drawTime2p(time)
            
            self.myClock.tick(FPS)
            pygame.display.flip()
        
        # Send game end to server if not already sent
        if not self.game_ended:
            if winner == 0:
                self.network.send_game_end("win")
            elif winner == 1:
                self.network.send_game_end("lose")
        
        # Show result
        if not force_quit:
            if winner == 0:
                self.renderer.drawByName("transparent", *my_pos["transparent"])
                self.renderer.drawByName("you_win", *my_pos["you_win"])
                self.renderer.drawByName("transparent", *opponent_pos["transparent"])
                self.renderer.drawByName("you_lose", *opponent_pos["you_lose"])
            else:
                self.renderer.drawByName("transparent", *my_pos["transparent"])
                self.renderer.drawByName("you_lose", *my_pos["you_lose"])
                self.renderer.drawByName("transparent", *opponent_pos["transparent"])
                self.renderer.drawByName("you_win", *opponent_pos["you_win"])
            
            pygame.display.flip()
            
            import time as t
            t.sleep(3.0)
        
        # Return to matchmaking
        self.current_screen = "matchmaking"
        self.matchmaking_ui.reset()
    
    def send_full_game_state(self, tetris, attack=0):
        """Send complete game state to opponent"""
        state = {
            "grid": tetris.grid,
            "current_block": {
                "type": tetris.block.block_type(),
                "rotation": tetris.block.current_shape_id,
                "x": tetris.px,
                "y": tetris.py
            },
            "held": tetris.held.block_type() if tetris.held else None,
            "next_pieces": [p.block_type() for p in tetris.buffer.now_list[:5]],
            "attack": attack,
            "combo": tetris.combo,
            "ko": tetris.KO,
            "lines_sent": tetris.sent,
            "attacked": tetris.attacked,
            "is_ko": tetris.check_KO()
        }
        self.network.send_game_state(state)
    
    def update_opponent_display(self, opponent_tetris, state):
        """Update opponent's tetris display from network state"""
        try:
            # Update grid
            if "grid" in state:
                opponent_tetris.grid = state["grid"]
            
            # Update current block position
            if "current_block" in state:
                block_data = state["current_block"]
                block_type = block_data.get("type")
                
                from TetrisBattle.tetris import Piece
                from TetrisBattle.settings import PIECES_DICT
                
                if block_type:
                    opponent_tetris.block = Piece(block_type, PIECES_DICT[block_type])
                    opponent_tetris.block.current_shape_id = block_data.get("rotation", 0)
                    opponent_tetris.px = block_data.get("x", 4)
                    opponent_tetris.py = block_data.get("y", 0)
            
            # Update held piece
            if "held" in state and state["held"]:
                from TetrisBattle.tetris import Piece
                from TetrisBattle.settings import PIECES_DICT
                held_type = state["held"]
                opponent_tetris.held = Piece(held_type, PIECES_DICT[held_type])
            
            # Update next pieces
            if "next_pieces" in state:
                from TetrisBattle.tetris import Piece
                from TetrisBattle.settings import PIECES_DICT
                opponent_tetris.buffer.now_list = [
                    Piece(bt, PIECES_DICT[bt]) for bt in state["next_pieces"]
                ]
            
            # Update stats
            if "combo" in state:
                opponent_tetris.combo = state["combo"]
            
            if "ko" in state:
                opponent_tetris._KO = state["ko"]
            
            if "lines_sent" in state:
                opponent_tetris.sent = state["lines_sent"]
            
            if "attacked" in state:
                opponent_tetris._attacked = state["attacked"]
                
        except Exception as e:
            logger.error(f"Error updating opponent display: {e}")


if __name__ == "__main__":
    game = TetrisGameOnline()
    game.play()