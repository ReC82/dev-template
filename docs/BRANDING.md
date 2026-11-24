# Identité visuelle (facultative)

Le projet démarre avec des **placeholders** explicites (`public/favicon.svg` marqué « PLACEHOLDER »,
couleurs neutres de `public/styles.css`). Une identité réelle n'est créée que si le propriétaire le
demande, après un brief, et n'est intégrée qu'après sa validation.

## Parcours

1. **Brief** (ChatGPT) : valeurs, public, ton, 3 références aimées / détestées, contraintes
   (couleurs imposées, usage sur fond sombre, impression), déclinaisons nécessaires.
2. **Propositions** (ChatGPT avec génération d'images, si disponible) : 3 pistes de logo, chacune
   avec sa palette. Annoncer clairement qu'il s'agit d'images générées par IA ; vérifier
   l'absence de ressemblance avec une marque existante.
3. **Validation** du propriétaire : une piste choisie, écrite dans le ticket (décision).
4. **Production** (ticket `type:design` pour Claude) : version vectorielle SVG propre (redessinée,
   pas une image raster vectorisée automatiquement), déclinaisons, intégration.
5. **Contrôle** : contraste AA du texte sur les couleurs de marque, lisibilité à 16 px.

## Livrables et emplacement

| Fichier | Contenu |
|---|---|
| `public/brand/logo.svg`, `logo-mono.svg`, `logo-inverse.svg` | logo principal, monochrome, sur fond sombre |
| `public/favicon.svg`, `public/favicon-32.png`, `public/apple-touch-icon.png` (180 px) | icônes |
| `public/brand/og-image.png` (1200×630) | partage sur les réseaux |
| `public/styles.css` (`:root`) | jetons : `--brand`, `--brand-fg`, `--bg`, `--fg`, `--muted`, `--focus` |
| `BRAND_ASSETS.md` dans `docs/` (à créer) | tableau **créé / placeholder** pour chaque élément, source (IA, humain), date de validation |

## Règles

- Distinguer toujours, dans `BRAND_ASSETS.md` et dans la PR, un **asset validé** d'un **placeholder**.
- Aucune police ni image chargée depuis un service tiers : fichiers servis localement, licences notées.
- Aucun logo d'un tiers sans autorisation écrite.
