// The configurator page: the options from options.yaml as buttons, the CAD
// engine in worker.js, and the built parts in a three.js view with their
// downloads. The choices live in the address (#tool-bin&cells=4&...), so a
// configuration can be bookmarked or sent.
import * as THREE from 'three';
import { OrbitControls } from '../vendor/three/OrbitControls.js';
import { STLLoader } from '../vendor/three/STLLoader.js';
import { makeLights, fitCamera } from '../assets/scene.js';
import yaml from 'https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.mjs';

const $ = (id) => document.getElementById(id);
const E = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const OPT = yaml.load(await (await fetch('src/configurator/options.yaml')).text());
const TYPES = OPT.types;

// small side views for the type buttons (back against the panel on the left)
const ICONS = {
  'tool-bin': '<path d="M6 30V6h4c6 0 6 9 12 9h12v15z"/><path d="M10 21h24" class="ins"/>',
  'lean-bin': '<path d="M6 30V6h7l21 13-12 11z"/><path d="M11 13l17 10" class="ins"/>',
  'tray': '<path d="M6 30V18h4c5 0 5 7 10 7h14v5z"/>',
  'arc-drawer': '<path d="M6 30V6h28v24z"/><path d="M10 10h20v16H10z" class="ins"/>',
};
const icon = (k) => `<svg viewBox="0 0 40 36" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round">
  <path d="M3 3v30" stroke-width="3" opacity=".35"/>${ICONS[k] || ''}</svg>`.replace('class="ins"', 'class="ins" stroke="#e07b2a"');

// ---------------------------------------------------------------- state
const state = { kind: Object.keys(TYPES)[0], values: {} };
const cond = (expr, v) => !expr || Function(...Object.keys(v), `return (${expr});`)(...Object.values(v));
function normalise(kind, given) {
  const v = {};
  for (const f of TYPES[kind].fields) v[f.id] = f.id in (given || {}) ? given[f.id] : f.default;
  for (const f of TYPES[kind].fields) {
    if (f.kind === 'int' || f.kind === 'number') {
      let x = Number(v[f.id]);
      if (!Number.isFinite(x)) x = f.default;
      x = Math.min(Math.max(x, f.min), f.max);
      v[f.id] = f.kind === 'int' ? Math.round(x) : Math.round(x / (f.step || 1)) * (f.step || 1);
    }
  }
  for (const f of TYPES[kind].fields) {
    if (f.kind !== 'choice') continue;
    const ok = f.choices.filter((c) => cond(c.when, v)).map((c) => String(c.id));
    if (!ok.includes(String(v[f.id]))) v[f.id] = ok[0];
  }
  return v;
}
function fromHash() {
  const [kind, ...pairs] = decodeURIComponent(location.hash.slice(1)).split('&');
  if (!TYPES[kind]) return;
  state.kind = kind;
  const v = {};
  for (const p of pairs) { const [k, x] = p.split('='); if (k) v[k] = x; }
  state.values[kind] = normalise(kind, v);
}
function toHash() {
  const v = state.values[state.kind];
  history.replaceState(null, '', '#' + [state.kind, ...Object.entries(v).map(([k, x]) => `${k}=${x}`)].join('&'));
}
const values = () => (state.values[state.kind] ||= normalise(state.kind, {}));
const isTested = (kind, v) => (TYPES[kind].tested || []).some((s) => Object.entries(s).every(([k, x]) => String(v[k]) === String(x)));

