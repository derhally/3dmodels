# The catalog's HTML: a home page with every model, a page per collection and
# a page per part. Styles and scripts are in web/assets.
import html
import json
from pathlib import Path

from core import REPO, SITE

E = html.escape

ICON = {  # inline SVG icons (stroke = currentColor)
    "cube": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8 20.5 7.5v9L12 21.2 3.5 16.5v-9z"/><path d="M3.8 7.6 12 12.2l8.2-4.6M12 12.2V21"/></svg>',
    "github": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "search": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    "download": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
    "cube3d": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8 20.5 7.5v9L12 21.2 3.5 16.5v-9z"/><path d="M3.8 7.6 12 12.2l8.2-4.6M12 12.2V21"/></svg>',
}

# Set the theme before the page draws, so a dark-mode visitor never sees a white flash.
THEME_JS = ("<script>try{var t=localStorage.getItem('catalog-theme');"
            "if(t)document.documentElement.dataset.theme=t}catch(e){}</script>")


def slug(s):
    return s.replace(" ", "-")


class Site:
    def __init__(self, cfg, colls, built, info):
        self.cfg, self.colls, self.built, self.info = cfg, colls, built, info
        self.repo, self.branch = cfg["repo"], cfg["branch"]

    # helpers ---------------------------------------------------------------
    def entry(self, coll, part):
        return self.built.get(f'{coll["id"]}/{part["id"]}', {})

    def images(self, coll, part):
        """[(path relative to the collection folder, caption)]"""
        if part.get("image"):
            return [("img/" + Path(part["image"]).name, part["name"])]
        return [tuple(i) for i in self.entry(coll, part).get("images", [])]

    def thumb(self, coll, part, up=""):
        imgs = self.images(coll, part)
        src = self.entry(coll, part).get("thumb") or (imgs[0][0] if imgs else "")
        return f'{up}{coll["id"]}/{src}' if src else ""

    def file_url(self, path, raw=False):
        return f'{self.repo}/{"raw" if raw else "blob"}/{self.branch}/{path}'

    def chip(self, status):
        return f'<span class="chip s-{slug(status)}">{E(status)}</span>'

    def page(self, title, body, depth, desc="", scripts=""):
        up = "../" * depth
        nav = "".join(f'<a href="{up}{c["id"]}/index.html">{E(c["name"])}</a>' for c in self.colls)
        sha = self.info["sha"]
        commit = (f' from <a href="{self.repo}/commit/{sha}"><code>{sha[:7]}</code></a>' if sha else "")
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc or self.cfg['tagline'])}">
{THEME_JS}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="{up}assets/site.css">
<link rel="icon" href="{up}assets/icon.svg" type="image/svg+xml">
<script type="importmap">{{"imports": {{"three": "{up or "./"}vendor/three/three.module.min.js"}}}}</script>
</head>
<body>
<header class="top"><div class="wrap bar">
<a class="brand" href="{up}index.html"><span class="mark">{ICON["cube"]}</span><span>{E(self.cfg["title"])}</span></a>
<nav class="cols">{nav}</nav>
<span class="spacer"></span>
<a class="iconbtn" href="{self.repo}" aria-label="Repository on GitHub" title="Repository on GitHub">{ICON["github"]}</a>
<button class="iconbtn" id="theme" type="button" aria-label="Switch light or dark" title="Switch light or dark"><span class="i-moon">{ICON["moon"]}</span><span class="i-sun">{ICON["sun"]}</span></button>
</div></header>
<main>
{body}
</main>
<footer class="foot"><div class="wrap">
<span>Built {E(self.info["date"])}{commit} by <code>catalog/build.py</code>. Renders are of the current model files.</span>
<a href="{self.repo}">{E(self.repo.split("github.com/")[-1])}</a>
</div></footer>
<script type="module" src="{up}assets/catalog.js"></script>
{scripts}
</body>
</html>
"""

    def card(self, coll, part, up="", show_coll=False):
        src = self.thumb(coll, part, up)
        img = f'<img src="{E(src)}" alt="" loading="lazy">' if src else f'<span class="noimg">{ICON["cube"]}</span>'
        text = " ".join([part["name"], part.get("summary", ""), part.get("was", ""), coll["name"], part["status"]]).lower()
        eyebrow = f'<span class="eyebrow">{E(coll["name"])}</span>' if show_coll else ""
        return f"""<a class="card" href="{up}{coll["id"]}/{part["id"]}.html" data-coll="{coll["id"]}" data-status="{slug(part["status"])}" data-text="{E(text)}">
