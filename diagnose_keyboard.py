#!/usr/bin/env python3
"""
Diagnostic script for silakka54 / Vial keyboard.
Run from the project directory: .venv/bin/python diagnose_keyboard.py
"""
import sys, zlib, json, struct
sys.path.insert(0, '.')

import hid

# --- find keyboard ---
all_devs = hid.enumerate()
targets = [d for d in all_devs if (d.get('serial_number','').startswith('vial:'))]
if not targets:
    print("ERROR: No Vial keyboard found (serial_number doesn't start with 'vial:')")
    sys.exit(1)

# Prefer interface 1 (Vial RAW HID)
iface1 = next((d for d in targets if d.get('interface_number') == 1), targets[0])
print(f"Device: {iface1['product_string']}  path={iface1['path']}  iface={iface1['interface_number']}")

dev = hid.device()
try:
    dev.open_path(iface1['path'])
except Exception as e:
    print(f"ERROR opening device: {e}")
    sys.exit(1)

def send_recv(cmd_bytes, read_size=32):
    buf = [0x00] * 32
    for i, b in enumerate(cmd_bytes[:32]):
        buf[i] = b
    dev.write([0x00] + buf)
    return dev.read(read_size, timeout_ms=1000)

# ── 1. GET_KEYBOARD_ID (0x00) ──────────────────────────────────────
print("\n── VIAL_GET_KEYBOARD_ID (cmd=0x00) ──")
r = send_recv([0x00])
print("  raw:", bytes(r).hex() if r else "NO RESPONSE")
if r:
    magic = bytes(r[0:4])
    print("  bytes[0:4]:", magic.hex(), "  expected: 564c4900 ('VIL\\0') or similar")

# ── 2. GET_SIZE (0x01) ─────────────────────────────────────────────
print("\n── VIAL_GET_SIZE (cmd=0x01) ──")
r = send_recv([0x01])
print("  raw:", bytes(r[:8]).hex() if r else "NO RESPONSE")
if r:
    size_a = struct.unpack_from('<I', bytes(r[0:4]))[0]
    size_b = struct.unpack_from('<I', bytes(r[1:5]))[0]
    print(f"  size from bytes[0:4] = {size_a}")
    print(f"  size from bytes[1:5] = {size_b}  (old code read this)")

# ── 3. GET_DEF_CHUNK (0x02) ────────────────────────────────────────
print("\n── VIAL_GET_DEF_CHUNK (cmd=0x02, offset=0) ──")
r = send_recv([0x02, 0x00, 0x00, 0x00])
print("  raw:", bytes(r[:16]).hex() if r else "NO RESPONSE")
if r:
    print("  bytes[0:4]:", bytes(r[0:4]).hex())
    print("  bytes[4:8]:", bytes(r[4:8]).hex())

# ── 4. Try reading the full JSON using bytes[0:4] as size ──────────
print("\n── Attempt full JSON load ──")
r = send_recv([0x01])
if r:
    size = struct.unpack_from('<I', bytes(r[0:4]))[0]
    print(f"  Trying size={size}")
    if 0 < size <= 65536:
        CHUNK = 28
        compressed = bytearray()
        offset = 0
        ok = True
        while offset < size:
            cr = send_recv([0x02, offset & 0xFF, (offset>>8) & 0xFF, (offset>>16) & 0xFF])
            if not cr:
                print(f"  ERROR: no response at offset {offset}")
                ok = False
                break
            remaining = size - offset
            compressed += bytes(cr[0:min(CHUNK, remaining)])
            offset += CHUNK
        if ok:
            try:
                raw = zlib.decompress(bytes(compressed))
                kbdef = json.loads(raw)
                print("  SUCCESS! JSON loaded, top-level keys:", list(kbdef.keys()))
                layouts = kbdef.get('layouts', {})
                print("  Layouts:", list(layouts.keys()))
                for name, layout in layouts.items():
                    keys = layout.get('layout', [])
                    print(f"  '{name}': {len(keys)} keys")
                    if keys:
                        rows = max(k.get('matrix',[0,0])[0] for k in keys if 'matrix' in k)
                        cols = max(k.get('matrix',[0,0])[1] for k in keys if 'matrix' in k)
                        print(f"    max row={rows}, max col={cols}")
                lc = kbdef.get('dynamic_keymap',{}).get('layer_count')
                print(f"  layer_count: {lc}")
                # Save it
                with open('/tmp/silakka54_kbdef.json', 'w') as f:
                    json.dump(kbdef, f, indent=2)
                print("  Saved to /tmp/silakka54_kbdef.json")
            except Exception as e:
                print(f"  decompress/parse failed: {e}")
                print(f"  first 16 compressed bytes: {bytes(compressed[:16]).hex()}")
    else:
        print(f"  size {size} is out of range, trying with bytes[1:5]...")
        size2 = struct.unpack_from('<I', bytes(r[1:5]))[0]
        print(f"  bytes[1:5] size = {size2}")

# ── 5. Sample keycode reads (left half + right half candidates) ───
print("\n── Keycode samples ──")
print("  Left half (row 0-5, col 0-5):")
for row in range(6):
    for col in range(6):
        kr = send_recv([0x04, 0, row, col])
        if kr and len(kr) >= 6:
            kc = (kr[4] << 8) | kr[5]
            if kc:
                print(f"    layer=0 row={row} col={col} → 0x{kc:04x}")

print("  Right half candidates (row 0-5, col 6-13):")
for row in range(6):
    for col in range(6, 14):
        kr = send_recv([0x04, 0, row, col])
        if kr and len(kr) >= 6:
            kc = (kr[4] << 8) | kr[5]
            if kc:
                print(f"    layer=0 row={row} col={col} → 0x{kc:04x}")

print("\n  Right half candidates (row 6-11, col 0-8):")
for row in range(6, 12):
    for col in range(9):
        kr = send_recv([0x04, 0, row, col])
        if kr and len(kr) >= 6:
            kc = (kr[4] << 8) | kr[5]
            if kc:
                print(f"    layer=0 row={row} col={col} → 0x{kc:04x}")

dev.close()
print("\nDone.")
