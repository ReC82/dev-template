# Reprise après incident

Principe : **stabiliser, prouver, puis corriger**. Toute action root ou destructive est une issue
`agent:human` avec commande, vérification et retour arrière.

## Le site ne répond plus ou sert une mauvaise version

1. `curl -fsS https://<domaine>/healthz` et `systemctl status <slug>`.
2. Version précédente : `RELEASES_DIR=… CURRENT_LINK=… RESTART_CMD=… HEALTH_URL=… scripts/release-switch.sh <sha_précédent>`.
3. Ouvrir une issue `type:bug` `priority:P0` avec les constats ; l'orchestrateur corrige par PR.

## Données corrompues ou perdues

1. Arrêter le service (root).
2. Tester l'archive **avant** de restaurer : `scripts/restore-test.sh <archive>`.
3. Restaurer : extraire l'archive dans un dossier neuf, l'échanger avec `$APP_DATA_DIR` (garder
   l'ancien dossier, renommé), redémarrer, vérifier `/healthz` et le smoke.
4. Noter dans l'issue : archive utilisée, période de données perdue, vérifications.

## Orchestrateur interrompu (redémarrage machine, crash)

Rien à faire en général : au redémarrage, le ticket `RUNNING` est repris sur sa branche et un
e-mail `RESUMED` (un seul) est envoyé. Si une session tourne en boucle : `orch.py pause`, lire
`logs/session-<id>.log`, commenter le ticket, `orch.py resume`.

## Ticket bloqué ou en échec

Lire les questions numérotées du ticket, répondre **dans le ticket**, retirer `agent:blocked`.
Après `FAILED`, préciser le ticket (critères, découpage) avant de le relancer.

## Secret exposé

1. **Révoquer/renouveler immédiatement** chez l'émetteur (GitHub, SMTP, fournisseur).
2. Remplacer le fichier secret sur le serveur, redémarrer le service concerné.
3. Retirer le secret du dépôt par une PR (l'historique Git le conserve : la révocation est ce qui protège).
4. Vérifier les journaux d'accès de l'émetteur ; consigner l'incident dans une issue.

## Perte du chat ChatGPT

Aucune conséquence : l'état est dans GitHub. Nouvelle conversation + prompt de reprise
(`docs/CHATGPT_PROJECT_SETUP.md` § 4).
