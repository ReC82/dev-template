# __PROJECT_NAME__

Projet `__GITHUB_REPO__`, créé le __INIT_DATE__ depuis `dev-template` (stack `__STACK__`).
Piloté par ChatGPT, développé par Claude Code, livré par l'orchestrateur `__ORCH_NAME__`.

## Démarrer

```
bash scripts/check-contract.sh                       # porte locale (identique à la CI)
HOST=127.0.0.1 PORT=__PROJECT_PORT__ APP_DATA_DIR=./data bash scripts/start.sh
curl http://127.0.0.1:__PROJECT_PORT__/healthz       # {"ok": true, "commit": "…"}
```

## Où en est le projet ?

L'état fait foi dans GitHub : issue « État du projet (tableau de bord) », issues et PR ouvertes.
Reprise dans une nouvelle conversation ChatGPT : [START_HERE.md](START_HERE.md) § 8.

## Documents

| Fichier | Contenu |
|---|---|
| [PROJECT_GUIDE.md](PROJECT_GUIDE.md) | Règles produit (à lire avant tout ticket) |
| [AGENTS.md](AGENTS.md) | Règles des sessions de développement |
| [START_HERE.md](START_HERE.md) | Manuel de pilotage pour ChatGPT |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture du projet |
| [docs/NEW_PROJECT_CHECKLIST.md](docs/NEW_PROJECT_CHECKLIST.md) | Checklist de lancement |
| [docs/ORCHESTRATOR.md](docs/ORCHESTRATOR.md) | Orchestrateur `__ORCH_NAME__` |
| [docs/EMAIL_REPORTS.md](docs/EMAIL_REPORTS.md) | Notifications e-mail |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Déploiement, retour arrière |
| [docs/SECURITY.md](docs/SECURITY.md) | Sécurité, secrets, coûts |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) · [docs/RECOVERY.md](docs/RECOVERY.md) | Exploitation, reprise |
