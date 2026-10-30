"""Runs the configurator on this computer, exactly as the catalog site serves it,
straight from the working tree (edit a builder or options.yaml, reload the page).

    uv run --no-project --python 3.12 --with build123d --with pyyaml python configurator/serve.py

Then open http://127.0.0.1:8765/configurator/ (it opens by itself). The page
needs the internet once per browser for the CAD engine (Pyodide, OCP.wasm),
which the browser then keeps in its cache. Stop with Ctrl+C.
"""
import http.server
import json
import sys
import webbrowser
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "catalog"))
sys.path.insert(0, str(HERE))
import build as catalog  # noqa: E402  (the catalog's build.py: its config and page frame)
import publish  # noqa: E402

PORT = next((int(a) for a in sys.argv[1:] if a.isdigit()), 8765)
TYPES = {".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".json": "application/json",
         ".html": "text/html; charset=utf-8", ".svg": "image/svg+xml", ".yaml": "text/plain; charset=utf-8",
         ".py": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8"}   # not the Windows registry's guesses
COLLS = catalog.load_collections()


class Handler(http.server.BaseHTTPRequestHandler):
    def send(self, body, ctype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def file(self, path):
        if not path.is_file():
            return self.send(b"not found", "text/plain", 404)
        self.send(path.read_bytes(), TYPES.get(path.suffix.lower(), "application/octet-stream"))

    def do_GET(self):
        p = unquote(urlparse(self.path).path)
        if p in ("/", "/configurator", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/configurator/")
            return self.end_headers()
        if p in ("/configurator/", "/configurator/index.html"):
            site = catalog.pages.Site(catalog.CFG, COLLS, {}, catalog.build_info())
            return self.send(site.configurator().encode("utf-8"), TYPES[".html"])
        if p == "/configurator/src/manifest.json":
            return self.send(json.dumps(publish.manifest()).encode(), TYPES[".json"])
        if p.startswith("/configurator/src/"):
            rel = p[len("/configurator/src/"):]
            if rel not in publish.manifest():             # only what the builders read
                return self.send(b"not served", "text/plain", 404)
            return self.file(REPO / rel)
        if p.startswith("/configurator/"):
            rel = p[len("/configurator/"):]
            return self.file(HERE / rel) if rel in publish.STATIC else self.send(b"not found", "text/plain", 404)
        if p.startswith(("/assets/", "/vendor/")):
            return self.file((REPO / "catalog" / "web" / p.lstrip("/")).resolve())
        self.send(b"not found", "text/plain", 404)

    def log_message(self, fmt, *args):
        if args and str(args[1]) not in ("200", "302"):
            sys.stderr.write("%s\n" % (fmt % args))


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/configurator/"
    print(f"Omniwall configurator at {url} (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
