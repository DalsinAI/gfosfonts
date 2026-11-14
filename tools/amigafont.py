#!/usr/bin/env python3
"""amigafont: a grid font (src/*.txt) as an Amiga bitmap font, the files diskfont.library loads from FONTS:.

  amigafont.py build FONT.txt NAME OUTDIR [MORE.txt...]   writes OUTDIR/NAME/<size> for each grid and
                                            OUTDIR/NAME.font (the contents file) listing every size
  amigafont.py dump OUTDIR/NAME/<size>      prints what a font file holds (size, baseline, chars, widths)
  amigafont.py c FONT.txt NAME OUT.h PREFIX  writes the grid as C constant data for a ROM font (openintuition's
                                            fonts/: the system default text, added to the font list at start)

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
    fw = fixed_width(glyphs)
    if fw and fw > dw:                                   # a monospaced face: the box takes the same width
        drows = [r + "." * (fw - dw) for r in drows]
        dw = fw
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


def fixed_width(glyphs):
    """the one width every glyph has (a monospaced face), else None"""
    ws = {g[0] for g in glyphs.values()}
    return ws.pop() if len(ws) == 1 else None

def font_flags(glyphs):
    """DISKFONT and DESIGNED, and PROPORTIONAL unless every glyph is one width"""
    return FPF_DISKFONT | FPF_DESIGNED | (0 if fixed_width(glyphs) else FPF_PROPORTIONAL)

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
    nwidth = fixed_width(glyphs) or glyphs.get(ord("n"), (7,))[0]
    struct.pack_into(">HHBBHHHHBB", h, t + 18, 52, size, 0, font_flags(glyphs),
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


def contents_file(name, sizes, flags=FPF_DISKFONT | FPF_PROPORTIONAL | FPF_DESIGNED):
    """NAME.font: a FontContentsHeader and one FontContents (260 bytes) per size, 'NAME/<size>'"""
    b = bytearray(struct.pack(">HH", FCH_ID, len(sizes)))
    for y in sizes:
        e = bytearray(260)
        f = f"{name}/{y}".encode()
        e[:len(f)] = f
        struct.pack_into(">HBB", e, 256, y, 0, flags)
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


def build(src, name, outdir, *more):
    """one font file per grid (one size each), and the contents file listing the sizes, smallest first"""
    os.makedirs(os.path.join(outdir, name), exist_ok=True)
    sizes, flags = [], FPF_DISKFONT | FPF_PROPORTIONAL | FPF_DESIGNED
    for path in (src,) + more:
        glyphs, size, ascent = gridfont.read(path)
        if size in sizes:
            raise SystemExit(f"{path}: a second {size} px grid")
        sizes.append(size)
        flags = font_flags(glyphs)
        with open(os.path.join(outdir, name, str(size)), "wb") as fp:
            fp.write(font_file(glyphs, size, ascent, f"{name}.font"))
    with open(os.path.join(outdir, name + ".font"), "wb") as fp:
        fp.write(contents_file(name, sorted(sizes), flags))


def c_header(src, name, prefix):
    """the grid as C constant data (tf_CharData, tf_CharLoc and the TextFont's numbers), for a ROM font"""
    import hashlib
    glyphs, size, ascent = gridfont.read(src)
    loc, space, modulo, plane = bitmap(glyphs, size, ascent)
    fw, P = fixed_width(glyphs), prefix.upper()
    sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
    out = [f"/* {name} {size} as constant data, made by gfosfonts' tools/amigafont.py:",
           f" *   amigafont.py c {src} {name} OUT {prefix}",
           f" * from {src} (sha256 {sha}).",
           " * GFOS's own pixel font: the fonts' licence is gfosfonts' LICENSE-FONTS (DejaVu's changes are public",
           " * domain; the notice goes with every copy). Don't edit by hand: change the grid, then make this again. */",
           f'#define {P}_NAME "{name}"', f"#define {P}_YSIZE {size}", f"#define {P}_XSIZE {fw or max(space)}",
           f"#define {P}_BASELINE {ascent - 1}", f"#define {P}_BOLDSMEAR 1",
           f"#define {P}_LOCHAR {LO}", f"#define {P}_HICHAR {HI}", f"#define {P}_MODULO {modulo}",
           f"/* tf_CharData: {size} rows of {modulo} bytes */",
           f"static const unsigned char {prefix}_data[{len(plane)}] = {{"]
    out += ["    " + " ".join(f"0x{b:02x}," for b in plane[i:i + 16]) for i in range(0, len(plane), 16)]
    out += ["};", f"/* tf_CharLoc: for each character {LO} to {HI} and the default glyph, its first bit (high word) "
            "and width (low word) */", f"static const unsigned long {prefix}_loc[{len(loc)}] = {{"]
    words = [f"0x{(x << 16) | w:08x}," for x, w in loc]
    out += ["    " + " ".join(words[i:i + 8]) for i in range(0, len(words), 8)]
    if not fw:
        out += ["};", f"static const short {prefix}_space[{len(space)}] = {{"]
        out += ["    " + " ".join(f"{v}," for v in space[i:i + 16]) for i in range(0, len(space), 16)]
    return "\n".join(out + ["};"]) + "\n"


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 4 and a[0] == "build":
        build(*a[1:])
    elif len(a) == 5 and a[0] == "c":
        open(a[3], "w").write(c_header(a[1], a[2], a[4]))
    elif len(a) == 2 and a[0] == "dump":
        f = read(open(a[1], "rb").read())
        print(f"{f['name']}: {f['size']} px, baseline {f['baseline']}, chars ${f['lo']:02X}-${f['hi']:02X}, "
              f"modulo {f['modulo']}, widths {sorted(set(w for _, w in f['loc']))}")
    else:
        sys.exit(__doc__)
