"""
Keycode Label Mapper

Converts raw 16-bit QMK keycodes to human-readable display strings
and tooltip descriptions.

Public API:
    keycode_to_label(code)       – short label shown on the key cap
    keycode_to_description(code) – longer tooltip string
"""

from typing import Tuple

# ---------------------------------------------------------------------------
# QMK keycode ranges
# ---------------------------------------------------------------------------
QK_BASIC_MAX        = 0x00FF
QK_MODS             = 0x0100   # modded keys start here
QK_MODS_MAX         = 0x1FFF
QK_FUNCTION         = 0x2000
QK_MACRO            = 0x6000
QK_LAYER_TAP        = 0x4000
QK_LAYER_TAP_MAX    = 0x4FFF
QK_TO               = 0x5000
QK_TO_MAX           = 0x50FF
QK_MOMENTARY        = 0x5100
QK_MOMENTARY_MAX    = 0x51FF
QK_DEF_LAYER        = 0x5200
QK_DEF_LAYER_MAX    = 0x52FF
QK_TOGGLE_LAYER     = 0x5300
QK_TOGGLE_LAYER_MAX = 0x53FF
QK_ONE_SHOT_LAYER   = 0x5400
QK_ONE_SHOT_LAYER_MAX = 0x54FF
QK_ONE_SHOT_MOD     = 0x5500
QK_TAP_DANCE        = 0x5700
QK_TAP_DANCE_MAX    = 0x57FF

# ---------------------------------------------------------------------------
# Basic HID keycodes → (label, description)
# ---------------------------------------------------------------------------
_BASIC: dict[int, Tuple[str, str]] = {
    0x0000: ("", "No key / Transparent"),
    0x0001: ("Roll", "Roll over (error)"),
    0x0004: ("A", "A"),
    0x0005: ("B", "B"),
    0x0006: ("C", "C"),
    0x0007: ("D", "D"),
    0x0008: ("E", "E"),
    0x0009: ("F", "F"),
    0x000A: ("G", "G"),
    0x000B: ("H", "H"),
    0x000C: ("I", "I"),
    0x000D: ("J", "J"),
    0x000E: ("K", "K"),
    0x000F: ("L", "L"),
    0x0010: ("M", "M"),
    0x0011: ("N", "N"),
    0x0012: ("O", "O"),
    0x0013: ("P", "P"),
    0x0014: ("Q", "Q"),
    0x0015: ("R", "R"),
    0x0016: ("S", "S"),
    0x0017: ("T", "T"),
    0x0018: ("U", "U"),
    0x0019: ("V", "V"),
    0x001A: ("W", "W"),
    0x001B: ("X", "X"),
    0x001C: ("Y", "Y"),
    0x001D: ("Z", "Z"),
    0x001E: ("1", "1 / !"),
    0x001F: ("2", "2 / @"),
    0x0020: ("3", "3 / #"),
    0x0021: ("4", "4 / $"),
    0x0022: ("5", "5 / %"),
    0x0023: ("6", "6 / ^"),
    0x0024: ("7", "7 / &"),
    0x0025: ("8", "8 / *"),
    0x0026: ("9", "9 / ("),
    0x0027: ("0", "0 / )"),
    0x0028: ("Enter", "Enter / Return"),
    0x0029: ("Esc", "Escape"),
    0x002A: ("Bksp", "Backspace"),
    0x002B: ("Tab", "Tab"),
    0x002C: ("Space", "Space"),
    0x002D: ("-", "- / _"),
    0x002E: ("=", "= / +"),
    0x002F: ("[", "[ / {"),
    0x0030: ("]", "] / }"),
    0x0031: ("\\", "\\ / |"),
    0x0033: (";", "; / :"),
    0x0034: ("'", "' / \""),
    0x0035: ("`", "` / ~"),
    0x0036: (",", ", / <"),
    0x0037: (".", ". / >"),
    0x0038: ("/", "/ / ?"),
    0x0039: ("Caps", "Caps Lock"),
    0x003A: ("F1", "F1"),
    0x003B: ("F2", "F2"),
    0x003C: ("F3", "F3"),
    0x003D: ("F4", "F4"),
    0x003E: ("F5", "F5"),
    0x003F: ("F6", "F6"),
    0x0040: ("F7", "F7"),
    0x0041: ("F8", "F8"),
    0x0042: ("F9", "F9"),
    0x0043: ("F10", "F10"),
    0x0044: ("F11", "F11"),
    0x0045: ("F12", "F12"),
    0x0046: ("PrtSc", "Print Screen"),
    0x0047: ("ScrLk", "Scroll Lock"),
    0x0048: ("Pause", "Pause / Break"),
    0x0049: ("Ins", "Insert"),
    0x004A: ("Home", "Home"),
    0x004B: ("PgUp", "Page Up"),
    0x004C: ("Del", "Delete"),
    0x004D: ("End", "End"),
    0x004E: ("PgDn", "Page Down"),
    0x004F: ("→", "Right Arrow"),
    0x0050: ("←", "Left Arrow"),
    0x0051: ("↓", "Down Arrow"),
    0x0052: ("↑", "Up Arrow"),
    0x0053: ("NumLk", "Num Lock"),
    0x0054: ("/ (N)", "Numpad /"),
    0x0055: ("* (N)", "Numpad *"),
    0x0056: ("- (N)", "Numpad -"),
    0x0057: ("+ (N)", "Numpad +"),
    0x0058: ("Ent(N)", "Numpad Enter"),
    0x0059: ("1 (N)", "Numpad 1"),
    0x005A: ("2 (N)", "Numpad 2"),
    0x005B: ("3 (N)", "Numpad 3"),
    0x005C: ("4 (N)", "Numpad 4"),
    0x005D: ("5 (N)", "Numpad 5"),
    0x005E: ("6 (N)", "Numpad 6"),
    0x005F: ("7 (N)", "Numpad 7"),
    0x0060: ("8 (N)", "Numpad 8"),
    0x0061: ("9 (N)", "Numpad 9"),
    0x0062: ("0 (N)", "Numpad 0"),
    0x0063: (". (N)", "Numpad ."),
    0x0064: ("\\", "\\ / |"),
    0x0065: ("App", "Application / Menu"),
    0x0066: ("Power", "Power"),
    0x00E0: ("LCtrl", "Left Control"),
    0x00E1: ("LShift", "Left Shift"),
    0x00E2: ("LAlt", "Left Alt"),
    0x00E3: ("LGui", "Left GUI / Win / Cmd"),
    0x00E4: ("RCtrl", "Right Control"),
    0x00E5: ("RShift", "Right Shift"),
    0x00E6: ("RAlt", "Right Alt / AltGr"),
    0x00E7: ("RGui", "Right GUI / Win / Cmd"),
}

