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
                        # Look for game-specific subdirectories
                        game_subdirs = self._find_game_subdirs(loc, clean_name)
                        if game_subdirs:
                            candidates.extend(game_subdirs)
        
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
    
    def _find_game_subdirs(self, base_path: Path, game_name: str, max_depth: int = 3) -> List[Path]:
        """Find subdirectories matching game name
        
        Args:
            base_path: Base directory to search
            game_name: Game name to match
            max_depth: Maximum depth to search (default 3)
            
        Returns:
            List of matching directories
        """
        if not base_path.exists():
            return []
        
        matches = []
        game_name_lower = game_name.lower()
        
        # Create variations and extract key words from game name
        game_words = [word for word in game_name_lower.split() if len(word) > 3]
        game_variations = [
            game_name_lower,
            game_name_lower.replace(' ', ''),
            game_name_lower.replace(' ', '-'),
            game_name_lower.replace("'", ''),
        ]
        
        def search_recursive(path: Path, depth: int = 0):
            if depth > max_depth:
                return
            
            try:
                for item in path.iterdir():
                    if not item.is_dir():
                        continue
                    
                    # Skip system directories
                    if item.name in ['Microsoft', 'Temp', 'temp', 'Cache', 'cache']:
                        continue
                    
                    item_name_lower = item.name.lower()
                    
                    # Check exact or partial matches with variations
                    matched = False
                    for variation in game_variations:
                        if variation and (variation in item_name_lower or item_name_lower in variation):
                            matched = True
                            break
                    
                    # Also check if any significant word from game name is in directory name
                    if not matched and game_words:
                        for word in game_words:
                            if word in item_name_lower:
                                matched = True
                                break
                    
                    if matched:
                        # Check if this directory or subdirectories contain saves
                        save_dirs = self._find_save_subdirs(item)
                        if save_dirs:
                            matches.extend(save_dirs)
                        else:
                            # Add the directory itself if no specific save subdirs found
                            matches.append(item)
                    else:
                        # Continue searching deeper
                        search_recursive(item, depth + 1)
            except PermissionError:
                pass
        
        search_recursive(base_path)
        return matches
    
    def _find_save_subdirs(self, game_dir: Path, max_depth: int = 3) -> List[Path]:
        """Find subdirectories containing actual save files
        
        Args:
            game_dir: Game directory to search
            max_depth: Maximum depth to search for save files
            
        Returns:
            List of directories containing save files (prefers parent dirs with most files)
        """
        save_dirs = {}  # path -> file count
        save_extensions = ['.sav', '.dat', '.save', '.bin', '.slot']
        save_keywords = ['save', 'saves', 'savegame', 'savegames', 'savedata', 'saved']
        
        def search_for_saves(path: Path, depth: int = 0):
            if depth > max_depth:
                return
            
            try:
                has_save_files = False
                save_file_count = 0
                
                for item in path.iterdir():
                    if item.is_file():
                        # Check if it's a save file by extension or name
                        if any(item.name.lower().endswith(ext) for ext in save_extensions):
                            has_save_files = True
                            save_file_count += 1
                        elif any(kw in item.name.lower() for kw in save_keywords):
                            has_save_files = True
                            save_file_count += 1
                    elif item.is_dir():
                        # Skip system directories
                        if item.name not in ['Microsoft', 'Temp', 'temp', 'Cache', 'cache', '__pycache__']:
                            search_for_saves(item, depth + 1)
                
                if has_save_files:
                    save_dirs[path] = save_file_count
                    
            except PermissionError:
                pass
        
        search_for_saves(game_dir)
        
        # Return only parent directories (avoid returning both parent and child)
        if save_dirs:
            # Sort by file count descending
            sorted_dirs = sorted(save_dirs.items(), key=lambda x: x[1], reverse=True)
            
            # Keep only the shallowest directory in each hierarchy
            result = []
            for path, count in sorted_dirs:
                # Check if any existing result is a parent of this path
                has_parent = any(p in path.parents for p in result)
                
                if not has_parent:
                    # Remove any children of this path from results
                    result = [p for p in result if path not in p.parents]
                    result.append(path)
            
            return result
        
        return []
