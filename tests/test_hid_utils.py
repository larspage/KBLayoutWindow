"""
Tests for HID Utilities Module

This module contains unit tests for the HID utility functions that handle
USB HID communication with Vial-compatible keyboards.
"""

import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import hid_utils


class TestFindVialDevices:
    """Test suite for find_vial_devices function."""

    @patch("src.utils.hid_utils.hid.enumerate")
    def test_find_vial_devices_empty(self, mock_enumerate: Mock) -> None:
        """
        Test finding Vial devices when none are present.

        Verifies that an empty list is returned when no Vial devices
        are found on the system.
        """
        mock_enumerate.return_value = []

        devices = hid_utils.find_vial_devices()

        assert devices == []
        mock_enumerate.assert_called_once()

    @patch("src.utils.hid_utils.hid.enumerate")
    def test_find_vial_devices_single(self, mock_enumerate: Mock, mock_vial_device_info: Dict[str, Any]) -> None:
        """
        Test finding a single Vial device.

        Verifies that a single Vial device is correctly identified
        and returned with proper information.
        """
        mock_enumerate.return_value = [mock_vial_device_info]

        devices = hid_utils.find_vial_devices()

        assert len(devices) == 1
        assert devices[0]["vendor_id"] == 0x5342
        assert devices[0]["product_id"] == 0x0001
        assert devices[0]["product_string"] == "Test Keyboard"

    @patch("src.utils.hid_utils.hid.enumerate")
    def test_find_vial_devices_multiple(self, mock_enumerate: Mock) -> None:
        """
        Test finding multiple Vial devices.

        Verifies that multiple Vial devices are correctly identified
        and returned.
        """
        device1 = {
            "vendor_id": 0x5342,
            "product_id": 0x0001,
            "path": b"/dev/hidraw0",
            "manufacturer_string": "Vial",
            "product_string": "Keyboard 1",
            "serial_number": "TEST1",
            "usage_page": 0xFF60,
            "usage": 0x61,
        }
        device2 = {
            "vendor_id": 0x3496,
            "product_id": 0x0002,
            "path": b"/dev/hidraw1",
            "manufacturer_string": "Vial",
            "product_string": "Keyboard 2",
            "serial_number": "TEST2",
            "usage_page": 0xFF60,
            "usage": 0x61,
        }
        mock_enumerate.return_value = [device1, device2]

        devices = hid_utils.find_vial_devices()

        assert len(devices) == 2
        assert devices[0]["product_string"] == "Keyboard 1"
        assert devices[1]["product_string"] == "Keyboard 2"

    @patch("src.utils.hid_utils.hid.enumerate")
    def test_find_vial_devices_filters_non_vial(self, mock_enumerate: Mock) -> None:
        """
        Test that non-Vial devices are filtered out.

        Verifies that devices without Vial vendor IDs are not
        included in the results.
        """
        vial_device = {
            "vendor_id": 0x5342,
            "product_id": 0x0001,
            "path": b"/dev/hidraw0",
            "manufacturer_string": "Vial",
            "product_string": "Vial Keyboard",
            "serial_number": "TEST",
            "usage_page": 0xFF60,
            "usage": 0x61,
        }
        non_vial_device = {
            "vendor_id": 0x1234,
            "product_id": 0x5678,
            "path": b"/dev/hidraw1",
            "manufacturer_string": "Other",
            "product_string": "Other Device",
            "serial_number": "OTHER",
            "usage_page": 0x0001,
            "usage": 0x0002,
        }
        mock_enumerate.return_value = [vial_device, non_vial_device]

        devices = hid_utils.find_vial_devices()

        assert len(devices) == 1
        assert devices[0]["vendor_id"] == 0x5342

    @patch("src.utils.hid_utils.hid.enumerate")
    def test_find_vial_devices_handles_exception(self, mock_enumerate: Mock) -> None:
        """
        Test that exceptions during enumeration are handled gracefully.

        Verifies that an exception during device enumeration doesn't
        crash the function and returns an empty list.
        """
        mock_enumerate.side_effect = Exception("Enumeration error")

        devices = hid_utils.find_vial_devices()

        assert devices == []