# ---------------------------------------------------------------------------
# QMK transparent / no-op
# ---------------------------------------------------------------------------
KC_TRANSPARENT = 0x0001  # also commonly 0xFFFF in some builds
KC_NO          = 0x0000


def _mod_label(mod_bits: int) -> str:
    """Convert a 5-bit QMK mod mask to a short string like 'S(', 'C(', etc."""
    mods = []
    if mod_bits & 0x01: mods.append("C")
    if mod_bits & 0x02: mods.append("S")
    if mod_bits & 0x04: mods.append("A")
    if mod_bits & 0x08: mods.append("G")
    return "+".join(mods)


def keycode_to_label(code: int) -> str:
    """
    Return a short display label for a keycode (shown on the key cap).

    Args:
        code: 16-bit QMK keycode

    Returns:
        Short string, e.g. "A", "MO(1)", "TD(2)", "LCtrl"
    """
    label, _ = _decode(code)
    return label


def keycode_to_description(code: int) -> str:
    """
    Return a longer tooltip description for a keycode.

    Args:
        code: 16-bit QMK keycode

    Returns:
        Description string, e.g. "Momentary layer 1", "Tap Dance 2"
    """
    _, desc = _decode(code)
    return desc


def _decode(code: int) -> Tuple[str, str]:
    """Internal: return (label, description) for any keycode."""

    if code == 0x0000:
        return ("▽", "KC_NO / Transparent")

    if code == 0xFFFF:
        return ("▽", "KC_TRANSPARENT")

    # --- basic keycodes ---
    if code in _BASIC:
        label, desc = _BASIC[code]
        return (label or "▽", f"KC_{desc}" if desc else "KC_NO")

    # --- modded keys  QK_MODS 0x0100-0x1FFF ---
    if 0x0100 <= code <= 0x1FFF:
        base = code & 0x00FF
        mods = (code >> 8) & 0x1F
        base_label = _BASIC.get(base, (hex(base), hex(base)))[0]
        mod_str = _mod_label(mods)
        label = f"{mod_str}({base_label})" if mod_str else base_label
        return (label, f"Modified key: {mod_str}+{base_label}")

    # --- Momentary layer MO(n) ---
    if 0x5100 <= code <= 0x51FF:
        n = code & 0xFF
        return (f"MO({n})", f"Momentary layer {n}")

    # --- To layer TO(n) ---
    if 0x5000 <= code <= 0x50FF:
        n = code & 0xFF
        return (f"TO({n})", f"Switch to layer {n}")

    # --- Toggle layer TG(n) ---
    if 0x5300 <= code <= 0x53FF:
        n = code & 0xFF
        return (f"TG({n})", f"Toggle layer {n}")

    # --- Default layer DF(n) ---
    if 0x5200 <= code <= 0x52FF:
        n = code & 0xFF
        return (f"DF({n})", f"Set default layer {n}")

    # --- One-shot layer OSL(n) ---
    if 0x5400 <= code <= 0x54FF:
        n = code & 0xFF
        return (f"OSL({n})", f"One-shot layer {n}")

    # --- One-shot mod OSM ---
    if 0x5500 <= code <= 0x55FF:
        mods = code & 0xFF
        mod_str = _mod_label(mods)
        return (f"OSM({mod_str})", f"One-shot mod {mod_str}")

    # --- Tap Dance TD(n) ---
    if 0x5700 <= code <= 0x57FF:
        n = code & 0xFF
        return (f"TD({n})", f"Tap Dance {n}")

    # --- Layer-tap LT(layer, key) ---
    if 0x4000 <= code <= 0x4FFF:
        layer = (code >> 8) & 0x0F
        key   = code & 0xFF
        key_label = _BASIC.get(key, (hex(key), hex(key)))[0]
        return (f"LT({layer},{key_label})", f"Layer-tap: hold=layer {layer}, tap={key_label}")

    # --- Unknown ---
    return (f"0x{code:04X}", f"Unknown keycode 0x{code:04X}")
