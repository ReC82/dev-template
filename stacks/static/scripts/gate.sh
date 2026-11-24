#!/usr/bin/env bash
# Porte de la stack statique : HTML présent, JSON i18n valides, construction de dist/ avec /healthz.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f public/index.html ] || { echo "✗ public/index.html absent"; exit 1; }
for f in public/i18n/*.json; do python3 -m json.tool "$f" >/dev/null || { echo "✗ JSON invalide : $f"; exit 1; }; done
rm -rf dist && cp -a public dist
rev="$(git rev-parse HEAD 2>/dev/null || cat REVISION 2>/dev/null || echo dev)"
printf '{"ok": true, "commit": "%s"}\n' "$rev" > dist/healthz
echo "✓ dist/ construit"
