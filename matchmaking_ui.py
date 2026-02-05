# OPTIMIZED VERSION - Enhanced matchmaking UI
"""
Matchmaking UI for Tetris Battle - Enhanced with Map Selection
Shows user stats, map selection, and handles finding matches
"""

import pygame
from network_client import get_network_client

class Button:
    """Enhanced button for matchmaking UI"""
    
    def __init__(self, x, y, width, height, text, font, 
                 color=(70, 180, 100), hover_color=(90, 220, 130)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.base_color = color
        self.hover_color = hover_color
        self.current_color = color
        self.is_hovered = False
        self.press_offset = 0
    
    def draw(self, screen):
        """Draw the button with shadow"""
        # Shadow
        shadow_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3 + self.press_offset, 
                                 self.rect.width, self.rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=10)
        
        # Button
        button_rect = pygame.Rect(self.rect.x, self.rect.y + self.press_offset,
                                 self.rect.width, self.rect.height)
        pygame.draw.rect(screen, self.current_color, button_rect, border_radius=10)
        
        # Highlight
        highlight_rect = pygame.Rect(button_rect.x, button_rect.y, 
                                    button_rect.width, button_rect.height // 3)
        highlight_color = tuple(min(c + 40, 255) for c in self.current_color)
        pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=10)
        
        # Border
        pygame.draw.rect(screen, (255, 255, 255), button_rect, 3, border_radius=10)
        
        # Text
        text_shadow = self.font.render(self.text, True, (0, 0, 0))
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=button_rect.center)
        screen.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        """Handle button events"""
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.current_color = self.hover_color
                self.is_hovered = True
            else:
                self.current_color = self.base_color
                self.is_hovered = False
                self.press_offset = 0
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.press_offset = 2
                return True
        
        if event.type == pygame.MOUSEBUTTONUP:
            self.press_offset = 0
        
        return False


