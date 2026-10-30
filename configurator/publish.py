"""The configurator's files for the catalog site (catalog/build.py) and the
local test server (serve.py): the page's own scripts, and a copy of the repo
files the builders read, under src/, with src/manifest.json listing them."""
import json
import shutil
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
STATIC = ["app.js", "app.css", "worker.js", "vendor/bootstrap.py", "vendor/LICENSE-OCP.wasm.txt"]


def manifest():
    """repo-relative paths of every file the builders read, as the browser gets them"""
    opts = yaml.safe_load((HERE / "options.yaml").read_text(encoding="utf-8"))
    globs = list(opts["files"])
    for t in opts["types"].values():
        globs += [f"{t['builder']}/*.py", f"{t['builder']}/params.yaml"]
    return sorted({p.relative_to(REPO).as_posix() for g in globs for p in REPO.glob(g) if p.is_file()})


def write(out):
    """copies the configurator into out (the site's configurator/ folder); the
    page itself (index.html) comes from catalog/pages.py"""
    out = Path(out)
    for f in STATIC:
        (out / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / f, out / f)
    files = manifest()
    for f in files:
        (out / "src" / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / f, out / "src" / f)
    (out / "src" / "manifest.json").write_text(json.dumps(files), encoding="utf-8")
    return len(files)
