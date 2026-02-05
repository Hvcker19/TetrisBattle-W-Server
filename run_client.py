#!/usr/bin/env python3
"""
Tetris Battle Client Launcher
Simple script to start the game client with proper configuration
"""

import sys
import os

def main():
    print("=" * 60)
    print("TETRIS BATTLE - ONLINE MULTIPLAYER")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Check dependencies
    try:
        import pygame
        print("✓ pygame installed")
    except ImportError:
        print("✗ pygame not installed")
        print("  Run: pip install pygame")
        sys.exit(1)
    
    try:
        import websockets
        print("✓ websockets installed")
    except ImportError:
        print("✗ websockets not installed")
        print("  Run: pip install websockets")
        sys.exit(1)
    
    # Check for TetrisBattle package
    try:
        import TetrisBattle
        print("✓ TetrisBattle package found")
    except ImportError:
        print("✗ TetrisBattle package not found")
        print("  Make sure the original game files are in the TetrisBattle/ directory")
        sys.exit(1)
    
    print()
    print("Server Configuration:")
    server_url = os.environ.get("TETRIS_SERVER", "ws://localhost:8765")
    print(f"  Server URL: {server_url}")
    print(f"  (Set TETRIS_SERVER environment variable to change)")
    print()
    
    # Start game
    try:
        print("Starting Tetris Battle...")
        print()
        
        from tetris_game_online import TetrisGameOnline
        
        game = TetrisGameOnline()
        game.play()
    
    except KeyboardInterrupt:
        print()
        print("Game closed by user")
    except Exception as e:
        print(f"Error starting game: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()