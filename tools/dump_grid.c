/* dump_grid: a TrueType face drawn at one size exactly as GFOS draws it today
 * (diskfont.library's outline path through bullet.library, gfopenfont
 * library/textfont), written out as editable pixel grids.
 *
 *   dump_grid FONT.ttf YSIZE > glyphs.txt
 *
 * Rules copied from diskfont_core.cpp engine_open and bullet_core.cpp
 * glyph_map: 72 x 72 DPI and no OT_YSizeFactor, so the em is YSIZE pixels;
 * GFOpenFont's coverage, a pixel set at 128 and over; no hinting; the advance
 * rnd(adv * ppem / upm); under 15 pixels to the em a glyph with no room on its
 * right advances one more; the descent kept whole and the ascent the rest of
 * YSIZE, a glyph taller than that moved down to fit.
 *
 * Output (src/README.md has the format): a header, then per character
 *   char U+006E n
 *   width 7
 * and YSIZE rows of '.' and '#', 'width' columns each, the baseline after
 * row 'ascent'. Characters 32-126 and 160-255 (ISO-Latin-1; 127-159 are
 * controls). */
#include "gfopenfont/gfopenfont.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libgen.h>

typedef struct { int has, adv, left, top, w, h; unsigned char *px; } G;

static long rnd(long long a, long long b) { return (long)((a >= 0 ? a + b / 2 : a - b / 2) / b); }

int main(int argc, char **argv)
{
    if (argc != 3) { fprintf(stderr, "usage: dump_grid FONT.ttf YSIZE\n"); return 2; }
    int ys = atoi(argv[2]);
    OFContext *ctx = of_context_create();
    OFFace *face = ctx ? of_face_open(ctx, argv[1]) : NULL;
    OFFaceInfo info;
    if (!face || of_face_info(face, &info) != OF_OK || ys < 4 || ys > 64) { fprintf(stderr, "dump_grid: can't open %s\n", argv[1]); return 1; }
    const long long ppx = (long long)ys << 16, upm = info.units_per_em;
    const int32_t m[4] = { (int32_t)ppx, 0, 0, (int32_t)ppx };
    static G g[256];
    int top = 0, bottom = 0;
    for (int c = 32; c < 256; c++) {
        if (c >= 127 && c < 160) continue;
        uint32_t gi = of_face_char_index(face, (uint32_t)c);
        if (!gi) continue;
        OFBitmap b;
        memset(&b, 0, sizeof b);
        if (of_raster_glyph_matrix_a8(face, gi, m, &b) != OF_OK) continue;
        /* the set pixels' box, x from the origin, y up (row r's bottom edge at top - 1 - r) */
        int bl = 0, br = -1, bb = 0, bt = -1, any = 0;
        for (uint32_t r = 0; r < b.height; r++)
            for (uint32_t x = 0; x < b.width; x++)
                if (b.pixels[r * b.stride + x] >= 128) {
                    int pc = b.left + (int)x, pr = b.top - 1 - (int)r;
                    if (!any) { bl = br = pc; bb = bt = pr; any = 1; }
                    if (pc < bl) bl = pc;
                    if (pc > br) br = pc;
                    if (pr < bb) bb = pr;
                    if (pr > bt) bt = pr;
                }
        int32_t adv = of_face_glyph_advance(face, gi);
        int a = (int)rnd(rnd((long long)(adv > 0 ? adv : 0) * ppx, upm * 1024), 64);
        G *e = &g[c];
        e->has = 1; e->adv = a;
        if (any) {
            e->left = bl; e->top = bt + 1; e->w = br - bl + 1; e->h = bt - bb + 1;
            e->px = calloc((size_t)(e->w * e->h), 1);
            for (uint32_t r = 0; r < b.height; r++)
                for (uint32_t x = 0; x < b.width; x++)
                    if (b.pixels[r * b.stride + x] >= 128) {
                        int pc = b.left + (int)x - bl, pr = bt - (b.top - 1 - (int)r);
                        e->px[pr * e->w + pc] = 1;
                    }
            if (e->top > top) top = e->top;
            if (e->h - e->top > bottom) bottom = e->h - e->top;
            if (ys < 15) { int rb = e->adv - e->left - e->w; if (rb <= 0) e->adv++; }
        }
        of_bitmap_release(&b);
    }
    int ascent = top;
    if (ascent + bottom > ys) ascent = ys - bottom;
    if (ascent < 1) ascent = 1;
    printf("# %s at %d px (YSize %d, 72 dpi): today's GFOS render, diskfont/bullet rules\n", basename(argv[1]), ys, ys);
    printf("size %d\nascent %d\n\n", ys, ascent);
    for (int c = 32; c < 256; c++) {
        G *e = &g[c];
        if (!e->has) continue;
        /* the cell: columns from min(0, left) to max(adv, left + w); x 0 the origin */
        int x0 = e->px && e->left < 0 ? e->left : 0, x1 = e->adv;
        if (e->px && e->left + e->w > x1) x1 = e->left + e->w;
        int dy = e->px && e->top > ascent ? e->top - ascent : 0;   /* taller than the ascent: moved down */
        if (c < 128) printf("char U+%04X %c\n", c, c == ' ' ? '_' : c);
        else printf("char U+%04X %c%c\n", c, 0xC0 | (c >> 6), 0x80 | (c & 0x3F));
        printf("width %d\n", e->adv);
        if (x0) printf("origin %d\n", -x0);
        for (int row = 0; row < ys; row++) {
            int y = ascent - 1 - row + dy;          /* the pixel row's y above the baseline */
            for (int x = x0; x < x1; x++) {
                int on = 0;
                if (e->px) {
                    int pc = x - e->left, pr = e->top - 1 - y;
                    on = pc >= 0 && pc < e->w && pr >= 0 && pr < e->h && e->px[pr * e->w + pc];
                }
                putchar(on ? '#' : '.');
            }
            putchar('\n');
        }
        putchar('\n');
    }
    return 0;
}