// ---------------------------------------------------------------- the form
function renderTypes() {
  $('types').innerHTML = '<legend>What hangs on the wall</legend><div class="cfg-typelist">' +
    Object.entries(TYPES).map(([k, t]) => `<button type="button" class="cfg-type" data-kind="${k}" aria-pressed="${k === state.kind}">
      ${icon(k)}<span><b>${E(t.name)}</b><small>${E(t.blurb)}</small></span></button>`).join('') + '</div>';
}
function renderFields() {
  const v = values();
  let h = '<legend>Size and insert</legend>';
  for (const f of TYPES[state.kind].fields) {
    h += `<div class="cfg-field"><span class="cfg-label" id="l-${f.id}">${E(f.label)}</span>`;
    if (f.kind === 'int') {
      h += `<div class="cfg-step" role="group" aria-labelledby="l-${f.id}">
        <button type="button" data-step="${f.id}" data-by="-1" aria-label="fewer" ${v[f.id] <= f.min ? 'disabled' : ''}>−</button>
        <output>${v[f.id]} ${E(f.unit || '')}</output>
        <button type="button" data-step="${f.id}" data-by="1" aria-label="more" ${v[f.id] >= f.max ? 'disabled' : ''}>+</button>
        <span class="cfg-range">${f.min}–${f.max}</span></div>`;
    } else if (f.kind === 'number') {
      h += `<div class="cfg-step"><input id="f-${f.id}" type="number" inputmode="decimal" data-num="${f.id}" min="${f.min}" max="${f.max}" step="${f.step || 1}"
        value="${v[f.id]}" aria-labelledby="l-${f.id}"><span class="cfg-unit">${E(f.unit || '')}</span><span class="cfg-range">${f.min}–${f.max}</span></div>`;
    } else {
      h += `<div class="cfg-seg" role="group" aria-labelledby="l-${f.id}">` + f.choices.map((c) =>
        `<button type="button" data-k="${f.id}" data-v="${E(c.id)}" aria-pressed="${String(v[f.id]) === String(c.id)}" ${cond(c.when, v) ? '' : 'disabled'}>${E(c.label)}</button>`).join('') + '</div>';
    }
    if (f.note) h += `<span class="cfg-note">${E(f.note)}</span>`;
    h += '</div>';
  }
  $('fields').innerHTML = h;
  const t = TYPES[state.kind];
  const w = (v.cells * 25.4 - 0.3).toFixed(1);       // every Omniwall part: cells x pitch - 0.3, so they tile
  const hgt = v.rows != null ? (v.rows * 25.4 - 0.3).toFixed(1) : '25.1';
  $('summary').textContent = `${t.name}: ${w} wide × ${hgt} tall × ${v.depth} deep (mm)` + (isTested(state.kind, v) ? ' · a size on main' : '');
}
function setValue(k, x) {
  state.values[state.kind] = normalise(state.kind, { ...values(), [k]: x });
  toHash();
  renderFields();
}
$('form').addEventListener('click', (e) => {
  const b = e.target.closest('button');
  if (!b || b.disabled) return;
  if (b.dataset.kind) { state.kind = b.dataset.kind; values(); toHash(); renderTypes(); renderFields(); }
  else if (b.dataset.step) setValue(b.dataset.step, values()[b.dataset.step] + Number(b.dataset.by));
  else if (b.dataset.k) setValue(b.dataset.k, b.dataset.v);
});
$('form').addEventListener('change', (e) => { if (e.target.dataset.num) setValue(e.target.dataset.num, e.target.value); });
$('form').addEventListener('submit', (e) => { e.preventDefault(); build(); });
window.addEventListener('hashchange', () => { fromHash(); renderTypes(); renderFields(); });
fromHash();
renderTypes();
renderFields();

