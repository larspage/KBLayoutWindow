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

# Known Vial vendor IDs (non-exhaustive; serial_number check is more reliable)
VIAL_VENDOR_IDS = [0x5342, 0x3496, 0x3297, 0xFEED, 0x6582]

# Vial usage page and usage (Linux hidapi often reports 0 for these)
VIAL_USAGE_PAGE = 0xFF60
VIAL_USAGE = 0x61

# Vial serial number prefix — the most reliable cross-platform identifier
VIAL_SERIAL_PREFIX = "vial:"

# The Vial RAW HID interface is always interface 1 on multi-interface keyboards
VIAL_INTERFACE = 1

# QMK HID console interface identifiers
CONSOLE_USAGE_PAGE = 0xFF31
CONSOLE_USAGE = 0x0074
CONSOLE_INTERFACE = 3  # fallback for Linux where hidapi may report usage=0


def find_vial_devices() -> List[Dict[str, Any]]:
    """
    Enumerate all Vial-compatible keyboards connected to the system.

    Detection strategy (in priority order):
    1. serial_number starts with "vial:" — definitive Vial marker
    2. usage_page == 0xFF60 and usage == 0x61 — Vial RAW HID descriptor
    3. vendor_id in VIAL_VENDOR_IDS — known Vial VIDs

    On Linux, hidapi often reports usage_page=0 so strategy 1 is the
    most reliable. We also de-duplicate by VID/PID and prefer
    interface_number == 1 (the Vial RAW HID interface).

    Returns:
        List of device dicts, one entry per physical keyboard.
    """
    devices = []
    seen: set = set()   # (vendor_id, product_id) already added

    try:
        all_devices = hid.enumerate()

        # First pass: group by (VID, PID) to find keyboards with multiple interfaces
        by_vidpid: Dict[tuple, List[Dict]] = {}
        for d in all_devices:
            if is_vial_device(d):
                key = (d.get("vendor_id", 0), d.get("product_id", 0))
                by_vidpid.setdefault(key, []).append(d)

        for (vid, pid), ifaces in by_vidpid.items():
            if (vid, pid) in seen:
                continue
            seen.add((vid, pid))

            # Interface 1 = VIA RAW HID (keycode reads)
            # Interface 2 = Vial RAW HID (layout JSON)
            iface = next(
                (i for i in ifaces if i.get("interface_number") == VIAL_INTERFACE),
                ifaces[0],
            )
            iface2 = next(
                (i for i in ifaces if i.get("interface_number") == 2),
                None,
            )

            device_data = {
                "vendor_id":           vid,
                "product_id":          pid,
                "path":                iface.get("path", b""),
                "vial_path":           iface2.get("path", b"") if iface2 else b"",
                "manufacturer_string": iface.get("manufacturer_string", ""),
                "product_string":      iface.get("product_string", ""),
                "serial_number":       iface.get("serial_number", ""),
                "interface_number":    iface.get("interface_number", 0),
            }
            devices.append(device_data)
            logger.info(
                f"Found Vial device: {device_data['product_string']} "
                f"(VID:{vid:04x} PID:{pid:04x} "
                f"iface:{device_data['interface_number']})"
            )

    except Exception as e:
        logger.error(f"Error enumerating Vial devices: {e}")

    return devices


def open_device(vendor_id: int, product_id: int) -> Optional["hid.Device"]:
    """
    Open the Vial RAW HID interface of a keyboard by VID/PID.

    Prefers interface_number == VIAL_INTERFACE (1); falls back to the
    first enumerated path if interface 1 is not found.

    Args:
        vendor_id: Vendor ID
        product_id: Product ID

    Returns:
        Opened hid.Device, or None on failure.
    """
    try:
        all_ifaces = hid.enumerate(vendor_id, product_id)

        if not all_ifaces:
            logger.warning(f"No device found VID:{vendor_id:04x} PID:{product_id:04x}")
            return None

        # Prefer the Vial RAW HID interface
        target = next(
            (d for d in all_ifaces if d.get("interface_number") == VIAL_INTERFACE),
            all_ifaces[0],
        )

        device_path = target.get("path")
        if not device_path:
            logger.error("Device path not found")
            return None

        device = hid.Device(path=device_path)

        logger.info(
            f"Opened {target.get('product_string','?')} "
            f"VID:{vendor_id:04x} PID:{product_id:04x} "
            f"iface:{target.get('interface_number',0)}"
        )
        return device

    except OSError as e:
        if "Permission denied" in str(e) or "Access is denied" in str(e):
            logger.error(
                "Permission denied opening HID device. "
                "Ensure /etc/udev/rules.d/59-vial.rules is in place and "
                "you have unplugged/replugged the keyboard."
            )
        else:
            logger.error(f"OSError opening device: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error opening device: {e}")
        return None


