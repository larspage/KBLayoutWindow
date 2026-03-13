"""
Vial Protocol Utilities

Implements the VIA/Vial HID protocol for reading keyboard layout definitions
and keymaps from Vial-compatible keyboards.

Functions:
    get_keyboard_info: Read rows, cols, and layer count from device
    get_keyboard_layout_json: Read keyboard layout definition (key positions)
    get_keymap: Read all keycodes for a given layer
    get_all_keymaps: Read keycodes for all layers
"""

import json
import logging
import lzma
import zlib
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# VIA protocol command IDs
VIA_GET_PROTOCOL_VERSION = 0x01
VIA_GET_KEYBOARD_VALUE   = 0x02
VIA_GET_KEYCODE          = 0x04

# VIA keyboard value IDs
VIA_LAYOUT_OPTIONS       = 0x02

# Vial-specific commands share interface 1 with VIA but use a 0xFE prefix byte.
# Packet format: [0xFE, <vial_cmd>, ...]
VIAL_CMD_PREFIX          = 0xFE
VIAL_GET_KEYBOARD_ID     = 0x00
VIAL_GET_SIZE            = 0x01
VIAL_GET_DEF_CHUNK       = 0x02

# Vial dynamic entry operations (tap dance, combos, key overrides)
# Request:  [0xFE, VIAL_DYNAMIC_ENTRY_OP, op, entry_type, ...]
# Response: data written from byte 0 (no command echo)
VIAL_DYNAMIC_ENTRY_OP    = 0x0C
VIAL_DYN_OP_GET_COUNT    = 0x00  # resp[0]=td_count, resp[1]=combo_count, resp[2]=ko_count
VIAL_DYN_OP_GET          = 0x01  # read one entry by index
VIAL_ENTRY_TAP_DANCE     = 0x00  # entry type: tap dance

# Packet size used by the Vial HID interface
PACKET_SIZE = 32


def _send_recv(device: Any, data: List[int]) -> Optional[List[int]]:
    """
    Send a 32-byte packet and return the 32-byte response.

    Args:
        device: Open hid.device instance
        data: Command bytes (padded to PACKET_SIZE automatically)

    Returns:
        Response bytes as a list, or None on failure
    """
    buf = [0x00] * PACKET_SIZE
    for i, b in enumerate(data[:PACKET_SIZE]):
        buf[i] = b
    try:
        device.write(bytes([0x00] + buf))   # report-id prefix required by hidapi
        response = device.read(PACKET_SIZE, timeout=500)
        if response and len(response) >= PACKET_SIZE:
            return list(response[:PACKET_SIZE])
        if response:
            return list(response)
        return None
    except Exception as e:
        logger.error(f"HID send/recv error: {e}")
        return None


def get_keyboard_info(device: Any) -> Dict[str, Any]:
    """
    Read basic keyboard info from the device.

    Queries VIA cmd 0x11 (id_dynamic_keymap_get_layer_count) for the layer count.
    Rows/cols are overridden once the layout JSON is parsed.

    Falls back to safe defaults when the device does not respond.
    Returns a dict with keys: layers (int), rows (int), cols (int).
    """
    layers = 8  # safe default
    resp = _send_recv(device, [0x11])  # id_dynamic_keymap_get_layer_count
    if resp and resp[0] == 0x11 and len(resp) > 1:
        n = resp[1]
        if 1 <= n <= 32:
            layers = n
            logger.debug(f"Layer count from firmware: {layers}")
    return {"layers": layers, "rows": 6, "cols": 14}


