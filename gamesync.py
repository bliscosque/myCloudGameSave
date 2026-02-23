#!/usr/bin/env python3
"""
Cloud Game Save Synchronization Tool
Main entry point for the CLI application
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_manager import ConfigManager, ConfigError
from src.logger import init_logger, get_logger


def create_parser():
    """Create and configure argument parser
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='gamesync',
        description='Synchronize game saves between local machine and cloud storage',
        epilog='For more information, see README.md'
    )
    
    # Global options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force operation without confirmation prompts'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # init command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize configuration for this machine'
    )
    
    # detect command
    detect_parser = subparsers.add_parser(
        'detect',
        help='Auto-detect non-Steam games from Steam library'
    )
    
    # list command
    list_parser = subparsers.add_parser(
        'list',
        help='List all configured games'
    )
    
    # sync command
    sync_parser = subparsers.add_parser(
        'sync',
        help='Synchronize game saves'
    )
    sync_parser.add_argument(
        'game_id',
        nargs='?',
        help='Game ID to sync (omit to sync all games)'
    )
    sync_parser.add_argument(
        '--all',
        action='store_true',
        help='Sync all configured games'
    )
    
    # status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show sync status for games'
    )
    status_parser.add_argument(
        'game_id',
        nargs='?',
        help='Game ID to check (omit for all games)'
    )
    
    # config command
    config_parser = subparsers.add_parser(
        'config',
        help='Manage configuration'
    )
    config_parser.add_argument(
        'action',
        choices=['show', 'edit', 'set'],
        help='Configuration action'
    )
    config_parser.add_argument(
        'key',
        nargs='?',
        help='Configuration key (for set action)'
    )
    config_parser.add_argument(
        'value',
        nargs='?',
        help='Configuration value (for set action)'
    )
    
    return parser


def cmd_init(args):
    """Initialize configuration"""
    config_mgr = ConfigManager()
    
    if config_mgr.config_exists():
        print(f"Configuration already exists at: {config_mgr.config_dir}")
        print(f"Hostname: {config_mgr.hostname}")
        return
    
    print("Initializing GameSync configuration...")
    print(f"Hostname: {config_mgr.hostname}")
    print(f"OS: {config_mgr.get_os_type()}")
    print(f"Config directory: {config_mgr.config_dir}")
    
    if config_mgr.initialize():
        print("\n✓ Configuration initialized successfully!")
        print(f"\nNext steps:")
        print(f"1. Edit {config_mgr.config_file}")
        print(f"2. Set your cloud_directory path")
        print(f"3. Run 'python gamesync.py detect' to find games")
    else:
        print("\n✗ Failed to initialize configuration")
        sys.exit(1)


def cmd_detect(args):
    """Detect non-Steam games from Steam library"""
    from src.game_detector import GameDetector
    
    config_mgr = ConfigManager()
    if not config_mgr.config_exists():
        print("✗ Configuration not initialized. Run 'gamesync init' first.")
        sys.exit(1)
    
    print("Detecting non-Steam games from Steam library...")
    detector = GameDetector(config_manager=config_mgr)
    games = detector.detect_non_steam_games()
    
    if not games:
        print("\n✗ No non-Steam games found in Steam library")
        return
    
    print(f"\n✓ Found {len(games)} non-Steam game(s):\n")
    
    for i, game in enumerate(games, 1):
        game_id = detector.create_game_id(game['name'])
        backup_dir = detector.create_backup_dir_name(game)
        
        print(f"{i}. {game['name']}")
        print(f"   ID: {game_id}")
        print(f"   Exe: {game['exe']}")
        if args.verbose:
            print(f"   Start Dir: {game.get('start_dir', 'N/A')}")
            print(f"   Backup Dir: {backup_dir}")
        print()
    
    # Prompt user to confirm
    if not args.force:
        response = input("Add all detected games to configuration? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Create game configs
    added = 0
    skipped = 0
    
    for game in games:
        save_locations = detector.detect_save_locations(game)
        success = detector.save_game_config(game, save_locations, overwrite=False)
        
        if success:
            print(f"✓ Added: {game['name']}")
            added += 1
        else:
            print(f"⊘ Skipped (already exists): {game['name']}")
            skipped += 1
    
    print(f"\n✓ Added {added} game(s), skipped {skipped}")
    if added > 0:
        print("\nNext steps:")
        print("1. Review game configs in config/<hostname>/games/")
        print("2. Verify save_locations are correct")
        print("3. Run 'gamesync sync --all' to synchronize")


def setup_logging(args):
    """Set up logging based on config and arguments
    
    Args:
        args: Command line arguments
        
    Returns:
        ConfigManager instance or None if config doesn't exist
    """
    try:
        config_mgr = ConfigManager()
        
        # Skip logging setup for init command if config doesn't exist
        if not config_mgr.config_exists():
            if args.command != 'init':
                print("Configuration not initialized. Run 'init' command first.")
                sys.exit(1)
            return None
        
        # Load config and initialize logger
        config = config_mgr.load_config()
        log_level = config.get("general", {}).get("log_level", "info")
        verbose = getattr(args, 'verbose', False)
        
        init_logger(config_mgr.logs_dir, log_level, verbose)
        
        return config_mgr
        
    except ConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Cloud Game Save Synchronization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show help if no command specified
    if args.command is None:
        parser.print_help()
        return
    
    # Set up logging (except for init if config doesn't exist)
    config_mgr = setup_logging(args)
    
    # Log command execution
    if config_mgr:
        logger = get_logger()
        logger.info(f"Executing command: {args.command} (verbose={args.verbose}, dry_run={args.dry_run}, force={args.force})")
    
    # Execute command
    if args.command == 'init':
        cmd_init(args)
    elif args.command == 'detect':
        cmd_detect(args)
    else:
        print(f"Command '{args.command}' not yet implemented")


if __name__ == "__main__":
    main()
