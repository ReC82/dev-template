#!/usr/bin/env bash
# Test de restauration (à planifier, ex. mensuel) : vérifie l'empreinte, extrait dans un dossier
# temporaire, contrôle l'intégrité des bases SQLite et lance VERIFY_CMD (facultatif) avec
# APP_DATA_DIR pointant sur la copie. Ne touche JAMAIS aux données de production.
# Usage : scripts/restore-test.sh ARCHIVE [VERIFY_CMD]
set -euo pipefail
archive="${1:?ARCHIVE}"; verify="${2:-}"
{ [ -f "$archive" ] && [ -f "$archive.sha256" ]; } || { echo "✗ archive ou empreinte absente" >&2; exit 1; }
(cd "$(dirname "$archive")" && sha256sum -c --quiet "$(basename "$archive").sha256") || { echo "✗ empreinte invalide" >&2; exit 1; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
tar -C "$tmp" -xzf "$archive"
while IFS= read -r -d '' db; do
  python3 -c 'import sqlite3,sys; c=sqlite3.connect(f"file:{sys.argv[1]}?mode=ro",uri=True); sys.exit(0 if c.execute("PRAGMA integrity_check").fetchone()[0]=="ok" else 1)' "$db" \
    || { echo "✗ intégrité : ${db#"$tmp"/}" >&2; exit 1; }
done < <(find "$tmp" -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) -print0)
if [ -n "$verify" ]; then APP_DATA_DIR="$tmp" bash -c "$verify"; fi
echo "✓ restauration vérifiée : $(basename "$archive") ($(find "$tmp" -type f | wc -l) fichier(s))"
