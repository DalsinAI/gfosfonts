#!/usr/bin/env python3
"""gridfont's checks and the corrected set: run from the repo's root (python3 tests/test_gridfont.py)."""
import io, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import gridfont

fails = oks = 0
def check(c, what):
    global fails, oks
    if c: oks += 1
    else: fails += 1; print("FAIL", what)

# the rules catch what Dale saw: a 2 px stem, a 2x2 blob
check(gridfont.stems([".##.", ".##.", ".##."]) == [(1, 0)], "a 2 px stem three rows down is found")
check(gridfont.stems([".##.", ".#..", ".##."]) == [], "two rows of 2 px is not a stem")
check(gridfont.blobs(["##", "##"]) == [(0, 0)], "a 2x2 blob is found")
check(gridfont.blobs(["#.", ".#"]) == [], "a diagonal step is not a blob")

# the hand set: every glyph 13 rows, one width, no 2 px stem or blob
hand = gridfont.read_hand("src/gfos-sans-13-hand.txt")
need = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.")
check(need <= {chr(c) for c in hand}, "a-z, A-Z, 0-9 and '.' are all drawn by hand")
check(all(len(r) == 13 and len({len(x) for x in r}) == 1 for r in hand.values()), "13 rows, one width each")
check(all(not gridfont.stems(r) and not gridfont.blobs(r) for r in hand.values()), "1 px stems, no blobs")
# the ASCII punctuation, drawn by hand too (Lisette, 14 Nov)
check(set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~") <= {chr(c) for c in hand}, "the ASCII punctuation is drawn by hand")
check(gridfont.read_hand("src/gfos-sans-13-hand.txt")[ord("#")][3] == ".#######.", "'#' is read from its 'char U+0023' line")
for ch in ".,:;!":
    check(sum(r.count("#") for r in hand[ord(ch)][9:10]) == 1, f"{ch!r}: a 1 px dot on the baseline row")
check(hand[ord("(")] == [r[::-1] for r in hand[ord(")")]], "( and ) mirror each other")
check(hand[ord("[")] == [r[::-1] for r in hand[ord("]")]], "[ and ] mirror each other")
check(hand[ord("<")] == [r[::-1] for r in hand[ord(">")]], "< and > mirror each other")
# f and t never alike; the stems of n, m, h, u one column each
check(hand[ord("f")] != hand[ord("t")], "f and t differ")
check(hand[ord("f")][0].count("#") and not hand[ord("t")][0].count("#"), "f has a hook at the top, t none")
check(hand[ord("t")][9].endswith("##.") and hand[ord("f")][9] == "..#..", "t has a foot, f none")
for ch in "nmhu":
    rows = hand[ord(ch)][5:8]
    check(all(r.count("#") == r.count(".#") for r in rows), f"{ch}: every stem 1 px")
# x-height 7 (rows 3-9), capitals and figures 9 (rows 1-9)
for ch in "acemnorsuvwxz":
    r = hand[ord(ch)]
    check("#" in r[3] and "#" in r[9] and not any("#" in x for x in r[:3] + r[10:]), f"{ch}: x-height rows 3-9")
for ch in "ABDEFHKLMNPRTUVWXYZ0123456789":
    r = hand[ord(ch)]
    check("#" in r[1] and "#" in r[9] and "#" not in r[0], f"{ch}: rows 1-9")

# the font file is the merge of today's render and the hand set, as committed
out = subprocess.run([sys.executable, "tools/gridfont.py", "merge", "src/dejavu-sans-13-today.txt",
                      "src/gfos-sans-13-hand.txt", "GFOS Sans Regular 13"], capture_output=True, text=True)
check(out.returncode == 0 and out.stdout == open("src/gfos-sans-13.txt", encoding="utf-8").read(),
      "src/gfos-sans-13.txt is the merge, as committed")
g, size, ascent = gridfont.read("src/gfos-sans-13.txt")
check(size == 13 and ascent == 10 and len(g) == 191, "13 px, ascent 10, ISO-Latin-1 (191 characters)")
check(not any(0x7F <= c <= 0x9F for c in g), "$7F-$9F left empty")
check(gridfont.check("src/gfos-sans-13.txt", "src/gfos-sans-13-hand.txt") == 0, "gridfont check passes")

# Latin-1's letters with no plain letter under them, by hand (Lisette, 14 Nov)
check(set("ßæÆøØðÐþÞµ") <= {chr(c) for c in hand}, "ß æ Æ ø Ø ð Ð þ Þ µ are drawn by hand")
check(all("#" in "".join(hand[ord(c)][1:10]) and "#" not in "".join(hand[ord(c)][10:]) for c in "ÆØÐÞ"),
      "Æ Ø Ð Þ stand on the baseline, capitals' height")
check(all("#" in "".join(hand[ord(c)][10:]) for c in "þµ"), "þ and µ go under the baseline")

# Latin-1 complete: every character from $A0 to $FF drawn by hand or made from the hand set (Lisette, 14 Nov)
check(all(c in hand or c in gridfont.compose(hand) for c in range(0xA0, 0x100)), "$A0-$FF all drawn or made")
check(len(hand[0xA0][0]) == gridfont.read("src/gfos-sans-13.txt")[0][0x20][0] and "#" not in "".join(hand[0xA0]),
      "NBSP: blank, as wide as a space")
check(hand[0xAD] == hand[ord("-")], "the soft hyphen is the hyphen")

# Latin-1's accented letters, made from the hand set (Lisette, 14 Nov)
made = gridfont.compose(hand)
check(set(made) == set(gridfont.LATIN1) | set(gridfont.CEDILLA) and len(made) == 53, "53 accented letters made")
check(all(len(r) == 13 and not gridfont.stems(r) and not gridfont.blobs(r) for r in made.values()),
      "each made letter: 13 rows, 1 px stems, no blobs")
for cp in gridfont.LATIN1:
    r = made[cp]
    check("#" in r[0] + r[1], f"U+{cp:04X}: its mark is in rows 0-1")
    if chr(cp).isupper():
        check(all("#" in row for row in r[2:10]) and "#" not in "".join(r[10:]), f"U+{cp:04X}: the capital in rows 2-9")
    else:
        check(r[3:] == (hand[ord(gridfont.LATIN1[cp][0])][3:]), f"U+{cp:04X}: the letter under its mark as drawn")
check(made[0xE9][0].index("#") > made[0xE9][1].index("#"), "acute leans right")
check(made[0xE8][0].index("#") < made[0xE8][1].index("#"), "grave leans left")
check(all(made[c][10:12] != ["." * len(made[c][0])] * 2 for c in gridfont.CEDILLA), "the cedilla hangs under the baseline")
check(gridfont.compose({ord("e"): hand[ord("e")]}).keys() == {0xE8, 0xE9, 0xEA, 0xEB}, "only letters that are drawn are made")

# GFOS Sans 11 px (Lisette, 14 Nov): made from 13 px by shrink, the 11 px hand file over it
check(gridfont.drop_like(["a", "b", "b", "c"], 1) == ["a", "b", "c"], "drop_like drops one of two like rows")
check(gridfont.drop_like(["a", "b", "c"], 1) is None, "drop_like: None with no like rows")
check(gridfont.drop_like(["x", "x", "y", "y", "y", "z"], 1) == ["x", "x", "y", "y", "z"], "the like pair nearest the middle goes")
check(gridfont.narrow([".#....#."] * 3) == [".#...#."] * 3, "narrow: a column of two like ones goes")
check(gridfont.narrow(["#.....#", ".#...#.", "..#.#..", "...#..."]) == ["#.....#", ".#...#.", "..#.#..", "...#..."],
      "narrow: a diagonal letter keeps its width")
check(gridfont.narrow([".##.", ".##."]) == [".##.", ".##."], "narrow: under 7 columns unchanged")
out = subprocess.run([sys.executable, "tools/gridfont.py", "shrink", "src/gfos-sans-13.txt", "src/gfos-sans-11-hand.txt",
                      "GFOS Sans Regular 11"], capture_output=True, text=True)
check(out.returncode == 0 and out.stdout == open("src/gfos-sans-11.txt", encoding="utf-8").read(),
      "src/gfos-sans-11.txt is the shrink, as committed")
g11, s11, a11 = gridfont.read("src/gfos-sans-11.txt")
h11 = gridfont.read_hand("src/gfos-sans-11-hand.txt")
check(s11 == 11 and a11 == 9 and sorted(g11) == list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)),
      "11 px, ascent 9, ISO-Latin-1 like 13 px ($20-$7E, $A0-$FF)")
