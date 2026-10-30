// The configurator's CAD engine, in a Web Worker so the page stays responsive:
// Pyodide (Python in WebAssembly), build123d on OCP.wasm (OpenCascade in
// WebAssembly), and the repo's own builder files in Pyodide's file system.
// Messages in:  {cmd: "init", engine: {pyodide, build123d}}
//               {cmd: "build", id, kind, values}
// Messages out: {type: "status", text, step, of} while loading,
//               {type: "ready", seconds}, {type: "log", text},
//               {type: "built", id, result, files: {path: ArrayBuffer}},
//               {type: "error", id, text}
let py = null;
const ROOT = "/repo";
const post = (m, transfer) => self.postMessage(m, transfer || []);
const t0 = performance.now();
const secs = () => ((performance.now() - t0) / 1000).toFixed(1);

async function init(engine) {
  const of = 5;
  post({ type: "status", text: "Loading Python", step: 1, of });
  // Pyodide 314 runs only in a module worker (app.js starts this one with type "module")
  const { loadPyodide } = await import(`https://cdn.jsdelivr.net/pyodide/v${engine.pyodide}/full/pyodide.mjs`);
  py = await loadPyodide();
  py.setStdout({ batched: (s) => post({ type: "log", text: s }) });
  py.setStderr({ batched: (s) => post({ type: "log", text: s }) });

  post({ type: "status", text: "Downloading the CAD kernel (about 25 MB, cached after the first visit)", step: 2, of });
  await py.loadPackage("micropip");
  py.FS.mkdirTree("/engine");
  py.FS.writeFile("/engine/bootstrap.py", await (await fetch("vendor/bootstrap.py")).text());
  await py.runPythonAsync(`
import os, sys
if not hasattr(os, "geteuid"):            # platformdirs (via build123d) asks for it; Pyodide has getuid only
    os.geteuid = os.getuid
sys.path.insert(0, "/engine")
import bootstrap
await bootstrap.bootstrap(${JSON.stringify(engine.build123d)})
import micropip
await micropip.install("pyyaml")
`);

  post({ type: "status", text: "Starting build123d", step: 3, of });
  await py.runPythonAsync("import build123d");

  post({ type: "status", text: "Copying the builders", step: 4, of });
  const files = await (await fetch("src/manifest.json")).json();
  await Promise.all(files.map(async (p) => {
    const r = await fetch("src/" + p.split("/").map(encodeURIComponent).join("/"));
    if (!r.ok) throw new Error(`could not fetch ${p} (${r.status})`);
    const dst = `${ROOT}/${p}`;
    py.FS.mkdirTree(dst.slice(0, dst.lastIndexOf("/")));
    py.FS.writeFile(dst, new Uint8Array(await r.arrayBuffer()));
  }));

  post({ type: "status", text: "Ready", step: 5, of });
  await py.runPythonAsync(`
import sys
sys.path.insert(0, "${ROOT}/configurator")
import configure
`);
  post({ type: "ready", seconds: +secs(), files: files.length });
}

// what the page offers for download: the print files and the assembly
const WANT = /^(print\/.*\.(3mf|stl)|step\/.*_assembly\.step|params\.yaml|report\.txt)$/;

async function build(msg) {
  const t = performance.now();
  py.globals.set("_kind", msg.kind);
  py.globals.set("_values", JSON.stringify(msg.values));
  const result = JSON.parse(await py.runPythonAsync(`configure.build_json("${ROOT}", _kind, _values)`));
  result.seconds = +((performance.now() - t) / 1000).toFixed(1);
  const files = {}, transfer = [];
  for (const rel of Object.keys(result.files)) {
    if (!WANT.test(rel)) continue;
    const bytes = py.FS.readFile(`${result.folder}/${rel}`);
    files[rel] = bytes.buffer;
    transfer.push(bytes.buffer);
  }
  post({ type: "built", id: msg.id, result, files }, transfer);
}

self.onmessage = async (e) => {
  const msg = e.data;
  try {
    if (msg.cmd === "init") await init(msg.engine);
    else if (msg.cmd === "build") await build(msg);
  } catch (err) {
    post({ type: "error", id: msg.id, text: String(err && err.message || err) });
  }
};