class TestIsVialDevice:
    """Test suite for is_vial_device function."""

    def test_is_vial_device_valid(self, mock_vial_device_info: Dict[str, Any]) -> None:
        """
        Test identifying a valid Vial device.

        Verifies that a device with Vial vendor ID and correct
        usage page/usage is identified as Vial-compatible.
        """
        result = hid_utils.is_vial_device(mock_vial_device_info)

        assert result is True

    def test_is_vial_device_wrong_vendor(self) -> None:
        """
        Test rejecting a device with wrong vendor ID.

        Verifies that a device without a Vial vendor ID is not
        identified as Vial-compatible.
        """
        device_info = {
            "vendor_id": 0x1234,
            "product_id": 0x5678,
            "usage_page": 0xFF60,
            "usage": 0x61,
        }

        result = hid_utils.is_vial_device(device_info)

        assert result is False

    def test_is_vial_device_all_vendor_ids(self) -> None:
        """
        Test all valid Vial vendor IDs.

        Verifies that all known Vial vendor IDs are correctly
        identified.
        """
        vendor_ids = [0x5342, 0x3496, 0x3297]

        for vid in vendor_ids:
            device_info = {
                "vendor_id": vid,
                "product_id": 0x0001,
                "usage_page": 0xFF60,
                "usage": 0x61,
            }
            assert hid_utils.is_vial_device(device_info) is True

    def test_is_vial_device_missing_usage(self) -> None:
        """
        Test Vial device with missing usage information.

        Verifies that a device with Vial vendor ID but missing
        usage information is still identified as Vial-compatible.
        """
        device_info = {
            "vendor_id": 0x5342,
            "product_id": 0x0001,
        }

        result = hid_utils.is_vial_device(device_info)

        assert result is True

    def test_is_vial_device_different_usage(self) -> None:
        """
        Test Vial device with different usage values.

        Verifies that a device with Vial vendor ID but different
        usage values is still identified as Vial-compatible.
        """
        device_info = {
            "vendor_id": 0x5342,
            "product_id": 0x0001,
            "usage_page": 0x0001,
            "usage": 0x0002,
        }

        result = hid_utils.is_vial_device(device_info)

        assert result is True


class TestOpenDevice:
    """Test suite for open_device function."""

    @patch("src.utils.hid_utils.hid.enumerate")
    @patch("src.utils.hid_utils.hid.device")
    def test_open_device_success(self, mock_device_class: Mock, mock_enumerate: Mock, mock_hid_device: Mock) -> None:
        """
        Test successfully opening a HID device.

        Verifies that a device can be opened successfully when
        it exists and is accessible.
        """
        device_info = {
            "vendor_id": 0x5342,
            "product_id": 0x0001,
            "path": b"/dev/hidraw0",
            "product_string": "Test Keyboard",
        }
        mock_enumerate.return_value = [device_info]
        mock_device_class.return_value = mock_hid_device

        device = hid_utils.open_device(0x5342, 0x0001)

        assert device is not None
        mock_enumerate.assert_called_once_with(0x5342, 0x0001)
        mock_device_class.assert_called_once()
        mock_hid_device.open_path.assert_called_once_with(b"/dev/hidraw0")

    @patch("src.utils.hid_utils.hid.enumerate")
    def test_open_device_not_found(self, mock_enumerate: Mock) -> None:
        """
        Test opening a device that doesn't exist.

        Verifies that None is returned when no matching device
        is found.
        """
        mock_enumerate.return_value = []

        device = hid_utils.open_device(0x5342, 0x0001)

        assert device is None

    @patch("src.utils.hid_utils.hid.enumerate")
    def test_open_device_no_path(self, mock_enumerate: Mock) -> None:
        """
        Test opening a device with no path information.

        Verifies that None is returned when device info doesn't
        contain a path.
        """
        device_info = {
            "vendor_id": 0x5342,
            "product_id": 0x0001,
        }
        mock_enumerate.return_value = [device_info]

        device = hid_utils.open_device(0x5342, 0x0001)

        assert device is None

    @patch("src.utils.hid_utils.hid.enumerate")
    @patch("src.utils.hid_utils.hid.device")
    def test_open_device_permission_denied(self, mock_device_class: Mock, mock_enumerate: Mock) -> None:
        """
        Test opening a device with permission denied error.

        Verifies that None is returned when permission is denied
        and the error is logged appropriately.
        """
        device_info = {
            "vendor_id": 0x5342,
            "product_id": 0x0001,
            "path": b"/dev/hidraw0",
            "product_string": "Test Keyboard",
        }
        mock_enumerate.return_value = [device_info]
        mock_device_instance = Mock()
        mock_device_instance.open_path.side_effect = OSError("Permission denied")
        mock_device_class.return_value = mock_device_instance

        device = hid_utils.open_device(0x5342, 0x0001)

        assert device is None


