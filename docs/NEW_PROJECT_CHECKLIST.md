# Checklist de lancement d'un nouveau projet

Ordre imposé : **GitHub → orchestrateur → infrastructure → DNS/TLS → tests → déploiement**.
Chaque ligne a un mode et une preuve à coller dans l'issue correspondante.

- **AUTO** — fait par ChatGPT (si son connecteur le permet), Claude ou l'orchestrateur, sans root ni secret.
- **HUMAIN** — propriétaire : droits GitHub, registraire DNS, root/`sudo`, secrets, dépenses.
- **VÉRIF** — contrôle en lecture seule ; la sortie est la preuve.

## 0. Cadrage

| # | Étape | Mode | Preuve |
|---|---|---|---|
| 0.1 | Brief complet (`START_HERE.md` § 2) dans `plan/brief.md` | AUTO (ChatGPT) | fichier |
| 0.2 | Stack et architecture choisies (`docs/STACKS.md`) dans `plan/architecture.md` | AUTO + validation HUMAIN | décision écrite |
| 0.3 | `plan/issues.json` valide : `github_bootstrap.py --offline --plan plan/issues.json` | VÉRIF | sortie « 0 erreur » |
| 0.4 | Budget mensuel plafond et autorisations (fusion/déploiement automatiques) | HUMAIN | décision écrite |

## 1. GitHub

| # | Étape | Mode | Preuve |
|---|---|---|---|
| 1.1 | Créer le dépôt depuis `dev-template` (« Use this template » ou `gh repo create OWNER/REPO --template OWNER/dev-template`) | HUMAIN | URL du dépôt |
| 1.2 | Labels, issues du plan et tableau de bord : `github_bootstrap.py --repo OWNER/REPO --plan plan/issues.json --dashboard --apply` | AUTO ou HUMAIN (mode B) | sortie ; relancer = « 0 à créer » |
| 1.3 | Protection de `main` : `github_bootstrap.py --repo OWNER/REPO --protect --apply` | HUMAIN | réglage visible, ou refus GitHub documenté |
| 1.4 | Issue n° 1 « Initialiser le projet » (`init_project.py`, `check-contract.sh` vert, CI verte) | AUTO (Claude, via l'orchestrateur ou manuellement) | PR fusionnée |

## 2. Orchestrateur

| # | Étape | Mode | Preuve |
|---|---|---|---|
| 2.1 | `scripts/check-prereqs.sh server <stack>` sur le serveur | VÉRIF | tout ✓ |
| 2.2 | `scripts/prepare-orchestrator.sh --orch NOM --repo OWNER/REPO --out ./orch-prep` | AUTO | fichiers générés |
| 2.3 | Exécuter `orch-prep/INSTALL.md` : utilisateur, dossiers, clone dédié, jeton GitHub limité, connexion Claude, service | HUMAIN (root) | `systemctl status NOM` |
| 2.4 | SMTP : fichier mot de passe 0600 ou relais local ; `NOTIFY_TRANSPORT=smtp` | HUMAIN | — |
| 2.5 | **E-mail de test reçu** : `notify.py test` | VÉRIF — **bloquant** | e-mail reçu |
| 2.6 | Poser `agent:auto` sur l'issue n° 1 : **e-mail START reçu** puis **PR READY** | VÉRIF — **bloquant** | e-mails reçus |

## 3. Infrastructure (si le projet est servi)

| # | Étape | Mode | Preuve |
|---|---|---|---|
| 3.1 | Profil d'hébergement choisi (`docs/DEPLOYMENT.md`) ; capacité machine et coût acceptés | HUMAIN | décision |
| 3.2 | Port local libre : `ss -ltn` ne le montre pas | VÉRIF | sortie |
| 3.3 | Utilisateur, dossiers releases/données, unité systemd, sauvegarde quotidienne | HUMAIN (root), via issue `agent:human` préparée par Claude | `systemctl status` |
| 3.4 | `DEPLOY_CMD`, `PUBLIC_URL` dans `orch.env` ; `AUTO_MERGE` selon décision 0.4 | HUMAIN | — |

## 4. DNS et TLS

| # | Étape | Mode | Preuve |
|---|---|---|---|
| 4.1 | Enregistrement DNS vers l'IP fixe du serveur | HUMAIN (registraire) | — |
| 4.2 | `dig +short <domaine>` = IP | VÉRIF | sortie |
| 4.3 | Vhost dédié + certificat (aucun autre vhost modifié) | HUMAIN (root) | `curl -sSI https://<domaine>/` |

## 5. Tests

| # | Étape | Mode | Preuve |
|---|---|---|---|
| 5.1 | CI verte sur `main` | VÉRIF | lien Actions |
| 5.2 | `scripts/restore-test.sh` sur la première sauvegarde | VÉRIF | sortie ✓ |
| 5.3 | Tests humains de la PR sur mobile (360 px) et ordinateur | HUMAIN | commentaire |

## 6. Déploiement

| # | Étape | Mode | Preuve |
|---|---|---|---|
| 6.1 | Premier déploiement (ticket de lancement) | AUTO (orchestrateur) ou HUMAIN | e-mail **DEPLOYED** |
| 6.2 | `scripts/smoke-test.sh https://<domaine> <sha> config/smoke.txt` | VÉRIF | sortie ✓ |
| 6.3 | Variable de dépôt `PUBLIC_URL` pour `live-smoke.yml` | HUMAIN | exécution verte |
| 6.4 | Tableau de bord à jour (`status_report.py --update-issue`) | AUTO | issue à jour |

Le projet est **lancé** quand 2.5, 2.6, 6.1 et 6.2 ont leur preuve. Sinon, donner le statut exact.
