#!/usr/bin/env python3
"""Game Save Sync - Terminal User Interface"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Label, Button, DataTable, ProgressBar
from textual.reactive import reactive
from textual.screen import ModalScreen
from pathlib import Path

from src.config_manager import ConfigManager
from src.logger import init_logger, get_logger
from src.sync_engine import SyncEngine


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
            
            # Debug log result
            with open("/tmp/tui_debug.log", "a") as f:
                f.write(f"Result: {result}\n")
                f.write(f"Actions: {result.get('actions', [])}\n")
            
            # Populate table
            table = self.query_one("#sync-preview-table", DataTable)
            table.add_columns("File", "Action", "Size", "Direction")
            
            actions = result.get("actions", [])
            if actions:
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
            
            # Update table row
            table = event.data_table
            row_data = list(table.get_row(event.row_key))
            row_data[1] = new_action  # Update action column
            row_data[3] = self.get_direction_symbol(new_action)  # Update direction column
            
            table.remove_row(event.row_key)
            table.add_row(*row_data, key=row_key)
            
        except Exception as e:
            pass
    
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
        yield Label("Press Enter to view game details")
        
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
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Settings[/bold]")
        yield Static("─" * 40)
        yield Label("Settings coming soon...")


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
        elif screen_name == "sync":
            content_area.mount(SyncScreen(self.config_manager, self))
        elif screen_name == "settings":
            content_area.mount(SettingsScreen())
        
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
