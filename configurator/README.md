# Omniwall configurator

A page on the catalog site ("Build your own") where you pick an Omniwall part
(tool bin, lean bin, tray or arc drawer), set its width, height, depth and
insert, and build it in the browser. It runs the builders' own `build.py`
through build123d on [OCP.wasm](https://github.com/yeicor/OCP.wasm)
(OpenCascade compiled to WebAssembly, in Pyodide), so you get the same parts,
the same checks and the same Bambu Studio 3MF (H2C settings) as a build on your
computer. Nothing is pre-built and no server is needed.

## How a choice becomes a model

- `options.yaml` lists what the page offers per type and what each choice
  writes into a size folder's `params.yaml` (such as `bin: {cells: 4}`). The
  builder's shared `params.yaml` supplies everything else, as it does for the
  size folders on main.
- `configure.py` writes that size folder (`<builder>/configured/`, git-ignored)
  and runs the builder's `build.py` on it.
- `checks.py` grades the build's `report.txt`: valid solids, no face flatter
  than 45 degrees, hooks fit, the insert snaps in, the lean bin stands, the
  drawer moves freely. A failed check says not to print it.

Back channels: every builder takes a `channels` count (`bin`, `tray` or `unit`
in params.yaml; null = one pocket at every seam, as on main). `pocket_columns` in
`omniwall/hook_geometry.py` keeps both ends and works inward from the edges,
adding the middle seam for an odd count. 5, 7 and 9 cells have no middle seam,
so they take even counts only (Zeid: no lopsided layouts). Fewer channels add
`_<n>ch` to the file names.

To offer a new choice, add it to `options.yaml`. When it needs geometry the
builder can't make yet, add a switch to the builder's params (as
`grid.seats` and `grid.include` were added to the tool and lean bins).

## Files

| File | What it does |
|---|---|
| `options.yaml` | types, fields, choices, and the params each choice sets |
| `configure.py` | choices to a size folder; builds it with the builder's `build.py` |
| `checks.py` | grades `report.txt` |
| `page.html`, `app.js`, `app.css` | the page; `catalog/pages.py` puts it in the site's frame |
| `worker.js` | the CAD engine in a Web Worker: Pyodide, build123d, the builder files |
| `vendor/bootstrap.py` | OCP.wasm's installer for build123d in Pyodide (MIT) |
| `publish.py` | copies the page and the builder files into the catalog site |
| `serve.py` | runs the page locally, from the working tree |
| `build_one.py` | builds one configuration in plain Python |
| `test_page.py` | builds a few configurations in headless Edge and saves the 3MFs (into `test-prints/`) |

## Run it locally

From the repo root:

    uv run --no-project --python 3.12 --with build123d --with pyyaml python configurator/serve.py

It opens http://127.0.0.1:8765/configurator/. The browser downloads the CAD
engine once (Pyodide and about 25 MB of OpenCascade) and caches it.

To build one configuration without a browser:

    uv run --no-project --python 3.12 --with build123d --with pyyaml python configurator/build_one.py tool-bin cells=4 rows=3 depth=80 insert=hex

## Ranges

Every range in `options.yaml` was built natively (2026-10-30): tool bins 2 to
6 cells, 2 to 8 rows, 40 to 150 deep (the lower tall front needs 60 deep: the
S-curve sides fail below that); lean bins 3 to 6 cells, 3 to 6 rows, 60 to 100
deep (55 fails a fillet); trays 2 to 6 cells, 40 to 150 deep; arc drawers 2 to
5 cells, 2 to 5 rows, 45 to 150 deep. Sizes that aren't on main
are not print-tested; the page says so.
