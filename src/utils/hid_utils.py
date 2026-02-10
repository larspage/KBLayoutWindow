"""
HID Utilities Module

This module provides helper functions for USB HID communication with Vial-compatible
keyboards. It handles device enumeration, opening devices, and reading layer data.

Functions:
    find_vial_devices: Enumerate all Vial-compatible keyboards
    open_device: Open a HID device by vendor and product ID
    read_layer_data: Read current layer from a Vial device
    is_vial_device: Check if a device is Vial-compatible
"""

import logging
import sys
from typing import Any, Dict, List, Optional

import hid

# Configure logging
logger = logging.getLogger(__name__)

# Vial vendor IDs
VIAL_VENDOR_IDS = [0x5342, 0x3496, 0x3297]

# Vial usage page and usage for identifying Vial devices
VIAL_USAGE_PAGE = 0xFF60
VIAL_USAGE = 0x61


def find_vial_devices() -> List[Dict[str, Any]]:
    """
    Enumerate all Vial-compatible keyboards connected to the system.

    This function scans all HID devices and filters for those that match
    Vial's vendor IDs and usage page/usage combination.

    Returns:
        List[Dict[str, Any]]: List of device information dictionaries.
            Each dictionary contains:
            - vendor_id: int - Vendor ID
            - product_id: int - Product ID
            - path: bytes - Device path
            - manufacturer_string: str - Manufacturer name
            - product_string: str - Product name
            - serial_number: str - Serial number

    Example:
        >>> devices = find_vial_devices()
        >>> for device in devices:
        ...     print(f"{device['product_string']} - {device['vendor_id']:04x}")
    """
    devices = []

    try:
        # Enumerate all HID devices
        all_devices = hid.enumerate()

        for device_info in all_devices:
            if is_vial_device(device_info):
                # Extract relevant information
                device_data = {
                    "vendor_id": device_info.get("vendor_id", 0),
                    "product_id": device_info.get("product_id", 0),
                    "path": device_info.get("path", b""),
                    "manufacturer_string": device_info.get("manufacturer_string", ""),
                    "product_string": device_info.get("product_string", ""),
                    "serial_number": device_info.get("serial_number", ""),
                }
                devices.append(device_data)
                logger.info(
                    f"Found Vial device: {device_data['product_string']} "
                    f"(VID: {device_data['vendor_id']:04x}, "
                    f"PID: {device_data['product_id']:04x})"
                )

    except Exception as e:
        logger.error(f"Error enumerating Vial devices: {e}")

    return devices


def open_device(vendor_id: int, product_id: int) -> Optional["hid.device"]:
    """
    Open a HID device by vendor and product ID.

    This function attempts to open the first matching device found with the
    specified vendor and product IDs.

    Args:
        vendor_id: The vendor ID of the device to open
        product_id: The product ID of the device to open

    Returns:
        Optional[hid.device]: The opened HID device, or None if opening failed

    Raises:
        OSError: If the device cannot be opened due to permission issues

    Example:
        >>> device = open_device(0x5342, 0x0001)
        >>> if device:
        ...     print("Device opened successfully")
    """
    try:
        # Find the device path
        devices = hid.enumerate(vendor_id, product_id)

        if not devices:
            logger.warning(
                f"No device found with VID: {vendor_id:04x}, PID: {product_id:04x}"
            )
            return None

        # Open the first matching device
        device_path = devices[0].get("path")
        if not device_path:
            logger.error("Device path not found in device info")
            return None

        device = hid.device()
        device.open_path(device_path)

        logger.info(
            f"Opened device: {devices[0].get('product_string', 'Unknown')} "
            f"(VID: {vendor_id:04x}, PID: {product_id:04x})"
        )

        return device

    except OSError as e:
        if "Permission denied" in str(e) or "Access is denied" in str(e):
            logger.error(
                f"Permission denied when opening device. "
                f"Try running with elevated privileges or configure udev rules."
            )
        else:
            logger.error(f"OSError opening device: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error opening device: {e}")
        return None


