# Orchestrateur du projet

L'orchestrateur est le **seul acteur qui travaille quand personne n'est connecté**. ChatGPT ne
tourne pas en arrière-plan ; le propriétaire n'est pas toujours là. Chaque projet a **son propre**
orchestrateur : utilisateur système, clone Git dédié, dossier d'état, service ou session tmux, et
jeton GitHub limité à son dépôt. Il ne lit ni ne pilote jamais un autre projet.

Implémentation de référence : `orchestrator/orch.py` (Python 3, bibliothèque standard ; outils
externes `git`, `gh`, `claude`). Elle peut être remplacée par un orchestrateur plus riche tant que
ce document (cycle, états, e-mails, plafonds) reste vrai.

## Cycle (une passe toutes les `POLL_SECONDS`)

1. **Drapeaux** : fichier `STOP` ou `PAUSE` dans `ORCH_STATE_DIR` → aucun nouveau ticket.
2. **File d'e-mails** : renvoi des notifications en attente (`notify.py flush`).
3. **Reprise** : un ticket resté `RUNNING` (arrêt machine, crash, délai) → e-mail **RESUMED**
   (dédupliqué), puis relance sur la **même branche**.
4. **Livraison** (seulement si `AUTO_MERGE=1`) : pour chaque PR prête dont la porte est verte :
   fusion squash → `DEPLOY_CMD` → `scripts/smoke-test.sh PUBLIC_URL SHA` → **DEPLOYED** et ticket
   fermé avec `status:deployed` ; sinon **FAILED/BLOCKED**, ticket ouvert.
5. **Sélection** : issues ouvertes `agent:auto`, sans `agent:blocked` ni `agent:human`, triées
   `priority:P0` → `P2` puis par numéro ; dépendances non livrées ignorées.
6. **Plafond** : au-delà de `MAX_SESSIONS_PER_DAY` sessions sur la journée (UTC), attente.
7. **Prise en charge** : label `agent:in-progress`, commentaire, e-mail **START** (avant Claude).
8. **Session** : worktree `WORKTREES_DIR/ticket-<n>` sur `agent/<n>-<slug>`, prompt
   `orchestrator/session-prompt.md`, délai `SESSION_TIMEOUT_MINUTES`, journal dans `logs/`.
9. **Rapport** de la session (JSON) :

| Statut rendu | Action de l'orchestrateur | E-mail |
|---|---|---|
| `WAITING_OWNER` + PR | porte locale `GATE_CMD` dans le worktree ; verte → attente fusion | **PR_READY** |
| `WAITING_OWNER`, porte rouge | relance avec le diagnostic (au plus `MAX_ATTEMPTS`) puis échec | FAILED au dernier essai |
| `BLOCKED` | label `agent:blocked` | **BLOCKED** (questions) |
| `READY` + `deps` | attend la livraison des dépendances | — |
| `RUNNING` | reprise au cycle suivant | — |
| absent / illisible / autre | relance jusqu'à `MAX_ATTEMPTS`, puis label `agent:blocked` | **FAILED** |

Relance après blocage : le propriétaire répond dans le ticket et **retire `agent:blocked`**.

## États d'un ticket

`READY` → `RUNNING` → `WAITING_OWNER` → (`AUTO_MERGE`) → `DONE` ; ou `BLOCKED` / `FAILED`.
**`DONE` = fusionné + déployé + `/healthz` public au SHA fusionné + smoke OK.** Un projet sans
déploiement configuré reste `BLOCKED` après fusion, avec le message « fusionné mais aucun déploiement
configuré » : jamais de faux DONE.

## Commandes

```
python3 orchestrator/orch.py --env /etc/<orch>/orch.env status    # état JSON (tickets, e-mails)
python3 orchestrator/orch.py --env … cycle                         # une passe
python3 orchestrator/orch.py --env … pause | resume | stop
python3 orchestrator/orch.py --env … ship <n>                      # livraison manuelle d'un ticket prêt
python3 orchestrator/notify.py status | flush | test
```

## Installation

`scripts/prepare-orchestrator.sh --orch NOM --repo OWNER/REPO --out DIR` **prépare** l'unité systemd
durcie, le lanceur tmux, `orch.env` (sans secret) et `INSTALL.md` (commandes root à faire exécuter
par le propriétaire). Rien n'est installé par le script. Configuration : `config/orchestrator.env.example`.

## Plafonds et coûts

| Variable | Défaut | Effet |
|---|---|---|
| `MAX_SESSIONS_PER_DAY` | 6 | limite le coût Claude et la charge machine |
| `SESSION_TIMEOUT_MINUTES` | 120 | une session bloquée est arrêtée puis reprise |
| `MAX_ATTEMPTS` | 2 | au-delà : FAILED + `agent:blocked` |
| `AUTO_MERGE` | 0 | fusion/déploiement automatiques **uniquement** sur accord écrit du propriétaire |
| `MemoryMax` (unité) | 1G | protège les autres services de la machine |

## Garde-fous recommandés pour les sessions

Un crochet `PreToolUse` de Claude Code (fichier de réglages de l'utilisateur de l'orchestrateur)
refuse : `sudo`, `git push` vers `main`, `--force`, `gh pr merge`, modification des labels, lecture
des fichiers de secrets, accès aux dossiers des autres projets. Le prompt de session rappelle ces
interdits ; le crochet les fait respecter.
