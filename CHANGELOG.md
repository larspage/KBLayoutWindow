# Changelog

All notable changes to the Vial Layer Display project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Phase 2: User Interface Implementation
  - Layer display widget with zoom functionality
  - Main application window with system tray integration
  - Layer preview dialog for viewing all layers
- Phase 3: Integration & Polish
  - Integration testing
  - Performance optimization
  - Binary builds (PyInstaller)

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
| 0.2.0 | TBD | 🚧 Planned | Phase 2 - User Interface |
| 0.3.0 | TBD | ⏳ Planned | Phase 3 - Integration & Polish |
| 1.0.0 | TBD | ⏳ Planned | First stable release |

---

**Note**: This project is currently in active development. Features and APIs may change before the 1.0.0 release.
