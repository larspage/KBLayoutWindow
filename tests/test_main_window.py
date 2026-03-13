"""
Tests for Main Window

This module contains tests for the MainWindow class.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.core.layer_state import LayerState
from src.core.keyboard_monitor import KeyboardMonitor
from src.config.config_manager import ConfigManager


@pytest.fixture
def qapp():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app


@pytest.fixture
def mock_config_manager():
    """Create mock ConfigManager."""
    manager = Mock(spec=ConfigManager)
    manager.load_config.return_value = {
        "window": {
            "width": 200,
            "height": 150,
            "x": 100,
            "y": 100,
            "always_on_top": True,
            "frameless": False,
            "opacity": 1.0,
            "minimize_to_tray": True
        },
        "display": {
            "font_family": "Arial",
            "font_size": 24,
            "bg_color": "#282C34",
            "text_color": "#ABB2BF",
            "border_color": "#3C4048",
            "accent_color": "#61AFEF"
        },
        "keyboard": {
            "poll_interval_ms": 100,
            "auto_detect": True
        }
    }
    manager.save_config = Mock()
    return manager


@pytest.fixture
def mock_layer_state():
    """Create mock LayerState."""
    state = Mock(spec=LayerState)
    state.get_current_layer.return_value = 0
    state.get_layer_name.return_value = "Base"
    state.get_all_layer_names.return_value = {0: "Base", 1: "Layer 1", 2: "Layer 2"}
    state.max_layers = 16
    return state


@pytest.fixture
def mock_keyboard_monitor():
    """Create mock KeyboardMonitor."""
    monitor = Mock(spec=KeyboardMonitor)
    monitor.start = Mock()
    monitor.stop = Mock()
    return monitor


@pytest.fixture
def main_window(qapp, mock_config_manager, mock_layer_state, mock_keyboard_monitor):
    """Create MainWindow instance for testing."""
    window = MainWindow(
        config_manager=mock_config_manager,
        layer_state=mock_layer_state,
        keyboard_monitor=mock_keyboard_monitor
    )
    yield window
    window.deleteLater()


class TestMainWindowInitialization:
    """Tests for MainWindow initialization."""
    
    def test_initialization(self, main_window):
        """Test basic initialization."""
        assert main_window.windowTitle() == "Vial Layer Display"
        assert main_window._config_manager is not None
        assert main_window._layer_state is not None
        assert main_window._keyboard_monitor is not None
    
    def test_initialization_starts_monitor(self, main_window, mock_keyboard_monitor):
        """Test that keyboard monitor is started on initialization."""
        mock_keyboard_monitor.start.assert_called_once()
    
    def test_window_size_from_config(self, main_window):
        """Test window size is set from config."""
        assert main_window.width() == 200
        assert main_window.height() == 150
    
    def test_window_position_from_config(self, main_window):
        """Test window position is set from config."""
        assert main_window.x() == 100
        assert main_window.y() == 100
    
    def test_always_on_top_flag(self, main_window):
        """Test always-on-top flag is set."""
        flags = main_window.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint
    
    def test_layer_display_created(self, main_window):
        """Test layer display widget is created."""
        assert main_window._layer_display is not None
        assert main_window._layer_display.current_layer == 0
    
    def test_system_tray_created(self, main_window):
        """Test system tray icon is created."""
        assert main_window._tray_icon is not None


class TestMainWindowSignals:
    """Tests for signal connections."""
    
    def test_layer_changed_connected(self, main_window, mock_layer_state):
        """Test layer_changed signal is connected."""
        # Emit signal
        mock_layer_state.layer_changed.emit(2)
        
        # Check layer display was updated
        assert main_window._layer_display.current_layer == 2
    
    def test_device_found_connected(self, main_window):
        """Test device_found signal is connected."""
        device_info = {"product_string": "Test Keyboard"}
        main_window._on_device_found(device_info)
        
        assert "Connected" in main_window._status_label.text()
    
    def test_device_lost_connected(self, main_window):
        """Test device_lost signal is connected."""
        main_window._on_device_lost()
        
        assert "disconnected" in main_window._status_label.text()
    
    def test_error_connected(self, main_window):
        """Test error signal is connected."""
        main_window._on_error("Test error")
        
        assert "Error" in main_window._status_label.text()


class TestMainWindowLayerDisplay:
    """Tests for layer display integration."""
    
    def test_get_layer_display(self, main_window):
        """Test getting layer display widget."""
        display = main_window.get_layer_display()
        assert display is main_window._layer_display
    
    def test_layer_display_zoom_buttons(self, main_window):
        """Test zoom buttons are connected."""
        initial_zoom = main_window._layer_display.zoom_level
        
        # Click zoom in
        main_window._zoom_in_btn.click()
        assert main_window._layer_display.zoom_level > initial_zoom
        
        # Click zoom out
        main_window._zoom_out_btn.click()
        assert main_window._layer_display.zoom_level == initial_zoom
    
    def test_layer_display_reset_button(self, main_window):
        """Test reset zoom button."""
        main_window._layer_display.set_zoom(2.0)
        main_window._zoom_reset_btn.click()
        assert main_window._layer_display.zoom_level == 1.0


class TestMainWindowSystemTray:
    """Tests for system tray functionality."""
    
    def test_tray_icon_created(self, main_window):
        """Test system tray icon is created."""
        assert main_window._tray_icon is not None
    
    def test_tray_menu_created(self, main_window):
        """Test tray menu is created."""
        assert main_window._tray_icon.contextMenu() is not None
    
    def test_toggle_window_visibility_show(self, main_window):
        """Test toggling window visibility to show."""
        main_window.hide()
        main_window._toggle_window_visibility()
        assert main_window.isVisible()
    
    def test_toggle_window_visibility_hide(self, main_window):
        """Test toggling window visibility to hide."""
        main_window._toggle_window_visibility()
        assert not main_window.isVisible()
    
    def test_tray_icon_activated(self, main_window):
        """Test tray icon activation toggles visibility."""
        main_window._tray_icon_activated(
            QSystemTrayIcon.ActivationReason.Trigger
        )
        assert not main_window.isVisible()


class TestMainWindowPreview:
    """Tests for preview window functionality."""
    
    def test_preview_button_exists(self, main_window):
        """Test preview button exists."""
        assert main_window._preview_btn is not None
    
    def test_show_preview(self, main_window):
        """Test showing preview window."""
        # This will show a message box for now
        with patch.object(main_window, '_show_preview'):
            main_window._preview_btn.click()
            # Preview functionality will be fully tested when preview_window is integrated


class TestMainWindowSettings:
    """Tests for settings functionality."""
    
    def test_show_settings(self, main_window):
        """Test showing settings dialog."""
        with patch('PyQt6.QtWidgets.QMessageBox.information'):
            main_window._show_settings()
            # Settings dialog will be implemented in future version


class TestMainWindowAbout:
    """Tests for about dialog."""
    
    def test_show_about(self, main_window):
        """Test showing about dialog."""
        with patch('PyQt6.QtWidgets.QMessageBox.about'):
            main_window._show_about()
            # About dialog should be shown


class TestMainWindowQuit:
    """Tests for quit functionality."""
    
    def test_quit_application_stops_monitor(self, main_window, mock_keyboard_monitor):
        """Test quit stops keyboard monitor."""
        with patch.object(main_window, 'closed'):
            with patch('PyQt6.QtWidgets.QApplication.instance') as mock_app:
                mock_qapp = Mock()
                mock_app.return_value = mock_qapp
                main_window._quit_application()
                
                mock_keyboard_monitor.stop.assert_called_once()
    
    def test_quit_application_saves_state(self, main_window, mock_config_manager):
        """Test quit saves window state."""
        with patch.object(main_window, 'closed'):
            with patch('PyQt6.QtWidgets.QApplication.instance'):
                main_window._quit_application()
                
                mock_config_manager.save_config.assert_called_once()
    
    def test_close_event_minimize_to_tray(self, main_window):
        """Test close event minimizes to tray."""
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()
        
        main_window.closeEvent(event)
        
        assert event.isAccepted() == False  # Event was ignored
        assert not main_window.isVisible()


class TestMainWindowWindowState:
    """Tests for window state management."""
    
    def test_save_window_state(self, main_window, mock_config_manager):
        """Test saving window state."""
        main_window._save_window_state()
        
        mock_config_manager.save_config.assert_called_once()
        saved_config = mock_config_manager.save_config.call_args[0][0]
        
        assert "window" in saved_config
        assert saved_config["window"]["width"] == main_window.width()
        assert saved_config["window"]["height"] == main_window.height()


class TestMainWindowGetters:
    """Tests for getter methods."""
    
    def test_get_keyboard_monitor(self, main_window, mock_keyboard_monitor):
        """Test getting keyboard monitor."""
        monitor = main_window.get_keyboard_monitor()
        assert monitor is mock_keyboard_monitor
    
    def test_get_layer_state(self, main_window, mock_layer_state):
        """Test getting layer state."""
        state = main_window.get_layer_state()
        assert state is mock_layer_state


class TestMainWindowLayerNamesChanged:
    """Tests for layer names changed handling."""
    
    def test_on_layer_names_changed(self, main_window, mock_layer_state):
        """Test handling layer names changed."""
        new_names = {0: "Base", 1: "Function", 2: "Media"}
        mock_layer_state.get_layer_name.return_value = "Function"
        
        main_window._on_layer_names_changed(new_names)
        
        # Layer display should be updated
        assert main_window._layer_display.layer_name == "Function"


# Import QSystemTrayIcon at the end
from PyQt6.QtWidgets import QSystemTrayIcon
