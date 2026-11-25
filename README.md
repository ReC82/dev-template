# dev-template — démarrer un projet piloté par ChatGPT et développé par Claude Code

Modèle de dépôt **universel** (aucune technologie, aucun hébergeur, aucun produit imposés) pour
créer un projet logiciel de A à Z avec quatre acteurs aux rôles séparés :

- **le propriétaire** décide et valide ce qui est sensible ;
- **ChatGPT** pilote (brief, plan, issues GitHub, suivi, tests fonctionnels) pendant les conversations ;
- **Claude Code** développe (code, tests, PR) ;
- **un orchestrateur serveur dédié** travaille entre les conversations (issues `agent:auto` →
  sessions Claude → porte locale → fusion/déploiement si autorisé) et envoie les e-mails de suivi.

## Démarrer depuis un nouveau Projet ChatGPT

**→ [CHATGPT_START_PROMPT.md](CHATGPT_START_PROMPT.md) : le prompt de démarrage, un seul bloc à copier.**

1. Créer un Projet ChatGPT et coller ce bloc dans ses **instructions** (ou comme premier message) ;
   joindre `START_HERE.md` et les documents listés (pas à pas : [docs/CHATGPT_PROJECT_SETUP.md](docs/CHATGPT_PROJECT_SETUP.md)).
2. ChatGPT lit le modèle, dit ce que ses outils lui permettent, puis demande
   « Quel projet souhaitez-vous créer ? » et cadre le projet par petites questions.
3. Il suit ensuite [START_HERE.md](START_HERE.md) jusqu'au projet livré et testable.

## Prérequis

| Où | Quoi |
|---|---|
| Poste ou serveur de développement | `git`, `gh` (authentifié), `python3` ≥ 3.10, `curl` ; Node 22 si stack `node` |
| Serveur de l'orchestrateur | les mêmes + Claude Code (`claude`) connecté ; `systemd` ou `tmux` ; un relais SMTP |
| Comptes | GitHub (droit de créer un dépôt), ChatGPT avec Projets, Claude Code |

`scripts/check-prereqs.sh dev|server` vérifie tout cela sans rien modifier.

## Contenu

| Chemin | Rôle |
|---|---|
| [CHATGPT_START_PROMPT.md](CHATGPT_START_PROMPT.md) | Prompt de démarrage ChatGPT A→Z, prêt à copier |
| [START_HERE.md](START_HERE.md) | Manuel complet pour ChatGPT : brief, stack, dépôt, issues, orchestrateur, suivi, reprise |
| [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md) | Règles de toute session de développement |
| [PROJECT_GUIDE.md](PROJECT_GUIDE.md) | Règles produit du projet (rempli à l'initialisation) |
| [docs/CHATGPT_PROJECT_SETUP.md](docs/CHATGPT_PROJECT_SETUP.md) | Instructions et fichiers du Projet ChatGPT, prompts copiables |
| [docs/NEW_PROJECT_CHECKLIST.md](docs/NEW_PROJECT_CHECKLIST.md) | Checklist de lancement : GitHub → orchestrateur → infra → DNS/TLS → tests → déploiement |
| [docs/ORCHESTRATOR.md](docs/ORCHESTRATOR.md) | Orchestrateur de référence (`orchestrator/`), cycle, états, plafonds |
| [docs/EMAIL_REPORTS.md](docs/EMAIL_REPORTS.md) | E-mails START / PR READY / DEPLOYED / BLOCKED / FAILED / REPRISE (obligatoires) |
| [docs/GITHUB_WORKFLOW.md](docs/GITHUB_WORKFLOW.md) | Labels, format des issues et du plan, PR, CI, protection de branche, tableau de bord |
| [docs/STACKS.md](docs/STACKS.md) | Choix de stack : Node, Python, statique, autre ; i18n et responsive |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Contrat universel, profils d'hébergement, bascule et retour arrière |
| [docs/SECURITY.md](docs/SECURITY.md) | Secrets hors dépôt, isolation des projets, coûts plafonnés, règles applicatives |
| [docs/BRANDING.md](docs/BRANDING.md) | Identité visuelle facultative : logo IA après brief, favicon, couleurs |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Exploitation courante, sauvegardes, diagnostic |
| [docs/RECOVERY.md](docs/RECOVERY.md) | Reprise après incident, restauration, retour arrière |
| [docs/PROFILES.md](docs/PROFILES.md) | Construire un modèle spécialisé (profil) au-dessus de ce noyau |
| `scripts/` | Initialisation, GitHub, prérequis, orchestrateur, smoke, état, sauvegarde |
| `orchestrator/` | Orchestrateur de référence et notifications e-mail (Python, bibliothèque standard) |
| `stacks/` | Squelettes Node / Python / statique / autre (retirés après initialisation) |
| `.github/` | Modèles d'issues et de PR, CI, smoke planifié |
| `examples/dry-runs/` | Deux plans complets produits à blanc (jeu web, site vitrine avec logo) |

## Essai local en cinq minutes

```
gh repo create OWNER/essai --template OWNER/dev-template --private --clone && cd essai
python3 scripts/init_project.py --name "Essai" --slug essai --repo OWNER/essai --stack python
bash scripts/check-contract.sh            # porte locale : tests + démarrage + /healthz
```

Version du modèle : `.devtemplate/TEMPLATE_VERSION`. Licence : à choisir par le propriétaire.
