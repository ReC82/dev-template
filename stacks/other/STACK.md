# Stack « autre » — contrat à implémenter

Le noyau n'impose aucune technologie. Pour une autre stack (Go, PHP, Rust, Java, mobile…), la
première issue du projet doit livrer ces deux scripts, appelés par la CI et l'orchestrateur :

| Script | Rôle |
|---|---|
| `scripts/gate.sh` | installer les dépendances (verrouillées), lint, tests, build ; code ≠ 0 si échec |
| `scripts/start.sh` | démarrer l'application sur `$HOST:$PORT`, données sous `$APP_DATA_DIR` |

et respecter `GET /healthz` → `{"ok": true, "commit": "<contenu de REVISION>"}`.
Tant qu'ils ne sont pas écrits, `scripts/check-contract.sh` échoue volontairement.
