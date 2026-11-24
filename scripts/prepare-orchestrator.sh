#!/usr/bin/env bash
# Prépare (sans RIEN installer) les fichiers d'un orchestrateur DISTINCT pour ce projet :
#   <out>/<orch>.service      unité systemd durcie (installation root = action humaine)
#   <out>/<orch>-tmux.sh      alternative sans root : boucle dans une session tmux dédiée
#   <out>/orch.env            configuration (créée une seule fois, jamais écrasée ; aucun secret)
#   <out>/INSTALL.md          commandes exactes à faire valider/exécuter par l'humain
# Usage : scripts/prepare-orchestrator.sh --orch NOM --repo owner/nom --out DIR [--home DIR] [--user NOM]
#         (--home par défaut : /opt/<orch>)
# Idempotent : relancer avec les mêmes paramètres produit les mêmes fichiers.
set -euo pipefail
orch=""; repo=""; out=""; home=""; user=""
while [ $# -gt 0 ]; do
  case "$1" in
    --orch) orch="$2"; shift 2;; --repo) repo="$2"; shift 2;; --out) out="$2"; shift 2;;
    --home) home="$2"; shift 2;; --user) user="$2"; shift 2;;
    *) echo "option inconnue : $1" >&2; exit 1;;
  esac
done
[[ "$orch" =~ ^[a-z][a-z0-9-]{1,30}$ ]] || { echo "✗ --orch : minuscules, chiffres, tirets" >&2; exit 1; }
[[ "$repo" =~ ^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$ ]] || { echo "✗ --repo : propriétaire/nom" >&2; exit 1; }
[ -n "$out" ] || { echo "✗ --out requis" >&2; exit 1; }
home="${home:-/opt/$orch}"; user="${user:-$orch}"
here="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$out"

cat > "$out/$orch.service" <<UNIT
[Unit]
Description=Orchestrateur $orch ($repo) : issues agent:auto, Claude Code, PR, porte, livraison
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$user
Group=$user
WorkingDirectory=$home
ExecStart=/usr/bin/python3 $home/orchestrator/orch.py --env /etc/$orch/orch.env loop
Restart=on-failure
RestartSec=60
# Durcissement : l'orchestrateur n'a besoin que de son dossier, de son état et du réseau sortant.
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$home /var/lib/$orch
MemoryMax=1G
TasksMax=256

[Install]
WantedBy=multi-user.target
UNIT

cat > "$out/$orch-tmux.sh" <<TMUX
#!/usr/bin/env bash
# Alternative sans root : une session tmux dédiée « $orch » (jamais celle d'un autre projet).
set -euo pipefail
if tmux has-session -t "$orch" 2>/dev/null; then echo "session $orch déjà active"; exit 0; fi
tmux new-session -d -s "$orch" "python3 $home/orchestrator/orch.py --env $home/orch.env loop 2>&1 | tee -a $home/orch-console.log"
echo "✓ session tmux $orch lancée (tmux attach -t $orch)"
TMUX
chmod +x "$out/$orch-tmux.sh"

if [ ! -f "$out/orch.env" ]; then
  sed -e "s|^ORCH_NAME=.*|ORCH_NAME=$orch|" -e "s|^GITHUB_REPO=.*|GITHUB_REPO=$repo|" \
      -e "s|^REPO_DIR=.*|REPO_DIR=$home/repo|" -e "s|^WORKTREES_DIR=.*|WORKTREES_DIR=$home/worktrees|" \
      -e "s|^ORCH_STATE_DIR=.*|ORCH_STATE_DIR=/var/lib/$orch|" \
      -e "s|^SMTP_PASSWORD_FILE=.*|SMTP_PASSWORD_FILE=/etc/$orch/smtp-password|" \
      "$here/config/orchestrator.env.example" > "$out/orch.env"
  echo "+ $out/orch.env créé (à compléter, sans secret : les secrets vont dans des fichiers 0600 référencés)"
else
  echo "= $out/orch.env conservé"
fi

cat > "$out/INSTALL.md" <<INSTALL
# Installation de l'orchestrateur $orch : ACTIONS HUMAINES (root)

Rien n'a été installé par le script. À exécuter par le propriétaire, après relecture :

\`\`\`
sudo useradd --system --create-home --home-dir $home --shell /usr/sbin/nologin $user
sudo install -d -o $user -g $user -m 0700 /var/lib/$orch /etc/$orch
sudo -u $user git clone https://github.com/$repo.git $home/repo        # clone DÉDIÉ à l'orchestrateur
sudo cp -r $here/orchestrator $here/scripts $here/config $home/ && sudo chown -R $user: $home
sudo install -o $user -g $user -m 0600 $out/orch.env /etc/$orch/orch.env
# secrets : fichiers 0600 lisibles par $user seulement (jamais dans Git ni dans orch.env)
sudo install -o $user -g $user -m 0600 /dev/null /etc/$orch/smtp-password
sudo -u $user gh auth login            # jeton GitHub limité à $repo (fine-grained) : action humaine
sudo -u $user claude                   # connexion Claude Code : action humaine
sudo install -m 0644 $out/$orch.service /etc/systemd/system/$orch.service
sudo systemctl daemon-reload && sudo systemctl enable --now $orch.service
\`\`\`

Vérifications (lecture seule) :

\`\`\`
systemctl status $orch --no-pager
sudo -u $user env \$(grep -v '^#' /etc/$orch/orch.env | xargs) python3 $home/orchestrator/notify.py test
sudo -u $user python3 $home/orchestrator/orch.py --env /etc/$orch/orch.env status
journalctl -u $orch -n 50 --no-pager
\`\`\`
INSTALL
echo "✓ fichiers de l'orchestrateur $orch préparés dans $out (rien d'installé)"
