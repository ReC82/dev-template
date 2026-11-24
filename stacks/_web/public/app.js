// i18n minimal sans dépendance : ?lang=xx > choix mémorisé > langue du navigateur > langue par défaut.
// Les langues disponibles viennent de <html data-locales="fr,en"> ; un fichier /i18n/<code>.json par langue.
const root = document.documentElement;
const locales = (root.dataset.locales || root.lang).split(',');
const fallback = root.lang || locales[0];

function pick() {
  const fromUrl = new URLSearchParams(location.search).get('lang');
  let saved = null;
  try { saved = localStorage.getItem('lang'); } catch { /* stockage indisponible */ }
  const nav = (navigator.languages || [navigator.language || '']).map((l) => l.slice(0, 2));
  return [fromUrl, saved, ...nav].find((l) => l && locales.includes(l)) || fallback;
}

async function apply(lang) {
  const res = await fetch(`/i18n/${lang}.json`);
  if (!res.ok) return;
  const dict = await res.json();
  root.lang = lang;
  for (const el of document.querySelectorAll('[data-i18n]')) {
    const v = dict[el.dataset.i18n];
    if (typeof v === 'string') el.textContent = v;
  }
  for (const el of document.querySelectorAll('[data-i18n-attr]')) {
    const [attr, key] = el.dataset.i18nAttr.split(':');
    if (typeof dict[key] === 'string') el.setAttribute(attr, dict[key]);
  }
  try { localStorage.setItem('lang', lang); } catch { /* idem */ }
  for (const b of document.querySelectorAll('#langs button')) b.setAttribute('aria-pressed', String(b.value === lang));
}

const nav = document.getElementById('langs');
if (nav && locales.length > 1) {
  for (const l of locales) {
    const b = document.createElement('button');
    b.type = 'button'; b.value = l; b.textContent = l.toUpperCase();
    b.addEventListener('click', () => apply(l));
    nav.append(b);
  }
}
apply(pick());
