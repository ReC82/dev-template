# Test à blanc n° 1 — « Mini Tower Defense »

Simulation de ce que ChatGPT produit en suivant `START_HERE.md`, **sans créer de dépôt ni déployer**.
Les réponses du propriétaire sont des hypothèses plausibles, marquées _(hypothèse)_.

## Brief (`plan/brief.md`)

| Question (§ 2) | Réponse |
|---|---|
| Nom, présentation, public | « Mini Tower Defense » : défense de tours en parties de 5 minutes, jouable sur téléphone ; joueurs occasionnels _(hypothèse)_ |
| Langues | fr, en |
| MVP | carte en grille avec chemin, 10 vagues, 3 tours améliorables, menus/pause/fin, meilleurs scores sans compte |
| Hors périmètre | comptes, monétisation, multijoueur, éditeur de cartes |
| Type | jeu web → serveur léger (scores) |
| Comptes / données / paiement | aucun compte ; pseudo + score seulement ; aucun paiement |
| Dépôt | `OWNER/mini-td`, public (protection de `main` gratuite) _(hypothèse)_ |
| Domaine / serveur | `td.example.org`, serveur Linux existant, port 8710 libre _(hypothèse)_ |
| Identité visuelle | placeholder au lancement ; logo plus tard |
| Budget | 0 € hors domaine |
| E-mails | adresse du propriétaire ; relais SMTP local existant _(hypothèse)_ |
| Autorisations | fusion et déploiement automatiques acceptés après le premier déploiement manuel _(hypothèse)_ |

## Architecture et stack (`plan/architecture.md`)

- **Stack `node`** : Canvas 2D et modules ES côté client sans bundler ; `server.js` sert les fichiers
  et une API `POST/GET /api/scores` ; SQLite (`node:sqlite`) sous `$APP_DATA_DIR`. Aucune dépendance.
- Simulation de jeu déterministe et séparée du rendu (testable par `node --test`).
- Scores : validation serveur (durée minimale, bornes, limitation de débit), pseudo seul.
- Hébergement : profil A de `docs/DEPLOYMENT.md` (unité systemd durcie, proxy TLS, `MemoryMax=300M`).
- Accessibilité : clavier, ≥ 44 px, contraste AA, mouvement réduit ; i18n `public/i18n/{fr,en}.json`.

## Issues (`issues.json`, 10 + tableau de bord)

| # | Titre | Label | Phase |
|---|---|---|---|
| 1 | Initialiser le projet (stack node, fr/en) | auto P0 | cadrage |
| 2 | Notifications e-mail testées (six évènements) | auto P0 | cadrage |
| 3 | Boucle de jeu Canvas 2D et grille | auto P1 | MVP |
| 4 | Vagues d'ennemis déterministes | auto P1 | MVP |
| 5 | Tours : placement, tir, amélioration | auto P1 | MVP |
| 6 | Interface : menus, pause, fin, fr/en, accessibilité | auto P1 | MVP |
| 7 | Meilleurs scores sans compte, validés côté serveur | auto P2 | MVP |
| 8 | Préparer l'hébergement : commandes root | **humain** P1 | lancement |
| 9 | DNS vers le serveur | **humain** P1 | lancement |
| 10 | Premier déploiement et smoke public | auto P1 | lancement |

Validation : `python3 scripts/github_bootstrap.py --repo OWNER/mini-td --offline --dashboard --plan examples/dry-runs/mini-tower-defense/issues.json`
→ 18 labels, 11 issues à créer, 0 erreur (vérifié par les tests du modèle).

## Gestes humains, dans l'ordre

1. Créer `OWNER/mini-td` depuis le modèle (droits GitHub).
2. Lancer `github_bootstrap.py … --apply` si le connecteur ChatGPT ne peut pas créer d'issues.
3. Installer l'orchestrateur (`orch-prep/INSTALL.md`, root), jeton GitHub limité, connexion Claude.
4. Fichier/relais SMTP, puis confirmer la réception de l'e-mail de test.
5. Issue 8 (root), issue 9 (registraire DNS).
6. Autoriser `AUTO_MERGE=1` après le premier déploiement réussi.

## Mesure

Temps estimé jusqu'au premier e-mail START : ~1 h de gestes humains (dépôt, orchestrateur, SMTP).
Jusqu'au MVP en ligne : 10 tickets, environ 10 à 14 sessions Claude (2 jours au plafond de 6/jour).
