"""
Vial Layer Display - Main Entry Point

This module serves as the application entry point for the Vial Layer Display
desktop application, which shows the current keyboard layer from Vial-compatible
keyboards.
"""

import sys
from typing import NoReturn

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Local imports - these modules will be created later
from src.config.config_manager import ConfigManager
from src.ui.main_window import MainWindow


def main() -> int:
    """
    Initialize and run the Vial Layer Display application.

    This function performs the following steps:
    1. Creates the QApplication instance
    2. Loads application configuration
    3. Creates and displays the main window
    4. Executes the application event loop

    Returns:
        int: Application exit code (0 for success, non-zero for errors)

    Raises:
        Exception: Propagates any unhandled exceptions during initialization
    """
    try:
        # Create QApplication instance with high DPI scaling support
        app = QApplication(sys.argv)
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        # Load application configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()

        # Create and show main window
        main_window = MainWindow(config)
        main_window.show()

        # Execute application event loop
        exit_code = app.exec()

        return exit_code

    except Exception as e:
        # Print error to stderr for proper error handling
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
