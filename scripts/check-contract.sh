#!/usr/bin/env bash
# Porte locale universelle (CI et orchestrateur) : porte de la stack puis démarrage d'essai et /healthz.
# Usage : scripts/check-contract.sh [PORT]   (port d'essai, défaut : libre choisi automatiquement)
set -euo pipefail
cd "$(dirname "$0")/.."
# Dépôt modèle pas encore initialisé (le dépôt dev-template lui-même, ou « Use this template » avant
# scripts/init_project.py) : pas de porte de stack à lancer. On vérifie la structure, puis que chaque
# stack s'initialise proprement dans une copie temporaire. La CI du modèle reste ainsi verte.
if [ ! -e .devtemplate/project.env ] && [ -d stacks ]; then
  python3 scripts/check_repo.py
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT
  for stack in node python static other; do
    mkdir "$work/$stack"
    tar --exclude=./.git --exclude=./node_modules -cf - . | tar -xf - -C "$work/$stack"
    python3 "$work/$stack/scripts/init_project.py" --name "Essai $stack" --slug "essai-$stack" \
      --repo "owner/essai-$stack" --stack "$stack" > "$work/$stack.log" 2>&1 \
      || { cat "$work/$stack.log"; echo "✗ initialisation de la stack $stack impossible"; exit 1; }
    python3 "$work/$stack/scripts/check_repo.py" "$work/$stack" > /dev/null \
      || { echo "✗ stack $stack : dépôt initialisé non conforme"; exit 1; }
    [ -x "$work/$stack/scripts/gate.sh" ] || { echo "✗ stack $stack : scripts/gate.sh absent"; exit 1; }
    echo "✓ stack $stack : initialisation conforme"
  done
  echo "✓ modèle non initialisé : structure et initialisation vérifiées (lancer scripts/init_project.py pour la porte complète)"
  exit 0
fi
[ -x scripts/gate.sh ] || { echo "✗ scripts/gate.sh absent : lancer d'abord scripts/init_project.py"; exit 1; }
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
