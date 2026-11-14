#!/usr/bin/env python3
"""sysimages: GFOS's gadget images (sysiclass) as pen grids, read, checked and drawn.

  sysimages.py check [SET...]            the rules: every image there, the set's box size, known pens
  sysimages.py specimen OUT.png          Dale's sheet: today's drawn-in-code glyphs beside each set's grids,
                                         on the blue glass title bar and on the window, at 1x and 4x

The grid format (src/images/README.md): 'image NAME', 'size W H', then H rows of W pens:
  '.'  clear, the gadget's own background shows (the title bar's bands, the window's grey)
  '#'  the glyph pen (BARDETAILPEN on the title bar, TEXTPEN in a menu or on the window)
  'o'  the back pen, a filled face over what is behind (the depth gadget's front window)
The sets (DISPLAY-PROFILES section 2.3): lores, hires 1:2 (pixels twice as tall as wide, so every shape is
drawn twice as wide in pixels), medres (square pixels: laced and RTG) and large. The set gives the drawing, the
profile gives the size. MIT, AmiCradle Team.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMAGES_DIR = os.path.join(ROOT, "src", "images")

# the images every set has, in sysiclass order, and the menu's sub-item mark
IMAGES = ["close", "depth", "zoom", "iconify", "size", "up", "down", "left", "right",
          "check", "mx", "amigakey", "submenu"]
# each set's glyph box, W x H in pixels, and how tall one pixel is (hires 1:2: twice as tall as wide)
SETS = {"lores": (7, 7, 1), "hires12": (14, 7, 2), "medres": (11, 11, 1), "large": (15, 15, 1)}
SET_LABELS = {"lores": "lores (profile 1)", "hires12": "hires 1:2 (profile 2)",
              "medres": "medres (profiles 3, 4, 5)", "large": "large (profile 6)"}
PENS = set(".#o")


def read(path):
    """(name, w, h, rows)"""
    name = w = h = None
    rows = []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if not line or line.startswith("# "):
            continue
        word = line.split()
        if word[0] == "image" and len(word) == 2:
            name = word[1]
        elif word[0] == "size" and len(word) == 3:
            w, h = int(word[1]), int(word[2])
        elif set(line) <= PENS | {"#"}:
            rows.append(line)
        else:
            raise ValueError(f"{path}:{n}: can't read {line!r}")
    if name is None or w is None:
        raise ValueError(f"{path}: needs 'image NAME' and 'size W H'")
    return name, w, h, rows


def write(name, rows, out):
    out.write(f"image {name}\nsize {len(rows[0])} {len(rows)}\n")
    for r in rows:
        out.write(r + "\n")


def load_set(set_name, base=IMAGES_DIR):
    d = os.path.join(base, set_name)
    got = {}
    for f in sorted(os.listdir(d)):
        if f.endswith(".txt"):
            name, w, h, rows = read(os.path.join(d, f))
            got[name] = (w, h, rows, f)
    return got


def check_set(set_name, base=IMAGES_DIR):
    """the problems, as lines (none: the set is good)"""
    bw, bh, _ = SETS[set_name]
    errs = []
    try:
        got = load_set(set_name, base)
    except (OSError, ValueError) as e:
        return [str(e)]
    for name in IMAGES:
        if name not in got:
            errs.append(f"{set_name}: no {name}")
    for name, (w, h, rows, f) in got.items():
        where = f"{set_name}/{f}"
        if name not in IMAGES:
            errs.append(f"{where}: {name} isn't a gadget image")
        if f != name + ".txt":
            errs.append(f"{where}: the file should be {name}.txt")
        if (w, h) != (bw, bh):
            errs.append(f"{where}: {w}x{h}, the set's box is {bw}x{bh}")
        if len(rows) != h:
            errs.append(f"{where}: {len(rows)} rows, size says {h}")
        for i, r in enumerate(rows):
            if len(r) != w:
                errs.append(f"{where}: row {i} is {len(r)} wide, size says {w}")
            if set(r) - PENS:
                errs.append(f"{where}: row {i} has pens {''.join(sorted(set(r) - PENS))}")
        if not any("#" in r for r in rows):
            errs.append(f"{where}: no glyph pen at all")
    return errs


# ---- today's glyphs: oi_look_glyph (amicradle-guest libraries/openintuition/look_core.c), pen for pen ----

class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [["."] * w for _ in range(h)]

    def dot(self, pen, x, y, n=1):
        for i in range(n):
            if 0 <= x + i < self.w and 0 <= y < self.h:
                self.px[y][x + i] = pen

    def hline(self, pen, xa, xb, y):
        for x in range(xa, xb + 1):
            self.dot(pen, x, y)

    def vline(self, pen, x, ya, yb):
        for y in range(ya, yb + 1):
            self.dot(pen, x, y)

    def fill(self, pen, x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            self.hline(pen, x0, x1, y)

    def outline(self, pen, x0, y0, x1, y1):
        self.hline(pen, x0, x1, y0)
        self.hline(pen, x0, x1, y1)
        self.vline(pen, x0, y0, y1)
        self.vline(pen, x1, y0, y1)

    def rows(self):
        return ["".join(r) for r in self.px]


def cdiv(a, b):
    """C's division, toward zero"""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def today(name, w, h):
    """today's glyph in a w x h box, as pen rows"""
    c = Canvas(w, h)
    x0, y0 = 0, 0
    m = min(w, h)
    g = m - m // 3
    if g < 3:
        g = m
    cx, cy = x0 + w // 2, y0 + h // 2
    gx, gy = x0 + (w - g) // 2, y0 + (h - g) // 2
    P, B = "#", "o"

    def arrow(t, d):
        for i in range(t):
            dd = i if d in (0, 2) else t - 1 - i
            at = (cy if d < 2 else cx) - t // 2 + i
            if d < 2:
                c.hline(P, cx - dd, cx + dd, at)
            else:
                c.vline(P, at, cy - dd, cy + dd)

    if name == "close":
        g = g * 2 // 3 + 1
        gx, gy = x0 + (w - g) // 2, y0 + (h - g) // 2
        for i in range(g):
            c.dot(P, gx + i, gy + i, 2 if i < g - 1 else 1)
            c.dot(P, gx + g - 1 - i - (1 if i < g - 1 else 0), gy + i, 2 if i < g - 1 else 1)
    elif name == "zoom":
        zh = g - g // 5
        gy = y0 + (h - zh) // 2
        c.outline(P, gx, gy, gx + g - 1, gy + zh - 1)
        c.outline(P, gx + 1, gy + 1, gx + g - 2, gy + zh - 2)
        c.hline(P, gx + 2, gx + g - 3, gy + 2)
    elif name == "depth":
        s = g - g // 3
        c.outline(P, gx, gy, gx + s - 1, gy + s - 1)
        c.fill(B, gx + g - s, gy + g - s, gx + g - 1, gy + g - 1)
        c.outline(P, gx + g - s, gy + g - s, gx + g - 1, gy + g - 1)
        c.outline(P, gx + g - s + 1, gy + g - s + 1, gx + g - 2, gy + g - 2)
    elif name == "iconify":
        t = 3 if g >= 9 else 2
        c.fill(P, gx, gy + g - t, gx + g - 1, gy + g - 1)
    elif name == "size":
        for i in range(3):
            k = g * (i + 1) // 3
            for j in range(k):
                c.dot(P, gx + g - k + j, gy + g - 1 - j)
    elif name in ("up", "down", "left", "right"):
        arrow(g // 2 + 1, ["up", "down", "left", "right"].index(name))
    elif name == "check":
        x, y, low = gx, gy - g // 6, g // 3
        for i in range(g):
            row = y + g // 2 + i if i < low else y + g // 2 + low - cdiv((i - low) * (g // 2 + low), g - low)
            c.dot(P, x + i, row)
            c.dot(P, x + i, row - 1)
    elif name == "mx":
        g = (g + 1) // 2 + 1
        gy = y0 + (h - g) // 2
        for i in range((g + 1) // 2):
            d = min(i + (g + 3) // 4, g // 2)
            c.hline(P, cx - d, cx + d - 1 + (g & 1), gy + i)
            c.hline(P, cx - d, cx + d - 1 + (g & 1), gy + g - 1 - i)
    elif name == "amigakey":
        c.outline(P, gx, gy, gx + g - 1, gy + g - 1)
        if g >= 7:
            ih, top = g - 4, gy + 2
            den = 2 * (ih - 1 if ih > 1 else 1)
            for i in range(ih):
                d = i * (g - 6) // den
                c.dot(P, cx - d - 1, top + i)
                c.dot(P, cx + d - (0 if g & 1 else 1), top + i)
            bar = top + ih * 2 // 3
            d = (bar - top) * (g - 6) // den
            c.hline(P, cx - d - 1, cx + d - (0 if g & 1 else 1), bar)
    # submenu: today the menu draws its sub-item mark as text ("»" in the menu's font), no glyph
    return c.rows()


# ---- the specimen sheet ----

BAR_TOP, BAR_BOTTOM = (74, 132, 214), (28, 72, 150)    # the blue glass title bar's bands
BAR_GLYPH = (255, 255, 255)
WINDOW = (170, 170, 170)
WINDOW_GLYPH = (0, 0, 0)
BACK_ON_BAR, BACK_ON_WINDOW = (52, 104, 186), (255, 255, 255)


def paint(px, rows, x, y, zx, zy, glyph, back):
    for r, row in enumerate(rows):
        for col, p in enumerate(row):
            if p == ".":
                continue
            ink = glyph if p == "#" else back
            for dy in range(zy):
                for dx in range(zx):
                    px[x + col * zx + dx, y + r * zy + dy] = ink


def text(px, font, s, x, y, ink):
    sys.path.insert(0, HERE)
    import gridfont
    img = gridfont.draw(font, s)
    for r, row in enumerate(img):
        for col, on in enumerate(row):
            if on:
                px[x + col, y + r] = ink
    return len(img)


def specimen(out, base=IMAGES_DIR):
    from PIL import Image
    sys.path.insert(0, HERE)
    import gridfont
    font = gridfont.read(os.path.join(ROOT, "src", "gfos-sans-13.txt"))[0]
    M, PAD, GAP, Z = 16, 6, 8, 4
    sets = [s for s in SETS if os.path.isdir(os.path.join(base, s))]
    loaded = {s: load_set(s, base) for s in sets}
    # each set: a label, then 4 strips (today 1x, drawn 1x, today 4x, drawn 4x), each once on the bar, once on the window
    cell = lambda s, z: (SETS[s][0] * z + PAD * 2, SETS[s][1] * SETS[s][2] * z + PAD * 2)
    width = M * 2 + 90 + max(len(IMAGES) * (cell(s, Z)[0] + GAP) for s in sets)
    height = M * 2
    for s in sets:
        height += 20 + 2 * (2 * (cell(s, 1)[1] + GAP) + 2 * (cell(s, Z)[1] + GAP)) + GAP * 2
    im = Image.new("RGB", (width, height), (255, 255, 255))
    px = im.load()
    y = M
    for s in sets:
        bw, bh, tall = SETS[s]
        text(px, font, SET_LABELS[s] + f": {bw} x {bh} pixels" + (", each pixel twice as tall" if tall == 2 else ""),
             M, y, (0, 85, 170))
        y += 20
        for z in (1, Z):
            cw, ch = cell(s, z)
            for kind in ("today", "drawn"):
                for where in ("bar", "window"):
                    text(px, font, f"{kind} {z}x" if where == "bar" else "", M, y + ch // 2 - 6, (40, 40, 40))
                    x = M + 90
                    for name in IMAGES:
                        if where == "bar":
                            for yy in range(ch):
                                f = yy / max(ch - 1, 1)
                                col = tuple(int(a + (b - a) * f) for a, b in zip(BAR_TOP, BAR_BOTTOM))
                                for xx in range(cw):
                                    px[x + xx, y + yy] = col
                            glyph, back = BAR_GLYPH, BACK_ON_BAR
                        else:
                            for yy in range(ch):
                                for xx in range(cw):
                                    px[x + xx, y + yy] = WINDOW
                            glyph, back = WINDOW_GLYPH, BACK_ON_WINDOW
                        rows = today(name, bw, bh) if kind == "today" else loaded[s][name][2]
                        paint(px, rows, x + PAD, y + PAD, z, z * tall, glyph, back)
                        x += cw + GAP
                    y += ch + GAP
        y += GAP * 2
    im.save(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "check":
        bad = [e for s in (a[1:] or list(SETS)) for e in check_set(s)]
        for e in bad:
            print(e)
        sys.exit(1 if bad else 0)
    elif a and a[0] == "specimen" and len(a) == 2:
        specimen(a[1])
    else:
        sys.exit(__doc__)
