#!/bin/sh
# gfosfonts' tests. GFOPENFONT=<gfopenfont checkout> also rebuilds dump_grid against it and checks
# that today's render (src/dejavu-sans-13-today.txt) is what it dumps from DEJAVU (DejaVuSans.ttf 2.37).
set -e
cd "$(dirname "$0")/.."
python3 tests/test_gridfont.py
if [ -n "$GFOPENFONT" ]; then
    T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
    cmake -S "$GFOPENFONT" -B "$T/of" -DCMAKE_BUILD_TYPE=Release >/dev/null && make -C "$T/of" -j4 openfont >/dev/null
    cc -std=gnu11 -O2 -Wall -Werror -I"$GFOPENFONT/include" tools/dump_grid.c "$T/of/libopenfont.a" -lm -o "$T/dump_grid"
    "$T/dump_grid" "${DEJAVU:-/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf}" 13 > "$T/d13.txt"
    cmp "$T/d13.txt" src/dejavu-sans-13-today.txt && echo "dump_grid: today's 13 px render unchanged"
fi
