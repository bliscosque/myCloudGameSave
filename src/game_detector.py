"""
Game detection module
Handles detection of Steam installation and non-Steam games
"""

import os
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .vdf_parser import ShortcutsParser
from .save_detector import SaveLocationDetector
from .config_manager import ConfigManager


class GameDetector:
    """Detects Steam installation and non-Steam games"""
    
    def __init__(self, os_type: str = None, custom_paths: List[str] = None, config_manager: ConfigManager = None):
        """Initialize game detector
        
        Args:
            os_type: Operating system type ("linux" or "windows"). Auto-detected if None.
            custom_paths: List of custom game directory paths to scan
            config_manager: ConfigManager instance for saving game configs
        """
        if os_type is None:
            system = platform.system().lower()
            os_type = "windows" if system == "windows" else "linux"
        
        self.os_type = os_type
        self.steam_path: Optional[Path] = None
        self.userdata_path: Optional[Path] = None
        self.user_ids: List[str] = []
        self.save_detector = SaveLocationDetector(os_type)
        self.custom_paths = [Path(p) for p in (custom_paths or [])]
        self.config_manager = config_manager
    
    def detect_steam_path(self) -> Optional[Path]:
        """Detect Steam installation path
        
        Returns:
            Path to Steam installation or None if not found
        """
        if self.os_type == "linux":
            return self._detect_steam_linux()
        else:
            return self._detect_steam_windows()
    
    def _detect_steam_linux(self) -> Optional[Path]:
        """Detect Steam installation on Linux
        
        Returns:
            Path to Steam installation or None if not found
        """
        # Common Steam paths on Linux
        possible_paths = [
            Path.home() / ".local" / "share" / "Steam",
            Path.home() / ".steam" / "steam",
            Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",  # Flatpak
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                # Verify it's a valid Steam installation
                if (path / "steam.sh").exists() or (path / "userdata").exists():
                    self.steam_path = path
                    return path
        
        return None
    
    def _detect_steam_windows(self) -> Optional[Path]:
        """Detect Steam installation on Windows
        
        Returns:
            Path to Steam installation or None if not found
        """
        # Common Steam paths on Windows
        possible_paths = [
            Path("C:/Program Files (x86)/Steam"),
            Path("C:/Program Files/Steam"),
        ]
        
        # Check registry-based paths (if available)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\WOW6432Node\Valve\Steam")
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            possible_paths.insert(0, Path(install_path))
        except:
            pass
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                # Verify it's a valid Steam installation
                if (path / "steam.exe").exists() or (path / "userdata").exists():
                    self.steam_path = path
                    return path
        
        return None
    
    def detect_userdata_path(self) -> Optional[Path]:
        """Detect Steam userdata directory
        
        Returns:
            Path to userdata directory or None if not found
        """
        if self.steam_path is None:
            self.detect_steam_path()
        
        if self.steam_path is None:
            return None
        
        userdata = self.steam_path / "userdata"
        if userdata.exists() and userdata.is_dir():
            self.userdata_path = userdata
            return userdata
        
        return None
    
    def detect_user_ids(self) -> List[str]:
        """Detect Steam user IDs from userdata directory
        
        Returns:
            List of user IDs (directory names in userdata)
        """
        if self.userdata_path is None:
            self.detect_userdata_path()
        
        if self.userdata_path is None:
            return []
        
        user_ids = []
        for item in self.userdata_path.iterdir():
            if item.is_dir() and item.name.isdigit():
                user_ids.append(item.name)
        
        self.user_ids = sorted(user_ids)
        return self.user_ids
    
    def get_shortcuts_path(self, user_id: str) -> Optional[Path]:
        """Get path to shortcuts.vdf for a specific user
        
        Args:
            user_id: Steam user ID
            
        Returns:
            Path to shortcuts.vdf or None if not found
        """
        if self.userdata_path is None:
            self.detect_userdata_path()
        
        if self.userdata_path is None:
            return None
        
        shortcuts_path = self.userdata_path / user_id / "config" / "shortcuts.vdf"
        if shortcuts_path.exists():
            return shortcuts_path
        
        return None
    
    def detect_non_steam_games(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Detect non-Steam games from shortcuts.vdf
        
        Args:
            user_id: Specific user ID to check. If None, checks all users.
            
        Returns:
            List of non-Steam game dictionaries
        """
        if user_id:
            user_ids = [user_id]
        else:
            user_ids = self.detect_user_ids()
        
        all_games = []
        
        for uid in user_ids:
            shortcuts_path = self.get_shortcuts_path(uid)
            if not shortcuts_path:
                continue
            
            try:
                parser = ShortcutsParser(shortcuts_path)
                games = parser.parse()
                
                # Add user_id to each game
                for game in games:
                    game['user_id'] = uid
                
                all_games.extend(games)
            except Exception as e:
                # Log error but continue with other users
                print(f"Warning: Failed to parse shortcuts for user {uid}: {e}")
        
        return all_games
    
    def scan_custom_directories(self) -> List[Dict[str, Any]]:
        """Scan custom directories for game installations
        
        Returns:
            List of detected game dictionaries
        """
        games = []
        
        for custom_path in self.custom_paths:
            if not custom_path.exists():
                continue
            
            try:
                # Look for game executables in subdirectories
                for item in custom_path.iterdir():
                    if not item.is_dir():
                        continue
                    
                    # Look for .exe files (game executables)
                    exe_files = list(item.glob("*.exe"))
                    if not exe_files:
                        continue
                    
                    # Use the first exe as the game executable
                    game_exe = exe_files[0]
                    
                    game_info = {
                        'name': item.name,
                        'exe': str(game_exe),
                        'start_dir': str(item),
                        'app_id': None,
                        'source': 'custom_directory',
                        'custom_path': str(custom_path)
                    }
                    
                    games.append(game_info)
            except PermissionError:
                print(f"Warning: Permission denied accessing {custom_path}")
        
        return games
    
    def detect_save_locations(self, game_info: Dict[str, Any]) -> List[Path]:
        """Detect potential save locations for a game
        
        Args:
            game_info: Game information dictionary
            
        Returns:
            List of potential save directories
        """
        return self.save_detector.find_save_directories(game_info, self.steam_path)
    
    def create_game_id(self, game_name: str) -> str:
        """Create a game ID from game name
        
        Args:
            game_name: Game name
            
        Returns:
            Game ID (lowercase, alphanumeric with hyphens)
        """
        import re
        # Convert to lowercase and replace spaces/special chars with hyphens
        game_id = game_name.lower()
        game_id = re.sub(r'[^\w\s-]', '', game_id)
        game_id = re.sub(r'[-\s]+', '-', game_id)
        game_id = game_id.strip('-')
        return game_id
    
    def create_game_config(self, game_info: Dict[str, Any], save_locations: List[Path] = None) -> Dict[str, Any]:
        """Create game configuration from detected game info
        
        Args:
            game_info: Game information dictionary
            save_locations: List of detected save locations (optional)
            
        Returns:
            Game configuration dictionary
        """
        game_id = self.create_game_id(game_info['name'])
        
        # Use first save location if available, otherwise empty
        local_path = str(save_locations[0]) if save_locations else ""
        
        config = {
            "game": {
                "id": game_id,
                "name": game_info['name'],
                "platform": game_info.get('source', 'steam')
            },
            "paths": {
                "local": local_path,
                "cloud": game_id  # relative to cloud_directory
            },
            "sync": {
                "enabled": True,
                "exclude_patterns": ["*.tmp", "*.log"],
                "last_sync": ""
            },
            "metadata": {
                "auto_detected": True,
                "last_modified": datetime.now().isoformat()
            }
        }
        
        # Add optional fields
        if game_info.get('app_id'):
            config["game"]["steam_app_id"] = str(game_info['app_id'])
        
        if game_info.get('exe'):
            config["game"]["exe"] = game_info['exe']
        
        if game_info.get('start_dir'):
            config["game"]["start_dir"] = game_info['start_dir']
        
        return config
    
    def save_game_config(self, game_info: Dict[str, Any], save_locations: List[Path] = None, overwrite: bool = False) -> bool:
        """Create and save game configuration
        
        Args:
            game_info: Game information dictionary
            save_locations: List of detected save locations (optional)
            overwrite: If False, skip if config already exists (default: False)
            
        Returns:
            True if saved successfully, False if skipped or failed
        """
        if not self.config_manager:
            print("Warning: No config manager available")
            return False
        
        game_id = self.create_game_id(game_info['name'])
        
        # Check if config already exists
        if not overwrite:
            existing_games = self.config_manager.list_games()
            if game_id in existing_games:
                return False  # Skip, config already exists
        
        config = self.create_game_config(game_info, save_locations)
        
        try:
            self.config_manager.save_game_config(game_id, config)
            return True
        except Exception as e:
            print(f"Error saving game config for {game_info['name']}: {e}")
            return False
    
    def detect_all(self) -> dict:
        """Run all detection steps and return summary
        
        Returns:
            Dictionary with detection results
        """
        results = {
            "steam_path": self.detect_steam_path(),
            "userdata_path": self.detect_userdata_path(),
            "user_ids": self.detect_user_ids(),
            "shortcuts_files": [],
            "non_steam_games": [],
            "custom_games": []
        }
        
        for user_id in self.user_ids:
            shortcuts = self.get_shortcuts_path(user_id)
            if shortcuts:
                results["shortcuts_files"].append({
                    "user_id": user_id,
                    "path": shortcuts
                })
        
        # Detect non-Steam games
        results["non_steam_games"] = self.detect_non_steam_games()
        
        # Detect save locations for each game
        for game in results["non_steam_games"]:
            game['potential_save_locations'] = self.detect_save_locations(game)
        
        # Scan custom directories
        results["custom_games"] = self.scan_custom_directories()
        
        # Detect save locations for custom games
        for game in results["custom_games"]:
            game['potential_save_locations'] = self.detect_save_locations(game)
        
        return results

    
    def detect_steam_path(self) -> Optional[Path]:
        """Detect Steam installation path
        
        Returns:
            Path to Steam installation or None if not found
        """
        if self.os_type == "linux":
            return self._detect_steam_linux()
        else:
            return self._detect_steam_windows()
    
    def _detect_steam_linux(self) -> Optional[Path]:
        """Detect Steam installation on Linux
        
        Returns:
            Path to Steam installation or None if not found
        """
        # Common Steam paths on Linux
        possible_paths = [
            Path.home() / ".local" / "share" / "Steam",
            Path.home() / ".steam" / "steam",
            Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",  # Flatpak
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                # Verify it's a valid Steam installation
                if (path / "steam.sh").exists() or (path / "userdata").exists():
                    self.steam_path = path
                    return path
        
        return None
    
    def _detect_steam_windows(self) -> Optional[Path]:
        """Detect Steam installation on Windows
        
        Returns:
            Path to Steam installation or None if not found
        """
        # Common Steam paths on Windows
        possible_paths = [
            Path("C:/Program Files (x86)/Steam"),
            Path("C:/Program Files/Steam"),
        ]
        
        # Check registry-based paths (if available)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\WOW6432Node\Valve\Steam")
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            possible_paths.insert(0, Path(install_path))
        except:
            pass
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                # Verify it's a valid Steam installation
                if (path / "steam.exe").exists() or (path / "userdata").exists():
                    self.steam_path = path
                    return path
        
        return None
    
    def detect_userdata_path(self) -> Optional[Path]:
        """Detect Steam userdata directory
        
        Returns:
            Path to userdata directory or None if not found
        """
        if self.steam_path is None:
            self.detect_steam_path()
        
        if self.steam_path is None:
            return None
        
        userdata = self.steam_path / "userdata"
        if userdata.exists() and userdata.is_dir():
            self.userdata_path = userdata
            return userdata
        
        return None
    
    def detect_user_ids(self) -> List[str]:
        """Detect Steam user IDs from userdata directory
        
        Returns:
            List of user IDs (directory names in userdata)
        """
        if self.userdata_path is None:
            self.detect_userdata_path()
        
        if self.userdata_path is None:
            return []
        
        user_ids = []
        for item in self.userdata_path.iterdir():
            if item.is_dir() and item.name.isdigit():
                user_ids.append(item.name)
        
        self.user_ids = sorted(user_ids)
        return self.user_ids
    
    def get_shortcuts_path(self, user_id: str) -> Optional[Path]:
        """Get path to shortcuts.vdf for a specific user
        
        Args:
            user_id: Steam user ID
            
        Returns:
            Path to shortcuts.vdf or None if not found
        """
        if self.userdata_path is None:
            self.detect_userdata_path()
        
        if self.userdata_path is None:
            return None
        
        shortcuts_path = self.userdata_path / user_id / "config" / "shortcuts.vdf"
        if shortcuts_path.exists():
            return shortcuts_path
        
        return None
    
    def detect_non_steam_games(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Detect non-Steam games from shortcuts.vdf
        
        Args:
            user_id: Specific user ID to check. If None, checks all users.
            
        Returns:
            List of non-Steam game dictionaries
        """
        if user_id:
            user_ids = [user_id]
        else:
            user_ids = self.detect_user_ids()
        
        all_games = []
        
        for uid in user_ids:
            shortcuts_path = self.get_shortcuts_path(uid)
            if not shortcuts_path:
                continue
            
            try:
                parser = ShortcutsParser(shortcuts_path)
                games = parser.parse()
                
                # Add user_id to each game
                for game in games:
                    game['user_id'] = uid
                
                all_games.extend(games)
            except Exception as e:
                # Log error but continue with other users
                print(f"Warning: Failed to parse shortcuts for user {uid}: {e}")
        
        return all_games
    
    def scan_custom_directories(self) -> List[Dict[str, Any]]:
        """Scan custom directories for game installations
        
        Returns:
            List of detected game dictionaries
        """
        games = []
        
        for custom_path in self.custom_paths:
            if not custom_path.exists():
                continue
            
            try:
                # Look for game executables in subdirectories
                for item in custom_path.iterdir():
                    if not item.is_dir():
                        continue
                    
                    # Look for .exe files (game executables)
                    exe_files = list(item.glob("*.exe"))
                    if not exe_files:
                        continue
                    
                    # Use the first exe as the game executable
                    game_exe = exe_files[0]
                    
                    game_info = {
                        'name': item.name,
                        'exe': str(game_exe),
                        'start_dir': str(item),
                        'app_id': None,
                        'source': 'custom_directory',
                        'custom_path': str(custom_path)
                    }
                    
                    games.append(game_info)
            except PermissionError:
                print(f"Warning: Permission denied accessing {custom_path}")
        
        return games
    
    def detect_save_locations(self, game_info: Dict[str, Any]) -> List[Path]:
        """Detect potential save locations for a game
        
        Args:
            game_info: Game information dictionary
            
        Returns:
            List of potential save directories
        """
        return self.save_detector.find_save_directories(game_info, self.steam_path)
    
    def detect_all(self) -> dict:
        """Run all detection steps and return summary
        
        Returns:
            Dictionary with detection results
        """
        results = {
            "steam_path": self.detect_steam_path(),
            "userdata_path": self.detect_userdata_path(),
            "user_ids": self.detect_user_ids(),
            "shortcuts_files": [],
            "non_steam_games": [],
            "custom_games": []
        }
        
        for user_id in self.user_ids:
            shortcuts = self.get_shortcuts_path(user_id)
            if shortcuts:
                results["shortcuts_files"].append({
                    "user_id": user_id,
                    "path": shortcuts
                })
        
        # Detect non-Steam games
        results["non_steam_games"] = self.detect_non_steam_games()
        
        # Detect save locations for each game
        for game in results["non_steam_games"]:
            game['potential_save_locations'] = self.detect_save_locations(game)
        
        # Scan custom directories
        results["custom_games"] = self.scan_custom_directories()
        
        # Detect save locations for custom games
        for game in results["custom_games"]:
            game['potential_save_locations'] = self.detect_save_locations(game)
        
        return results
