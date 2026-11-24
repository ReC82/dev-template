// Serveur minimal du contrat universel (Node 22, aucune dépendance) :
// écoute $HOST:$PORT, GET /healthz → {"ok": true, "commit": <REVISION>}, fichiers de public/,
// données sous $APP_DATA_DIR, en-têtes de sécurité, journal sans donnée personnelle.
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { readFileSync } from 'node:fs';
import { join, normalize, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const host = process.env.HOST || '127.0.0.1';
const port = Number(process.env.PORT || 8080);
if (!Number.isInteger(port) || port < 1 || port > 65535) {
  console.error('PORT invalide');
  process.exit(1);
}
const dataDir = process.env.APP_DATA_DIR || join(root, 'data');
await mkdir(dataDir, { recursive: true, mode: 0o700 });
let commit = 'dev';
try { commit = readFileSync(join(root, 'REVISION'), 'utf8').trim() || 'dev'; } catch { /* REVISION absent en dev */ }

const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.webp': 'image/webp' };
const security = {
  'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
  'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Cross-Origin-Opener-Policy': 'same-origin', 'X-Frame-Options': 'DENY',
  'Strict-Transport-Security': 'max-age=31536000',
};

const server = createServer(async (req, res) => {
  const started = Date.now();
  const url = new URL(req.url, 'http://local');
  const send = (status, type, body) => {
    res.writeHead(status, { ...security, 'Content-Type': type });
    res.end(body);
    console.log(JSON.stringify({ m: req.method, p: url.pathname, s: status, ms: Date.now() - started }));
  };
  if (req.method !== 'GET' && req.method !== 'HEAD') return send(405, 'text/plain; charset=utf-8', 'Méthode non autorisée');
  if (url.pathname === '/healthz') return send(200, 'application/json', JSON.stringify({ ok: true, commit }));
  let rel;
  try { rel = normalize(decodeURIComponent(url.pathname)).replace(/^(\.\.[/\\])+/, ''); } catch {
    return send(400, 'text/plain; charset=utf-8', 'Requête invalide');
  }
  const file = join(root, 'public', rel.endsWith('/') ? join(rel, 'index.html') : rel);
  if (!file.startsWith(join(root, 'public'))) return send(400, 'text/plain; charset=utf-8', 'Requête invalide');
  try {
    send(200, types[extname(file)] || 'application/octet-stream', await readFile(file));
  } catch {
    send(404, 'text/plain; charset=utf-8', 'Introuvable');
  }
});
server.listen(port, host, () => console.log(JSON.stringify({ event: 'listening', host, port })));
for (const sig of ['SIGTERM', 'SIGINT']) process.on(sig, () => server.close(() => process.exit(0)));
