# Choisir une stack

Le noyau n'impose aucune technologie. `scripts/init_project.py --stack <profil>` copie un squelette
qui respecte le contrat universel (`docs/DEPLOYMENT.md`) puis retire les autres profils.

| Profil | Pour | Contenu copié | Porte (`scripts/gate.sh`) |
|---|---|---|---|
| `static` | site vitrine, documentation, page d'atterrissage | `public/` | JSON i18n valides, construction de `dist/` + `dist/healthz` |
| `node` | application web, API, jeu web (Node 22, bibliothèque standard d'abord) | `server.js`, `package.json` + lockfile, `tests/*.spec.js`, `public/` | `npm ci`, lint, `npm test`, build |
| `python` | application web, API, traitements (Python 3 bibliothèque standard d'abord) | `app.py`, `tests/test_*.py`, `public/` | `py_compile`, `unittest` |
| `other` | toute autre technologie (Go, PHP, Rust, Java, mobile…) | `STACK.md` + scripts qui échouent volontairement | à écrire dans la première issue |

Critères de choix (à écrire dans `plan/architecture.md`) : besoin fonctionnel, compétences de
maintenance du propriétaire, coût et simplicité d'exploitation, mémoire disponible sur le serveur.
Une base de données ? Commencer par des fichiers ou SQLite sous `$APP_DATA_DIR` ; un serveur de base
séparé est une décision (coût, sauvegarde, exploitation).

## Commun aux profils web

- **Responsive, mobile d'abord** : `public/styles.css` (360 px, cibles ≥ 44 px, focus visible,
  thème sombre, `prefers-reduced-motion`).
- **i18n configurable** : `--locales fr,en` (première = défaut) → `<html data-locales>` ; un fichier
  `public/i18n/<code>.json` par langue ; `public/app.js` choisit `?lang=` > choix mémorisé > langue
  du navigateur > défaut. Ajouter une langue = ajouter son JSON et l'inscrire dans `data-locales`.
- **Sécurité** : en-têtes de `docs/SECURITY.md`, aucun script en ligne, aucune ressource tierce.
- **Placeholders visuels** : `docs/BRANDING.md`.

## Changer de stack plus tard

Remplacer `scripts/gate.sh` et `scripts/start.sh` dans une PR dédiée, garder `/healthz` et
`$APP_DATA_DIR` : la CI et l'orchestrateur n'ont rien à changer.
