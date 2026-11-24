# Sécurité, secrets, isolation et coûts

## Secrets : jamais dans le dépôt

- Aucun secret dans Git, les issues, les PR, les journaux, les e-mails ou une conversation ChatGPT.
- Sur le serveur : un fichier par secret, `0600`, propriétaire = utilisateur du service, sous
  `/etc/<projet>/` ; la configuration référence le **chemin** (`SMTP_PASSWORD_FILE=…`), jamais la valeur.
- Jetons GitHub : *fine-grained*, limités au dépôt du projet, droits minimum (issues, PR, contenu),
  expiration fixée ; rotation documentée dans une issue `agent:human`.
- `scripts/check_repo.py` (CI) refuse les motifs de jetons usuels, les clés privées, les fichiers
  `.env`/`*.pem` versionnés et toute valeur de secret dans un exemple de configuration.
- Fuite constatée : révoquer d'abord, nettoyer ensuite (`docs/RECOVERY.md`).

## Isolation stricte des projets

Chaque projet a son utilisateur système, son dossier de code, son dossier de données, son
orchestrateur, sa session tmux (nommée comme lui), ses jetons. Un orchestrateur ou une session
Claude ne lit jamais le dépôt, la base, les secrets, les journaux ou la session d'un autre projet.
Un crochet de garde des sessions fait respecter ces règles (`docs/ORCHESTRATOR.md`).

## Coûts et API plafonnés

| Poste | Règle |
|---|---|
| Sessions Claude | `MAX_SESSIONS_PER_DAY`, `SESSION_TIMEOUT_MINUTES`, `MAX_ATTEMPTS` |
| API externes payantes (IA, cartes, paiement…) | interdites sans décision écrite du propriétaire ; si acceptées : clé dédiée, **plafond de dépense configuré chez le fournisseur**, quota applicatif, alerte |
| Hébergement, domaine, e-mail | chiffrés dans le brief ; toute hausse = décision |
| Développement et tests | transports factices (e-mail, paiement, identité), aucun appel réseau externe |

## Règles applicatives (tests obligatoires pour chaque règle touchée)

- En-têtes : CSP stricte sans `unsafe-inline`, `frame-ancestors 'none'`, HSTS, `nosniff`,
  `Referrer-Policy`, `Cross-Origin-Opener-Policy`. Aucune ressource tierce par défaut.
- Entrées : taille maximale des corps, validation stricte (types, longueurs, listes blanches),
  erreurs sans écho des valeurs.
- Comptes (si le projet en a) : hachage scrypt/bcrypt/argon2 ; jetons aléatoires dont seul le hash
  est stocké ; cookies `HttpOnly; Secure; SameSite=Lax` (préfixe `__Host-`) ; CSRF sur toute
  écriture ; limitation de débit ; réponses identiques qu'un compte existe ou non ; e-mails factices
  en développement.
- Journaux : ni secret, ni mot de passe, ni jeton, ni adresse e-mail ou IP en clair.
- Données personnelles : minimisation, durée de conservation, export et suppression prévus.
- Dépendances : chacune justifiée ; Dependabot ; lockfile commité.
