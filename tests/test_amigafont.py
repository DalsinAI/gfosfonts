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
check(all(amigafont.glyph_rows(f11, c) == amigafont.glyph_rows(f11, 0x100) for c in range(0x7F, 0xA0))
      and amigafont.glyph_rows(f11, 0xE9) == g11[0xE9][2], "11 px: $7F-$9F the default glyph, Latin-1 drawn")
with tempfile.TemporaryDirectory() as d:
    amigafont.build("src/gfos-sans-13.txt", "GFOSSans", d, "src/gfos-sans-11.txt", "src/gfos-sans-16.txt")
    f16 = amigafont.read(open(os.path.join(d, "GFOSSans", "16"), "rb").read())
    fc3 = open(os.path.join(d, "GFOSSans.font"), "rb").read()
g16 = gridfont.read("src/gfos-sans-16.txt")[0]
check(struct.unpack_from(">H", fc3, 2)[0] == 3 and [struct.unpack_from(">H", fc3, 4 + 260 * i + 256)[0] for i in range(3)]
      == [11, 13, 16], "three sizes: 11, 13, 16")
check(f16["size"] == 16 and f16["baseline"] == 12 and all(amigafont.glyph_rows(f16, c) == g16[c][2] for c in g16),
      "16 px, baseline row 12, every glyph reads back")
with tempfile.TemporaryDirectory() as d:
    amigafont.build("src/gfos-sans-bold-13.txt", "GFOSSansBold", d)
    fb = amigafont.read(open(os.path.join(d, "GFOSSansBold", "13"), "rb").read())
gbold = gridfont.read("src/gfos-sans-bold-13.txt")[0]
check(fb["name"] == "GFOSSansBold.font" and all(amigafont.glyph_rows(fb, c) == gbold[c][2] for c in gbold),
      "GFOSSansBold/13: named GFOSSansBold.font, every glyph reads back")
with tempfile.TemporaryDirectory() as d:
    amigafont.build("src/gfos-mono-13.txt", "GFOSMono", d)
    fm = amigafont.read(open(os.path.join(d, "GFOSMono", "13"), "rb").read())
    fcm = open(os.path.join(d, "GFOSMono.font"), "rb").read()
gmono = gridfont.read("src/gfos-mono-13.txt")[0]
check(fm["flags"] == amigafont.FPF_DISKFONT | amigafont.FPF_DESIGNED and fm["xsize"] == 8,
      "GFOSMono/13: not proportional, tf_XSize 8")
check(struct.unpack_from(">HBB", fcm, 4 + 256)[2] == fm["flags"], "GFOSMono.font's entry: the same flags")
check(set(fm["space"]) == {8} and all(amigafont.glyph_rows(fm, c) == gmono[c][2] for c in gmono),
      "GFOSMono: every character, the default box too, 8 wide; every glyph reads back")
try:
    with tempfile.TemporaryDirectory() as d:
        amigafont.build("src/gfos-sans-13.txt", "GFOSSans", d, "src/gfos-sans-13.txt")
    check(False, "two grids of one size refused")
except SystemExit:
    check(True, "two grids of one size refused")
# the ROM's system default text (GFOS Mono 11, openintuition's fonts/): the C data is the font file's bitmap
import re
hdr = amigafont.c_header("src/gfos-mono-11.txt", "GFOSMono.font", "oi_gfm11")
gm11, _, a11 = gridfont.read("src/gfos-mono-11.txt")
loc, space, modulo, plane = amigafont.bitmap(gm11, 11, a11)
data = bytes(int(x, 16) for x in re.findall(r"0x([0-9a-f]{2}),", hdr.split("_data[")[1].split("};")[0]))
locs = [int(x, 16) for x in re.findall(r"0x([0-9a-f]{8}),", hdr.split("_loc[")[1].split("};")[0])]
check(data == bytes(plane) and locs == [(x << 16) | w for x, w in loc], "c header: the bitmap and locations as built")
check('#define OI_GFM11_NAME "GFOSMono.font"' in hdr and "#define OI_GFM11_XSIZE 7" in hdr and
      "#define OI_GFM11_BASELINE 8" in hdr and "_space[" not in hdr, "c header: GFOSMono.font 11, 7 wide, baseline 8, fixed")
print(f"test_amigafont: {oks + fails} checks, {fails} failed")
sys.exit(1 if fails else 0)
