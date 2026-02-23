# Tasks Document: Cloud Game Save Synchronization Tool

## Phase 1: CLI Implementation

### Milestone 1: Project Setup & Core Infrastructure

- [x] **Task 1.1**: Initialize project structure
  - Create directory layout
  - Set up version control (git)
  - Create README.md with project description
  - Choose implementation language (Python/Rust)
  - Set up dependency management (requirements.txt / Cargo.toml)

- [x] **Task 1.2**: Implement configuration directory initialization
  - Create config/<HOSTNAME> directory structure in project root
  - Get system hostname automatically
  - Create subdirectories: games/, backups/, logs/
  - Detect OS (Linux/Windows) and store in config
  - Create default global configuration file with OS parameter
  - Add config/ to .gitignore

- [x] **Task 1.3**: Implement configuration file parser
  - Parse TOML configuration files
  - Validate configuration schema
  - Handle missing/malformed config files gracefully
  - Implement config file writer

- [x] **Task 1.4**: Set up logging system
  - Configure log levels (DEBUG, INFO, WARNING, ERROR)
  - Implement file logging with rotation
  - Implement console logging with verbosity control
  - Add timestamps and structured logging

### Milestone 2: Game Detection & Configuration

- [x] **Task 2.1**: Implement Steam path detection
  - Detect Steam installation on Linux (~/.local/share/Steam)
  - Detect Steam installation on Windows (Program Files)
  - Find Steam userdata directory
  - Handle multiple Steam user accounts

- [x] **Task 2.2**: Implement non-Steam game detection
  - Parse shortcuts.vdf file (binary VDF format)
  - Extract non-Steam game information (AppID, name, exe path)
  - Build list of manually added non-Steam games
  - Handle both Windows and Linux shortcuts format

- [x] **Task 2.3**: Implement save location detection heuristics
  - Create database of common save locations per game
  - Implement path expansion for Windows user directories
  - Implement path expansion for Linux XDG directories
  - Check game installation directory for saves
  - Check Proton/Wine prefix paths for Windows games on Linux

- [x] **Task 2.4**: Implement custom directory scanning
  - Scan user-configured game directories
  - Detect game executables and infer save locations
  - Create game configuration suggestions

- [x] **Task 2.5**: Implement per-game configuration management
  - Create game configuration file template
  - Save detected games as individual config files
  - Load game configurations from files
  - Validate game configuration (paths exist, etc.)
  - Support manual editing of game configs

### Milestone 3: Sync Engine

- [x] **Task 3.1**: Implement file comparison logic
  - Compare file timestamps (mtime)
  - Compare file sizes
  - Build list of files to sync (local → cloud, cloud → local)
  - Handle missing files (new files to copy)

- [x] **Task 3.2**: Implement basic file operations
  - Safe file copy with error handling
  - Preserve file timestamps during copy
  - Preserve file permissions
  - Handle large files with progress indication
  - Verify disk space before copying

- [x] **Task 3.3**: Implement backup system
  - Create backup directory structure
  - Generate timestamped backup filenames
  - Copy files to backup before overwriting
  - Implement backup retention policy (optional)

- [x] **Task 3.4**: Implement sync algorithm
  - Scan local and cloud directories
  - Determine sync direction for each file
  - Execute file copies with backups
  - Update last_sync timestamp in game config
  - Handle sync interruptions gracefully

- [x] **Task 3.5**: Implement dry-run mode
  - Show what would be synced without executing
  - Display file sizes and directions
  - Estimate total data transfer

### Milestone 4: Conflict Resolution

- [x] **Task 4.1**: Implement conflict detection
  - Detect when both local and cloud files are newer than last sync
  - Detect size mismatches with same timestamp
  - Track conflicts in game configuration

- [x] **Task 4.2**: Implement conflict backup creation
  - Create backups of both conflicting versions
  - Label backups clearly (local vs cloud)
  - Store conflict metadata

- [x] **Task 4.3**: Implement interactive conflict resolution
  - Display conflict information to user
  - Show file details (size, timestamp, location)
  - Prompt user for choice (keep local, keep cloud, keep both)
  - Apply user's resolution choice
  - Update game configuration

- [x] **Task 4.4**: Implement conflict listing
  - List all pending conflicts for a game
  - Show conflict details in readable format
  - Support resolving multiple conflicts in batch

### Milestone 5: CLI Interface

- [x] **Task 5.1**: Implement CLI framework
  - Set up command-line argument parser
  - Define command structure and subcommands
  - Implement global options (--verbose, --dry-run, --force)
  - Add help text and usage examples

- [x] **Task 5.2**: Implement `init` command
  - Initialize configuration directories
  - Create default global config
  - Display setup instructions

- [x] **Task 5.3**: Implement `detect` command
  - Run game detection algorithms
  - Display detected games
  - Prompt user to confirm which games to add
  - Create game configuration files

- [x] **Task 5.4**: Implement `list` command
  - List all configured games
  - Display game ID, name, and status
  - Show last sync time
  - Indicate if conflicts exist

- [x] **Task 5.5**: Implement `add` command
  - Interactive prompt for game details
  - Manual path entry for local and cloud
  - Validate paths
  - Create game configuration file

- [x] **Task 5.6**: Implement `sync` command
  - Sync specific game by ID
  - Sync all games with --all flag
  - Show progress during sync
  - Display summary of synced files
  - Handle conflicts (prompt or defer)

- [x] **Task 5.7**: Implement `status` command
  - Show sync status for game(s)
  - Display files that would be synced
  - Show pending conflicts
  - Display last sync time