<div class="thumb">{img}{self.chip(part["status"])}</div>
<div class="body">{eyebrow}<h3>{E(part["name"])}</h3><p>{E(part.get("summary", ""))}</p></div></a>"""

    # pages -------------------------------------------------------------------
    def home(self):
        parts = [(c, p) for c in self.colls for p in c["parts"] if p.get("kind") != "reference"]
        tested = sum(1 for _, p in parts if p["status"] in ("print-tested", "printed"))
        art = []
        for ref in self.cfg.get("hero", []):                # "collection/part"
            cid, pid = ref.split("/")
            art += [self.thumb(c, p) for c in self.colls if c["id"] == cid for p in c["parts"] if p["id"] == pid]
        art = "".join(f'<img class="a{i}" src="{E(a)}" alt="">' for i, a in enumerate(a for a in art[:3] if a))
        cols = "".join(f"""<a class="coll" href="{c["id"]}/index.html">
<div class="cover">{f'<img src="{E(t)}" alt="" loading="lazy">' if (t := self.thumb(c, next((p for p in c["parts"] if p["id"] == c.get("cover")), c["parts"][0]))) else ""}</div>
<div class="body"><span class="eyebrow">{len([p for p in c["parts"] if p.get("kind") != "reference"])} models</span>
<h3>{E(c["name"])}</h3><p>{E(c.get("tagline", ""))}</p><span class="more">Open the collection {ICON["arrow"]}</span></div></a>"""
                       for c in self.colls)
        filt = '<button type="button" class="pill" data-coll="" aria-pressed="true">All</button>' + "".join(
            f'<button type="button" class="pill" data-coll="{c["id"]}" aria-pressed="false">{E(c["name"])}</button>' for c in self.colls)
        statuses = list(dict.fromkeys(p["status"] for _, p in parts))
        sfilt = "".join(f'<button type="button" class="pill small" data-status="{slug(s)}" aria-pressed="false">{E(s)}</button>' for s in statuses)
        cards = "".join(self.card(c, p, show_coll=True) for c, p in parts)
        body = f"""<section class="hero"><div class="wrap hero-grid">
<div class="hero-text">
<span class="eyebrow">{E(self.repo.split("github.com/")[-1])}</span>
<h1>{E(self.cfg["title"])}<span class="dot">.</span></h1>
<p class="tag">{E(self.cfg["tagline"])}</p>
<p class="lede">{E(self.cfg["intro"])}</p>
<div class="stats"><div><b>{len(parts)}</b><span>models</span></div><div><b>{len(self.colls)}</b><span>collections</span></div><div><b>{tested}</b><span>print-tested</span></div></div>
<a class="cta" href="#models">Browse the models {ICON["arrow"]}</a>
</div>
<div class="hero-art" aria-hidden="true">{art}</div>
</div></section>
<section class="wrap"><h2 class="sec">Collections</h2><div class="colls">{cols}</div></section>
<section class="wrap" id="models">
<div class="toolbar">
<h2 class="sec">All models</h2>
<label class="search">{ICON["search"]}<input id="q" type="search" placeholder="Search models" autocomplete="off"></label>
</div>
<div class="filters" id="fc">{filt}</div>
<div class="filters" id="fs">{sfilt}</div>
<div class="grid" id="cards">{cards}</div>
<p class="empty" id="empty" hidden>No models match.</p>
</section>"""
        return self.page(self.cfg["title"], body, 0)

    def collection(self, coll):
        out = []
        for cat in coll["categories"]:
            parts = [p for p in coll["parts"] if p["category"] == cat["id"]]
            if not parts:
                continue
            out.append(f'<section class="cat" id="{cat["id"]}"><div class="cat-head"><h2>{E(cat["name"])}</h2>'
                       f'<p>{E(cat.get("blurb", ""))}</p></div>')
            if cat.get("table"):
                keys = cat["table"]
                was = any(p.get("was") for p in parts)
                head = "".join(f"<th>{E(k)}</th>" for k in keys) + ("<th>Was called</th>" if was else "")
                rows = "".join(f'<tr><td><a href="{p["id"]}.html">{E(p["name"])}</a></td>'
                               + "".join(f'<td>{E(str(p.get("specs", {}).get(k, "")))}</td>' for k in keys)
                               + (f'<td>{E(p.get("was", ""))}</td>' if was else "") + "</tr>" for p in parts)
                out.append(f'<div class="scroll tablecard"><table class="names"><tr><th>Name</th>{head}</tr>{rows}</table></div>')
            out.append('<div class="grid">' + "".join(self.card(coll, p, up="../") for p in parts) + "</div></section>")
        jump = "".join(f'<a href="#{c["id"]}">{E(c["name"])}</a>' for c in coll["categories"]
                       if any(p["category"] == c["id"] for p in coll["parts"]))
        count = len([p for p in coll["parts"] if p.get("kind") != "reference"])
        body = f"""<section class="hero small"><div class="wrap">