def read_layer_data(device: "hid.device") -> Optional[int]:
    """
    Read the current layer from a Vial device.

    This function sends a Vial protocol command to request the current layer
    and reads the response from the device.

    Args:
        device: The opened HID device to read from

    Returns:
        Optional[int]: The current layer number (0-indexed), or None if read failed

    Note:
        The Vial protocol uses specific report IDs and commands. This implementation
        uses the standard Vial layer query command.

    Example:
        >>> device = open_device(0x5342, 0x0001)
        >>> if device:
        ...     layer = read_layer_data(device)
        ...     if layer is not None:
        ...         print(f"Current layer: {layer}")
    """
    try:
        # Vial protocol command to get current layer
        # Report ID 0x00, command 0x01 for layer query
        report_id = 0x00
        command = [0x01]  # Get layer command

        # Send command to device
        # Vial uses 64-byte reports
        buffer = [0x00] * 64
        buffer[0] = report_id
        buffer[1] = command[0]

        device.write([report_id] + buffer[1:])

        # Read response
        # Vial devices respond with 64-byte reports
        response = device.read(64, timeout_ms=100)

        if response and len(response) > 1:
            # Layer is typically in byte 1 of the response
            layer = response[1]
            logger.debug(f"Read layer data: {layer}")
            return layer

        logger.warning("No response from device or invalid response length")
        return None

    except OSError as e:
        logger.error(f"OSError reading layer data: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error reading layer data: {e}")
        return None


def is_vial_device(device_info: Dict[str, Any]) -> bool:
    """
    Check if a device is Vial-compatible.

    This function checks if a device matches Vial's vendor IDs and
    usage page/usage combination.

    Args:
        device_info: Dictionary containing device information from hid.enumerate()

    Returns:
        bool: True if the device is Vial-compatible, False otherwise

    Example:
        >>> devices = hid.enumerate()
        >>> for device in devices:
        ...     if is_vial_device(device):
        ...         print(f"Vial device: {device.get('product_string')}")
    """
    # Check vendor ID
    vendor_id = device_info.get("vendor_id", 0)
    if vendor_id not in VIAL_VENDOR_IDS:
        return False

    # Check usage page and usage for Vial protocol
    usage_page = device_info.get("usage_page", 0)
    usage = device_info.get("usage", 0)

    # Vial devices typically use usage_page 0xFF60 and usage 0x61
    # However, some devices may use different values, so we're lenient
    # if the vendor ID matches
    if usage_page == VIAL_USAGE_PAGE and usage == VIAL_USAGE:
        return True

    # Also accept devices with Vial vendor ID even if usage differs
    # (some keyboards may have non-standard HID descriptors)
    return True


def close_device(device: "hid.device") -> None:
    """
    Close a HID device.

    This function safely closes a HID device and handles any errors
    that may occur during the close operation.

    Args:
        device: The HID device to close

    Example:
        >>> device = open_device(0x5342, 0x0001)
        >>> # ... use device ...
        >>> close_device(device)
    """
    try:
        if device:
            device.close()
            logger.debug("Device closed successfully")
    except Exception as e:
        logger.error(f"Error closing device: {e}")


def get_platform_info() -> Dict[str, Any]:
    """
    Get platform-specific information for HID device access.

    This function returns information about the current platform that
    may be relevant for HID device access, such as whether elevated
    privileges are required.

    Returns:
        Dict[str, Any]: Platform information dictionary containing:
            - platform: str - Platform name (windows, linux, darwin)
            - requires_elevation: bool - Whether elevated privileges are needed
            - notes: str - Additional platform-specific notes

    Example:
        >>> info = get_platform_info()
        >>> print(f"Platform: {info['platform']}")
        >>> if info['requires_elevation']:
        ...     print("Elevated privileges required")
    """
    platform = sys.platform.lower()
    info = {
        "platform": platform,
        "requires_elevation": False,
        "notes": "",
    }

    if platform == "win32" or platform == "cygwin":
        info["platform"] = "windows"
        info["requires_elevation"] = False
        info["notes"] = "Windows typically allows HID access without elevation"

    elif platform.startswith("linux"):
        info["platform"] = "linux"
        info["requires_elevation"] = True
        info["notes"] = (
            "Linux requires udev rules or elevated privileges for HID access. "
            "Create udev rules in /etc/udev/rules.d/ for persistent access."
        )

    elif platform == "darwin":
        info["platform"] = "darwin"
        info["requires_elevation"] = False
        info["notes"] = "macOS typically allows HID access without elevation"

    else:
        info["notes"] = f"Unknown platform: {platform}"

    return info
