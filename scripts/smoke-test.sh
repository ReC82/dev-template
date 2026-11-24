#!/usr/bin/env bash
# Smoke test public ou local : /healthz = {"ok": true, "commit": <SHA attendu>} puis contrôles du fichier
# de smoke (une ligne « chemin<TAB>texte attendu », # = commentaire).
# Usage : scripts/smoke-test.sh BASE_URL [SHA_ATTENDU] [FICHIER_SMOKE]
set -euo pipefail
base="${1:?usage : smoke-test.sh BASE_URL [SHA] [FICHIER]}"; base="${base%/}"
sha="${2:-}"; file="${3:-}"
fail=0
health="$(curl -fsS --max-time 15 "$base/healthz")" || { echo "✗ $base/healthz injoignable"; exit 1; }
commit="$(printf '%s' "$health" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("ok") is True; print(d.get("commit",""))')" \
  || { echo "✗ /healthz ne rend pas {\"ok\": true, …}"; exit 1; }
if [ -n "$sha" ]; then
  if [ -z "$commit" ] || { [ "${commit#"$sha"}" = "$commit" ] && [ "${sha#"$commit"}" = "$sha" ]; }; then
    echo "✗ commit servi « $commit » ≠ attendu « $sha »"; exit 1
  fi
fi
echo "✓ /healthz ok (commit ${commit:0:12})"
if [ -n "$file" ] && [ -f "$file" ]; then
  while IFS=$'\t' read -r path expect || [ -n "${path:-}" ]; do
    case "$path" in ''|\#*) continue;; esac
    body="$(curl -fsS --max-time 15 "$base$path")" || { echo "✗ $path : erreur HTTP"; fail=1; continue; }
    if [ -n "${expect:-}" ] && ! printf '%s' "$body" | grep -qF -- "$expect"; then
      echo "✗ $path : « $expect » absent"; fail=1
    else
      echo "✓ $path"
    fi
  done < "$file"
fi
exit "$fail"
