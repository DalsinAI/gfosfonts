#!/bin/sh
# GFOSFonts-<VERSION>.lha from a gfosfonts checkout: builds the three faces with its tools/amigafont.py (as
# gfopenup's GFOSFonts part does), lays them out as they go into FONTS:, and adds the specimens, both licences,
# ReadMe, Install and SHA256SUMS. It makes the archive only; publishing is separate.
#   release/make-lha.sh . [DIST]   (or any gfosfonts checkout)   VERSION=1.0 (default)
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SRC=$(CDPATH= cd -- "${1:?usage: make-lha.sh GFOSFONTS_CHECKOUT [DIST]}" && pwd)
DIST=${2:-"$HERE/dist"}
VERSION=${VERSION:-1.0}
NAME="GFOSFonts-$VERSION"
command -v lha >/dev/null || { echo "make-lha.sh: needs lha"; exit 2; }
STAGE=$(mktemp -d "${TMPDIR:-/tmp}/gfosfonts-lha.XXXXXX")
trap 'rm -rf "$STAGE"' EXIT INT TERM
R="$STAGE/$NAME"
mkdir -p "$R/Fonts" "$R/Specimens" "$DIST"
DIST=$(CDPATH= cd -- "$DIST" && pwd)
for f in gfos-sans:GFOSSans gfos-sans-bold:GFOSSansBold gfos-mono:GFOSMono; do
    s=${f%%:*}; n=${f##*:}
    python3 -I "$SRC/tools/amigafont.py" build "$SRC/src/$s-13.txt" "$n" "$R/Fonts" "$SRC/src/$s-11.txt" "$SRC/src/$s-16.txt"
done
cp "$SRC"/specimens/*.png "$R/Specimens/"
cp "$SRC/LICENSE-FONTS" "$SRC/LICENSE-TOOLS" "$HERE/ReadMe" "$HERE/Install" "$R/"
(cd "$R" && find . -type f ! -name SHA256SUMS | LC_ALL=C sort | sed 's|^\./||' | xargs -d '\n' sha256sum > SHA256SUMS)
# the same bytes from the same inputs: one date for every file, the commit's
find "$STAGE" -exec touch -h -d "@$(git -C "$SRC" show -s --format=%ct HEAD)" {} +
rm -f "$DIST/$NAME.lha"
(cd "$STAGE" && LC_ALL=C find "$NAME" -type f | LC_ALL=C sort | xargs -d '\n' lha -aq "$DIST/$NAME.lha")
echo "$DIST/$NAME.lha ($(wc -c < "$DIST/$NAME.lha") bytes) sha256 $(sha256sum "$DIST/$NAME.lha" | cut -d' ' -f1)"
echo "from gfosfonts $(git -C "$SRC" rev-parse HEAD)"
