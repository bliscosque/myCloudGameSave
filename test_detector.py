#!/usr/bin/env python3
"""
Test script for game detection
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

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


def test_detect_all():
    """Test complete detection"""
    print("\nTest 6: Running complete detection...")
    
    detector = GameDetector()
    results = detector.detect_all()
    
    print(f"  OS Type: {detector.os_type}")
    print(f"  Steam Path: {results['steam_path']}")
    print(f"  Userdata Path: {results['userdata_path']}")
    print(f"  User IDs: {results['user_ids']}")
    print(f"  Shortcuts Files: {len(results['shortcuts_files'])}")
    print(f"  Non-Steam Games: {len(results['non_steam_games'])}")
    
    for shortcut in results['shortcuts_files']:
        print(f"    - User {shortcut['user_id']}: {shortcut['path']}")
    
    if results['steam_path']:
        print("✓ Detection complete")
        return True
    else:
        print("✗ Steam not detected")
        return False


def main():
    print("=== Game Detection Tests ===\n")
    
    tests = [
        test_steam_detection,
        test_userdata_detection,
        test_user_ids,
        test_shortcuts_path,
        test_non_steam_games,
        test_detect_all
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
