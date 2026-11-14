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

# the specimen draws
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "s.png")
    gridfont.specimen(p, [("A", "src/dejavu-sans-13-today.txt"), ("B", "src/gfos-sans-13.txt")])
    check(os.path.getsize(p) > 1000, "a specimen PNG is written")

print(f"test_gridfont: {oks + fails} checks, {fails} failed")
sys.exit(1 if fails else 0)