// ---------------------------------------------------------------- the engine
const worker = new Worker('worker.js', { type: 'module' });   // Pyodide 314 runs only in a module worker
let ready = false, building = null, nextId = 1;
const started = performance.now();
const tick = setInterval(() => { if (!ready) $('engine-time').textContent = `${((performance.now() - started) / 1000).toFixed(0)} s`; }, 500);
worker.onmessage = (e) => {
  const m = e.data;
  if (m.type === 'status') {
    $('engine-text').textContent = m.text;
    $('engine-bar').style.width = `${(m.step - 0.5) / m.of * 100}%`;
  } else if (m.type === 'ready') {
    ready = true;
    clearInterval(tick);
    $('engine').classList.add('ready');
    $('engine-text').textContent = 'CAD engine ready: build123d and OpenCascade, running in this page';
    $('engine-time').textContent = `loaded in ${m.seconds.toFixed(0)} s`;
    $('build').disabled = false;
    if (pendingBuild) { pendingBuild = false; build(); }
  } else if (m.type === 'log') {
    if (building) building.log.push(m.text);
  } else if (m.type === 'built') {
    finish(m.result, m.files);
  } else if (m.type === 'error') {
    if (building) { failed(m.text); return; }
    clearInterval(tick);
    $('engine').classList.add('failed');
    $('engine-text').textContent = `The CAD engine did not load: ${m.text}. Reload the page to try again.`;
  }
};
worker.postMessage({ cmd: 'init', engine: OPT.engine });

let pendingBuild = false;
function build() {
  if (building) return;
  if (!ready) { pendingBuild = true; $('build').textContent = 'Building once the engine is ready…'; return; }
  const kind = state.kind, v = values();
  building = { id: nextId++, kind, v, t: performance.now(), log: [] };
  $('build').disabled = true;
  $('build').textContent = 'Building…';
  busy(`Building ${TYPES[kind].name.toLowerCase()} with build.py…`);
  worker.postMessage({ cmd: 'build', id: building.id, kind, values: v });
}
function busy(text) {
  let el = document.querySelector('.cfg-busy');
  if (!el) { el = document.createElement('div'); el.className = 'cfg-busy'; $('stage').append(el); }
  const t0 = performance.now();
  clearInterval(busy.timer);
  const put = () => { el.textContent = `${text} ${((performance.now() - t0) / 1000).toFixed(0)} s`; };
  put();
  busy.timer = setInterval(put, 500);
}
function idle() {
  clearInterval(busy.timer);
  document.querySelector('.cfg-busy')?.remove();
  $('build').disabled = false;
  $('build').textContent = 'Build';
  building = null;
}
function failed(text) {
  const log = building ? building.log.join('\n') : '';
  idle();
  showResult({ ok: false, checks: [{ label: 'Build', status: 'fail', detail: text }], report: log, params: '', files: {}, prefix: '' }, {});
}

