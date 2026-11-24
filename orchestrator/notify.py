#!/usr/bin/env python3
"""Notifications e-mail de l'orchestrateur (bibliothèque standard Python 3 uniquement).

Évènements obligatoires : START, PR_READY, DEPLOYED, BLOCKED, FAILED, RESUMED.
- File d'attente sur disque (NOTIFY_STATE_DIR/outbox) : un message n'est jamais perdu si le SMTP tombe.
- Retries bornés (NOTIFY_MAX_RETRIES par passage, NOTIFY_MAX_ATTEMPTS au total, puis état « dead »).
- Déduplication par clé (évènement + ticket + clé fournie) ; RESUMED limité à un envoi par fenêtre.
- Expurgation des secrets avant mise en file ; journal JSONL sans contenu ni adresse en clair.
- Transports : file (factice, écrit des .eml), smtp (réel, configuré hors Git), none (désactivé, signalé).

Utilisation en ligne de commande :
  notify.py send --event START --issue 12 --title "…" --url … [--field clé=valeur …] [--key …]
  notify.py flush            # renvoie les messages en attente
  notify.py status           # résumé de la file (JSON)
  notify.py test             # envoie un message de test (évènement TEST, non dédupliqué)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import smtplib
import socket
import ssl
import sys
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

EVENTS = {
    'START': 'Prise en charge',
    'PR_READY': 'Développement terminé — PR prête (pas encore livrée)',
    'DEPLOYED': 'Livré — fusionné, déployé et vérifié publiquement',
    'BLOCKED': 'Bloqué — action humaine nécessaire',
    'FAILED': 'Échec',
    'RESUMED': 'Reprise après interruption',
    'TEST': 'Message de test',
}
# Champs exigés par évènement : un rapport incomplet est refusé plutôt qu'envoyé trompeur.
REQUIRED = {
    'START': ['plan'],
    'PR_READY': ['pr', 'sha', 'tests'],
    'DEPLOYED': ['pr', 'sha', 'public_url', 'healthz', 'tests'],
    'BLOCKED': ['reason', 'action'],
    'FAILED': ['reason', 'attempts'],
    'RESUMED': ['reason'],
    'TEST': [],
}
SECRET_NAME = re.compile(r'(PASS|SECRET|TOKEN|KEY|CREDENTIAL)', re.I)
SECRET_PATTERNS = [
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----', re.S), '[expurgé]'),
    (re.compile(r'\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})'), '[expurgé]'),
    (re.compile(r'\b(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,})'), '[expurgé]'),
    (re.compile(r'(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]{8,}'), r'\1 [expurgé]'),
    (re.compile(r'(?i)\b(password|passwd|secret|token|api[_-]?key)(\s*[=:]\s*)\S+'), r'\1\2[expurgé]'),
    (re.compile(r'://[^/\s:@]+:[^/\s@]+@'), '://[expurgé]@'),
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or now()).strftime('%Y-%m-%dT%H:%M:%SZ')


def redact(text: str, env: dict | None = None) -> str:
    """Retire les secrets connus (valeurs d'environnement sensibles) et les motifs usuels."""
    env = os.environ if env is None else env
    out = str(text)
    for name, value in env.items():
        if SECRET_NAME.search(name) and value and len(value) >= 6 and not name.endswith('_FILE'):
            out = out.replace(value, '[expurgé]')
    for pat, repl in SECRET_PATTERNS:
        out = pat.sub(repl, out)
    return out


def mask_address(addr: str) -> str:
    """o***@e*** : le journal ne contient jamais d'adresse en clair."""
    parts = []
    for a in [x.strip() for x in addr.split(',') if x.strip()]:
        local, _, domain = a.partition('@')
        parts.append(f'{local[:1]}***@{domain[:1]}***')
    return ','.join(parts)


class Config:
    def __init__(self, env: dict | None = None):
        e = os.environ if env is None else env
        self.env = e
        self.state = Path(e.get('NOTIFY_STATE_DIR') or Path(e.get('ORCH_STATE_DIR', '.orch-state')) / 'notify')
        self.transport = e.get('NOTIFY_TRANSPORT', 'file')
        self.to = e.get('NOTIFY_TO', '')
        self.sender = e.get('NOTIFY_FROM', '')
        self.project = e.get('PROJECT_NAME', 'projet')
        self.orch = e.get('ORCH_NAME', 'orchestrateur')
        self.max_retries = int(e.get('NOTIFY_MAX_RETRIES', '3'))
        self.max_attempts = int(e.get('NOTIFY_MAX_ATTEMPTS', '10'))
        self.backoff = float(e.get('NOTIFY_BACKOFF_SECONDS', '5'))
        self.dedup_hours = float(e.get('NOTIFY_RESUME_DEDUP_HOURS', '6'))
        self.smtp_host = e.get('SMTP_HOST', '')
        self.smtp_port = int(e.get('SMTP_PORT', '587'))
        self.smtp_security = e.get('SMTP_SECURITY', 'starttls')  # starttls | ssl | none (loopback seulement)
        self.smtp_user = e.get('SMTP_USER', '')
        self.smtp_password_file = e.get('SMTP_PASSWORD_FILE', '')
        self.smtp_timeout = float(e.get('SMTP_TIMEOUT', '20'))
        self.file_dir = Path(e.get('NOTIFY_FILE_DIR') or self.state / 'sent-mail')

    def problems(self) -> list[str]:
        p = []
        if self.transport not in ('file', 'smtp', 'none'):
            p.append(f'NOTIFY_TRANSPORT inconnu : {self.transport}')
        if self.transport == 'smtp':
            for k, v in (('SMTP_HOST', self.smtp_host), ('NOTIFY_TO', self.to), ('NOTIFY_FROM', self.sender)):
                if not v:
                    p.append(f'{k} manquant')
            if self.smtp_security not in ('starttls', 'ssl', 'none'):
                p.append('SMTP_SECURITY doit valoir starttls, ssl ou none')
            if self.smtp_security == 'none' and self.smtp_host not in ('127.0.0.1', 'localhost', '::1'):
                p.append('SMTP_SECURITY=none est réservé à un relais local (127.0.0.1)')
            if self.smtp_user and not self.smtp_password_file:
                p.append('SMTP_USER sans SMTP_PASSWORD_FILE (le mot de passe ne va jamais dans une variable)')
        return p


class Notifier:
    def __init__(self, cfg: Config | None = None):
        self.cfg = cfg or Config()
        self.outbox = self.cfg.state / 'outbox'
        self.outbox.mkdir(parents=True, exist_ok=True)
        self.sent_index = self.cfg.state / 'sent.jsonl'
        self.log_file = self.cfg.state / 'notify.log'

    # -- journal --------------------------------------------------------------------------------
    def log(self, **fields) -> None:
        fields = {'ts': iso(), **fields}
        with self.log_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(fields, ensure_ascii=False) + '\n')

    def _sent_keys(self) -> dict[str, str]:
        keys: dict[str, str] = {}
        if self.sent_index.exists():
            for line in self.sent_index.read_text(encoding='utf-8').splitlines():
                try:
                    rec = json.loads(line)
                    keys[rec['key']] = rec['ts']
                except (ValueError, KeyError):
                    continue
        for p in self.outbox.glob('*.json'):  # en attente = déjà « pris en compte »
            try:
                rec = json.loads(p.read_text(encoding='utf-8'))
                keys.setdefault(rec['dedup_key'], rec['created'])
            except (ValueError, KeyError):
                continue
        return keys

    # -- composition ----------------------------------------------------------------------------
    def compose(self, event: str, issue: str, title: str, url: str, fields: dict) -> dict:
        if event not in EVENTS:
            raise ValueError(f'évènement inconnu : {event}')
        missing = [k for k in REQUIRED[event] if not str(fields.get(k, '')).strip()]
        if missing:
            raise ValueError(f'{event} : champs obligatoires manquants : {", ".join(missing)}')
        label = EVENTS[event]
        subject = f'[{self.cfg.project}][{event}] #{issue} {title}'.strip()
        lines = [
            f'{label}',
            '',
            f'Projet        : {self.cfg.project}',
            f'Orchestrateur : {self.cfg.orch}',
            f'Ticket        : #{issue} — {title}',
            f'URL           : {url}',
            f'Date (UTC)    : {iso()}',
        ]
        for k, v in fields.items():
            lines.append(f'{k:<14}: {v}' if '\n' not in str(v) else f'{k} :\n{v}')
        if event == 'PR_READY':
            lines += ['', 'ATTENTION : ce message ne signifie PAS que la modification est en ligne.',
                      'Elle le sera après fusion, déploiement et vérification publique (message DEPLOYED).']
        if event in ('BLOCKED', 'FAILED'):
            lines += ['', 'Le ticket n\'est pas terminé. Répondre dans le ticket GitHub relance le travail.']
        body = redact('\n'.join(lines), self.cfg.env)
        return {'subject': redact(subject, self.cfg.env), 'body': body}

    def send(self, event: str, issue: str, title: str = '', url: str = '', fields: dict | None = None,
             key: str = '') -> dict:
        """Met le message en file (avec déduplication) puis tente l'envoi. Rend l'état final."""
        fields = fields or {}
        dedup_key = f'{event}:{issue}:{key}'
        sent = self._sent_keys()
        if event != 'TEST' and dedup_key in sent:
            if event != 'RESUMED':
                self.log(event=event, issue=issue, result='dedup')
                return {'status': 'dedup', 'key': dedup_key}
            age_h = (now() - datetime.strptime(sent[dedup_key], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if age_h < self.cfg.dedup_hours:
                self.log(event=event, issue=issue, result='dedup')
                return {'status': 'dedup', 'key': dedup_key}
        msg = self.compose(event, str(issue), title, url, fields)
        mid = hashlib.sha256(f'{dedup_key}:{time.time_ns()}'.encode()).hexdigest()[:16]
        rec = {'id': mid, 'dedup_key': dedup_key, 'event': event, 'issue': str(issue), 'created': iso(),
               'attempts': 0, 'status': 'pending', 'last_error': '', **msg}
        self._write(rec)
        self.log(event=event, issue=issue, id=mid, result='queued')
        return self._deliver(rec)

    def _write(self, rec: dict) -> None:
        p = self.outbox / f'{rec["id"]}.json'
        tmp = p.with_suffix('.tmp')
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding='utf-8')
        os.replace(tmp, p)

    def _deliver(self, rec: dict) -> dict:
        problems = self.cfg.problems()
        if problems:
            rec['status'], rec['last_error'] = 'pending', '; '.join(problems)
            self._write(rec)
            self.log(event=rec['event'], issue=rec['issue'], id=rec['id'], result='config_error', error=rec['last_error'])
            return {'status': 'pending', 'error': rec['last_error'], 'id': rec['id']}
        for i in range(self.cfg.max_retries):
            if rec['attempts'] >= self.cfg.max_attempts:
                break
            rec['attempts'] += 1
            try:
                self._transport(rec)
            except (OSError, smtplib.SMTPException, socket.error) as err:  # pas d'écho de secret
                rec['last_error'] = redact(f'{type(err).__name__}: {err}', self.cfg.env)[:300]
                self._write(rec)
                self.log(event=rec['event'], issue=rec['issue'], id=rec['id'], result='retry', attempt=rec['attempts'], error=rec['last_error'])
                if i + 1 < self.cfg.max_retries:
                    time.sleep(self.cfg.backoff * (2 ** i))
                continue
            status = 'disabled' if self.cfg.transport == 'none' else 'sent'
            with self.sent_index.open('a', encoding='utf-8') as f:
                f.write(json.dumps({'key': rec['dedup_key'], 'ts': iso(), 'id': rec['id'], 'status': status}) + '\n')
            (self.outbox / f'{rec["id"]}.json').unlink(missing_ok=True)
            self.log(event=rec['event'], issue=rec['issue'], id=rec['id'], result=status,
                     transport=self.cfg.transport, to=mask_address(self.cfg.to), attempt=rec['attempts'])
            return {'status': status, 'id': rec['id']}
        rec['status'] = 'dead' if rec['attempts'] >= self.cfg.max_attempts else 'pending'
        self._write(rec)
        self.log(event=rec['event'], issue=rec['issue'], id=rec['id'], result=rec['status'], attempts=rec['attempts'])
        return {'status': rec['status'], 'error': rec['last_error'], 'id': rec['id']}

    def _transport(self, rec: dict) -> None:
        c = self.cfg
        if c.transport == 'none':
            return
        msg = EmailMessage()
        msg['Subject'] = rec['subject']
        msg['From'] = c.sender or f'{c.orch}@localhost'
        msg['To'] = c.to or 'owner@localhost'
        msg['Date'] = formatdate(localtime=False)
        msg['Message-ID'] = make_msgid(idstring=rec['id'], domain='orchestrator.local')
        msg.set_content(rec['body'])
        if c.transport == 'file':
            c.file_dir.mkdir(parents=True, exist_ok=True)
            (c.file_dir / f'{rec["created"].replace(":", "")}-{rec["event"]}-{rec["id"]}.eml').write_bytes(bytes(msg))
            return
        password = ''
        if c.smtp_password_file:
            password = Path(c.smtp_password_file).read_text(encoding='utf-8').strip()
        context = ssl.create_default_context()
        if c.smtp_security == 'ssl':
            server = smtplib.SMTP_SSL(c.smtp_host, c.smtp_port, timeout=c.smtp_timeout, context=context)
        else:
            server = smtplib.SMTP(c.smtp_host, c.smtp_port, timeout=c.smtp_timeout)
        try:
            server.ehlo()
            if c.smtp_security == 'starttls':
                server.starttls(context=context)
                server.ehlo()
            if c.smtp_user:
                server.login(c.smtp_user, password)
            server.send_message(msg)
        finally:
            try:
                server.quit()
            except (OSError, smtplib.SMTPException):
                pass

    # -- maintenance ----------------------------------------------------------------------------
    def flush(self) -> list[dict]:
        results = []
        for p in sorted(self.outbox.glob('*.json')):
            rec = json.loads(p.read_text(encoding='utf-8'))
            if rec.get('status') == 'dead':
                results.append({'status': 'dead', 'id': rec['id']})
                continue
            results.append(self._deliver(rec))
        return results

    def status(self) -> dict:
        pending = dead = 0
        for p in self.outbox.glob('*.json'):
            rec = json.loads(p.read_text(encoding='utf-8'))
            dead += rec.get('status') == 'dead'
            pending += rec.get('status') != 'dead'
        sent = len(self.sent_index.read_text(encoding='utf-8').splitlines()) if self.sent_index.exists() else 0
        return {'transport': self.cfg.transport, 'pending': pending, 'dead': dead, 'sent': sent,
                'config_problems': self.cfg.problems(),
                'warning': 'NOTIFY_TRANSPORT=none : aucun e-mail réel envoyé' if self.cfg.transport == 'none' else ''}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='Notifications e-mail de l\'orchestrateur')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('send')
    s.add_argument('--event', required=True, choices=sorted(EVENTS))
    s.add_argument('--issue', required=True)
    s.add_argument('--title', default='')
    s.add_argument('--url', default='')
    s.add_argument('--key', default='')
    s.add_argument('--field', action='append', default=[], help='clé=valeur (répétable)')
    sub.add_parser('flush')
    sub.add_parser('status')
    sub.add_parser('test')
    a = ap.parse_args(argv)
    n = Notifier()
    if a.cmd == 'send':
        fields = dict(f.split('=', 1) for f in a.field)
        try:
            res = n.send(a.event, a.issue, a.title, a.url, fields, a.key)
        except ValueError as err:
            print(json.dumps({'status': 'refused', 'error': str(err)}, ensure_ascii=False))
            return 2
    elif a.cmd == 'flush':
        res = n.flush()
    elif a.cmd == 'test':
        res = n.send('TEST', '0', 'test de notification', '', {'note': 'vérification du transport'}, key=iso())
    else:
        res = n.status()
    print(json.dumps(res, ensure_ascii=False))
    if isinstance(res, dict) and res.get('status') in ('pending', 'dead'):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
