#!/usr/bin/env python3
"""tools/sysimages.py and src/images: the sets are complete and keep their rules. MIT, AmiCradle Team."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import sysimages as si

fails = 0


def ok(cond, what):
    global fails
    if not cond:
        fails += 1
        print("FAIL:", what)


def rows(set_name, name):
    return si.load_set(set_name)[name][2]


def transpose(r):
    return ["".join(r[y][x] for y in range(len(r))) for x in range(len(r[0]))]


# every set passes check and has exactly the 13 images
for s in si.SETS:
    errs = si.check_set(s)
    ok(not errs, f"{s}: {errs}")
    ok(sorted(si.load_set(s)) == sorted(si.IMAGES), f"{s}: the images are {sorted(si.load_set(s))}")

# hires 1:2 is drawn for tall pixels: twice as wide as high, and today it is the lores drawing, every column twice
for name in si.IMAGES:
    lo, hi = rows("lores", name), rows("hires12", name)
    ok(hi == ["".join(c * 2 for c in r) for r in lo], f"hires12/{name} isn't lores/{name} doubled")

for s in ("lores", "medres", "large"):
    up = rows(s, "up")
    ok(rows(s, "down") == up[::-1], f"{s}: down isn't up upside down")
    ok(rows(s, "left") == transpose(up), f"{s}: left isn't up turned")
    ok(rows(s, "right") == [r[::-1] for r in transpose(up)], f"{s}: right isn't left mirrored")
    for name in ("close", "mx", "up"):                  # symmetric left to right
        r = rows(s, name)
        ok(r == [x[::-1] for x in r], f"{s}/{name} isn't symmetric")
    for name in ("close", "mx"):                        # and top to bottom
        r = rows(s, name)
        ok(r == r[::-1], f"{s}/{name} isn't symmetric top to bottom")
    # the depth gadget's front window: back pen inside, glyph pen around it, nothing clear inside it
    d = rows(s, "depth")
    ys = [y for y, r in enumerate(d) if "o" in r]
    xs = [x for r in d for x, c in enumerate(r) if c == "o"]
    ok(ys and all(d[y][x] == "o" for y in range(ys[0], ys[-1] + 1) for x in range(min(xs), max(xs) + 1)),
       f"{s}/depth: the front window's face has holes")
    ok(d[ys[-1] + 1][min(xs):max(xs) + 1] == "#" * (max(xs) - min(xs) + 1), f"{s}/depth: the front window has no bottom")

# the reader refuses what it can't read, and check catches a wrong size, a missing image and an unknown pen
with tempfile.TemporaryDirectory() as t:
    d = os.path.join(t, "medres")
    os.makedirs(d)
    for name in si.IMAGES[1:]:                          # no close
        with open(os.path.join(d, name + ".txt"), "w") as f:
            si.write(name, rows("medres", name), f)
    with open(os.path.join(d, "up.txt"), "w") as f:
        f.write("image up\nsize 11 11\n" + "\n".join(rows("medres", "up")[:10]) + "\n")
    with open(os.path.join(d, "down.txt"), "w") as f:
        si.write("down", ["#" * 7] * 7, f)
    errs = si.check_set("medres", t)
    ok(any("no close" in e for e in errs), f"missing close not caught: {errs}")
    ok(any("down.txt: 7x7" in e for e in errs), f"wrong size not caught: {errs}")
    ok(any("up.txt: 10 rows" in e for e in errs), f"short image not caught: {errs}")
    bad = os.path.join(t, "bad.txt")
    with open(bad, "w") as f:
        f.write("image up\nsize 3 1\n.x.\n")
    try:
        si.read(bad)
        ok(False, "an unknown pen read")
    except ValueError as e:
        ok("can't read '.x.'" in str(e), f"unknown pen: {e}")

# today's glyphs: the port draws in the box it is given and the boxes give today's sizes
for s, (w, h, _) in si.SETS.items():
    for name in si.IMAGES:
        r = si.today(name, w, h)
        ok(len(r) == h and all(len(x) == w for x in r), f"today {name} in {w}x{h}")
# oi_look_glyph's close cross at 11 x 11: g = 11 - 3 = 8, then 8 * 2 / 3 + 1 = 6 rows of the cross
ok(sum(1 for r in si.today("close", 11, 11) if "#" in r) == 6, "today's close at 11 is 6 rows")
ok(not any("#" in r for r in si.today("submenu", 11, 11)), "today's sub-item mark is text, not a glyph")

# the specimen draws
try:
    import PIL  # noqa: F401
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "s.png")
        si.specimen(out)
        from PIL import Image
        w, h = Image.open(out).size
        ok(w > 600 and h > 800, f"specimen is {w}x{h}")
except ImportError:
    print("specimen: no PIL, skipped")

print("sysimages:", "FAIL" if fails else "all good")
sys.exit(1 if fails else 0)
