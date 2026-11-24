#!/usr/bin/env python3
"""Crée labels, jalons et issues GitHub depuis des fichiers versionnés (idempotent, simulation par défaut).

  python3 scripts/github_bootstrap.py --repo owner/nom [--labels config/labels.tsv] \
      [--plan plan/issues.json] [--protect] [--dashboard] [--apply]

Sans --apply : n'appelle que des commandes de LECTURE et affiche ce qui serait créé.
Idempotence : un label existant (même nom) ou une issue existante (même titre exact, ouverte ou
fermée) n'est jamais recréé. Format du plan : voir docs/GITHUB_WORKFLOW.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

GH = os.environ.get('GH_BIN', 'gh')
ALLOWED_PREFIXES = ('agent:', 'priority:', 'status:', 'type:', 'phase:', 'area:')
DASHBOARD_TITLE = 'État du projet (tableau de bord)'


def gh(*args: str, read: bool = True, apply: bool = False) -> str:
    if not read and not apply:
        print('  [simulation] gh ' + ' '.join(args[:4]) + (' …' if len(args) > 4 else ''))
        return ''
    p = subprocess.run([GH, *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f'gh {" ".join(args[:3])} : {p.stderr.strip()[-300:]}')
    return p.stdout


def read_labels(path: Path) -> list[dict]:
    labels = []
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) != 3 or not re.fullmatch(r'[0-9a-fA-F]{6}', parts[1]):
            raise ValueError(f'{path}:{n} : attendu « nom<TAB>couleur hex<TAB>description »')
        labels.append({'name': parts[0], 'color': parts[1], 'description': parts[2]})
    return labels


def validate_plan(plan: dict, known_labels: set[str]) -> list[str]:
    err = []
    if not isinstance(plan.get('issues'), list) or not plan['issues']:
        return ['plan : liste « issues » vide ou absente']
    titles = set()
    for i, it in enumerate(plan['issues']):
        where = f'issues[{i}]'
        t = it.get('title', '')
        if not t or len(t) > 120:
            err.append(f'{where} : titre absent ou > 120 caractères')
        if t in titles:
            err.append(f'{where} : titre en double « {t} »')
        titles.add(t)
        body = it.get('body', '')
        for section in ('Objectif', 'Critères d\'acceptation'):
            if section not in body:
                err.append(f'{where} : section « {section} » absente du corps')
        for lb in it.get('labels', []):
            if lb not in known_labels:
                err.append(f'{where} : label inconnu « {lb} » (à déclarer dans labels.tsv)')
        if not any(lb.startswith('priority:') for lb in it.get('labels', [])):
            err.append(f'{where} : label priority:P0/P1/P2 manquant')
        if 'agent:auto' in it.get('labels', []) and 'agent:human' in it.get('labels', []):
            err.append(f'{where} : agent:auto et agent:human sont exclusifs')
        if re.search(r'(?i)(password|secret|token)\s*[=:]\s*\S{6,}', body):
            err.append(f'{where} : le corps semble contenir un secret')
    return err


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--repo', required=True)
    ap.add_argument('--labels', default='config/labels.tsv')
    ap.add_argument('--plan', default='')
    ap.add_argument('--protect', action='store_true', help='protéger la branche main (si l\'offre GitHub le permet)')
    ap.add_argument('--dashboard', action='store_true', help='créer l\'issue « tableau de bord » épinglée')
    ap.add_argument('--apply', action='store_true', help='exécuter réellement (sinon simulation)')
    ap.add_argument('--offline', action='store_true', help='simulation sans aucun appel gh (validation seule)')
    a = ap.parse_args(argv)
    labels = read_labels(Path(a.labels))
    known = {lb['name'] for lb in labels}
    plan = json.loads(Path(a.plan).read_text(encoding='utf-8')) if a.plan else {'issues': []}
    if a.plan:
        errors = validate_plan(plan, known)
        if errors:
            print('✗ plan invalide :\n  ' + '\n  '.join(errors), file=sys.stderr)
            return 1
    mode = 'EXÉCUTION' if a.apply else 'SIMULATION'
    print(f'== {mode} sur {a.repo} ==')
    if a.offline:
        existing_labels, existing_titles = set(), set()
    else:
        existing_labels = {x['name'] for x in json.loads(gh('label', 'list', '--repo', a.repo, '--limit', '200', '--json', 'name') or '[]')}
        existing_titles = {x['title'] for x in json.loads(gh('issue', 'list', '--repo', a.repo, '--state', 'all', '--limit', '1000', '--json', 'title') or '[]')}
    created = {'labels': 0, 'issues': 0}
    for lb in labels:
        if lb['name'] in existing_labels:
            continue
        created['labels'] += 1
        print(f'+ label {lb["name"]}')
        if not a.offline:
            gh('label', 'create', lb['name'], '--repo', a.repo, '--color', lb['color'], '--description', lb['description'],
               read=False, apply=a.apply)
    for ms in plan.get('milestones', []):
        print(f'· jalon « {ms} » : à créer dans l\'interface GitHub ou via gh api (facultatif)')
    issues = list(plan.get('issues', []))
    if a.dashboard:
        issues.append({'title': DASHBOARD_TITLE, 'labels': ['agent:human', 'priority:P2'],
                          'body': 'Objectif\n\nTableau de bord mis à jour par scripts/status_report.py --update-issue.\n\n'
                                  'Critères d\'acceptation\n\n- reflète l\'état réel (issues, PR, déploiement).'})
    for it in issues:
        if it['title'] in existing_titles:
            print(f'= issue existante : {it["title"]}')
            continue
        created['issues'] += 1
        print(f'+ issue {it["title"]} [{", ".join(it.get("labels", []))}]')
        if not a.offline:
            args = ['issue', 'create', '--repo', a.repo, '--title', it['title'], '--body', it.get('body', '')]
            for lb in it.get('labels', []):
                args += ['--label', lb]
            gh(*args, read=False, apply=a.apply)
    if a.protect:
        print('+ protection de main (vérification « contract » obligatoire, pas de force push ni suppression)')
        if a.apply and not a.offline:
            payload = json.dumps({'required_status_checks': {'strict': True, 'contexts': ['contract']},
                                  'enforce_admins': False, 'required_pull_request_reviews': None,
                                  'restrictions': None, 'allow_force_pushes': False, 'allow_deletions': False})
            p = subprocess.run([GH, 'api', '-X', 'PUT', f'repos/{a.repo}/branches/main/protection', '--input', '-'],
                               input=payload, capture_output=True, text=True)
            if p.returncode != 0:
                print('⚠ protection refusée par GitHub (dépôt privé en offre gratuite ?) : '
                      'décision humaine, voir docs/GITHUB_WORKFLOW.md')
    print(f'== {created["labels"]} label(s), {created["issues"]} issue(s) {"créés" if a.apply else "à créer"} ==')
    return 0


if __name__ == '__main__':
    sys.exit(main())
