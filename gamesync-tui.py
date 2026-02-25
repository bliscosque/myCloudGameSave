#!/usr/bin/env python3
"""Game Save Sync - Terminal User Interface"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Label, Button, DataTable, ProgressBar, Input, Select
from textual.reactive import reactive
from textual.screen import ModalScreen
from pathlib import Path

from src.config_manager import ConfigManager
from src.logger import init_logger, get_logger
from src.sync_engine import SyncEngine
from src.game_detector import GameDetector


class SyncPreviewScreen(ModalScreen):
    """Modal screen for interactive sync preview and control"""
    
    CSS = """
    SyncPreviewScreen {
        align: center middle;
    }
    
    #sync-preview-container {
        width: 90;
        height: auto;
        max-height: 90%;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }
    
    #sync-preview-table {
        width: 100%;
        height: 20;
    }
    
    #sync-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    
    #progress-container {
        width: 100%;
        height: auto;
        margin-top: 1;
    }
    """
    
    def __init__(self, game_id: str, game_config: dict, config_manager):
        super().__init__()
        self.game_id = game_id
        self.game_config = game_config
        self.config_manager = config_manager
        self.sync_actions = {}  # Store user's action choices per file
        self.file_list = []  # Store file info for sync execution
        self.syncing = False  # Track if sync is in progress
        
    def compose(self) -> ComposeResult:
        game_name = self.game_config.get("game", {}).get("name", self.game_id)
        
        yield Container(
            Label(f"[bold cyan]Sync Preview: {game_name}[/bold cyan]"),
            Static("Running dry-run...", id="status-message"),
            Label("Click on a row to change its action"),
            ScrollableContainer(
                DataTable(id="sync-preview-table", cursor_type="row"),
                id="sync-preview-content"
            ),
            Container(
                ProgressBar(id="sync-progress", total=100, show_eta=False),
                id="progress-container"
            ),
            Horizontal(
                Button("Start Sync", variant="primary", id="start-sync-btn"),
                Button("Cancel", variant="default", id="cancel-sync-btn"),
                id="sync-buttons"
            ),
            id="sync-preview-container"
        )
    
    def on_mount(self) -> None:
        """Run dry-run when modal opens"""
        self.run_dry_run()
    
    def run_dry_run(self) -> None:
        """Execute dry-run and populate table"""
        try:
            # Get paths
            local_dir = Path(self.game_config.get("paths", {}).get("local", ""))
            cloud_base = Path(self.config_manager.load_config().get("general", {}).get("cloud_directory", ""))
            cloud_subdir = self.game_config.get("paths", {}).get("cloud", "")
            cloud_dir = cloud_base / cloud_subdir
            backup_dir = self.config_manager.backups_dir / self.game_id
            last_sync = self.game_config.get("sync", {}).get("last_sync")
            
            # Debug log
            with open("/tmp/tui_debug.log", "a") as f:
                f.write(f"\n=== Dry Run ===\n")
                f.write(f"Game ID: {self.game_id}\n")
                f.write(f"Local dir: {local_dir}\n")
                f.write(f"Cloud dir: {cloud_dir}\n")
                f.write(f"Backup dir: {backup_dir}\n")
                f.write(f"Last sync: {last_sync}\n")
            
            # Run sync engine in dry-run mode
            sync_engine = SyncEngine()
            result = sync_engine.sync_files(
                local_dir=local_dir,
                cloud_dir=cloud_dir,
                backup_dir=backup_dir,
                last_sync=last_sync,
                dry_run=True
            )
            
            # Debug log result with file details
            with open("/tmp/tui_debug.log", "a") as f:
                f.write(f"Result: {result}\n")
                f.write(f"\nFile details:\n")
                for action in result.get("actions", []):
                    f.write(f"  {action.get('filename')}: {action.get('action')} "
                           f"(local: {action.get('local_mtime')}, cloud: {action.get('cloud_mtime')})\n")
                f.write(f"Actions: {result.get('actions', [])}\n")
            
            # Populate table
            table = self.query_one("#sync-preview-table", DataTable)
            table.add_columns("File", "Action", "Size", "Direction")
            
            actions = result.get("actions", [])
            if actions:
                # Sort actions by filename
                actions.sort(key=lambda x: x.get("filename", "").lower())
                
                for idx, action in enumerate(actions):
                    filename = action.get("filename", "")
                    action_type = action.get("action", "")
                    size = action.get("local_size", 0)
                    
                    # Store file info for later sync execution
                    self.file_list.append({
                        "filename": filename,
                        "original_action": action_type,
                        "local_size": action.get("local_size", 0),
                        "cloud_size": action.get("cloud_size", 0),
                        "index": idx
                    })
                    
                    # Determine direction symbol
                    direction = self.get_direction_symbol(action_type)
                    
                    # Format size
                    size_str = self.format_size(size)
                    
                    # Store default action
                    self.sync_actions[f"file_{idx}"] = action_type
                    
                    # Use sequential key to avoid duplicates
                    table.add_row(filename, action_type, size_str, direction, key=f"file_{idx}")
            else:
                table.add_row("No changes needed", "", "", "")
            
            # Update status message
            status = self.query_one("#status-message", Static)
            status.update(f"Found {len(actions)} file(s) to sync")
            
            # Hide progress bar initially
            progress_container = self.query_one("#progress-container")
            progress_container.display = False
            
        except Exception as e:
            # Log error
            with open("/tmp/tui_debug.log", "a") as f:
                import traceback
                f.write(f"Error in dry-run: {e}\n")
                f.write(traceback.format_exc())
            
            table = self.query_one("#sync-preview-table", DataTable)
            table.add_columns("Error", "", "", "")
            table.add_row(f"Error running dry-run: {e}", "", "", "")
    
    def get_direction_symbol(self, action_type: str) -> str:
        """Get direction symbol for action type"""
        if action_type == "copy_to_cloud":
            return "↑ To Cloud"
        elif action_type == "copy_to_local":
            return "↓ From Cloud"
        elif action_type == "conflict":
            return "⚠ Conflict"
        elif action_type == "skip":
            return "⊗ Skip"
        else:
            return "?"
    
    def cycle_action(self, current_action: str) -> str:
        """Cycle to next action: skip → to_cloud → to_local → skip"""
        if current_action == "skip":
            return "copy_to_cloud"
        elif current_action == "copy_to_cloud":
            return "copy_to_local"
        elif current_action == "copy_to_local":
            return "skip"
        else:
            return "skip"
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row click - cycle through actions"""
        if self.syncing:
            return  # Don't allow changes during sync
        
        try:
            row_key = event.row_key.value if hasattr(event.row_key, 'value') else str(event.row_key)
            
            # Get current action and cycle it
            current_action = self.sync_actions.get(row_key, "skip")
            new_action = self.cycle_action(current_action)
            self.sync_actions[row_key] = new_action
            
            # Update table row - get column keys
            table = event.data_table
            columns = list(table.columns.keys())
            
            # Update action column (index 1) and direction column (index 3)
            if len(columns) >= 4:
                table.update_cell(row_key, columns[1], new_action)
                table.update_cell(row_key, columns[3], self.get_direction_symbol(new_action))
            
        except Exception as e:
            # Log error for debugging
            with open("/tmp/tui_debug.log", "a") as f:
                import traceback
                f.write(f"\nError updating cell: {e}\n")
                f.write(traceback.format_exc())
    
    def format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "cancel-sync-btn":
            self.dismiss()
        elif event.button.id == "start-sync-btn":
            if not self.syncing:
                self.execute_sync()
    
    def execute_sync(self) -> None:
        """Execute actual sync with user's choices"""
        self.syncing = True
        
        try:
            # Disable buttons during sync
            start_btn = self.query_one("#start-sync-btn", Button)
            start_btn.disabled = True
            
            # Show progress bar
            progress_container = self.query_one("#progress-container")
            progress_container.display = True
            progress_bar = self.query_one("#sync-progress", ProgressBar)
            
            # Update status
            status = self.query_one("#status-message", Static)
            status.update("Syncing files...")
            
            # Get paths
            local_dir = Path(self.game_config.get("paths", {}).get("local", ""))
            cloud_base = Path(self.config_manager.load_config().get("general", {}).get("cloud_directory", ""))
            cloud_subdir = self.game_config.get("paths", {}).get("cloud", "")
            cloud_dir = cloud_base / cloud_subdir
            backup_dir = self.config_manager.backups_dir / self.game_id
            
            # Create sync engine
            sync_engine = SyncEngine()
            
            # Process each file according to user's choice
            total_files = len(self.file_list)
            synced_count = 0
            error_count = 0
            
            for idx, file_info in enumerate(self.file_list):
                filename = file_info["filename"]
                row_key = f"file_{idx}"
                action = self.sync_actions.get(row_key, "skip")
                
                # Update progress
                progress = int((idx / total_files) * 100)
                progress_bar.update(progress=progress)
                
                if action == "skip":
                    continue
                
                try:
                    local_file = local_dir / filename
                    cloud_file = cloud_dir / filename
                    
                    if action == "copy_to_cloud":
                        # Copy local to cloud
                        if local_file.exists():
                            sync_engine.copy_file(local_file, cloud_file)
                            synced_count += 1
                    elif action == "copy_to_local":
                        # Copy cloud to local
                        if cloud_file.exists():
                            sync_engine.copy_file(cloud_file, local_file)
                            synced_count += 1
                            
                except Exception as e:
                    error_count += 1
            
            # Update last_sync timestamp
            from datetime import datetime
            self.game_config["sync"]["last_sync"] = datetime.now().isoformat()
            self.config_manager.save_game_config(self.game_id, self.game_config)
            
            # Complete
            progress_bar.update(progress=100)
            status.update(f"Sync complete! {synced_count} files synced, {error_count} errors")
            
            # Re-enable cancel button (now acts as close)
            cancel_btn = self.query_one("#cancel-sync-btn", Button)
            cancel_btn.label = "Close"
            
        except Exception as e:
            status = self.query_one("#status-message", Static)
            status.update(f"Sync failed: {e}")
        
        finally:
            self.syncing = False


