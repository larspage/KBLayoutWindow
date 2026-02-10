"""
Tests for Keyboard Monitor Module

This module contains unit tests for the KeyboardMonitor class, which provides
USB HID monitoring for Vial-compatible keyboards with PyQt6 signals.
"""

import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.keyboard_monitor import KeyboardMonitor
from src.core.layer_state import LayerState


class TestKeyboardMonitorInitialization:
    """Test suite for KeyboardMonitor initialization."""

    def test_initialization(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test KeyboardMonitor initialization.

        Verifies that KeyboardMonitor is initialized correctly
        with the provided configuration and layer state.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        assert monitor.is_running() is False
        assert monitor.get_poll_interval() == 100

    def test_initialization_default_poll_interval(self, layer_state: LayerState) -> None:
        """
        Test initialization with default poll interval.

        Verifies that the default poll interval is used when
        not specified in the configuration.
        """
        config = {}
        monitor = KeyboardMonitor(config, layer_state)

        assert monitor.get_poll_interval() == 100

    def test_initialization_custom_poll_interval(self, layer_state: LayerState) -> None:
        """
        Test initialization with custom poll interval.

        Verifies that a custom poll interval is used when
        specified in the configuration.
        """
        config = {"poll_interval_ms": 200}
        monitor = KeyboardMonitor(config, layer_state)

        assert monitor.get_poll_interval() == 200

    def test_initialization_invalid_layer_state(self, keyboard_config: Dict[str, Any]) -> None:
        """
        Test initialization with invalid layer state.

        Verifies that TypeError is raised when layer_state is
        not a LayerState instance.
        """
        with pytest.raises(TypeError, match="layer_state must be a LayerState instance"):
            KeyboardMonitor(keyboard_config, None)  # type: ignore

        with pytest.raises(TypeError, match="layer_state must be a LayerState instance"):
            KeyboardMonitor(keyboard_config, "not a layer state")  # type: ignore


class TestStartStop:
    """Test suite for start and stop methods."""

    def test_start_stop(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test starting and stopping the monitor.

        Verifies that the monitor can be started and stopped
        correctly.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        assert monitor.is_running() is False

        monitor.start()
        assert monitor.is_running() is True

        monitor.stop()
        assert monitor.is_running() is False

    def test_start_already_running(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test starting an already running monitor.

        Verifies that starting an already running monitor
        doesn't cause issues.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.start()

        # Should not raise an exception
        monitor.start()
        assert monitor.is_running() is True

        monitor.stop()

    def test_stop_not_running(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test stopping a monitor that's not running.

        Verifies that stopping a non-running monitor doesn't
        cause issues.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        # Should not raise an exception
        monitor.stop()
        assert monitor.is_running() is False

    def test_start_creates_thread(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test that start creates a monitoring thread.

        Verifies that a new thread is created when starting
        the monitor.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.start()

        # Give thread time to start
        time.sleep(0.1)

        assert monitor._thread is not None
        assert monitor._thread.is_alive()

        monitor.stop()


class TestIsRunning:
    """Test suite for is_running method."""

    def test_is_running_initially_false(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test that is_running returns False initially.

        Verifies that a newly created monitor is not running.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        assert monitor.is_running() is False

    def test_is_running_after_start(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test that is_running returns True after start.

        Verifies that is_running returns True after the monitor
        has been started.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.start()

        assert monitor.is_running() is True

        monitor.stop()

    def test_is_running_after_stop(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test that is_running returns False after stop.

        Verifies that is_running returns False after the monitor
        has been stopped.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.start()
        monitor.stop()

        assert monitor.is_running() is False


class TestDeviceDetection:
    """Test suite for device detection functionality."""

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.read_layer_data")
    def test_device_detection(
        self,
        mock_read_layer: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test automatic device detection.

        Verifies that the monitor automatically detects and
        connects to Vial devices.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = mock_hid_device
        mock_read_layer.return_value = 2

        device_found_emitted = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.device_found.connect(lambda dev: device_found_emitted.append(dev))

        monitor.start()
        time.sleep(0.2)  # Give time for device detection
        monitor.stop()

        assert len(device_found_emitted) > 0
        assert device_found_emitted[0]["product_string"] == "Test Keyboard"

    @patch("src.core.keyboard_monitor.find_vial_devices")
    def test_no_device_found(
        self,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
    ) -> None:
        """
        Test behavior when no device is found.

        Verifies that the monitor handles the absence of devices
        gracefully.
        """
        mock_find_devices.return_value = []

        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        # Should not crash
        assert monitor.is_running() is False

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.close_device")
    def test_device_lost(
        self,
        mock_close_device: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test device disconnection detection.

        Verifies that the monitor detects when a device is
        disconnected and emits the device_lost signal.
        """
        # First return a device, then return empty list
        mock_find_devices.side_effect = [[mock_vial_device_info], []]
        mock_open_device.return_value = mock_hid_device

        device_lost_emitted = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.device_lost.connect(lambda dev: device_lost_emitted.append(dev))

        monitor.start()
        time.sleep(0.3)  # Give time for device detection and loss
        monitor.stop()

        assert len(device_lost_emitted) > 0


class TestLayerPolling:
    """Test suite for layer polling functionality."""

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.read_layer_data")
    def test_layer_polling(
        self,
        mock_read_layer: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test polling for layer changes.

        Verifies that the monitor polls the device for layer
        changes and updates the layer state.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = mock_hid_device
        mock_read_layer.return_value = 3

        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        assert layer_state.get_current_layer() == 3

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.read_layer_data")
    def test_layer_change_emitted(
        self,
        mock_read_layer: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test that layer_changed signal is emitted.

        Verifies that the layer_changed signal is emitted when
        the layer changes.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = mock_hid_device
        mock_read_layer.return_value = 5

        layer_changes = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.layer_changed.connect(lambda layer: layer_changes.append(layer))

        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        assert len(layer_changes) > 0
        assert 5 in layer_changes

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.read_layer_data")
    def test_layer_read_failure(
        self,
        mock_read_layer: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test handling of layer read failures.

        Verifies that the monitor handles read failures gracefully
        without crashing.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = mock_hid_device
        mock_read_layer.return_value = None  # Simulate read failure

        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        # Should not crash
        assert monitor.is_running() is False


class TestErrorHandling:
    """Test suite for error handling."""

    @patch("src.core.keyboard_monitor.find_vial_devices")
    def test_find_devices_error(
        self,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
    ) -> None:
        """
        Test handling of device enumeration errors.

        Verifies that errors during device enumeration are
        handled gracefully and the error signal is emitted.
        """
        mock_find_devices.side_effect = Exception("Enumeration error")

        errors = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.error.connect(lambda err: errors.append(err))

        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        assert len(errors) > 0

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    def test_open_device_error(
        self,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
    ) -> None:
        """
        Test handling of device open errors.

        Verifies that errors during device opening are handled
        gracefully and the error signal is emitted.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = None  # Simulate open failure

        errors = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.error.connect(lambda err: errors.append(err))

        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        assert len(errors) > 0

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.read_layer_data")
    def test_read_layer_error(
        self,
        mock_read_layer: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test handling of layer read errors.

        Verifies that errors during layer reading are handled
        gracefully and the error signal is emitted.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = mock_hid_device
        mock_read_layer.side_effect = Exception("Read error")

        errors = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.error.connect(lambda err: errors.append(err))

        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        assert len(errors) > 0


class TestSignals:
    """Test suite for signal emissions."""

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.read_layer_data")
    def test_device_found_signal(
        self,
        mock_read_layer: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test device_found signal emission.

        Verifies that the device_found signal is emitted when
        a device is connected.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = mock_hid_device
        mock_read_layer.return_value = 0

        device_found_emitted = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.device_found.connect(lambda dev: device_found_emitted.append(dev))

        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        assert len(device_found_emitted) > 0
        assert device_found_emitted[0]["vendor_id"] == 0x5342

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.close_device")
    def test_device_lost_signal(
        self,
        mock_close_device: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test device_lost signal emission.

        Verifies that the device_lost signal is emitted when
        a device is disconnected.
        """
        mock_find_devices.side_effect = [[mock_vial_device_info], []]
        mock_open_device.return_value = mock_hid_device

        device_lost_emitted = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.device_lost.connect(lambda dev: device_lost_emitted.append(dev))

        monitor.start()
        time.sleep(0.3)
        monitor.stop()

        assert len(device_lost_emitted) > 0

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.read_layer_data")
    def test_layer_changed_signal(
        self,
        mock_read_layer: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test layer_changed signal emission.

        Verifies that the layer_changed signal is emitted when
        the layer changes.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = mock_hid_device
        mock_read_layer.return_value = 7

        layer_changes = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.layer_changed.connect(lambda layer: layer_changes.append(layer))

        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        assert len(layer_changes) > 0
        assert 7 in layer_changes

    @patch("src.core.keyboard_monitor.find_vial_devices")
    def test_error_signal(
        self,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
    ) -> None:
        """
        Test error signal emission.

        Verifies that the error signal is emitted when an
        error occurs.
        """
        mock_find_devices.side_effect = Exception("Test error")

        errors = []
        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.error.connect(lambda err: errors.append(err))

        monitor.start()
        time.sleep(0.2)
        monitor.stop()

        assert len(errors) > 0


class TestPollInterval:
    """Test suite for poll interval methods."""

    def test_get_poll_interval(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test getting the poll interval.

        Verifies that get_poll_interval returns the correct
        interval in milliseconds.
        """
        config = {"poll_interval_ms": 250}
        monitor = KeyboardMonitor(config, layer_state)

        assert monitor.get_poll_interval() == 250

    def test_set_poll_interval(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test setting the poll interval.

        Verifies that the poll interval can be changed.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        monitor.set_poll_interval(200)
        assert monitor.get_poll_interval() == 200

    def test_set_poll_interval_invalid_too_small(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test setting poll interval to too small a value.

        Verifies that ValueError is raised when trying to set
        an interval less than 10ms.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        with pytest.raises(ValueError, match="interval_ms must be at least 10"):
            monitor.set_poll_interval(5)

    def test_set_poll_interval_invalid_type(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test setting poll interval with invalid type.

        Verifies that TypeError is raised when trying to set
        an interval with a non-integer value.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        with pytest.raises(TypeError, match="interval_ms must be an integer"):
            monitor.set_poll_interval("100")  # type: ignore


class TestGetCurrentDeviceInfo:
    """Test suite for get_current_device_info method."""

    @patch("src.core.keyboard_monitor.find_vial_devices")
    @patch("src.core.keyboard_monitor.open_device")
    @patch("src.core.keyboard_monitor.read_layer_data")
    def test_get_current_device_info(
        self,
        mock_read_layer: Mock,
        mock_open_device: Mock,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
        mock_hid_device: Mock,
    ) -> None:
        """
        Test getting current device information.

        Verifies that get_current_device_info returns the
        correct device information when a device is connected.
        """
        mock_find_devices.return_value = [mock_vial_device_info]
        mock_open_device.return_value = mock_hid_device
        mock_read_layer.return_value = 0

        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.start()
        time.sleep(0.2)

        device_info = monitor.get_current_device_info()

        assert device_info is not None
        assert device_info["vendor_id"] == 0x5342
        assert device_info["product_string"] == "Test Keyboard"

        monitor.stop()

    def test_get_current_device_info_no_device(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test getting device info when no device is connected.

        Verifies that None is returned when no device is connected.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        device_info = monitor.get_current_device_info()

        assert device_info is None


class TestForceDeviceScan:
    """Test suite for force_device_scan method."""

    @patch("src.core.keyboard_monitor.find_vial_devices")
    def test_force_device_scan(
        self,
        mock_find_devices: Mock,
        keyboard_config: Dict[str, Any],
        layer_state: LayerState,
        mock_vial_device_info: Dict[str, Any],
    ) -> None:
        """
        Test forcing an immediate device scan.

        Verifies that force_device_scan triggers an immediate
        scan for devices.
        """
        mock_find_devices.return_value = [mock_vial_device_info]

        monitor = KeyboardMonitor(keyboard_config, layer_state)
        monitor.force_device_scan()

        # Give time for the scan to complete
        time.sleep(0.1)

        mock_find_devices.assert_called()


class TestLayerStateConnection:
    """Test suite for layer state signal connection."""

    def test_layer_state_signal_forwarded(self, keyboard_config: Dict[str, Any], layer_state: LayerState) -> None:
        """
        Test that layer state changes are forwarded.

        Verifies that layer changes from LayerState are forwarded
        through the monitor's layer_changed signal.
        """
        monitor = KeyboardMonitor(keyboard_config, layer_state)

        forwarded_layers = []
        monitor.layer_changed.connect(lambda layer: forwarded_layers.append(layer))

        # Simulate layer state change
        layer_state.update_layer(4)

        assert 4 in forwarded_layers
