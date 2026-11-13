#!/usr/bin/env python3
"""gridfont: GFOS's pixel-grid fonts (src/*.txt) read, checked, merged and drawn.

  gridfont.py merge BASE.txt HAND.txt NAME > OUT.txt   base (dump_grid's) with the hand-drawn glyphs over it
  gridfont.py check FONT.txt                            the rules: rows, widths, 1 px stems in the hand set
  gridfont.py specimen OUT.png LABEL1=A.txt LABEL2=B.txt  Dale's specimen sheet, the faces one under the other

The grid format (src/README.md): 'size N', 'ascent N', then per glyph 'char U+XXXX c', 'width N',
optional 'origin N' (columns left of the origin), and N rows of '.' and '#'. MIT, AmiCradle Team.
"""
import sys

def read(path):
    """{codepoint: (width, origin, rows)}, size, ascent"""
    size = ascent = None
    glyphs, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line and set(line) <= set(".#") and cur is not None:
            glyphs[cur][2].append(line)
            continue
        if line.startswith("#"):
            continue
        if not line:
            cur = None
            continue
        w = line.split(" ", 2)
        if w[0] == "size": size = int(w[1]); continue
        if w[0] == "ascent": ascent = int(w[1]); continue
        if w[0] == "char":
            cur = int(w[1][2:], 16)
            glyphs[cur] = [0, 0, []]
            continue
        if w[0] == "width": glyphs[cur][0] = int(w[1]); continue
        if w[0] == "origin": glyphs[cur][1] = int(w[1]); continue
        if set(line) <= set(".#"):
            glyphs[cur][2].append(line)
            continue
        raise SystemExit(f"{path}: can't read {line!r}")
    return glyphs, size, ascent

def read_hand(path):
    """the hand file: a character on its own line, then its rows; width = the row length"""
    glyphs, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if cur is not None and line and set(line) <= set(".#"):
            glyphs[cur].append(line)
            continue
        if line.startswith("#"):
            continue
        if not line:
            cur = None
            continue
        if cur is None and not (set(line) <= set(".#") and len(line) > 1 or line == "."):
            cur = ord(line)
            glyphs[cur] = []
            continue
        if cur is None and line == "." :
            cur = ord(".")
            glyphs[cur] = []
            continue
        glyphs[cur].append(line)
    return glyphs

def write(glyphs, size, ascent, name, hand, out):
    out.write(f"# {name}: GFOS's own pixel font. Hand-drawn characters marked 'hand';\n")
    out.write("# the rest still DejaVu Sans as GFOS draws it today (tools/dump_grid), to be redrawn.\n")
    out.write("# DejaVu changes are public domain; Bitstream Vera licence: LICENSE-VERA.txt.\n")
    out.write(f"size {size}\nascent {ascent}\n\n")
    for cp in sorted(glyphs):
        w, o, rows = glyphs[cp]
        ch = "_" if cp == 32 else chr(cp)
        out.write(f"char U+{cp:04X} {ch}\n")
        if cp in hand: out.write("# hand\n")
        out.write(f"width {w}\n")
        if o: out.write(f"origin {o}\n")
        out.write("\n".join(rows) + "\n\n")

def merge(base, handp, name):
    glyphs, size, ascent = read(base)
    hand = read_hand(handp)
    for cp, rows in hand.items():
        if len(rows) != size:
            raise SystemExit(f"{chr(cp)!r}: {len(rows)} rows, not {size}")
        glyphs[cp] = [len(rows[0]), 0, rows]
    write(glyphs, size, ascent, name, set(hand), sys.stdout)

def stems(rows):
    """runs of 2+ set pixels across that stay 2+ wide for 3+ rows down: a 2 px stem"""
    bad = []
    h, w = len(rows), len(rows[0])
    for x in range(w - 1):
        run = 0
        for y in range(h):
            if rows[y][x] == "#" and rows[y][x + 1] == "#":
                run += 1
                if run == 3: bad.append((x, y - 2))
            else:
                run = 0
    return bad

def blobs(rows):
    """a 2x2 block of set pixels"""
    return [(x, y) for y in range(len(rows) - 1) for x in range(len(rows[0]) - 1)
            if rows[y][x] == rows[y][x + 1] == rows[y + 1][x] == rows[y + 1][x + 1] == "#"]

def check(path, handp=None):
    glyphs, size, ascent = read(path)
    hand = set(read_hand(handp)) if handp else set(glyphs)
    errs = 0
    for cp, (w, o, rows) in sorted(glyphs.items()):
        if len(rows) != size or any(len(r) != len(rows[0]) for r in rows):
            print(f"U+{cp:04X}: rows not {size} or not all one width"); errs += 1; continue
        if cp in hand:
            for what, f in (("2 px stem", stems), ("2x2 blob", blobs)):
                for x, y in f(rows):
                    print(f"U+{cp:04X} {chr(cp)}: {what} at column {x}, row {y}"); errs += 1
    print(f"{path}: {len(glyphs)} glyphs, {len(hand & set(glyphs))} checked, {errs} problems")
    return errs

def draw(glyphs, text, missing=63):
    """the line as rows of 0/1"""
    size = len(next(iter(glyphs.values()))[2])
    cols = [[] for _ in range(size)]
    pen = 0
    pieces = []
    for ch in text:
        g = glyphs.get(ord(ch)) or glyphs.get(missing)
        w, o, rows = g
        pieces.append((pen - o, rows))
        pen += w
    width = max([pen] + [x + len(r[0]) for x, r in pieces])
    img = [[0] * width for _ in range(size)]
    for x, rows in pieces:
        for y, row in enumerate(rows):
            for i, c in enumerate(row):
                if c == "#" and 0 <= x + i < width: img[y][x + i] = 1
    return img

def specimen(out, faces):
    from PIL import Image
    lines = ["abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789",
             "This is an Amiga with a 68040 and an FPU."]
    loaded = [(label, read(p)[0]) for label, p in faces]
    label_font = loaded[-1][1]
    Z, M, GAP = 4, 16, 10                               # zoom, margin, gap
    blocks = []                                         # (image rows, zoom)
    for label, g in loaded:
        blocks.append((draw(label_font, label), 1, "label"))
        for ln in lines:
            blocks.append((draw(g, ln), 1, "1x"))
        for ln in lines:
            blocks.append((draw(g, ln), Z, "zoom"))
    width = max(len(b[0][0]) * b[1] for b in blocks) + 2 * M
    height = sum(len(b[0]) * b[1] + GAP for b in blocks) + 2 * M + GAP * len(loaded)
    im = Image.new("RGB", (width, height), (255, 255, 255))
    px = im.load()
    y = M
    for k, (rows, z, kind) in enumerate(blocks):
        if kind == "label" and k: y += GAP * 2
        ink = (40, 40, 40) if kind != "label" else (0, 85, 170)
        for r, row in enumerate(rows):
            for c, on in enumerate(row):
                if on:
                    for dy in range(z):
                        for dx in range(z):
                            px[M + c * z + dx, y + r * z + dy] = ink
        y += len(rows) * z + GAP
    im.save(out)

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "merge" and len(a) == 4: merge(a[1], a[2], a[3])
    elif a and a[0] == "check" and len(a) in (2, 3): sys.exit(1 if check(*a[1:]) else 0)
    elif a and a[0] == "specimen" and len(a) >= 3: specimen(a[1], [x.split("=", 1) for x in a[2:]])
    else: sys.exit(__doc__)
