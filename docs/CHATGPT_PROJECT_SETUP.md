# Créer et configurer le Projet ChatGPT

Un « Projet » ChatGPT regroupe des conversations, des instructions et des fichiers. Il sert de
**poste de pilotage** ; la source de vérité reste le dépôt GitHub et ses issues.

## 1. Création

1. ChatGPT → *Projets* → *Nouveau projet*, nommé comme le dépôt (ex. `mon-projet`).
2. Si disponible, activer le **connecteur GitHub** et lui donner accès au dépôt `dev-template` et au
   futur dépôt du projet (lecture au minimum). Vérifier ce qu'il permet réellement (lecture, recherche,
   création d'issues) : les capacités varient selon l'offre et évoluent ; `START_HERE.md` § 1 couvre
   les deux cas.
3. Ajouter aux **fichiers du projet** : `START_HERE.md`, `docs/CHATGPT_PROJECT_SETUP.md`,
   `docs/NEW_PROJECT_CHECKLIST.md`, `docs/GITHUB_WORKFLOW.md`, `docs/STACKS.md`. Ces copies peuvent
   vieillir : les instructions ci-dessous demandent de relire GitHub en priorité.

## 2. Instructions du projet (à coller telles quelles)

```
Tu es le chef de projet de ce projet logiciel. Ton manuel est START_HERE.md du dépôt modèle
dev-template (et sa copie dans les fichiers du projet). Règles :
1. Au début de chaque conversation, relis l'état réel dans GitHub (README, PROJECT_GUIDE.md, issue
   « État du projet (tableau de bord) », issues et PR ouvertes). Ne te fie pas à ta mémoire.
2. Dis clairement ce que tes outils te permettent (lire / écrire dans GitHub). N'affirme jamais
   qu'une action est faite sans l'avoir vue réussir (lien, SHA, URL).
3. Tu n'es pas un service permanent : le travail entre deux conversations est fait par
   l'orchestrateur du serveur (e-mails START, PR READY, DEPLOYED, BLOCKED, FAILED, REPRISE).
4. Claude Code écrit le code via les issues `agent:auto`. Toi, tu cadres, découpes, rédiges les
   issues (Objectif, Périmètre, Critères d'acceptation, Hors périmètre, Dépendances), suis et
   expliques les tests au propriétaire.
5. Demande confirmation avant : création de dépôt, fusion/déploiement automatiques, root, DNS,
   secrets, toute dépense. Ne demande jamais un secret dans le chat.
6. DONE = fusionné + déployé + /healthz public au bon SHA + smoke OK. Sinon, donne le statut exact.
```

## 3. Prompt initial copiable (première conversation)

```
Base-toi sur START_HERE.md du dépôt OWNER/dev-template pour créer mon nouveau projet.
Commence par me dire ce que tes outils GitHub te permettent, puis pose-moi en un seul message
les questions du brief (avec tes recommandations par défaut). Ensuite : architecture et stack,
plan/brief.md, plan/architecture.md, plan/issues.json (issue n° 1 = initialisation, puis e-mails,
CI, MVP, lancement), et la liste ordonnée de ce que je dois faire moi-même.
Mon idée : <décrire le projet en quelques phrases>.
```

## 4. Prompt de reprise copiable (toute conversation suivante)

```
Reprends le projet OWNER/REPO. Relis GitHub (tableau de bord, issues, PR, derniers commentaires),
puis résume : livré (URL, SHA), en cours, bloqué (questions), prochaine étape recommandée,
et ce que je dois tester ou décider aujourd'hui.
```

## 5. Ce qu'il ne faut pas attendre du Projet ChatGPT

- Il ne surveille rien quand la conversation est fermée ; les alertes viennent des e-mails de
  l'orchestrateur et de GitHub.
- Il n'a pas accès au serveur ni aux secrets ; il prépare des commandes, l'humain les exécute.
- Ses fichiers de projet sont des copies : en cas de divergence, GitHub a raison.
