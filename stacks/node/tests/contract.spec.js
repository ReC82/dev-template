// Contrat universel : /healthz, en-têtes de sécurité, i18n, chemin hors public/ refusé.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:net';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const freePort = () => new Promise((r) => { const s = createServer().listen(0, '127.0.0.1', () => { const { port } = s.address(); s.close(() => r(port)); }); });

test('contrat : healthz, en-têtes, fichiers, i18n', async () => {
  const port = await freePort();
  const child = spawn(process.execPath, ['server.js'], { cwd: root, env: { ...process.env, HOST: '127.0.0.1', PORT: String(port), APP_DATA_DIR: mkdtempSync(join(tmpdir(), 'data-')) } });
  try {
    let res;
    for (let i = 0; i < 50; i++) { try { res = await fetch(`http://127.0.0.1:${port}/healthz`); break; } catch { await new Promise((r) => setTimeout(r, 100)); } }
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.ok, true);
    assert.equal(typeof body.commit, 'string');
    assert.match(res.headers.get('content-security-policy'), /frame-ancestors 'none'/);
    assert.equal(res.headers.get('x-content-type-options'), 'nosniff');
    const home = await fetch(`http://127.0.0.1:${port}/`);
    assert.match(await home.text(), /<html/);
    const locales = readFileSync(join(root, 'public/index.html'), 'utf8').match(/data-locales="([^"]+)"/)[1].split(',');
    for (const l of locales) assert.equal((await fetch(`http://127.0.0.1:${port}/i18n/${l}.json`)).status, 200, `i18n ${l}`);
    assert.equal((await fetch(`http://127.0.0.1:${port}/%2e%2e/server.js`)).status === 200, false);
    assert.equal((await fetch(`http://127.0.0.1:${port}/`, { method: 'POST' })).status, 405);
  } finally { child.kill(); }
});
