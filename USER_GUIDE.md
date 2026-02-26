# User Guide - Cloud Game Save Synchronization Tool

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Command Reference](#command-reference)
5. [Common Workflows](#common-workflows)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Cloud storage mounted locally (e.g., via rclone, Seafile client, etc.)
- Steam installed (for game detection)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bliscosque/myCloudGameSave.git
   cd myCloudGameSave
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv ~/vscode/venv
   ```

3. **Install dependencies:**
   ```bash
   ~/vscode/venv/bin/pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   ~/vscode/venv/bin/python gamesync.py --help
   ```

---

## Quick Start

### 1. Initialize Configuration

```bash
~/vscode/venv/bin/python gamesync.py init
```

This creates a configuration directory at `config/<your-hostname>/`.

### 2. Configure Cloud Directory

Edit `config/<your-hostname>/config.toml` and set your cloud directory:

```toml
[general]
cloud_directory = "/path/to/your/cloud/storage/My Games/"
```

### 3. Detect Games

```bash
~/vscode/venv/bin/python gamesync.py detect
```

This auto-detects non-Steam games added to your Steam library.

### 4. List Configured Games

```bash
~/vscode/venv/bin/python gamesync.py list
```

### 5. Sync Your Games

Sync a specific game:
```bash
~/vscode/venv/bin/python gamesync.py sync <game-id>
```

Sync all games:
```bash
~/vscode/venv/bin/python gamesync.py sync --all
```

---

## Configuration

### Global Configuration

Location: `config/<hostname>/config.toml`

```toml
[system]
os = "linux"
hostname = "your-hostname"

[general]
cloud_directory = "/path/to/cloud/My Games/"
backup_directory = "backups"
log_level = "info"

[detection]
steam_enabled = true
custom_paths = []
```

**Key Settings:**
- `cloud_directory`: Path to your cloud-mounted directory (required)
- `backup_directory`: Where backups are stored (relative to config dir)
- `log_level`: Logging verbosity (debug, info, warning, error)

### Per-Game Configuration

Location: `config/<hostname>/games/<game-id>.toml`

```toml
[game]
id = "hellbladegame"
name = "Hellblade Senua's Sacrifice"
platform = "steam"
backup_dir_name = "hellbladegame"

[paths]
local = "/home/user/.local/share/Steam/steamapps/compatdata/.../SaveGames"
cloud = "hellbladegame"

[sync]
enabled = true
exclude_patterns = ["*.tmp", "*.log"]
last_sync = "2026-02-24T10:30:00"

[metadata]
auto_detected = true
last_modified = "2026-02-24T10:30:00"
```

**Key Settings:**
- `enabled`: Enable/disable sync for this game
- `exclude_patterns`: Files to skip during sync
- `local`: Local save directory path
- `backup_dir_name`: Cloud subdirectory name (based on exe filename)

### Editing Configurations

All configuration files are human-readable TOML format. Edit them with any text editor:

```bash
nano config/<hostname>/config.toml
nano config/<hostname>/games/<game-id>.toml
```

---

## Command Reference

### `init` - Initialize Configuration

```bash
gamesync.py init
```

Creates configuration directory structure for your machine.

**Options:** None

---

### `detect` - Auto-Detect Games

```bash
gamesync.py detect [--verbose] [--force]
```

Detects non-Steam games from Steam library and creates configurations.

**Options:**
- `--verbose, -v`: Show detailed detection information
- `--force`: Skip confirmation prompt

**Example:**
```bash
~/vscode/venv/bin/python gamesync.py --verbose detect
```

---

### `list` - List Configured Games

```bash
gamesync.py list [--verbose]
```

Shows all configured games with their status.

**Options:**
- `--verbose, -v`: Show local/cloud paths

**Example:**
```bash
~/vscode/venv/bin/python gamesync.py list
```

**Output:**
```
Configured games (3):

✓ Hellblade Senua's Sacrifice
  ID: hellbladegame
  Last sync: 2026-02-24T10:30:00

✓ METAPHOR.exe
  ID: metaphor
  Last sync: Never
```

---

### `add` - Manually Add Game

```bash
gamesync.py add [game-id] [--force]
```

Manually add a game configuration through interactive prompts.

**Options:**
- `game-id`: Optional game ID (will prompt if not provided)
- `--force`: Overwrite existing configuration

**Example:**
```bash
~/vscode/venv/bin/python gamesync.py add
```

**Prompts:**
1. Game ID (lowercase, use hyphens)
2. Game name
3. Local save path
4. Backup directory name

---

### `sync` - Synchronize Saves

```bash
gamesync.py sync <game-id> [--dry-run] [--verbose] [--force]
gamesync.py sync --all [--dry-run] [--verbose] [--force]
```

Synchronizes game saves between local and cloud.

**Options:**
- `game-id`: Specific game to sync
- `--all`: Sync all enabled games
- `--dry-run`: Show what would be synced without making changes
- `--verbose, -v`: Show detailed sync information
- `--force`: Skip conflict resolution prompts

**Examples:**

Sync one game:
```bash
~/vscode/venv/bin/python gamesync.py sync hellbladegame
```

Sync all games:
```bash
~/vscode/venv/bin/python gamesync.py sync --all
```

Dry-run (preview):
```bash
~/vscode/venv/bin/python gamesync.py --dry-run sync --all
```

**Conflict Resolution:**

If conflicts are detected, you'll be prompted:
```
Conflict: save.dat
Local:  1024 bytes, modified 2026-02-24T10:00:00
Cloud:  2048 bytes, modified 2026-02-24T11:00:00

Choose resolution:
  1. Keep local (copy local → cloud)
  2. Keep cloud (copy cloud → local)
  3. Keep both (rename with suffixes)
  4. Skip this file

Your choice [1-4]:
```

---

### `sync-to-cloud` - One-Way Sync to Cloud

```bash
gamesync.py sync-to-cloud <game-id> [--dry-run] [--force]
```

Syncs game saves from local to cloud (one-way only). Designed for post-game workflow.

**Behavior:**
- Copies files if local is newer than cloud
- Skips if files are equal (timestamp + checksum)
- Skips if cloud is newer (safety check)
- Use `--force` to override safety check

**Options:**
- `game-id`: Game to sync (required)
- `--dry-run`: Preview without copying
- `--force`: Override safety (copy even if cloud is newer)

**Examples:**

After playing a game:
```bash
~/vscode/venv/bin/python gamesync.py sync-to-cloud hellbladegame
```

Preview changes:
```bash
~/vscode/venv/bin/python gamesync.py --dry-run sync-to-cloud hellbladegame
```

Force sync (override safety):
```bash
~/vscode/venv/bin/python gamesync.py --force sync-to-cloud hellbladegame
```

**Output:**
```
============================================================
Syncing to cloud: Hellblade Senua's Sacrifice
============================================================
Local:  /home/user/.local/share/Steam/steamapps/compatdata/.../SaveGames
Cloud:  /home/user/Seafile/My Games/hellbladegame

────────────────────────────────────────────────────────────

✓ Copied to cloud (2 files):
  → save1.sav
  → save2.sav

⊘ Skipped (1 files):
  - save3.sav: files are equal

============================================================
Summary: 2 copied, 1 skipped, 0 errors
============================================================
```

**Exit Codes:**
- `0` - Success (files copied or skipped because equal)
- `1` - Error (configuration missing, permissions, etc.)
- `2` - Safety check prevented sync (cloud has newer files)

**Note:** Exit code 2 means you need to use `--force` if you really want to overwrite newer cloud files.

---

### `sync-from-cloud` - One-Way Sync from Cloud

```bash
gamesync.py sync-from-cloud <game-id> [--dry-run] [--force]
```

Syncs game saves from cloud to local (one-way only). Designed for pre-game workflow.

**Behavior:**
- Copies files if cloud is newer than local
- Skips if files are equal (timestamp + checksum)
- Skips if local is newer (safety check)
- Use `--force` to override safety check

**Options:**
- `game-id`: Game to sync (required)
- `--dry-run`: Preview without copying
- `--force`: Override safety (copy even if local is newer)

**Examples:**

Before playing a game:
```bash
~/vscode/venv/bin/python gamesync.py sync-from-cloud hellbladegame
```

Preview changes:
```bash
~/vscode/venv/bin/python gamesync.py --dry-run sync-from-cloud hellbladegame
```

Force sync (override safety):
```bash
~/vscode/venv/bin/python gamesync.py --force sync-from-cloud hellbladegame
```

**Output:**
```
============================================================
Syncing from cloud: Hellblade Senua's Sacrifice
============================================================
Cloud:  /home/user/Seafile/My Games/hellbladegame
Local:  /home/user/.local/share/Steam/steamapps/compatdata/.../SaveGames

────────────────────────────────────────────────────────────

✓ Copied from cloud (1 files):
  ← save1.sav

⊘ Skipped (2 files):
  - save2.sav: local is newer
  - save3.sav: files are equal

============================================================
Summary: 1 copied, 2 skipped, 0 errors
============================================================
```

**Exit Codes:**
- `0` - Success (files copied or skipped because equal)
- `1` - Error (configuration missing, permissions, etc.)
- `2` - Safety check prevented sync (local has newer files)

**Note:** Exit code 2 means you need to use `--force` if you really want to overwrite newer local files.

---

### `status` - Show Sync Status

```bash
gamesync.py status [game-id] [--verbose]
```

Shows sync status without making changes.

**Options:**
- `game-id`: Check specific game (omit for all games)
- `--verbose, -v`: Show detailed file list

**Example:**
```bash
~/vscode/venv/bin/python gamesync.py status hellbladegame
```

**Output:**
```
============================================================
Hellblade Senua's Sacrifice (hellbladegame)
============================================================
Status: Enabled
Last sync: 2026-02-24T10:30:00

Files to sync:
  → Cloud: 2
  ← Local: 0
  ⚠ Conflicts: 0
  ✓ Up to date: 5
```

---

## Common Workflows

### First-Time Setup

1. Initialize configuration:
   ```bash
   ~/vscode/venv/bin/python gamesync.py init
   ```

2. Edit config to set cloud directory:
   ```bash
   nano config/$(hostname)/config.toml
   ```

3. Detect games:
   ```bash
   ~/vscode/venv/bin/python gamesync.py detect
   ```

4. Review detected games:
   ```bash
   ~/vscode/venv/bin/python gamesync.py list
   ```

5. Perform initial sync:
   ```bash
   ~/vscode/venv/bin/python gamesync.py sync --all
   ```

---

### Daily Usage

Check what needs syncing:
```bash
~/vscode/venv/bin/python gamesync.py status
```

Sync all games:
```bash
~/vscode/venv/bin/python gamesync.py sync --all
```

---

### Pre-Game/Post-Game Workflow (Recommended)

This workflow uses directional sync commands for safer, simpler synchronization.

**Before playing a game:**
```bash
~/vscode/venv/bin/python gamesync.py sync-from-cloud <game-id>
```

This pulls the latest saves from cloud to local. Only copies if cloud is newer.

**After playing a game:**
```bash
~/vscode/venv/bin/python gamesync.py sync-to-cloud <game-id>
```

This pushes your saves to cloud. Only copies if local is newer.

**Example workflow:**
```bash
# Before playing Hellblade
~/vscode/venv/bin/python gamesync.py sync-from-cloud hellbladegame

# Play the game...

# After playing
~/vscode/venv/bin/python gamesync.py sync-to-cloud hellbladegame
```

**Benefits:**
- Simple one-way sync (no conflicts)
- Safe (never overwrites newer files)
- Fast (only copies what changed)
- Clear intent (to-cloud vs from-cloud)

**Integration with Steam (Wrapper Script):**

For automatic pre/post-game sync with error handling, use a wrapper script:

1. Create `steam_wrapper.sh`:
   ```bash
   #!/bin/bash
   
   GAMESYNC_PATH="$HOME/vscode/venv/bin/python $HOME/vscode/myCloudGameSave/gamesync.py"
   GAME_ID="your-game-id"  # CHANGE THIS
   
   echo "=== PRE GAME ==="
   $GAMESYNC_PATH sync-from-cloud "$GAME_ID"
   EXIT_CODE=$?
   
   if [ $EXIT_CODE -eq 2 ]; then
       zenity --error \
           --title="Sync Conflict" \
           --text="Cannot sync from cloud!\n\nYou have newer local saves.\nGame launch aborted." \
           --width=400
       exit 1
   elif [ $EXIT_CODE -ne 0 ]; then
       zenity --question \
           --title="Sync Error" \
           --text="Sync failed. Continue anyway?" \
           --width=300 || exit 1
   fi
   
   echo "=== RUN GAME ==="
   gamemoderun "$@"
   GAME_EXIT_CODE=$?
   
   echo "=== POST GAME ==="
   $GAMESYNC_PATH sync-to-cloud "$GAME_ID"
   EXIT_CODE=$?
   
   if [ $EXIT_CODE -eq 2 ]; then
       zenity --error \
           --title="Sync Conflict" \
           --text="Cloud has newer saves!\nLocal changes NOT uploaded." \
           --width=400
   elif [ $EXIT_CODE -ne 0 ]; then
       zenity --warning \
           --title="Sync Error" \
           --text="Failed to sync. Please sync manually." \
           --width=300
   fi
   
   exit $GAME_EXIT_CODE
   ```

2. Make executable: `chmod +x steam_wrapper.sh`

3. In Steam → Game Properties → Launch Options:
   ```
   /path/to/steam_wrapper.sh %command%
   ```

**Exit Code Handling:**
- Exit code `2` = Safety check failed (newer files on other side) → Aborts pre-game, warns post-game
- Exit code `1` = Configuration error → Prompts user
- Exit code `0` = Success → Continues normally

**Requirements:** Install zenity for GUI dialogs: `sudo dnf install zenity`

---

### Before Playing on Another Machine

Sync from cloud to local:
```bash
~/vscode/venv/bin/python gamesync.py sync --all
```

Or use directional sync for specific game:
```bash
~/vscode/venv/bin/python gamesync.py sync-from-cloud <game-id>
```

This pulls the latest saves from cloud to your local machine.

---

### After Playing

Sync from local to cloud:
```bash
~/vscode/venv/bin/python gamesync.py sync --all
```

Or use directional sync for specific game:
```bash
~/vscode/venv/bin/python gamesync.py sync-to-cloud <game-id>
```

This pushes your updated saves to the cloud.

---

### Adding a New Game Manually

If auto-detection doesn't find your game:

```bash
~/vscode/venv/bin/python gamesync.py add
```

Then provide:
- Game ID: `my-game`
- Game name: `My Game`
- Local path: `/path/to/saves`
- Backup dir: `mygame`

---

### Fixing Incorrect Save Paths

1. Find the game config:
   ```bash
   ls config/$(hostname)/games/
   ```

2. Edit the config:
   ```bash
   nano config/$(hostname)/games/<game-id>.toml
   ```

3. Update the `local` path under `[paths]`

4. Test with dry-run:
   ```bash
   ~/vscode/venv/bin/python gamesync.py --dry-run sync <game-id>
   ```

---

## Troubleshooting

### Game Not Detected

**Problem:** `detect` command doesn't find your game.

**Solutions:**

1. **Check if game is added to Steam:**
   - Open Steam
   - Check if game appears in your library
   - Non-Steam games must be manually added to Steam

2. **Use verbose mode to debug:**
   ```bash
   ~/vscode/venv/bin/python gamesync.py --verbose detect
   ```
   
   Check the output for:
   - Steam path found
   - User IDs detected
   - Games in shortcuts.vdf

3. **Add game manually:**
   ```bash
   ~/vscode/venv/bin/python gamesync.py add
   ```

---

### Wrong Save Location Detected

**Problem:** Tool detects wrong directory for saves.

**Solution:**

Edit the game config manually:
```bash
nano config/$(hostname)/games/<game-id>.toml
```

Update the `local` path to the correct location.

---

### Cloud Directory Not Found

**Problem:** Error: "Cloud directory does not exist"

**Solutions:**

1. **Check if cloud storage is mounted:**
   ```bash
   ls /path/to/cloud/directory
   ```

2. **Update config with correct path:**
   ```bash
   nano config/$(hostname)/config.toml
   ```
   
   Set `cloud_directory` to your mounted cloud path.

3. **For Seafile:** Ensure Seafile client is running and library is synced.

4. **For rclone:** Ensure rclone mount is active:
   ```bash
   rclone mount remote:path /mount/point &
   ```

---

### Permission Denied Errors

**Problem:** Cannot read/write save files.

**Solutions:**

1. **Check file permissions:**
   ```bash
   ls -la /path/to/saves
   ```

2. **Fix permissions if needed:**
   ```bash
   chmod -R u+rw /path/to/saves
   ```

3. **Check if files are in use:**
   - Close the game before syncing
   - Some games lock save files while running

---

### Conflicts Keep Appearing

**Problem:** Same files always show as conflicts.

**Solutions:**

1. **Ensure last_sync is being updated:**
   - Check game config after successful sync
   - `last_sync` field should have recent timestamp

2. **Check system clocks:**
   - Ensure both machines have correct time
   - Time zone differences can cause issues

3. **Use `--force` to skip prompts:**
   ```bash
   ~/vscode/venv/bin/python gamesync.py --force sync <game-id>
   ```
   (This will use automatic conflict resolution)

---

### Sync is Slow

**Problem:** Syncing takes a long time.

**Solutions:**

1. **Check cloud connection:**
   - Slow network can affect sync speed
   - Test cloud mount performance

2. **Exclude unnecessary files:**
   Edit game config and add patterns:
   ```toml
   [sync]
   exclude_patterns = ["*.tmp", "*.log", "*.cache"]
   ```

3. **Sync specific games instead of --all:**
   ```bash
   ~/vscode/venv/bin/python gamesync.py sync <game-id>
   ```

---

## FAQ

### Q: Does this work with native Steam games?

**A:** No, this tool is designed for non-Steam games that have been manually added to Steam. Native Steam games use Steam Cloud.

---

### Q: Can I use this without Steam?

**A:** Yes, but you'll need to add games manually using the `add` command. Auto-detection requires Steam.

---

### Q: What cloud providers are supported?

**A:** Any cloud storage that can be mounted as a local directory:
- Seafile (with sync client)
- rclone (with any supported backend)
- Dropbox, Google Drive, OneDrive (via rclone)
- Network drives (NFS, SMB)

---

### Q: Are subdirectories synced?

**A:** Currently no. Only files in the top-level save directory are synced. This is sufficient for most games. Recursive sync may be added in a future version.

---

### Q: What happens to my saves if sync fails?

**A:** Original files are never deleted. Backups are created before any overwrites. Check `config/<hostname>/backups/` for backup files.

---

### Q: Can I sync the same game on multiple machines?

**A:** Yes! That's the main purpose. Each machine has its own config in `config/<hostname>/`, and they all sync to the same cloud directory.

---

### Q: How do I disable sync for a game temporarily?

**A:** Edit the game config and set:
```toml
[sync]
enabled = false
```

---

### Q: Where are logs stored?

**A:** Logs are in `config/<hostname>/logs/gamesync.log`

View logs:
```bash
tail -f config/$(hostname)/logs/gamesync.log
```

---

### Q: Can I sync to multiple cloud locations?

**A:** Not currently. This is planned for a future version (sync profiles).

---

### Q: Is my data safe?

**A:** 
- Backups are created before overwrites
- Original files are never deleted
- Conflicts are detected and require user action
- All operations are logged
- Dry-run mode available for testing

However, always maintain your own backups of important saves!

---

## Getting Help

- **Issues:** https://github.com/bliscosque/myCloudGameSave/issues
- **Documentation:** See README.md, design.md, and TESTING.md
- **Logs:** Check `config/<hostname>/logs/gamesync.log`

---

## Tips & Best Practices

1. **Always test with --dry-run first** when trying new configurations
2. **Sync before and after playing** to keep saves current
3. **Check status regularly** to catch issues early
4. **Keep backups** of important saves outside the tool
5. **Use verbose mode** when troubleshooting
6. **Close games before syncing** to avoid file locks
7. **Verify save paths** after auto-detection
8. **Monitor logs** for errors or warnings
