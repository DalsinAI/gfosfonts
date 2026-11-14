# GFOS gadget images

The window gadgets, arrows, checkmark, radio button, Amiga key and the menu's sub-item mark that Intuition's
`sysiclass` draws, as pen grids (DISPLAY-PROFILES section 2.3). One folder per set, one file per image.

| set | profiles | box | pixels |
| --- | --- | --- | --- |
| `lores` | 1 (PAL/NTSC lores) | 7 x 7 | square |
| `hires12` | 2 (hires, super-hires laced) | 14 x 7 | twice as tall as wide: the lores drawing with every column twice |
| `medres` | 3, 4, 5 (laced, RTG) | 11 x 11 | square |
| `large` | 6 (RTG large) | 15 x 15 | square |

A file is `image NAME`, `size W H`, then H rows of W pens. Lines that start with `# ` are notes.

- `.` clear: the gadget's own background shows through (the title bar's bands, the window's grey)
- `#` the glyph pen: BARDETAILPEN on the title bar, TEXTPEN on the window and in menus
- `o` the back pen: a filled face over what is behind it (the depth gadget's front window)

Pens, not colours, so the images follow the theme and the blue glass title bar. The set gives the drawing and the
profile gives the gadget's size; the glyph box sits centred in the gadget.

`tools/sysimages.py check` checks every set; `tools/sysimages.py specimen OUT.png` draws today's glyphs (drawn in
code by `oi_look_glyph`, amicradle-guest `libraries/openintuition/look_core.c`) beside these, on the title bar and
the window, at 1x and 4x. Nothing here is in the ROM: the sets load from disk (DISPLAY-PROFILES step 3).
