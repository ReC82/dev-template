#!/usr/bin/env python3
"""Orchestrateur de référence (Python 3, bibliothèque standard ; outils externes : git, gh, claude).

Il travaille SANS ChatGPT connecté : il consomme les issues GitHub `agent:auto`, envoie l'e-mail START
avant de lancer Claude Code dans un worktree dédié, lit le rapport JSON de la session, passe la porte
locale, puis (si autorisé par la configuration) fusionne, déploie et vérifie l'URL publique.
DONE n'existe qu'après fusion + déploiement + smoke public réussi.

  orch.py --env /etc/<orch>/orch.env cycle     # une passe (pour un timer systemd)
  orch.py --env … loop                         # boucle (service systemd ou fenêtre tmux)
  orch.py --env … status | pause | resume | stop
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notify import Config as NotifyConfig, Notifier, iso, redact  # noqa: E402

HERE = Path(__file__).resolve().parent
PRIORITIES = {'priority:P0': 0, 'priority:P1': 1, 'priority:P2': 2}
SKIP_LABELS = {'agent:blocked', 'agent:human'}
FINAL = {'DONE', 'FAILED'}


def load_env(path: str | None) -> dict:
    env = dict(os.environ)
    if path:
        for line in Path(path).read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


class Orchestrator:
    def __init__(self, env: dict):
        self.env = env
        g = env.get
        self.name = g('ORCH_NAME', 'orch')
        self.repo = g('GITHUB_REPO', '')
        self.repo_dir = Path(g('REPO_DIR', '.'))
        self.worktrees = Path(g('WORKTREES_DIR', str(self.repo_dir.parent / 'worktrees')))
        self.state_dir = Path(g('ORCH_STATE_DIR', '.orch-state'))
        self.gh = g('GH_BIN', 'gh')
        self.claude = g('CLAUDE_BIN', 'claude')
        self.claude_args = shlex.split(g('CLAUDE_ARGS', '-p'))
        self.session_timeout = int(g('SESSION_TIMEOUT_MINUTES', '120')) * 60
        self.max_attempts = int(g('MAX_ATTEMPTS', '2'))
        self.max_sessions_day = int(g('MAX_SESSIONS_PER_DAY', '6'))
        self.gate_cmd = g('GATE_CMD', 'scripts/check-contract.sh')
        self.auto_merge = g('AUTO_MERGE', '0') == '1'
        self.deploy_cmd = g('DEPLOY_CMD', '')
        self.public_url = g('PUBLIC_URL', '')
        self.smoke_file = g('SMOKE_FILE', 'config/smoke.txt')
        self.base_branch = g('BASE_BRANCH', 'main')
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / 'sessions').mkdir(exist_ok=True)
        (self.state_dir / 'logs').mkdir(exist_ok=True)
        ncfg = dict(env)
        ncfg.setdefault('NOTIFY_STATE_DIR', str(self.state_dir / 'notify'))
        ncfg.setdefault('ORCH_NAME', self.name)
        self.notifier = Notifier(NotifyConfig(ncfg))
        self.state_file = self.state_dir / 'state.json'
        self.state = self._load()

    # -- état -----------------------------------------------------------------------------------
    def _load(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding='utf-8'))
        return {'tickets': {}, 'sessions': []}

    def save(self) -> None:
        tmp = self.state_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=1), encoding='utf-8')
        os.replace(tmp, self.state_file)

    def log(self, msg: str) -> None:
        line = f'{iso()} {redact(msg, self.env)}'
        with (self.state_dir / 'logs' / 'orch.log').open('a', encoding='utf-8') as f:
            f.write(line + '\n')
        print(line, flush=True)

    def ticket(self, n: int | str) -> dict:
        return self.state['tickets'].setdefault(str(n), {'status': 'READY', 'attempts': 0})

    # -- outils externes -------------------------------------------------------------------------
    def run(self, args: list[str], cwd: Path | None = None, timeout: int = 300, check: bool = True,
            env_extra: dict | None = None) -> subprocess.CompletedProcess:
        env = dict(self.env)
        env.update(env_extra or {})
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
        if check and p.returncode != 0:
            raise RuntimeError(f'{args[0]} {" ".join(args[1:3])} → code {p.returncode} : {redact(p.stderr.strip()[-400:], self.env)}')
        return p

    def gh_json(self, *args: str):
        out = self.run([self.gh, *args]).stdout
        return json.loads(out or 'null')

    # -- commandes de contrôle -------------------------------------------------------------------
    def paused(self) -> str:
        for flag in ('STOP', 'PAUSE'):
            if (self.state_dir / flag).exists():
                return flag
        return ''

    def sessions_today(self) -> int:
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        return sum(1 for s in self.state['sessions'] if s.get('start', '').startswith(today))

    # -- sélection --------------------------------------------------------------------------------
    def queue(self) -> list[dict]:
        issues = self.gh_json('issue', 'list', '--repo', self.repo, '--state', 'open', '--label', 'agent:auto',
                              '--limit', '100', '--json', 'number,title,labels,url') or []
        eligible = []
        for it in issues:
            labels = {lb['name'] for lb in it.get('labels', [])}
            t = self.ticket(it['number'])
            t.update(title=it['title'], url=it['url'])
            prio = min([PRIORITIES[lb] for lb in labels if lb in PRIORITIES] or [2])
            t['priority'] = f'P{prio}'
            if t['status'] == 'BLOCKED' and 'agent:blocked' not in labels:
                self.log(f'#{it["number"]} : agent:blocked retiré par le propriétaire → relance')
                t.update(status='READY', attempts=0)
            if labels & SKIP_LABELS or t['status'] in FINAL | {'WAITING_OWNER', 'BLOCKED'}:
                continue
            if t.get('deps') and any(self.ticket(d).get('status') != 'DONE' for d in str(t['deps']).split(',') if d.strip()):
                continue
            eligible.append({'number': it['number'], 'prio': prio, **t})
        eligible.sort(key=lambda x: (x['prio'], x['number']))
        self.save()
        return eligible

    # -- cycle --------------------------------------------------------------------------------------
    def cycle(self) -> str:
        if self.paused():
            self.log(f'{self.paused()} : aucun nouveau ticket')
            return self.paused().lower()
        self.notifier.flush()
        # 1. reprise d'une session interrompue (arrêt machine, crash, délai dépassé)
        running = [n for n, t in self.state['tickets'].items() if t['status'] == 'RUNNING']
        for n in running:
            t = self.ticket(n)
            self.notifier.send('RESUMED', n, t.get('title', ''), t.get('url', ''),
                               {'reason': f'session {t.get("session", "?")} interrompue ; reprise sur la branche {t.get("branch", "?")}',
                                'attempts': str(t.get('attempts', 0))}, key=t.get('session', ''))
            t['status'] = 'READY'
        self.save()
        # 2. livraison des PR prêtes, si la configuration l'autorise
        for n, t in list(self.state['tickets'].items()):
            if t['status'] == 'WAITING_OWNER' and t.get('gate') == 'ok' and self.auto_merge:
                self.ship(n)
        # 3. ticket suivant
        q = self.queue()
        if not q:
            return 'idle'
        if self.sessions_today() >= self.max_sessions_day:
            self.log(f'plafond de {self.max_sessions_day} sessions/jour atteint : attente du lendemain')
            return 'budget'
        return self.work(q[0]['number'])

    def work(self, n: int | str) -> str:
        t = self.ticket(n)
        n = str(n)
        first = not t.get('claimed')
        t['attempts'] = t.get('attempts', 0) + 1
        t['session'] = uuid.uuid4().hex[:8]
        slug = re.sub(r'[^a-z0-9]+', '-', t.get('title', '').lower()).strip('-')[:40] or 'ticket'
        t.setdefault('branch', f'agent/{n}-{slug}')
        t['status'] = 'RUNNING'
        self.state['sessions'].append({'issue': n, 'session': t['session'], 'start': iso()})
        self.save()
        if first:
            # START avant de lancer Claude : prise en charge visible même si la session échoue ensuite
            self.run([self.gh, 'issue', 'edit', n, '--repo', self.repo, '--add-label', 'agent:in-progress'], check=False)
            plan = (f'1) session Claude Code sur la branche {t["branch"]} ; 2) PR + porte locale ({self.gate_cmd}) ; '
                    f'3) {"fusion, déploiement et smoke public automatiques" if self.auto_merge else "fusion par le propriétaire"}')
            self.run([self.gh, 'issue', 'comment', n, '--repo', self.repo, '--body',
                      f'<!-- {self.name} -->\nPrise en charge par **{self.name}** (session `{t["session"]}`).\n\nPlan : {plan}'], check=False)
            res = self.notifier.send('START', n, t.get('title', ''), t.get('url', ''),
                                     {'priority': t.get('priority', 'P2'), 'session': t['session'], 'plan': plan})
            t['claimed'] = 1
            t['start_mail'] = res['status']
            self.save()
        try:
            wt = self.prepare_worktree(n, t['branch'])
            status = self.launch_session(n, t, wt)
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as err:
            status = {'status': 'ERROR', 'blockers': str(err)}
        return self.apply_status(n, t, status)

    def prepare_worktree(self, n: str, branch: str) -> Path:
        wt = self.worktrees / f'ticket-{n}'
        if wt.exists():
            return wt
        self.worktrees.mkdir(parents=True, exist_ok=True)
        self.run(['git', '-C', str(self.repo_dir), 'fetch', 'origin'])
        remote = self.run(['git', '-C', str(self.repo_dir), 'ls-remote', '--heads', 'origin', branch]).stdout.strip()
        if remote:
            self.run(['git', '-C', str(self.repo_dir), 'worktree', 'add', str(wt), branch])
        else:
            self.run(['git', '-C', str(self.repo_dir), 'worktree', 'add', '-b', branch, str(wt), f'origin/{self.base_branch}'])
        return wt

    def render_prompt(self, n: str, t: dict, wt: Path, status_file: Path) -> str:
        tpl = (HERE / 'session-prompt.md').read_text(encoding='utf-8')
        values = {'ISSUE': n, 'TITLE': t.get('title', ''), 'REPO': self.repo, 'BRANCH': t['branch'],
                  'WORKTREE': str(wt), 'STATUS_FILE': str(status_file), 'ORCH_NAME': self.name,
                  'ATTEMPT': str(t['attempts']), 'NOTE': t.get('note', '') or 'aucune', 'GATE_CMD': self.gate_cmd}
        return re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: values.get(m.group(1), m.group(0)), tpl)

    def launch_session(self, n: str, t: dict, wt: Path) -> dict:
        status_file = self.state_dir / 'sessions' / f'{t["session"]}.status.json'
        prompt = self.render_prompt(n, t, wt, status_file)
        self.log(f'#{n} : lancement de la session {t["session"]} (tentative {t["attempts"]})')
        logf = self.state_dir / 'logs' / f'session-{t["session"]}.log'
        with logf.open('w', encoding='utf-8') as out:
            p = subprocess.run([self.claude, *self.claude_args, prompt], cwd=wt, stdout=out, stderr=subprocess.STDOUT,
                               timeout=self.session_timeout, env={**self.env, 'ORCH_STATUS_FILE': str(status_file)})
        if not status_file.exists():
            return {'status': 'ERROR', 'blockers': f'aucun rapport de session (code {p.returncode})'}
        try:
            return json.loads(status_file.read_text(encoding='utf-8'))
        except ValueError:
            return {'status': 'ERROR', 'blockers': 'rapport de session illisible'}

    def apply_status(self, n: str, t: dict, s: dict) -> str:
        st = s.get('status', 'ERROR')
        for k in ('pr', 'commit_sha', 'tests', 'summary', 'deps', 'next_action'):
            if s.get(k):
                t[k] = s[k]
        self.state['sessions'][-1]['end'] = iso()
        if st == 'WAITING_OWNER' and s.get('pr'):
            gate = self.gate(n)
            t['gate'] = 'ok' if gate['ok'] else 'failed'
            if not gate['ok']:
                t['note'] = f'porte locale en échec : {gate["detail"]}'
                return self.retry_or_fail(n, t, t['note'])
            t['status'] = 'WAITING_OWNER'
            self.notifier.send('PR_READY', n, t.get('title', ''), t.get('url', ''),
                               {'pr': s['pr'], 'sha': s.get('commit_sha', '?'), 'summary': s.get('summary', ''),
                                'tests': f'{s.get("tests", "")} ; porte locale : OK'}, key=s.get('commit_sha', ''))
        elif st == 'BLOCKED':
            t['status'] = 'BLOCKED'
            self.run([self.gh, 'issue', 'edit', n, '--repo', self.repo, '--add-label', 'agent:blocked'], check=False)
            self.notifier.send('BLOCKED', n, t.get('title', ''), t.get('url', ''),
                               {'reason': s.get('blockers') or 'décision nécessaire',
                                'action': '; '.join(s.get('questions') or []) or 'répondre dans le ticket puis retirer agent:blocked'},
                               key=t['session'])
        elif st == 'READY' and s.get('deps'):
            t['status'] = 'READY'
            t['deps'] = s['deps']
        elif st == 'RUNNING':
            t['status'] = 'READY'  # reprise au prochain cycle, sur la même branche
            t['note'] = s.get('next_action', '')
        else:
            return self.retry_or_fail(n, t, s.get('blockers') or f'statut inattendu : {st}')
        self.save()
        return t['status']

    def retry_or_fail(self, n: str, t: dict, reason: str) -> str:
        if t['attempts'] < self.max_attempts:
            t['status'] = 'READY'
            t['note'] = reason
            self.log(f'#{n} : {reason} → nouvelle tentative au prochain cycle')
        else:
            t['status'] = 'FAILED'
            self.run([self.gh, 'issue', 'edit', n, '--repo', self.repo, '--add-label', 'agent:blocked'], check=False)
            self.notifier.send('FAILED', n, t.get('title', ''), t.get('url', ''),
                               {'reason': reason, 'attempts': str(t['attempts']),
                                'logs': f'{self.state_dir}/logs/session-{t["session"]}.log (expurgé)'}, key=t['session'])
        self.save()
        return t['status']

    def gate(self, n: str) -> dict:
        wt = self.worktrees / f'ticket-{n}'
        if not wt.exists():
            return {'ok': False, 'detail': 'worktree absent'}
        try:
            self.run(['git', '-C', str(wt), 'fetch', 'origin'], check=False)
            p = self.run(['bash', '-c', self.gate_cmd], cwd=wt, timeout=1800, check=False)
        except subprocess.TimeoutExpired:
            return {'ok': False, 'detail': 'délai dépassé'}
        tail = redact((p.stdout + p.stderr).strip()[-300:], self.env)
        return {'ok': p.returncode == 0, 'detail': f'code {p.returncode} : {tail}'}

    def ship(self, n: str) -> str:
        """Fusion → déploiement → smoke public. DEPLOYED seulement si tout passe."""
        t = self.ticket(n)
        try:
            self.run([self.gh, 'pr', 'merge', t['pr'], '--repo', self.repo, '--squash'])
            merged = self.gh_json('pr', 'view', t['pr'], '--repo', self.repo, '--json', 'mergeCommit,state')
            sha = (merged.get('mergeCommit') or {}).get('oid', '')
            t['merge_sha'] = sha
            self.run([self.gh, 'issue', 'edit', n, '--repo', self.repo, '--add-label', 'status:merged'], check=False)
        except RuntimeError as err:
            t['status'] = 'BLOCKED'
            self.notifier.send('BLOCKED', n, t.get('title', ''), t.get('url', ''),
                               {'reason': f'fusion impossible : {err}', 'action': 'vérifier la PR (conflit, protection de branche)'}, key='merge')
            self.save()
            return t['status']
        if not self.deploy_cmd or not self.public_url:
            t['status'] = 'BLOCKED'
            self.notifier.send('BLOCKED', n, t.get('title', ''), t.get('url', ''),
                               {'reason': f'fusionné ({sha[:12]}) mais aucun déploiement configuré (DEPLOY_CMD/PUBLIC_URL)',
                                'action': 'configurer le déploiement ou déclarer le ticket hors production'}, key=f'nodeploy:{sha}')
            self.save()
            return t['status']
        dep = self.run(['bash', '-c', self.deploy_cmd], cwd=self.repo_dir, timeout=1800, check=False,
                       env_extra={'DEPLOY_SHA': sha})
        smoke = self.run(['bash', str(HERE.parent / 'scripts' / 'smoke-test.sh'), self.public_url, sha,
                          str(self.repo_dir / self.smoke_file)], check=False, timeout=300) if dep.returncode == 0 else None
        if dep.returncode == 0 and smoke and smoke.returncode == 0:
            t['status'] = 'DONE'
            self.run([self.gh, 'issue', 'edit', n, '--repo', self.repo, '--add-label', 'status:deployed',
                      '--remove-label', 'agent:in-progress'], check=False)
            self.run([self.gh, 'issue', 'close', n, '--repo', self.repo, '--comment',
                      f'<!-- {self.name} -->\nLivré : fusionné ({sha}), déployé, `{self.public_url}/healthz` = {sha[:12]}, smoke public OK.'], check=False)
            self.notifier.send('DEPLOYED', n, t.get('title', ''), t.get('url', ''),
                               {'pr': t['pr'], 'sha': sha, 'public_url': self.public_url,
                                'healthz': f'commit = {sha[:12]}', 'tests': f'{t.get("tests", "")} ; smoke public : OK',
                                'changes': t.get('summary', ''), 'verify': f'ouvrir {self.public_url} et suivre les tests humains de la PR'},
                               key=sha)
        else:
            detail = redact(((smoke.stdout + smoke.stderr) if smoke else (dep.stdout + dep.stderr)).strip()[-400:], self.env)
            t['status'] = 'BLOCKED'
            self.notifier.send('FAILED', n, t.get('title', ''), t.get('url', ''),
                               {'reason': f'fusionné ({sha[:12]}) mais {"smoke public" if smoke else "déploiement"} en échec : {detail}',
                                'attempts': '1', 'action': 'voir docs/RECOVERY.md (retour arrière)'}, key=f'ship:{sha}')
        self.save()
        return t['status']


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Orchestrateur de référence')
    ap.add_argument('--env', help='fichier KEY=VALUE (hors Git, ex. /etc/<orch>/orch.env)')
    ap.add_argument('cmd', choices=['cycle', 'loop', 'status', 'pause', 'resume', 'stop', 'ship'])
    ap.add_argument('issue', nargs='?')
    a = ap.parse_args(argv)
    o = Orchestrator(load_env(a.env))
    if a.cmd == 'cycle':
        print(o.cycle())
    elif a.cmd == 'loop':
        while True:
            try:
                r = o.cycle()
            except Exception as err:  # la boucle survit ; l'erreur est journalisée expurgée
                o.log(f'erreur de cycle : {type(err).__name__}: {err}')
                r = 'error'
            if r == 'stop':
                return 0
            time.sleep(int(o.env.get('POLL_SECONDS', '300')))
    elif a.cmd == 'status':
        print(json.dumps({'paused': o.paused(), 'sessions_today': o.sessions_today(),
                          'tickets': o.state['tickets'], 'notifications': o.notifier.status()}, ensure_ascii=False, indent=1))
    elif a.cmd in ('pause', 'stop'):
        (o.state_dir / a.cmd.upper()).write_text(iso())
    elif a.cmd == 'resume':
        for f in ('PAUSE', 'STOP'):
            (o.state_dir / f).unlink(missing_ok=True)
    elif a.cmd == 'ship':
        print(o.ship(a.issue))
    return 0


if __name__ == '__main__':
    sys.exit(main())
