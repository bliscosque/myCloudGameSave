#!/usr/bin/env python3
"""Game Save Sync - Terminal User Interface"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static

from src.config_manager import ConfigManager
from src.logger import init_logger, get_logger


class GameSyncTUI(App):
    """Terminal UI for Game Save Synchronization"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #welcome {
        width: 100%;
        height: 100%;
        content-align: center middle;
        text-align: center;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config_manager = None
        self.logger = None
        
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()
        yield Container(
            Static(
                "[bold cyan]Game Save Sync[/bold cyan]\n\n"
                "Welcome to the Terminal User Interface\n\n"
                "Press [bold]q[/bold] to quit",
                id="welcome"
            ),
            id="main-container"
        )
        yield Footer()
        
    def on_mount(self) -> None:
        """Initialize app on mount"""
        self.title = "Game Save Sync"
        self.sub_title = "Cloud Synchronization Tool"
        
        # Initialize config manager
        try:
            self.config_manager = ConfigManager()
            config = self.config_manager.load_config()
            
            # Initialize logger
            log_dir = self.config_manager.get_log_dir()
            self.logger = init_logger(log_dir, config.get("log_level", "INFO"))
            self.logger.info("TUI started")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            
    def action_toggle_dark(self) -> None:
        """Toggle dark mode"""
        self.dark = not self.dark


def main():
    """Main entry point"""
    app = GameSyncTUI()
    app.run()


if __name__ == "__main__":
    main()
