"""
Login and Registration UI for Tetris Battle - OPTIMIZED & ENHANCED
Features: Smooth animations, better error handling, improved UX, modern design
"""

import pygame
import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from network_client import get_network_client

class InputBox:
    """Enhanced text input box with smooth animations and validation"""
    
    def __init__(self, x, y, width, height, font, placeholder="", max_length=30):
        if not pygame.font.get_init():
            pygame.font.init()
            
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = pygame.Color(70, 130, 220)
        self.color_active = pygame.Color(30, 180, 255)
        self.color_error = pygame.Color(255, 100, 100)
        self.border_color = pygame.Color(180, 210, 255)
        self.color = self.color_inactive
        self.font = font
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.password_mode = False
        self.max_length = max_length
        self.cursor_visible = True
        self.cursor_timer = 0
        self.has_error = False
    
    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
            self.has_error = False
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                self.has_error = False
            elif event.key == pygame.K_TAB:
                return "tab"
            else:
                if len(self.text) < self.max_length and event.unicode.isprintable():
                    self.text += event.unicode
                    self.has_error = False
        
        return False
    
    def draw(self, screen):
        """Draw the enhanced input box with animations"""
        # Update cursor blink
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
        
        # Determine colors
        border_color = self.color_error if self.has_error else (self.color if self.active else self.border_color)
        
        # Draw outer glow (subtle)
        if self.active:
            glow_rect = pygame.Rect(self.rect.x - 3, self.rect.y - 3, 
                                   self.rect.width + 6, self.rect.height + 6)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*border_color[:3], 60), 
                           (0, 0, glow_rect.width, glow_rect.height), border_radius=10)
            screen.blit(glow_surface, (glow_rect.x, glow_rect.y))
        
        # Draw background
        bg_color = (30, 35, 55) if not self.active else (35, 42, 65)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=8)
        
        # Draw border
        border_width = 3 if self.active else 2
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=8)
        
        # Draw text or placeholder
        text_color = (255, 255, 255)
        if self.text:
            if self.password_mode:
                display_text = "●" * len(self.text)
            else:
                display_text = self.text
            text_surface = self.font.render(display_text, True, text_color)
        elif not self.active:
            text_surface = self.font.render(self.placeholder, True, (120, 140, 170))
        else:
            text_surface = self.font.render("", True, text_color)
        
        # Center text vertically
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        text_x = self.rect.x + 15
        screen.blit(text_surface, (text_x, text_y))
        
        # Draw cursor
        if self.active and self.cursor_visible:
            cursor_x = text_x + text_surface.get_width() + 2
            cursor_y = text_y
            pygame.draw.line(screen, text_color, 
                           (cursor_x, cursor_y), 
                           (cursor_x, cursor_y + text_surface.get_height()), 2)
    
    def get_text(self):
        return self.text.strip()
    
    def clear(self):
        self.text = ""
        self.has_error = False
    
    def set_error(self):
        """Mark input as having an error"""
        self.has_error = True


class Button:
    """Enhanced button with smooth hover effects and animations"""
    
    def __init__(self, x, y, width, height, text, font, 
                 color=(60, 170, 90), hover_color=(80, 210, 120), disabled_color=(80, 80, 90)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.base_color = color
        self.hover_color = hover_color
        self.disabled_color = disabled_color
        self.current_color = color
        self.is_hovered = False
        self.press_offset = 0
        self.enabled = True
        self.hover_progress = 0  # For smooth color transition
    
    def draw(self, screen):
        """Draw the enhanced button with smooth transitions"""
        # Smooth color transition
        if self.enabled:
            if self.is_hovered and self.hover_progress < 1:
                self.hover_progress = min(1, self.hover_progress + 0.15)
            elif not self.is_hovered and self.hover_progress > 0:
                self.hover_progress = max(0, self.hover_progress - 0.15)
            
            # Interpolate between base and hover color
            current_color = tuple(
                int(self.base_color[i] + (self.hover_color[i] - self.base_color[i]) * self.hover_progress)
                for i in range(3)
            )
        else:
            current_color = self.disabled_color
        
        # Draw shadow
        shadow_rect = pygame.Rect(self.rect.x + 4, self.rect.y + 4 + self.press_offset, 
                                 self.rect.width, self.rect.height)
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 80), 
                        (0, 0, shadow_rect.width, shadow_rect.height), border_radius=12)
        screen.blit(shadow_surface, (shadow_rect.x, shadow_rect.y))
        
        # Main button
        button_rect = pygame.Rect(self.rect.x, self.rect.y + self.press_offset,
                                 self.rect.width, self.rect.height)
        pygame.draw.rect(screen, current_color, button_rect, border_radius=12)
        
        # Highlight (top gradient effect)
        highlight_rect = pygame.Rect(button_rect.x + 2, button_rect.y + 2, 
                                    button_rect.width - 4, button_rect.height // 3)
        highlight_color = tuple(min(c + 50, 255) for c in current_color)
        highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surface, (*highlight_color, 100), 
                        (0, 0, highlight_rect.width, highlight_rect.height), border_radius=10)
        screen.blit(highlight_surface, (highlight_rect.x, highlight_rect.y))
        
        # Border
        border_color = (255, 255, 255) if self.enabled else (120, 120, 130)
        pygame.draw.rect(screen, border_color, button_rect, 3, border_radius=12)
        
        # Text with shadow
        text_color = (255, 255, 255) if self.enabled else (160, 160, 170)
        text_shadow = self.font.render(self.text, True, (0, 0, 0))
        text_surface = self.font.render(self.text, True, text_color)
        
        text_rect = text_surface.get_rect(center=button_rect.center)
        if self.enabled:
            screen.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        """Handle button events with animation"""
        if not self.enabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.press_offset = 3
                return True
        
        if event.type == pygame.MOUSEBUTTONUP:
            self.press_offset = 0
        
        return False
    
    def set_enabled(self, enabled):
        """Enable or disable the button"""
        self.enabled = enabled


