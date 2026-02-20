"""
Vial Layer Display - Main Entry Point

This module serves as the application entry point for the Vial Layer Display
desktop application, which shows the current keyboard layer from Vial-compatible
keyboards.
"""

import json
import os
import sys
import time
from typing import NoReturn

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Local imports
from src.config.config_manager import ConfigManager
from src.core.layer_state import LayerState
from src.core.keyboard_monitor import KeyboardMonitor
from src.ui.main_window import MainWindow

LOG_PATH = "debug-e5c2e4.log"


def _dbg(payload: dict) -> None:
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps({**payload, "timestamp": int(time.time() * 1000)}) + "\n")


def main() -> int:
    """
    Initialize and run the Vial Layer Display application.

    This function performs the following steps:
    1. Creates the QApplication instance
    2. Loads application configuration
    3. Creates layer state and keyboard monitor
    4. Creates and displays the main window
    5. Executes the application event loop

    Returns:
        int: Application exit code (0 for success, non-zero for errors)

    Raises:
        Exception: Propagates any unhandled exceptions during initialization
    """
    # #region agent log
    _dbg({"sessionId": "e5c2e4", "runId": "run1", "hypothesisId": "H1", "location": "main.py:main", "message": "main entered, env", "data": {"DISPLAY": os.environ.get("DISPLAY"), "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY"), "QT_QPA_PLATFORM": os.environ.get("QT_QPA_PLATFORM"), "platform": sys.platform}})
    # #endregion
    # Force xcb on Linux when unset so Qt skips broken Wayland (H1/H3); requires libxcb-cursor0 installed
    if sys.platform == "linux" and os.environ.get("QT_QPA_PLATFORM") is None:
        os.environ["QT_QPA_PLATFORM"] = "xcb"
        # Hint if xcb fails: Qt 6.5+ needs libxcb-cursor0
        print(
            "Using Qt platform 'xcb'. If the app fails to start, install: sudo apt install libxcb-cursor0",
            file=sys.stderr,
        )
    try:
        # Create QApplication instance with high DPI scaling support
        # #region agent log
        _dbg({"sessionId": "e5c2e4", "runId": "run1", "hypothesisId": "H5", "location": "main.py:before QApplication", "message": "before QApplication", "data": {}})
        # #endregion
        app = QApplication(sys.argv)
        # #region agent log
        _dbg({"sessionId": "e5c2e4", "runId": "run1", "hypothesisId": "H5", "location": "main.py:after QApplication", "message": "after QApplication", "data": {}})
        # #endregion
        # Note: AA_EnableHighDpiScaling and AA_UseHighDpiPixmaps are deprecated in Qt6
        # High DPI scaling is enabled by default in Qt6

        # Load application configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()

        # Create layer state and keyboard monitor
        layer_state = LayerState()
        keyboard_monitor = KeyboardMonitor(config, layer_state)

        # Create and show main window
        main_window = MainWindow(config_manager, layer_state, keyboard_monitor)
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
