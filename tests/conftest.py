"""
Pytest Configuration and Shared Fixtures

This module provides shared fixtures for all test modules in the Vial Layer
Display test suite. Fixtures are automatically discovered by pytest and can
be used in any test function by including them as parameters.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.config_manager import ConfigManager
from src.core.layer_state import LayerState


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """
    Provide a sample configuration dictionary for testing.

    Returns:
        Dict[str, Any]: Sample configuration with all expected sections.
    """
    return {
        "window": {
            "width": 300,
            "height": 200,
            "x": 100,
            "y": 100,
            "always_on_top": True,
        },
        "display": {
            "font_size": 14,
            "font_family": "Arial",
            "theme": "dark",
        },
        "keyboard": {
            "poll_interval_ms": 100,
            "auto_detect": True,
        },
        "layer": {
            "default_layer_names": ["Base", "Mod", "Fn", "Mouse", "Media"],
        },
    }


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """
    Provide a temporary directory for configuration files.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path: Temporary directory path for config files.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def config_manager(tmp_config_dir: Path) -> ConfigManager:
    """
    Provide a ConfigManager instance for testing.

    This fixture creates a ConfigManager that uses a temporary directory
    for configuration files, ensuring tests don't affect the user's
    actual configuration.

    Args:
        tmp_config_dir: Temporary directory fixture.

    Returns:
        ConfigManager: Configured instance for testing.
    """
    config_path = str(tmp_config_dir / "config.toml")
    return ConfigManager(config_path=config_path)


@pytest.fixture
def layer_state() -> LayerState:
    """
    Provide a LayerState instance for testing.

    Returns:
        LayerState: Fresh instance with default settings.
    """
    return LayerState(max_layers=16)


@pytest.fixture
def mock_hid_device() -> Mock:
    """
    Provide a mock HID device for testing.

    This fixture creates a mock object that simulates a HID device,
    allowing tests to verify device operations without requiring
    actual hardware.

    Returns:
        Mock: Mocked HID device with common methods.
    """
    device = Mock()
    device.write = Mock(return_value=None)
    device.read = Mock(return_value=[0x00, 0x02] + [0x00] * 62)
    device.close = Mock(return_value=None)
    return device


@pytest.fixture
def mock_vial_device_info() -> Dict[str, Any]:
    """
    Provide mock Vial device information for testing.

    Returns:
        Dict[str, Any]: Mock device information dictionary.
    """
    return {
        "vendor_id": 0x5342,
        "product_id": 0x0001,
        "path": b"/dev/hidraw0",
        "manufacturer_string": "Vial",
        "product_string": "Test Keyboard",
        "serial_number": "TEST123",
        "usage_page": 0xFF60,
        "usage": 0x61,
    }


@pytest.fixture
def mock_hid_enumerate() -> Mock:
    """
    Provide a mock for hid.enumerate() function.

    Returns:
        Mock: Mocked enumerate function that returns empty list by default.
    """
    mock = Mock(return_value=[])
    return mock


@pytest.fixture
def mock_hid_open() -> Mock:
    """
    Provide a mock for hid.device() and open operations.

    Returns:
        Mock: Mocked device class and instance.
    """
    mock_device = Mock()
    mock_device.write = Mock(return_value=None)
    mock_device.read = Mock(return_value=[0x00, 0x02] + [0x00] * 62)
    mock_device.close = Mock(return_value=None)

    mock_device_class = Mock(return_value=mock_device)
    return mock_device_class


@pytest.fixture
def sample_toml_config() -> str:
    """
    Provide a sample TOML configuration string.

    Returns:
        str: TOML-formatted configuration string.
    """
    return """
[window]
width = 300
height = 200
x = 100
y = 100
always_on_top = true

[display]
font_size = 14
font_family = "Arial"
theme = "dark"

[keyboard]
poll_interval_ms = 100
auto_detect = true

[layer]
default_layer_names = ["Base", "Mod", "Fn", "Mouse", "Media"]
"""


@pytest.fixture
def mock_qt_application() -> Mock:
    """
    Provide a mock Qt application for testing.

    This fixture creates a mock QApplication instance, allowing tests
    to run without requiring an actual Qt application.

    Returns:
        Mock: Mocked QApplication instance.
    """
    app = Mock()
    app.exec = Mock(return_value=0)
    return app


@pytest.fixture
def mock_signal_emitter() -> Mock:
    """
    Provide a mock signal emitter for testing PyQt signals.

    Returns:
        Mock: Mocked signal emitter with emit method.
    """
    emitter = Mock()
    emitter.emit = Mock()
    emitter.connect = Mock()
    emitter.disconnect = Mock()
    return emitter


@pytest.fixture
def keyboard_config() -> Dict[str, Any]:
    """
    Provide keyboard monitor configuration for testing.

    Returns:
        Dict[str, Any]: Configuration dictionary for KeyboardMonitor.
    """
    return {
        "poll_interval_ms": 100,
        "auto_detect": True,
    }


@pytest.fixture(autouse=True)
def reset_logging() -> None:
    """
    Reset logging configuration before each test.

    This fixture runs automatically for all tests to ensure
    consistent logging behavior.
    """
    # Clear any existing handlers
    import logging
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Reset to default level
    root_logger.setLevel(logging.WARNING)
    
    yield
    
    # Cleanup after test
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
