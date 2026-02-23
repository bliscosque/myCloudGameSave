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
    
    # add command
    add_parser = subparsers.add_parser(
        'add',
        help='Manually add a game configuration'
    )
    add_parser.add_argument(
        'game_id',
        nargs='?',
        help='Game ID (optional, will prompt if not provided)'
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
    
    # Show debug info if verbose
    if args.verbose:
        print("\n[Debug Info]")
        steam_path = detector.detect_steam_path()
        print(f"Steam path: {steam_path}")
        print(f"Steam exists: {steam_path.exists() if steam_path else False}")
        
        if steam_path:
            userdata = steam_path / "userdata"
            print(f"Userdata path: {userdata}")
            print(f"Userdata exists: {userdata.exists()}")
            
            user_ids = detector.detect_user_ids()
            print(f"User IDs found: {user_ids}")
            
            for uid in user_ids:
                shortcuts_path = detector.get_shortcuts_path(uid)
                print(f"\nUser {uid}:")
                print(f"  Shortcuts path: {shortcuts_path}")
                print(f"  Shortcuts exists: {shortcuts_path.exists() if shortcuts_path else False}")
                
                if shortcuts_path and shortcuts_path.exists():
                    try:
                        from src.vdf_parser import ShortcutsParser
                        parser = ShortcutsParser(shortcuts_path)
                        vdf_games = parser.parse()
                        print(f"  Games in shortcuts.vdf: {len(vdf_games)}")
                        for g in vdf_games:
                            print(f"    - {g.get('name', 'Unknown')}")
                    except Exception as e:
                        print(f"  Error parsing shortcuts.vdf: {e}")
        print()
    
    games = detector.detect_non_steam_games()
    
    if not games:
        print("\n✗ No non-Steam games found in Steam library")
        return
    
    print(f"\n✓ Found {len(games)} non-Steam game(s):\n")
    
    for i, game in enumerate(games, 1):
        game_id = detector.create_game_id(game)
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


def cmd_list(args):
    """List all configured games"""
    config_mgr = ConfigManager()
    if not config_mgr.config_exists():
        print("✗ Configuration not initialized. Run 'gamesync init' first.")
        sys.exit(1)
    
    games = config_mgr.list_games()
    
    if not games:
        print("No games configured.")
        print("\nRun 'gamesync detect' to find games automatically.")
        return
    
    print(f"Configured games ({len(games)}):\n")
    
    for game_id in sorted(games):
        try:
            config = config_mgr.load_game_config(game_id)
            name = config.get('game', {}).get('name', game_id)
            enabled = config.get('sync', {}).get('enabled', True)
            last_sync = config.get('sync', {}).get('last_sync', '')
            
            status = "✓" if enabled else "⊘"
            print(f"{status} {name}")
            print(f"  ID: {game_id}")
            
            if last_sync:
                print(f"  Last sync: {last_sync}")
            else:
                print(f"  Last sync: Never")
            
            if args.verbose:
                local_path = config.get('paths', {}).get('local', '')
                backup_dir = config.get('game', {}).get('backup_dir_name', '')
                print(f"  Local: {local_path}")
                print(f"  Cloud: {backup_dir}")
            
            print()
            
        except Exception as e:
            print(f"✗ {game_id}: Error loading config - {e}\n")


def cmd_add(args):
    """Manually add a game configuration"""
    from src.game_detector import GameDetector
    
    config_mgr = ConfigManager()
    if not config_mgr.config_exists():
        print("✗ Configuration not initialized. Run 'gamesync init' first.")
        sys.exit(1)
    
    # Get game ID
    if args.game_id:
        game_id = args.game_id
    else:
        game_id = input("Game ID (lowercase, use hyphens): ").strip()
    
    if not game_id:
        print("✗ Game ID is required")
        sys.exit(1)
    
    # Check if already exists
    existing_games = config_mgr.list_games()
    if game_id in existing_games and not args.force:
        print(f"✗ Game '{game_id}' already exists. Use --force to overwrite.")
        sys.exit(1)
    
    # Get game details
    name = input("Game name: ").strip()
    if not name:
        print("✗ Game name is required")
        sys.exit(1)
    
    local_path = input("Local save path: ").strip()
    if not local_path:
        print("✗ Local path is required")
        sys.exit(1)
    
    # Validate local path
    local_path_obj = Path(local_path).expanduser()
    if not local_path_obj.exists():
        print(f"⚠ Warning: Local path does not exist: {local_path_obj}")
        if not args.force:
            response = input("Continue anyway? [y/N]: ")
            if response.lower() != 'y':
                print("Cancelled.")
                sys.exit(1)
    
    backup_dir_name = input("Backup directory name (for cloud): ").strip()
    if not backup_dir_name:
        print("✗ Backup directory name is required")
        sys.exit(1)
    
    # Create config
    from datetime import datetime
    config = {
        "game": {
            "id": game_id,
            "name": name,
            "platform": "manual",
            "backup_dir_name": backup_dir_name
        },
        "paths": {
            "local": str(local_path_obj),
            "cloud": backup_dir_name
        },
        "sync": {
            "enabled": True,
            "exclude_patterns": ["*.tmp", "*.log"],
            "last_sync": ""
        },
        "metadata": {
            "auto_detected": False,
            "last_modified": datetime.now().isoformat()
        }
    }
    
    # Save config
    try:
        config_mgr.save_game_config(game_id, config)
        print(f"\n✓ Game '{name}' added successfully!")
        print(f"  Config: config/{config_mgr.hostname}/games/{game_id}.toml")
    except Exception as e:
        print(f"\n✗ Failed to save config: {e}")
        sys.exit(1)


def cmd_sync(args):
    """Synchronize game saves"""
    from src.sync_engine import SyncEngine
    from src.conflict_resolver import ConflictResolver, ResolutionStrategy
    from datetime import datetime
    
    config_mgr = ConfigManager()
    if not config_mgr.config_exists():
        print("✗ Configuration not initialized. Run 'gamesync init' first.")
        sys.exit(1)
    
    # Load global config
    global_config = config_mgr.load_config()
    cloud_directory = global_config.get('general', {}).get('cloud_directory')
    
    if not cloud_directory:
        print("✗ Cloud directory not configured. Edit config and set 'cloud_directory'.")
        sys.exit(1)
    
    cloud_dir = Path(cloud_directory)
    if not cloud_dir.exists():
        print(f"✗ Cloud directory does not exist: {cloud_dir}")
        sys.exit(1)
    
    # Determine which games to sync
    if args.all:
        game_ids = config_mgr.list_games()
        if not game_ids:
            print("No games configured.")
            sys.exit(1)
    elif args.game_id:
        game_ids = [args.game_id]
    else:
        print("✗ Specify a game ID or use --all to sync all games")
        sys.exit(1)
    
    # Sync each game
    sync_engine = SyncEngine()
    total_synced = 0
    total_conflicts = 0
    total_errors = 0
    
    for game_id in game_ids:
        try:
            game_config = config_mgr.load_game_config(game_id)
        except Exception as e:
            print(f"✗ {game_id}: Failed to load config - {e}")
            total_errors += 1
            continue
        
        name = game_config.get('game', {}).get('name', game_id)
        enabled = game_config.get('sync', {}).get('enabled', True)
        
        if not enabled:
            print(f"⊘ {name}: Sync disabled, skipping")
            continue
        
        print(f"\n{'='*60}")
        print(f"Syncing: {name}")
        print(f"{'='*60}")
        
        # Get paths
        local_path = Path(game_config.get('paths', {}).get('local', ''))
        backup_dir_name = game_config.get('game', {}).get('backup_dir_name', '')
        game_cloud_dir = cloud_dir / backup_dir_name
        backup_path = config_mgr.config_dir / "backups" / game_id
        
        if not local_path.exists():
            print(f"✗ Local path does not exist: {local_path}")
            total_errors += 1
            continue
        
        # Create cloud directory if needed
        game_cloud_dir.mkdir(parents=True, exist_ok=True)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Get last sync time
        last_sync = game_config.get('sync', {}).get('last_sync', '')
        
        # Check for conflicts first (unless --force)
        conflict_resolver = ConflictResolver()
        if not args.force:
            comparisons = sync_engine.compare_directories(
                local_path,
                game_cloud_dir,
                last_sync if last_sync else None
            )
            
            conflicts = [c for c in comparisons if c.action.value == 'conflict']
            
            if conflicts and not args.dry_run:
                print(f"\n⚠ Found {len(conflicts)} conflict(s):")
                for conflict in conflicts:
                    print(f"  - {conflict.filename}")
                
                print("\nResolving conflicts...")
                for conflict in conflicts:
                    info = conflict_resolver.get_conflict_info(conflict.local_path, conflict.cloud_path)
                    
                    print(f"\n{'='*60}")
                    print(f"Conflict: {info['filename']}")
                    print(f"{'='*60}")
                    print(f"Local:  {info['local']['size']} bytes, modified {info['local']['modified']}")
                    print(f"Cloud:  {info['cloud']['size']} bytes, modified {info['cloud']['modified']}")
                    print("\nChoose resolution:")
                    print("  1. Keep local (copy local → cloud)")
                    print("  2. Keep cloud (copy cloud → local)")
                    print("  3. Keep both (rename with suffixes)")
                    print("  4. Skip this file")
                    
                    while True:
                        choice = input("\nYour choice [1-4]: ").strip()
                        if choice in ['1', '2', '3', '4']:
                            break
                        print("Invalid choice. Please enter 1, 2, 3, or 4.")
                    
                    if choice == '1':
                        conflict_resolver.resolve_conflict(
                            conflict.local_path,
                            conflict.cloud_path,
                            ResolutionStrategy.KEEP_LOCAL,
                            backup_path
                        )
                        print(f"✓ Resolved: Kept local version")
                    elif choice == '2':
                        conflict_resolver.resolve_conflict(
                            conflict.local_path,
                            conflict.cloud_path,
                            ResolutionStrategy.KEEP_CLOUD,
                            backup_path
                        )
                        print(f"✓ Resolved: Kept cloud version")
                    elif choice == '3':
                        conflict_resolver.resolve_conflict(
                            conflict.local_path,
                            conflict.cloud_path,
                            ResolutionStrategy.KEEP_BOTH,
                            backup_path
                        )
                        print(f"✓ Resolved: Kept both versions")
                    else:
                        print(f"⊘ Skipped: {conflict.filename}")
                
                print(f"\n{'='*60}")
                print("All conflicts resolved. Continuing with sync...")
                print(f"{'='*60}\n")
        
        # Perform sync
        results = sync_engine.sync_files(
            local_path, 
            game_cloud_dir, 
            backup_path,
            last_sync=last_sync if last_sync else None,
            dry_run=args.dry_run
        )
        
        # Display results
        if args.dry_run:
            print("\n[DRY RUN - No changes made]")
        
        for action in results['actions']:
            filename = action['filename']
            direction = action.get('direction', 'unknown')
            
            if action['action'] == 'conflict':
                print(f"⚠ {filename}: CONFLICT")
                total_conflicts += 1
            elif action['action'] == 'skip':
                if args.verbose:
                    print(f"  {filename}: Up to date")
            elif action.get('success'):
                size = action.get('size', 0)
                print(f"✓ {filename}: {direction} ({size} bytes)")
                total_synced += 1
            else:
                error = action.get('error', 'Unknown error')
                print(f"✗ {filename}: {error}")
                total_errors += 1
        
        # Update last sync time if not dry run and successful
        if not args.dry_run and results['success'] and results['conflicts'] == 0:
            game_config['sync']['last_sync'] = datetime.now().isoformat()
            game_config['metadata']['last_modified'] = datetime.now().isoformat()
            try:
                config_mgr.save_game_config(game_id, game_config)
            except Exception as e:
                print(f"⚠ Warning: Failed to update last_sync: {e}")
        
        print(f"\nSummary: {results['files_synced']} synced, {results['files_skipped']} skipped, {results['conflicts']} conflicts")
    
    # Overall summary
    print(f"\n{'='*60}")
    print(f"Overall: {total_synced} files synced, {total_conflicts} conflicts, {total_errors} errors")
    print(f"{'='*60}")
    
    if total_conflicts > 0:
        print("\n⚠ Conflicts detected. Run 'gamesync status' to review.")


def cmd_status(args):
    """Show sync status for games"""
    from src.sync_engine import SyncEngine
    
    config_mgr = ConfigManager()
    if not config_mgr.config_exists():
        print("✗ Configuration not initialized. Run 'gamesync init' first.")
        sys.exit(1)
    
    # Load global config
    global_config = config_mgr.load_config()
    cloud_directory = global_config.get('general', {}).get('cloud_directory')
    
    if not cloud_directory:
        print("✗ Cloud directory not configured.")
        sys.exit(1)
    
    cloud_dir = Path(cloud_directory)
    
    # Determine which games to check
    if args.game_id:
        game_ids = [args.game_id]
    else:
        game_ids = config_mgr.list_games()
    
    if not game_ids:
        print("No games configured.")
        return
    
    sync_engine = SyncEngine()
    
    for game_id in game_ids:
        try:
            game_config = config_mgr.load_game_config(game_id)
        except Exception as e:
            print(f"✗ {game_id}: Failed to load config - {e}\n")
            continue
        
        name = game_config.get('game', {}).get('name', game_id)
        enabled = game_config.get('sync', {}).get('enabled', True)
        last_sync = game_config.get('sync', {}).get('last_sync', '')
        
        print(f"\n{'='*60}")
        print(f"{name} ({game_id})")
        print(f"{'='*60}")
        print(f"Status: {'Enabled' if enabled else 'Disabled'}")
        print(f"Last sync: {last_sync if last_sync else 'Never'}")
        
        if not enabled:
            continue
        
        # Get paths
        local_path = Path(game_config.get('paths', {}).get('local', ''))
        backup_dir_name = game_config.get('game', {}).get('backup_dir_name', '')
        game_cloud_dir = cloud_dir / backup_dir_name
        
        if not local_path.exists():
            print(f"✗ Local path does not exist: {local_path}")
            continue
        
        if not game_cloud_dir.exists():
            print(f"⚠ Cloud directory does not exist (will be created on sync)")
            continue
        
        # Compare directories
        comparisons = sync_engine.compare_directories(
            local_path,
            game_cloud_dir,
            last_sync if last_sync else None
        )
        
        # Count actions
        to_cloud = sum(1 for c in comparisons if c.action.value == 'copy_to_cloud')
        to_local = sum(1 for c in comparisons if c.action.value == 'copy_to_local')
        conflicts = sum(1 for c in comparisons if c.action.value == 'conflict')
        up_to_date = sum(1 for c in comparisons if c.action.value == 'skip')
        
        print(f"\nFiles to sync:")
        print(f"  → Cloud: {to_cloud}")
        print(f"  ← Local: {to_local}")
        print(f"  ⚠ Conflicts: {conflicts}")
        print(f"  ✓ Up to date: {up_to_date}")
        
        # Show details if verbose or if there are conflicts
        if args.verbose or conflicts > 0:
            print(f"\nDetails:")
            for comp in comparisons:
                if comp.action.value == 'skip' and not args.verbose:
                    continue
                
                if comp.action.value == 'copy_to_cloud':
                    print(f"  → {comp.filename} (local → cloud)")
                elif comp.action.value == 'copy_to_local':
                    print(f"  ← {comp.filename} (cloud → local)")
                elif comp.action.value == 'conflict':
                    print(f"  ⚠ {comp.filename} (CONFLICT)")
                elif args.verbose:
                    print(f"  ✓ {comp.filename} (up to date)")


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
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'add':
        cmd_add(args)
    elif args.command == 'sync':
        cmd_sync(args)
    elif args.command == 'status':
        cmd_status(args)
    else:
        print(f"Command '{args.command}' not yet implemented")


if __name__ == "__main__":
    main()