class TetrisBackground:
    """Animated Tetris block background with improved performance"""
    
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.blocks = []
        self.colors = [
            (255, 120, 120),  # Red
            (255, 175, 60),   # Orange
            (255, 255, 120),  # Yellow
            (120, 255, 130),  # Green
            (120, 210, 255),  # Blue
            (170, 130, 255),  # Purple
            (255, 130, 200),  # Pink
        ]
        
        # Create initial blocks (reduced for performance)
        import random
        for i in range(15):
            self.blocks.append({
                'x': random.randint(0, screen_width),
                'y': random.randint(-screen_height, screen_height),
                'size': random.randint(25, 50),
                'color': random.choice(self.colors),
                'speed': random.uniform(0.4, 1.2),
                'alpha': random.randint(40, 90),
                'rotation': random.randint(0, 360),
                'rotation_speed': random.uniform(-1, 1)
            })
    
    def update(self):
        """Update block positions"""
        import random
        for block in self.blocks:
            block['y'] += block['speed']
            block['rotation'] += block['rotation_speed']
            
            # Reset if off screen
            if block['y'] > self.height + block['size']:
                block['y'] = -block['size']
                block['x'] = random.randint(0, self.width)
                block['speed'] = random.uniform(0.4, 1.2)
    
    def draw(self, screen):
        """Draw the background blocks efficiently"""
        for block in self.blocks:
            # Create semi-transparent surface
            surf = pygame.Surface((block['size'], block['size']), pygame.SRCALPHA)
            surf.fill((*block['color'], block['alpha']))
            
            # Rotate surface
            rotated = pygame.transform.rotate(surf, block['rotation'])
            rect = rotated.get_rect(center=(block['x'], block['y']))
            
            # Draw with border
            screen.blit(rotated, rect)
            pygame.draw.rect(screen, (*block['color'], block['alpha'] + 30), rect, 2)


class LoadingSpinner:
    """Animated loading spinner"""
    
    def __init__(self, x, y, radius=20):
        self.x = x
        self.y = y
        self.radius = radius
        self.angle = 0
        self.colors = [
            (100, 200, 255),
            (120, 180, 255),
            (140, 160, 255),
            (160, 140, 255)
        ]
    
    def update(self):
        """Update spinner animation"""
        self.angle = (self.angle + 12) % 360
    
    def draw(self, screen):
        """Draw the spinning loader"""
        for i in range(4):
            angle_rad = math.radians(self.angle + i * 90)
            x = self.x + int(self.radius * math.cos(angle_rad))
            y = self.y + int(self.radius * math.sin(angle_rad))
            size = 8 - i * 2
            pygame.draw.circle(screen, self.colors[i], (x, y), size)


