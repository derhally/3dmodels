// Every catalog page: the light/dark switch. The home page: search and filters.
const root = document.documentElement;
const dark = () => root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
document.getElementById('theme')?.addEventListener('click', () => {
  root.dataset.theme = dark() ? 'light' : 'dark';
  try { localStorage.setItem('catalog-theme', root.dataset.theme); } catch (e) { /* private window */ }
  window.dispatchEvent(new Event('themechange'));
});

const cards = [...document.querySelectorAll('#cards .card')];
if (cards.length) {
  const q = document.getElementById('q');
  const empty = document.getElementById('empty');
  const collBtns = [...document.querySelectorAll('#fc .pill')];
  const statusBtns = [...document.querySelectorAll('#fs .pill')];
  let coll = '';
  const statuses = new Set();
  const apply = () => {
    const words = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const c of cards) {
      const ok = (!coll || c.dataset.coll === coll)
        && (!statuses.size || statuses.has(c.dataset.status))
        && words.every(w => c.dataset.text.includes(w));
      c.hidden = !ok;
      shown += ok;
    }
    empty.hidden = shown > 0;
  };
  for (const b of collBtns) b.addEventListener('click', () => {
    coll = b.dataset.coll;
    collBtns.forEach(x => x.setAttribute('aria-pressed', String(x === b)));
    apply();
  });
  for (const b of statusBtns) b.addEventListener('click', () => {
    const on = !statuses.has(b.dataset.status);
    on ? statuses.add(b.dataset.status) : statuses.delete(b.dataset.status);
    b.setAttribute('aria-pressed', String(on));
    apply();
  });
  q.addEventListener('input', apply);
}
