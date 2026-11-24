#!/usr/bin/env python3
"""Serveur minimal du contrat universel (Python 3 bibliothèque standard) :
$HOST:$PORT, GET /healthz → {"ok": true, "commit": <REVISION>}, fichiers de public/, données sous
$APP_DATA_DIR, en-têtes de sécurité, journal sans donnée personnelle."""
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECURITY = {
    'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cross-Origin-Opener-Policy': 'same-origin', 'X-Frame-Options': 'DENY',
    'Strict-Transport-Security': 'max-age=31536000',
}


def revision() -> str:
    try:
        return (ROOT / 'REVISION').read_text(encoding='utf-8').strip() or 'dev'
    except OSError:
        return 'dev'


class Handler(SimpleHTTPRequestHandler):
    server_version = 'app'
    sys_version = ''

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT / 'public'), **kw)

    def end_headers(self):
        for k, v in SECURITY.items():
            self.send_header(k, v)
        super().end_headers()

    def do_GET(self):
        if self.path.split('?')[0] == '/healthz':
            body = json.dumps({'ok': True, 'commit': revision()}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        self.send_error(405)

    def log_message(self, fmt, *args):  # pas d'adresse IP ni d'en-tête dans le journal
        sys.stderr.write(json.dumps({'p': self.path.split('?')[0], 's': args[1] if len(args) > 1 else ''}) + '\n')


def main() -> int:
    host = os.environ.get('HOST', '127.0.0.1')
    try:
        port = int(os.environ.get('PORT', '8080'))
        assert 1 <= port <= 65535
    except (ValueError, AssertionError):
        print('PORT invalide', file=sys.stderr)
        return 1
    Path(os.environ.get('APP_DATA_DIR', ROOT / 'data')).mkdir(parents=True, exist_ok=True, mode=0o700)
    srv = ThreadingHTTPServer((host, port), Handler)
    print(json.dumps({'event': 'listening', 'host': host, 'port': port}), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
