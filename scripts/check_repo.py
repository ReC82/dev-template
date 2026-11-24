#!/usr/bin/env python3
"""Contrôles statiques du dépôt (CI et porte locale) — lecture seule, sans dépendance.

1. fichiers obligatoires présents ;
2. aucun secret (motifs usuels, fichiers sensibles, valeurs dans les exemples de configuration) ;
3. après initialisation : plus aucun placeholder ;
4. liens Markdown relatifs et renvois `docs/*.md` valides.
Code de sortie 1 au premier problème trouvé (tous sont listés).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'dist'}
SELF = {'scripts/check_repo.py', 'scripts/init_project.py', 'orchestrator/notify.py'}
REQUIRED = ['README.md', 'AGENTS.md', 'CLAUDE.md', 'PROJECT_GUIDE.md', 'START_HERE.md', 'docs/ORCHESTRATOR.md',
            'docs/GITHUB_WORKFLOW.md', 'docs/DEPLOYMENT.md', 'docs/EMAIL_REPORTS.md', 'docs/SECURITY.md',
            'docs/BRANDING.md', 'docs/OPERATIONS.md', 'docs/NEW_PROJECT_CHECKLIST.md', 'docs/RECOVERY.md',
            'config/labels.tsv', 'orchestrator/orch.py', 'orchestrator/notify.py']
SECRET_RES = [
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{30,}'),
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    re.compile(r'\bsk-[A-Za-z0-9]{20,}'),
    re.compile(r'\bxox[abpr]-[A-Za-z0-9-]{10,}'),
]
SENSITIVE_NAMES = re.compile(r'(^|/)(\.env|.*\.pem|.*\.key|id_rsa|id_ed25519|.*\.p12)$')
ENV_SECRET_LINE = re.compile(r'^\s*[A-Z0-9_]*(PASS|PASSWORD|SECRET|TOKEN|API_KEY)[A-Z0-9_]*\s*=\s*(\S+)')
PLACEHOLDER = re.compile(r'__([A-Z][A-Z0-9_]*)__')
MD_LINK = re.compile(r'\]\(([^)\s]+)\)')
DOC_REF = re.compile(r'`(docs/[A-Za-z0-9_-]+\.md)`')


def files():
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        if p.is_file() and not any(x in SKIP_DIRS for x in rel.parts):
            yield p, rel.as_posix()


def main() -> int:
    problems: list[str] = []
    initialized = (ROOT / '.devtemplate' / 'project.env').exists()
    for f in REQUIRED:
        if not (ROOT / f).exists():
            problems.append(f'fichier obligatoire absent : {f}')
    for p, rel in files():
        if SENSITIVE_NAMES.search(rel):
            problems.append(f'fichier sensible versionné : {rel}')
        try:
            text = p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        if rel not in SELF:
            for r in SECRET_RES:
                if r.search(text):
                    problems.append(f'motif de secret dans {rel}')
        if '.env' in rel or rel.endswith('.example'):
            for line in text.splitlines():
                m = ENV_SECRET_LINE.match(line)
                if m and not m.group(2).startswith(('/', '<', '"<', '#')):
                    problems.append(f'valeur secrète dans un exemple : {rel} ({line.split("=")[0].strip()})')
        if initialized and rel not in SELF and rel != '.devtemplate/TEMPLATE_VERSION':
            for m in PLACEHOLDER.finditer(text):
                problems.append(f'placeholder restant {m.group(0)} dans {rel}')
        if rel.endswith('.md'):
            for m in MD_LINK.finditer(text):
                target = m.group(1).split('#')[0]
                if not target or re.match(r'^[a-z]+:', target) or PLACEHOLDER.search(target):
                    continue
                if not (p.parent / target).exists():
                    problems.append(f'lien cassé dans {rel} : {m.group(1)}')
            for m in DOC_REF.finditer(text):
                if not (ROOT / m.group(1)).exists():
                    problems.append(f'renvoi inexistant dans {rel} : {m.group(1)}')
    if problems:
        print('✗ check_repo :\n  ' + '\n  '.join(dict.fromkeys(problems)))
        return 1
    print(f'✓ check_repo : dépôt {"initialisé" if initialized else "modèle"} conforme')
    return 0


if __name__ == '__main__':
    sys.exit(main())
