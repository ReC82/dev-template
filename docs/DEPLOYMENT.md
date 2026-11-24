# Déploiement

## Contrat universel (toutes stacks)

| Élément | Exigence |
|---|---|
| Porte | `scripts/gate.sh` (installation verrouillée, lint, tests, build) ; `scripts/check-contract.sh` l'enchaîne avec un démarrage d'essai |
| Démarrage | `scripts/start.sh` écoute `$HOST:$PORT` (défaut `127.0.0.1`, derrière un proxy TLS) |
| Santé | `GET /healthz` → `{"ok": true, "commit": "<contenu du fichier REVISION>"}` |
| Données | uniquement sous `$APP_DATA_DIR` ; jamais dans le dossier du code |
| Configuration | variables d'environnement ; secrets en fichiers 0600 hors dépôt (`docs/SECURITY.md`) |
| Smoke | `config/smoke.txt` (chemin, texte attendu) vérifié par `scripts/smoke-test.sh URL SHA` |

## Chaîne de livraison

```
PR verte → fusion squash → DEPLOY_CMD (avec DEPLOY_SHA) → smoke-test.sh PUBLIC_URL SHA → DEPLOYED
                                           └─ échec → retour arrière automatique → FAILED
```

`DEPLOY_CMD` est propre au profil d'hébergement ci-dessous. Il est exécuté **sur le serveur** par
l'orchestrateur, jamais par GitHub Actions.

## Profils d'hébergement (adaptables)

### Profil A — serveur Linux avec systemd et un proxy TLS (ex. VM chez un hébergeur, instance EC2)

- Utilisateur système dédié au projet ; code en lecture seule dans `/srv/<slug>/releases/<sha>` ;
  lien `/srv/<slug>/current` ; données dans `/var/lib/<slug>` (0700).
- Unité systemd durcie (`NoNewPrivileges`, `ProtectSystem=strict`, `ReadWritePaths` limité aux
  données, `MemoryMax`), écoute `127.0.0.1:<port>`.
- Proxy (nginx, Caddy…) : vhost dédié, `server_name` exact, HTTP → HTTPS, certificat Let's Encrypt,
  limitation de débit sur les API ; **aucun autre vhost modifié**, configuration testée avant rechargement.
- Bascule : `scripts/release-switch.sh <sha>` (sauvegarde → lien → redémarrage → `/healthz` = SHA,
  sinon version **et** données précédentes rétablies). Le redémarrage demande root : soit une
  unité `.path` déclenchée par un fichier que l'orchestrateur écrit (root n'exécute alors aucun code
  de la version), soit une règle `sudoers` limitée à `systemctl restart <slug>` — **décision du propriétaire**.
- Installation initiale (utilisateur, dossiers, unité, vhost, certificat) : **une fois, par root**,
  via une issue `agent:human` avec les commandes exactes.

### Profil B — site statique

`scripts/gate.sh` construit `dist/` (dont `dist/healthz`). Déploiement : copie atomique de `dist/`
vers le dossier servi (`rsync` vers un dossier versionné + lien), ou hébergement statique (GitHub
Pages, etc. — choix et coût à valider). Smoke identique.

### Profil C — plateforme gérée (PaaS, conteneurs)

Possible si le propriétaire l'accepte (coût, données hors serveur). `DEPLOY_CMD` appelle l'outil de
la plateforme ; les secrets restent dans la plateforme ; le smoke public reste obligatoire.

## DNS et TLS

1. **Humain** : créer l'enregistrement `A`/`AAAA` (ou `CNAME`) chez le registraire ; vérifier que
   l'adresse IP du serveur est fixe.
2. Vérification (lecture seule) : `dig +short <domaine>` = IP du serveur.
3. **Humain (root)** : vhost + certificat ; vérification `curl -sSI https://<domaine>/healthz`.

## Retour arrière

- Code : `scripts/release-switch.sh <sha_précédent>`, ou revert + chaîne normale.
- Données : restauration de la sauvegarde d'avant bascule (`docs/RECOVERY.md`). Les migrations
  sont additives pour que le code précédent fonctionne sur la base migrée.