def get_keyboard_layout_json(device: Any) -> Optional[Dict[str, Any]]:
    """
    Retrieve the keyboard layout definition JSON from the device firmware.

    Vial stores a compressed (zlib) JSON blob describing the keyboard layout
    (physical key positions, matrix map, etc.). It is fetched in 28-byte chunks.

    Returns:
        Parsed dict from the keyboard JSON, or None if retrieval fails.
    """
    # Step 1: get total size of the compressed blob.
    # Vial commands are prefixed with VIAL_CMD_PREFIX (0xFE) on the VIA interface.
    # Response for GET_SIZE has NO command echo — bytes 0-3 are the size (LE uint32).
    resp = _send_recv(device, [VIAL_CMD_PREFIX, VIAL_GET_SIZE])
    if not resp:
        logger.warning("No response to VIAL_GET_SIZE")
        return None

    size = int.from_bytes(bytes(resp[0:4]), "little")
    if size == 0 or size > 65536:
        logger.warning(f"Unexpected keyboard definition size: {size}")
        return None

    logger.debug(f"Keyboard definition compressed size: {size} bytes")

    # Step 2: fetch chunks.
    # The third byte of GET_DEF_CHUNK is a block number (0-based), not a byte
    # offset.  Each block is 32 bytes.  Response has no command echo — all 32
    # bytes are data.
    BLOCK_SIZE = 32
    n_blocks = (size + BLOCK_SIZE - 1) // BLOCK_SIZE
    compressed = bytearray()

    for block in range(n_blocks):
        chunk_req = [VIAL_CMD_PREFIX, VIAL_GET_DEF_CHUNK, block & 0xFF, 0x00, 0x00]
        resp = _send_recv(device, chunk_req)
        if not resp:
            logger.error(f"No response fetching block {block}")
            return None
        compressed += bytes(resp[:BLOCK_SIZE])

    # Trim to exact reported size
    compressed = compressed[:size]

    # Step 3: decompress (XZ format) and parse
    try:
        raw_json = lzma.decompress(bytes(compressed))
        layout_data = json.loads(raw_json.decode("utf-8"))
        logger.debug("Keyboard layout JSON parsed successfully")
        return layout_data
    except lzma.LZMAError:
        # Fall back to zlib in case firmware uses zlib compression
        try:
            raw_json = zlib.decompress(bytes(compressed))
            layout_data = json.loads(raw_json.decode("utf-8"))
            logger.debug("Keyboard layout JSON parsed (zlib fallback)")
            return layout_data
        except Exception as e2:
            logger.error(f"Failed to decompress keyboard layout JSON: {e2}")
            logger.error(f"First 16 compressed bytes: {bytes(compressed[:16]).hex()}")
            return None
    except Exception as e:
        logger.error(f"Failed to parse keyboard layout JSON: {e}")
        return None


def get_keycode(device: Any, layer: int, row: int, col: int) -> int:
    """
    Read a single keycode from the device.

    Args:
        device: Open hid.device
        layer: Layer index (0-based)
        row: Matrix row
        col: Matrix column

    Returns:
        16-bit keycode, or 0 on failure
    """
    resp = _send_recv(device, [VIA_GET_KEYCODE, layer, row, col])
    if resp and len(resp) >= 6:
        return (resp[4] << 8) | resp[5]
    return 0


def get_keymap(
    device: Any,
    layer: int,
    rows: int,
    cols: int,
) -> List[List[int]]:
    """
    Read all keycodes for one layer.

    Returns:
        2-D list [row][col] of 16-bit keycodes.
    """
    keymap: List[List[int]] = []
    for row in range(rows):
        row_codes: List[int] = []
        for col in range(cols):
            code = get_keycode(device, layer, row, col)
            row_codes.append(code)
        keymap.append(row_codes)
    return keymap


def get_all_keymaps(
    device: Any,
    layers: int,
    rows: int,
    cols: int,
) -> List[List[List[int]]]:
    """
    Read keycodes for all layers.

    Returns:
        3-D list [layer][row][col] of 16-bit keycodes.
    """
    all_maps: List[List[List[int]]] = []
    for layer in range(layers):
        logger.debug(f"Reading keymap for layer {layer}")
        km = get_keymap(device, layer, rows, cols)
        all_maps.append(km)
    return all_maps


def get_layer_count_from_json(layout_data: Dict[str, Any]) -> Optional[int]:
    """
    Extract the layer count from a keyboard definition JSON.

    Returns the layer count, or None if not found.
    """
    count = layout_data.get("dynamic_keymap", {}).get("layer_count")
    if isinstance(count, int) and 1 <= count <= 32:
        return count
    return None


def get_tap_dance_count(device: Any) -> int:
    """
    Return the number of tap dance entries stored in firmware.

    Sends VIAL_DYNAMIC_ENTRY_OP / GET_COUNT.  The response byte 0 is the
    tap dance count (combo count is byte 1, key-override count byte 2).
    Returns 0 if the device doesn't support tap dance or doesn't respond.
    """
    resp = _send_recv(device, [
        VIAL_CMD_PREFIX, VIAL_DYNAMIC_ENTRY_OP,
        VIAL_DYN_OP_GET_COUNT, VIAL_ENTRY_TAP_DANCE,
    ])
    if not resp or len(resp) < 5:
        return 0
    # VIAL_DYNAMIC_ENTRY_OP echoes the 4-byte command header in the response.
    # Actual data starts at byte 4: [td_count, combo_count, ko_count, ...]
    count = resp[4]
    if 0 < count <= 128:
        return count
    return 0


