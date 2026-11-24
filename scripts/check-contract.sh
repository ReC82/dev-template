#!/usr/bin/env bash
# Porte locale universelle (CI et orchestrateur) : porte de la stack puis démarrage d'essai et /healthz.
# Usage : scripts/check-contract.sh [PORT]   (port d'essai, défaut : libre choisi automatiquement)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -x scripts/gate.sh ] || { echo "✗ scripts/gate.sh absent : lancer d'abord scripts/init-project.sh"; exit 1; }
python3 scripts/check_repo.py
bash scripts/gate.sh
port="${1:-$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')}"
data="$(mktemp -d)"
git rev-parse HEAD > REVISION 2>/dev/null || echo dev > REVISION
HOST=127.0.0.1 PORT="$port" APP_DATA_DIR="$data" bash scripts/start.sh > "$data/start.log" 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; rm -rf "$data"' EXIT
for _ in $(seq 1 50); do curl -fsS "http://127.0.0.1:$port/healthz" >/dev/null 2>&1 && break; sleep 0.2; done
bash scripts/smoke-test.sh "http://127.0.0.1:$port" "$(cat REVISION)" config/smoke.txt || { cat "$data/start.log"; exit 1; }
echo "✓ contrat respecté"
