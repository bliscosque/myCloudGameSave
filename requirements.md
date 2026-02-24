# Requirements Document: Cloud Game Save Synchronization Tool

## 1. Project Overview

A multi-platform command-line tool that synchronizes game save files between local machines and a cloud-mounted directory. The tool will support Windows and Linux, with special consideration for Steam games (including custom-added non-Steam games in the Steam library).

## 2. Functional Requirements

### 2.1 Core Synchronization

- **FR-1.1**: The tool shall synchronize game save files between local directories and a cloud-mounted directory
- **FR-1.2**: The tool shall support manual synchronization triggered by user command
- **FR-1.3**: The tool shall use timestamp-based comparison to determine newer files
- **FR-1.4**: The tool shall support bidirectional sync (local ↔ cloud)
- **FR-1.5**: The tool shall perform per-game synchronization (individual games can be synced independently)

### 2.2 Conflict Resolution

- **FR-2.1**: When conflicts are detected, the tool shall create a backup of the conflicting file
- **FR-2.2**: The tool shall prompt the user to choose which version to keep (local, cloud, or both)
- **FR-2.3**: Backup files shall be clearly labeled with timestamps and source (local/cloud)

### 2.3 Game Detection

- **FR-3.1**: The tool shall attempt to auto-detect non-Steam games that have been manually added to the Steam library
- **FR-3.2**: The tool shall check a configurable list of common game installation directories
- **FR-3.3**: The tool shall allow manual configuration of game save locations
- **FR-3.4**: Auto-detected game configurations shall be editable by the user

### 2.4 Configuration Management

- **FR-4.1**: Configuration shall be stored in human-readable text files in the project directory
- **FR-4.2**: Configuration shall be organized per-hostname to support multiple machines
- **FR-4.3**: Each game shall have its own separate configuration file
- **FR-4.4**: Configuration files shall be easily editable with any text editor
- **FR-4.5**: Users shall be able to add new games by creating configuration files
- **FR-4.6**: Users shall be able to remove games by deleting configuration files
- **FR-4.7**: The tool shall have a global configuration file for tool-wide settings
- **FR-4.8**: Configuration directory shall be excluded from version control (git-ignored)

### 2.5 Command-Line Interface

- **FR-5.1**: The tool shall provide commands to:
  - List all configured games
  - Sync a specific game
  - Sync all games
  - Add a new game configuration
  - Detect and add games automatically
  - Show sync status for games
  - Resolve conflicts interactively
- **FR-5.2**: The tool shall provide clear feedback on sync operations
- **FR-5.3**: The tool shall support verbose/debug output mode

## 3. Non-Functional Requirements

### 3.1 Platform Support

- **NFR-1.1**: The tool shall run on Windows 10/11
- **NFR-1.2**: The tool shall run on modern Linux distributions
- **NFR-1.3**: The tool shall detect non-Steam games added to Steam library on both platforms
- **NFR-1.4**: All configuration and data shall be stored within the project directory
- **NFR-1.5**: Configuration shall be organized by hostname to support multiple machines

### 3.2 Cloud Storage

- **NFR-2.1**: The tool shall assume cloud storage is already mounted locally (via rclone or similar)
- **NFR-2.2**: The tool shall treat the cloud directory as a regular local directory

### 3.3 Performance

- **NFR-3.1**: The tool shall efficiently handle save files ranging from KB to several GB
- **NFR-3.2**: The tool shall provide progress indication for large file transfers

### 3.4 Reliability

- **NFR-4.1**: The tool shall not corrupt or lose save files during sync operations
- **NFR-4.2**: The tool shall create backups before overwriting files
- **NFR-4.3**: The tool shall handle interrupted syncs gracefully

### 3.5 Usability

- **NFR-5.1**: Configuration files shall be simple and self-documenting
- **NFR-5.2**: Error messages shall be clear and actionable
- **NFR-5.3**: The tool shall be suitable for automation (cron jobs, scheduled tasks)

### 3.6 Maintainability

- **NFR-6.1**: Code shall be modular to allow future TUI/GUI integration
- **NFR-6.2**: Sync backend shall be abstracted to allow alternative implementations

## 4. Development Phases

### Phase 1: CLI Implementation (Current)
- Command-line interface
- Core sync functionality
- Game detection and configuration
- Conflict resolution

### Phase 2: TUI Implementation
- Terminal User Interface using Textual library
- Interactive dashboard
- Real-time sync monitoring
- Visual conflict resolution
- Configuration management UI

### Phase 3: GUI Implementation
- Qt-based graphical interface
- System tray integration
- Desktop notifications
- Advanced features

## 5. Future Enhancements

### Phase 2 (TUI) Enhancements:
- **FE-1**: Textual-based TUI for interactive management
- **FE-2**: Real-time sync status dashboard
- **FE-3**: Visual game library browser
- **FE-4**: Interactive conflict resolution interface

### Phase 3+ Enhancements:
- **FE-5**: Qt-based GUI for easier configuration and monitoring
- **FE-6**: Automatic file watching and sync on changes
- **FE-7**: Support for native Steam games (in addition to non-Steam)
- **FE-8**: Support for additional game launchers (Epic, GOG, etc.)
- **FE-9**: Sync scheduling within the tool
- **FE-10**: Cloud provider integration (direct API access without mounting)
- **FE-11**: Recursive directory sync (currently only syncs files in top-level directory)
  - Research: Determine if most games store saves in flat structure or nested directories
  - If nested is common, implement recursive sync with proper conflict handling
  - Consider per-game configuration option for recursive vs flat sync

## 6. Constraints

- **C-1**: Cloud storage must be mounted and accessible as a local directory
- **C-2**: Phase 1 is terminal/CLI only, Phase 2 is TUI, Phase 3 is GUI
- **C-3**: User is responsible for cloud mounting (rclone, etc.)
- **C-4**: All configuration and data files must remain within the project directory
- **C-5**: Configuration directory must be excluded from version control

## 6. Assumptions

- **A-1**: Users have basic command-line knowledge
- **A-2**: Cloud directory remains mounted during sync operations
- **A-3**: Users will not manually modify cloud files during sync
- **A-4**: File timestamps are reliable indicators of file versions
