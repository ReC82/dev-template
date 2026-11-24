#!/usr/bin/env python3
"""Rapport d'état du projet, consultable dans GitHub (source de vérité pour ChatGPT et le propriétaire).

  python3 scripts/status_report.py --repo owner/nom [--public-url https://…] [--orch-state DIR] \
      [--update-issue N]

Sans --update-issue : écrit le Markdown sur la sortie standard. Avec : remplace le corps de l'issue
« tableau de bord » N. Lecture seule partout ailleurs. Aucun secret ni donnée personnelle.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GH = os.environ.get('GH_BIN', 'gh')


def gh_json(*args: str):
    p = subprocess.run([GH, *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f'gh {" ".join(args[:2])} : {p.stderr.strip()[-200:]}')
    return json.loads(p.stdout or 'null')


def healthz(url: str) -> str:
    try:
        with urllib.request.urlopen(url.rstrip('/') + '/healthz', timeout=10) as r:
            d = json.loads(r.read().decode())
            return f'ok={d.get("ok")} commit={str(d.get("commit", ""))[:12]}'
    except (OSError, ValueError) as err:
        return f'injoignable ({type(err).__name__})'


def build(repo: str, public_url: str, orch_state: str) -> str:
    issues = gh_json('issue', 'list', '--repo', repo, '--state', 'open', '--limit', '200',
                     '--json', 'number,title,labels,url')
    prs = gh_json('pr', 'list', '--repo', repo, '--state', 'open', '--limit', '50', '--json', 'number,title,url,headRefName')
    closed = gh_json('issue', 'list', '--repo', repo, '--state', 'closed', '--limit', '10', '--json', 'number,title,labels')
    groups: dict[str, list] = {'en cours': [], 'bloqués / humain': [], 'file automatique': [], 'autres': []}
    for it in issues:
        labels = {lb['name'] for lb in it['labels']}
        line = f'- #{it["number"]} {it["title"]} `{" ".join(sorted(labels))}`'
        if 'agent:in-progress' in labels:
            groups['en cours'].append(line)
        elif labels & {'agent:blocked', 'agent:human'}:
            groups['bloqués / humain'].append(line)
        elif 'agent:auto' in labels:
            groups['file automatique'].append(line)
        else:
            groups['autres'].append(line)
    out = [f'# État du projet `{repo}`', '',
           f'_Généré le {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC par `scripts/status_report.py`. '
           'Ce tableau reflète GitHub ; il ne remplace pas la lecture des tickets._', '']
    if public_url:
        out += ['## Production', '', f'- {public_url} — `/healthz` : {healthz(public_url)}', '']
    for name, lines in groups.items():
        out += [f'## Tickets {name} ({len(lines)})', ''] + (lines or ['- aucun']) + ['']
    out += [f'## Pull requests ouvertes ({len(prs)})', ''] + \
           ([f'- #{p["number"]} {p["title"]} (`{p["headRefName"]}`)' for p in prs] or ['- aucune']) + ['']
    out += ['## Derniers tickets fermés', ''] + \
           ([f'- #{c["number"]} {c["title"]} `{" ".join(sorted(lb["name"] for lb in c["labels"]))}`' for c in closed] or ['- aucun']) + ['']
    if orch_state:
        sf = Path(orch_state) / 'state.json'
        if sf.exists():
            st = json.loads(sf.read_text(encoding='utf-8'))
            out += ['## Orchestrateur', '']
            for n, t in sorted(st.get('tickets', {}).items(), key=lambda x: int(x[0])):
                out.append(f'- #{n} : {t.get("status")} (tentatives {t.get("attempts", 0)}) {t.get("pr", "")}')
            paused = [f for f in ('STOP', 'PAUSE') if (Path(orch_state) / f).exists()]
            out += [f'- drapeau : {", ".join(paused) or "actif"}', '']
    return '\n'.join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--public-url', default='')
    ap.add_argument('--orch-state', default='')
    ap.add_argument('--update-issue', default='')
    a = ap.parse_args(argv)
    md = build(a.repo, a.public_url, a.orch_state)
    if a.update_issue:
        p = subprocess.run([GH, 'issue', 'edit', a.update_issue, '--repo', a.repo, '--body-file', '-'],
                           input=md, capture_output=True, text=True)
        if p.returncode != 0:
            print(p.stderr, file=sys.stderr)
            return 1
        print(f'✓ tableau de bord #{a.update_issue} mis à jour')
    else:
        print(md)
    return 0


if __name__ == '__main__':
    sys.exit(main())
