"""
Save location detection module
Heuristics for finding game save directories
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any


class SaveLocationDetector:
    """Detects game save file locations"""
    
    def __init__(self, os_type: str):
        """Initialize save location detector
        
        Args:
            os_type: Operating system type ("linux" or "windows")
        """
        self.os_type = os_type
    
    def expand_path(self, path: str) -> Path:
        """Expand environment variables and user paths
        
        Args:
            path: Path with potential variables
            
        Returns:
            Expanded Path object
        """
        # Expand environment variables
        path = os.path.expandvars(path)
        
        # Expand user home
        path = os.path.expanduser(path)
        
        # Windows-specific expansions
        if self.os_type == "windows":
            path = path.replace("%USERPROFILE%", str(Path.home()))
            path = path.replace("%APPDATA%", str(Path.home() / "AppData" / "Roaming"))
            path = path.replace("%LOCALAPPDATA%", str(Path.home() / "AppData" / "Local"))
            path = path.replace("%DOCUMENTS%", str(Path.home() / "Documents"))
        
        return Path(path)
    
    def get_common_save_locations(self) -> List[Path]:
        """Get common save file locations for the OS
        
        Returns:
            List of common save directories
        """
        if self.os_type == "linux":
            return self._get_linux_save_locations()
        else:
            return self._get_windows_save_locations()
    
    def _get_linux_save_locations(self) -> List[Path]:
        """Get common Linux save locations
        
        Returns:
            List of directories
        """
        home = Path.home()
        locations = [
            home / ".local" / "share",
            home / ".config",
            home / "Documents",
            home / "Documents" / "My Games",
        ]
        
        # XDG directories
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            locations.append(Path(xdg_data))
        
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            locations.append(Path(xdg_config))
        
        return [loc for loc in locations if loc.exists()]
    
    def _get_windows_save_locations(self) -> List[Path]:
        """Get common Windows save locations
        
        Returns:
            List of directories
        """
        home = Path.home()
        locations = [
            home / "Documents",
            home / "Documents" / "My Games",
            home / "Saved Games",
            home / "AppData" / "Roaming",
            home / "AppData" / "Local",
            home / "AppData" / "LocalLow",
        ]
        
        return [loc for loc in locations if loc.exists()]
    
    def check_proton_prefix(self, game_info: Dict[str, Any], steam_path: Path) -> Optional[Path]:
        """Check for Proton/Wine prefix save locations
        
        Args:
            game_info: Game information dictionary
            steam_path: Steam installation path
            
        Returns:
            Proton prefix path or None
        """
        if self.os_type != "linux":
            return None
        
        app_id = game_info.get('app_id')
        if not app_id:
            return None
        
        # For non-Steam games, the app_id is very large (> 2^32)
        # We need to check compatdata directory
        compatdata = steam_path / "steamapps" / "compatdata" / str(app_id)
        if compatdata.exists():
            prefix = compatdata / "pfx" / "drive_c"
            if prefix.exists():
                return prefix
        
        # Also check if the game is using a custom prefix path
        # Sometimes non-Steam games use the start_dir as a hint
        start_dir = game_info.get('start_dir', '')
        if start_dir and 'drive_c' in start_dir:
            # Extract the prefix path
            parts = Path(start_dir).parts
            try:
                drive_c_index = parts.index('drive_c')
                prefix_path = Path(*parts[:drive_c_index]) / 'drive_c'
                if prefix_path.exists():
                    return prefix_path
            except (ValueError, IndexError):
                pass
        
        return None
    
    def check_game_directory(self, game_info: Dict[str, Any]) -> Optional[Path]:
        """Check game installation directory for saves
        
        Args:
            game_info: Game information dictionary
            
        Returns:
            Game directory or None
        """
        start_dir = game_info.get('start_dir', '')
        if not start_dir:
            return None
        
        game_dir = Path(start_dir)
        if game_dir.exists():
            return game_dir
        
        return None
    
    def find_save_directories(self, game_info: Dict[str, Any], steam_path: Path = None) -> List[Path]:
        """Find potential save directories for a game
        
        Args:
            game_info: Game information dictionary
            steam_path: Steam installation path (optional)
            
        Returns:
            List of potential save directories
        """
        candidates = []
        game_name = game_info.get('name', '')
        
        # Clean game name for directory matching
        clean_name = self._clean_game_name(game_name)
        
        # Check Proton prefix (Linux only) - PRIORITY for non-Steam games
        if self.os_type == "linux":
            proton_prefix = self.check_proton_prefix(game_info, steam_path)
            if proton_prefix:
                # Check common Windows save locations in prefix
                prefix_locations = [
                    proton_prefix / "users" / "steamuser" / "AppData" / "Local",
                    proton_prefix / "users" / "steamuser" / "AppData" / "Roaming",
                    proton_prefix / "users" / "steamuser" / "AppData" / "LocalLow",
                    proton_prefix / "users" / "steamuser" / "Documents",
                    proton_prefix / "users" / "steamuser" / "Documents" / "My Games",
                    proton_prefix / "users" / "steamuser" / "Saved Games",
                ]
                
                for loc in prefix_locations:
                    if loc.exists():
                        # Look for game-specific subdirectories (non-system dirs)
                        game_subdirs = self._find_game_subdirs(loc, clean_name)
                        if game_subdirs:
                            candidates.extend(game_subdirs)
                        else:
                            # If no game-specific subdirs found, add the base location
                            # but only for AppData locations (most common for saves)
                            if 'AppData' in str(loc):
                                candidates.append(loc)
        
        # Check game installation directory
        game_dir = self.check_game_directory(game_info)
        if game_dir:
            # Look for save-related subdirectories
            save_dirs = ['save', 'saves', 'savegame', 'savegames', 'SaveData', 'Saves']
            for save_dir in save_dirs:
                potential = game_dir / save_dir
                if potential.exists():
                    candidates.append(potential)
        
        # Check common OS save locations (lower priority for Proton games)
        if not candidates or self.os_type != "linux":
            for base_loc in self.get_common_save_locations():
                candidates.extend(self._find_game_subdirs(base_loc, clean_name))
        
        # Remove duplicates and return
        return list(set(candidates))    
    def _clean_game_name(self, name: str) -> str:
        """Clean game name for directory matching
        
        Args:
            name: Game name
            
        Returns:
            Cleaned name
        """
        # Remove special characters, keep alphanumeric and spaces
        clean = re.sub(r'[^\w\s-]', '', name)
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        return clean
    
    def _find_game_subdirs(self, base_path: Path, game_name: str) -> List[Path]:
        """Find subdirectories matching game name
        
        Args:
            base_path: Base directory to search
            game_name: Game name to match
            
        Returns:
            List of matching directories
        """
        if not base_path.exists():
            return []
        
        matches = []
        game_name_lower = game_name.lower()
        
        try:
            for item in base_path.iterdir():
                if not item.is_dir():
                    continue
                
                item_name_lower = item.name.lower()
                
                # Exact match
                if item_name_lower == game_name_lower:
                    matches.append(item)
                # Partial match (game name in directory name)
                elif game_name_lower in item_name_lower or item_name_lower in game_name_lower:
                    matches.append(item)
        except PermissionError:
            pass
        
        return matches
