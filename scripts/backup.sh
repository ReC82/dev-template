#!/usr/bin/env bash
# Sauvegarde du dossier de données ($APP_DATA_DIR) : archive horodatée + empreinte SHA-256, rotation.
# Bases SQLite copiées de façon cohérente (API backup de sqlite3, Python) puis vérifiées.
# Usage : scripts/backup.sh DATA_DIR BACKUP_DIR [CONSERVER=14]
set -euo pipefail
data="${1:?DATA_DIR}"; dest="${2:?BACKUP_DIR}"; keep="${3:-14}"
[ -d "$data" ] || { echo "✗ $data absent" >&2; exit 1; }
mkdir -p "$dest"; chmod 700 "$dest"
stamp="$(date -u +%Y%m%dT%H%M%SZ)-$$"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
cp -a "$data/." "$work/"
while IFS= read -r -d '' db; do
  rel="${db#"$data"/}"
  rm -f "$work/$rel" "$work/$rel-wal" "$work/$rel-shm"
  python3 - "$db" "$work/$rel" <<'PY'
import sqlite3, sys
src = sqlite3.connect(f'file:{sys.argv[1]}?mode=ro', uri=True)
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
ok = dst.execute('PRAGMA integrity_check').fetchone()[0]
dst.close(); src.close()
sys.exit(0 if ok == 'ok' else 1)
PY
done < <(find "$data" -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) -print0)
archive="$dest/backup-$stamp.tar.gz"
tar -C "$work" -czf "$archive" .
(cd "$dest" && sha256sum "$(basename "$archive")" > "$(basename "$archive").sha256")
chmod 600 "$archive" "$archive.sha256"
# shellcheck disable=SC2012 # noms maîtrisés (backup-<horodatage>)
mapfile -t old < <(ls -1t "$dest"/backup-*.tar.gz 2>/dev/null | tail -n +"$((keep + 1))")
for f in "${old[@]}"; do rm -f "$f" "$f.sha256"; done
echo "✓ $archive"
