# GitHub : labels, issues, PR, CI et état du projet

GitHub est la **mémoire du projet** : ChatGPT, Claude, l'orchestrateur et le propriétaire y
lisent et y écrivent l'état réel. Rien d'important ne vit seulement dans une conversation.

## Labels (`config/labels.tsv`)

| Famille | Labels | Posé par |
|---|---|---|
| File | `agent:auto` (l'orchestrateur peut prendre), `agent:human` (action humaine) | ChatGPT / propriétaire |
| Suivi | `agent:in-progress`, `agent:blocked`, `status:merged`, `status:deployed` | orchestrateur |
| Contrôle | `agent:approved` (chemins protégés approuvés), `agent:no-merge` | propriétaire |
| Priorité | `priority:P0`, `priority:P1`, `priority:P2` | ChatGPT / propriétaire |
| Classement | `type:*`, `phase:*` | ChatGPT |

Création idempotente : `python3 scripts/github_bootstrap.py --repo OWNER/REPO` (simulation) puis `--apply`.

## Format d'une issue

Titre `[P1] Verbe + résultat` (≤ 120 caractères). Corps :

```
## Objectif
## Périmètre
## Critères d'acceptation      (cases à cocher, vérifiables par un test ou une URL)
## Hors périmètre
## Dépendances                 (« Dépend de #n » ou rien)
```

Les modèles `.github/ISSUE_TEMPLATE/` (fonctionnalité, anomalie, action humaine) l'imposent dans
l'interface. Une issue `agent:human` décrit la commande exacte, la vérification et le retour arrière.

## Plan versionné (`plan/issues.json`)

```json
{
  "project": "Nom",
  "milestones": ["Cadrage", "MVP", "Lancement"],
  "issues": [
    {"title": "[P0] Initialiser le projet", "labels": ["agent:auto", "priority:P0", "phase:cadrage"],
     "body": "## Objectif\n…\n## Critères d'acceptation\n- [ ] …"}
  ]
}
```

`github_bootstrap.py --plan plan/issues.json` valide le plan (sections, labels connus, priorité,
`agent:auto` et `agent:human` exclusifs, aucun secret) puis crée les issues absentes (titre exact).
Relancer ne crée aucun doublon. `--dashboard` crée en dernier l'issue « État du projet (tableau de
bord) ». Dans un dépôt neuf, les issues reçoivent les numéros 1, 2, 3… dans l'ordre du plan : les
mentions « Dépend de #n » d'un plan s'appuient sur cet ordre (à vérifier si le dépôt a déjà des issues).

## Branches et PR

- Branche `agent/<n>-<slug>` par ticket ; jamais de push sur `main`, jamais de `--force`.
- Une PR par ticket (`.github/PULL_REQUEST_TEMPLATE.md`), `Closes #n`, tests, risques, tests humains.
- Fusion **squash** par l'orchestrateur (`AUTO_MERGE=1`) ou par le propriétaire. Une PR qui touche
  `deploy/`, `infra/`, `ops/` ou `.github/` attend le label `agent:approved`.

## CI et protection de branche

- `.github/workflows/ci.yml` : la même porte que l'orchestrateur (`scripts/check-contract.sh`), sans
  secret, permissions en lecture. `live-smoke.yml` : smoke public planifié si la variable de dépôt
  `PUBLIC_URL` est définie (le certificat doit être valide plus de 14 jours).
- Protection de `main` (vérification `contract` obligatoire, pas de force push ni suppression) :
  `github_bootstrap.py --protect --apply`. GitHub la refuse sur un dépôt **privé en offre gratuite** :
  décision du propriétaire (rendre public, payer, ou s'en passer — la porte de l'orchestrateur reste).
- Le **déploiement n'est jamais fait par GitHub Actions** : aucune clé de serveur dans GitHub.

## État consultable

`python3 scripts/status_report.py --repo OWNER/REPO [--public-url URL] [--orch-state DIR] --update-issue N`
réécrit le corps de l'issue tableau de bord : tickets en cours, bloqués, en file, PR ouvertes,
derniers tickets fermés, `/healthz` public, état de l'orchestrateur. L'orchestrateur peut l'appeler
à chaque cycle (`DASHBOARD_ISSUE`) ; ChatGPT le lit au début de chaque conversation.

## Retour arrière d'une PR

`git revert <sha>` sur une branche, PR « Revert … (#n) », porte, fusion, déploiement : la même chaîne
que pour une évolution. Données : `docs/RECOVERY.md`.
