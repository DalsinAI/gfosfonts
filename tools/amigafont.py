#!/usr/bin/env python3
"""amigafont: a grid font (src/*.txt) as an Amiga bitmap font, the files diskfont.library loads from FONTS:.

  amigafont.py build FONT.txt NAME OUTDIR   writes OUTDIR/NAME.font (the contents file) and OUTDIR/NAME/<size>
  amigafont.py dump OUTDIR/NAME/<size>      prints what a font file holds (size, baseline, chars, widths)

The font file is one code hunk (MOVEQ #-1,D0; RTS so that running it by mistake does nothing), then the
DiskFontHeader, the TextFont, the character locations, spacing and kerning and the glyph bitmap, with a RELOC32
for each pointer: the layout of the NDK's diskfont/diskfont.h and graphics/text.h, written by our own code.

Characters $20-$FF; any the grid font doesn't have ($7F-$9F in Latin-1) get the font's default glyph, a box, which
is also the glyph past tf_HiChar that graphics draws for a character outside the font. Every glyph's width is its
grid's width, so tf_CharSpace is the width and tf_CharKern 0. MIT, AmiCradle Team."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gridfont

DFH_ID, FCH_ID = 0x0F80, 0x0F00
NT_FONT = 12
FPF_DISKFONT, FPF_PROPORTIONAL, FPF_DESIGNED = 0x02, 0x20, 0x40
HUNK_HEADER, HUNK_CODE, HUNK_RELOC32, HUNK_END = 0x3F3, 0x3E9, 0x3EC, 0x3F2
LO, HI = 0x20, 0xFF


def default_glyph(size, ascent):
    """the box drawn for a character the font hasn't: 5 wide, from the cap line to the baseline"""
    rows = ["." * 6 for _ in range(size)]
    for y in range(1, ascent):
        rows[y] = ".#...#" if 1 < y < ascent - 1 else ".#####"
    return 6, rows


