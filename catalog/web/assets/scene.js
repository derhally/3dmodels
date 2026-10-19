// Shared three.js scene setup for the catalog: the still renders
// (catalog/render.html, run by catalog/build.py) and the 3D viewer on
// each part page use the same materials, edges and lights, so they look alike.
import * as THREE from 'three';
import { STLLoader } from '../vendor/three/STLLoader.js';

const loader = new STLLoader();

// parts: [{stl, color, opacity, edges, noFit, offset}] with stl a URL and
// offset an optional [x, y, z] move (to lay print parts out side by side).
// Returns {group, box}: the meshes and the bounding box of the parts to frame.
export async function loadParts(parts) {
  const group = new THREE.Group();
  const box = new THREE.Box3();
  await Promise.all(parts.map(async (p) => {
    const buf = await (await fetch(p.stl)).arrayBuffer();
    const g = loader.parse(buf);
    if (p.offset) g.translate(...p.offset);
    g.computeVertexNormals();
    const opacity = p.opacity ?? 1;
    const mesh = new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      color: p.color || '#3b74d4', roughness: p.roughness ?? 0.6, metalness: p.metalness ?? 0.0,
      transparent: opacity < 1, opacity, depthWrite: opacity >= 1,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, side: THREE.DoubleSide,
    }));
    group.add(mesh);
    if (p.edges !== false) {
      group.add(new THREE.LineSegments(new THREE.EdgesGeometry(g, p.edgeAngle || 28),
        new THREE.LineBasicMaterial({ color: p.edgeColor || '#1c2430', transparent: true, opacity: p.edgeOpacity ?? 0.45 })));
    }
    if (!p.noFit) { g.computeBoundingBox(); box.union(g.boundingBox); }
  }));
  return { group, box };
}

// Lights that follow the camera: a key light from the upper left, a fill from
// the right and a soft sky/ground light.
export function makeLights(scene) {
  const hemi = new THREE.HemisphereLight(0xffffff, 0x5c6370, 1.15);
  const key = new THREE.DirectionalLight(0xffffff, 2.3);
  const fill = new THREE.DirectionalLight(0xffffff, 0.55);
  scene.add(hemi, key, fill, key.target, fill.target);
  return function place(cam, target) {
    const v = new THREE.Vector3().subVectors(cam.position, target).normalize();
    const up = cam.up.clone().normalize();
    const right = new THREE.Vector3().crossVectors(up, v).normalize();
    key.position.copy(target).add(v).addScaledVector(up, 1.0).addScaledVector(right, -0.6);
    fill.position.copy(target).add(v).addScaledVector(right, 1.0);
    key.target.position.copy(target); fill.target.position.copy(target);
  };
}

// Orthographic camera looking along -view at the box, fitted to a W x H frame.
// opts.center (a point to centre on) and opts.halfHeight (mm) fix the framing
// so a set of renders share one scale.
export function fitCamera(box, view, up, W, H, opts = {}) {
  const ctr = opts.center ? new THREE.Vector3(...opts.center) : box.getCenter(new THREE.Vector3());
  const R = box.getSize(new THREE.Vector3()).length() || 1;
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, -20 * R, 20 * R);
  cam.position.copy(ctr).addScaledVector(new THREE.Vector3(...view).normalize(), 4 * R);
  cam.up.set(...up);
  cam.lookAt(ctr);
  cam.updateMatrixWorld();
  let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
    const p = new THREE.Vector3(x, y, z).applyMatrix4(cam.matrixWorldInverse);
    xmin = Math.min(xmin, p.x); xmax = Math.max(xmax, p.x); ymin = Math.min(ymin, p.y); ymax = Math.max(ymax, p.y);
  }
  const pad = opts.pad ?? 1.1;
  let cx = (xmin + xmax) / 2, cy = (ymin + ymax) / 2;
  if (opts.center) { cx = 0; cy = 0; }
  let hw = (xmax - xmin) / 2 * pad, hh = (ymax - ymin) / 2 * pad;
  if (opts.halfHeight) { hh = opts.halfHeight; hw = hh * W / H; }
  else if (hw / hh > W / H) hh = hw * H / W; else hw = hh * W / H;
  cam.left = cx - hw; cam.right = cx + hw; cam.top = cy + hh; cam.bottom = cy - hh;
  cam.updateProjectionMatrix();
  return { cam, target: ctr };
}
