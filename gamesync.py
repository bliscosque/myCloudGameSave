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

from src.config_manager import ConfigManager


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


def main():
    parser = argparse.ArgumentParser(
        description="Cloud Game Save Synchronization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # init command
    parser_init = subparsers.add_parser('init', help='Initialize configuration')
    parser_init.set_defaults(func=cmd_init)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
