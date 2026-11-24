# Notifications e-mail (obligatoires)

Les e-mails sont le canal par lequel le propriétaire sait ce qui se passe **sans ouvrir ChatGPT ni
GitHub**. Ils font partie du socle : un projet issu de ce modèle n'est pas « lancé » tant que
l'e-mail de test, puis START et le rapport final d'un vrai ticket, ne sont pas arrivés.
Implémentation : `orchestrator/notify.py` (Python, bibliothèque standard).

## Évènements

| Évènement | Quand | Contenu obligatoire (refusé s'il manque) |
|---|---|---|
| `START` | dès qu'un ticket est accepté, **avant** de lancer Claude | numéro, URL, titre, priorité, projet, orchestrateur, session, date, plan succinct |
| `PR_READY` | PR ouverte et porte locale verte | PR, SHA, synthèse, tests locaux/CI ; mention « pas encore en ligne » |
| `DEPLOYED` | **seulement** après fusion + déploiement + `/healthz` public = SHA + smoke | PR, SHA, URL publique, résultat healthz, tests, changements, comment vérifier |
| `BLOCKED` | décision ou action humaine nécessaire | raison exacte, action attendue (questions) |
| `FAILED` | échec après les tentatives autorisées, ou déploiement/smoke en échec | raison, preuve expurgée (chemin du journal), nombre de tentatives |
| `RESUMED` | reprise d'une session interrompue | raison ; **un seul** e-mail par interruption et par fenêtre de `NOTIFY_RESUME_DEDUP_HOURS` |

Objet : `[<projet>][<ÉVÈNEMENT>] #<n> <titre>`. Jamais de secret ni de donnée personnelle
d'utilisateur : le texte passe par `redact()` (valeurs des variables sensibles, jetons usuels,
`password=…`, identifiants dans les URL, clés privées) avant d'être mis en file.

## Fiabilité

- **File sur disque** (`<état>/notify/outbox/`) : le message est écrit avant l'envoi ; une panne
  SMTP ne le perd pas.
- **Retries bornés** : `NOTIFY_MAX_RETRIES` essais par passage (délai exponentiel
  `NOTIFY_BACKOFF_SECONDS`), puis renvoi à chaque cycle de l'orchestrateur jusqu'à
  `NOTIFY_MAX_ATTEMPTS` au total ; ensuite état `dead`, visible dans `notify.py status`.
- **Déduplication** : clé `évènement:ticket:clé` (SHA, session…) ; un START n'est jamais envoyé deux fois.
- **Observabilité** : `<état>/notify/notify.log` (JSONL : horodatage, évènement, ticket, résultat,
  tentative, destinataire masqué `o***@e***`) ; `notify.py status` → envoyés, en attente, morts,
  problèmes de configuration.

## Configuration (hors Git)

Dans `/etc/<orch>/orch.env` (modèle `config/orchestrator.env.example`) :

| Variable | Rôle |
|---|---|
| `NOTIFY_TRANSPORT` | `file` (factice : `.eml` écrits sur disque, défaut et tests), `smtp` (réel), `none` (désactivé ; signalé par `status`) |
| `NOTIFY_TO`, `NOTIFY_FROM` | destinataire(s) séparés par des virgules ; expéditeur d'un domaine autorisé (SPF/DKIM) |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY` | relais ; `starttls` (587), `ssl` (465) ou `none` réservé à `127.0.0.1` |
| `SMTP_USER`, `SMTP_PASSWORD_FILE` | identifiant ; le mot de passe est **un fichier** 0600, jamais une variable ni le dépôt |

**Réutiliser un relais existant** : si la machine a déjà un relais SMTP local (ex. Postfix en
écoute sur `127.0.0.1:25` qui signe en DKIM), utiliser `SMTP_HOST=127.0.0.1`, `SMTP_PORT=25`,
`SMTP_SECURITY=none`, sans identifiant, avec l'accord du propriétaire. Sinon, un fournisseur SMTP
transactionnel (coût à valider) ou la boîte du propriétaire avec un mot de passe d'application.

## Tests

- Automatiques (aucun envoi réel) : transport `file`, et un **faux serveur SMTP local** pour le
  transport `smtp` ; échec SMTP → message en file, essais bornés, puis `dead`.
- Au bootstrap du projet : `python3 orchestrator/notify.py test` doit livrer un e-mail réel au
  propriétaire (critère bloquant de `docs/NEW_PROJECT_CHECKLIST.md`).