// ---------------------------------------------------------------- the result
const urls = [];
function finish(result, files) {
  idle();
  showResult(result, files);
  showParts(files);
}
const SIZE = (n) => n > 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1e3))} kB`;
const ABOUT = [
  [/_all_parts\.3mf$/, 'Bambu Studio project: every part on the plate, H2C settings'],
  [/_print\.stl$/, 'STL, laid as on the bed'],
  [/_assembly\.step$/, 'STEP for CAD: the parts on their hooks'],
];
function showResult(r, files) {
  urls.splice(0).forEach(URL.revokeObjectURL);
  const t = TYPES[r.kind] || TYPES[state.kind];
  $('result').hidden = false;
  $('result-title').textContent = r.prefix ? `${t.name}: ${r.prefix}` : `${t.name}: build failed`;
  const fails = r.checks.filter((c) => c.status === 'fail').length, warns = r.checks.filter((c) => c.status === 'warn').length;
  $('result-chip').innerHTML = !r.ok || fails ? '<span class="chip cfg-fail">Failed a check: don\'t print</span>'
    : r.tested ? '<span class="chip s-printed">Same as a size on main</span>'
    : `<span class="chip s-new">New size${warns ? ', see the notes' : ''}: not print-tested yet</span>` + (r.seconds ? ` <span class="cfg-faint">built in ${r.seconds.toFixed(0)} s</span>` : '');
  $('checks').innerHTML = r.checks.map((c) => `<li class="${c.status}"><span class="dot"></span><b>${E(c.label)}</b><span>${E(c.detail)}</span></li>`).join('');
  const names = Object.keys(files).filter((f) => /\.(3mf|stl|step)$/.test(f))
    .sort((a, b) => (/\.3mf$/.test(b) - /\.3mf$/.test(a)) || a.localeCompare(b));
  $('files').innerHTML = names.map((f) => {
    const blob = new Blob([files[f]]);
    const u = URL.createObjectURL(blob);
    urls.push(u);
    const name = f.split('/').pop();
    const about = (ABOUT.find(([re]) => re.test(name)) || [, ''])[1];
    return `<li class="${/\.3mf$/.test(name) ? 'main' : ''}"><a href="${u}" download="${E(name)}"><code>${E(name)}</code><small>${E(about)} · ${SIZE(blob.size)}</small></a></li>`;
  }).join('') || '<li class="cfg-faint">No files: the build stopped before writing them.</li>';
  $('params').textContent = r.params || '';
  $('report').textContent = (r.report || '') + (r.error ? `\n${r.error}` : '');
}

// ---------------------------------------------------------------- 3D view
const loader = new STLLoader();
let view = null;
function makeView() {
  const el = $('stage');
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);
  el.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  const place = makeLights(scene);
  const v = { el, renderer, scene, place, group: null, cam: null, controls: null };
  v.draw = () => { if (v.cam) { place(v.cam, v.controls.target); renderer.render(scene, v.cam); } };
  v.resize = () => {
    const W = el.clientWidth, H = el.clientHeight;
    renderer.setSize(W, H, false);
    if (!v.cam) return;
    const a = W / H, hh = Math.max(v.half.h, v.half.w / a);
    const cx = (v.cam.left + v.cam.right) / 2, cy = (v.cam.top + v.cam.bottom) / 2;
    v.cam.left = cx - hh * a; v.cam.right = cx + hh * a; v.cam.top = cy + hh; v.cam.bottom = cy - hh;
    v.cam.updateProjectionMatrix();
    v.draw();
  };
  new ResizeObserver(v.resize).observe(el);
  (function frame() { requestAnimationFrame(frame); v.controls?.update(); })();
  window.addEventListener('themechange', v.draw);
  return v;
}
const COLORS = ['#3b74d4', '#e07b2a', '#2f9e6e', '#8a63d2'];
function showParts(files) {
  const stls = Object.keys(files).filter((f) => /^print\/.*_print\.stl$/.test(f)).sort((a, b) => files[b].byteLength - files[a].byteLength);
  if (!stls.length) return;
  $('empty').hidden = true;
  view ||= makeView();
  if (view.group) { view.scene.remove(view.group); view.group.traverse((o) => { o.geometry?.dispose(); o.material?.dispose(); }); }
  const group = new THREE.Group();
  let x = 0;
  stls.forEach((f, i) => {
    const g = loader.parse(files[f].slice(0));
    g.computeBoundingBox();
    const b = g.boundingBox;
    g.translate(x - b.min.x, -(b.min.y + b.max.y) / 2, -b.min.z);   // side by side along x, on the bed
    x += b.max.x - b.min.x + 30;
    g.computeVertexNormals();
    group.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: COLORS[i % COLORS.length], roughness: 0.6,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, side: THREE.DoubleSide })));
    group.add(new THREE.LineSegments(new THREE.EdgesGeometry(g, 28),
      new THREE.LineBasicMaterial({ color: '#1c2430', transparent: true, opacity: 0.45 })));
  });
  view.group = group;
  view.scene.add(group);
  const box = new THREE.Box3().setFromObject(group);
  const { cam, target } = fitCamera(box, [-0.9, -1.6, 1.1], [0, 0, 1], view.el.clientWidth, view.el.clientHeight, { pad: 1.2 });
  view.cam = cam;
  view.half = { w: (cam.right - cam.left) / 2, h: (cam.top - cam.bottom) / 2 };
  view.controls?.dispose();
  view.controls = new OrbitControls(cam, view.renderer.domElement);
  view.controls.target.copy(target);
  view.controls.enableDamping = true;
  view.controls.addEventListener('change', view.draw);
  view.resize();
}
