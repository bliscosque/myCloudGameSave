"""
Configuration management module
Handles loading, saving, and initializing configuration files
"""

import os
import platform
import socket
from pathlib import Path
from typing import Dict, Any
import toml


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
        """
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        with open(self.config_file, 'r') as f:
            return toml.load(f)
    
    def save_config(self, config: Dict[str, Any]):
        """Save global configuration
        
        Args:
            config: Configuration dictionary to save
        """
        with open(self.config_file, 'w') as f:
            toml.dump(config, f)
    
    def config_exists(self) -> bool:
        """Check if configuration is initialized
        
        Returns:
            True if config directory and file exist
        """
        return self.config_dir.exists() and self.config_file.exists()
