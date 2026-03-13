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
from src.utils.hid_utils import (
    close_device, find_console_interface, find_vial_devices, open_console_device,
    open_device, open_device_by_path, read_console_layer, read_matrix_state,
)
from src.utils.vial_protocol import (
    extract_layout_keys,
    get_all_keymaps,
    get_keyboard_info,
    get_keyboard_layout_json,
    get_layer_count_from_json,
    get_tap_dance_count,
    get_tap_dance_entry,
)

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
        self._console_device: Optional[Any] = None
        self._has_console: bool = False
        self._lock = threading.RLock()

        # Layer state machine — mirrors QMK's runtime layer tracking.
        # Updated only from the monitor thread; read also from monitor thread.
        self._prev_bits: set = set()           # matrix bits from last poll
        self._key_press_times: dict = {}       # bit_idx -> float (time.time())
        self._mo_layers: set = set()           # layers held via MO / LT
        self._tg_layers: set = set()           # layers toggled on via TG
        self._default_layer: int = 0           # set by DF / TO
        self._tap_dance_entries: dict = {}     # td_idx -> {on_tap, on_hold, …}
        self._tapping_term_ms: float = 200.0  # ms — matches QMK default
        self._num_layers: int = 0              # set after keyboard data loads

        # Cached matrix lookup maps; populated after keyboard data loads.
        self._bit_to_pos: dict = {}            # bit_idx -> (row, col)
        self._pos_to_idx: dict = {}            # (row, col) -> key_defs index
        self._layer0_keycodes: list = []       # flat keycodes for layer 0

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

                # Try to open the QMK HID console interface for firmware layer broadcast
                import hid as _hid
                all_ifaces = _hid.enumerate(vendor_id, product_id)
                console_iface = find_console_interface(all_ifaces)
                if console_iface:
                    console_path = console_iface.get("path")
                    console_dev = open_console_device(console_path)
                    if console_dev:
                        self._console_device = console_dev
                        self._has_console = True
                        logger.info("HID console interface opened — using firmware layer broadcast")
                    else:
                        logger.info("Console interface found but could not open — using matrix simulation")
                else:
                    logger.info("No HID console interface — using matrix simulation")

                logger.info("Device connected successfully")
                self.device_found.emit(device_info)

                # Read keyboard layout and full keymap in a background thread
                # so we don't block the monitor loop
                import threading as _threading
                _threading.Thread(
                    target=self._load_keyboard_data,
                    args=(device,),
                    daemon=True,
                ).start()

                # Read initial layer
                self._read_and_update_layer()
            else:
                logger.warning("Failed to open device")
                self.error.emit("Failed to open Vial device")

        except Exception as e:
            logger.error(f"Error connecting to device: {e}")
            self.error.emit(f"Device connection error: {str(e)}")

    def _load_keyboard_data(self, device) -> None:
        """
        Read the keyboard layout definition and full keymap from the device
        and push them into LayerState.  Runs in a background thread.

        Layout JSON must be fetched from interface 2 (Vial RAW HID).
        Keycode reads (VIA cmd 0x04) stay on interface 1 (the main device handle).
        """
        try:
            kb_info = get_keyboard_info(device)
            rows    = kb_info["rows"]
            cols    = kb_info["cols"]
            layers  = kb_info["layers"]

            logger.info(f"Keyboard defaults: {layers} layers, {rows} rows, {cols} cols")

            # Try to get the physical layout JSON from the firmware.
            # Vial commands use a 0xFE prefix on the same interface as VIA.
            layout_json = get_keyboard_layout_json(device)
            if layout_json:
                key_defs = extract_layout_keys(layout_json)
                logger.info(f"Layout: {len(key_defs)} keys from firmware JSON")

                # Derive layer count from JSON (most reliable source)
                json_layers = get_layer_count_from_json(layout_json)
                if json_layers:
                    layers = json_layers
                    logger.info(f"Layer count from JSON: {layers}")

                # Derive rows/cols from the max matrix coordinates in key_defs
                if key_defs:
                    rows = max(k["row"] for k in key_defs) + 1
                    cols = max(k["col"] for k in key_defs) + 1
                    logger.info(f"Matrix from layout: {rows} rows, {cols} cols")
            else:
                # Fall back to a flat row×col grid
                logger.warning("No layout JSON from firmware – using flat grid fallback")
                key_defs = []
                for r in range(rows):
                    for c in range(cols):
                        key_defs.append({
                            "x": float(c), "y": float(r),
                            "w": 1.0, "h": 1.0,
                            "row": r, "col": c,
                        })

            logger.info(f"Keyboard: {layers} layers, {rows} rows, {cols} cols")

            # Read keymaps for all layers.
            # Build a flat list per layer: index matches key_defs order.
            raw_keymaps = get_all_keymaps(device, layers, rows, cols)

            # Convert [layer][row][col] → [layer][key_index]
            flat_keymaps = []
            for layer_data in raw_keymaps:
                flat: list = []
                for kd in key_defs:
                    r, c = kd["row"], kd["col"]
                    if r < len(layer_data) and c < len(layer_data[r]):
                        flat.append(layer_data[r][c])
                    else:
                        flat.append(0)
                flat_keymaps.append(flat)

            self._num_layers = layers
            self._layer_state.set_keyboard_data(key_defs, flat_keymaps, num_layers=layers)
            logger.info("Keyboard data loaded into LayerState")

            # Cache matrix position lookup maps for the hot polling loop.
            import math
            bits_per_row = math.ceil(cols / 8) * 8
            self._bit_to_pos = {
                kd["row"] * bits_per_row + kd["col"]: (kd["row"], kd["col"])
                for kd in key_defs
            }
            self._pos_to_idx = {
                (kd["row"], kd["col"]): i for i, kd in enumerate(key_defs)
            }
            self._layer0_keycodes = flat_keymaps[0] if flat_keymaps else []

            # Read tap dance configurations so TD key actions are known.
            try:
                td_count = get_tap_dance_count(device)
                logger.info(f"Tap dance entries in firmware: {td_count}")
                td_entries: dict = {}
                for i in range(td_count):
                    entry = get_tap_dance_entry(device, i)
                    if entry:
                        td_entries[i] = entry
                        logger.debug(
                            f"  TD({i}): on_tap=0x{entry['on_tap']:04x} "
                            f"on_hold=0x{entry['on_hold']:04x} "
                            f"custom_term={entry['custom_tapping_term']}ms"
                        )
                self._tap_dance_entries = td_entries
            except Exception as td_err:
                logger.warning(f"Could not load tap dance configs: {td_err}")

        except Exception as e:
            logger.error(f"Failed to load keyboard data: {e}")
            self.error.emit(f"Keymap load error: {e}")

    def _close_current_device(self) -> None:
        """
        Close the currently connected device.
        """
        with self._lock:
            if self._console_device:
                try:
                    close_device(self._console_device)
                    logger.debug("Console device closed")
                except Exception as e:
                    logger.error(f"Error closing console device: {e}")
                self._console_device = None
                self._has_console = False

            if self._current_device:
                try:
                    close_device(self._current_device)
                    logger.debug("Current device closed")
                except Exception as e:
                    logger.error(f"Error closing device: {e}")

                self._current_device = None
                self._current_device_info = None

    def _layer_mod(self, n: int) -> int:
        """
        Clamp layer n to the valid range [0, num_layers-1].

        QMK firmware stores layer state as a bitmask.  On keyboards compiled
        with LAYER_STATE_8BIT, DF(33) effectively targets layer 33 % 8 = 1
        because the uint8_t bitmask wraps.  We replicate that here.
        """
        if self._num_layers > 0:
            return n % self._num_layers
        return n

    def _apply_layer_action(self, code: int) -> None:
        """
        Apply a QMK layer action keycode to the internal layer state.

        Handles: DF (set default layer), TG (toggle layer), TO (switch to layer).
        MO and LT are handled separately because they are hold-activated.
        """
        if 0x5200 <= code <= 0x52FF:
            # DF(n): set default layer (persists until next DF/TO)
            n = self._layer_mod(code & 0xFF)
            self._default_layer = n
            logger.debug(f"DF: default layer → {n}")
        elif 0x5300 <= code <= 0x53FF:
            # TG(n): toggle layer n on/off
            n = self._layer_mod(code & 0xFF)
            if n in self._tg_layers:
                self._tg_layers.discard(n)
                logger.debug(f"TG({n}): layer OFF")
            else:
                self._tg_layers.add(n)
                logger.debug(f"TG({n}): layer ON")
        elif 0x5000 <= code <= 0x50FF:
            # TO(n): activate layer n, deactivate all others
            n = self._layer_mod(code & 0xFF)
            self._default_layer = n
            self._tg_layers.clear()
            logger.debug(f"TO({n}): switched to layer {n}")

    def _read_and_update_layer(self) -> None:
        """
        Maintain a QMK-compatible layer state machine by tracking matrix
        press/release transitions, then emit the computed active layer.

        Layer rules mirrored from QMK:
          MO(n) / LT(n,kc): layer active while key is physically held.
          TG(n):             toggle layer on tap (brief press + release).
          DF(n):             set default layer on tap.
          TO(n):             switch to layer n (clear others) on tap.
          TD(n):             resolve to on_tap or on_hold depending on
                             how long the key was held vs tapping_term.

        Active layer = max bit set in (default_layer | tg_layers | mo_layers).
        """
        with self._lock:
            device = self._current_device
        if device is None:
            return

        try:
            # Fast path: firmware broadcasts layer over HID console
            if self._has_console and self._console_device:
                layer = read_console_layer(self._console_device)
                if layer is not None:
                    self._layer_state.update_layer(layer)
                return

            pressed_bits = read_matrix_state(device)
            if pressed_bits is None:
                return

            now = time.time()

            # Use cached maps; bail if keyboard data not loaded yet
            bit_to_pos = self._bit_to_pos
            pos_to_idx = self._pos_to_idx
            layer0     = self._layer0_keycodes
            if not bit_to_pos or not layer0:
                self._prev_bits = pressed_bits
                return

            prev_bits    = self._prev_bits
            new_presses  = pressed_bits - prev_bits
            new_releases = prev_bits - pressed_bits

            # --- Record press timestamps ---
            for bit in new_presses:
                self._key_press_times[bit] = now

            # --- Process key presses: activate hold-type layers immediately ---
            for bit in new_presses:
                pos = bit_to_pos.get(bit)
                if pos is None:
                    continue
                idx = pos_to_idx.get(pos)
                if idx is None or idx >= len(layer0):
                    continue
                code = layer0[idx]

                if 0x5100 <= code <= 0x51FF:
                    # MO(n): activate on press
                    self._mo_layers.add(code & 0xFF)
                elif 0x4000 <= code <= 0x4FFF:
                    # LT(layer, kc): activate layer on press
                    self._mo_layers.add((code >> 8) & 0x0F)

            # --- Process key releases: resolve tap vs hold, deactivate layers ---
            for bit in new_releases:
                press_time = self._key_press_times.pop(bit, None)
                hold_ms    = (now - (press_time or now)) * 1000
                is_tap     = press_time is not None and hold_ms < self._tapping_term_ms

                pos = bit_to_pos.get(bit)
                if pos is None:
                    continue
                idx = pos_to_idx.get(pos)
                if idx is None or idx >= len(layer0):
                    continue
                code = layer0[idx]

                if 0x5100 <= code <= 0x51FF:
                    # MO(n): deactivate on release
                    self._mo_layers.discard(code & 0xFF)

                elif 0x4000 <= code <= 0x4FFF:
                    # LT(layer, kc): deactivate layer; tap action is a normal keycode
                    self._mo_layers.discard((code >> 8) & 0x0F)

                elif 0x5700 <= code <= 0x577F:
                    # TD(n): resolve via tap dance config
                    td_idx = code & 0x7F
                    entry  = self._tap_dance_entries.get(td_idx)
                    if entry:
                        # Use entry's custom tapping term if set
                        term = (entry["custom_tapping_term"]
                                or self._tapping_term_ms)
                        is_td_tap = press_time is not None and hold_ms < term
                        action = entry["on_tap"] if is_td_tap else entry["on_hold"]
                        logger.debug(
                            f"TD({td_idx}) {'tap' if is_td_tap else 'hold'} "
                            f"({hold_ms:.0f}ms) → action 0x{action:04x}"
                        )
                        self._apply_layer_action(action)

                elif is_tap:
                    # TG / DF / TO: apply on tap (brief press)
                    self._apply_layer_action(code)

            # --- Commit and emit ---
            self._prev_bits = pressed_bits
            active  = ({self._default_layer} | self._tg_layers | self._mo_layers)
            highest = max(active) if active else 0
            # Clamp to valid range; out-of-range values can appear from
            # keycodes like DF(33) on an 8-layer keyboard (handled by
            # _layer_mod in _apply_layer_action, but guard here too).
            if self._num_layers > 0:
                highest = min(highest, self._num_layers - 1)
            self._layer_state.update_layer(highest)

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
