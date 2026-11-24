#!/usr/bin/env bash
# Porte de la stack Node : exactement ce que lancent la CI et l'orchestrateur.
set -euo pipefail
cd "$(dirname "$0")/.."
npm ci
npm run --if-present lint
npm test
npm run --if-present build