def bitmap(glyphs, size, ascent):
    """(locations, spacing, modulo, plane): every glyph from LO to HI and the default glyph after them"""
    dw, drows = default_glyph(size, ascent)
    order = [glyphs.get(c) for c in range(LO, HI + 1)] + [None]
    xs, cols = [], 0
    pieces = []
    for g in order:
        w, rows = (g[0], g[2]) if g else (dw, drows)
        pieces.append((cols, w, rows))
        cols += w
    modulo = ((cols + 15) // 16) * 2
    plane = bytearray(modulo * size)
    loc, space = [], []
    default_at = pieces[-1][0]
    for i, (x0, w, rows) in enumerate(pieces):
        if order[i] is None and i < len(pieces) - 1:          # a character the font hasn't: the default glyph
            loc.append((default_at, dw)); space.append(dw)
            continue
        loc.append((x0, w)); space.append(w)
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                if c == "#":
                    b = x0 + x
                    plane[y * modulo + (b >> 3)] |= 0x80 >> (b & 7)
    return loc, space, modulo, plane


def font_file(glyphs, size, ascent, name):
    """the font file's bytes"""
    h = bytearray(4 + 54 + 52)
    relocs = []

    def ptr(at, to):
        struct.pack_into(">I", h, at, to)
        relocs.append(at)

    def add(b):
        if len(h) & 1: h.append(0)
        at = len(h)
        h.extend(b)
        return at

    loc, space, modulo, plane = bitmap(glyphs, size, ascent)
    struct.pack_into(">I", h, 0, 0x70FF4E75)                     # MOVEQ #-1,D0; RTS
    d = 4                                                         # struct DiskFontHeader
    h[d + 8] = NT_FONT
    ptr(d + 10, d + 22)                                           # ln_Name -> dfh_Name
    struct.pack_into(">HH", h, d + 14, DFH_ID, 1)
    nm = name.encode("latin-1")[:31]
    h[d + 22:d + 22 + len(nm)] = nm
    t = d + 54                                                    # struct TextFont
    h[t + 8] = NT_FONT
    ptr(t + 10, d + 22)
    nwidth = glyphs.get(ord("n"), (7,))[0]
    struct.pack_into(">HHBBHHHHBB", h, t + 18, 52, size, 0, FPF_DISKFONT | FPF_PROPORTIONAL | FPF_DESIGNED,
                     nwidth, ascent - 1, 1, 0, LO, HI)
    struct.pack_into(">H", h, t + 38, modulo)
    ptr(t + 40, add(b"".join(struct.pack(">HH", o, w) for o, w in loc)))
    ptr(t + 44, add(b"".join(struct.pack(">h", v) for v in space)))
    ptr(t + 48, add(b"\0\0" * len(space)))
    ptr(t + 34, add(bytes(plane)))
    while len(h) & 3: h.append(0)
    out = struct.pack(">IIIIII", HUNK_HEADER, 0, 1, 0, 0, len(h) // 4)
    out += struct.pack(">II", HUNK_CODE, len(h) // 4) + bytes(h)
    out += struct.pack(">III", HUNK_RELOC32, len(relocs), 0) + b"".join(struct.pack(">I", r) for r in relocs)
    out += struct.pack(">II", 0, HUNK_END)
    return out


def contents_file(name, sizes):
    """NAME.font: a FontContentsHeader and one FontContents (260 bytes) per size, 'NAME/<size>'"""
    b = bytearray(struct.pack(">HH", FCH_ID, len(sizes)))
    for y in sizes:
        e = bytearray(260)
        f = f"{name}/{y}".encode()
        e[:len(f)] = f
        struct.pack_into(">HBB", e, 256, y, 0, FPF_DISKFONT | FPF_PROPORTIONAL | FPF_DESIGNED)
        b += e
    return bytes(b)


def read(data):
    """a font file read back through its relocations: dict(size, baseline, lo, hi, modulo, loc, space, kern, plane)"""
    g = lambda o: struct.unpack_from(">I", data, o)[0]
    assert g(0) == HUNK_HEADER and g(8) == 1
    n = g(20)
    o = 24
    assert g(o) == HUNK_CODE and g(o + 4) == n
    h = bytearray(data[o + 8:o + 8 + 4 * n])
    o += 8 + 4 * n
    if g(o) == HUNK_RELOC32:
        o += 4
        while g(o):
            k, o = g(o), o + 8
            o += 4 * k
        o += 4
    assert g(o) == HUNK_END
    u16 = lambda a: struct.unpack_from(">H", h, a)[0]
    u32 = lambda a: struct.unpack_from(">I", h, a)[0]
    d, t = 4, 58
    assert u16(d + 14) == DFH_ID and u32(t + 10) == d + 22
    size, lo, hi, modulo = u16(t + 20), h[t + 32], h[t + 33], u16(t + 38)
    k = hi - lo + 2
    loc = [struct.unpack_from(">HH", h, u32(t + 40) + 4 * i) for i in range(k)]
    space = [struct.unpack_from(">h", h, u32(t + 44) + 2 * i)[0] for i in range(k)]
    kern = [struct.unpack_from(">h", h, u32(t + 48) + 2 * i)[0] for i in range(k)]
    plane = bytes(h[u32(t + 34):u32(t + 34) + modulo * size])
    name = bytes(h[d + 22:d + 54]).split(b"\0")[0].decode("latin-1")
    return dict(name=name, size=size, flags=h[t + 23], xsize=u16(t + 24), baseline=u16(t + 26), lo=lo, hi=hi,
                modulo=modulo, loc=loc, space=space, kern=kern, plane=plane)


def glyph_rows(f, c):
    """character c's rows as '.'/'#' strings, from a read() font"""
    i = c - f["lo"] if f["lo"] <= c <= f["hi"] else f["hi"] - f["lo"] + 1
    x0, w = f["loc"][i]
    return ["".join("#" if f["plane"][y * f["modulo"] + ((x0 + x) >> 3)] & (0x80 >> ((x0 + x) & 7)) else "."
                    for x in range(w)) for y in range(f["size"])]


def build(src, name, outdir):
    glyphs, size, ascent = gridfont.read(src)
    os.makedirs(os.path.join(outdir, name), exist_ok=True)
    with open(os.path.join(outdir, name, str(size)), "wb") as fp:
        fp.write(font_file(glyphs, size, ascent, f"{name}.font"))
    with open(os.path.join(outdir, name + ".font"), "wb") as fp:
        fp.write(contents_file(name, [size]))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == "build":
        build(a[1], a[2], a[3])
    elif len(a) == 2 and a[0] == "dump":
        f = read(open(a[1], "rb").read())
        print(f"{f['name']}: {f['size']} px, baseline {f['baseline']}, chars ${f['lo']:02X}-${f['hi']:02X}, "
              f"modulo {f['modulo']}, widths {sorted(set(w for _, w in f['loc']))}")
    else:
        sys.exit(__doc__)
