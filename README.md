# GFOS Fonts

GFOS Sans and GFOS Mono: hand-corrected bitmap fonts for GFOS, derived from DejaVu.


GFOS's default fonts, drawn by hand pixel by pixel (Dale, 13 Nov 2026: "we should hand draw our
default fonts", "correcting these"). Decision: amicradle-teams `teams/DECISION-HANDDRAWN-FONTS-20261113-1954.md`.

Status: Dale approved the direction from the second sheet (14 Nov 04:36: "yes, go for it"). Third cut: Latin-1's accented letters, the letters with no plain base and most symbols. Nothing here is a default yet: Dale sees it on a real screen first.

![GFOS Sans 13 px against today's DejaVu Sans](specimens/gfos-sans-13-vs-dejavu.png)

## What is here
| File | What |
| --- | --- |
| `src/dejavu-sans-13-today.txt` | DejaVu Sans at 13 px exactly as GFOS draws it today (the `_ttf` font OpenBench uses), dumped by `tools/dump_grid` |
| `src/gfos-sans-13-hand.txt` | the characters drawn by hand: a-z, A-Z, 0-9, all the ASCII punctuation, and Latin-1's letters with no plain base and its symbols |
| `src/gfos-sans-13.txt` | GFOS Sans Regular 13 px: the hand set, and Latin-1's accented letters made from it (`compose`), over today's render (`gridfont.py merge`) |
| `specimens/gfos-sans-13-vs-dejavu.png`, `specimens/gfos-sans-13-latin1-20261114.png` | the specimen sheets: both faces, actual size and at 4x |
| `tools/dump_grid.c` | dumps a TrueType face as GFOS draws it, as editable grids |
| `tools/gridfont.py` | reads, checks, merges and draws the grids |
| `tools/amigafont.py` | builds the Amiga bitmap font from a grid: `amigafont.py build src/gfos-sans-13.txt GFOSSans OUT` writes `OUT/GFOSSans.font` and `OUT/GFOSSans/13` for FONTS: (build outputs stay out of git) |

## The grid format
Plain text, one file per face and size, so every change is a readable diff:

```
size 13
ascent 10

char U+006E n
width 7
.......
...      13 rows of '.' (clear) and '#' (set), 'width' columns;
...      the baseline is under row 'ascent' (rows 0-9 above it, 10-12 below)
```

A glyph that starts left of its origin has an `origin N` line (N columns before the origin).
Lines starting `# ` are comments. The hand file is simpler: the character on its own line,
then its 13 rows; its width is the rows' length. `#`, which would read as a comment, is named
`char U+0023` instead.

## Today's render, reproduced
`dump_grid FONT.ttf 13` follows GFOS's own path (gfopenfont `library/textfont`): diskfont at 72 x 72 dpi
with no `OT_YSizeFactor` (FONTS:DejaVuSans.otag has none, so the em is 13 px), bullet's coverage set at
128 and over with no hinting, the advance rounded, a pixel added after a glyph with no room on its
right under 15 px to the em, and the descent kept whole. The DejaVu Sans used is 2.37 (759,720 bytes,
the same size as FONTS:_ttf/DejaVuSans.ttf on Instance-32).

## Rules for the hand-drawn set (from the decision)
- Stems 1 px at the small sizes, the same in every letter.
- Round shoulders on n, m, h, a and d: a one-pixel diagonal step, never a 2x2 blob.
- f and t never alike: f has a hook at the top and no foot, t a foot and no hook.
- x-height 7 px (rows 3-9); capitals and figures 9 px (rows 1-9); figures all 7 wide.

`gridfont.py check` finds 2 px stems and 2x2 blobs in the hand set. Today's DejaVu render
has problems in the same characters (233 in the first 63 alone); GFOS Sans has none in its hand-drawn and composed characters.

## Tests
`tests/run.sh` (185 + 15 checks). With `GFOPENFONT=<gfopenfont checkout>` it also rebuilds `dump_grid`
and checks that today's render is unchanged.

## Next (Dale, 14 Nov 04:36: finish Latin-1, then the other sizes, Bold and Mono)
Latin-1 is complete ($80-$9F left empty). Bold, 11 and 16 px, GFOS Mono 8x16 and 10x20,
hires (1:2) cuts, then the build to Amiga diskfont `.font` files.

## Licences
- **The fonts** (GFOS Sans, GFOS Mono and anything else derived from DejaVu here) are under the Bitstream Vera licence, with DejaVu's changes in the public domain. See `LICENSE-FONTS`. That licence lets the glyphs be changed only if the changed fonts are renamed, so no font in this repository may have "Bitstream" or "Vera" in its name.
- **The tools** in this repository (converters, build and check scripts) are MIT. See `LICENSE-TOOLS`.

Designed, tested and delivered by The AmiCradle Team.