- [x] **Task 5.8**: Implement interactive conflict resolution in sync command
  - Detect conflicts during sync
  - Prompt user for resolution (keep local, keep cloud, keep both)
  - Apply resolution and continue sync
  - Skip conflict resolution if --force flag is used

### Milestone 6: Testing & Documentation

- [ ] **Task 6.1**: Write unit tests
  - Test configuration parsing
  - Test file comparison logic
  - Test conflict detection
  - Test path detection algorithms
  - Test backup creation

- [ ] **Task 6.2**: Write integration tests
  - Test end-to-end sync workflow
  - Test conflict resolution workflow
  - Test game detection on test data
  - Test cross-platform path handling

- [ ] **Task 6.3**: Manual testing with real games
  - Test with actual Steam games
  - Test with non-Steam games
  - Test on both Linux and Windows
  - Test with cloud-mounted directory (rclone)
  - Test large save files
  - Test conflict scenarios

- [ ] **Task 6.4**: Write user documentation
  - Installation instructions
  - Configuration guide
  - Command reference
  - Troubleshooting guide
  - Examples and common workflows

- [ ] **Task 6.5**: Write developer documentation
  - Code architecture overview
  - Module documentation
  - Contribution guidelines
  - Build and test instructions

### Milestone 7: Polish & Release

- [ ] **Task 7.1**: Error handling improvements
  - Add user-friendly error messages
  - Suggest fixes for common errors
  - Handle edge cases gracefully

- [ ] **Task 7.2**: Performance optimization
  - Optimize directory scanning
  - Optimize file comparison
  - Add progress indicators for slow operations

- [ ] **Task 7.3**: Cross-platform testing
  - Test on multiple Linux distributions
  - Test on Windows 10 and 11
  - Test with different Steam configurations
  - Test with various cloud mount scenarios

- [ ] **Task 7.4**: Create installation package
  - Create pip package (if Python) or binary release (if Rust)
  - Write installation script
  - Create release notes

- [ ] **Task 7.5**: Prepare for automation
  - Test with cron (Linux)
  - Test with Task Scheduler (Windows)
  - Document automation setup
  - Add --quiet mode for scripting

---

## Phase 2: GUI Implementation (Future)

### Milestone 8: GUI Foundation

- [ ] **Task 8.1**: Set up Qt project
  - Choose Qt binding (PyQt/PySide or Qt for Rust)
  - Create GUI project structure
  - Set up build system

- [ ] **Task 8.2**: Refactor core logic for GUI
  - Separate business logic from CLI
  - Create service layer / API
  - Implement event callbacks for progress updates

- [ ] **Task 8.3**: Design GUI mockups
  - Main window layout
  - Game list view
  - Configuration dialogs
  - Sync progress views

### Milestone 9: GUI Implementation

- [ ] **Task 9.1**: Implement main window
  - Game list with status indicators
  - Menu bar and toolbar
  - Status bar

- [ ] **Task 9.2**: Implement game management dialogs
  - Add game dialog
  - Edit game configuration dialog
  - Game detection wizard

- [ ] **Task 9.3**: Implement sync interface
  - Sync progress dialog
  - Conflict resolution dialog
  - Sync history view

- [ ] **Task 9.4**: Implement settings panel
  - Global configuration editor
  - Preferences dialog
  - Theme selection

### Milestone 10: GUI Polish & Release

- [ ] **Task 10.1**: GUI testing
  - Usability testing
  - Cross-platform GUI testing
  - Accessibility testing

- [ ] **Task 10.2**: GUI documentation
  - User guide with screenshots
  - Video tutorials

- [ ] **Task 10.3**: Package GUI application
  - Create installers for Windows
  - Create packages for Linux distributions
  - Create application icons and assets

---

## Optional Enhancements (Backlog)

- [ ] **Enhancement 1**: Automatic file watching
  - Implement file system watcher
  - Auto-sync on save file changes
  - Debounce rapid changes

- [ ] **Enhancement 2**: Advanced sync options
  - File filtering by pattern
  - Selective file sync within game
  - Compression for cloud storage

- [ ] **Enhancement 3**: Additional launcher support
  - Native Steam games detection
  - Epic Games Store detection
  - GOG Galaxy detection
  - Origin/EA App detection

- [ ] **Enhancement 4**: Cloud provider integration
  - Direct S3 integration
  - Direct Google Drive integration
  - Eliminate need for rclone mounting

- [ ] **Enhancement 5**: Sync profiles
  - Multiple cloud destinations
  - Different sync rules per profile
  - Profile switching

- [ ] **Enhancement 6**: Statistics and reporting
  - Sync history tracking
  - Data usage statistics
  - Sync success/failure reports

---

## Progress Summary

**Phase 1 - CLI Implementation**
- Milestone 1: Project Setup & Core Infrastructure (4/4 tasks) ✓
- Milestone 2: Game Detection & Configuration (5/5 tasks) ✓
- Milestone 3: Sync Engine (5/5 tasks) ✓
- Milestone 4: Conflict Resolution (4/4 tasks) ✓
- Milestone 5: CLI Interface (8/8 tasks) ✓
- Milestone 6: Testing & Documentation (0/5 tasks)
- Milestone 7: Polish & Release (0/5 tasks)

**Total Phase 1 Progress: 26/36 tasks completed**

---

## Notes

- Tasks are ordered by dependency - complete earlier tasks before later ones
- Some tasks within a milestone can be done in parallel
- Testing should be done incrementally, not just at Milestone 6
- Update this document as tasks are completed by checking the boxes
- Add notes or blockers for tasks as needed