m11 = gridfont.compose({c: g11[c][2] for c in range(0x20, 0x7F)}, 11)
check(all(g11[c][2] == m11[c] for c in m11) and len(m11) == 53, "11 px: the 53 accented letters made from its own letters")
check(all("#" not in "".join(g11[ord(c)][2][3:4]) and "#" in "".join(g11[ord(c)][2][1:3]) for c in "àáâãäèéêëìíîïñòóôõöùúûüý"),
      "11 px small marks in rows 1-2, row 3 clear")
check(g11[0xC9][2][2] == "." * g11[0xC9][0] and "#" in g11[0xC9][2][3], "11 px É: the E lowered to rows 3-8 under its mark")
check(all("#" in "".join(g11[c][2][9:]) for c in (0xC7, 0xE7)), "11 px: the cedilla hangs under the baseline")
check(gridfont.lower_cap(["...."] * 2 + ["#..#"] * 7 + ["...."] * 2, 2, 9) == ["...."] * 3 + ["#..#"] * 6 + ["...."] * 2,
      "lower_cap at 11 px: the capital moves from rows 2-8 to rows 3-8")
check(all(len(r) == 11 and len({len(x) for x in r}) == 1 for _, _, r in g11.values()), "11 rows, one width each")
check(gridfont.check("src/gfos-sans-11.txt") == 0, "every 11 px glyph: 1 px stems, no blobs")
check(all(len(r) == 11 for r in h11.values()), "the 11 px hand file: 11 rows each")
check({g11[ord(c)][0] for c in "0123456789"} == {6}, "11 px figures all 6 wide")
for ch in "acemnorsuvwxz":
    r = g11[ord(ch)][2]
    check("#" in r[4] and "#" in r[8] and not any("#" in x for x in r[:4] + r[9:]), f"11 px {ch}: x-height rows 4-8")
