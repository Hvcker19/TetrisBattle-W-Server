#!/usr/bin/env python3
"""
Test script for Tetris Battle Online
Verifies that all components are working correctly
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        import pygame
        print("  ✓ pygame")
    except ImportError as e:
        print(f"  ✗ pygame: {e}")
        return False
    
    try:
        import websockets
        print("  ✓ websockets")
    except ImportError as e:
        print(f"  ✗ websockets: {e}")
        return False
    
    try:
        from network_client import NetworkClient, get_network_client
        print("  ✓ network_client")
    except ImportError as e:
        print(f"  ✗ network_client: {e}")
        return False
    
    try:
        from auth_ui import AuthUI
        print("  ✓ auth_ui")
    except ImportError as e:
        print(f"  ✗ auth_ui: {e}")
        return False
    
    try:
        from matchmaking_ui import MatchmakingUI
        print("  ✓ matchmaking_ui")
    except ImportError as e:
        print(f"  ✗ matchmaking_ui: {e}")
        return False
    
    try:
        from tetris_game_online import TetrisGameOnline
        print("  ✓ tetris_game_online")
    except ImportError as e:
        print(f"  ✗ tetris_game_online: {e}")
        return False
    
    return True


def test_tetris_battle_package():
    """Test that TetrisBattle package is available"""
    print("\nTesting TetrisBattle package...")
    
    try:
        from TetrisBattle.tetris_game import TetrisGame, TetrisGameDouble
        print("  ✓ TetrisBattle.tetris_game")
    except ImportError as e:
        print(f"  ✗ TetrisBattle.tetris_game: {e}")
        print("  → Make sure TetrisBattle/ directory exists with all game files")
        return False
    
    try:
        from TetrisBattle.tetris import Tetris, Player
        print("  ✓ TetrisBattle.tetris")
    except ImportError as e:
        print(f"  ✗ TetrisBattle.tetris: {e}")
        return False
    
    try:
        from TetrisBattle.settings import FPS, MAX_TIME
        print("  ✓ TetrisBattle.settings")
    except ImportError as e:
        print(f"  ✗ TetrisBattle.settings: {e}")
        return False
    
    return True


def test_game_initialization():
    """Test that game can be initialized"""
    print("\nTesting game initialization...")
    
    try:
        import pygame
        pygame.init()
        
        from tetris_game_online import TetrisGameOnline
        
        game = TetrisGameOnline()
        print("  ✓ Game object created")
        
        # Check required attributes
        required_attrs = ['width', 'height', 'screen', 'network', 
                         'renderer', 'myClock', 'current_screen']
        
        missing = []
        for attr in required_attrs:
            if not hasattr(game, attr):
                missing.append(attr)
        
        if missing:
            print(f"  ✗ Missing attributes: {', '.join(missing)}")
            return False
        
        print(f"  ✓ All required attributes present")
        print(f"  ✓ Screen size: {game.width}x{game.height}")
        print(f"  ✓ Current screen: {game.current_screen}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_network_client():
    """Test network client initialization"""
    print("\nTesting network client...")
    
    try:
        from network_client import get_network_client
        
        client = get_network_client("ws://localhost:8765")
        print("  ✓ Network client created")
        
        # Check attributes
        if hasattr(client, 'server_url'):
            print(f"  ✓ Server URL: {client.server_url}")
        
        if hasattr(client, 'callbacks'):
            print(f"  ✓ Callbacks dict: {len(client.callbacks)} registered")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("TETRIS BATTLE - COMPONENT TEST")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Import Test", test_imports()))
    results.append(("TetrisBattle Package", test_tetris_battle_package()))
    results.append(("Game Initialization", test_game_initialization()))
    results.append(("Network Client", test_network_client()))
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("✅ All tests passed! Game is ready to run.")
        print()
        print("Next steps:")
        print("  1. Start server: python3 run_server.py")
        print("  2. Start client: python3 run_client.py")
        return 0
    else:
        print()
        print("❌ Some tests failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  - Install dependencies: pip3 install pygame websockets")
        print("  - Ensure TetrisBattle/ directory exists")
        print("  - Check Python version: python3 --version (need 3.7+)")
        return 1


if __name__ == "__main__":
    sys.exit(main())