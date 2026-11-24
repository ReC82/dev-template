#!/usr/bin/env bash
# Prévisualisation locale de dist/ (en production : serveur web statique, docs/DEPLOYMENT.md).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d dist ] || bash scripts/gate.sh
if [ -f REVISION ]; then printf '{"ok": true, "commit": "%s"}\n' "$(cat REVISION)" > dist/healthz; fi
exec python3 -m http.server "${PORT:-8080}" --bind "${HOST:-127.0.0.1}" --directory dist
