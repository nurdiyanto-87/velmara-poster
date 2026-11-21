#!/usr/bin/env python3
"""VELMARA - Isles of the Drifting Light.

A travel poster for a place that does not exist, drawn entirely in
code with the Python standard library (no third-party packages, no
network, no external fonts or files).

Writes /output/entry.png (1024x1024 PNG) — or $MAKEFUN_OUTPUT_DIR.
Run: python3 main.py
"""
import math
import os
import struct
import zlib
from pathlib import Path

W, H = 1024, 1024

# --- palette ---
CREAM = (255, 246, 224)
GOLD = (255, 205, 120)
GOLD_DARK = (214, 148, 64)
NAVY = (24, 28, 72)
NAVY_DEEP = (16, 20, 54)
INK = (20, 26, 52)
SUN = (255, 214, 130)
SUN_GLOW = (250, 178, 98)
ROCK = (58, 38, 80)
ROCK_DARK = (40, 26, 60)
ROCK_RIM = (255, 170, 100)
GRASS = (52, 128, 102)
SEA_TOP = (34, 116, 136)
SEA_BOT = (10, 52, 88)
FOAM = (190, 228, 238)
BEAM = (255, 232, 158)
WHITE = (255, 255, 255)
RED = (198, 62, 48)

rows = [bytearray(W * 3) for _ in range(H)]


def set_px(x, y, rgb):
    if 0 <= x < W and 0 <= y < H:
        row = rows[y]
        row[x * 3:x * 3 + 3] = bytes(rgb)


def fill_rect(x, y, w, h, rgb):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    band = bytes(rgb) * (x1 - x0)
    for yy in range(y0, y1):
        rows[yy][x0 * 3:x1 * 3] = band


def fill_disc(cx, cy, r, rgb):
    for yy in range(cy - r, cy + r + 1):
        dx = int(math.sqrt(max(0, r * r - (yy - cy) * (yy - cy))))
        fill_rect(cx - dx, yy, 2 * dx + 1, 1, rgb)


def disc_ring(cx, cy, r, thick, rgb):
    lo, hi = (r - thick) * (r - thick), (r + thick) * (r + thick)
    for yy in range(cy - r - thick, cy + r + thick + 1):
        for xx in range(cx - r - thick, cx + r + thick + 1):
            d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
            if lo <= d2 <= hi:
                set_px(xx, yy, rgb)


def draw_line(x0, y0, x1, y1, rgb, w=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    step_x = 1 if x0 < x1 else -1
    step_y = 1 if y0 < y1 else -1
    err = dx - dy
    half = w // 2
    while True:
        for a in range(-half, half + 1):
            for b in range(-half, half + 1):
                set_px(x0 + a, y0 + b, rgb)
        if x0 == x1 and y0 == y1:
            return
        twice = 2 * err
        if twice > -dy:
            err -= dy
            x0 += step_x
        if twice < dx:
            err += dx
            y0 += step_y


def fill_poly(pts, rgb):
    top, bottom = min(p[1] for p in pts), max(p[1] for p in pts)
    count = len(pts)
    for y in range(top, bottom + 1):
        hits = []
        for i in range(count):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % count]
            if (ay <= y < by) or (by <= y < ay):
                hits.append(ax + (y - ay) * (bx - ax) / (by - ay))
        hits.sort()
        for i in range(0, len(hits) - 1, 2):
            for x in range(int(hits[i]), int(hits[i + 1]) + 1):
                set_px(x, y, rgb)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(y0, y1, c_top, c_bot):
    """Vertical gradient band, one fill_rect per row."""
    span = max(1, y1 - y0)
    for y in range(y0, y1):
        fill_rect(0, y, W, 1, lerp(c_top, c_bot, (y - y0) / span))


# --- 5x7 bitmap font ---
FONT_DATA = """
A 01110 10001 10001 11111 10001 10001 10001
B 11110 10001 10001 11110 10001 10001 11110
C 01110 10001 10000 10000 10000 10001 01110
D 11100 10010 10001 10001 10001 10010 11100
E 11111 10000 10000 11110 10000 10000 11111
F 11111 10000 10000 11110 10000 10000 10000
G 01110 10001 10000 10111 10001 10001 01111
H 10001 10001 10001 11111 10001 10001 10001
I 01110 00100 00100 00100 00100 00100 01110
J 00111 00010 00010 00010 00010 10010 01100
K 10001 10010 10100 11000 10100 10010 10001
L 10000 10000 10000 10000 10000 10000 11111
M 10001 11011 10101 10101 10001 10001 10001
N 10001 11001 10101 10011 10001 10001 10001
O 01110 10001 10001 10001 10001 10001 01110
P 11110 10001 10001 11110 10000 10000 10000
Q 01110 10001 10001 10001 10101 10010 01101
R 11110 10001 10001 11110 10100 10010 10001
S 01111 10000 10000 01110 00001 00001 11110
T 11111 00100 00100 00100 00100 00100 00100
U 10001 10001 10001 10001 10001 10001 01110
V 10001 10001 10001 10001 10001 01010 00100
W 10001 10001 10001 10101 10101 11011 10001
X 10001 10001 01010 00100 01010 10001 10001
Y 10001 10001 01010 00100 00100 00100 00100
Z 11111 00001 00010 00100 01000 10000 11111
0 01110 10001 10011 10101 11001 10001 01110
1 00100 01100 00100 00100 00100 00100 01110
2 01110 10001 00001 00110 01000 10000 11111
3 11111 00010 00100 00010 00001 10001 01110
4 00010 00110 01010 10010 11111 00010 00010
5 11111 10000 11110 00001 00001 10001 01110
6 00110 01000 10000 11110 10001 10001 01110
7 11111 00001 00010 00100 01000 01000 01000
8 01110 10001 10001 01110 10001 10001 01110
9 01110 10001 10001 01111 00001 00010 01100
. 00000 00000 00000 00000 00000 01100 01100
? 01110 10001 00001 00010 00100 00000 00100
- 00000 00000 00000 01110 00000 00000 00000
"""

