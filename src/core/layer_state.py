"""
Layer State Module

This module provides thread-safe layer state management for the Vial Layer Display
application. It tracks the current keyboard layer and provides PyQt6 signals for
UI updates when the layer changes.

Classes:
    LayerState: Thread-safe layer state tracker with PyQt6 signals
"""

import logging
import threading
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

# Configure logging
logger = logging.getLogger(__name__)


class LayerState(QObject):
    """
    Thread-safe layer state tracker with PyQt6 signals for UI updates.

    This class manages the current keyboard layer state and provides signals
    that can be connected to UI components for real-time updates. All state
    modifications are protected by a lock to ensure thread safety.

    Signals:
        layer_changed(int): Emitted when the current layer changes.
            The parameter is the new layer number (0-indexed).

    Attributes:
        max_layers: Maximum number of layers supported
        current_layer: Current active layer (0-indexed)
        layer_names: Dictionary mapping layer numbers to names

    Example:
        >>> layer_state = LayerState(max_layers=16)
        >>> layer_state.layer_changed.connect(lambda layer: print(f"Layer: {layer}"))
        >>> layer_state.update_layer(2)
        Layer: 2
        >>> print(layer_state.get_layer_name(2))
        Layer 2
        >>> layer_state.set_layer_name(2, "Gaming")
        >>> print(layer_state.get_layer_name(2))
        Gaming
    """

    # PyQt6 signals
    layer_changed   = pyqtSignal(int)
    keymap_loaded   = pyqtSignal()      # emitted when full keymap data arrives

    def __init__(self, max_layers: int = 16) -> None:
        """
        Initialize the layer state tracker.

        Args:
            max_layers: Maximum number of layers to support (default: 16)

        Raises:
            ValueError: If max_layers is less than 1
        """
        super().__init__()

        if max_layers < 1:
            raise ValueError("max_layers must be at least 1")

        self._max_layers = max_layers
        self._current_layer = 0
        self._layer_names: Dict[int, str] = {}
        self._lock = threading.RLock()

        # Keyboard layout and keymap data (set by KeyboardMonitor after connect)
        self._key_defs: List[Dict[str, Any]] = []
        # all_keymaps[layer][key_index] = 16-bit keycode
        self._all_keymaps: List[List[int]] = []

        # Initialize default layer names
        self._initialize_default_names()

        logger.info(f"LayerState initialized with {max_layers} layers")

    def _initialize_default_names(self) -> None:
        """
        Initialize default layer names.

        Sets up default names for all layers:
        - Layer 0: "Base"
        - Layer 1+: "Layer 1", "Layer 2", etc.
        """
        with self._lock:
            self._layer_names[0] = "Base"
            for i in range(1, self._max_layers):
                self._layer_names[i] = f"Layer {i}"

    def update_layer(self, layer: int) -> None:
        """
        Update the current layer.

        This method updates the current layer and emits the layer_changed
        signal if the layer has actually changed. Thread-safe.

        Args:
            layer: The new layer number (0-indexed)

        Raises:
            ValueError: If layer is out of valid range

        Example:
            >>> layer_state = LayerState()
            >>> layer_state.update_layer(3)
        """
        if not isinstance(layer, int):
            raise TypeError(f"layer must be an integer, got {type(layer)}")

        if layer < 0 or layer >= self._max_layers:
            raise ValueError(
                f"layer must be between 0 and {self._max_layers - 1}, got {layer}"
            )

        layer_actually_changed = False
        with self._lock:
            if self._current_layer != layer:
                old_layer = self._current_layer
                self._current_layer = layer
                layer_actually_changed = True
                logger.debug(f"Layer changed from {old_layer} to {layer}")
            else:
                logger.debug(f"Layer unchanged: {layer}")

        # Emit signal after releasing the lock to avoid potential deadlocks
        if layer_actually_changed:
            self.layer_changed.emit(layer)

    def get_current_layer(self) -> int:
        """
        Get the current layer.

        Returns:
            int: The current layer number (0-indexed)

        Example:
            >>> layer_state = LayerState()
            >>> layer_state.update_layer(2)
            >>> print(layer_state.get_current_layer())
            2
        """
        with self._lock:
            return self._current_layer

    def get_layer_name(self, layer: int) -> str:
        """
        Get the name for a specific layer.

        Args:
            layer: The layer number (0-indexed)

        Returns:
            str: The layer name, or "Unknown" if layer is out of range

        Example:
            >>> layer_state = LayerState()
            >>> print(layer_state.get_layer_name(0))
            Base
            >>> print(layer_state.get_layer_name(1))
            Layer 1
        """
        if not isinstance(layer, int):
            raise TypeError(f"layer must be an integer, got {type(layer)}")

        with self._lock:
            if 0 <= layer < self._max_layers:
                return self._layer_names.get(layer, "Unknown")
            return "Unknown"

    def set_layer_name(self, layer: int, name: str) -> None:
        """
        Set a custom name for a specific layer.

        Args:
            layer: The layer number (0-indexed)
            name: The new name for the layer

        Raises:
            ValueError: If layer is out of valid range
            TypeError: If name is not a string

        Example:
            >>> layer_state = LayerState()
            >>> layer_state.set_layer_name(2, "Gaming")
            >>> print(layer_state.get_layer_name(2))
            Gaming
        """
        if not isinstance(layer, int):
            raise TypeError(f"layer must be an integer, got {type(layer)}")

        if not isinstance(name, str):
            raise TypeError(f"name must be a string, got {type(name)}")

        if layer < 0 or layer >= self._max_layers:
            raise ValueError(
                f"layer must be between 0 and {self._max_layers - 1}, got {layer}"
            )

        with self._lock:
            old_name = self._layer_names.get(layer, "")
            self._layer_names[layer] = name
            logger.debug(f"Layer {layer} name changed from '{old_name}' to '{name}'")

    def get_all_layer_names(self) -> Dict[int, str]:
        """
        Get all layer names.

        Returns:
            Dict[int, str]: Dictionary mapping layer numbers to names

        Example:
            >>> layer_state = LayerState(max_layers=4)
            >>> names = layer_state.get_all_layer_names()
            >>> for layer, name in names.items():
            ...     print(f"{layer}: {name}")
        """
        with self._lock:
            return self._layer_names.copy()

    def reset_layer_names(self) -> None:
        """
        Reset all layer names to defaults.

        This method restores the default layer names:
        - Layer 0: "Base"
        - Layer 1+: "Layer 1", "Layer 2", etc.

        Example:
            >>> layer_state = LayerState()
            >>> layer_state.set_layer_name(0, "Custom Base")
            >>> layer_state.reset_layer_names()
            >>> print(layer_state.get_layer_name(0))
            Base
        """
        with self._lock:
            self._initialize_default_names()
            logger.debug("Layer names reset to defaults")

    @property
    def max_layers(self) -> int:
        """
        Get the maximum number of layers.

        Returns:
            int: Maximum number of layers supported
        """
        return self._max_layers

    def set_keyboard_data(
        self,
        key_defs: List[Dict[str, Any]],
        all_keymaps: List[List[int]],
        num_layers: Optional[int] = None,
    ) -> None:
        """
        Store keyboard layout definition and full keymap data.

        Args:
            key_defs:    List of key position dicts from vial_protocol.extract_layout_keys()
            all_keymaps: [layer][key_index] → 16-bit keycode
            num_layers:  Actual layer count (overrides max_layers if provided)
        """
        with self._lock:
            self._key_defs    = key_defs
            self._all_keymaps = all_keymaps
            if num_layers and 1 <= num_layers <= 32:
                self._max_layers = num_layers
        self.keymap_loaded.emit()

    def get_keyboard_data(self):
        """
        Return (key_defs, all_keymaps) tuple.
        """
        with self._lock:
            return list(self._key_defs), [list(km) for km in self._all_keymaps]

    def is_valid_layer(self, layer: int) -> bool:
        """
        Check if a layer number is valid.

        Args:
            layer: The layer number to check

        Returns:
            bool: True if the layer is valid, False otherwise

        Example:
            >>> layer_state = LayerState(max_layers=8)
            >>> layer_state.is_valid_layer(5)
            True
            >>> layer_state.is_valid_layer(10)
            False
        """
        if not isinstance(layer, int):
            return False
        return 0 <= layer < self._max_layers

    def get_layer_info(self, layer: int) -> Optional[Dict[str, any]]:
        """
        Get detailed information about a layer.

        Args:
            layer: The layer number (0-indexed)

        Returns:
            Optional[Dict[str, any]]: Dictionary containing layer information,
                or None if layer is invalid. Contains:
                - layer: int - Layer number
                - name: str - Layer name
                - is_current: bool - Whether this is the current layer

        Example:
            >>> layer_state = LayerState()
            >>> layer_state.update_layer(2)
            >>> info = layer_state.get_layer_info(2)
            >>> print(f"{info['name']} (current: {info['is_current']})")
            Layer 2 (current: True)
        """
        if not self.is_valid_layer(layer):
            return None

        with self._lock:
            return {
                "layer": layer,
                "name": self._layer_names.get(layer, "Unknown"),
                "is_current": self._current_layer == layer,
            }
