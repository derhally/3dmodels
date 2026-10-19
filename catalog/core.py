# Shared pieces of the model catalog: paths, meshes, the headless renderer and
# the per-part context that a collection's render functions get.
import base64
import os
import struct
from pathlib import Path

from build123d import Compound, export_stl, import_step

HERE = Path(__file__).resolve().parent     # catalog/
REPO = HERE.parent
SITE = REPO / "_site"                     # the generated site (git-ignored)
CACHE = HERE / "cache"                    # meshes only the renders use (git-ignored)


def rel(path):
    """Repo-relative POSIX path."""
    return Path(path).resolve().relative_to(REPO).as_posix()


def write_mesh(shape, path, tol=0.02):
    path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(shape, str(path), tolerance=tol, angular_tolerance=0.2)
    return path


def stl_bounds(path):
    """(min, max) corners of a binary STL, without loading it as a shape."""
    data = Path(path).read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * n:
        raise ValueError(f"{path} is not a binary STL")
    lo, hi = [float("inf")] * 3, [float("-inf")] * 3
    for i in range(n):
        v = struct.unpack_from("<9f", data, 84 + 50 * i + 12)
        for k in range(9):
            a = k % 3
            lo[a], hi[a] = min(lo[a], v[k]), max(hi[a], v[k])
    return lo, hi


def labelled_solids(step):
    """[(label, solid)] of an assembly STEP, each solid in its assembled place
    (a child on its own lacks the placement, its solids() don't)."""
    out = []
    for c in import_step(str(step)).children or []:
        labels = [d.label for d in c.children] if c.children else [c.label]
        sols = c.solids()
        if len(labels) != len(sols):
            labels = [c.label] * len(sols)
        out += list(zip(labels, sols))
    return out


def merged(solids):
    return solids[0] if len(solids) == 1 else Compound(children=solids)


class Renderer:
    """three.js stills in a headless browser. The repo is served at
    http://catalog.local/ so render.html can load the site's scene.js and the
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
        self.page.goto(self.ORIGIN + "catalog/render.html")
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


class Ctx:
    """Where one part's files go. Images and 3D-view meshes go in the site under
    <collection>/img/<part>/ and <collection>/models/<part>/; meshes only the
    renders need go in the cache."""

    def __init__(self, coll, part, colors):
        self.coll, self.part, self.colors = coll, part, colors
        self.root = SITE / coll["id"]
        self.folder = REPO / part["folder"] if part.get("folder") else None

    def img(self, name):
        return self.root / "img" / self.part["id"] / name

    def model(self, name):
        return self.root / "models" / self.part["id"] / name

    def shared(self, name):
        return self.root / "models" / "_shared" / name

    def cache(self, name):
        return CACHE / self.coll["id"] / self.part["id"] / name
