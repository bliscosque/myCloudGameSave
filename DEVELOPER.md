# Developer Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Documentation](#module-documentation)
3. [Development Setup](#development-setup)
4. [Testing](#testing)
5. [Code Style](#code-style)
6. [Contributing](#contributing)
7. [Release Process](#release-process)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Interface                        │
│  (commands: sync, list, add, detect, status, init)      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Core Application                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Config     │  │    Game      │  │   Conflict   │  │
│  │   Manager    │  │   Detector   │  │   Resolver   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Sync Engine                             │
│  (timestamp comparison, file operations, backup)         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              File System Layer                           │
│  (local game saves ↔ cloud-mounted directory)           │
└─────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Testability**: All core logic is unit tested
3. **Configurability**: Human-readable TOML configs
4. **Safety**: Backups before overwrites, no destructive operations
5. **Transparency**: Detailed logging and dry-run mode

### Data Flow

1. **Detection**: VDF Parser → Game Detector → Save Detector → Config Manager
2. **Sync**: Config Manager → Sync Engine → File System
3. **Conflicts**: Sync Engine → Conflict Resolver → User Prompt → Resolution

---

## Module Documentation

### `gamesync.py` - Main Entry Point

**Purpose**: CLI interface and command routing

**Key Functions**:
- `create_parser()`: Sets up argparse with all commands
- `cmd_init()`: Initialize configuration
- `cmd_detect()`: Auto-detect games
- `cmd_list()`: List configured games
- `cmd_add()`: Manually add game
- `cmd_sync()`: Synchronize saves
- `cmd_status()`: Show sync status

**Dependencies**: All src modules

---

### `src/config_manager.py` - Configuration Management

**Purpose**: Load, validate, and save configurations

**Classes**:
- `ConfigManager`: Main configuration manager
- `ConfigError`: Configuration-related exceptions

**Key Methods**:
```python
ConfigManager.__init__(config_dir=None)
ConfigManager.initialize() -> bool
ConfigManager.load_config() -> dict
ConfigManager.save_config(config: dict)
ConfigManager.load_game_config(game_id: str) -> dict
ConfigManager.save_game_config(game_id: str, config: dict)
ConfigManager.list_games() -> list
```

**Configuration Structure**:
- Global: `config/<hostname>/config.toml`
- Per-game: `config/<hostname>/games/<game-id>.toml`

**Validation**:
- Checks required fields
- Validates paths
- Ensures TOML format

---

### `src/game_detector.py` - Game Detection

**Purpose**: Detect non-Steam games from Steam library

**Classes**:
- `GameDetector`: Main detector class

**Key Methods**:
```python
GameDetector.__init__(os_type=None, custom_paths=None, config_manager=None)
GameDetector.detect_steam_path() -> Path
GameDetector.detect_user_ids() -> list
GameDetector.detect_non_steam_games(user_id=None) -> list
GameDetector.detect_save_locations(game_info: dict) -> list
GameDetector.create_game_id(game_info: dict) -> str
GameDetector.create_backup_dir_name(game_info: dict) -> str
GameDetector.create_game_config(game_info: dict, save_locations: list) -> dict
GameDetector.save_game_config(game_info: dict, save_locations: list, overwrite: bool) -> bool
```

**Detection Process**:
1. Find Steam installation
2. Locate userdata directory
3. Parse shortcuts.vdf for each user
4. Detect save locations using SaveLocationDetector
5. Create game configurations

**Game ID Logic**:
- Based on executable filename (lowercase, no extension)
- Example: `HellbladeGame.exe` → `hellbladegame`

---

### `src/save_detector.py` - Save Location Detection

**Purpose**: Find game save directories

**Classes**:
- `SaveLocationDetector`: Detects save locations

**Key Methods**:
```python
SaveLocationDetector.__init__(os_type: str)
SaveLocationDetector.detect_save_locations(game_info: dict) -> list
SaveLocationDetector._get_appdata_paths() -> list
SaveLocationDetector._find_game_subdirs(base_path: Path, game_name: str, max_depth: int) -> list
SaveLocationDetector._find_save_subdirs(game_dir: Path, max_depth: int) -> list
```

**Detection Strategy**:
1. Get AppData paths (Local, Roaming, LocalLow)
2. Search for directories matching game name
3. Recursively search for actual save files (.sav, .dat, etc.)
4. Return shallowest directory containing saves

**Supported Patterns**:
- Windows: `%APPDATA%`, `%LOCALAPPDATA%`
- Linux (Proton): `compatdata/*/pfx/drive_c/users/steamuser/AppData/`

---

### `src/vdf_parser.py` - VDF File Parser

**Purpose**: Parse Steam's binary VDF format

**Classes**:
- `VDFParser`: Base VDF parser
- `ShortcutsParser`: Shortcuts.vdf specific parser

**Key Methods**:
```python
ShortcutsParser.__init__(shortcuts_path: Path)
ShortcutsParser.parse() -> list
```

**VDF Format**:
- Binary format used by Steam
- Contains non-Steam game entries
- Includes: name, exe, start_dir, app_id

---

### `src/sync_engine.py` - Synchronization Engine

**Purpose**: Compare and sync files between local and cloud

**Classes**:
- `SyncEngine`: Main sync engine
- `FileComparison`: File comparison result
- `SyncAction`: Enum for sync actions

**Key Methods**:
```python
SyncEngine.compare_files(local_path: Path, cloud_path: Path, last_sync: str) -> FileComparison
SyncEngine.compare_directories(local_dir: Path, cloud_dir: Path, last_sync: str) -> list
SyncEngine.copy_file(src: Path, dst: Path) -> bool
SyncEngine.create_backup(file_path: Path, backup_dir: Path, source: str) -> Path
SyncEngine.sync_files(local_dir: Path, cloud_dir: Path, backup_dir: Path, last_sync: str, dry_run: bool) -> dict
```

**Sync Logic**:
1. Compare timestamps
2. Determine action (copy_to_cloud, copy_to_local, conflict, skip)
3. Create backups before overwrites
4. Execute file operations
5. Update last_sync timestamp

**Conflict Detection**:
- Both files modified after last_sync
- Requires user resolution

---

### `src/conflict_resolver.py` - Conflict Resolution

**Purpose**: Detect and resolve file conflicts

**Classes**:
- `ConflictResolver`: Conflict handler
- `ResolutionStrategy`: Enum for resolution strategies

**Key Methods**:
```python
ConflictResolver.detect_conflict(local_path: Path, cloud_path: Path, last_sync: str) -> bool
ConflictResolver.create_conflict_backup(local_path: Path, cloud_path: Path, backup_dir: Path) -> dict
ConflictResolver.get_conflict_info(local_path: Path, cloud_path: Path) -> dict
ConflictResolver.resolve_conflict(local_path: Path, cloud_path: Path, strategy: ResolutionStrategy, backup_dir: Path) -> bool
ConflictResolver.add_conflict(local_path: Path, cloud_path: Path)
ConflictResolver.list_conflicts() -> list
```

**Resolution Strategies**:
- `KEEP_LOCAL`: Copy local → cloud
- `KEEP_CLOUD`: Copy cloud → local
- `KEEP_BOTH`: Rename both with suffixes

---

### `src/logger.py` - Logging System

**Purpose**: Centralized logging with file rotation

**Key Functions**:
```python
init_logger(log_dir: Path, log_level: str) -> logging.Logger
get_logger() -> logging.Logger
```

**Features**:
- File logging with rotation (10MB, 5 backups)
- Console logging
- Configurable log levels
- Timestamped entries

---

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Virtual environment tool

### Setup Steps

1. **Clone repository:**
   ```bash
   git clone https://github.com/bliscosque/myCloudGameSave.git
   cd myCloudGameSave
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv ~/vscode/venv
   source ~/vscode/venv/bin/activate  # Linux/Mac
   # or
   ~/vscode/venv/Scripts/activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies:**
   ```bash
   pip install pytest pytest-cov black flake8
   ```

5. **Verify setup:**
   ```bash
   python gamesync.py --help
   python tests/run_tests.py
   ```

---

## Testing

### Test Structure

```
tests/
├── __init__.py              # Package init
├── run_tests.py             # Test runner
├── test_config.py           # Config tests (7)
├── test_logger.py           # Logger tests (5)
├── test_detector.py         # Detector tests (9)
├── test_sync.py             # Sync tests (14)
├── test_conflict.py         # Conflict tests (9)
└── test_integration.py      # Integration tests (5)
```

### Running Tests

**All tests:**
```bash
python tests/run_tests.py
```

**Individual suites:**
```bash
python tests/test_config.py
python tests/test_sync.py
```

**With coverage:**
```bash
pytest --cov=src tests/
```

### Writing Tests

**Test Template:**
```python
def test_feature():
    """Test description"""
    print("\nTest N: Feature name...")
    
    # Setup
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test code
        
        # Assertions
        assert condition
        
        print("  ✓ Test passed")
        return True
```

**Best Practices:**
- Use temporary directories
- Clean up after tests
- Test normal and edge cases
- Use descriptive names
- Print progress messages

---

## Code Style

### Python Style Guide

Follow PEP 8 with these specifics:

**Formatting:**
- 4 spaces for indentation
- Max line length: 100 characters
- Use double quotes for strings
- Use f-strings for formatting

**Naming:**
- `snake_case` for functions and variables
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Descriptive names over short names

**Documentation:**
- Docstrings for all public functions/classes
- Type hints where helpful
- Comments for complex logic

**Example:**
```python
def sync_files(self, local_dir: Path, cloud_dir: Path, 
               backup_dir: Path, last_sync: Optional[str] = None,
               dry_run: bool = False) -> Dict[str, Any]:
    """Synchronize files between local and cloud directories
    
    Args:
        local_dir: Local directory path
        cloud_dir: Cloud directory path
        backup_dir: Backup directory path
        last_sync: ISO format timestamp of last sync (optional)
        dry_run: If True, only show what would be done
        
    Returns:
        Dictionary with sync results
    """
    # Implementation
```

### Code Organization

**Module Structure:**
```python
#!/usr/bin/env python3
"""Module description"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import toml

# Local imports
from src.config_manager import ConfigManager

# Constants
DEFAULT_TIMEOUT = 30

# Classes
class MyClass:
    pass

# Functions
def my_function():
    pass

# Main
if __name__ == "__main__":
    main()
```

---

## Contributing

### Contribution Workflow

1. **Fork the repository**

2. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Make changes:**
   - Write code
   - Add tests
   - Update documentation

4. **Test changes:**
   ```bash
   python tests/run_tests.py
   ```

5. **Commit changes:**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. **Push to fork:**
   ```bash
   git push origin feature/my-feature
   ```

7. **Create Pull Request**

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `style`: Formatting
- `chore`: Maintenance

**Example:**
```
feat: Add recursive directory sync

- Implement recursive file scanning
- Add max_depth parameter
- Update tests for recursive sync

Closes #123
```

### Pull Request Guidelines

- Clear description of changes
- Reference related issues
- All tests passing
- Documentation updated
- No merge conflicts

---

## Release Process

### Version Numbering

Follow Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Example: `1.2.3`

**Increment:**
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist

1. **Update version:**
   - Update version in code
   - Update CHANGELOG.md

2. **Run all tests:**
   ```bash
   python tests/run_tests.py
   ```

3. **Update documentation:**
   - README.md
   - USER_GUIDE.md
   - CHANGELOG.md

4. **Create release commit:**
   ```bash
   git commit -m "Release v1.0.0"
   ```

5. **Tag release:**
   ```bash
   git tag -a v1.0.0 -m "Version 1.0.0"
   git push origin v1.0.0
   ```

6. **Create GitHub release:**
   - Go to GitHub releases
   - Create new release from tag
   - Add release notes
   - Attach any binaries

---

## Project Structure

```
myCloudGameSave/
├── gamesync.py              # Main CLI entry point
├── src/                     # Source modules
│   ├── __init__.py
│   ├── config_manager.py    # Configuration management
│   ├── game_detector.py     # Game detection
│   ├── save_detector.py     # Save location detection
│   ├── vdf_parser.py        # VDF file parsing
│   ├── sync_engine.py       # Sync logic
│   ├── conflict_resolver.py # Conflict handling
│   └── logger.py            # Logging system
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── run_tests.py
│   └── test_*.py
├── config/                  # Configuration (git-ignored)
│   └── <hostname>/
│       ├── config.toml
│       ├── games/
│       ├── logs/
│       └── backups/
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── LICENSE                 # MIT License
├── README.md               # Project overview
├── USER_GUIDE.md           # User documentation
├── DEVELOPER.md            # This file
├── TESTING.md              # Test documentation
├── design.md               # Architecture design
├── requirements.md         # Requirements spec
└── tasks.md                # Development roadmap
```

---

## Useful Commands

### Development

```bash
# Run application
python gamesync.py <command>

# Run tests
python tests/run_tests.py

# Run specific test
python tests/test_sync.py

# Check code style
flake8 src/ gamesync.py

# Format code
black src/ gamesync.py

# View logs
tail -f config/$(hostname)/logs/gamesync.log
```

### Debugging

```bash
# Verbose mode
python gamesync.py --verbose detect

# Dry-run mode
python gamesync.py --dry-run sync --all

# Check status
python gamesync.py status

# Python debugger
python -m pdb gamesync.py sync <game-id>
```

---

## Resources

- **Repository**: https://github.com/bliscosque/myCloudGameSave
- **Issues**: https://github.com/bliscosque/myCloudGameSave/issues
- **Documentation**: See README.md, USER_GUIDE.md, design.md
- **Python Docs**: https://docs.python.org/3/
- **TOML Spec**: https://toml.io/

---

## Getting Help

- Check existing documentation
- Search closed issues
- Ask in discussions
- Create new issue with:
  - Clear description
  - Steps to reproduce
  - Expected vs actual behavior
  - Logs and error messages
  - System information
