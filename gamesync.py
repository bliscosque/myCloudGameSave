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
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # init command
    parser_init = subparsers.add_parser('init', help='Initialize configuration')
    parser_init.set_defaults(func=cmd_init)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Set up logging (except for init if config doesn't exist)
    config_mgr = setup_logging(args)
    
    # Log command execution
    if config_mgr:
        logger = get_logger()
        logger.info(f"Executing command: {args.command}")
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
