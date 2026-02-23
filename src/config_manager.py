"""
Configuration management module
Handles loading, saving, and initializing configuration files
"""

import os
import platform
import socket
from pathlib import Path
from typing import Dict, Any, Optional
import toml


class ConfigError(Exception):
    """Configuration-related errors"""
    pass


class ConfigManager:
    """Manages configuration files and directories"""
    
    def __init__(self, project_root: Path = None):
        """Initialize configuration manager
        
        Args:
            project_root: Root directory of the project. Defaults to script location.
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.hostname = socket.gethostname()
        self.config_dir = self.project_root / "config" / self.hostname
        self.games_dir = self.config_dir / "games"
        self.backups_dir = self.config_dir / "backups"
        self.logs_dir = self.config_dir / "logs"
        self.config_file = self.config_dir / "config.toml"
    
    def get_os_type(self) -> str:
        """Detect operating system type
        
        Returns:
            "windows" or "linux"
        """
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        else:
            # Default to linux for other Unix-like systems
            return "linux"
    
    def initialize(self) -> bool:
        """Initialize configuration directory structure
        
        Creates all necessary directories and default config file if they don't exist.
        
        Returns:
            True if initialization was successful
        """
        try:
            # Create directory structure
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.games_dir.mkdir(exist_ok=True)
            self.backups_dir.mkdir(exist_ok=True)
            self.logs_dir.mkdir(exist_ok=True)
            
            # Create default config if it doesn't exist
            if not self.config_file.exists():
                self._create_default_config()
            
            return True
        except Exception as e:
            print(f"Error initializing configuration: {e}")
            return False
    
    def _create_default_config(self):
        """Create default global configuration file"""
        os_type = self.get_os_type()
        
        default_config = {
            "system": {
                "os": os_type,
                "hostname": self.hostname
            },
            "general": {
                "cloud_directory": "",
                "backup_directory": "backups",
                "log_level": "info"
            },
            "detection": {
                "steam_enabled": True,
                "custom_paths": []
            }
        }
        
        with open(self.config_file, 'w') as f:
            toml.dump(default_config, f)
    
    def load_config(self) -> Dict[str, Any]:
        """Load global configuration
        
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigError: If config file doesn't exist or is invalid
        """
        if not self.config_file.exists():
            raise ConfigError(
                f"Configuration file not found: {self.config_file}\n"
                f"Run 'init' command to create it."
            )
        
        try:
            with open(self.config_file, 'r') as f:
                config = toml.load(f)
        except toml.TomlDecodeError as e:
            raise ConfigError(f"Invalid TOML syntax in {self.config_file}: {e}")
        except Exception as e:
            raise ConfigError(f"Error reading config file: {e}")
        
        # Validate config
        self._validate_config(config)
        return config
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration structure
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigError: If configuration is invalid
        """
        # Check required sections
        required_sections = ["system", "general", "detection"]
        for section in required_sections:
            if section not in config:
                raise ConfigError(f"Missing required section: [{section}]")
        
        # Validate system section
        if "os" not in config["system"]:
            raise ConfigError("Missing 'os' in [system] section")
        if config["system"]["os"] not in ["linux", "windows"]:
            raise ConfigError(f"Invalid os value: {config['system']['os']} (must be 'linux' or 'windows')")
        
        # Validate general section
        if "cloud_directory" not in config["general"]:
            raise ConfigError("Missing 'cloud_directory' in [general] section")
        
        # Validate log_level if present
        if "log_level" in config["general"]:
            valid_levels = ["debug", "info", "warning", "error"]
            if config["general"]["log_level"] not in valid_levels:
                raise ConfigError(
                    f"Invalid log_level: {config['general']['log_level']} "
                    f"(must be one of: {', '.join(valid_levels)})"
                )
    
    def save_config(self, config: Dict[str, Any]):
        """Save global configuration
        
        Args:
            config: Configuration dictionary to save
            
        Raises:
            ConfigError: If config is invalid or cannot be saved
        """
        # Validate before saving
        self._validate_config(config)
        
        try:
            with open(self.config_file, 'w') as f:
                toml.dump(config, f)
        except Exception as e:
            raise ConfigError(f"Error saving config file: {e}")
    
    def load_game_config(self, game_id: str) -> Dict[str, Any]:
        """Load a specific game configuration
        
        Args:
            game_id: Game identifier
            
        Returns:
            Game configuration dictionary
            
        Raises:
            ConfigError: If game config doesn't exist or is invalid
        """
        game_file = self.games_dir / f"{game_id}.toml"
        
        if not game_file.exists():
            raise ConfigError(f"Game configuration not found: {game_id}")
        
        try:
            with open(game_file, 'r') as f:
                config = toml.load(f)
        except toml.TomlDecodeError as e:
            raise ConfigError(f"Invalid TOML syntax in {game_file}: {e}")
        except Exception as e:
            raise ConfigError(f"Error reading game config: {e}")
        
        # Validate game config
        self._validate_game_config(config, game_id)
        return config
    
    def _validate_game_config(self, config: Dict[str, Any], game_id: str):
        """Validate game configuration structure
        
        Args:
            config: Game configuration dictionary
            game_id: Game identifier for error messages
            
        Raises:
            ConfigError: If configuration is invalid
        """
        # Check required sections
        required_sections = ["game", "paths", "sync"]
        for section in required_sections:
            if section not in config:
                raise ConfigError(f"Game '{game_id}': Missing required section [{section}]")
        
        # Validate game section
        if "id" not in config["game"]:
            raise ConfigError(f"Game '{game_id}': Missing 'id' in [game] section")
        if "name" not in config["game"]:
            raise ConfigError(f"Game '{game_id}': Missing 'name' in [game] section")
        
        # Validate paths section
        if "local" not in config["paths"]:
            raise ConfigError(f"Game '{game_id}': Missing 'local' in [paths] section")
        if "cloud" not in config["paths"]:
            raise ConfigError(f"Game '{game_id}': Missing 'cloud' in [paths] section")
        
        # Validate sync section
        if "enabled" not in config["sync"]:
            raise ConfigError(f"Game '{game_id}': Missing 'enabled' in [sync] section")
    
    def save_game_config(self, game_id: str, config: Dict[str, Any]):
        """Save a game configuration
        
        Args:
            game_id: Game identifier
            config: Game configuration dictionary
            
        Raises:
            ConfigError: If config is invalid or cannot be saved
        """
        # Validate before saving
        self._validate_game_config(config, game_id)
        
        game_file = self.games_dir / f"{game_id}.toml"
        
        try:
            with open(game_file, 'w') as f:
                toml.dump(config, f)
        except Exception as e:
            raise ConfigError(f"Error saving game config: {e}")
    
    def list_games(self) -> list[str]:
        """List all configured game IDs
        
        Returns:
            List of game IDs
        """
        if not self.games_dir.exists():
            return []
        
        games = []
        for file in self.games_dir.glob("*.toml"):
            games.append(file.stem)
        
        return sorted(games)
    
    def config_exists(self) -> bool:
        """Check if configuration is initialized
        
        Returns:
            True if config directory and file exist
        """
        return self.config_dir.exists() and self.config_file.exists()
