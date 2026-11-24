#!/usr/bin/env bash
# Bascule de version avec retour arrière automatique (profil serveur « releases + lien current »).
#   RELEASES_DIR/<sha>/   versions extraites (lecture seule)      CURRENT_LINK -> RELEASES_DIR/<sha>
# Étapes : BACKUP_CMD → lien current → RESTART_CMD → /healthz = SHA attendu ;
# en cas d'échec : lien précédent rétabli, RESTORE_CMD (facultatif), RESTART_CMD, code 1.
# Usage : RELEASES_DIR=… CURRENT_LINK=… RESTART_CMD=… HEALTH_URL=… scripts/release-switch.sh SHA
set -euo pipefail
sha="${1:?SHA}"
: "${RELEASES_DIR:?}" "${CURRENT_LINK:?}" "${RESTART_CMD:?}" "${HEALTH_URL:?}"
[[ "$sha" =~ ^[0-9a-f]{7,40}$ ]] || { echo "✗ SHA invalide" >&2; exit 1; }
target="$RELEASES_DIR/$sha"
[ -d "$target" ] || { echo "✗ version absente : $target" >&2; exit 1; }
previous="$(readlink "$CURRENT_LINK" 2>/dev/null || true)"
if [ -n "${BACKUP_CMD:-}" ]; then bash -c "$BACKUP_CMD"; fi
ln -sfn "$target" "$CURRENT_LINK.new" && mv -T "$CURRENT_LINK.new" "$CURRENT_LINK"
bash -c "$RESTART_CMD"
served() { curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null | python3 -c '
import json, sys
d = json.load(sys.stdin); c = str(d.get("commit") or ""); s = sys.argv[1]
sys.exit(0 if d.get("ok") is True and c and (c.startswith(s) or s.startswith(c)) else 1)' "$sha"; }
for _ in $(seq 1 "${HEALTH_TRIES:-30}"); do
  if served; then echo "✓ $sha en service"; exit 0; fi
  sleep "${HEALTH_DELAY:-1}"
done
echo "✗ /healthz ne rend pas $sha : retour arrière" >&2
if [ -n "$previous" ]; then
  ln -sfn "$previous" "$CURRENT_LINK.new" && mv -T "$CURRENT_LINK.new" "$CURRENT_LINK"
  if [ -n "${RESTORE_CMD:-}" ]; then bash -c "$RESTORE_CMD"; fi
  bash -c "$RESTART_CMD"
  echo "↩ version précédente rétablie : $(basename "$previous")" >&2
fi
exit 1
