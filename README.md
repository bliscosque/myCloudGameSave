# Cloud Game Save Synchronization Tool

A multi-platform command-line tool that synchronizes game save files between local machines and a cloud-mounted directory. Supports Windows and Linux, with special support for non-Steam games that have been manually added to the Steam library.

## Features

- Manual synchronization of game saves to cloud storage
- Timestamp-based conflict detection with backup creation
- Auto-detection of non-Steam games added to Steam library
- Per-game configuration files for easy manual editing
- Support for custom game directories
- Cross-platform (Windows & Linux)

## Requirements

- Python 3.8+
- Cloud storage mounted locally (via rclone or similar)

## Installation

```bash
# Clone the repository
git clone https://github.com/bliscosque/myCloudGameSave.git
cd myCloudGameSave

# Create virtual environment (recommended)
python3 -m venv ~/vscode/venv

# Install dependencies
~/vscode/venv/bin/pip install -r requirements.txt
```

## Quick Start

```bash
# Initialize configuration
~/vscode/venv/bin/python gamesync.py init

# Auto-detect games
~/vscode/venv/bin/python gamesync.py detect

# List configured games
~/vscode/venv/bin/python gamesync.py list

# Sync a specific game
~/vscode/venv/bin/python gamesync.py sync <game-id>

# Sync all games
~/vscode/venv/bin/python gamesync.py sync --all
```

## Configuration

Configuration is stored in `config/<HOSTNAME>/` where HOSTNAME is your machine's hostname. This allows the same project to work on multiple machines without conflicts.

- `config/<HOSTNAME>/config.toml` - Global settings
- `config/<HOSTNAME>/games/*.toml` - Per-game configurations

All configuration files are human-readable and can be edited manually.

## Documentation

- [Requirements](requirements.md) - Detailed project requirements
- [Design](design.md) - Technical architecture and design decisions
- [Tasks](tasks.md) - Development roadmap and progress tracking

## Development Status

Phase 1 (CLI) is currently in development. See [tasks.md](tasks.md) for detailed progress.

## Roadmap

- **Phase 1**: CLI Implementation (Current - 72% complete)
  - Command-line interface
  - Core sync functionality
  - Game detection and configuration
  
- **Phase 2**: TUI Implementation (Planned)
  - Terminal User Interface using Textual
  - Interactive dashboard
  - Real-time monitoring
  
- **Phase 3**: GUI Implementation (Future)
  - Qt-based graphical interface
  - System tray integration
  - Desktop notifications

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
