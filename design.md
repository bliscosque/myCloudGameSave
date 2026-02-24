# Design Document: Cloud Game Save Synchronization Tool

## 1. System Architecture

### 1.1 High-Level Architecture

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

### 1.2 Component Responsibilities

**CLI Interface**: Parse commands, display output, handle user interaction
**Config Manager**: Read/write configuration files, validate settings
**Game Detector**: Auto-detect games from Steam and common directories
**Conflict Resolver**: Detect conflicts, create backups, prompt user during sync
**Sync Engine**: Compare timestamps, copy files, manage sync operations

## 2. Data Model

### 2.1 Configuration Structure

#### Global Configuration (`config/<HOSTNAME>/config.toml`)
```toml
[system]
os = "linux"  # or "windows"
hostname = "my-machine"

[general]
cloud_directory = "/path/to/mounted/cloud"
backup_directory = "backups"  # relative to config/<HOSTNAME>/
log_level = "info"

[detection]
steam_enabled = true
custom_paths = ["/mnt/games", "/opt/games", "C:\\Games"]
```

#### Per-Game Configuration (`config/<HOSTNAME>/games/<game-id>.toml`)
```toml
[game]
id = "witcher3"  # derived from witcher3.exe
name = "The Witcher 3: Wild Hunt"
platform = "steam"  # or "standalone"
backup_dir_name = "witcher3"  # same as id, derived from exe name
steam_app_id = "292030"  # optional

[paths]
local = "/home/user/.local/share/Steam/steamapps/compatdata/292030/pfx/drive_c/users/steamuser/My Documents/The Witcher 3/gamesaves"
cloud = "witcher3"  # relative to cloud_directory, same as id and backup_dir_name

[sync]
enabled = true
exclude_patterns = ["*.tmp", "*.log"]
last_sync = "2026-02-23T10:30:00Z"

[metadata]
auto_detected = true
last_modified = "2026-02-23T10:30:00Z"
```

**Design Decision - Game ID Naming**: Both `game_id` and `backup_dir_name` are derived from the game's executable filename (lowercase, without extension). This ensures:
- Consistent naming across different machines
- Simple, predictable identifiers
- No conflicts between game_id and cloud directory names
- Easy to understand and remember

Examples:
- `HellbladeGame.exe` → `hellbladegame`
- `Hellblade2.exe` → `hellblade2`
- `METAPHOR.exe` → `metaphor`

### 2.2 Backup Naming Convention

```
<original-filename>.<timestamp>.<source>.backup
Example: save001.dat.20260223-103045.local.backup
```

## 3. Module Design

### 3.1 CLI Module (`cli.py` or `cli.rs`)

**Commands**:
- `gamesync list` - List all configured games
- `gamesync sync <game-id>` - Sync specific game (prompts for conflict resolution)
- `gamesync sync --all` - Sync all enabled games
- `gamesync add <game-id>` - Manually add game configuration
- `gamesync detect` - Auto-detect games and create configs
- `gamesync status [game-id]` - Show sync status
- `gamesync init` - Initialize configuration directory

**Options**:
- `--verbose, -v` - Verbose output
- `--dry-run` - Show what would be synced without doing it
- `--force` - Force sync without prompting

### 3.2 Config Manager Module

**Responsibilities**:
- Load and parse configuration files
- Validate configuration values
- Create default configurations
- Save configuration changes
- Manage configuration directory structure

**Key Functions**:
- `load_global_config()` - Load global settings
- `load_game_config(game_id)` - Load specific game config
- `save_game_config(game_config)` - Save game config
- `list_games()` - Return all configured games
- `validate_paths(config)` - Ensure paths exist and are accessible

### 3.3 Game Detector Module

**Responsibilities**:
- Detect Steam installation paths
- Parse Steam shortcuts.vdf to find non-Steam games
- Identify game save locations for non-Steam games
- Support platform-specific detection logic

**Platform-Specific Paths**:

**Linux**:
- Steam: `~/.local/share/Steam` or `~/.steam/steam`
- Non-Steam shortcuts: `userdata/<userid>/config/shortcuts.vdf`
- Proton saves: `steamapps/compatdata/<appid>/pfx/drive_c/users/steamuser/`

**Windows**:
- Steam: `C:\Program Files (x86)\Steam`
- Non-Steam shortcuts: `userdata\<userid>\config\shortcuts.vdf`
- User saves: `%USERPROFILE%\Documents`, `%APPDATA%`, `%LOCALAPPDATA%`

**Key Functions**:
- `detect_steam_path()` - Find Steam installation
- `parse_shortcuts_vdf()` - Parse non-Steam games from shortcuts.vdf
- `detect_non_steam_games()` - List manually added non-Steam games
- `guess_save_location(game_info)` - Heuristic for save location
- `detect_custom_games(paths)` - Scan custom directories

### 3.4 Sync Engine Module

**Responsibilities**:
- Compare file timestamps
- Copy files bidirectionally
- Handle file conflicts
- Create backups
- Track sync operations

**Sync Algorithm**:
```
For each file in local and cloud:
  1. If file exists only in local → copy to cloud
  2. If file exists only in cloud → copy to local
  3. If file exists in both:
     a. Compare timestamps
     b. If local newer → copy to cloud
     c. If cloud newer → copy to local
     d. If same timestamp → skip
     e. If conflict detected → prompt user for resolution (keep local/cloud/both)
```

