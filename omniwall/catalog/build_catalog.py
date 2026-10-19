# Builds the Omniwall parts catalog, a static site for GitHub Pages in ../../docs.
# Run it from this folder:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml --with playwright python build_catalog.py
# It reads the parts' STEP and STL files (build them first with each part's own
# build script), writes web meshes for the 3D viewer to docs/omniwall/models/,
# renders stills with three.js in a headless browser to docs/omniwall/img/, and
# writes the pages from catalog.yaml. The browser is Edge or Chrome where
# installed (Windows), or the Chromium at CATALOG_CHROMIUM / Playwright's own.
# `python build_catalog.py pages` rewrites the pages only, without meshes or renders.
import base64
import copy
import html
import json
import os
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

HERE = Path(__file__).resolve().parent
OW = HERE.parent                       # omniwall/
REPO = OW.parent
DOCS = REPO / "docs"
SITE = DOCS / "omniwall"
CACHE = HERE / "cache"                 # meshes only the renders use (git-ignored)
CAT = yaml.safe_load((HERE / "catalog.yaml").read_text(encoding="utf-8"))
panel = yaml.safe_load((OW / "panel.yaml").read_text())
P, SL = panel["pitch"], panel["slot"]
COL = CAT["colors"]


def rel(path):
    """Repo-relative POSIX path."""
    return Path(path).resolve().relative_to(REPO).as_posix()


def write_mesh(shape, path, tol=0.02):
    path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(shape, str(path), tolerance=tol, angular_tolerance=0.2)
    return path


