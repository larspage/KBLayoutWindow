"""
Tests for ConfigManager Module

This module contains unit tests for the ConfigManager class, which handles
loading, saving, and managing application configuration using TOML files.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.config_manager import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager class."""

    def test_load_default_config(self, config_manager: ConfigManager) -> None:
        """
        Test loading default configuration.

        Verifies that the default configuration is loaded correctly
        and contains expected sections.
        """
        config = config_manager.load_config()

        assert isinstance(config, dict)
        assert "window" in config
        assert "display" in config
        assert "keyboard" in config
        assert "layer" in config

    def test_get_config_path(self, config_manager: ConfigManager) -> None:
        """
        Test getting platform-specific configuration path.

        Verifies that the configuration path is returned correctly
        and is an absolute path.
        """
        config_path = config_manager.get_config_path()

        assert isinstance(config_path, str)
        assert os.path.isabs(config_path)
        assert config_path.endswith("config.toml")

    def test_get_config_path_custom(self, tmp_path: Path) -> None:
        """
        Test getting custom configuration path.

        Verifies that a custom configuration path is returned
        when provided during initialization.
        """
        custom_path = str(tmp_path / "custom_config.toml")
        manager = ConfigManager(config_path=custom_path)

        result = manager.get_config_path()

        assert result == os.path.abspath(custom_path)

    def test_get_set(self, config_manager: ConfigManager) -> None:
        """
        Test getting and setting configuration values.

        Verifies that configuration values can be retrieved and set
        correctly using the get and set methods.
        """
        # Load config first
        config_manager.load_config()

        # Test getting existing value
        width = config_manager.get("window.width")
        assert width is not None
        assert isinstance(width, int)

        # Test setting a new value
        config_manager.set("window.width", 400)
        new_width = config_manager.get("window.width")
        assert new_width == 400

        # Test getting non-existent value with default
        non_existent = config_manager.get("nonexistent.key", "default")
        assert non_existent == "default"

    def test_save_config(self, config_manager: ConfigManager, sample_config: Dict[str, Any]) -> None:
        """
        Test saving configuration to file.

        Verifies that configuration can be saved to a file and
        the saved file contains the expected data.
        """
        # Save the sample configuration
        config_manager.save_config(sample_config)

        # Verify the file was created
        config_path = config_manager.get_config_path()
        assert os.path.exists(config_path)

        # Load and verify the saved configuration
        loaded_config = config_manager.load_config()
        assert loaded_config == sample_config

    def test_nested_keys(self, config_manager: ConfigManager) -> None:
        """
        Test accessing nested configuration keys using dot notation.

        Verifies that nested keys can be accessed and modified
        using dot notation (e.g., "window.width").
        """
        config_manager.load_config()

        # Test getting nested value
        theme = config_manager.get("display.theme")
        assert theme is not None

        # Test setting nested value
        config_manager.set("display.theme", "light")
        new_theme = config_manager.get("display.theme")
        assert new_theme == "light"

        # Test deeply nested access
        config_manager.set("window.always_on_top", False)
        always_on_top = config_manager.get("window.always_on_top")
        assert always_on_top is False

    def test_missing_config_file(self, tmp_path: Path) -> None:
        """
        Test handling of missing configuration file.

        Verifies that the ConfigManager handles missing user
        configuration files gracefully by using defaults.
        """
        # Create a manager with a non-existent user config path
        non_existent_path = str(tmp_path / "nonexistent" / "config.toml")
        manager = ConfigManager(config_path=non_existent_path)

        # This should load default config even though user config doesn't exist
        config = manager.load_config()

        assert isinstance(config, dict)
        assert "window" in config

    def test_get_all(self, config_manager: ConfigManager) -> None:
        """
        Test getting the entire configuration dictionary.

        Verifies that get_all returns a copy of the complete
        configuration dictionary.
        """
        config_manager.load_config()
        all_config = config_manager.get_all()

        assert isinstance(all_config, dict)
        assert "window" in all_config
        assert "display" in all_config

        # Verify it's a copy, not the same object
        all_config["test"] = "value"
        assert "test" not in config_manager.get_all()

    def test_reload(self, config_manager: ConfigManager) -> None:
        """
        Test reloading configuration from disk.

        Verifies that reload clears the cache and reloads
        configuration from disk.
        """
        # Load initial config
        config_manager.load_config()
        initial_width = config_manager.get("window.width")

        # Modify cached config
        config_manager.set("window.width", 999)
        modified_width = config_manager.get("window.width")
        assert modified_width == 999

        # Reload should reset to original
        reloaded_config = config_manager.reload()
        reloaded_width = config_manager.get("window.width")
        assert reloaded_width == initial_width

    def test_merge_configs(self, config_manager: ConfigManager) -> None:
        """
        Test merging user configuration with default configuration.

        Verifies that user configuration values override default
        values and nested dictionaries are merged correctly.
        """
        default_config = {
            "window": {"width": 300, "height": 200},
            "display": {"theme": "dark"},
        }
        user_config = {
            "window": {"width": 400},  # Override default
            "display": {"font_size": 16},  # Add new nested value
        }

        merged = config_manager._merge_configs(default_config, user_config)

        assert merged["window"]["width"] == 400  # User override
        assert merged["window"]["height"] == 200  # Default preserved
        assert merged["display"]["theme"] == "dark"  # Default preserved
        assert merged["display"]["font_size"] == 16  # User addition

    def test_validate_config_structure(self, config_manager: ConfigManager) -> None:
        """
        Test configuration structure validation.

        Verifies that valid configurations pass validation
        and invalid ones are rejected.
        """
        # Valid config
        valid_config = {"window": {"width": 300}}
        assert config_manager._validate_config_structure(valid_config) is True

        # Invalid config (no expected sections)
        invalid_config = {"unknown": {"key": "value"}}
        assert config_manager._validate_config_structure(invalid_config) is False

        # Empty config
        empty_config = {}
        assert config_manager._validate_config_structure(empty_config) is False

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """
        Test that save_config creates the configuration directory if needed.

        Verifies that the configuration directory is created automatically
        when saving to a non-existent directory.
        """
        nested_path = tmp_path / "nested" / "dir" / "config.toml"
        manager = ConfigManager(config_path=str(nested_path))

        sample_config = {"window": {"width": 300}}
        manager.save_config(sample_config)

        assert os.path.exists(nested_path)

    def test_get_default_config_path(self, config_manager: ConfigManager) -> None:
        """
        Test getting the default configuration file path.

        Verifies that the default configuration path points to
        the correct location in the project.
        """
        default_path = config_manager.get_default_config_path()

        assert isinstance(default_path, str)
        assert os.path.isabs(default_path)
        assert "default_config.toml" in default_path

    def test_load_toml_file_not_found(self, config_manager: ConfigManager) -> None:
        """
        Test loading a non-existent TOML file.

        Verifies that FileNotFoundError is raised when attempting
        to load a file that doesn't exist.
        """
        with pytest.raises(FileNotFoundError):
            config_manager._load_toml_file("/nonexistent/path/config.toml")

    def test_set_creates_nested_structure(self, config_manager: ConfigManager) -> None:
        """
        Test that set creates nested dictionary structure as needed.

        Verifies that setting a deeply nested key creates all
        intermediate dictionaries.
        """
        config_manager.load_config()

        # Set a deeply nested value
        config_manager.set("new.nested.key", "value")

        # Verify the structure was created
        assert config_manager.get("new.nested.key") == "value"

    def test_get_with_none_default(self, config_manager: ConfigManager) -> None:
        """
        Test getting a value with None as default.

        Verifies that None is returned when a key doesn't exist
        and no default is provided.
        """
        config_manager.load_config()

        result = config_manager.get("nonexistent.key")
        assert result is None

    def test_invalid_toml_file(self, tmp_path: Path) -> None:
        """
        Test loading an invalid TOML file.

        Verifies that ValueError is raised when attempting
        to load a malformed TOML file.
        """
        invalid_toml = tmp_path / "invalid.toml"
        invalid_toml.write_text("invalid [toml content")

        manager = ConfigManager(config_path=str(invalid_toml))

        with pytest.raises(ValueError):
            manager._load_toml_file(str(invalid_toml))

    def test_config_manager_initialization(self) -> None:
        """
        Test ConfigManager initialization.

        Verifies that ConfigManager can be initialized with
        and without a custom config path.
        """
        # Without custom path
        manager1 = ConfigManager()
        assert manager1.config_path is None

        # With custom path
        manager2 = ConfigManager(config_path="/custom/path/config.toml")
        assert manager2.config_path == "/custom/path/config.toml"

    def test_multiple_get_set_operations(self, config_manager: ConfigManager) -> None:
        """
        Test multiple get and set operations in sequence.

        Verifies that multiple operations work correctly
        and don't interfere with each other.
        """
        config_manager.load_config()

        # Set multiple values
        config_manager.set("window.width", 500)
        config_manager.set("window.height", 300)
        config_manager.set("display.theme", "light")
        config_manager.set("display.font_size", 18)

        # Verify all values
        assert config_manager.get("window.width") == 500
        assert config_manager.get("window.height") == 300
        assert config_manager.get("display.theme") == "light"
        assert config_manager.get("display.font_size") == 18
