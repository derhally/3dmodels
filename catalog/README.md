# Model catalog

A static website with every model in this repo: renders, a 3D view you can
turn, specs, printing notes and download links. It is built into `_site/`
(git-ignored) by [build.py](build.py), and the
[Model catalog workflow](../.github/workflows/catalog.yml) rebuilds and
publishes it with GitHub Pages whenever model files, catalog text or this code
change on `main`.

## Where the content comes from

- **Collections.** Every `catalog.yaml` in the repo is one collection, with its
  own text, colours and parts: [omniwall/catalog/catalog.yaml](../omniwall/catalog/catalog.yaml)
  and [waveshare-esp32-p4-wifi6-touch-lcd-7b/catalog.yaml](../waveshare-esp32-p4-wifi6-touch-lcd-7b/catalog.yaml).
  [site.yaml](site.yaml) has the home page's text and the collections' order.
- **New models show up on their own.** Any folder with STEP files in `step/` or
  print files in `print/` that no catalog.yaml names gets a page anyway: the
  name and summary come from its README's heading and first paragraph, the
  renders from its assembly STEP and print STLs. It is listed under its
  collection's "More" heading if a collection `covers` its folder, otherwise
  under "More models". Give it a catalog.yaml entry for proper text.
- **Renders.** Parts with `kind: assembly` get the generic renders in
  [generic.py](generic.py): front, back, side, cut in half, extra states, and
  the print parts laid out on the bed. Solids are coloured by their STEP label
  through the collection's `colors`. A collection can add its own kinds in a
  `renderers` module, as Omniwall does for hooks, drawers and labels
  ([omniwall/catalog/renderers.py](../omniwall/catalog/renderers.py)).

## Adding a part

Add an entry under `parts:` in the collection's catalog.yaml:

```yaml
  - id: my-part                 # page name
    kind: assembly              # or a kind from the collection's renderers
    category: stands            # one of the collection's categories
    name: My part
    folder: path/to/model       # repo-relative; the renders read its step/ and print/
    status: design              # design, test print, print-tested, ready to print
    summary: One or two sentences for the card.
    how: How it works, for the part page.
    specs: {Size: 100 × 50 × 20 mm}
    print: Orientation, material, supports.
    downloads: [path/to/model/step/model_assembly.step]
```

`assembly`, `front`, `states`, `prints` and `section` fine-tune the generic
renders (see the top of [generic.py](generic.py)). A new collection is a new
catalog.yaml with a `collection:` block (`id`, `name`, `tagline`, `intro`,
`cover`, `covers`).

## Building it yourself

From the repo root:

```
uv run --no-project --python 3.12 --with build123d --with pyyaml --with playwright python catalog/build.py
```

The renders use three.js in a headless browser: Edge or Chrome if installed,
or the browser named by `CATALOG_CHROMIUM`. Arguments narrow it down: `pages`
rewrites the pages only (after editing text), and collection or part ids
re-render just those (`python catalog/build.py omniwall nightstand`).

To look at the site, serve it (the 3D view doesn't load from `file://`):
`python -m http.server -d _site` and open http://localhost:8000/.

## Publishing

The workflow needs GitHub Pages set to deploy from **GitHub Actions**
(Settings → Pages → Source). On a private repository Pages needs a paid plan,
so the workflow only publishes there when the repository variable
`CATALOG_PAGES` is `true`; otherwise it still builds the site and attaches it
to the run as the `github-pages` artifact. Download links on the site point
at the files on GitHub, so in a private repo they only work when signed in.
