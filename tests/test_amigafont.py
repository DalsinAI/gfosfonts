#!/usr/bin/env python3
"""amigafont's checks: the font files diskfont.library loads, built from GFOS Sans 13 and read back through their
relocations (python3 tests/test_amigafont.py, from the repo's root)."""
import os, struct, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import amigafont, gridfont

fails = oks = 0
def check(c, what):
    global fails, oks
    if c: oks += 1
    else: fails += 1; print("FAIL", what)

glyphs, size, ascent = gridfont.read("src/gfos-sans-13.txt")
with tempfile.TemporaryDirectory() as d:
    amigafont.build("src/gfos-sans-13.txt", "GFOSSans", d)
    data = open(os.path.join(d, "GFOSSans", "13"), "rb").read()
    fc = open(os.path.join(d, "GFOSSans.font"), "rb").read()
f = amigafont.read(data)
# the file
check(struct.unpack_from(">I", data, 0)[0] == 0x3F3 and data[-4:] == struct.pack(">I", 0x3F2), "a hunk file, one hunk")
check(struct.unpack_from(">I", data, 32)[0] == 0x70FF4E75, "it starts MOVEQ #-1,D0; RTS")
check(f["name"] == "GFOSSans.font" and "Vera" not in f["name"] and "Bitstream" not in f["name"], "named GFOSSans.font")
check(f["size"] == 13 and f["baseline"] == 9 and f["lo"] == 0x20 and f["hi"] == 0xFF, "13 px, baseline row 9, $20-$FF")
check(f["flags"] == amigafont.FPF_DISKFONT | amigafont.FPF_PROPORTIONAL | amigafont.FPF_DESIGNED,
      "a designed proportional disk font")
check(f["modulo"] % 2 == 0 and f["modulo"] * 8 >= sum(w for _, w in f["loc"][:0x60]), "an even modulo, wide enough")
# every glyph as drawn
check(all(amigafont.glyph_rows(f, c) == glyphs[c][2] for c in glyphs), "every glyph reads back as its grid")
check(all(f["space"][c - 0x20] == glyphs[c][0] for c in glyphs), "spacing is each glyph's width")
check(not any(f["kern"]), "no kerning")
box = amigafont.glyph_rows(f, 0x100)
check(all(amigafont.glyph_rows(f, c) == box for c in range(0x7F, 0xA0)), "$7F-$9F get the default glyph")
check(box[1] == ".#####" and box[ascent - 1] == ".#####", "the default glyph is a box, cap line to baseline")
check(all(0 <= x and x + w <= f["modulo"] * 8 for x, w in f["loc"]), "every location inside the bitmap")
# the contents file
check(len(fc) == 4 + 260 and struct.unpack_from(">HH", fc, 0) == (0x0F00, 1), "GFOSSans.font: one entry")
check(fc[4:4 + 11] == b"GFOSSans/13" and fc[4 + 11] == 0, "its entry names GFOSSans/13")
check(struct.unpack_from(">HBB", fc, 4 + 256) == (13, 0, f["flags"]), "its entry: 13, plain, the font's flags")
# both sizes in one contents file (11 and 13)
with tempfile.TemporaryDirectory() as d:
    amigafont.build("src/gfos-sans-13.txt", "GFOSSans", d, "src/gfos-sans-11.txt")
    f11 = amigafont.read(open(os.path.join(d, "GFOSSans", "11"), "rb").read())
    fc2 = open(os.path.join(d, "GFOSSans.font"), "rb").read()
    check(os.path.exists(os.path.join(d, "GFOSSans", "13")), "the 13 px file is written too")
check(struct.unpack_from(">HH", fc2, 0) == (0x0F00, 2) and len(fc2) == 4 + 2 * 260, "GFOSSans.font: two entries")
check(fc2[4:15] == b"GFOSSans/11" and fc2[264:275] == b"GFOSSans/13", "the entries name 11 then 13")
check(struct.unpack_from(">H", fc2, 4 + 256)[0] == 11 and struct.unpack_from(">H", fc2, 264 + 256)[0] == 13,
      "the entries' sizes, smallest first")
g11 = gridfont.read("src/gfos-sans-11.txt")[0]
check(f11["size"] == 11 and f11["baseline"] == 8, "11 px, baseline row 8")
check(all(amigafont.glyph_rows(f11, c) == g11[c][2] for c in g11), "every 11 px glyph reads back as its grid")
check(all(amigafont.glyph_rows(f11, c) == amigafont.glyph_rows(f11, 0x100) for c in range(0xA0, 0x100)),
      "11 px: Latin-1 not yet drawn, so it gets the default glyph")
try:
    with tempfile.TemporaryDirectory() as d:
        amigafont.build("src/gfos-sans-13.txt", "GFOSSans", d, "src/gfos-sans-13.txt")
    check(False, "two grids of one size refused")
except SystemExit:
    check(True, "two grids of one size refused")
print(f"test_amigafont: {oks + fails} checks, {fails} failed")
sys.exit(1 if fails else 0)
