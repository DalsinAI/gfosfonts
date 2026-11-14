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
    """the hand file: a character on its own line (or 'char U+XXXX'), then its rows; width = the row length"""
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
        if cur is None and line.startswith("char U+"):   # a character a name line can't hold, e.g. '#'
            cur = int(line[7:].split()[0], 16)
            glyphs[cur] = []
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

# ---- Latin-1's accented letters, made from the hand-drawn letters and these marks (14 Nov 2026) ----
# A small letter's mark sits in rows 0-1 (the x-height starts on row 3, so row 2 stays clear; the ring takes
# rows 0-2). A capital's mark takes rows 0-1 too: the capital loses one of two like rows (a straight run of its
# stems) and moves down a row to rows 2-9, so the mark sits on it (a dot over a capital told grave from acute
# from nothing). A capital with no two like rows keeps its height and the mark is drawn over its top row. The
# cedilla hangs under the baseline, rows 10-11.
MARKS_SMALL = {"grave": ["#.", ".#"], "acute": [".#", "#."], "circ": [".#.", "#.#"], "tilde": [".#.#", "#.#."],
               "diaer": ["...", "#.#"], "ring": [".#.", "#.#", ".#."]}
MARKS_CAP = {"grave": ["#.", ".#"], "acute": [".#", "#."], "circ": [".#.", "#.#"], "tilde": [".#.#", "#.#."],
             "diaer": ["#.#", "..."], "ring": [".#.", "#.#"]}       # the ring closes on the A's apex
LATIN1 = {  # codepoint: the letter, then its mark
    0xC0: "Agrave", 0xC1: "Aacute", 0xC2: "Acirc", 0xC3: "Atilde", 0xC4: "Adiaer", 0xC5: "Aring",
    0xC8: "Egrave", 0xC9: "Eacute", 0xCA: "Ecirc", 0xCB: "Ediaer", 0xCC: "Igrave", 0xCD: "Iacute", 0xCE: "Icirc",
    0xCF: "Idiaer", 0xD1: "Ntilde", 0xD2: "Ograve", 0xD3: "Oacute", 0xD4: "Ocirc", 0xD5: "Otilde", 0xD6: "Odiaer",
    0xD9: "Ugrave", 0xDA: "Uacute", 0xDB: "Ucirc", 0xDC: "Udiaer", 0xDD: "Yacute",
    0xE0: "agrave", 0xE1: "aacute", 0xE2: "acirc", 0xE3: "atilde", 0xE4: "adiaer", 0xE5: "aring",
    0xE8: "egrave", 0xE9: "eacute", 0xEA: "ecirc", 0xEB: "ediaer", 0xEC: "igrave", 0xED: "iacute", 0xEE: "icirc",
    0xEF: "idiaer", 0xF1: "ntilde", 0xF2: "ograve", 0xF3: "oacute", 0xF4: "ocirc", 0xF5: "otilde", 0xF6: "odiaer",
    0xF9: "ugrave", 0xFA: "uacute", 0xFB: "ucirc", 0xFC: "udiaer", 0xFD: "yacute", 0xFF: "ydiaer",
}
CEDILLA = {0xC7: "C", 0xE7: "c"}

def ink_centre(rows, top, bottom):
    cols = [x for x in range(len(rows[0])) if any(rows[y][x] == "#" for y in range(top, bottom))]
    return (min(cols) + max(cols)) / 2 if cols else len(rows[0]) / 2

def put(rows, mark, y0, centre):
    rows = [list(r) for r in rows]
    x0 = int(round(centre - (len(mark[0]) - 1) / 2))
    x0 = max(0, min(x0, len(rows[0]) - len(mark[0])))
    for dy, line in enumerate(mark):
        for dx, c in enumerate(line):
            if c == "#": rows[y0 + dy][x0 + dx] = "#"
    return ["".join(r) for r in rows]

def lower_cap(rows):
    """the capital in rows 1-9 moved down a row by dropping one of two like rows; None when it has none"""
    for y in (5, 4, 6, 3, 7, 2):                        # a like pair, nearest the middle first, keeps the shape
        if rows[y] == rows[y + 1] and "#" in rows[y]:
            return [rows[0], "." * len(rows[0])] + rows[1:y] + rows[y + 1:]
    return None

def compose(hand):
    """Latin-1's accented letters and the cedillas from the hand-drawn letters: {codepoint: rows}"""
    out = {}
    for cp, name in LATIN1.items():
        letter, mark = name[0], name[1:]
        base = hand.get(ord(letter))
        if base is None: continue
        if letter.isupper():
            moved = lower_cap(base)
            rows = moved or base
            out[cp] = put(rows, MARKS_CAP[mark], 0, ink_centre(rows, 1, 10))
        else:
            rows = list(base)
            if letter in "ij":                          # the dotless letter under the mark
                rows = ["." * len(rows[0])] * 3 + rows[3:]
            out[cp] = put(rows, MARKS_SMALL[mark], 0, ink_centre(rows, 3, 10))
    for cp, letter in CEDILLA.items():
        base = hand.get(ord(letter))
        if base is None: continue
        c = ink_centre(base, 1 if letter.isupper() else 3, 10)
        out[cp] = put(base, [".#", "#."], 10, c + 0.5)
    return out

def merge(base, handp, name):
    glyphs, size, ascent = read(base)
    hand = read_hand(handp)
    made = compose(hand)
    for cp, rows in list(made.items()) + list(hand.items()):   # what is drawn by hand wins
        if len(rows) != size:
            raise SystemExit(f"{chr(cp)!r}: {len(rows)} rows, not {size}")
        glyphs[cp] = [len(rows[0]), 0, rows]
    write(glyphs, size, ascent, name, set(hand) | set(made), sys.stdout)

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
    if handp:
        h = read_hand(handp)
        hand = set(h) | set(compose(h))
    else:
        hand = set(glyphs)
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
             "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
             "\u00c0\u00c1\u00c2\u00c3\u00c4\u00c5\u00c7\u00c8\u00c9\u00ca\u00cb\u00cc\u00cd\u00ce\u00cf\u00d1\u00d2\u00d3\u00d4\u00d5\u00d6\u00d9\u00da\u00db\u00dc\u00dd",
             "\u00e0\u00e1\u00e2\u00e3\u00e4\u00e5\u00e7\u00e8\u00e9\u00ea\u00eb\u00ec\u00ed\u00ee\u00ef\u00f1\u00f2\u00f3\u00f4\u00f5\u00f6\u00f9\u00fa\u00fb\u00fc\u00fd\u00ff",
             "Fran\u00e7ois, se\u00f1or, M\u00fcller, \u00c9cole, na\u00efve, \u00c5ngstr\u00f6m",
             "This is an Amiga with a 68040 and an FPU.",
             "RAM Disk: 1,024 KB free (98%) - Work:Games/[OK] {x+y=z} #1 ~ok? @3.2"]
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
