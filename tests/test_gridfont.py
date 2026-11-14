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

# the specimen draws
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "s.png")
    gridfont.specimen(p, [("A", "src/dejavu-sans-13-today.txt"), ("B", "src/gfos-sans-13.txt")])
    check(os.path.getsize(p) > 1000, "a specimen PNG is written")

print(f"test_gridfont: {oks + fails} checks, {fails} failed")
sys.exit(1 if fails else 0)