class AuthUI:
    """Enhanced authentication screen with better UX"""
    
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Fonts
        self.title_font = pygame.font.Font(None, 80)
        self.subtitle_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 26)
        
        # Network client
        self.network = get_network_client()
        
        # State
        self.mode = "login"  # "login" or "register"
        self.logged_in = False
        self.user_data = None
        self.status_message = ""
        self.status_color = (200, 220, 255)
        self.is_loading = False
        
        # Animation
        self.anim_timer = 0
        self.background = TetrisBackground(self.width, self.height)
        self.loading_spinner = LoadingSpinner(self.width // 2, 580)
        
        # Register callbacks
        self.network.register_callback("login_response", self.handle_login_response)
        self.network.register_callback("register_response", self.handle_register_response)
        self.network.register_callback("session_valid", self.handle_session_valid)
        
        # Create UI elements
        center_x = self.width // 2
        
        # Input boxes with improved spacing
        self.username_input = InputBox(
            center_x - 180, 260, 360, 55, self.font, "Username"
        )
        self.password_input = InputBox(
            center_x - 180, 330, 360, 55, self.font, "Password"
        )
        self.password_input.password_mode = True
        
        self.email_input = InputBox(
            center_x - 180, 400, 360, 55, self.font, "Email (optional)"
        )
        
        # Buttons
        self.login_button = Button(
            center_x - 140, 480, 280, 65,
            "LOGIN", self.font,
            color=(50, 160, 80), hover_color=(70, 200, 110)
        )
        
        self.register_button = Button(
            center_x - 140, 480, 280, 65,
            "REGISTER", self.font,
            color=(80, 140, 200), hover_color=(100, 170, 230)
        )
        
        self.switch_button = Button(
            center_x - 120, 570, 240, 50,
            "Create Account", self.small_font,
            color=(100, 100, 130), hover_color=(130, 130, 160)
        )
        
        # Logo
        self.logo = None
    
    def switch_mode(self):
        """Switch between login and register mode"""
        self.mode = "register" if self.mode == "login" else "login"
        self.switch_button.text = "Back to Login" if self.mode == "register" else "Create Account"
        
        self.username_input.clear()
        self.password_input.clear()
        self.email_input.clear()
        self.status_message = ""
        self.is_loading = False
    
    def handle_login_response(self, data):
        """Handle login response from server"""
        self.is_loading = False
        if data["success"]:
            self.status_message = "✓ Login successful!"
            self.status_color = (100, 255, 120)
            self.logged_in = True
            self.user_data = data["user"]
            self.network.save_session(data["session_id"], data["user"])
        else:
            self.status_message = "✗ " + data["message"]
            self.status_color = (255, 120, 120)
            self.password_input.set_error()
    
    def handle_register_response(self, data):
        """Handle registration response from server"""
        self.is_loading = False
        if data["success"]:
            self.status_message = "✓ Registration successful! Please login."
            self.status_color = (100, 255, 120)
            self.mode = "login"
            self.switch_button.text = "Create Account"
            self.username_input.clear()
            self.password_input.clear()
        else:
            self.status_message = "✗ " + data["message"]
            self.status_color = (255, 120, 120)
    
    def handle_session_valid(self, data):
        """Handle session validation response"""
        self.is_loading = False
        if data["success"]:
            self.logged_in = True
            self.user_data = data["user"]
            self.status_message = f"✓ Welcome back, {data['user']['username']}!"
            self.status_color = (100, 255, 120)
        else:
            self.status_message = "Session expired. Please login."
            self.status_color = (255, 200, 120)
    
    def try_auto_login(self):
        """Try to auto-login with saved session"""
        session_id = self.network.load_session()
        if session_id:
            self.network.validate_session(session_id)
            self.status_message = "Checking saved session..."
            self.status_color = (180, 200, 255)
            self.is_loading = True
    
    def handle_events(self, events):
        """Handle pygame events"""
        for event in events:
            # Handle TAB navigation
            result = self.username_input.handle_event(event)
            if result == "tab":
                self.password_input.active = True
                self.username_input.active = False
            elif result:
                self.do_action()
            
            result = self.password_input.handle_event(event)
            if result == "tab":
                if self.mode == "register":
                    self.email_input.active = True
                    self.password_input.active = False
                else:
                    self.password_input.active = False
            elif result:
                self.do_action()
            
            if self.mode == "register":
                result = self.email_input.handle_event(event)
                if result == "tab":
                    self.email_input.active = False
                elif result:
                    self.do_action()
            
            if not self.is_loading:
                if self.login_button.handle_event(event) and self.mode == "login":
                    self.do_login()
                
                if self.register_button.handle_event(event) and self.mode == "register":
                    self.do_register()
                
                if self.switch_button.handle_event(event):
                    self.switch_mode()
    
    def do_action(self):
        """Execute the current action (login or register)"""
        if self.mode == "login":
            self.do_login()
        else:
            self.do_register()
    
    def do_login(self):
        """Perform login"""
        username = self.username_input.get_text()
        password = self.password_input.get_text()
        
        if not username or not password:
            self.status_message = "⚠ Please enter username and password"
            self.status_color = (255, 200, 100)
            if not username:
                self.username_input.set_error()
            if not password:
                self.password_input.set_error()
            return
        
        self.network.login(username, password)
        self.status_message = "Logging in..."
        self.status_color = (180, 200, 255)
        self.is_loading = True
    
    def do_register(self):
        """Perform registration"""
        username = self.username_input.get_text()
        password = self.password_input.get_text()
        email = self.email_input.get_text()
        
        # Validation
        if not username or not password:
            self.status_message = "⚠ Please enter username and password"
            self.status_color = (255, 200, 100)
            if not username:
                self.username_input.set_error()
            if not password:
                self.password_input.set_error()
            return
        
        if len(username) < 3:
            self.status_message = "⚠ Username must be at least 3 characters"
            self.status_color = (255, 200, 100)
            self.username_input.set_error()
            return
        
        if len(password) < 6:
            self.status_message = "⚠ Password must be at least 6 characters"
            self.status_color = (255, 200, 100)
            self.password_input.set_error()
            return
        
        self.network.register(username, password, email if email else None)
        self.status_message = "Registering..."
        self.status_color = (180, 200, 255)
        self.is_loading = True
    
    def draw(self):
        """Draw the enhanced authentication screen"""
        # Gradient background
        for y in range(self.height):
            ratio = y / self.height
            r = int(20 + ratio * 25)
            g = int(25 + ratio * 15)
            b = int(45 + ratio * 30)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))
        
        # Animated background blocks
        self.background.update()
        self.background.draw(self.screen)
        
        # Title with rainbow effect
        title_text = "TETRIS BATTLE"
        colors = [
            (255, 120, 120), (255, 175, 60), (255, 255, 120), 
            (120, 255, 130), (120, 210, 255), (170, 130, 255), (255, 130, 200)
        ]
        
        x_offset = (self.width - 650) // 2
        for i, char in enumerate(title_text):
            if char != ' ':
                color = colors[i % len(colors)]
                y_wave = int(6 * math.sin(self.anim_timer + i * 0.4))
                
                # Shadow
                shadow = self.title_font.render(char, True, (0, 0, 0))
                self.screen.blit(shadow, (x_offset + i * 45 + 4, 54 + y_wave))
                
                # Character
                char_surface = self.title_font.render(char, True, color)
                self.screen.blit(char_surface, (x_offset + i * 45, 50 + y_wave))
        
        # Subtitle
        self.anim_timer += 0.08
        subtitle = "LOGIN" if self.mode == "login" else "REGISTER"
        
        # Pulsing effect
        pulse = int(25 * math.sin(self.anim_timer * 2))
        subtitle_color = tuple(min(max(180 + pulse, 150), 255) for _ in range(3))
        
        subtitle_surface = self.subtitle_font.render(subtitle, True, subtitle_color)
        subtitle_rect = subtitle_surface.get_rect(center=(self.width // 2, 170))
        
        # Glow effect
        glow_surface = self.subtitle_font.render(subtitle, True, (80, 130, 200))
        glow_rect = glow_surface.get_rect(center=(self.width // 2, 171))
        self.screen.blit(glow_surface, glow_rect)
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Input boxes
        self.username_input.draw(self.screen)
        self.password_input.draw(self.screen)
        
        if self.mode == "register":
            self.email_input.draw(self.screen)
        
        # Buttons (disable during loading)
        self.login_button.set_enabled(not self.is_loading)
        self.register_button.set_enabled(not self.is_loading)
        self.switch_button.set_enabled(not self.is_loading)
        
        if self.mode == "login":
            self.login_button.draw(self.screen)
        else:
            self.register_button.draw(self.screen)
        
        self.switch_button.draw(self.screen)
        
        # Status message or loading spinner
        if self.is_loading:
            self.loading_spinner.update()
            self.loading_spinner.draw(self.screen)
        
        if self.status_message:
            status_y = 630
            status_surface = self.small_font.render(
                self.status_message, True, self.status_color
            )
            status_rect = status_surface.get_rect(center=(self.width // 2, status_y))
            
            # Background for status
            bg_rect = pygame.Rect(status_rect.x - 12, status_rect.y - 7,
                                 status_rect.width + 24, status_rect.height + 14)
            pygame.draw.rect(self.screen, (25, 30, 50), bg_rect, border_radius=6)
            pygame.draw.rect(self.screen, self.status_color, bg_rect, 2, border_radius=6)
            
            self.screen.blit(status_surface, status_rect)
        
        # Connection status indicator
        conn_status = self.network.get_connection_status()
        status_color = (100, 255, 120) if conn_status['connected'] else (255, 120, 120)
        pygame.draw.circle(self.screen, status_color, (30, 30), 8)
        
        status_text = "Connected" if conn_status['connected'] else "Disconnected"
        status_surf = self.small_font.render(status_text, True, status_color)
        self.screen.blit(status_surf, (45, 20))
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return self.logged_in
    
    def get_user_data(self):
        """Get logged in user data"""
        return self.user_data
