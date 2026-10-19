# Omniwall parts catalog

A static website listing every Omniwall part with renders, a 3D view, specs,
printing notes and download links. It is generated into [`docs/`](../../docs/)
so GitHub Pages can serve it (Settings → Pages → Deploy from a branch, `main`,
folder `/docs`).

- [catalog.yaml](catalog.yaml): the text on each page (names, what it is, how it
  works, specs, printing, files). Edit this to change the wording or add a part.
- [build_catalog.py](build_catalog.py): makes the site. It reads each part's
  STEP and STL files, writes web meshes to `docs/omniwall/models/`, renders
  stills to `docs/omniwall/img/` and writes the pages.
- [render.html](render.html): the page the renders are drawn in. It uses
  `docs/assets/scene.js`, the same lights and materials as the 3D view on the
  site, so stills and 3D view look alike.

## Rebuilding

Build the parts first (`hook/build_hooks.py`, `arc-drawer/build.py` per size,
`labels/bin-label/build.py`), then from this folder:

```
uv run --no-project --python 3.12 --with build123d --with pyyaml --with playwright python build_catalog.py
```

The renders use three.js in a headless browser: Edge or Chrome if installed,
or the Chromium named by `CATALOG_CHROMIUM`. Arguments narrow it down:
`pages` rewrites the pages only (after editing catalog.yaml), and `hook`,
`drawer` or `label` re-render only those parts.

To look at the site locally, serve `docs/` (the 3D view doesn't load from
`file://`): `python -m http.server -d docs` and open
http://localhost:8000/omniwall/.

## Adding a part

Add an entry under `parts:` in catalog.yaml with `kind` (`hook`, `drawer`,
`label`, or `reference` for a page with one picture), `category`, `name`,
`status` and the text fields, then rebuild. A new kind of part needs a
render function in build_catalog.py, like `hooks()` or `drawers()`.
