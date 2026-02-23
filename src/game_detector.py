"""
Game detection module
Handles detection of Steam installation and non-Steam games
"""

import os
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any

from .vdf_parser import ShortcutsParser


class GameDetector:
    """Detects Steam installation and non-Steam games"""
    
    def __init__(self, os_type: str = None):
        """Initialize game detector
        
        Args:
            os_type: Operating system type ("linux" or "windows"). Auto-detected if None.
        """
        if os_type is None:
            system = platform.system().lower()
            os_type = "windows" if system == "windows" else "linux"
        
        self.os_type = os_type
        self.steam_path: Optional[Path] = None
        self.userdata_path: Optional[Path] = None
        self.user_ids: List[str] = []
    
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
            "non_steam_games": []
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
        
        return results
