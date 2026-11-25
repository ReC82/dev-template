#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# node directement (pas `npm start`) : le PID suivi par check-contract.sh et le superviseur est
# alors celui du serveur ; arrêter npm laisserait un serveur node orphelin.
exec node server.js
