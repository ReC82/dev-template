#!/usr/bin/env bash
# Porte de la stack Python : contrôle syntaxique puis tests (unittest, bibliothèque standard).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m py_compile app.py
python3 -m unittest discover -s tests -v
