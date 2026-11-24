# Test à blanc n° 2 — « Site web de support audiovisuel avec logo »

Simulation de ce que ChatGPT produit en suivant `START_HERE.md`, **sans créer de dépôt ni déployer**.
Les réponses du propriétaire sont des hypothèses plausibles, marquées _(hypothèse)_.

## Brief (`plan/brief.md`)

| Question (§ 2) | Réponse |
|---|---|
| Nom, présentation, public | « Studio Support AV » : prestations de captation vidéo, régie, location de matériel et assistance technique pour événements ; entreprises et associations locales _(hypothèse)_ |
| Langues | fr, en |
| MVP | Accueil, Services, Réalisations (galerie), Contact ; mentions légales |
| Hors périmètre | réservation en ligne, paiement, espace client |
| Type | site vitrine → stack statique |
| Comptes / données / paiement | aucun ; contact par mailto/téléphone recommandé (aucune donnée stockée) |
| Dépôt | `OWNER/support-av`, public _(hypothèse)_ |
| Domaine / serveur | `support-av.example.org` ; hébergement statique sur le serveur existant _(hypothèse)_ |
| Identité visuelle | **logo à créer** avec ChatGPT (piste IA validée par le propriétaire, puis SVG propre) |
| Budget | 0 € hors domaine |
| E-mails | adresse du propriétaire ; relais SMTP local _(hypothèse)_ |
| Autorisations | déploiement automatique accepté (site sans données) _(hypothèse)_ |

## Architecture et stack (`plan/architecture.md`)

- **Stack `static`** : HTML/CSS/JS sans framework, `public/` → `dist/` par `scripts/gate.sh`,
  `dist/healthz` portant le SHA. Images WebP redimensionnées, chargement différé.
- Hébergement : profil B de `docs/DEPLOYMENT.md` (copie atomique de `dist/`, vhost + certificat).
- Aucune ressource tierce (polices locales, pas de carte ni de vidéo embarquée sans décision).

## Identité visuelle (`docs/BRANDING.md`)

1. Brief : sérieux, technique, chaleureux ; couleurs évoquant la lumière de scène ; doit rester
   lisible en monochrome sur un flight case _(hypothèse)_.
2. Trois pistes générées par IA présentées dans l'issue 3 (`agent:human`) ; le propriétaire choisit.
3. Issue 4 (`agent:auto`) : SVG redessiné, mono, inverse, favicon, apple-touch-icon, og-image,
   jetons de couleur, `BRAND_ASSETS.md` listant **créé / placeholder** pour chaque élément.
4. Tant que l'issue 4 n'est pas livrée, le site garde le favicon PLACEHOLDER du modèle.

## Issues (`issues.json`, 9 + tableau de bord)

| # | Titre | Label | Phase |
|---|---|---|---|
| 1 | Initialiser le projet (stack static, fr/en) | auto P0 | cadrage |
| 2 | Notifications e-mail testées (six évènements) | auto P0 | cadrage |
| 3 | Brief d'identité visuelle et trois pistes de logo | **humain** P1 | cadrage |
| 4 | Intégrer le logo validé, favicon et palette | auto P1 | MVP |
| 5 | Pages Accueil, Services, Réalisations, Contact | auto P1 | MVP |
| 6 | Décider du formulaire de contact | **humain** P1 | MVP |
| 7 | Mentions légales et confidentialité | auto P2 | MVP |
| 8 | Hébergement statique et DNS | **humain** P1 | lancement |
| 9 | Premier déploiement et smoke public | auto P1 | lancement |

Validation : `python3 scripts/github_bootstrap.py --repo OWNER/support-av --offline --dashboard --plan examples/dry-runs/audiovisual-support/issues.json`
→ 18 labels, 10 issues à créer, 0 erreur (vérifié par les tests du modèle).

## Gestes humains, dans l'ordre

1. Créer le dépôt ; 2. installer l'orchestrateur et valider l'e-mail de test ; 3. choisir une piste
de logo (issue 3) ; 4. décider du contact (issue 6) ; 5. DNS + vhost (issue 8) ; 6. fournir les
informations légales (issue 7).

## Mesure

Jusqu'au site en ligne : 9 tickets dont 3 humains, environ 7 à 9 sessions Claude.