class Sidebar(Vertical):
    """Navigation sidebar"""
    
    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Navigation[/bold cyan]")
        yield Static("─" * 20)
        yield Button("Dashboard", id="nav-dashboard", variant="primary")
        yield Button("Games", id="nav-games")
        yield Button("Sync", id="nav-sync")
        yield Button("Settings", id="nav-settings")
        yield Static("")
        yield Button("Quit", id="nav-quit", variant="error")


class Dashboard(Vertical):
    """Main dashboard content"""
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Dashboard[/bold]")
        yield Static("─" * 40)
        yield Label("Welcome to Game Save Sync")
        yield Static("")
        
        # Get actual game count and last sync
        game_count = 0
        last_sync = "Never"
        
        if self.config_manager:
            try:
                games = self.config_manager.list_games()
                game_count = len(games)
                
                # Find most recent sync
                from datetime import datetime
                most_recent = None
                
                for game_id in games:
                    game_config = self.config_manager.load_game_config(game_id)
                    sync_time = game_config.get("sync", {}).get("last_sync")
                    
                    if sync_time:
                        try:
                            dt = datetime.fromisoformat(sync_time)
                            if most_recent is None or dt > most_recent:
                                most_recent = dt
                        except:
                            pass
                
                if most_recent:
                    last_sync = most_recent.strftime("%Y-%m-%d %H:%M")
                    
            except:
                pass
        
        yield Label("Status: Ready")
        yield Label(f"Configured Games: {game_count}")
        yield Label(f"Last Sync: {last_sync}")


