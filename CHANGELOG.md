# Changelog

All notable changes to the Vial Layer Display project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Phase 3: Integration & Polish
  - Integration testing
  - Performance optimization
  - Binary builds (PyInstaller)

## [0.2.0] - 2025-02-10

### Added
- **User Interface Modules**
  - [`LayerDisplay`](src/ui/layer_display.py:1) widget for displaying current keyboard layer
  - [`MainWindow`](src/ui/main_window.py:1) application window with system tray integration
  - [`LayerPreviewWindow`](src/ui/preview_window.py:1) dialog for viewing and editing all layers

- **Layer Display Widget Features**
  - Visual rendering of current layer number and name
  - Zoom functionality (0.5x to 3.0x, default 1.0x)
  - Custom styling and theming support
  - PyQt6 signals for zoom changes and click events
  - Custom painting with accent border
  - Configurable font family and size
  - Color parsing from hex strings, RGB tuples, or QColor objects

- **Main Window Features**
  - Integration with layer display, keyboard monitor, and layer state
  - System tray icon with context menu
  - Window management (always-on-top, minimize to tray)
  - Zoom controls (zoom in, zoom out, reset)
  - Layer preview button
  - Status label for device connection state
  - About dialog with application information
  - Window state persistence (position, size)
  - Signal connections for layer changes, device events, and errors

- **Layer Preview Window Features**
  - Grid view of all available layers (up to 16)
  - Visual indication of current layer
  - Layer name editing capability
  - Save/Cancel/Reset buttons
  - Confirmation dialogs for destructive actions
  - Signal emission when layer names are changed
  - Scrollable interface for many layers

- **UI Test Suite**
  - [`test_layer_display.py`](tests/test_layer_display.py:1) - 30+ tests for LayerDisplay widget
  - [`test_main_window.py`](tests/test_main_window.py:1) - 25+ tests for MainWindow
  - [`test_preview_window.py`](tests/test_preview_window.py:1) - 25+ tests for LayerPreviewWindow
  - Tests for initialization, zoom, theming, signals, and user interactions

### Technical Details
- **UI Framework**: PyQt6 with custom widgets
- **Threading**: Qt signals/slots for cross-thread communication
- **Styling**: CSS-like stylesheets with QColor support
- **Layouts**: QVBoxLayout, QHBoxLayout, QGridLayout
- **Dialogs**: Modal dialogs with confirmation prompts
- **System Tray**: QSystemTrayIcon with context menu

### Integration
- MainWindow integrates all Phase 1 modules (config_manager, layer_state, keyboard_monitor)
- LayerDisplay receives layer updates from LayerState
- MainWindow handles keyboard monitor signals (device_found, device_lost, error)
- LayerPreviewWindow allows editing layer names in LayerState

## [0.1.0] - 2025-02-10

### Added
- **Project Structure**
  - Complete directory structure (src/, tests/, docs/, config/, assets/)
  - Subdirectories for core, ui, config, and utils modules

- **Configuration Management**
  - [`ConfigManager`](src/config/config_manager.py:1) class for loading/saving TOML configurations
  - Platform-specific config paths (Windows, macOS, Linux)
  - Default configuration file at [`config/default_config.toml`](config/default_config.toml:1)
  - Support for nested config keys with dot notation

- **HID Communication**
  - [`hid_utils.py`](src/utils/hid_utils.py:1) with Vial keyboard detection
  - Support for Vial vendor IDs (0x5342, 0x3496, 0x3297)
  - Device enumeration and connection management
  - Layer data reading using Vial protocol

- **Layer State Management**
  - [`LayerState`](src/core/layer_state.py:1) class for thread-safe state tracking
  - PyQt6 signals for UI updates on layer changes
  - Custom layer name support
  - Default layer names: "Base", "Layer 1", "Layer 2", etc.

- **Keyboard Monitoring**
  - [`KeyboardMonitor`](src/core/keyboard_monitor.py:1) class for USB HID monitoring
  - Separate thread execution to avoid blocking UI
  - Configurable polling interval (default 100ms)
  - Auto-detection of Vial keyboards
  - Signals for device_found, device_lost, error, and layer_changed

- **Application Entry Point**
  - [`main.py`](src/main.py:1) with PyQt6 application setup
  - High DPI scaling support
  - Error handling and graceful shutdown

- **Test Suite**
  - 125+ test cases covering all implemented modules
  - Shared fixtures in [`conftest.py`](tests/conftest.py:1)
  - Tests for config_manager, hid_utils, layer_state, and keyboard_monitor
  - Pytest configuration in [`pytest.ini`](pytest.ini:1)

- **Development Tools**
  - [`requirements.txt`](requirements.txt) - Runtime dependencies
  - [`requirements-dev.txt`](requirements-dev.txt) - Development dependencies
  - [`.gitignore`](.gitignore) - Git ignore patterns
  - [`pytest.ini`](pytest.ini) - Pytest configuration

- **Documentation**
  - Project documentation in [`Documents/`](Documents/) folder
  - INDEX.md, LICENSE, PROJECT_SUMMARY.md, README.md

### Technical Details
- **Language**: Python 3.11+
- **Framework**: PyQt6 (GUI), hidapi (USB HID)
- **Testing**: pytest, pytest-mock, pytest-cov
- **Configuration**: TOML format with tomli/tomli-w
- **Thread Safety**: threading.RLock() for state management
- **Cross-Platform**: Windows, macOS, Linux support

### Git Repository
- Repository: https://github.com/larspage/KBLayoutWindow.git
- Initial commit: e180913
- Branch: main
- Files: 21
- Lines of code: 4,706

## Roadmap

### Phase 2: User Interface (Next)
- [ ] Layer display widget with visual rendering
- [ ] Zoom functionality for adjustable display size
- [ ] Main application window with system tray
- [ ] Layer preview dialog for viewing all layers
- [ ] Layer name editing capability
- [ ] Theme and styling support

### Phase 3: Integration & Polish
- [ ] Integration testing with real hardware
- [ ] Performance optimization
- [ ] Memory usage optimization
- [ ] CPU usage optimization
- [ ] Binary builds with PyInstaller
- [ ] Windows installer
- [ ] macOS app bundle
- [ ] Linux packages

### Future Enhancements
- [ ] Multiple keyboard support
- [ ] Custom layer icons
- [ ] Keyboard layout visualization
- [ ] Layer switching shortcuts
- [ ] Plugin system
- [ ] Cloud sync for settings
- [ ] Mobile companion app

## Version History

| Version | Date | Status | Description |
|---------|------|--------|-------------|
| 0.1.0 | 2025-02-10 | ✅ Released | Phase 1 - Core Infrastructure |
| 0.2.0 | 2025-02-10 | ✅ Released | Phase 2 - User Interface |
| 0.3.0 | TBD | 🚧 Planned | Phase 3 - Integration & Polish |
| 1.0.0 | TBD | ⏳ Planned | First stable release |

---

**Note**: This project is currently in active development. Features and APIs may change before the 1.0.0 release.
