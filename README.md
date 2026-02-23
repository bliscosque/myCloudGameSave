# Cloud Game Save Synchronization Tool

A multi-platform command-line tool that synchronizes game save files between local machines and a cloud-mounted directory. Supports Windows and Linux, with special support for Steam games (including custom-added non-Steam games).

## Features

- Manual synchronization of game saves to cloud storage
- Timestamp-based conflict detection with backup creation
- Auto-detection of Steam games (including Proton/Wine games on Linux)
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

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Initialize configuration
python gamesync.py init

# Auto-detect games
python gamesync.py detect

# List configured games
python gamesync.py list

# Sync a specific game
python gamesync.py sync <game-id>

# Sync all games
python gamesync.py sync --all
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

## Future Plans

- Phase 2: Qt-based GUI
- Automatic file watching and sync
- Additional game launcher support (Epic, GOG, etc.)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