def open_device_by_path(path: bytes) -> Optional["hid.Device"]:
    """
    Open a HID device by its raw path.

    Args:
        path: Device path bytes as returned by hid.enumerate()

    Returns:
        Opened hid.Device, or None on failure.
    """
    if not path:
        return None
    try:
        device = hid.Device(path=path)
        logger.info(f"Opened device by path: {path}")
        return device
    except Exception as e:
        logger.error(f"Error opening device by path {path}: {e}")
        return None


def read_matrix_state(device: "hid.Device") -> Optional[set]:
    """
    Read the current switch-matrix state via VIA id_get_keyboard_value (0x02/0x03).

    Returns a set of (row, col) tuples for every key that is currently pressed,
    or None on failure.  The caller is responsible for mapping positions to
    keycodes and inferring the active layer.
    """
    try:
        buf = [0x00] * 32
        buf[0] = 0x02   # id_get_keyboard_value
        buf[1] = 0x03   # id_keyboard_value_switch_matrix_state
        device.write(bytes([0x00] + buf))
        response = device.read(32, timeout=100)

        if not response or len(response) < 3 or response[0] != 0x02:
            return None

        # Bitmask starts at byte 2; bit (row*cols + col) → key [row][col].
        # We don't know rows/cols here, so return the raw bitmask bytes and
        # let the caller decode them.  We return a frozenset of set bit indices.
        pressed_bits: set = set()
        for byte_idx, byte_val in enumerate(response[2:]):
            for bit in range(8):
                if byte_val & (1 << bit):
                    pressed_bits.add(byte_idx * 8 + bit)

        return pressed_bits

    except OSError as e:
        logger.error(f"OSError reading matrix state: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading matrix state: {e}")
        return None


def is_vial_device(device_info: Dict[str, Any]) -> bool:
    """
    Check if a HID device is Vial-compatible.

    Detection order:
    1. serial_number starts with "vial:" — definitive marker set by Vial firmware
    2. usage_page == 0xFF60 and usage == 0x61 — Vial RAW HID descriptor
    3. vendor_id in VIAL_VENDOR_IDS — known Vial vendor IDs

    On Linux, hidapi often reports usage_page=0, so check 1 is most reliable.
    """
    # 1. Serial number prefix — most reliable on all platforms
    serial = device_info.get("serial_number", "") or ""
    if serial.lower().startswith(VIAL_SERIAL_PREFIX):
        return True

    # 2. Usage page / usage — works on Windows/macOS; often 0 on Linux
    if (device_info.get("usage_page", 0) == VIAL_USAGE_PAGE
            and device_info.get("usage", 0) == VIAL_USAGE):
        return True

    # 3. Known Vial vendor IDs
    if device_info.get("vendor_id", 0) in VIAL_VENDOR_IDS:
        return True

    return False


def find_console_interface(all_ifaces: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find the QMK HID console interface in a list of enumerated interfaces.

    Tries usage_page/usage match first; falls back to interface_number because
    Linux hidapi often reports usage=0 for non-keyboard interfaces.
    """
    for d in all_ifaces:
        if d.get("usage_page") == CONSOLE_USAGE_PAGE and d.get("usage") == CONSOLE_USAGE:
            return d
    for d in all_ifaces:
        if d.get("interface_number") == CONSOLE_INTERFACE:
            return d
    return None


def open_console_device(path: bytes) -> Optional["hid.Device"]:
    """Open the QMK HID console interface by path."""
    try:
        device = hid.Device(path=path)
        logger.info(f"Opened console interface: {path}")
        return device
    except Exception as e:
        logger.error(f"Error opening console device {path}: {e}")
        return None


def read_console_layer(device: "hid.Device") -> Optional[int]:
    """
    Non-blocking read from the QMK HID console interface.

    The firmware sends xprintf("%d", layer) on every layer change, which
    produces a single ASCII digit character. Returns the layer as an int,
    or None if no data is available or the byte is not a digit.
    """
    try:
        data = device.read(32, timeout=0)
        if not data:
            return None
        non_zero = [b for b in data if b != 0]
        if not non_zero:
            return None
        last_byte = non_zero[-1]
        if 0x30 <= last_byte <= 0x39:  # ASCII '0'-'9'
            return last_byte - 0x30
        return None
    except Exception as e:
        logger.error(f"Error reading console layer: {e}")
        return None


def close_device(device: "hid.Device") -> None:
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
