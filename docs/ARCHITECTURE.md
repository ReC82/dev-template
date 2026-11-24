# Architecture — __PROJECT_NAME__

_À compléter lors de l'issue d'initialisation à partir de `plan/architecture.md`._

## Vue d'ensemble

| Composant | Technologie | Rôle |
|---|---|---|
| Application | `__STACK__` | sert l'interface et `/healthz` sur `$HOST:$PORT` |
| Données | sous `$APP_DATA_DIR` | _à préciser (fichiers, SQLite, autre)_ |
| Hébergement | profil de `docs/DEPLOYMENT.md` | _à préciser_ |

## Données et confidentialité

_Quelles données, pourquoi, durée de conservation, export, suppression._

## Langues et interface

Langues `__LOCALES__` ; fichiers `public/i18n/<code>.json` ; mobile d'abord.

## Dépendances

_Chaque dépendance avec sa justification._