for ch in "ABDEFHKLMNPRTUVWXYZ0123456789":
    r = g11[ord(ch)][2]
    check("#" in r[2] and "#" in r[8] and not any("#" in x for x in r[:2] + r[9:]), f"11 px {ch}: rows 2-8")
for ch in "gjpqy":
    check("#" in g11[ord(ch)][2][10], f"11 px {ch}: down to row 10")
check(g11[ord("f")][2] != g11[ord("t")][2] and "#" in g11[ord("f")][2][1] and "#" not in g11[ord("t")][2][1],
      "11 px: f keeps its hook, t none")
check(all(g11[ord(c)][0] <= g[ord(c)][0] for c in "abcdefghijklmnopqrstuvwxyz"), "11 px letters no wider than 13 px")
for ch in "SKXZ2$%&@<>¢¤¥§©®ª«»¼½¾Æ×÷Øßæøþ¸":
    check(ord(ch) in h11, f"11 px {ch!r} drawn by hand")
check(h11[ord("«")] == [r[::-1] for r in h11[ord("»")]], "11 px « and » mirror each other")

# GFOS Sans 16 px (Lisette, 14 Nov): made from 13 px by grow, the 16 px hand file over it
check(gridfont.add_like(["a", "b", "b", "c"], 1) == ["a", "b", "b", "b", "c"], "add_like adds beside two like rows")
check(gridfont.add_like(["a", "b", "c"], 1) is None, "add_like: None with no like rows")
check(gridfont.widen([".#....#."] * 3) == [".#.....#."] * 3, "widen: a column beside two like ones")
check(gridfont.widen(["#...#", ".#.#."]) == ["#...#", ".#.#."], "widen: under 6 columns unchanged")
out = subprocess.run([sys.executable, "tools/gridfont.py", "grow", "src/gfos-sans-13.txt", "src/gfos-sans-16-hand.txt",
                      "GFOS Sans Regular 16"], capture_output=True, text=True)
