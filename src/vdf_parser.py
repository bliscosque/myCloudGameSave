"""
VDF (Valve Data Format) parser
Handles parsing of binary VDF files (shortcuts.vdf)
"""

import struct
from pathlib import Path
from typing import Dict, Any, List


class VDFParser:
    """Parser for binary VDF files"""
    
    # VDF data types
    TYPE_SECTION = 0x00
    TYPE_STRING = 0x01
    TYPE_INT32 = 0x02
    TYPE_END = 0x08
    
    def __init__(self, file_path: Path):
        """Initialize VDF parser
        
        Args:
            file_path: Path to VDF file
        """
        self.file_path = file_path
        self.data = None
        self.position = 0
    
    def parse(self) -> Dict[str, Any]:
        """Parse VDF file
        
        Returns:
            Parsed data as dictionary
        """
        with open(self.file_path, 'rb') as f:
            self.data = f.read()
        
        self.position = 0
        return self._parse_section()
    
    def _read_cstring(self) -> str:
        """Read null-terminated string
        
        Returns:
            String value
        """
        start = self.position
        while self.position < len(self.data) and self.data[self.position] != 0:
            self.position += 1
        
        result = self.data[start:self.position].decode('utf-8', errors='ignore')
        self.position += 1  # Skip null terminator
        return result
    
    def _read_int32(self) -> int:
        """Read 32-bit integer
        
        Returns:
            Integer value
        """
        value = struct.unpack('<I', self.data[self.position:self.position + 4])[0]
        self.position += 4
        return value
    
    def _parse_section(self) -> Dict[str, Any]:
        """Parse a section (dictionary)
        
        Returns:
            Dictionary of parsed data
        """
        result = {}
        
        while self.position < len(self.data):
            type_byte = self.data[self.position]
            self.position += 1
            
            if type_byte == self.TYPE_END:
                break
            elif type_byte == self.TYPE_SECTION:
                key = self._read_cstring()
                value = self._parse_section()
                result[key] = value
            elif type_byte == self.TYPE_STRING:
                key = self._read_cstring()
                value = self._read_cstring()
                result[key] = value
            elif type_byte == self.TYPE_INT32:
                key = self._read_cstring()
                value = self._read_int32()
                result[key] = value
            else:
                # Unknown type, try to skip
                break
        
        return result


class ShortcutsParser:
    """Parser for Steam shortcuts.vdf file"""
    
    def __init__(self, shortcuts_path: Path):
        """Initialize shortcuts parser
        
        Args:
            shortcuts_path: Path to shortcuts.vdf
        """
        self.shortcuts_path = shortcuts_path
        self.parser = VDFParser(shortcuts_path)
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse shortcuts.vdf and extract non-Steam games
        
        Returns:
            List of game dictionaries
        """
        try:
            data = self.parser.parse()
        except Exception as e:
            raise ValueError(f"Failed to parse shortcuts.vdf: {e}")
        
        games = []
        
        # shortcuts.vdf structure: {"shortcuts": {"0": {...}, "1": {...}, ...}}
        shortcuts = data.get('shortcuts', {})
        
        for key, game_data in shortcuts.items():
            if not isinstance(game_data, dict):
                continue
            
            game = self._extract_game_info(game_data)
            if game:
                games.append(game)
        
        return games
    
    def _extract_game_info(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant game information
        
        Args:
            game_data: Raw game data from VDF
            
        Returns:
            Cleaned game information dictionary
        """
        # Extract key fields
        app_name = game_data.get('AppName', game_data.get('appname', ''))
        exe = game_data.get('Exe', game_data.get('exe', ''))
        start_dir = game_data.get('StartDir', game_data.get('StartDir', ''))
        app_id = game_data.get('appid', 0)
        
        if not app_name:
            return None
        
        return {
            'name': app_name,
            'exe': exe,
            'start_dir': start_dir,
            'app_id': app_id,
            'raw_data': game_data
        }
