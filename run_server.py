#!/usr/bin/env python3
"""
Tetris Battle Server Launcher
Simple script to start the server with proper configuration
"""

import sys
import os

def main():
    print("=" * 60)
    print("TETRIS BATTLE - MULTIPLAYER SERVER")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Check dependencies
    try:
        import websockets
        print("✓ websockets installed")
    except ImportError:
        print("✗ websockets not installed")
        print("  Run: pip install websockets")
        sys.exit(1)
    
    try:
        import sqlite3
        print("✓ sqlite3 available")
    except ImportError:
        print("✗ sqlite3 not available")
        sys.exit(1)
    
    print()
    print("Configuration:")
    print(f"  Host: 0.0.0.0 (all interfaces)")
    print(f"  Port: 8765")
    print(f"  Database: tetris_battle.db")
    print()
    
    # Import and start server
    try:
        from server import TetrisBattleServer
        import asyncio
        
        print("Starting server...")
        print("Press Ctrl+C to stop")
        print()
        
        server = TetrisBattleServer()
        asyncio.run(server.start())
    
    except KeyboardInterrupt:
        print()
        print("Server stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()