GLYPHS = {}
for _line in FONT_DATA.strip().splitlines():
    _parts = _line.split()
    GLYPHS[_parts[0]] = [int(_row, 2) for _row in _parts[1:]]


def glyph_w(s, scale):
    return len(s) * 6 * scale - scale


def blit_text(x, y, s, scale, rgb):
    cursor = x
    for ch in s.upper():
        if ch == " ":
            cursor += 6 * scale
            continue
        bits = GLYPHS.get(ch, GLYPHS["?"])
        for row in range(7):
            value = bits[row]
            for col in range(5):
                if value & (1 << (4 - col)):
                    fill_rect(cursor + col * scale, y + row * scale,
                              scale, scale, rgb)
        cursor += 6 * scale


def centred_text(cx, y, s, scale, rgb):
    blit_text(cx - glyph_w(s, scale) // 2, y, s, scale, rgb)


# --- scene pieces ---
def cloud(cx, cy, w, rgb):
    """Soft horizontal cloud from overlapping discs."""
    for dx, r in ((-w // 2, 16), (-w // 4, 24), (0, 30), (w // 4, 24),
                  (w // 2, 16)):
        fill_disc(cx + dx, cy, r, rgb)
    fill_rect(cx - w // 2, cy - 8, w, 16, rgb)


def bird(x, y, s, rgb):
    draw_line(x - s, y, x, y - s // 2, rgb, 2)
    draw_line(x, y - s // 2, x + s, y, rgb, 2)


def pine(x, y, h, rgb):
    fill_poly([(x, y - h), (x - h // 3, y), (x + h // 3, y)], rgb)
    fill_poly([(x, y - h * 3 // 4), (x - h // 4, y - h // 4),
               (x + h // 4, y - h // 4)], rgb)
    fill_rect(x - 2, y, 5, 8, rgb)


def floating_island(cx, top, half_w, depth, scale=1):
    """Rocky island floating above the sea, grassy top, pointed base."""
    # grassy plateau
    fill_poly([(cx - half_w, top), (cx + half_w, top),
               (cx + half_w - 14, top + 14), (cx - half_w + 14, top + 14)],
              GRASS)
    # rock underside: inverted cone to a point
    fill_poly([(cx - half_w + 14, top + 14), (cx + half_w - 14, top + 14),
               (cx + 26, top + depth), (cx, top + depth + 26),
               (cx - 26, top + depth)], ROCK)
    # warm rim light on the right flank
    fill_poly([(cx + half_w - 30, top + 14), (cx + half_w - 14, top + 14),
               (cx + 26, top + depth), (cx + 12, top + depth)],
              ROCK_RIM)
    # dark shading on the left flank
    fill_poly([(cx - half_w + 14, top + 14), (cx - half_w + 34, top + 14),
               (cx - 12, top + depth)], ROCK_DARK)


def lighthouse(x, base_y, h):
    """Cream tower with a red cap and a light beam to the right."""
    w = 26
    fill_rect(x, base_y - h, w, h, CREAM)
    fill_rect(x, base_y - h, w, 8, RED)
    fill_disc(x + w // 2, base_y - h - 4, 12, RED)
    fill_rect(x - 4, base_y - h - 16, w + 8, 10, (40, 40, 70))
    fill_disc(x + w // 2, base_y - h - 16, 6, SUN)
    # beam: two widening triangles to the right
    fill_poly([(x + w, base_y - h - 14), (x + w + 210, base_y - h - 52),
               (x + w + 210, base_y - h - 30), (x + w, base_y - h - 6)],
              BEAM)
    # beam edge sparkle
    fill_disc(x + w + 150, base_y - h - 40, 4, WHITE)


def waterfall(x, y0, y1):
    fill_rect(x, y0, 8, y1 - y0, FOAM)
    fill_rect(x + 12, y0 + 8, 5, y1 - y0 - 8, FOAM)
    fill_disc(x + 4, y1, 8, FOAM)
    fill_rect(x - 8, y1 + 2, 32, 3, FOAM)


def sailboat(x, y, s):
    # hull
    fill_poly([(x - 34 * s // 10, y), (x + 34 * s // 10, y),
               (x + 22 * s // 10, y + 12 * s // 10),
               (x - 22 * s // 10, y + 12 * s // 10)], NAVY_DEEP)
    # mast + sail
    draw_line(x, y, x, y - 46 * s // 10, INK, 3)
    fill_poly([(x + 3, y - 44 * s // 10), (x + 3, y - 4),
               (x + 30 * s // 10, y - 4)], CREAM)
    fill_poly([(x - 3, y - 40 * s // 10), (x - 3, y - 4),
               (x - 22 * s // 10, y - 4)], GOLD)
    # reflection
    fill_rect(x - 26, y + 16, 52, 3, (120, 170, 190))


def build():
    # frame
    fill_rect(0, 0, W, H, NAVY_DEEP)
    fill_rect(14, 14, W - 28, H - 28, NAVY)
    # sky: deep indigo -> violet -> warm gold at the horizon
    vgrad(18, 300, (26, 30, 76), (96, 56, 116))
    vgrad(300, 520, (96, 56, 116), (196, 96, 108))
    vgrad(520, 640, (196, 96, 108), (252, 190, 118))
    horizon = 640

    # sun + glow, low over the sea
    fill_disc(712, 500, 150, (238, 148, 92))
    fill_disc(712, 500, 112, SUN_GLOW)
    fill_disc(712, 500, 78, SUN)

    # clouds
    cloud(240, 250, 260, (214, 158, 178))
    cloud(870, 150, 200, (226, 170, 186))
    cloud(760, 285, 170, (240, 182, 150))
    cloud(150, 420, 200, (232, 168, 140))

    # birds
    for bx, by, bs in [(300, 300, 12), (360, 270, 9), (620, 250, 10),
                       (830, 330, 12), (880, 300, 8), (250, 360, 9)]:
        bird(bx, by, bs, INK)

    # --- main floating island with lighthouse (the landmark) ---
    floating_island(430, 452, 150, 96)
    lighthouse(468, 452, 96)
    pine(360, 452, 34, (30, 70, 58))
    pine(398, 452, 26, (30, 70, 58))
    pine(560, 452, 30, (30, 70, 58))
    waterfall(306, 466, horizon)
    # small islet, right, with pines
    floating_island(820, 540, 78, 52)
    pine(800, 540, 24, (30, 70, 58))
    pine(832, 540, 18, (30, 70, 58))
    # tiny islet, far left
    floating_island(150, 580, 52, 36)

    # sea
    vgrad(horizon, 1006, SEA_TOP, SEA_BOT)
    # sun reflection: broken golden streaks under the sun
    for i, (yy, half) in enumerate([(660, 46), (690, 58), (722, 40),
                                    (756, 66), (792, 48), (830, 60),
                                    (870, 42), (912, 54), (954, 40)]):
        fill_rect(712 - half, yy, 2 * half, 5, (255, 196, 116))
    # wave dashes
    for yy in range(680, 990, 46):
        for xx in range(40, 980, 90):
            fill_rect(xx + (yy % 90), yy, 34, 3, (90, 150, 175))
    # sailboat on the sea — the promise of a stay
    sailboat(600, 800, 10)

    # dark headland silhouettes framing the bottom corners
    fill_poly([(18, 1006), (18, 900), (120, 962), (260, 1006)], NAVY_DEEP)
    pine(80, 952, 44, NAVY_DEEP)
    pine(130, 968, 34, NAVY_DEEP)
    fill_poly([(1006, 1006), (1006, 920), (920, 968), (820, 1006)],
              NAVY_DEEP)
    pine(940, 962, 36, NAVY_DEEP)

    # --- type: the place name, big and legible, with a gold rule ---
    # soft shadow, then cream letters
    centred_text(512 + 5, 72 + 5, "VELMARA", 13, (18, 14, 48))
    centred_text(512, 72, "VELMARA", 13, CREAM)
    fill_rect(512 - 190, 178, 380, 4, GOLD)
    centred_text(512, 196, "ISLES OF THE DRIFTING LIGHT", 3, GOLD)
    fill_rect(512 - 190, 226, 380, 2, GOLD_DARK)

    # inner gold frame line
    fill_rect(22, 22, W - 44, 2, GOLD_DARK)
    fill_rect(22, H - 24, W - 44, 2, GOLD_DARK)
    fill_rect(22, 22, 2, H - 44, GOLD_DARK)
    fill_rect(W - 24, 22, 2, H - 44, GOLD_DARK)


def write_png(path):
    build()
    raw = bytearray()
    for row in rows:
        raw.append(0)
        raw.extend(row)
    payload = zlib.compress(bytes(raw), 9)

    def add_chunk(kind, data):
        piece = struct.pack(">I", len(data)) + kind + data
        return piece + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += add_chunk(b"IHDR",
                      struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += add_chunk(b"IDAT", payload)
    png += add_chunk(b"IEND", b"")
    path.write_bytes(png)
    print(f"wrote {path} {len(png)} bytes")


def main():
    target = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    target.mkdir(parents=True, exist_ok=True)
    write_png(target / "entry.png")


if __name__ == "__main__":
    main()