<div class="crumbs"><a href="../index.html">{E(self.cfg["title"])}</a><span>/</span>{E(coll["name"])}</div>
<h1>{E(coll["name"])}</h1>
<p class="lede">{E(coll.get("intro", ""))}</p>
<div class="jump"><span class="count">{count} models</span>{jump}</div>
</div></section>
<div class="wrap">{"".join(out)}</div>"""
        return self.page(f'{coll["name"]} · {self.cfg["title"]}', body, 1, desc=coll.get("tagline", ""))

    def part(self, coll, part):
        imgs = self.images(coll, part)
        viewer = self.entry(coll, part).get("viewer")
        thumbs = "".join(f'<button type="button" data-src="{E(s)}" data-caption="{E(c)}" aria-pressed="{str(i == 0).lower()}">'
                         f'<img src="{E(s)}" alt=""></button>' for i, (s, c) in enumerate(imgs))
        if viewer:
            thumbs += (f'<button type="button" class="three" data-caption="3D view: drag to turn it, scroll to zoom" '
                       f'aria-pressed="false">{ICON["cube3d"]}<span>3D</span></button>')
        first = imgs[0] if imgs else ("", "")
        specs = "".join(f"<div><dt>{E(k)}</dt><dd>{E(str(v))}</dd></div>" for k, v in part.get("specs", {}).items())
        dl = part.get("downloads", [])
        names = [Path(f).name for f in dl]

        def file_row(f):
            p = Path(f)
            ext = p.suffix.lstrip(".").upper()
            label = "/".join(p.parts[-2:]) if names.count(p.name) > 1 else p.name
            size = (REPO / f).stat().st_size if (REPO / f).exists() else 0
            size = f"{size / 1e6:.1f} MB" if size >= 1e6 else f"{max(1, round(size / 1e3))} kB"
            return (f'<li><a href="{self.file_url(f, raw=not f.endswith((".md", ".yaml")))}"><span class="ext e-{ext.lower()}">{E(ext)}</span>'
                    f'<span class="fname">{E(label)}</span><span class="size">{size}</span>{ICON["download"]}</a></li>')

        files = "".join(file_row(f) for f in dl)
        src = part.get("folder")
        cat = next((c for c in coll["categories"] if c["id"] == part["category"]), None)
        sec = lambda t, b: f'<section class="fact"><h3>{t}</h3>{b}</section>' if b else ""
        was = f'<p class="note">Was called: {E(part["was"])}.</p>' if part.get("was") else ""
        how = part.get("how") or ""
        siblings = [p for p in coll["parts"] if p["category"] == part["category"] and p["id"] != part["id"]]
        more = ("<section class=\"wrap related\"><h2 class=\"sec\">More in " + E(cat["name"] if cat else coll["name"]) + "</h2>"
                '<div class="grid">' + "".join(self.card(coll, p, up="../") for p in siblings[:4]) + "</div></section>") if siblings else ""
        parts_json = E(json.dumps(viewer or []))
        body = f"""<section class="wrap partpage">
<div class="crumbs"><a href="../index.html">{E(self.cfg["title"])}</a><span>/</span><a href="index.html">{E(coll["name"])}</a>{f'<span>/</span><a href="index.html#{cat["id"]}">{E(cat["name"])}</a>' if cat else ""}</div>
<div class="part-head"><h1>{E(part["name"])}</h1>{self.chip(part["status"])}</div>
<p class="lede">{E(part.get("summary", ""))}</p>
<div class="part">
<div class="gallery">
<div class="stage" id="stage" data-parts="{parts_json}" data-view="{E(json.dumps(self.entry(coll, part).get("view", [0.8, 1.6, 0.9])))}">
{f'<img class="shot" src="{E(first[0])}" alt="{E(first[1])}">' if first[0] else '<div class="shot noimg"></div>'}
<div class="caption">{E(first[1])}</div>
</div>
<div class="thumbs">{thumbs if len(imgs) > 1 or viewer else ""}</div>
</div>
<aside class="facts">
{sec("How it works", (f"<p>{E(how)}</p>" if how else "") + was)}
{sec("Specs", f"<dl>{specs}</dl>" if specs else "")}
{sec("Printing", f'<p>{E(part["print"])}</p>' if part.get("print") else "")}
{sec("Files", f'<ul class="files">{files}</ul>' if files else "")}
{f'<p class="note">Source: <a href="{self.repo}/tree/{self.branch}/{src}">{E(src)}/</a></p>' if src else ""}
</aside>
</div>
</section>
{more}"""
        script = '<script type="module" src="../assets/viewer.js"></script>' if imgs or viewer else ""
        return self.page(f'{part["name"]} · {coll["name"]}', body, 1, desc=part.get("summary", ""), scripts=script)

    def write(self):
        for coll in self.colls:
            root = SITE / coll["id"]
            root.mkdir(parents=True, exist_ok=True)
            for part in coll["parts"]:
                if part.get("image"):
                    dst = root / "img" / Path(part["image"]).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes((REPO / part["image"]).read_bytes())
                (root / f'{part["id"]}.html').write_text(self.part(coll, part), encoding="utf-8")
            (root / "index.html").write_text(self.collection(coll), encoding="utf-8")
        (SITE / "index.html").write_text(self.home(), encoding="utf-8")


def write_site(cfg, colls, built, info):
    Site(cfg, colls, built, info).write()
