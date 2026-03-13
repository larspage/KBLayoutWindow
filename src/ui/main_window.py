"""
Main Application Window

This module provides the main application window for the Vial Layer Display.
It integrates the layer display widget, keyboard monitor, and system tray.

Classes:
    MainWindow: Main application window with system tray integration
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QLabel, QMenu, QSystemTrayIcon,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QCloseEvent

from src.ui.keyboard_widget import KeyboardWidget
from src.ui.preview_window import LayerPreviewWindow
from src.core.layer_state import LayerState
from src.core.keyboard_monitor import KeyboardMonitor
from src.config.config_manager import ConfigManager


class MainWindow(QMainWindow):
    """
    Main application window for Vial Layer Display.
    
    This window provides:
    - Layer display widget with zoom controls
    - System tray integration
    - Menu bar with settings and quit options
    - Window management (always-on-top, minimize to tray)
    
    Signals:
        closed: Emitted when window is closed
    
    Attributes:
        config_manager: Configuration manager instance
        layer_state: Layer state manager
        keyboard_monitor: Keyboard monitor instance
        layer_display: Layer display widget
    """
    
    # Signals
    closed = pyqtSignal()
    
    # Default window settings
    DEFAULT_WIDTH = 200
    DEFAULT_HEIGHT = 150
    
    def __init__(
        self,
        config_manager: ConfigManager,
        layer_state: LayerState,
        keyboard_monitor: KeyboardMonitor,
        parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the main window.
        
        Args:
            config_manager: Configuration manager instance
            layer_state: Layer state manager
            keyboard_monitor: Keyboard monitor instance
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        # Store references
        self._config_manager = config_manager
        self._layer_state = layer_state
        self._keyboard_monitor = keyboard_monitor
        
        # Load configuration
        self._config = config_manager.load_config()
        
        # Setup window
        self._setup_window()
        
        # Setup UI
        self._setup_ui()
        
        # Setup system tray
        self._setup_system_tray()
        
        # Connect signals
        self._connect_signals()
        
        # Start keyboard monitoring
        self._keyboard_monitor.start()
    
    def _setup_window(self) -> None:
        """Setup window properties from configuration."""
        # Window title
        self.setWindowTitle("Vial Layer Display")
        
        # Window size
        window_config = self._config.get("window", {})
        self.resize(
            window_config.get("width", self.DEFAULT_WIDTH),
            window_config.get("height", self.DEFAULT_HEIGHT)
        )
        # Window position
        x = window_config.get("x")
        y = window_config.get("y")
        if x is not None and y is not None:
            self.move(x, y)
        
        # Window flags
        flags = Qt.WindowType.Window
        if window_config.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        if window_config.get("frameless", False):
            flags |= Qt.WindowType.FramelessWindowHint
        self.setWindowFlags(flags)
        
        # Window opacity
        opacity = window_config.get("opacity", 1.0)
        self.setWindowOpacity(max(0.3, min(1.0, opacity)))
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self._main_layout = QVBoxLayout()
        self._main_layout.setSpacing(0)

        # Keyboard widget — full layout with layer tabs and zoom controls
        self._kb_widget = KeyboardWidget(parent=central_widget)
        self._main_layout.addWidget(self._kb_widget)

        # Status label — doubles as the bottom margin; height sets the padding unit
        self._status_label = QLabel("Initializing...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("color: #888; font-size: 10px;")
        self._main_layout.addWidget(self._status_label)

        central_widget.setLayout(self._main_layout)

        # Apply equal margins once the label height is known
        self._apply_margins()
    
    def _setup_system_tray(self) -> None:
        """Setup system tray icon and menu."""
        # Create system tray icon
        self._tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu(self)
        
        # Show/Hide action
        self._show_hide_action = QAction("Hide", self)
        self._show_hide_action.triggered.connect(self._toggle_window_visibility)
        tray_menu.addAction(self._show_hide_action)
        
        # Separator
        tray_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings)
        tray_menu.addAction(settings_action)
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        tray_menu.addAction(about_action)
        
        # Separator
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)
        
        # Set menu
        self._tray_icon.setContextMenu(tray_menu)
        
        # Set icon (placeholder - will need actual icon file)
        # self._tray_icon.setIcon(QIcon("assets/icons/app_icon.png"))
        
        # Show tray icon
        self._tray_icon.show()
        
        # Connect tray icon activation
        self._tray_icon.activated.connect(self._tray_icon_activated)
    
    def _connect_signals(self) -> None:
        """Connect signals from other components."""
        # Layer state changes
        self._layer_state.layer_changed.connect(self._on_layer_changed)
        self._layer_state.keymap_loaded.connect(self._on_keymap_loaded)

        # Keyboard monitor signals
        self._keyboard_monitor.device_found.connect(self._on_device_found)
        self._keyboard_monitor.device_lost.connect(self._on_device_lost)
        self._keyboard_monitor.error.connect(self._on_error)

        # Auto-fit window when keyboard layout changes size
        self._kb_widget.layout_resized.connect(self._fit_to_keyboard)
    
    def _on_layer_changed(self, layer: int) -> None:
        self._kb_widget.set_active_layer(layer)

    def _on_keymap_loaded(self) -> None:
        key_defs, all_keymaps = self._layer_state.get_keyboard_data()
        num_layers = len(all_keymaps)
        self._kb_widget.set_keyboard_data(key_defs, all_keymaps, num_layers)

    def _apply_margins(self) -> None:
        """Set equal padding on all sides using the status label height as the unit."""
        s = self._status_label.sizeHint().height()
        if s <= 0:
            s = 16  # fallback before widget is realized
        self._status_label.setFixedHeight(s)
        # top=s, left=s, right=s, bottom=0 — status label provides the bottom s
        self._main_layout.setContentsMargins(s, s, s, 0)

    def _fit_to_keyboard(self) -> None:
        self._apply_margins()
        def do_fit():
            self.setMinimumSize(0, 0)
            self.resize(self.sizeHint())
        QTimer.singleShot(0, do_fit)
    
    def _on_device_found(self, device_info: Dict[str, Any]) -> None:
        """
        Handle device found events.
        
        Args:
            device_info: Device information dictionary
        """
        product_name = device_info.get("product_string", "Unknown")
        self._status_label.setText(f"Connected: {product_name}")
        self._status_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
    
    def _on_device_lost(self) -> None:
        """Handle device lost events."""
        self._status_label.setText("Device disconnected")
        self._status_label.setStyleSheet("color: #F44336; font-size: 10px;")
    
    def _on_error(self, error_message: str) -> None:
        """
        Handle error events.
        
        Args:
            error_message: Error message
        """
        self._status_label.setText(f"Error: {error_message}")
        self._status_label.setStyleSheet("color: #F44336; font-size: 10px;")
    
    def _on_layer_display_clicked(self) -> None:
        self._toggle_window_visibility()
    
    def _tray_icon_activated(self, reason) -> None:
        """
        Handle system tray icon activation.
        
        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_window_visibility()
    
    def _toggle_window_visibility(self) -> None:
        """Toggle window visibility."""
        if self.isVisible():
            self.hide()
            self._show_hide_action.setText("Show")
        else:
            self.show()
            self.activateWindow()
            self._show_hide_action.setText("Hide")
    
    def _show_preview(self) -> None:
        """Show layer preview dialog."""
        # Create preview window
        preview_window = LayerPreviewWindow(
            layer_state=self._layer_state,
            parent=self
        )
        
        # Connect layer names changed signal
        preview_window.layer_names_changed.connect(self._on_layer_names_changed)
        
        # Show dialog
        preview_window.exec()
    
    def _on_layer_names_changed(self, layer_names: Dict[int, str]) -> None:
        """
        Handle layer names changed events.
        
        Args:
            layer_names: Dictionary of layer numbers to names
        """
        # Update layer display with new name
        current_layer = self._layer_state.get_current_layer()
        layer_name = self._layer_state.get_layer_name(current_layer)
        self._kb_widget.set_active_layer(current_layer)
    
    def _show_settings(self) -> None:
        """Show settings dialog."""
        QMessageBox.information(
            self,
            "Settings",
            "Settings dialog will be implemented in a future version."
        )
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Vial Layer Display",
            """
            <h3>Vial Layer Display</h3>
            <p>Version 0.1.0</p>
            <p>A lightweight desktop application for displaying the current keyboard layer from Vial-compatible mechanical keyboards.</p>
            <p>License: MIT</p>
            <p>GitHub: https://github.com/larspage/KBLayoutWindow</p>
            """
        )
    
    def _quit_application(self) -> None:
        """Quit the application."""
        # Stop keyboard monitoring
        self._keyboard_monitor.stop()
        
        # Save window position and size
        self._save_window_state()
        
        # Emit closed signal
        self.closed.emit()
        
        # Close application
        QApplication.instance().quit()
    
    def _save_window_state(self) -> None:
        """Save window state to configuration."""
        window_config = self._config.get("window", {})
        window_config["width"] = self.width()
        window_config["height"] = self.height()
        window_config["x"] = self.x()
        window_config["y"] = self.y()
        self._config["window"] = window_config
        
        self._config_manager.save_config(self._config)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # Check if should minimize to tray instead of closing
        if self._config.get("window", {}).get("minimize_to_tray", True):
            event.ignore()
            self.hide()
            self._show_hide_action.setText("Show")
        else:
            self._quit_application()
            event.accept()
    
    def get_kb_widget(self) -> KeyboardWidget:
        return self._kb_widget
    
    def get_keyboard_monitor(self) -> KeyboardMonitor:
        """
        Get the keyboard monitor instance.
        
        Returns:
            KeyboardMonitor instance
        """
        return self._keyboard_monitor
    
    def get_layer_state(self) -> LayerState:
        """
        Get the layer state manager.
        
        Returns:
            LayerState instance
        """
        return self._layer_state


# Import QApplication at the end to avoid circular imports
from PyQt6.QtWidgets import QApplication
