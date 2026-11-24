"""Contrat universel : /healthz, en-têtes de sécurité, i18n, POST refusé."""
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ContractTest(unittest.TestCase):
    def test_contract(self):
        port = free_port()
        env = {**os.environ, 'HOST': '127.0.0.1', 'PORT': str(port), 'APP_DATA_DIR': tempfile.mkdtemp()}
        p = subprocess.Popen([sys.executable, 'app.py'], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            base = f'http://127.0.0.1:{port}'
            for _ in range(50):
                try:
                    r = urllib.request.urlopen(base + '/healthz')
                    break
                except OSError:
                    time.sleep(0.1)
            body = json.loads(r.read())
            self.assertIs(body['ok'], True)
            self.assertIn("frame-ancestors 'none'", r.headers['Content-Security-Policy'])
            self.assertIn('<html', urllib.request.urlopen(base + '/').read().decode())
            html = (ROOT / 'public/index.html').read_text(encoding='utf-8')
            for loc in re.search(r'data-locales="([^"]+)"', html).group(1).split(','):
                self.assertEqual(urllib.request.urlopen(f'{base}/i18n/{loc}.json').status, 200)
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(urllib.request.Request(base + '/', data=b'x', method='POST'))
            self.assertEqual(ctx.exception.code, 405)
        finally:
            p.terminate()
            p.wait(5)


if __name__ == '__main__':
    unittest.main()
