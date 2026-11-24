# PROJECT_GUIDE — __PROJECT_NAME__

Règles produit du projet. Rempli à partir de `plan/brief.md` lors de l'issue d'initialisation ;
à tenir à jour par le propriétaire (ou par ChatGPT avec son accord). Elles priment sur `AGENTS.md`.

## Produit

- Présentation en une phrase : _à compléter_
- Public visé : _à compléter_
- Fonctionnalités du MVP : _à compléter (3 à 7)_
- Hors périmètre : _à compléter_

## Paramètres

| Paramètre | Valeur |
|---|---|
| Dépôt | `__GITHUB_REPO__` |
| Stack | `__STACK__` (`docs/STACKS.md`) |
| Domaine | `__PROJECT_DOMAIN__` |
| Port local | `__PROJECT_PORT__` |
| Langues | `__LOCALES__` (défaut `__DEFAULT_LOCALE__`) |
| Orchestrateur | `__ORCH_NAME__` |

## Règles impératives

- **Données** : minimisation ; export et suppression prévus dès la conception si données personnelles.
- **Sécurité** : `docs/SECURITY.md` ; tests obligatoires pour chaque règle.
- **Interface** : mobile d'abord (360 px), langues ci-dessus, ≥ 44 px, contraste AA, clavier,
  `prefers-reduced-motion`.
- **Coûts** : aucun service payant ni API externe sans décision écrite du propriétaire et plafond chiffré.
- **Déploiement** : automatique seulement si le propriétaire l'a autorisé (`AUTO_MERGE`, `DEPLOY_CMD`).
- **E-mails** : START et rapport final obligatoires pour chaque ticket (`docs/EMAIL_REPORTS.md`).

## Décisions du propriétaire

| Date | Décision |
|---|---|
| __INIT_DATE__ | Création du projet depuis dev-template |