**Key Functions**:
- `sync_game(game_config)` - Main sync function
- `compare_directories(local, cloud)` - Build file comparison list
- `copy_file(source, dest, backup=True)` - Safe file copy
- `detect_conflicts(file_info)` - Identify conflict scenarios
- `create_backup(file_path)` - Create timestamped backup

### 3.5 Conflict Resolver Module

**Responsibilities**:
- Detect conflict types
- Create backups of conflicting files
- Present options to user
- Apply user's resolution choice

**Conflict Types**:
- Timestamp conflict: Both files modified since last sync
- Size mismatch: Same timestamp, different sizes (rare)

**Key Functions**:
- `detect_conflict(local_file, cloud_file, last_sync)` - Check for conflicts
- `prompt_resolution(conflict_info)` - Interactive prompt during sync
- `resolve_conflict(choice, conflict_info)` - Apply resolution

## 4. File System Layout

```
<project-root>/
├── gamesync.py                  # Main application
├── src/                         # Source modules
│   ├── config_manager.py
│   ├── game_detector.py
│   ├── save_detector.py
│   ├── sync_engine.py
│   ├── conflict_resolver.py
│   ├── vdf_parser.py
│   └── logger.py
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── run_tests.py            # Test runner
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_detector.py
│   ├── test_sync.py
│   └── test_conflict.py
├── config/                      # Configuration directory (git-ignored)
│   └── <HOSTNAME>/              # Per-machine configuration
│       ├── config.toml          # Global configuration
│       ├── games/               # Per-game configurations
│       │   ├── witcher3.toml
│       │   ├── skyrim.toml
│       │   └── ...
│       ├── backups/             # Conflict backups
│       │   ├── witcher3/
│       │   └── skyrim/
│       └── logs/                # Operation logs
│           └── gamesync.log
└── .gitignore                   # Excludes config/ directory
```

**Cloud Directory Structure**:
```
<cloud_directory>/               # e.g., /home/user/Seafile/My Games/
├── witcher3/                    # backup_dir_name from exe (witcher3.exe)
│   ├── save001.dat
│   └── ...
├── skyrim/                      # backup_dir_name from exe (skyrim.exe)
│   ├── save001.dat
│   └── ...
└── ...
```

**Note**: Configuration is stored locally in the project directory under `config/<HOSTNAME>/` where HOSTNAME is the machine's hostname. This allows the same project to be used on multiple machines without configuration conflicts, while keeping all data private (git-ignored).

The `game_id` and `backup_dir_name` fields in each game config are both derived from the executable filename (lowercase, no extension) and ensure consistent naming across machines.

## 5. Technology Stack

### 5.1 Language Options

**Option A: Python**
- Pros: Cross-platform, rich libraries, rapid development
- Libs: `click` (CLI), `toml` (config), `pathlib` (paths)

**Option B: Rust**
- Pros: Performance, single binary, type safety
- Libs: `clap` (CLI), `toml` (config), `serde` (serialization)

**Recommendation**: Python for Phase 1 (faster development), consider Rust for Phase 2 with GUI

### 5.2 Configuration Format

**TOML** - Human-readable, supports comments, good for nested config

### 5.3 Sync Backend

**Phase 1**: Simple timestamp-based file copying using standard library
**Future**: Optional Unison integration for advanced scenarios

## 6. Error Handling

### 6.1 Error Categories

- **Configuration Errors**: Invalid paths, missing files, parse errors
- **File System Errors**: Permission denied, disk full, path not found
- **Sync Errors**: Conflicts, interrupted transfers, corrupted files

### 6.2 Error Recovery

- All file operations create backups before overwriting
- Failed syncs leave original files intact
- Clear error messages with suggested actions
- Log all errors for debugging

## 7. Security Considerations

- Validate all file paths to prevent directory traversal
- Check available disk space before large copies
- Preserve file permissions during sync
- Don't follow symlinks by default (configurable)

## 8. Testing Strategy

### 8.1 Unit Tests
- Config parsing and validation
- File comparison logic
- Conflict detection
- Path detection algorithms

### 8.2 Integration Tests
- End-to-end sync operations
- Multi-file sync scenarios
- Conflict resolution workflows
- Cross-platform path handling

### 8.3 Manual Testing
- Real game save directories
- Various Steam configurations
- Cloud mount scenarios
- Large file handling

## 9. Future GUI Integration (Phase 2)

### 9.1 Architecture Preparation

- Keep business logic separate from CLI
- Use a service/controller pattern
- CLI and GUI both call same core functions

### 9.2 Qt GUI Components

- Main window with game list
- Per-game configuration dialog
- Sync progress indicators
- Conflict resolution dialogs
- Settings panel

## 10. Performance Considerations

- Use file hashing for large files (optional, configurable)
- Parallel sync for multiple games (future)
- Incremental sync (only changed files)
- Progress reporting for large transfers
- Efficient directory traversal

## 11. Logging

- Log levels: DEBUG, INFO, WARNING, ERROR
- Log file rotation
- Structured logging with timestamps
- Log sync operations, conflicts, errors
- Optional verbose console output
