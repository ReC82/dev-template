# Créer et configurer le Projet ChatGPT

Un « Projet » ChatGPT regroupe des conversations, des instructions et des fichiers. Il sert de
**poste de pilotage** ; la source de vérité reste le dépôt GitHub et ses issues.

## 1. Création

1. ChatGPT → *Projets* → *Nouveau projet*, nommé comme le futur dépôt (ex. `mon-projet`).
2. Si disponible, activer le **connecteur GitHub** et lui donner accès au dépôt modèle
   <https://github.com/ReC82/dev-template> et au futur dépôt du projet (lecture au minimum). Vérifier ce
   qu'il permet réellement (lecture, recherche, création d'issues) : les capacités varient selon
   l'offre et évoluent ; `START_HERE.md` § 1 couvre les deux cas.
3. **Joindre les documents** : *Projet → Fichiers → Ajouter*, téléverser `START_HERE.md`,
   `CHATGPT_START_PROMPT.md`, `docs/CHATGPT_PROJECT_SETUP.md`, `docs/NEW_PROJECT_CHECKLIST.md`,
   `docs/GITHUB_WORKFLOW.md`, `docs/EMAIL_REPORTS.md`, `docs/STACKS.md` (téléchargés depuis GitHub :
   bouton *Download raw file*, ou `git clone` du modèle). Indispensables si le connecteur GitHub est
   absent ou en lecture partielle. Ces copies peuvent vieillir : les instructions demandent de relire
   GitHub en priorité, et de redemander les fichiers manquants plutôt que de les inventer.

## 2. Instructions du projet (où coller le prompt)

*Projet → icône ⋯ ou « Instructions » → Personnaliser / Instructions du projet* : coller **tel quel**
le bloc de [CHATGPT_START_PROMPT.md](../CHATGPT_START_PROMPT.md) § « Bloc à copier » (tout le contenu
entre les trois accents graves), puis enregistrer. Ces instructions s'appliquent à **chaque**
conversation du Projet : c'est ce qui permet de repartir de zéro à tout moment.

Si l'interface limite la longueur des instructions : y coller seulement le bloc court ci-dessous et
joindre `CHATGPT_START_PROMPT.md` aux fichiers du Projet.

```
Tu es le chef de projet de ce projet logiciel. Ton prompt de démarrage complet est
CHATGPT_START_PROMPT.md et ton manuel START_HERE.md du modèle https://github.com/ReC82/dev-template
(copies dans les fichiers du Projet). Applique-les intégralement. Règles essentielles :
1. Au début de chaque conversation, relis l'état réel dans GitHub (README, PROJECT_GUIDE.md, issue
   « État du projet (tableau de bord) », issues et PR ouvertes). Ne te fie pas à ta mémoire.
2. Dis clairement ce que tes outils te permettent (lire / écrire dans GitHub). N'affirme jamais
   qu'une action est faite sans l'avoir vue réussir (lien, SHA, URL).
3. Tu n'es pas un service permanent : le travail entre deux conversations est fait par
   l'orchestrateur dédié du serveur (e-mails START, PR READY, DEPLOYED, BLOCKED, FAILED, REPRISE).
4. Claude Code écrit le code via les issues `agent:auto`. Toi, tu cadres par petites questions avec
   des valeurs par défaut, découpes, rédiges les issues (Objectif, Périmètre, Critères d'acceptation,
   Hors périmètre, Dépendances), suis et expliques les tests au propriétaire.
5. Demande confirmation avant : création de dépôt, fusion/déploiement automatiques, root, DNS,
   secrets, opérations destructrices, toute dépense. Ne demande jamais un secret dans le chat.
6. DONE = critères d'acceptation satisfaits : fusionné + déployé + /healthz public au bon SHA +
   smoke OK. Sinon, donne le statut exact.
```

## 3. Prompt initial copiable (première conversation)

Instructions du Projet en place : écrire simplement

```
Démarrons. Lis le modèle, fais ton diagnostic, puis demande-moi quel projet je veux créer.
```

Sans instructions de Projet (conversation ordinaire) : coller comme premier message le bloc complet
de [CHATGPT_START_PROMPT.md](../CHATGPT_START_PROMPT.md).

## 4. Prompt de reprise copiable (toute conversation suivante)

```
Reprends le projet OWNER/REPO (instructions du Projet et START_HERE.md § 8). Relis GitHub (tableau de bord, issues, PR, derniers commentaires),
puis résume : livré (URL, SHA), en cours, bloqué (questions), prochaine étape recommandée,
et ce que je dois tester ou décider aujourd'hui.
```

Relancer proprement : ouvrir une **nouvelle conversation dans le même Projet** (les instructions et
les fichiers y sont déjà) plutôt que de prolonger une conversation très longue ; si les fichiers
joints ont changé dans GitHub (nouvelle version du modèle ou du projet), les remplacer d'abord.

## 5. Ce qu'il ne faut pas attendre du Projet ChatGPT

- Il ne surveille rien quand la conversation est fermée ; les alertes viennent des e-mails de
  l'orchestrateur et de GitHub.
- Il n'a pas accès au serveur ni aux secrets ; il prépare des commandes, l'humain les exécute.
- Ses fichiers de projet sont des copies : en cas de divergence, GitHub a raison.