check(out.returncode == 0 and out.stdout == open("src/gfos-sans-16.txt", encoding="utf-8").read(),
      "src/gfos-sans-16.txt is the grow, as committed")
out = subprocess.run([sys.executable, "tools/gridfont.py", "shrink", "src/gfos-sans-13.txt", "src/gfos-sans-11-hand.txt",
                      "GFOS Sans Regular 11"], capture_output=True, text=True)
check(out.stdout == open("src/gfos-sans-11.txt", encoding="utf-8").read(), "shrink unchanged by the shared derive")
g16, s16, a16 = gridfont.read("src/gfos-sans-16.txt")
h16 = gridfont.read_hand("src/gfos-sans-16-hand.txt")
check(s16 == 16 and a16 == 13 and sorted(g16) == sorted(g11), "16 px, ascent 13, the same 191 characters")
check(all(len(r) == 16 and len({len(x) for x in r}) == 1 for _, _, r in g16.values()), "16 rows, one width each")
check(gridfont.check("src/gfos-sans-16.txt") == 0, "every 16 px glyph: 1 px stems, no blobs")
check({g16[ord(c)][0] for c in "0123456789"} == {8}, "16 px figures all 8 wide")
for ch in "acemnorsuvwxz":
    r = g16[ord(ch)][2]
    check("#" in r[5] and "#" in r[12] and not any("#" in x for x in r[:5] + r[13:]), f"16 px {ch}: x-height rows 5-12")
for ch in "ABDEFHKLMNPRTUVWXYZ0123456789":
    r = g16[ord(ch)][2]
    check("#" in r[2] and "#" in r[12] and not any("#" in x for x in r[:2] + r[13:]), f"16 px {ch}: rows 2-12")
for ch in "bdhkl":
    check("#" in g16[ord(ch)][2][1] and "#" not in g16[ord(ch)][2][0], f"16 px {ch}: the ascender from row 1")
for ch in "gjpqy":
    check("#" in "".join(g16[ord(ch)][2][13:]), f"16 px {ch}: under the baseline")
check(all(g16[ord(c)][0] >= g[ord(c)][0] for c in "abcdefghijklmnopqrstuvwxyz"), "16 px letters no narrower than 13 px")
m16 = gridfont.compose({c: g16[c][2] for c in range(0x20, 0x7F)}, 16)
check(all(g16[c][2] == m16[c] for c in m16) and len(m16) == 53, "16 px: the 53 accented letters made from its own letters")
check(all("#" not in g16[ord(c)][2][4] and "#" in "".join(g16[ord(c)][2][2:4]) for c in "àáâãäèéêëìíîïñòóôõöùúûüý"),
      "16 px small marks in rows 2-3, row 4 clear")
for ch in "<>Kz§©«®»¼½¾×æ÷ø24":
    check(ord(ch) in h16, f"16 px {ch!r} drawn by hand")
check(h16[ord("<")] == [r[::-1] for r in h16[ord(">")]] and h16[ord("«")] == [r[::-1] for r in h16[ord("»")]],
      "16 px < > and « » mirror each other")

# GFOS Sans Bold 13 px (Lisette, 14 Nov): Regular 13 set again a pixel right, the Bold hand file over it
check(gridfont.smear([".#..", "#..#"]) == [".##..", "##.##"], "smear: each pixel set again one to the right")
check(gridfont.counters([".###.", ".#.#.", ".###."]) == 1 and gridfont.counters(["#..", "#.."]) == 0,
      "counters: a closed inside counts, an open one doesn't")
out = subprocess.run([sys.executable, "tools/gridfont.py", "bold", "src/gfos-sans-13.txt", "src/gfos-sans-bold-13-hand.txt",
                      "GFOS Sans Bold 13"], capture_output=True, text=True)
check(out.returncode == 0 and out.stdout == open("src/gfos-sans-bold-13.txt", encoding="utf-8").read(),
      "src/gfos-sans-bold-13.txt is the bold, as committed")
