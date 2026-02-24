#!/usr/bin/env python3
"""
Test script for game detection
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game_detector import GameDetector


def test_steam_detection():
    """Test Steam installation detection"""
    print("Test 1: Detecting Steam installation...")
    
    detector = GameDetector()
    steam_path = detector.detect_steam_path()
    
    if steam_path:
        print(f"✓ Steam found at: {steam_path}")
        return True
    else:
        print("✗ Steam not found")
        return False


def test_userdata_detection():
    """Test userdata directory detection"""
    print("\nTest 2: Detecting userdata directory...")
    
    detector = GameDetector()
    userdata_path = detector.detect_userdata_path()
    
    if userdata_path:
        print(f"✓ Userdata found at: {userdata_path}")
        return True
    else:
        print("✗ Userdata not found")
        return False


def test_user_ids():
    """Test Steam user ID detection"""
    print("\nTest 3: Detecting Steam user IDs...")
    
    detector = GameDetector()
    user_ids = detector.detect_user_ids()
    
    if user_ids:
        print(f"✓ Found {len(user_ids)} user(s): {', '.join(user_ids)}")
        return True
    else:
        print("✗ No users found")
        return False


def test_shortcuts_path():
    """Test shortcuts.vdf path detection"""
    print("\nTest 4: Detecting shortcuts.vdf files...")
    
    detector = GameDetector()
    detector.detect_user_ids()
    
    found_any = False
    for user_id in detector.user_ids:
        shortcuts = detector.get_shortcuts_path(user_id)
        if shortcuts:
            print(f"✓ User {user_id}: {shortcuts}")
            print(f"  Exists: {shortcuts.exists()}")
            found_any = True
        else:
            print(f"  User {user_id}: No shortcuts.vdf")
    
    if not found_any and detector.user_ids:
        print("  (No shortcuts.vdf files found - this is normal if no non-Steam games added)")
        return True
    
    return found_any or len(detector.user_ids) == 0


def test_non_steam_games():
    """Test non-Steam game detection"""
    print("\nTest 5: Detecting non-Steam games...")
    
    detector = GameDetector()
    games = detector.detect_non_steam_games()
    
    if games:
        print(f"✓ Found {len(games)} non-Steam game(s):")
        for i, game in enumerate(games, 1):
            print(f"  {i}. {game['name']}")
            print(f"     Exe: {game['exe']}")
            print(f"     Start Dir: {game['start_dir']}")
            print(f"     App ID: {game['app_id']}")
            print(f"     User ID: {game['user_id']}")
        return True
    else:
        print("  No non-Steam games found (this is normal if none added)")
        return True


def test_save_locations():
    """Test save location detection"""
    print("\nTest 6: Detecting save locations...")
    
    detector = GameDetector()
    games = detector.detect_non_steam_games()
    
    if not games:
        print("  No games to test (skipping)")
        return True
    
    # Test first game
    game = games[0]
    print(f"  Testing: {game['name']}")
    
    save_locations = detector.detect_save_locations(game)
    
    if save_locations:
        print(f"  ✓ Found {len(save_locations)} potential save location(s):")
        for loc in save_locations:
            print(f"    - {loc}")
            print(f"      Exists: {loc.exists()}")
        return True
    else:
        print("  No save locations detected (may need manual configuration)")
        return True


def test_detect_all():
    """Test complete detection"""
    print("\nTest 7: Running complete detection...")
    
    detector = GameDetector()
    results = detector.detect_all()
    
    print(f"  OS Type: {detector.os_type}")
    print(f"  Steam Path: {results['steam_path']}")
    print(f"  Userdata Path: {results['userdata_path']}")
    print(f"  User IDs: {results['user_ids']}")
    print(f"  Shortcuts Files: {len(results['shortcuts_files'])}")
    print(f"  Non-Steam Games: {len(results['non_steam_games'])}")
    print(f"  Custom Games: {len(results['custom_games'])}")
    
    for shortcut in results['shortcuts_files']:
        print(f"    - User {shortcut['user_id']}: {shortcut['path']}")
    
    # Show save locations for first game
    if results['non_steam_games']:
        game = results['non_steam_games'][0]
        save_locs = game.get('potential_save_locations', [])
        print(f"  Save locations for '{game['name']}': {len(save_locs)}")
    
    if results['steam_path']:
        print("✓ Detection complete")
        return True
    else:
        print("✗ Steam not detected")
        return False


def test_custom_directories():
    """Test custom directory scanning"""
    print("\nTest 8: Testing custom directory scanning...")
    
    # Test with a non-existent path (should handle gracefully)
    detector = GameDetector(custom_paths=["/nonexistent/path"])
    custom_games = detector.scan_custom_directories()
    
    print(f"  Found {len(custom_games)} games in custom directories")
    if custom_games:
        for game in custom_games:
            print(f"    - {game['name']}: {game['exe']}")
    
    print("✓ Custom directory scanning works")
    return True


def test_game_config_creation():
    """Test game configuration creation and saving"""
    print("\nTest 9: Testing game configuration creation...")
    
    from src.config_manager import ConfigManager
    
    config_mgr = ConfigManager()
    detector = GameDetector(config_manager=config_mgr)
    
    games = detector.detect_non_steam_games()
    if not games:
        print("  No games to test (skipping)")
        return True
    
    game = games[0]
    print(f"  Testing with: {game['name']}")
    
    # Create game ID
    game_id = detector.create_game_id(game)
    print(f"  Game ID: {game_id}")
    
    # Detect save locations
    save_locs = detector.detect_save_locations(game)
    
    # Create config
    config = detector.create_game_config(game, save_locs)
    print(f"  Config created: {config['game']['name']}")
    print(f"  Local path: {config['paths']['local'][:50]}...")
    
    # Save config (with overwrite to ensure test works)
    success = detector.save_game_config(game, save_locs, overwrite=True)
    if success:
        print(f"  ✓ Config saved to games/{game_id}.toml")
        
        # Verify it can be loaded
        loaded = config_mgr.load_game_config(game_id)
        if loaded['game']['name'] == game['name']:
            print("  ✓ Config verified")
            
            # Test that it skips existing configs by default
            skipped = not detector.save_game_config(game, save_locs, overwrite=False)
            if skipped:
                print("  ✓ Existing configs protected (not overwritten)")
            
            return True
    
    print("  ✗ Failed to save/verify config")
    return False

def main():
    print("=== Game Detection Tests ===\n")
    
    tests = [
        test_steam_detection,
        test_userdata_detection,
        test_user_ids,
        test_shortcuts_path,
        test_non_steam_games,
        test_save_locations,
        test_detect_all,
        test_custom_directories,
        test_game_config_creation
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print(f"\n=== Results: {sum(results)}/{len(results)} tests passed ===")
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