def get_tap_dance_entry(device: Any, idx: int) -> Optional[Dict[str, int]]:
    """
    Read one tap dance entry from firmware by index.

    Vial tap dance struct (10 bytes, all uint16 LE):
        on_tap, on_hold, on_double_tap, on_tap_hold, custom_tapping_term

    custom_tapping_term == 0 means "use the firmware default (usually 200 ms)".

    Returns a dict with those five keys, or None on failure.
    """
    resp = _send_recv(device, [
        VIAL_CMD_PREFIX, VIAL_DYNAMIC_ENTRY_OP,
        VIAL_DYN_OP_GET, VIAL_ENTRY_TAP_DANCE,
        idx & 0xFF, (idx >> 8) & 0xFF,
    ])
    # VIAL_DYNAMIC_ENTRY_OP echoes the 4-byte command header; data follows.
    if not resp or len(resp) < 14:
        return None

    def u16(i: int) -> int:
        return resp[i] | (resp[i + 1] << 8)

    base = 4  # skip echoed [0xFE, 0x0C, op, type]
    return {
        "on_tap":              u16(base + 0),
        "on_hold":             u16(base + 2),
        "on_double_tap":       u16(base + 4),
        "on_tap_hold":         u16(base + 6),
        "custom_tapping_term": u16(base + 8),
    }


def extract_layout_keys(layout_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract the list of key definitions from a Vial/QMK keyboard JSON.

    Handles two formats:

    1. Standard QMK/Vial JSON:
       {"layouts": {"LAYOUT": {"layout": [{"matrix": [r,c], "x":…, "y":…}, …]}}}

    2. KLE list format (used by some Vial firmware builds):
       {"layouts": {"keymap": [[{x/y modifiers}, "row,col", …], …]}}
       Each outer list element is a KLE row. Dict items adjust position;
       string items are "row,col" matrix coordinates.

    Each returned key dict contains: x, y, w, h, row, col.
    """
    keys: List[Dict[str, Any]] = []

    layouts = layout_data.get("layouts", {})
    if not layouts:
        return keys

    layout_name = next(iter(layouts))
    layout_def = layouts[layout_name]

    if isinstance(layout_def, dict):
        # Standard QMK/Vial JSON format
        for key in layout_def.get("layout", []):
            keys.append({
                "x":   float(key.get("x", 0)),
                "y":   float(key.get("y", 0)),
                "w":   float(key.get("w", 1.0)),
                "h":   float(key.get("h", 1.0)),
                "row": int(key.get("matrix", [0, 0])[0]),
                "col": int(key.get("matrix", [0, 0])[1]),
            })

    elif isinstance(layout_def, list):
        # KLE list format: list of rows
        # Each row: dicts = position modifiers, strings = "row,col" keys
        current_y = 0.0
        first_row = True

        for row in layout_def:
            if not first_row:
                current_y += 1.0  # advance one row unit between KLE rows
            first_row = False

            current_x = 0.0
            pend_x = 0.0
            pend_y = 0.0
            pend_w = 1.0
            pend_h = 1.0

            for item in row:
                if isinstance(item, dict):
                    pend_x += item.get("x", 0.0)
                    pend_y += item.get("y", 0.0)
                    if "w" in item:
                        pend_w = float(item["w"])
                    if "h" in item:
                        pend_h = float(item["h"])
                elif isinstance(item, str) and "," in item:
                    # Apply accumulated modifiers
                    current_x += pend_x
                    current_y += pend_y
                    w, h = pend_w, pend_h

                    r, c = item.split(",", 1)
                    keys.append({
                        "x": current_x, "y": current_y,
                        "w": w, "h": h,
                        "row": int(r), "col": int(c),
                    })

                    current_x += w
                    # x and y modifiers are consumed per key; w/h reset to default
                    pend_x = 0.0
                    pend_y = 0.0
                    pend_w = 1.0
                    pend_h = 1.0

    return keys