class MapSelectionButton:
    """Button for selecting game maps"""
    
    def __init__(self, x, y, width, height, map_name, map_display, font, selected=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.map_name = map_name
        self.map_display = map_display
        self.font = font
        self.selected = selected
        self.hovered = False
        
        # Colors
        self.base_color = (60, 60, 80)
        self.selected_color = (80, 180, 120)
        self.hover_color = (80, 80, 100)
    
    def draw(self, screen):
        """Draw the map selection button"""
        # Determine color
        if self.selected:
            color = self.selected_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.base_color
        
        # Draw background
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        
        # Draw border
        border_color = (150, 255, 150) if self.selected else (120, 120, 150)
        border_width = 4 if self.selected else 2
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=8)
        
        # Draw text
        text_color = (255, 255, 255) if self.selected else (200, 200, 220)
        text_surface = self.font.render(self.map_display, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
        # Draw checkmark if selected
        if self.selected:
            check_font = pygame.font.Font(None, 36)
            check = check_font.render("✓", True, (255, 255, 255))
            check_rect = check.get_rect(topright=(self.rect.right - 10, self.rect.top + 5))
            screen.blit(check, check_rect)
    
    def handle_event(self, event):
        """Handle button events"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        
        return False


class MatchmakingUI:
    """Enhanced matchmaking screen with map selection"""
    
    def __init__(self, screen, user_data):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.user_data = user_data
        
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.tiny_font = pygame.font.Font(None, 22)
        
        # Network client
        self.network = get_network_client()
        
        # State
        self.searching = False
        self.game_found = False
        self.opponent_data = None
        self.status_message = "Ready to play!"
        self.selected_map = "none"  # Default map (standard with no obstacles)
        
        # Animation
        self.anim_timer = 0
        
        # Register callbacks
        self.network.register_callback("matchmaking_status", self.handle_matchmaking_status)
        self.network.register_callback("game_start", self.handle_game_start)
        
        # Create UI elements
        self.create_buttons()
        self.create_map_buttons()
    
    def create_buttons(self):
        """Create main buttons"""
        center_x = self.width // 2
        
        self.find_match_button = Button(
            center_x - 120, 520, 240, 70,
            "FIND MATCH", self.font,
            color=(50, 180, 80), hover_color=(70, 220, 110)
        )
        
        self.cancel_button = Button(
            center_x - 120, 520, 240, 70,
            "CANCEL", self.font,
            color=(200, 60, 60), hover_color=(240, 80, 80)
        )
        
        self.logout_button = Button(
            20, self.height - 70, 150, 50,
            "Logout", self.small_font,
            color=(100, 100, 120), hover_color=(130, 130, 150)
        )
    
    def create_map_buttons(self):
        """Create map selection buttons"""
        # Available maps - using valid gridchoice values
        # Valid options: "none" (no obstacles), "classic", or other grid files in TetrisBattle/grid/
        maps = [
            ("none", "Standard"),
            ("classic", "Classic"),
            ("random", "Random")
        ]
        
        self.map_buttons = []
        center_x = self.width // 2
        start_x = center_x - 180
        button_width = 170
        button_height = 50
        spacing = 20
        
        for i, (map_name, display_name) in enumerate(maps):
            x = start_x + (i % 3) * (button_width + spacing)
            y = 380 + (i // 3) * (button_height + spacing)
            
            button = MapSelectionButton(
                x, y, button_width, button_height,
                map_name, display_name, self.small_font,
                selected=(map_name == self.selected_map)
            )
            self.map_buttons.append(button)
    
    def handle_matchmaking_status(self, data):
        """Handle matchmaking status update"""
        status = data.get("status")
        if status == "searching":
            queue_pos = data.get("queue_position", 0)
            self.status_message = f"Searching for opponent... (Queue: {queue_pos})"
    
    def handle_game_start(self, data):
        """Handle game start notification"""
        self.game_found = True
        self.opponent_data = data.get("opponent")
        self.status_message = f"Match found! vs {self.opponent_data['username']}"
    
    def handle_events(self, events):
        """Handle pygame events"""
        for event in events:
            # Map selection
            if not self.searching:
                for button in self.map_buttons:
                    if button.handle_event(event):
                        # Deselect all
                        for b in self.map_buttons:
                            b.selected = False
                        # Select this one
                        button.selected = True
                        self.selected_map = button.map_name
            
            # Main buttons
            if not self.searching:
                if self.find_match_button.handle_event(event):
                    self.start_matchmaking()
            else:
                if self.cancel_button.handle_event(event):
                    self.cancel_matchmaking()
            
            if self.logout_button.handle_event(event):
                return "logout"
        
        return None
    
    def start_matchmaking(self):
        """Start searching for a match"""
        self.searching = True
        # Send selected map to server (you can extend network protocol to include this)
        self.network.find_match()
        self.status_message = "Searching for opponent..."
    
    def cancel_matchmaking(self):
        """Cancel matchmaking"""
        self.searching = False
        self.network.cancel_match()
        self.status_message = "Search cancelled"
    
    def draw(self):
        """Draw the matchmaking screen"""
        # Gradient background
        for y in range(self.height):
            color_value = int(20 + (y / self.height) * 40)
            pygame.draw.line(self.screen, (color_value, color_value // 2, color_value * 1.5), 
                           (0, y), (self.width, y))
        
        # Animated title
        self.anim_timer += 0.05
        import math
        
        title_text = "TETRIS BATTLE"
        colors = [(255, 100, 100), (255, 165, 0), (255, 255, 100), 
                 (100, 255, 100), (100, 200, 255), (150, 100, 255)]
        
        x_offset = (self.width - 550) // 2
        for i, char in enumerate(title_text):
            color = colors[i % len(colors)]
            y_offset = int(5 * math.sin(self.anim_timer + i * 0.3))
            
            char_surface = self.title_font.render(char, True, color)
            shadow = self.title_font.render(char, True, (0, 0, 0))
            
            self.screen.blit(shadow, (x_offset + i * 42 + 3, 53 + y_offset))
            self.screen.blit(char_surface, (x_offset + i * 42, 50 + y_offset))
        
        # Welcome message
        welcome = f"Welcome, {self.user_data['username']}!"
        welcome_surface = self.font.render(welcome, True, (200, 220, 255))
        welcome_rect = welcome_surface.get_rect(center=(self.width // 2, 140))
        self.screen.blit(welcome_surface, welcome_rect)
        
        # Stats box
        self.draw_stats_box()
        
        # Map selection section
        if not self.searching:
            self.draw_map_selection()
        
        # Status message
        status_color = (255, 255, 150) if not self.searching else (150, 255, 150)
        status_surface = self.font.render(self.status_message, True, status_color)
        status_rect = status_surface.get_rect(center=(self.width // 2, 470))
        
        # Status background
        bg_rect = pygame.Rect(status_rect.x - 15, status_rect.y - 8,
                             status_rect.width + 30, status_rect.height + 16)
        pygame.draw.rect(self.screen, (30, 35, 55), bg_rect, border_radius=8)
        pygame.draw.rect(self.screen, status_color, bg_rect, 2, border_radius=8)
        
        self.screen.blit(status_surface, status_rect)
        
        # Buttons
        if not self.searching:
            self.find_match_button.draw(self.screen)
        else:
            self.cancel_button.draw(self.screen)
            self.draw_searching_animation()
        
        self.logout_button.draw(self.screen)
    
    def draw_stats_box(self):
        """Draw enhanced player stats"""
        stats = self.user_data['stats']
        center_x = self.width // 2
        
        # Stats background with gradient
        stats_rect = pygame.Rect(center_x - 220, 190, 440, 140)
        
        # Outer glow
        glow_rect = pygame.Rect(stats_rect.x - 2, stats_rect.y - 2,
                               stats_rect.width + 4, stats_rect.height + 4)
        pygame.draw.rect(self.screen, (100, 150, 255), glow_rect, border_radius=12)
        
        # Main background
        pygame.draw.rect(self.screen, (35, 40, 65), stats_rect, border_radius=12)
        pygame.draw.rect(self.screen, (120, 160, 255), stats_rect, 3, border_radius=12)
        
        # Title
        title_surface = self.font.render("Player Statistics", True, (200, 220, 255))
        title_rect = title_surface.get_rect(center=(center_x, stats_rect.y + 25))
        self.screen.blit(title_surface, title_rect)
        
        # Stats in columns
        col1_x = center_x - 130
        col2_x = center_x + 20
        y_start = stats_rect.y + 60
        
        # Calculate win rate
        total_games = stats['wins'] + stats['losses']
        win_rate = (stats['wins'] / total_games * 100) if total_games > 0 else 0
        
        stats_data = [
            (f"Rating: {stats['rating']}", col1_x),
            (f"Wins: {stats['wins']}", col2_x),
            (f"Losses: {stats['losses']}", col1_x),
            (f"Win Rate: {win_rate:.1f}%", col2_x),
        ]
        
        for i, (stat, x) in enumerate(stats_data):
            y = y_start + (i % 2) * 35
            stat_surface = self.small_font.render(stat, True, (255, 255, 255))
            self.screen.blit(stat_surface, (x, y))
    
    def draw_map_selection(self):
        """Draw map selection UI"""
        center_x = self.width // 2
        
        # Section title
        title = "SELECT MAP"
        title_surface = self.small_font.render(title, True, (200, 220, 255))
        title_rect = title_surface.get_rect(center=(center_x, 350))
        self.screen.blit(title_surface, title_rect)
        
        # Map buttons
        for button in self.map_buttons:
            button.draw(self.screen)
        
        # Selected map info
        map_info = f"Selected: {self.selected_map.upper()}"
        info_surface = self.tiny_font.render(map_info, True, (150, 255, 150))
        info_rect = info_surface.get_rect(center=(center_x, 495))
        self.screen.blit(info_surface, info_rect)
    
    def draw_searching_animation(self):
        """Draw enhanced searching animation"""
        import math
        import time
        
        center_x = self.width // 2
        center_y = 600
        
        # Rotating circles
        num_circles = 8
        radius = 50
        current_time = time.time()
        
        for i in range(num_circles):
            angle = (2 * math.pi * i / num_circles) + (current_time * 3)
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            
            # Size variation
            size = int(8 + 4 * math.sin(current_time * 4 + i))
            size = max(2, size)  # Ensure positive size
            
            # Create gradient colors (fixed to ensure valid RGB values)
            hue = (i / num_circles + current_time * 0.5) % 1
            if hue < 0.33:
                r = max(0, min(255, int(255 * max(0, 1 - hue * 3))))
                g = max(0, min(255, int(255 * hue * 3)))
                b = 255
            elif hue < 0.67:
                r = 255
                g = max(0, min(255, int(255 * (1 - (hue - 0.33) * 3))))
                b = max(0, min(255, int(255 * (hue - 0.33) * 3)))
            else:
                r = max(0, min(255, int(255 * (hue - 0.67) * 3)))
                g = 255
                b = max(0, min(255, int(255 * (1 - (hue - 0.67) * 3))))
            
            color = (r, g, b)
            
            pygame.draw.circle(self.screen, color, (x, y), size)
            
            # Inner glow (only if size is big enough)
            if size > 2:
                inner_size = max(1, size // 2)
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), inner_size)
    
    def is_game_found(self):
        """Check if game was found"""
        return self.game_found
    
    def get_opponent_data(self):
        """Get opponent data"""
        return self.opponent_data
    
    def get_selected_map(self):
        """Get the selected map"""
        return self.selected_map
    
    def reset(self):
        """Reset matchmaking state"""
        self.searching = False
        self.game_found = False
        self.opponent_data = None
        self.status_message = "Ready to play!"