class GameDetailsScreen(ModalScreen):
    """Modal screen showing game details"""
    
    CSS = """
    GameDetailsScreen {
        align: center middle;
    }
    
    #details-container {
        width: 80;
        height: auto;
        max-height: 90%;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }
    
    #details-content {
        width: 100%;
        height: auto;
        max-height: 30;
    }
    
    #details-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """
    
    def __init__(self, game_id: str, game_config: dict):
        super().__init__()
        self.game_id = game_id
        self.game_config = game_config
    
    def compose(self) -> ComposeResult:
        game = self.game_config.get("game", {})
        paths = self.game_config.get("paths", {})
        sync = self.game_config.get("sync", {})
        metadata = self.game_config.get("metadata", {})
        
        # Format last sync
        last_sync = sync.get("last_sync", "Never")
        if last_sync and last_sync != "Never":
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_sync)
                last_sync = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        # Build details text
        details = f"""[bold cyan]{game.get('name', self.game_id)}[/bold cyan]

[bold]Game Information:[/bold]
  ID: {game.get('id', self.game_id)}
  Platform: {game.get('platform', 'N/A')}
  Steam App ID: {game.get('steam_app_id', 'N/A')}
  Executable: {game.get('exe', 'N/A')}

[bold]Paths:[/bold]
  Local: {paths.get('local', 'N/A')}
  Cloud: {paths.get('cloud', 'N/A')}

[bold]Sync Configuration:[/bold]
  Enabled: {'Yes' if sync.get('enabled', True) else 'No'}
  Last Sync: {last_sync}
  Exclude Patterns: {', '.join(sync.get('exclude_patterns', [])) or 'None'}

[bold]Metadata:[/bold]
  Auto-detected: {'Yes' if metadata.get('auto_detected', False) else 'No'}
  Last Modified: {metadata.get('last_modified', 'N/A')}
"""
        
        yield Container(
            ScrollableContainer(
                Static(details, id="details-content"),
            ),
            Horizontal(
                Button("Close", variant="primary", id="close-btn"),
                id="details-buttons"
            ),
            id="details-container"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Close the modal"""
        self.dismiss()


class GamesScreen(Vertical):
    """Games management screen"""
    
    def __init__(self, config_manager, parent_app):
        super().__init__()
        self.config_manager = config_manager
        self.parent_app = parent_app
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Games[/bold]")
        yield Static("─" * 40)
        yield Label("Press Enter to view details")
        yield Horizontal(
            Button("Add Game", id="add-game-btn", variant="success"),
            Button("Detect Games", id="detect-games-btn", variant="primary"),
        )
        yield Static("")
        
        # Create data table
        table = DataTable(cursor_type="row")
        table.add_columns("Game ID", "Name", "Status", "Last Sync")
        
        # Load games from config
        if self.config_manager:
            try:
                games = self.config_manager.list_games()
                for game_id in games:
                    game_config = self.config_manager.load_game_config(game_id)
                    
                    name = game_config.get("game", {}).get("name", game_id)
                    enabled = game_config.get("sync", {}).get("enabled", True)
                    status = "✓ Enabled" if enabled else "✗ Disabled"
                    last_sync = game_config.get("sync", {}).get("last_sync", "Never")
                    
                    # Format last_sync if it's a timestamp
                    if last_sync and last_sync != "Never":
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(last_sync)
                            last_sync = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    table.add_row(game_id, name, status, last_sync)
                
                if not games:
                    table.add_row("", "No games configured", "", "")
            except Exception as e:
                table.add_row("", f"Error loading games: {e}", "", "")
        
        yield table
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection - show game details"""
        try:
            table = event.data_table
            row_key = event.row_key
            
            # Get game_id from first column
            row_data = table.get_row(row_key)
            game_id = str(row_data[0])
            
            # Skip if empty or error row
            if not game_id or not game_id.strip() or game_id == "":
                return
                
            # Load and show game config
            game_config = self.config_manager.load_game_config(game_id)
            self.parent_app.push_screen(GameDetailsScreen(game_id, game_config))
        except Exception as e:
            # Silently ignore errors (e.g., clicking on "No games" row)
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "add-game-btn":
            self.parent_app.push_screen(AddGameDialog(self.config_manager, self.parent_app))
        elif event.button.id == "detect-games-btn":
            self.parent_app.push_screen(DetectGamesDialog(self.config_manager, self.parent_app))


class DetectGamesDialog(ModalScreen):
    """Modal dialog for detecting games from Steam"""
    
    CSS = """
    DetectGamesDialog {
        align: center middle;
    }
    
    #detect-games-container {
        width: 80;
        height: 80%;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }
    
    #detect-progress {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    
    #detected-games-table {
        width: 100%;
        height: 100%;
    }
    
    #detect-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """
    
    def __init__(self, config_manager, parent_app):
        super().__init__()
        self.config_manager = config_manager
        self.parent_app = parent_app
        self.detected_games = []
        self.selected_games = set()
    
    def compose(self) -> ComposeResult:
        from textual.widgets import Checkbox
        
        yield Container(
            Label("[bold cyan]Detect Games from Steam[/bold cyan]"),
            Static("Detecting games...", id="detect-progress"),
            ScrollableContainer(
                DataTable(id="detected-games-table", cursor_type="row"),
                id="detect-scroll"
            ),
            Horizontal(
                Button("Add Selected", variant="success", id="add-selected-btn", disabled=True),
                Button("Select All", variant="default", id="select-all-btn"),
                Button("Cancel", variant="default", id="cancel-detect-btn"),
                id="detect-buttons"
            ),
            id="detect-games-container"
        )
    
    def on_mount(self) -> None:
        """Start detection when modal opens"""
        self.detect_games()
    
    def detect_games(self) -> None:
        """Run game detection"""
        try:
            progress = self.query_one("#detect-progress", Static)
            progress.update("Detecting games from Steam...")
            
            # Run detection
            detector = GameDetector(config_manager=self.config_manager)
            detected = detector.detect_non_steam_games()
            
            # Filter out already configured games
            existing_games = self.config_manager.list_games()
            new_games = []
            
            for game_info in detected:
                game_id = detector.create_game_id(game_info)
                if game_id not in existing_games:
                    new_games.append(game_info)
            
            self.detected_games = new_games
            
            # Populate table
            table = self.query_one("#detected-games-table", DataTable)
            table.add_columns("☐", "Game Name", "Executable", "Save Locations")
            
            if new_games:
                for idx, game_info in enumerate(new_games):
                    name = game_info.get("name", "Unknown")
                    exe = game_info.get("exe", "").split("/")[-1].split("\\")[-1]
                    
                    # Detect save locations
                    save_locs = detector.detect_save_locations(game_info)
                    save_count = f"{len(save_locs)} found" if save_locs else "None"
                    
                    table.add_row("☐", name, exe, save_count, key=f"game_{idx}")
                
                progress.update(f"Found {len(new_games)} new game(s)")
                
                # Enable buttons
                add_btn = self.query_one("#add-selected-btn", Button)
                add_btn.disabled = False
            else:
                table.add_row("", "No new games detected", "", "")
                progress.update("No new games found (all games already configured)")
            
        except Exception as e:
            progress = self.query_one("#detect-progress", Static)
            progress.update(f"[red]Error detecting games: {e}[/red]")
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Toggle game selection"""
        try:
            row_key = event.row_key.value if hasattr(event.row_key, 'value') else str(event.row_key)
            
            # Toggle selection
            if row_key in self.selected_games:
                self.selected_games.remove(row_key)
                checkbox = "☐"
            else:
                self.selected_games.add(row_key)
                checkbox = "☑"
            
            # Update checkbox in table
            table = event.data_table
            columns = list(table.columns.keys())
            table.update_cell(row_key, columns[0], checkbox)
            
        except Exception as e:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "cancel-detect-btn":
            self.dismiss()
        elif event.button.id == "select-all-btn":
            self.toggle_select_all()
        elif event.button.id == "add-selected-btn":
            self.add_selected_games()
    
    def toggle_select_all(self) -> None:
        """Select or deselect all games"""
        table = self.query_one("#detected-games-table", DataTable)
        columns = list(table.columns.keys())
        
        # Check if all are selected
        all_selected = len(self.selected_games) == len(self.detected_games)
        
        if all_selected:
            # Deselect all
            self.selected_games.clear()
            checkbox = "☐"
            btn_label = "Select All"
        else:
            # Select all
            self.selected_games = {f"game_{i}" for i in range(len(self.detected_games))}
            checkbox = "☑"
            btn_label = "Deselect All"
        
        # Update all checkboxes
        for i in range(len(self.detected_games)):
            row_key = f"game_{i}"
            table.update_cell(row_key, columns[0], checkbox)
        
        # Update button label
        btn = self.query_one("#select-all-btn", Button)
        btn.label = btn_label
    
    def add_selected_games(self) -> None:
        """Add selected games to configuration"""
        if not self.selected_games:
            self.app.notify("No games selected", severity="warning")
            return
        
        try:
            detector = GameDetector(config_manager=self.config_manager)
            added_count = 0
            
            for row_key in self.selected_games:
                idx = int(row_key.split("_")[1])
                game_info = self.detected_games[idx]
                
                # Detect save locations
                save_locs = detector.detect_save_locations(game_info)
                
                if save_locs:
                    # Save game config
                    detector.save_game_config(game_info, save_locs, overwrite=False)
                    added_count += 1
            
            # Show success
            self.app.notify(f"Added {added_count} game(s) successfully!")
            self.dismiss()
            
            # Refresh games list
            self.parent_app.switch_screen("games")
            
        except Exception as e:
            self.app.notify(f"Error adding games: {e}", severity="error")


class AddGameDialog(ModalScreen):
    """Modal dialog for adding a game manually"""
    
    CSS = """
    AddGameDialog {
        align: center middle;
    }
    
    #add-game-container {
        width: 70;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }
    
    .form-row {
        height: auto;
        margin-bottom: 1;
    }
    
    #add-game-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """
    
    def __init__(self, config_manager, parent_app):
        super().__init__()
        self.config_manager = config_manager
        self.parent_app = parent_app
    
    def compose(self) -> ComposeResult:
        yield Container(
            Label("[bold cyan]Add Game Manually[/bold cyan]"),
            Static("─" * 60),
            Vertical(
                Label("Game ID (lowercase, no spaces):"),
                Input(placeholder="e.g., mygame", id="game-id-input"),
                classes="form-row"
            ),
            Vertical(
                Label("Game Name:"),
                Input(placeholder="e.g., My Game", id="game-name-input"),
                classes="form-row"
            ),
            Vertical(
                Label("Local Save Path:"),
                Input(placeholder="/path/to/local/saves", id="local-path-input"),
                classes="form-row"
            ),
            Vertical(
                Label("Cloud Directory Name:"),
                Input(placeholder="e.g., mygame", id="cloud-dir-input"),
                classes="form-row"
            ),
            Static("", id="error-message"),
            Horizontal(
                Button("Add Game", variant="success", id="submit-btn"),
                Button("Cancel", variant="default", id="cancel-btn"),
                id="add-game-buttons"
            ),
            id="add-game-container"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "cancel-btn":
            self.dismiss()
        elif event.button.id == "submit-btn":
            self.add_game()
    
    def add_game(self) -> None:
        """Validate and add the game"""
        try:
            # Get input values
            game_id = self.query_one("#game-id-input", Input).value.strip().lower()
            game_name = self.query_one("#game-name-input", Input).value.strip()
            local_path = self.query_one("#local-path-input", Input).value.strip()
            cloud_dir = self.query_one("#cloud-dir-input", Input).value.strip()
            
            # Validate
            error_msg = self.query_one("#error-message", Static)
            
            if not game_id:
                error_msg.update("[red]Game ID is required[/red]")
                return
            
            if not game_id.replace("_", "").replace("-", "").isalnum():
                error_msg.update("[red]Game ID must be alphanumeric (with _ or -)[/red]")
                return
            
            if not game_name:
                error_msg.update("[red]Game Name is required[/red]")
                return
            
            if not local_path:
                error_msg.update("[red]Local Save Path is required[/red]")
                return
            
            if not cloud_dir:
                error_msg.update("[red]Cloud Directory Name is required[/red]")
                return
            
            # Check if game already exists
            existing_games = self.config_manager.list_games()
            if game_id in existing_games:
                error_msg.update("[red]Game ID already exists[/red]")
                return
            
            # Create game config
            game_config = {
                "game": {
                    "id": game_id,
                    "name": game_name,
                    "platform": "manual",
                    "backup_dir_name": cloud_dir
                },
                "paths": {
                    "local": local_path,
                    "cloud": cloud_dir
                },
                "sync": {
                    "enabled": True,
                    "exclude_patterns": ["*.tmp", "*.log"],
                    "last_sync": None
                },
                "metadata": {
                    "auto_detected": False,
                    "last_modified": None
                }
            }
            
            # Save game config
            self.config_manager.save_game_config(game_id, game_config)
            
            # Show success and close
            self.app.notify(f"Game '{game_name}' added successfully!")
            self.dismiss()
            
            # Refresh games list
            self.parent_app.switch_screen("games")
            
        except Exception as e:
            error_msg = self.query_one("#error-message", Static)
            error_msg.update(f"[red]Error: {e}[/red]")


class SyncScreen(Vertical):
    """Sync screen"""
    
    def __init__(self, config_manager, parent_app):
        super().__init__()
        self.config_manager = config_manager
        self.parent_app = parent_app
        self.game_id_map = {}  # Map row keys to game IDs
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Sync Dashboard[/bold]")
        yield Static("─" * 40)
        yield Label("Press Enter on a game to start sync")
        yield Static("")
        
        # Game list for syncing
        yield Label("[bold cyan]Games[/bold cyan]")
        table = DataTable(cursor_type="row", id="sync-games-table")
        table.add_columns("Game", "Status", "Last Sync")
        
        # Load games
        if self.config_manager:
            try:
                games = self.config_manager.list_games()
                row_num = 0
                for game_id in games:
                    game_config = self.config_manager.load_game_config(game_id)
                    
                    name = game_config.get("game", {}).get("name", game_id)
                    enabled = game_config.get("sync", {}).get("enabled", True)
                    status = "✓ Enabled" if enabled else "✗ Disabled"
                    last_sync = game_config.get("sync", {}).get("last_sync", "Never")
                    
                    if last_sync and last_sync != "Never":
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(last_sync)
                            last_sync = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    # Use row number as key and map it to game_id
                    row_key = f"row_{row_num}"
                    self.game_id_map[row_key] = game_id
                    table.add_row(name, status, last_sync, key=row_key)
                    row_num += 1
                
                if not games:
                    table.add_row("No games configured", "", "")
            except Exception as e:
                table.add_row(f"Error: {e}", "", "")
        
        yield table
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection - open sync preview"""
        # Only handle events from sync-games-table
        if event.data_table.id != "sync-games-table":
            return
        
        try:
            # Get game_id from mapping - row_key.value gives us the actual key string
            row_key = event.row_key.value if hasattr(event.row_key, 'value') else str(event.row_key)
            game_id = self.game_id_map.get(row_key)
            
            if not game_id:
                self.app.notify(f"No game_id found", severity="warning")
                return
            
            # Load game config and open sync preview
            game_config = self.config_manager.load_game_config(game_id)
            self.parent_app.push_screen(
                SyncPreviewScreen(game_id, game_config, self.config_manager)
            )
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")


class SettingsScreen(Vertical):
    """Settings screen"""
    
    def __init__(self, parent_app):
        super().__init__()
        self.parent_app = parent_app
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Settings[/bold]")
        yield Static("─" * 40)
        yield Static("")
        yield Button("View Logs", id="view-logs-btn", variant="primary")
        yield Static("")
        yield Label("Other settings coming soon...")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "view-logs-btn":
            self.parent_app.push_screen(LogViewerScreen(self.parent_app.config_manager))


class LogViewerScreen(ModalScreen):
    """Modal screen for viewing logs"""
    
    CSS = """
    LogViewerScreen {
        align: center middle;
    }
    
    #log-viewer-container {
        width: 90;
        height: 90%;
        background: $panel;
        border: thick $primary;
        padding: 1 2;
    }
    
    #log-content {
        width: 100%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }
    
    #log-controls {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    
    #log-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.log_level_filter = "all"
        self.search_term = ""
    
    def compose(self) -> ComposeResult:
        from textual.widgets import Input, Select
        
        yield Container(
            Label("[bold cyan]Log Viewer[/bold cyan]"),
            Horizontal(
                Select(
                    [("All Levels", "all"), ("Info", "info"), ("Warning", "warning"), ("Error", "error")],
                    value="all",
                    id="log-level-select"
                ),
                Input(placeholder="Search logs...", id="log-search-input"),
                id="log-controls"
            ),
            ScrollableContainer(
                Static("", id="log-content"),
                id="log-scroll"
            ),
            Horizontal(
                Button("Refresh", variant="primary", id="refresh-logs-btn"),
                Button("Export", variant="default", id="export-logs-btn"),
                Button("Close", variant="default", id="close-logs-btn"),
                id="log-buttons"
            ),
            id="log-viewer-container"
        )
    
    def on_mount(self) -> None:
        """Load logs when modal opens"""
        self.load_logs()
    
    def load_logs(self) -> None:
        """Load and display logs"""
        try:
            log_file = self.config_manager.logs_dir / "gamesync.log"
            
            if not log_file.exists():
                content = self.query_one("#log-content", Static)
                content.update("[yellow]No log file found[/yellow]")
                return
            
            # Read log file
            with open(log_file, "r") as f:
                lines = f.readlines()
            
            # Filter by level
            filtered_lines = []
            for line in lines:
                if self.log_level_filter == "all":
                    filtered_lines.append(line)
                elif self.log_level_filter.upper() in line:
                    filtered_lines.append(line)
            
            # Filter by search term
            if self.search_term:
                filtered_lines = [l for l in filtered_lines if self.search_term.lower() in l.lower()]
            
            # Display (last 1000 lines)
            display_lines = filtered_lines[-1000:]
            log_text = "".join(display_lines)
            
            content = self.query_one("#log-content", Static)
            content.update(log_text if log_text else "[yellow]No matching logs[/yellow]")
            
        except Exception as e:
            content = self.query_one("#log-content", Static)
            content.update(f"[red]Error loading logs: {e}[/red]")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle log level filter change"""
        self.log_level_filter = event.value
        self.load_logs()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input change"""
        if event.input.id == "log-search-input":
            self.search_term = event.value
            self.load_logs()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        if event.button.id == "close-logs-btn":
            self.dismiss()
        elif event.button.id == "refresh-logs-btn":
            self.load_logs()
        elif event.button.id == "export-logs-btn":
            self.export_logs()
    
    def export_logs(self) -> None:
        """Export filtered logs to file"""
        try:
            from datetime import datetime
            export_file = Path.home() / f"gamesync_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            content = self.query_one("#log-content", Static)
            with open(export_file, "w") as f:
                f.write(content.renderable)
            
            self.app.notify(f"Logs exported to {export_file}")
        except Exception as e:
            self.app.notify(f"Export failed: {e}", severity="error")


