// Part page: the gallery thumbnails swap the main picture, and the "3D" button
// swaps in a three.js view of the part you can turn (drag), zoom (wheel or
// pinch) and pan (right-drag or two fingers).
import * as THREE from 'three';
import { OrbitControls } from '../vendor/three/OrbitControls.js';
import { loadParts, makeLights, fitCamera } from './scene.js';

const stage = document.getElementById('stage');
const img = stage.querySelector('img.shot');
const caption = stage.querySelector('.caption');
const buttons = [...document.querySelectorAll('.thumbs button')];
let viewer = null;

function press(btn) { buttons.forEach(b => b.setAttribute('aria-pressed', String(b === btn))); }

for (const btn of buttons) {
  btn.addEventListener('click', () => {
    press(btn);
    if (btn.classList.contains('three')) { show3d(); caption.textContent = btn.dataset.caption; return; }
    if (viewer) { viewer.el.hidden = true; img.hidden = false; }
    img.src = btn.dataset.src;
    img.alt = btn.dataset.caption;
    caption.textContent = btn.dataset.caption;
  });
}

async function show3d() {
  img.hidden = true;
  if (viewer) { viewer.el.hidden = false; viewer.resize(); return; }
  const el = document.createElement('div');
  el.className = 'viewer';
  el.innerHTML = '<div class="hint">Loading…</div>';
  img.after(el);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0xeef0f3, 1);
  el.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  const { group, box } = await loadParts(JSON.parse(stage.dataset.parts));
  scene.add(group);
  const place = makeLights(scene);
  const W = () => el.clientWidth, H = () => el.clientHeight;
  const { cam, target } = fitCamera(box, [0.8, 1.6, 0.9], [0, 0, 1], W(), H(), { pad: 1.25 });
  const half = { w: (cam.right - cam.left) / 2, h: (cam.top - cam.bottom) / 2 };
  const controls = new OrbitControls(cam, renderer.domElement);
  controls.target.copy(target);
  controls.enableDamping = true;
  const draw = () => { place(cam, controls.target); renderer.render(scene, cam); };
  controls.addEventListener('change', draw);
  const resize = () => {
    renderer.setSize(W(), H(), false);
    const a = W() / H();
    const hh = Math.max(half.h, half.w / a);
    const cx = (cam.left + cam.right) / 2, cy = (cam.top + cam.bottom) / 2;
    cam.left = cx - hh * a; cam.right = cx + hh * a; cam.top = cy + hh; cam.bottom = cy - hh;
    cam.updateProjectionMatrix();
    draw();
  };
  new ResizeObserver(resize).observe(el);
  (function tick() { requestAnimationFrame(tick); if (!el.hidden) controls.update(); })();
  el.querySelector('.hint').textContent = 'Drag to turn · scroll or pinch to zoom · right-drag to pan';
  viewer = { el, resize };
  resize();
}
