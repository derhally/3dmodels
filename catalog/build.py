# Builds the model catalog: a static site of every model in the repo, in _site/.
# From the repo root:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml --with playwright python catalog/build.py
# It finds every catalog.yaml in the repo (one per collection of models), adds
# any model folder none of them names, renders each part's stills with three.js
# in a headless browser, writes the meshes for the 3D view, and writes the
# pages. The browser is Edge or Chrome where installed, or the Chromium at
# CATALOG_CHROMIUM. Arguments: `pages` rewrites the pages only (after editing
# text); collection or part ids re-render only those.
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import CACHE, HERE, REPO, SITE, Ctx, Renderer, rel  # noqa: E402
import generic  # noqa: E402
import pages  # noqa: E402

CFG = yaml.safe_load((HERE / "site.yaml").read_text(encoding="utf-8"))
BUILT = CACHE / "built.json"            # what the last renders made, for `pages` runs


def skipped(name):
    return name in CFG["skip"] or name.startswith(tuple(CFG["skip_prefix"]))


def model_folders():
    """Repo-relative folders holding model files: STEP files in step/ or print
    files in print/."""
    found = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = sorted(d for d in dirs if not skipped(d))
        here = Path(root)
        step, prnt = here / "step", here / "print"
        if (step.is_dir() and any(step.glob("*.step"))) or (prnt.is_dir() and any(prnt.glob("*.[s3][tm][lf]"))):
            found.append(rel(here))
    return found


def plain(md):
    """Markdown to plain text: links, emphasis and code marks dropped."""
    md = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", md)
    return re.sub(r"[*_`]", "", md).strip()


def readme_part(folder):
    """A page for a model folder no catalog.yaml names, from its README."""
    path = REPO / folder
    name, summary = path.name.replace("-", " ").capitalize(), ""
    readme = path / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        m = re.search(r"^# (.+)$", text, re.M)
        name = plain(m.group(1)) if m else name
        for para in re.split(r"\n\s*\n", text[m.end() if m else 0:]):
            para = para.strip()
            if para and not para.startswith(("#", "|", "```", "-", "*", ">", "<")):
                summary = plain(" ".join(para.split()))
                break
    downloads = [rel(f) for f in [generic.find_assembly(path)] if f]
    downloads += [rel(f) for f in sorted((path / "print").glob("*.3mf"))] if (path / "print").is_dir() else []
    downloads += [rel(readme)] if readme.exists() else []
    return dict(id=re.sub(r"[^a-z0-9]+", "-", folder.lower()).strip("-"), kind="assembly", category="more",
                name=name, folder=folder, status="new", summary=summary or f"Model files in {folder}/.",
                how=summary, downloads=downloads, auto=True)


def load_collections():
    colls = []
    for y in sorted(REPO.glob("**/catalog.yaml")):
        if any(skipped(p) for p in y.relative_to(REPO).parts[:-1]):
            continue
        d = yaml.safe_load(y.read_text(encoding="utf-8"))
        c = dict(d["collection"], yaml=y, categories=d.get("categories", []),
                 parts=d.get("parts", []), colors=d.get("colors", {}))
        colls.append(c)
    named = {p["folder"] for c in colls for p in c["parts"] if p.get("folder")}
    for folder in model_folders():
        if folder in named:
            continue
        owner = next((c for c in colls if any(folder == cv or folder.startswith(cv + "/") for cv in c.get("covers", []))), None)
        if owner is None:
            owner = next((c for c in colls if c["id"] == CFG["more"]["id"]), None)
            if owner is None:
                owner = dict(CFG["more"], yaml=None, categories=[], parts=[], colors={})
                colls.append(owner)
        if not any(cat["id"] == "more" for cat in owner["categories"]):
            owner["categories"].append(dict(id="more", name="More", blurb="Models without a catalog entry yet."))
        owner["parts"].append(readme_part(folder))
        print("no catalog entry, listed from its README:", folder)
    order = CFG["order"]
    colls.sort(key=lambda c: (order.index(c["id"]) if c["id"] in order else len(order), c["name"]))
    return colls


def renderers(coll):
    """kind -> render function: generic ones plus the collection's own."""
    fns = {"assembly": generic.assembly}
    if coll.get("renderers"):
        path = coll["yaml"].parent / coll["renderers"]
        spec = importlib.util.spec_from_file_location(f"renderers_{coll['id'].replace('-', '_')}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fns.update(mod.RENDERERS)
    return fns


def site_entry(ctx, out):
    """A render result with paths relative to the collection's folder in the
    site; viewer meshes from elsewhere in the repo are copied into it."""
    root = ctx.root

    def in_site(p):
        p = Path(p).resolve()
        if root.resolve() not in p.parents:
            dst = ctx.model(p.name)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dst)
            p = dst.resolve()
        return p.relative_to(root.resolve()).as_posix()

    entry = {"images": [(in_site(p), c) for p, c in out["images"]],
             "viewer": [dict(v, stl=in_site(v["stl"])) for v in out["viewer"]]}
    if out.get("view"):                         # where the 3D view's camera starts
        entry["view"] = out["view"]
    if out.get("thumb"):                        # the picture on the part's card, if not the first
        entry["thumb"] = in_site(out["thumb"])
    return entry


def render(colls, only):
    built = json.loads(BUILT.read_text()) if BUILT.exists() else {}
    with Renderer() as r:
        for coll in colls:
            fns = renderers(coll)
            for part in coll["parts"]:
                if only and coll["id"] not in only and part["id"] not in only:
                    continue
                fn = fns.get(part.get("kind"))
                if fn is None:                      # reference pages: a picture from the repo
                    continue
                print(f'{coll["name"]}: {part["name"]}')
                ctx = Ctx(coll, part, coll["colors"])
                for old in (ctx.img(""), ctx.model("")):
                    shutil.rmtree(old, ignore_errors=True)
                built[f'{coll["id"]}/{part["id"]}'] = site_entry(ctx, fn(r, ctx))
    BUILT.parent.mkdir(parents=True, exist_ok=True)
    BUILT.write_text(json.dumps(built, indent=1))
    return built


def build_info():
    sha = os.environ.get("GITHUB_SHA")
    if not sha:
        try:
            sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        except OSError:
            sha = ""
    return dict(sha=sha, date=datetime.now(timezone.utc).strftime("%Y-%m-%d"))


def main(args):
    colls = load_collections()
    if "pages" in args:
        built = json.loads(BUILT.read_text()) if BUILT.exists() else {}
    else:
        built = render(colls, set(args))
    shutil.copytree(HERE / "web", SITE, dirs_exist_ok=True)
    (SITE / ".nojekyll").write_text("")
    pages.write_site(CFG, colls, built, build_info())
    print("site written to", rel(SITE))


if __name__ == "__main__":
    main(sys.argv[1:])
