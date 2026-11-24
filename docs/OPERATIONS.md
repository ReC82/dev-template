# Exploitation courante

## Routines

| Fréquence | Quoi | Comment | Qui |
|---|---|---|---|
| À chaque déploiement | `/healthz` = SHA, smoke | orchestrateur (`scripts/smoke-test.sh`) | auto |
| Toutes les 6 h | smoke public + certificat > 14 jours | `.github/workflows/live-smoke.yml` | auto |
| Quotidienne | sauvegarde des données (14 conservées) | `scripts/backup.sh $APP_DATA_DIR /var/backups/<slug>` (timer) | auto |
| Avant chaque bascule | sauvegarde | `BACKUP_CMD` de `scripts/release-switch.sh` | auto |
| Mensuelle | **test de restauration** | `scripts/restore-test.sh <dernière archive> "<commande de vérification>"` | auto, résultat dans le tableau de bord |
| Hebdomadaire | relecture du tableau de bord, des e-mails `dead`, des PR en attente | `notify.py status`, issue tableau de bord | propriétaire / ChatGPT |

## Diagnostic (lecture seule)

```
curl -fsS https://<domaine>/healthz                                  # version servie
bash scripts/smoke-test.sh https://<domaine> "" config/smoke.txt     # parcours public
python3 orchestrator/orch.py --env /etc/<orch>/orch.env status       # tickets, e-mails
python3 orchestrator/notify.py status                                # file d'e-mails
systemctl status <slug> <orch> --no-pager                            # services
journalctl -u <orch> -n 100 --no-pager                               # journal orchestrateur
tail -n 50 <état>/logs/orch.log                                      # cycles
free -m; df -h                                                       # ressources
dig +short <domaine>                                                 # DNS
echo | openssl s_client -servername <domaine> -connect <domaine>:443 2>/dev/null | openssl x509 -noout -dates
```

## Symptômes fréquents

| Symptôme | Cause probable | Action |
|---|---|---|
| Aucun START après pose de `agent:auto` | orchestrateur arrêté, `PAUSE`, plafond journalier, jeton GitHub expiré | `status`, `systemctl status`, `gh auth status` |
| E-mails absents | transport `none`/`file`, SMTP refusé | `notify.py status` (problèmes de config), `notify.log` |
| PR READY mais jamais DEPLOYED | `AUTO_MERGE=0` (attendu) ou déploiement non configuré | fusion manuelle ou configurer `DEPLOY_CMD`/`PUBLIC_URL` |
| `/healthz` ≠ SHA fusionné | bascule échouée et retour arrière effectué | e-mail FAILED, `docs/RECOVERY.md` |
