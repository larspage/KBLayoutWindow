"""
Configuration Manager Module

This module provides the ConfigManager class for loading, saving, and managing
application configuration using TOML files. It handles platform-specific config
paths and merges default configuration with user configuration.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Use tomllib for Python 3.11+, otherwise use tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


class ConfigManager:
    """
    Manages application configuration loading, saving, and access.

    This class handles loading configuration from TOML files, merging default
    configuration with user configuration, and providing access to configuration
    values. It supports platform-specific configuration paths for Windows, macOS,
    and Linux.

    Attributes:
        config_path (Optional[str]): Custom configuration file path, if provided.
        _config (Dict[str, Any]): Cached configuration dictionary.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize the ConfigManager.

        Args:
            config_path: Optional custom path to the configuration file.
                        If not provided, uses the platform-specific default path.
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}

    def get_config_path(self) -> str:
        """
        Get the platform-specific configuration file path.

        Returns:
            str: The absolute path to the user configuration file.

        Platform-specific paths:
            - Windows: %APPDATA%/VialLayerDisplay/config.toml
            - macOS: ~/Library/Application Support/VialLayerDisplay/config.toml
            - Linux: ~/.config/VialLayerDisplay/config.toml
        """
        if self.config_path:
            return os.path.abspath(self.config_path)

        if sys.platform == "win32":
            # Windows: %APPDATA%/VialLayerDisplay/config.toml
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            config_dir = os.path.join(appdata, "VialLayerDisplay")
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/VialLayerDisplay/config.toml
            home = os.path.expanduser("~")
            config_dir = os.path.join(
                home, "Library", "Application Support", "VialLayerDisplay"
            )
        else:
            # Linux and others: ~/.config/VialLayerDisplay/config.toml
            home = os.path.expanduser("~")
            config_dir = os.path.join(home, ".config", "VialLayerDisplay")

        return os.path.join(config_dir, "config.toml")

    def get_default_config_path(self) -> str:
        """
        Get the path to the default configuration file.

        Returns:
            str: The absolute path to the default configuration file.
        """
        # Get the project root directory (parent of src directory)
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parent.parent.parent
        return str(project_root / "config" / "default_config.toml")

    def _load_toml_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load a TOML file and return its contents as a dictionary.

        Args:
            file_path: Path to the TOML file to load.

        Returns:
            Dict[str, Any]: The parsed TOML content as a dictionary.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed as valid TOML.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse TOML file {file_path}: {e}")

    def _merge_configs(
        self, default_config: Dict[str, Any], user_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge user configuration with default configuration.

        User configuration values override default values. Nested dictionaries
        are merged recursively.

        Args:
            default_config: The default configuration dictionary.
            user_config: The user configuration dictionary.

        Returns:
            Dict[str, Any]: The merged configuration dictionary.
        """
        merged = default_config.copy()

        for key, value in user_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # Override with user value
                merged[key] = value

        return merged

    def _validate_config_structure(self, config: Dict[str, Any]) -> bool:
        """
        Validate the basic structure of the configuration.

        Args:
            config: The configuration dictionary to validate.

        Returns:
            bool: True if the configuration structure is valid, False otherwise.
        """
        # Expected top-level sections based on default_config.toml
        expected_sections = {"window", "display", "keyboard", "layer"}

        # Check if at least one expected section exists
        # This is a basic validation - more specific validation can be added
        return any(section in config for section in expected_sections)

    def load_config(self) -> Dict[str, Any]:
        """
        Load and merge default and user configurations.

        This method loads the default configuration and merges it with the user
        configuration (if it exists). User configuration values override default
        values.

        Returns:
            Dict[str, Any]: The merged configuration dictionary.

        Raises:
            FileNotFoundError: If the default configuration file is not found.
            ValueError: If the configuration cannot be parsed or is invalid.
        """
        # Load default configuration
        default_config_path = self.get_default_config_path()
        try:
            default_config = self._load_toml_file(default_config_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Default configuration file not found: {default_config_path}"
            )

        # Load user configuration if it exists
        user_config_path = self.get_config_path()
        user_config: Dict[str, Any] = {}

        if os.path.exists(user_config_path):
            try:
                user_config = self._load_toml_file(user_config_path)
            except ValueError as e:
                raise ValueError(f"Invalid user configuration: {e}")

        # Merge configurations
        merged_config = self._merge_configs(default_config, user_config)

        # Validate configuration structure
        if not self._validate_config_structure(merged_config):
            raise ValueError("Invalid configuration structure")

        # Cache the merged configuration
        self._config = merged_config

        return merged_config

    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to the user configuration file.

        This method creates the configuration directory if it doesn't exist
        and saves the configuration to a TOML file.

        Args:
            config: The configuration dictionary to save.

        Raises:
            ValueError: If the configuration structure is invalid.
            OSError: If the file cannot be written.
        """
        # Validate configuration structure
        if not self._validate_config_structure(config):
            raise ValueError("Invalid configuration structure")

        # Get the user configuration path
        config_path = self.get_config_path()

        # Create the configuration directory if it doesn't exist
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
            except OSError as e:
                raise OSError(f"Failed to create config directory: {e}")

        # Write the configuration to the file
        try:
            with open(config_path, "wb") as f:
                tomli_w.dump(config, f)
        except Exception as e:
            raise OSError(f"Failed to write configuration file: {e}")

        # Update the cached configuration
        self._config = config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Supports nested keys using dot notation (e.g., "window.width").

        Args:
            key: The configuration key to retrieve. Can use dot notation for nested keys.
            default: The default value to return if the key is not found.

        Returns:
            Any: The configuration value, or the default if not found.

        Examples:
            >>> config_manager.get("window.width")
            300
            >>> config_manager.get("display.theme", "light")
            "dark"
        """
        if not self._config:
            # Load configuration if not already loaded
            self.load_config()

        # Handle nested keys using dot notation
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key.

        Supports nested keys using dot notation (e.g., "window.width").
        This method updates the cached configuration but does not automatically
        save to disk. Call save_config() to persist changes.

        Args:
            key: The configuration key to set. Can use dot notation for nested keys.
            value: The value to set.

        Examples:
            >>> config_manager.set("window.width", 400)
            >>> config_manager.set("display.theme", "light")
        """
        if not self._config:
            # Load configuration if not already loaded
            self.load_config()

        # Handle nested keys using dot notation
        keys = key.split(".")
        config = self._config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def reload(self) -> Dict[str, Any]:
        """
        Reload the configuration from disk.

        This method clears the cached configuration and reloads it from the
        default and user configuration files.

        Returns:
            Dict[str, Any]: The reloaded configuration dictionary.
        """
        self._config = {}
        return self.load_config()

    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration dictionary.

        Returns:
            Dict[str, Any]: The complete configuration dictionary.
        """
        if not self._config:
            self.load_config()
        return self._config.copy()