class GameSyncTUI(App):
    """Terminal UI for Game Save Synchronization"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Sidebar {
        width: 25;
        height: 100%;
        background: $panel;
        padding: 1;
        border-right: solid $primary;
    }
    
    Sidebar Button {
        width: 100%;
        margin-bottom: 1;
    }
    
    DataTable {
        height: 100%;
    }
    
    Dashboard, GamesScreen, SyncScreen, SettingsScreen {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
    }
    
    #content-area {
        width: 100%;
        height: 100%;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("1", "show_dashboard", "Dashboard"),
        ("2", "show_games", "Games"),
        ("3", "show_sync", "Sync"),
        ("4", "show_settings", "Settings"),
        ("up", "focus_previous", "Previous"),
        ("down", "focus_next", "Next"),
        ("left", "focus_sidebar", "Sidebar"),
        ("right", "focus_content", "Content"),
    ]
    
    current_screen = reactive("dashboard")
    
    def __init__(self):
        super().__init__()
        # Initialize config manager early
        try:
            self.config_manager = ConfigManager()
        except:
            self.config_manager = None
        self.logger = None
        
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header(show_clock=True)
        yield Horizontal(
            Sidebar(),
            Container(
                Dashboard(self.config_manager),
                id="content-area"
            ),
            id="main-container"
        )
        yield Footer()
        
    def on_mount(self) -> None:
        """Initialize app on mount"""
        self.title = "Game Save Sync"
        self.sub_title = "Cloud Synchronization Tool"
        
        # Initialize logger (config_manager already initialized in __init__)
        try:
            if self.config_manager:
                config = self.config_manager.load_config()
                self.logger = init_logger(
                    self.config_manager.logs_dir, 
                    config.get("general", {}).get("log_level", "INFO").upper()
                )
                self.logger.info("TUI started")
        except Exception as e:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id
        
        if button_id == "nav-dashboard":
            self.switch_screen("dashboard")
        elif button_id == "nav-games":
            self.switch_screen("games")
        elif button_id == "nav-sync":
            self.switch_screen("sync")
        elif button_id == "nav-settings":
            self.switch_screen("settings")
        elif button_id == "nav-quit":
            self.exit()
    
    def switch_screen(self, screen_name: str) -> None:
        """Switch to a different screen"""
        self.current_screen = screen_name
        
        # Get content area and clear it
        content_area = self.query_one("#content-area")
        content_area.remove_children()
        
        # Mount new screen
        if screen_name == "dashboard":
            content_area.mount(Dashboard(self.config_manager))
        elif screen_name == "games":
            content_area.mount(GamesScreen(self.config_manager, self))
            # Auto-focus on games table
            self.set_timer(0.1, lambda: self.action_focus_content())
        elif screen_name == "sync":
            content_area.mount(SyncScreen(self.config_manager, self))
            # Auto-focus on sync table
            self.set_timer(0.1, lambda: self.action_focus_content())
        elif screen_name == "settings":
            content_area.mount(SettingsScreen(self))
        
        # Update button variants
        for button in self.query("Sidebar Button"):
            if button.id == f"nav-{screen_name}":
                button.variant = "primary"
            else:
                button.variant = "default"
    
    def action_show_dashboard(self) -> None:
        """Show dashboard screen"""
        self.switch_screen("dashboard")
    
    def action_show_games(self) -> None:
        """Show games screen"""
        self.switch_screen("games")
    
    def action_show_sync(self) -> None:
        """Show sync screen"""
        self.switch_screen("sync")
    
    def action_show_settings(self) -> None:
        """Show settings screen"""
        self.switch_screen("settings")
    
    def action_focus_sidebar(self) -> None:
        """Focus on sidebar navigation"""
        try:
            sidebar = self.query_one("Sidebar")
            buttons = sidebar.query("Button")
            if buttons:
                buttons.first().focus()
        except:
            pass
    
    def action_focus_content(self) -> None:
        """Focus on content area"""
        try:
            content = self.query_one("#content-area")
            # Try to focus on DataTable if present, otherwise any focusable widget
            tables = content.query("DataTable")
            if tables:
                tables.first().focus()
            else:
                focusable = content.query("Button, Input, DataTable")
                if focusable:
                    focusable.first().focus()
        except:
            pass


def main():
    """Main entry point"""
    app = GameSyncTUI()
    app.run()


if __name__ == "__main__":
    main()
