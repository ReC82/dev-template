# Modèles spécialisés (profils) construits sur ce noyau

GitHub ne permet pas d'hériter d'un modèle de dépôt : un dépôt créé depuis un modèle en est une
**copie** sans lien. Un modèle spécialisé (par exemple pour une famille de jeux web ou de sites
d'une même marque) se construit donc par **composition versionnée** :

1. Le noyau publie des versions étiquetées (`v0.1.0`, …) ; sa version est dans `.devtemplate/TEMPLATE_VERSION`.
2. Le modèle spécialisé est un dépôt modèle distinct qui contient une **copie** du noyau à une
   version donnée, plus sa couche propre. Il note la version du noyau dans le même fichier.
3. Fichiers **du noyau** (modifiés seulement en amont, puis resynchronisés) : `orchestrator/`,
   `scripts/` (hors scripts ajoutés par le profil), `docs/ORCHESTRATOR.md`, `docs/EMAIL_REPORTS.md`,
   `docs/GITHUB_WORKFLOW.md`, `docs/SECURITY.md`, `docs/RECOVERY.md`, `.github/workflows/ci.yml`.
4. Fichiers **du profil** : règles produit supplémentaires (ajoutées à `PROJECT_GUIDE.md` et
   `AGENTS.md` dans une section « Profil »), squelette applicatif, documents propres
   (ex. intégration d'identité, règles de gameplay), labels supplémentaires dans `config/labels.tsv`.
5. **Mise à jour** : une PR du modèle spécialisé « Synchroniser le noyau vX.Y.Z » recopie les
   fichiers du noyau, relance tous les tests et met à jour `.devtemplate/TEMPLATE_VERSION`. Les
   projets déjà créés font de même, par une issue dédiée, s'ils veulent la nouveauté.

Règle : le noyau ne connaît aucun profil. Une règle utile à tous les profils remonte dans le noyau.