gb, sb, ab = gridfont.read("src/gfos-sans-bold-13.txt")
hb = gridfont.read_hand("src/gfos-sans-bold-13-hand.txt")
check(sb == 13 and ab == 10 and sorted(gb) == sorted(g), "Bold 13: ascent 10, the same 191 characters as Regular")
check(all(len(r) == 13 and len({len(x) for x in r}) == 1 for _, _, r in gb.values()), "Bold: 13 rows, one width each")
check(all(gb[c][0] == g[c][0] + 1 for c in g if c not in hb and c not in gridfont.LATIN1 and c not in gridfont.CEDILLA),
      "Bold: every smeared glyph one column wider than Regular")
check(all(gridfont.counters(gb[c][2]) >= gridfont.counters(g[c][2]) for c in g if c not in hb),
      "Bold: no counter filled outside the hand file")
check(all("##" in "".join(gb[ord(ch)][2][4:9]) for ch in "nmhulbdpq"), "Bold: 2 px stems")
for ch in "aeoBR8":
    check(gridfont.counters(gb[ord(ch)][2]) == gridfont.counters(g[ord(ch)][2]), f"Bold {ch}: its counters stay open")
mb = gridfont.compose({c: gb[c][2] for c in gb if c not in gridfont.LATIN1 and c not in gridfont.CEDILLA}, 13)
check(all(gb[c][2] == mb[c] for c in mb) and len(mb) == 53, "Bold: the accented letters made from the bold letters")
check(gb[0x22][2][1] == ".##.##." and gb[0xA8][2][1] == ".##.##.", "Bold: \" and ¨ keep their two marks apart")
for ch in "$¢ªº¼¾ð":
    check(ord(ch) in hb, f"Bold {ch!r} drawn by hand")

# GFOS Mono 13 px (Lisette, 14 Nov): every character 8 wide
check(gridfont.fit([".#.", "##."]) == ["...#....", "..##...."], "fit: ink centred in columns 0-6")
check(gridfont.fit(["########"]) is None, "fit: 8 columns of ink don't fit")
out = subprocess.run([sys.executable, "tools/gridfont.py", "mono", "src/gfos-sans-13.txt", "src/gfos-mono-13-hand.txt",
                      "GFOS Mono 13"], capture_output=True, text=True)
check(out.returncode == 0 and out.stdout == open("src/gfos-mono-13.txt", encoding="utf-8").read(),
      "src/gfos-mono-13.txt is the mono, as committed")
gm, sm, am = gridfont.read("src/gfos-mono-13.txt")
hm = gridfont.read_hand("src/gfos-mono-13-hand.txt")
check(sm == 13 and am == 10 and sorted(gm) == sorted(g), "Mono 13: ascent 10, the same 191 characters as Sans")
check({w for w, _, _ in gm.values()} == {8} and all(len(r) == 13 for _, _, r in gm.values()), "Mono: every glyph 8 wide, 13 rows")
check(all(all(row[7] == "." for row in gm[c][2]) for c in gm if c != ord("_")), "Mono: column 7 clear, the gap")
check(gridfont.check("src/gfos-mono-13.txt") == 0, "Mono: 1 px stems, no blobs")
for ch in "%&@MWmw©®¼½¾ÆÐæijlIfrt":
    check(ord(ch) in hm, f"Mono {ch!r} drawn by hand")
check("#" in gm[ord("f")][2][0] and "#" not in gm[ord("t")][2][0] and gm[ord("t")][2][9].count("#") > 1,
      "Mono: f has its hook, t its foot")
mm = gridfont.compose({c: gm[c][2] for c in gm if c not in gridfont.LATIN1 and c not in gridfont.CEDILLA}, 13)
check(all(gm[c][2] == mm[c] for c in mm) and len(mm) == 53, "Mono: the accented letters made from the mono letters")

# the specimen draws
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "s.png")
    gridfont.specimen(p, [("A", "src/dejavu-sans-13-today.txt"), ("B", "src/gfos-sans-13.txt")])
    check(os.path.getsize(p) > 1000, "a specimen PNG is written")

print(f"test_gridfont: {oks + fails} checks, {fails} failed")
sys.exit(1 if fails else 0)
