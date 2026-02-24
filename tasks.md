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

- [x] **Task 6.1**: Write unit tests
  - Test configuration parsing
  - Test file comparison logic
  - Test conflict detection
  - Test path detection algorithms
  - Test backup creation

- [x] **Task 6.2**: Write integration tests
  - Test end-to-end sync workflow
  - Test conflict resolution workflow
  - Test game detection on test data
  - Test cross-platform path handling

- [ ] **Task 6.3**: Manual testing with real games
  - ✓ Test with non-Steam games (completed - Hellblade 1/2, Metaphor, Persona 5 Royal)
  - Test on both Linux and Windows (pending - need Windows machine)
  - Test with cloud-mounted directory (pending - need to test with actual Seafile/rclone)
  - Test large save files (pending - need games with large saves)
  - Test conflict scenarios in real usage (pending - need extended usage period)
  
  Note: This task requires extended real-world usage and will be completed over time.
  - Test conflict scenarios

- [x] **Task 6.4**: Write user documentation
  - Installation instructions
  - Configuration guide
  - Command reference
  - Troubleshooting guide
  - Examples and common workflows

- [x] **Task 6.5**: Write developer documentation
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

## Phase 2: TUI Implementation (Textual)

### Milestone 8: TUI Foundation

- [x] **Task 8.1**: Set up Textual framework
  - Add textual to requirements.txt
  - Create TUI entry point (gamesync-tui.py)
  - Set up basic app structure
  - Implement theme and styling

- [x] **Task 8.2**: Create main dashboard layout
  - Header with app title and status
  - Sidebar for navigation
  - Main content area
  - Footer with help/shortcuts

- [x] **Task 8.3**: Implement navigation system
  - Menu items (Dashboard, Games, Sync, Settings)
  - Keyboard shortcuts
  - Screen switching logic

### Milestone 9: Game Management UI

- [x] **Task 9.1**: Implement game list view
  - Display all configured games
  - Show game status (enabled/disabled)
  - Show last sync time
  - Sortable columns

- [x] **Task 9.2**: Implement game details view
  - Show full game information
  - Display local and cloud paths
  - Show sync statistics
  - Edit game configuration

- [ ] **Task 9.3**: Implement add game dialog
  - Interactive form for manual game addition
  - Path browser/selector
  - Validation and error display

- [ ] **Task 9.4**: Implement game detection UI
  - Show detection progress
  - Display detected games with checkboxes
  - Bulk add selected games

### Milestone 10: Sync Operations UI

- [ ] **Task 10.1**: Implement sync dashboard
  - Real-time sync status display
  - Progress bars for active syncs
  - File transfer statistics
  - Recent sync history

- [ ] **Task 10.2**: Implement sync control panel
  - Start/stop sync buttons
  - Select games to sync (checkboxes)
  - Sync all button
  - Dry-run toggle

- [ ] **Task 10.3**: Implement conflict resolution UI
  - Visual diff display for conflicts
  - Side-by-side file comparison
  - Resolution buttons (keep local/cloud/both)
  - Batch conflict resolution

- [ ] **Task 10.4**: Implement sync logs viewer
  - Scrollable log display
  - Filter by level (info/warning/error)
  - Search functionality
  - Export logs

### Milestone 11: Configuration UI

- [ ] **Task 11.1**: Implement settings screen
  - Cloud directory configuration
  - Global sync options
  - Logging preferences
  - Theme selection

- [ ] **Task 11.2**: Implement game configuration editor
  - Edit local/cloud paths
  - Manage exclude patterns
  - Enable/disable sync
  - Advanced options

### Milestone 12: Polish & Integration

- [ ] **Task 12.1**: Add keyboard shortcuts
  - Global shortcuts (quit, help, refresh)
  - Context-specific shortcuts
  - Shortcut help overlay

- [ ] **Task 12.2**: Implement notifications
  - Sync completion notifications
  - Error notifications
  - Conflict alerts

- [ ] **Task 12.3**: Add help system
  - Help overlay/modal
  - Context-sensitive help
  - Tutorial/walkthrough

- [ ] **Task 12.4**: Performance optimization
  - Async operations for UI responsiveness
  - Efficient list rendering
  - Background sync monitoring

- [ ] **Task 12.5**: Testing and bug fixes
  - Test all UI interactions
  - Test keyboard navigation
  - Test on different terminal sizes
  - Fix identified issues

---

## Phase 3: GUI Implementation (Qt)

### Future Milestones (To be detailed later)

- Milestone 13: Qt Framework Setup
- Milestone 14: Main Window & Navigation
- Milestone 15: Game Management GUI
- Milestone 16: Sync Operations GUI
- Milestone 17: System Integration (Tray, Notifications)
- Milestone 18: Advanced Features

---

## Progress Summary

**Phase 1 - CLI Implementation**
- Milestone 1: Project Setup & Core Infrastructure (4/4 tasks) ✓
- Milestone 2: Game Detection & Configuration (5/5 tasks) ✓
- Milestone 3: Sync Engine (5/5 tasks) ✓
- Milestone 4: Conflict Resolution (4/4 tasks) ✓
- Milestone 5: CLI Interface (8/8 tasks) ✓
- Milestone 6: Testing & Documentation (5/5 tasks) ✓
- Milestone 7: Polish & Release (0/5 tasks) [SKIPPED]

**Total Phase 1 Progress: 31/36 tasks completed (86%)**

**Phase 2 - TUI Implementation**
- Milestone 8: TUI Foundation (3/3 tasks) ✓
- Milestone 9: Game Management UI (2/3 tasks)

**Total Phase 2 Progress: 5/18 tasks completed (28%)**

**Phase 2 - TUI Implementation**
- Milestone 8: TUI Foundation (0/3 tasks)
- Milestone 9: Game Management UI (0/4 tasks)
- Milestone 10: Sync Operations UI (0/4 tasks)
- Milestone 11: Configuration UI (0/2 tasks)
- Milestone 12: Polish & Integration (0/5 tasks)

**Total Phase 2 Progress: 0/18 tasks completed (0%)**

**Phase 3 - GUI Implementation (Qt)**
- To be detailed when Phase 2 is complete
- Will include: Qt setup, main window, game management, sync interface, system tray integration

---

## Optional Enhancements (Backlog)

These enhancements can be implemented in any phase as needed:

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

## Notes

- Tasks are ordered by dependency - complete earlier tasks before later ones
- Some tasks within a milestone can be done in parallel
- Testing should be done incrementally, not just at Milestone 6
- Update this document as tasks are completed by checking the boxes
- Add notes or blockers for tasks as needed
- Phase 2 (TUI) and Phase 3 (GUI) tasks are subject to review and adjustment before implementation
