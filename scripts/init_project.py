#!/usr/bin/env python3
"""Initialise un projet créé depuis dev-template (idempotent, sans réseau, sans secret).

  python3 scripts/init_project.py --name "Mon Projet" --slug monprojet --repo owner/monprojet \
      --stack node|python|static|other [--domain exemple.org] [--port 8080] [--orch monprojetorch] \
      [--locales fr,en] [--dry-run]

- copie le socle web commun puis le profil de stack choisi (sans écraser un fichier existant) ;
- remplace les placeholders (nom entouré de deux soulignés) dans tous les fichiers texte ;
- remplace README.md par README.project.md, retire stacks/ ;
- écrit .devtemplate/project.env (valeurs non secrètes) : relancer avec les mêmes valeurs ne change
  rien ; avec des valeurs différentes, refus explicite (code 2).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STACKS = ('node', 'python', 'static', 'other')
PLACEHOLDER = re.compile(r'__([A-Z][A-Z0-9_]*)__')
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'stacks'}
# outils qui manipulent eux-mêmes la syntaxe des placeholders
SKIP_FILES = {'scripts/init_project.py', 'scripts/check_repo.py'}
MARKER = Path('.devtemplate/project.env')
TEMPLATE_VERSION_FILE = Path('.devtemplate/TEMPLATE_VERSION')


def validate(a) -> list[str]:
    err = []
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,38}[a-z0-9]', a.slug):
        err.append('--slug : minuscules, chiffres, tirets (3 à 40 caractères)')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}', a.repo):
        err.append('--repo : propriétaire/nom')
    if a.domain and not re.fullmatch(r'(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', a.domain):
        err.append('--domain : nom de domaine en minuscules (ex. exemple.org)')
    if not (1024 <= a.port <= 65535):
        err.append('--port : entre 1024 et 65535')
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,30}', a.orch):
        err.append('--orch : minuscules, chiffres, tirets')
    if not a.name.strip() or len(a.name) > 60 or re.search(r'[<>"`$\\]', a.name):
        err.append('--name : 1 à 60 caractères, sans < > " ` $ \\')
    if not re.fullmatch(r'[a-z]{2}(-[A-Z]{2})?(,[a-z]{2}(-[A-Z]{2})?)*', a.locales):
        err.append('--locales : liste comme fr,en')
    return err


def values(a) -> dict[str, str]:
    locales = a.locales.split(',')
    return {
        'PROJECT_NAME': a.name.strip(), 'PROJECT_SLUG': a.slug, 'GITHUB_REPO': a.repo,
        'GITHUB_OWNER': a.repo.split('/')[0], 'PROJECT_DOMAIN': a.domain or 'localhost',
        'PROJECT_PORT': str(a.port), 'ORCH_NAME': a.orch, 'STACK': a.stack,
        'LOCALES': ','.join(locales), 'DEFAULT_LOCALE': locales[0],
    }


def runtime_values() -> dict[str, str]:
    return {'INIT_DATE': date.today().isoformat()}


def marker_text(v: dict) -> str:
    return '# Valeurs d\'initialisation (non secrètes) — écrit par scripts/init_project.py\n' + \
        ''.join(f'{k}={v[k]}\n' for k in sorted(v))


def text_files(root: Path):
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root)
        if p.is_dir() or any(part in SKIP_DIRS for part in rel.parts) or rel.as_posix() in SKIP_FILES:
            continue
        try:
            yield p, p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue


def copy_tree(src: Path, dst: Path, dry: bool, report: list[str]) -> None:
    if not src.exists():
        return
    for p in sorted(src.rglob('*')):
        rel = p.relative_to(src)
        target = dst / rel
        if p.is_dir():
            continue
        if target.exists():
            report.append(f'conservé (existe déjà) : {rel}')
            continue
        report.append(f'ajouté : {rel}')
        if not dry:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    ap = argparse.ArgumentParser(description='Initialise le projet depuis dev-template')
    ap.add_argument('--name', required=True)
    ap.add_argument('--slug', required=True)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--stack', required=True, choices=STACKS)
    ap.add_argument('--domain', default='')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--orch', default='')
    ap.add_argument('--locales', default='fr,en')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)
    a.orch = a.orch or f'{a.slug.replace("-", "")[:26]}orch'
    errors = validate(a)
    if errors:
        print('✗ paramètres invalides :\n  ' + '\n  '.join(errors), file=sys.stderr)
        return 1
    v = values(a)
    marker = root / MARKER
    if marker.exists():
        if marker.read_text(encoding='utf-8') == marker_text(v):
            print('✓ déjà initialisé avec ces valeurs : rien à faire')
            return 0
        print(f'✗ projet déjà initialisé avec d\'autres valeurs ({MARKER}) : modifier à la main ou repartir du template',
              file=sys.stderr)
        return 2
    if not (root / 'stacks').exists():
        print('✗ dossier stacks/ absent : ce dépôt ne vient pas de dev-template', file=sys.stderr)
        return 1
    report: list[str] = []
    if a.stack != 'other':
        copy_tree(root / 'stacks' / '_web', root, a.dry_run, report)
    copy_tree(root / 'stacks' / a.stack, root, a.dry_run, report)
    i18n = root / 'stacks' / '_web' / 'public' / 'i18n'
    if a.stack != 'other' and i18n.exists():
        base = i18n / 'en.json' if (i18n / 'en.json').exists() else sorted(i18n.glob('*.json'))[0]
        for loc in v['LOCALES'].split(','):
            target = root / 'public' / 'i18n' / f'{loc}.json'
            if not target.exists() and not (i18n / f'{loc}.json').exists():
                report.append(f'ajouté : public/i18n/{loc}.json (copie de {base.name}, À TRADUIRE)')
                if not a.dry_run:
                    data = json.loads(base.read_text(encoding='utf-8'))
                    data['_todo'] = f'à traduire en {loc} (copie de {base.stem})'
                    target.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    readme_project = root / 'README.project.md'
    if readme_project.exists():
        report.append('README.md ← README.project.md')
        if not a.dry_run:
            readme_project.replace(root / 'README.md')
    changed = 0
    for p, text in text_files(root):
        allv = {**v, **runtime_values()}
        new = PLACEHOLDER.sub(lambda m: allv.get(m.group(1), m.group(0)), text)
        if new != text:
            changed += 1
            if not a.dry_run:
                p.write_text(new, encoding='utf-8')
    report.append(f'placeholders remplacés dans {changed} fichier(s)')
    if not a.dry_run:
        shutil.rmtree(root / 'stacks')
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(marker_text(v), encoding='utf-8')
        for sh in list(root.glob('scripts/*.sh')) + list(root.glob('scripts/*.py')) + list(root.glob('orchestrator/*.py')):
            sh.chmod(0o755)
    leftovers = sorted({m.group(0) for p, t in text_files(root) for m in PLACEHOLDER.finditer(t)
                        }) if not a.dry_run else []
    print(('(simulation) ' if a.dry_run else '') + '\n'.join(report))
    if leftovers:
        print('⚠ placeholders inconnus restants : ' + ', '.join(leftovers))
    print(f'✓ projet « {v["PROJECT_NAME"]} » initialisé (stack {a.stack})' if not a.dry_run else '✓ simulation terminée')
    return 0


if __name__ == '__main__':
    sys.exit(main())
