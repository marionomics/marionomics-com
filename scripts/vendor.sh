#!/usr/bin/env bash
# Download pinned third-party assets into static/. Re-run only to change versions.
set -euo pipefail
KATEX=0.16.22
PRISM=1.30.0
CMU=0.1.2
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fetch() { mkdir -p "$TMP/$1"; curl -fsSL "https://registry.npmjs.org/$1/-/$1-$2.tgz" | tar -xz -C "$TMP/$1"; }

fetch katex "$KATEX"
K="$TMP/katex/package"
rm -rf "$ROOT/static/vendor/katex"
mkdir -p "$ROOT/static/vendor/katex/contrib"
cp "$K/dist/katex.min.css" "$K/dist/katex.min.js" "$K/LICENSE" "$ROOT/static/vendor/katex/"
cp "$K/dist/contrib/auto-render.min.js" "$ROOT/static/vendor/katex/contrib/"
cp -R "$K/dist/fonts" "$ROOT/static/vendor/katex/fonts"

fetch prismjs "$PRISM"
P="$TMP/prismjs/package"
rm -rf "$ROOT/static/vendor/prism"
mkdir -p "$ROOT/static/vendor/prism"
for c in core markup clike javascript jsx python r bash latex markdown json; do
  cat "$P/components/prism-$c.min.js"
  echo
done > "$ROOT/static/vendor/prism/prism.js"
cp "$P/themes/prism.min.css" "$ROOT/static/vendor/prism/prism.min.css"
cp "$P/LICENSE" "$ROOT/static/vendor/prism/LICENSE"

fetch computer-modern "$CMU"
rm -rf "$ROOT/static/fonts/cmu"
mkdir -p "$ROOT/static/fonts/cmu"
for f in cmu-serif-500-roman cmu-serif-500-italic cmu-serif-700-roman cmu-serif-700-italic; do
  cp "$TMP/computer-modern/package/fonts/$f.woff2" "$ROOT/static/fonts/cmu/"
done
cat > "$ROOT/static/fonts/cmu/README.md" <<'TXT'
CMU Serif (Computer Modern Unicode), by Andrey V. Panov — SIL Open Font License 1.1.
woff2 files from the `computer-modern` npm package; version pinned in scripts/vendor.sh.
TXT

echo "Vendored KaTeX $KATEX, Prism $PRISM, CMU Serif (computer-modern $CMU)"