# Panel stand-in: 18 ga steel with the slot and peg-hole grid. A vertical slot
# column is centred on x = cx, one of its slots has its bottom edge at z = zs, and
# the panel's front face is at y = yf (it runs back to yf - thickness).
def panel_sheet(cx, zs, yf, x0, x1, z0, z1):
    t, w, L = panel["panel"]["thickness"], SL["width"], SL["length"]
    yc = yf - t / 2
    sheet = Pos((x0 + x1) / 2, yc, (z0 + z1) / 2) * Box(x1 - x0, t, z1 - z0)
    cuts = []
    n0, n1 = int((x0 - cx) // P) - 1, int((x1 - cx) // P) + 2
    m0, m1 = int((z0 - zs) // P) - 1, int((z1 - zs) // P) + 2
    for n in range(n0, n1):
        for m in range(m0, m1):
            x, z = cx + n * P, zs + m * P
            cuts.append(Pos(x, yc, z + L / 2) * Box(w, 2 * t, L))                  # vertical slot
            cuts.append(Pos(x + P / 2, yc, z + L / 2 + P / 2) * Box(L, 2 * t, w))  # horizontal slot
            cuts.append(Pos(x + P / 2, yc, z + L / 2) * Rot(X=90) * Cylinder(panel["peg_hole"]["diameter"] / 2, 2 * t))
    return sheet - Compound(children=cuts)


class Renderer:
    """three.js stills in a headless browser. The repo is served at
    http://catalog.local/ so render.html can load docs/assets/scene.js and the
    meshes; nothing goes over the network."""
    ORIGIN = "http://catalog.local/"
    TYPES = {".html": "text/html", ".js": "text/javascript", ".stl": "model/stl", ".json": "application/json"}

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        args = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
        exe = os.environ.get("CATALOG_CHROMIUM")
        tries = [dict(executable_path=exe)] if exe else [dict(channel="msedge"), dict(channel="chrome"), {}]
        for kw in tries:
            try:
                self.browser = self.pw.chromium.launch(args=args, **kw)
                break
            except Exception as e:  # browser not installed: try the next one
                err = e
        else:
            raise RuntimeError(f"no browser for rendering (set CATALOG_CHROMIUM): {err}")
        self.page = self.browser.new_page()
        self.page.on("console", lambda m: m.type == "error" and print("  browser:", m.text))
        self.page.route(self.ORIGIN + "**", self._serve)
        self.page.goto(self.ORIGIN + "omniwall/catalog/render.html")
        self.page.wait_for_function("window.rendererReady === true")
        return self

    def _serve(self, route):
        path = REPO / route.request.url[len(self.ORIGIN):].split("?")[0]
        if path.is_file():
            route.fulfill(body=path.read_bytes(), content_type=self.TYPES.get(path.suffix, "application/octet-stream"))
        else:
            route.fulfill(status=404, body="not found")

    def __exit__(self, *exc):
        self.browser.close()
        self.pw.stop()

    def shot(self, out, parts, **view):
        """Render parts ([{stl: Path, color, ...}]) to the PNG `out`."""
        spec = dict(view, parts=[dict(p, stl="/" + rel(p["stl"])) for p in parts])
        url = self.page.evaluate("s => window.renderShot(s)", spec)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(url.split(",", 1)[1]))
        print("  rendered", rel(out))
        return out


def hooks(r, built):
    """Each hook: alone, cut away on the panel, side profile on the panel, as printed."""
    cx, yf = panel["dovetail_mount"]["dovetail"]["block_width"] / 2, panel["slot_hook_1u"]["panel_front_y"]
    z0, z1 = -P - 16, SL["length"] + 16                           # two slots of one column, a little more
    shared = SITE / "models" / "panel"
    piece = write_mesh(panel_sheet(cx, 0, yf, cx - 0.9 * P, cx + 0.9 * P, z0, z1), shared / "hook_panel.stl")
    strip = write_mesh(panel_sheet(cx, 0, yf, cx - 1.4, cx + 1.4, z0, z1), CACHE / "hook_panel_strip.stl")
    steel = dict(color=COL["panel"], metalness=0.15, roughness=0.5)
    for part in CAT["parts"]:
        if part.get("kind") != "hook":
            continue
        pid, stem = part["id"], part["file"]
        print(part["name"])
        mdir, idir = SITE / "models" / pid, SITE / "img" / pid
        hook = write_mesh(import_step(str(OW / "hook" / "step" / f"{stem}.step")), mdir / f"{stem}.stl")
        flat = OW / "hook" / "print" / f"{stem}.stl"
        blue = dict(stl=hook, color=COL["hook"])
        frame = dict(center=[cx, 5.5, -4.5], halfHeight=27)        # every hook at the same scale
        imgs = [
            (r.shot(idir / "hook.png", [blue], w=640, h=800, view=[1, 1.3, 0.7], **frame), "The hook: dovetail front on the right, finger and foot on the left go through the panel"),
            # see-through: the front covers the slot exactly, so solid it hides which steel it grips
            (r.shot(idir / "front.png", [dict(blue, opacity=0.45), dict(stl=piece, **steel)], w=640, h=800, view=[0.7, 1.6, 0.8], **frame),
             "On the panel, from the front, the hook drawn see-through so the steel behind it shows. Objects slide down onto the dovetail"),
            (r.shot(idir / "back.png", [blue, dict(stl=piece, **steel)], w=640, h=800, view=[0.7, -1.6, 0.6], **frame), "From behind the panel"),
            (r.shot(idir / "side.png", [blue, dict(stl=strip, **steel)], w=640, h=800, view=[1, 0, 0], **frame), "Side view: wall on the left, steel in grey"),
            (r.shot(idir / "print.png", [dict(stl=flat, color=COL["hook"])], w=800, h=500, view=[0.35, -1, 0.9], pad=1.2), "As printed: on its flat side, no supports"),
        ]
        built[pid] = {
            "images": [(rel(p), c) for p, c in imgs],
            "viewer": [dict(stl=rel(hook), color=COL["hook"]), dict(stl=rel(piece), **steel)],
        }


def solids_by_role(step):
    """{role: [solids]} of an arc drawer assembly STEP: housing, drawer, handle,
    pin, hook. Solids come with their placement (children alone don't have it)."""
    out = {}
    for c in import_step(str(step)).children:
        labels = [d.label for d in c.children] if c.children else [c.label]
        for lab, so in zip(labels, c.solids()):
            role = ("housing" if lab == "housing" else "hook" if lab.startswith("hook") else
                    "handle" if lab == "handle" else "drawer" if lab == "drawer" else "pin")
            out.setdefault(role, []).append(so)
    return out


def drawers(r, built):
    """Each arc drawer size: closed, open and tilted on the panel, the back with
    its hooks, and the print parts laid out."""
    bh = panel["bridge_hook"]
    for part in CAT["parts"]:
        if part.get("kind") != "drawer":
            continue
        pid, folder, prefix = part["id"], REPO / part["folder"], part["prefix"]
        print(part["name"])
        mdir, idir = SITE / "models" / pid, SITE / "img" / pid
        roles = {s: solids_by_role(folder / "step" / f"{prefix}_assembly_{s}.step") for s in ("closed", "open", "tilted")}
        fixed = roles["closed"]
        housing = write_mesh(fixed["housing"][0], mdir / "housing.stl", tol=0.05)
        hooks_ = write_mesh(Compound(children=fixed["hook"]), mdir / "hooks.stl", tol=0.03)
        moving = {}
        for s, rl in roles.items():
            where = mdir if s == "open" else CACHE / pid             # the 3D view shows it open
            moving[s] = [dict(stl=write_mesh(Compound(children=rl[k]), where / f"{k}_{s}.stl", tol=0.05), color=COL[k])
                         for k in ("drawer", "handle", "pin")]
        # The panel behind: the hooks' column and the upper slot they hang from.
        hb = fixed["hook"][0].bounding_box()
        hz = min(h.bounding_box().min.Z for h in fixed["hook"])
        b = fixed["housing"][0].bounding_box()
        sheet = panel_sheet((hb.min.X + hb.max.X) / 2, hz + bh["bar_bottom"], 0.0,
                            b.min.X - 0.75 * P, b.max.X + 0.75 * P, b.min.Z - 0.75 * P, b.max.Z + 0.75 * P)
        pnl = write_mesh(sheet, CACHE / pid / "panel.stl")
        base = [dict(stl=housing, color=COL["housing"]), dict(stl=hooks_, color=COL["hook_on_drawer"])]
        wall = [dict(stl=pnl, color=COL["panel"], metalness=0.15, roughness=0.5, noFit=True)]
        # Print parts side by side, as on the bed.
        layout, x = [], 0.0
        for k in ("housing", "drawer", "handle", "handle_pin"):
            stl = folder / "print" / f"{prefix}_{k}_print.stl"
            bb = import_step(str(stl.with_suffix(".step"))).bounding_box()
            layout.append(dict(stl=stl, color=COL["housing" if k == "housing" else "pin" if k == "handle_pin" else k],
                               offset=[x - bb.min.X, -bb.min.Y, -bb.min.Z]))
            x += bb.size.X + 8
        view = dict(w=1000, h=760, view=[0.75, 1.7, 0.85])
        imgs = [
            (r.shot(idir / "closed.png", base + moving["closed"] + wall, **view), "Closed, on the panel"),
            (r.shot(idir / "open.png", base + moving["open"] + wall, **view), "Pulled out to its stop"),
            (r.shot(idir / "tilted.png", base + moving["tilted"] + wall, w=1000, h=760, view=[1.6, 0.9, 0.45]), "Tilted down 30° at the end of its travel"),
            (r.shot(idir / "back.png", base + moving["closed"], w=1000, h=760, view=[0.8, -1.6, 0.7]), "The back: dovetail pockets on the hooks"),
            (r.shot(idir / "print.png", layout, w=1200, h=600, view=[0.3, -1, 1.1], pad=1.05), "Print parts: housing on its back, drawer upright, scoop, snap pin"),
        ]
        built[pid] = {
            "images": [(rel(p), c) for p, c in imgs],
            "viewer": [dict(stl=rel(p["stl"]), color=p["color"]) for p in base + moving["open"]],
        }


def labels(r, built):
    """Each label in labels/bin-label, face up, white plate and black text."""
    for part in CAT["parts"]:
        if part.get("kind") != "label":
            continue
        pid, src = part["id"], REPO / part["folder"]
        print(part["name"])
        mdir, idir = SITE / "models" / pid, SITE / "img" / pid
        imgs, viewer = [], []
        for step in sorted((src / "step").glob("*.step")):
            bodies = sorted(import_step(str(step)).solids(), key=lambda so: -so.volume)
            plate = write_mesh(bodies[0], mdir / f"{step.stem}-plate.stl", tol=0.01)
            text = write_mesh(Compound(children=bodies[1:]), mdir / f"{step.stem}-text.stl", tol=0.01)
            ps = [dict(stl=plate, color=COL["label_plate"], edgeOpacity=0.25), dict(stl=text, color=COL["label_text"], edges=False)]
            imgs.append((r.shot(idir / f"{step.stem}.png", ps, w=900, h=360, view=[0, -0.4, 1], up=[0, 1, 0], pad=1.08), step.stem))
            if not viewer:
                viewer = [dict(stl=rel(p_["stl"]), color=p_["color"]) for p_ in ps]
        built[pid] = {"images": [(rel(p_), c) for p_, c in imgs], "viewer": viewer}


# Pages ------------------------------------------------------------------------

E = html.escape


def page(title, body, depth=1, scripts=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<link rel="stylesheet" href="{up}assets/site.css">
<script type="importmap">{{"imports": {{"three": "{up}vendor/three/three.module.min.js"}}}}</script>
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">Omniwall parts</a>
<nav>{"".join(f'<a href="index.html#{c["id"]}">{E(c["name"])}</a>' for c in CAT["categories"])}</nav>
</div></header>
<main class="wrap">
{body}
<footer>Generated by <code>omniwall/catalog/build_catalog.py</code> from the parts in
<a href="{CAT["repo"]}">{E(CAT["repo"].split("github.com/")[-1])}</a>. Renders are of the current model files.</footer>
</main>
{scripts}
</body>
</html>
"""


def file_url(path, raw=False):
    return f'{CAT["repo"]}/{"raw" if raw else "blob"}/{CAT["branch"]}/{path}'


def size_text(path):
    n = (REPO / path).stat().st_size
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{max(1, round(n / 1e3))} kB"


def site_path(p):
    """A repo path under docs/omniwall as seen from a page there."""
    return Path(p).relative_to("docs/omniwall").as_posix()


def card(part, built):
    imgs = built.get(part["id"], {}).get("images") or [[part.get("image", ""), ""]]
    src = site_path(imgs[0][0]) if imgs[0][0].startswith("docs/") else "img/" + Path(imgs[0][0]).name
    was = f'<div class="was">Was: {E(part["was"])}</div>' if part.get("was") else ""
    return f"""<a class="card" href="{part["id"]}.html">
<div class="thumb"><img src="{src}" alt="{E(part["name"])}" loading="lazy"></div>
<div class="body"><div class="name">{E(part["name"])}</div>
<span class="chip {part["status"].replace(" ", "-")}">{E(part["status"])}</span>
<div class="sum">{E(part["summary"])}</div>{was}</div></a>"""


def index_page(built):
    body = [f'<h1>{E(CAT["title"])}</h1>', f'<p class="lede">{E(CAT["intro"])}</p>']
    for c in CAT["categories"]:
        parts = [p for p in CAT["parts"] if p["category"] == c["id"]]
        body.append(f'<h2 id="{c["id"]}">{E(c["name"])}</h2><p class="blurb">{E(c["blurb"])}</p>')
        if c["id"] == "hooks":
            rows = "".join(f'<tr><td><a href="{p["id"]}.html">{E(p["name"])}</a></td><td>{E(str(p["specs"]["Slots used"]))}</td>'
                           f'<td>{E(str(p["specs"]["Snap rows"]))}</td><td>{E(p["was"])}</td></tr>' for p in parts)
            body.append(f'<div class="scroll"><table class="names"><tr><th>Name</th><th>Slots used</th><th>Snap rows</th>'
                        f'<th>Was called</th></tr>{rows}</table></div><p></p>')
        body.append('<div class="grid">' + "".join(card(p, built) for p in parts) + "</div>")
    return page(CAT["title"], "\n".join(body))


def part_page(part, built):
    b = built.get(part["id"], {})
    imgs = [(site_path(p), c) for p, c in b.get("images", [])]
    if part.get("image"):                                  # a picture copied from the repo (the panel diagram)
        imgs = [("img/" + Path(part["image"]).name, part["name"])]
    thumbs = "".join(f'<button type="button" data-src="{E(s)}" data-caption="{E(c)}" aria-pressed="{str(i == 0).lower()}">'
                     f'<img src="{E(s)}" alt=""></button>' for i, (s, c) in enumerate(imgs))
    viewer = b.get("viewer")
    if viewer:
        thumbs += ('<button type="button" class="three" data-caption="3D view: drag to turn it" aria-pressed="false">3D</button>')
    parts_json = E(json.dumps([dict(v, stl=site_path(v["stl"])) for v in viewer])) if viewer else "[]"
    specs = "".join(f"<tr><th>{E(k)}</th><td>{E(str(v))}</td></tr>" for k, v in part.get("specs", {}).items())
    names = [Path(f).name for f in part.get("downloads", [])]
    files = "".join(f'<li><a href="{file_url(f, raw=not f.endswith((".md", ".yaml")))}">'
                    f'{E("/".join(Path(f).parts[-2:]) if names.count(Path(f).name) > 1 else Path(f).name)}</a><span>{size_text(f)}</span></li>'
                    for f in part.get("downloads", []))
    src = part.get("folder")
    was = f'<p class="note">Was called: {E(part["was"])}.</p>' if part.get("was") else ""
    body = f"""<div class="crumbs"><a href="index.html">Omniwall parts</a> / <a href="index.html#{part["category"]}">{E(next(c["name"] for c in CAT["categories"] if c["id"] == part["category"]))}</a></div>
<h1>{E(part["name"])}</h1>
<p class="lede">{E(part["summary"])}</p>
<span class="chip {part["status"].replace(" ", "-")}">{E(part["status"])}</span>
<p></p>
<div class="part">
<div>
<div class="stage" id="stage" data-parts="{parts_json}">
<img class="shot" src="{E(imgs[0][0])}" alt="{E(imgs[0][1])}">
<div class="caption">{E(imgs[0][1])}</div>
</div>
<div class="thumbs">{thumbs if len(imgs) > 1 or viewer else ""}</div>
</div>
<div class="facts">
<h3>How it works</h3><p>{E(part["how"])}</p>{was}
<h3>Specs</h3><div class="scroll"><table>{specs}</table></div>
{f'<h3>Printing</h3><p>{E(part["print"])}</p>' if part.get("print") else ""}
<h3>Files</h3><ul class="files">{files}</ul>
{f'<p class="note">Source: <a href="{CAT["repo"]}/tree/{CAT["branch"]}/{src}">{E(src)}/</a> in the repo.</p>' if src else ""}
</div>
</div>"""
    script = '<script type="module" src="../assets/viewer.js"></script>' if imgs else ""
    return page(f'{part["name"]} · {CAT["title"]}', body, scripts=script)


def write_pages(built):
    SITE.mkdir(parents=True, exist_ok=True)
    for part in CAT["parts"]:
        if part.get("image"):
            dst = SITE / "img" / Path(part["image"]).name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((REPO / part["image"]).read_bytes())
        (SITE / f'{part["id"]}.html').write_text(part_page(part, built), encoding="utf-8")
    (SITE / "index.html").write_text(index_page(built), encoding="utf-8")
    (DOCS / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>3D models</title>'
        '<meta http-equiv="refresh" content="0; url=omniwall/index.html">'
        '<a href="omniwall/index.html">Omniwall parts catalog</a>\n', encoding="utf-8")
    (DOCS / ".nojekyll").write_text("")
    print("pages written to", rel(SITE))


if __name__ == "__main__":
    # Arguments: "pages" to only rewrite the pages; or the kinds to re-render
    # (hook, drawer, label), all of them by default.
    args = sys.argv[1:]
    built_file = SITE / "build.json"
    built = json.loads(built_file.read_text()) if built_file.exists() else {}
    if "pages" not in args:
        kinds = args or ["hook", "drawer", "label"]
        with Renderer() as r:
            for kind, fn in (("hook", hooks), ("drawer", drawers), ("label", labels)):
                if kind in kinds:
                    fn(r, built)
        SITE.mkdir(parents=True, exist_ok=True)
        built_file.write_text(json.dumps(built, indent=1))
    write_pages(built)