class TestReadLayerData:
    """Test suite for read_layer_data function."""

    def test_read_layer_data_success(self, mock_hid_device: Mock) -> None:
        """
        Test successfully reading layer data from device.

        Verifies that layer data is correctly read and parsed
        from the device response.
        """
        mock_hid_device.read.return_value = [0x00, 0x03, 0x00, 0x00]

        layer = hid_utils.read_layer_data(mock_hid_device)

        assert layer == 3
        mock_hid_device.write.assert_called_once()
        mock_hid_device.read.assert_called_once_with(64, timeout_ms=100)

    def test_read_layer_data_layer_zero(self, mock_hid_device: Mock) -> None:
        """
        Test reading layer 0 from device.

        Verifies that layer 0 is correctly read and returned.
        """
        mock_hid_device.read.return_value = [0x00, 0x00, 0x00, 0x00]

        layer = hid_utils.read_layer_data(mock_hid_device)

        assert layer == 0

    def test_read_layer_data_no_response(self, mock_hid_device: Mock) -> None:
        """
        Test reading layer data when device doesn't respond.

        Verifies that None is returned when the device doesn't
        provide a response.
        """
        mock_hid_device.read.return_value = []

        layer = hid_utils.read_layer_data(mock_hid_device)

        assert layer is None

    def test_read_layer_data_short_response(self, mock_hid_device: Mock) -> None:
        """
        Test reading layer data with short response.

        Verifies that None is returned when the response is
        too short to contain layer information.
        """
        mock_hid_device.read.return_value = [0x00]

        layer = hid_utils.read_layer_data(mock_hid_device)

        assert layer is None

    def test_read_layer_data_os_error(self, mock_hid_device: Mock) -> None:
        """
        Test reading layer data with OSError.

        Verifies that None is returned when an OSError occurs
        during reading.
        """
        mock_hid_device.read.side_effect = OSError("Read error")

        layer = hid_utils.read_layer_data(mock_hid_device)

        assert layer is None

    def test_read_layer_data_write_error(self, mock_hid_device: Mock) -> None:
        """
        Test reading layer data when write fails.

        Verifies that None is returned when writing to the
        device fails.
        """
        mock_hid_device.write.side_effect = OSError("Write error")

        layer = hid_utils.read_layer_data(mock_hid_device)

        assert layer is None


class TestCloseDevice:
    """Test suite for close_device function."""

    def test_close_device_success(self, mock_hid_device: Mock) -> None:
        """
        Test successfully closing a HID device.

        Verifies that the device close method is called.
        """
        hid_utils.close_device(mock_hid_device)

        mock_hid_device.close.assert_called_once()

    def test_close_device_none(self) -> None:
        """
        Test closing a None device.

        Verifies that closing None doesn't raise an exception.
        """
        # Should not raise an exception
        hid_utils.close_device(None)

    def test_close_device_exception(self, mock_hid_device: Mock) -> None:
        """
        Test closing a device that raises an exception.

        Verifies that exceptions during close are handled gracefully.
        """
        mock_hid_device.close.side_effect = Exception("Close error")

        # Should not raise an exception
        hid_utils.close_device(mock_hid_device)


class TestGetPlatformInfo:
    """Test suite for get_platform_info function."""

    @patch("src.utils.hid_utils.sys.platform", "win32")
    def test_get_platform_info_windows(self) -> None:
        """
        Test getting platform info for Windows.

        Verifies that Windows platform information is returned
        correctly.
        """
        info = hid_utils.get_platform_info()

        assert info["platform"] == "windows"
        assert info["requires_elevation"] is False
        assert "Windows" in info["notes"]

    @patch("src.utils.hid_utils.sys.platform", "linux")
    def test_get_platform_info_linux(self) -> None:
        """
        Test getting platform info for Linux.

        Verifies that Linux platform information is returned
        correctly.
        """
        info = hid_utils.get_platform_info()

        assert info["platform"] == "linux"
        assert info["requires_elevation"] is True
        assert "udev" in info["notes"].lower()

    @patch("src.utils.hid_utils.sys.platform", "darwin")
    def test_get_platform_info_macos(self) -> None:
        """
        Test getting platform info for macOS.

        Verifies that macOS platform information is returned
        correctly.
        """
        info = hid_utils.get_platform_info()

        assert info["platform"] == "darwin"
        assert info["requires_elevation"] is False
        assert "macOS" in info["notes"]

    @patch("src.utils.hid_utils.sys.platform", "unknown")
    def test_get_platform_info_unknown(self) -> None:
        """
        Test getting platform info for unknown platform.

        Verifies that unknown platform information is returned
        with appropriate notes.
        """
        info = hid_utils.get_platform_info()

        assert info["platform"] == "unknown"
        assert info["requires_elevation"] is False
        assert "Unknown" in info["notes"]

    @patch("src.utils.hid_utils.sys.platform", "cygwin")
    def test_get_platform_info_cygwin(self) -> None:
        """
        Test getting platform info for Cygwin.

        Verifies that Cygwin is treated as Windows.
        """
        info = hid_utils.get_platform_info()

        assert info["platform"] == "windows"
        assert info["requires_elevation"] is False


class TestVialConstants:
    """Test suite for Vial-related constants."""

    def test_vial_vendor_ids(self) -> None:
        """
        Test Vial vendor IDs constant.

        Verifies that the VIAL_VENDOR_IDS constant contains
        the expected vendor IDs.
        """
        assert 0x5342 in hid_utils.VIAL_VENDOR_IDS
        assert 0x3496 in hid_utils.VIAL_VENDOR_IDS
        assert 0x3297 in hid_utils.VIAL_VENDOR_IDS

    def test_vial_usage_page(self) -> None:
        """
        Test Vial usage page constant.

        Verifies that the VIAL_USAGE_PAGE constant has the
        expected value.
        """
        assert hid_utils.VIAL_USAGE_PAGE == 0xFF60

    def test_vial_usage(self) -> None:
        """
        Test Vial usage constant.

        Verifies that the VIAL_USAGE constant has the
        expected value.
        """
        assert hid_utils.VIAL_USAGE == 0x61
