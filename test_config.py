#!/usr/bin/env python3
"""
Test script for configuration validation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config_manager import ConfigManager, ConfigError


def test_load_valid_config():
    """Test loading valid configuration"""
    print("Test 1: Loading valid configuration...")
    try:
        config_mgr = ConfigManager()
        config = config_mgr.load_config()
        print(f"✓ Config loaded successfully")
        print(f"  OS: {config['system']['os']}")
        print(f"  Hostname: {config['system']['hostname']}")
        print(f"  Cloud directory: {config['general']['cloud_directory']}")
        return True
    except ConfigError as e:
        print(f"✗ Error: {e}")
        return False


def test_invalid_toml():
    """Test handling of invalid TOML syntax"""
    print("\nTest 2: Testing invalid TOML handling...")
    config_mgr = ConfigManager()
    
    # Create a temporary invalid config
    backup_file = config_mgr.config_file.with_suffix('.toml.backup')
    config_mgr.config_file.rename(backup_file)
    
    try:
        with open(config_mgr.config_file, 'w') as f:
            f.write("[invalid\nthis is not valid toml")
        
        try:
            config_mgr.load_config()
            print("✗ Should have raised ConfigError")
            return False
        except ConfigError as e:
            print(f"✓ Correctly caught invalid TOML: {str(e)[:50]}...")
            return True
    finally:
        # Restore original config
        config_mgr.config_file.unlink(missing_ok=True)
        backup_file.rename(config_mgr.config_file)


def test_missing_section():
    """Test validation of missing required section"""
    print("\nTest 3: Testing missing section validation...")
    config_mgr = ConfigManager()
    
    invalid_config = {
        "system": {"os": "linux", "hostname": "test"},
        "general": {"cloud_directory": ""}
        # Missing "detection" section
    }
    
    try:
        config_mgr.save_config(invalid_config)
        print("✗ Should have raised ConfigError")
        return False
    except ConfigError as e:
        print(f"✓ Correctly caught missing section: {e}")
        return True


def test_invalid_os():
    """Test validation of invalid OS value"""
    print("\nTest 4: Testing invalid OS value...")
    config_mgr = ConfigManager()
    
    invalid_config = {
        "system": {"os": "macos", "hostname": "test"},
        "general": {"cloud_directory": ""},
        "detection": {"steam_enabled": True, "custom_paths": []}
    }
    
    try:
        config_mgr.save_config(invalid_config)
        print("✗ Should have raised ConfigError")
        return False
    except ConfigError as e:
        print(f"✓ Correctly caught invalid OS: {e}")
        return True


def test_game_config():
    """Test game configuration validation"""
    print("\nTest 5: Testing game configuration...")
    config_mgr = ConfigManager()
    
    # Valid game config
    valid_game = {
        "game": {
            "id": "test-game",
            "name": "Test Game"
        },
        "paths": {
            "local": "/path/to/saves",
            "cloud": "test-game"
        },
        "sync": {
            "enabled": True
        }
    }
    
    try:
        config_mgr.save_game_config("test-game", valid_game)
        loaded = config_mgr.load_game_config("test-game")
        print(f"✓ Game config saved and loaded successfully")
        print(f"  Game: {loaded['game']['name']}")
        
        # Clean up
        (config_mgr.games_dir / "test-game.toml").unlink()
        return True
    except ConfigError as e:
        print(f"✗ Error: {e}")
        return False


def test_invalid_game_config():
    """Test invalid game configuration"""
    print("\nTest 6: Testing invalid game configuration...")
    config_mgr = ConfigManager()
    
    # Missing required fields
    invalid_game = {
        "game": {
            "id": "test-game"
            # Missing "name"
        },
        "paths": {
            "local": "/path/to/saves",
            "cloud": "test-game"
        },
        "sync": {
            "enabled": True
        }
    }
    
    try:
        config_mgr.save_game_config("test-game", invalid_game)
        print("✗ Should have raised ConfigError")
        return False
    except ConfigError as e:
        print(f"✓ Correctly caught invalid game config: {e}")
        return True


def test_list_games():
    """Test listing games"""
    print("\nTest 7: Testing game listing...")
    config_mgr = ConfigManager()
    
    games = config_mgr.list_games()
    print(f"✓ Found {len(games)} configured games")
    if games:
        print(f"  Games: {', '.join(games)}")
    return True


def main():
    print("=== Configuration Parser Tests ===\n")
    
    tests = [
        test_load_valid_config,
        test_invalid_toml,
        test_missing_section,
        test_invalid_os,
        test_game_config,
        test_invalid_game_config,
        test_list_games
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
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
