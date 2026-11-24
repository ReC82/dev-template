#!/usr/bin/env bash
# Vérifie les prérequis (lecture seule, idempotent). Usage : scripts/check-prereqs.sh [dev|server] [stack]
# Code de sortie 1 si un outil OBLIGATOIRE manque. N'affiche jamais de jeton.
set -uo pipefail
role="${1:-dev}"; stack="${2:-}"
if [ -z "$stack" ] && [ -f .devtemplate/project.env ]; then stack="$(sed -n 's/^STACK=//p' .devtemplate/project.env)"; fi
missing=0
check() { # check <obligatoire|facultatif> <commande> <rôle>
  if command -v "$2" >/dev/null 2>&1; then printf '✓ %-10s %s\n' "$2" "$("$2" --version 2>/dev/null | head -n1)"
  elif [ "$1" = obligatoire ]; then printf '✗ %-10s manquant (%s)\n' "$2" "$3"; missing=1
  else printf '· %-10s absent (facultatif : %s)\n' "$2" "$3"; fi
}
check obligatoire git "versionnement"
check obligatoire python3 "scripts et orchestrateur (bibliothèque standard)"
check obligatoire curl "smoke tests"
check obligatoire gh "GitHub CLI : labels, issues, PR"
case "$stack" in
  node) check obligatoire node "stack Node"; check obligatoire npm "stack Node";;
  python|static) ;;
esac
if [ "$role" = server ]; then
  check obligatoire claude "Claude Code (sessions de développement)"
  check facultatif tmux "console de l'orchestrateur"
  check facultatif systemctl "service supervisé"
fi
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then echo "✓ gh authentifié"; else echo "✗ gh non authentifié : « gh auth login » (action humaine)"; missing=1; fi
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || { echo "✗ Python >= 3.10 requis"; missing=1; }
exit "$missing"
