"""
Keyboard Monitor Module

This module provides USB HID monitoring for Vial-compatible keyboards.
It runs in a separate thread to poll the keyboard for layer changes and
emits PyQt6 signals for UI updates.

Classes:
    KeyboardMonitor: Thread-based keyboard layer monitor with PyQt6 signals
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.layer_state import LayerState
from src.utils.hid_utils import close_device, find_vial_devices, open_device, read_layer_data

# Configure logging
logger = logging.getLogger(__name__)


class KeyboardMonitor(QObject):
    """
    Thread-based keyboard layer monitor with PyQt6 signals.

    This class monitors Vial-compatible keyboards for layer changes in a
    separate thread. It polls the device at regular intervals and emits
    signals when the layer changes, when a device is found, or when errors occur.

    Signals:
        device_found(dict): Emitted when a Vial keyboard is found.
            The parameter is a dictionary with device information.
        device_lost(dict): Emitted when a Vial keyboard is disconnected.
            The parameter is a dictionary with device information.
        error(str): Emitted when an error occurs during monitoring.
            The parameter is the error message.
        layer_changed(int): Emitted when the current layer changes.
            The parameter is the new layer number (0-indexed).

    Attributes:
        config: Configuration dictionary
        layer_state: LayerState instance for tracking layer changes
        poll_interval: Polling interval in milliseconds

    Example:
        >>> layer_state = LayerState()
        >>> config = {"poll_interval_ms": 100}
        >>> monitor = KeyboardMonitor(config, layer_state)
        >>> monitor.device_found.connect(lambda dev: print(f"Found: {dev['product_string']}"))
        >>> monitor.error.connect(lambda err: print(f"Error: {err}"))
        >>> monitor.start()
        >>> # ... monitor runs in background ...
        >>> monitor.stop()
    """

    # PyQt6 signals for cross-thread communication
    device_found = pyqtSignal(dict)
    device_lost = pyqtSignal(dict)
    error = pyqtSignal(str)
    layer_changed = pyqtSignal(int)

    def __init__(self, config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Initialize the keyboard monitor.

        Args:
            config: Configuration dictionary. Expected keys:
                - poll_interval_ms: Polling interval in milliseconds (default: 100)
            layer_state: LayerState instance for tracking layer changes

        Raises:
            TypeError: If layer_state is not a LayerState instance
        """
        super().__init__()

        if not isinstance(layer_state, LayerState):
            raise TypeError(
                f"layer_state must be a LayerState instance, got {type(layer_state)}"
            )

        self._config = config
        self._layer_state = layer_state
        self._poll_interval = config.get("poll_interval_ms", 100) / 1000.0  # Convert to seconds

        # Thread management
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Device tracking
        self._current_device: Optional[Any] = None
        self._current_device_info: Optional[Dict[str, Any]] = None
        self._lock = threading.RLock()

        # Connect layer state signal to forward layer changes
        self._layer_state.layer_changed.connect(self._on_layer_state_changed)

        logger.info(
            f"KeyboardMonitor initialized with poll interval: {self._poll_interval}s"
        )

    def _on_layer_state_changed(self, layer: int) -> None:
        """
        Handle layer state changes from LayerState.

        This method is called when the LayerState emits a layer_changed signal.
        It forwards the signal to the monitor's layer_changed signal.

        Args:
            layer: The new layer number (0-indexed)
        """
        logger.debug(f"Forwarding layer change: {layer}")
        self.layer_changed.emit(layer)

    def start(self) -> None:
        """
        Start the keyboard monitoring thread.

        This method starts a new thread that polls the keyboard for layer changes.
        If the monitor is already running, this method does nothing.

        Raises:
            RuntimeError: If the thread cannot be started

        Example:
            >>> monitor = KeyboardMonitor(config, layer_state)
            >>> monitor.start()
        """
        with self._lock:
            if self._running:
                logger.warning("Keyboard monitor is already running")
                return

            self._running = True
            self._stop_event.clear()

        # Create and start the monitoring thread
        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="KeyboardMonitorThread",
            daemon=True,
        )

        try:
            self._thread.start()
            logger.info("Keyboard monitor started")
        except Exception as e:
            self._running = False
            logger.error(f"Failed to start keyboard monitor thread: {e}")
            raise RuntimeError(f"Failed to start keyboard monitor: {e}")

    def stop(self) -> None:
        """
        Stop the keyboard monitoring thread.

        This method signals the monitoring thread to stop and waits for it
        to terminate. If the monitor is not running, this method does nothing.

        Example:
            >>> monitor = KeyboardMonitor(config, layer_state)
            >>> monitor.start()
            >>> # ... monitor runs ...
            >>> monitor.stop()
        """
        with self._lock:
            if not self._running:
                logger.warning("Keyboard monitor is not running")
                return

            logger.info("Stopping keyboard monitor")
            self._running = False
            self._stop_event.set()

        # Wait for the thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                logger.warning("Keyboard monitor thread did not stop gracefully")

        # Close device if open
        self._close_current_device()

        logger.info("Keyboard monitor stopped")

    def is_running(self) -> bool:
        """
        Check if the monitor is running.

        Returns:
            bool: True if the monitor is running, False otherwise

        Example:
            >>> monitor = KeyboardMonitor(config, layer_state)
            >>> print(monitor.is_running())
            False
            >>> monitor.start()
            >>> print(monitor.is_running())
            True
        """
        with self._lock:
            return self._running

    def _monitor_loop(self) -> None:
        """
        Main monitoring loop.

        This method runs in a separate thread and continuously polls the
        keyboard for layer changes. It handles device detection, layer reading,
        and error recovery.

        The loop continues until the stop event is set.
        """
        logger.info("Monitor loop started")

        while not self._stop_event.is_set():
            try:
                # Check for device
                self._check_device()

                # Read layer data if device is connected
                if self._current_device:
                    self._read_and_update_layer()

                # Wait for the next poll interval
                self._stop_event.wait(self._poll_interval)

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                self.error.emit(f"Monitoring error: {str(e)}")
                # Continue monitoring despite errors

        logger.info("Monitor loop stopped")

    def _check_device(self) -> None:
        """
        Check for Vial devices and manage device connection.

        This method scans for Vial devices and handles device connection
        and disconnection events.
        """
        try:
            # Find Vial devices
            devices = find_vial_devices()

            if not devices:
                # No devices found
                if self._current_device is not None:
                    # Device was lost
                    logger.info("Vial device disconnected")
                    device_info = self._current_device_info or {}
                    self.device_lost.emit(device_info)
                    self._close_current_device()
                return

            # Check if current device is still present
            if self._current_device_info:
                current_vid = self._current_device_info.get("vendor_id")
                current_pid = self._current_device_info.get("product_id")

                # Check if current device is still in the list
                device_still_present = any(
                    d.get("vendor_id") == current_vid and d.get("product_id") == current_pid
                    for d in devices
                )

                if not device_still_present:
                    # Current device was lost
                    logger.info("Current Vial device disconnected")
                    self.device_lost.emit(self._current_device_info)
                    self._close_current_device()

            # If no device is connected, connect to the first one
            if self._current_device is None and devices:
                device_info = devices[0]
                self._connect_device(device_info)

        except Exception as e:
            logger.error(f"Error checking for device: {e}")
            self.error.emit(f"Device check error: {str(e)}")

    def _connect_device(self, device_info: Dict[str, Any]) -> None:
        """
        Connect to a Vial device.

        Args:
            device_info: Device information dictionary
        """
        try:
            vendor_id = device_info.get("vendor_id", 0)
            product_id = device_info.get("product_id", 0)

            logger.info(
                f"Connecting to device: {device_info.get('product_string', 'Unknown')} "
                f"(VID: {vendor_id:04x}, PID: {product_id:04x})"
            )

            device = open_device(vendor_id, product_id)

            if device:
                with self._lock:
                    self._current_device = device
                    self._current_device_info = device_info

                logger.info("Device connected successfully")
                self.device_found.emit(device_info)

                # Read initial layer
                self._read_and_update_layer()
            else:
                logger.warning("Failed to open device")
                self.error.emit("Failed to open Vial device")

        except Exception as e:
            logger.error(f"Error connecting to device: {e}")
            self.error.emit(f"Device connection error: {str(e)}")

    def _close_current_device(self) -> None:
        """
        Close the currently connected device.
        """
        with self._lock:
            if self._current_device:
                try:
                    close_device(self._current_device)
                    logger.debug("Current device closed")
                except Exception as e:
                    logger.error(f"Error closing device: {e}")

                self._current_device = None
                self._current_device_info = None

    def _read_and_update_layer(self) -> None:
        """
        Read layer data from the device and update layer state.

        This method reads the current layer from the connected device and
        updates the LayerState if the layer has changed.
        """
        with self._lock:
            device = self._current_device

        if device is None:
            return

        try:
            layer = read_layer_data(device)

            if layer is not None:
                # Update layer state
                self._layer_state.update_layer(layer)
            else:
                logger.debug("Failed to read layer data from device")

        except Exception as e:
            logger.error(f"Error reading layer data: {e}")
            self.error.emit(f"Layer read error: {str(e)}")

    def set_poll_interval(self, interval_ms: int) -> None:
        """
        Set the polling interval.

        Args:
            interval_ms: New polling interval in milliseconds

        Raises:
            ValueError: If interval_ms is less than 10

        Example:
            >>> monitor = KeyboardMonitor(config, layer_state)
            >>> monitor.set_poll_interval(200)  # Poll every 200ms
        """
        if not isinstance(interval_ms, int):
            raise TypeError(f"interval_ms must be an integer, got {type(interval_ms)}")

        if interval_ms < 10:
            raise ValueError("interval_ms must be at least 10")

        with self._lock:
            self._poll_interval = interval_ms / 1000.0
            logger.info(f"Poll interval set to {interval_ms}ms")

    def get_poll_interval(self) -> int:
        """
        Get the current polling interval.

        Returns:
            int: Polling interval in milliseconds

        Example:
            >>> monitor = KeyboardMonitor(config, layer_state)
            >>> print(monitor.get_poll_interval())
            100
        """
        with self._lock:
            return int(self._poll_interval * 1000)

    def get_current_device_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently connected device.

        Returns:
            Optional[Dict[str, Any]]: Device information dictionary, or None if no device is connected

        Example:
            >>> monitor = KeyboardMonitor(config, layer_state)
            >>> monitor.start()
            >>> # ... wait for device ...
            >>> info = monitor.get_current_device_info()
            >>> if info:
            ...     print(f"Connected to: {info['product_string']}")
        """
        with self._lock:
            if self._current_device_info:
                return self._current_device_info.copy()
            return None

    def force_device_scan(self) -> None:
        """
        Force an immediate device scan.

        This method can be called to trigger an immediate scan for Vial devices,
        bypassing the normal polling interval. This is useful for responding to
        user actions or system events.

        Example:
            >>> monitor = KeyboardMonitor(config, layer_state)
            >>> monitor.start()
            >>> # User clicks "Refresh" button
            >>> monitor.force_device_scan()
        """
        logger.debug("Forcing device scan")
        threading.Thread(target=self._check_device, daemon=True).start()
