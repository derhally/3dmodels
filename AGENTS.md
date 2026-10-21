# 3D modeling

Models in this repo are designed in code for 3D printing: Python
[build123d](https://build123d.readthedocs.io/) scripts on the OpenCascade kernel,
built and checked with the **build123d-mcp** MCP server. Everything is exact
B-rep geometry, exported as STEP for CAD and STL/3MF for printing.

## The build123d-mcp tools

The server keeps a live build123d session, so build in small steps and check
each one. All dimensions are in mm.

| Tool | Use it to |
|---|---|
| `session_state`, `reset` | See what's loaded; start a fresh part |
| `execute` | Run build123d code in the session, one feature or boolean per call; `show(part, "name")` registers a part |
| `measure` | Size, volume and face inventory: the source of truth after every boolean (an unchanged face count means it silently failed) |
| `find_holes`, `find_hole_patterns`, `find_bosses`, `find_countersinks` | Confirm features exist where they should |
| `cross_sections`, `render_view` | Look inside (cavities, wall thickness); render only after the numbers agree |
| `compare` | `kind="fit"` for clearance or interference between two parts, `kind="align"` for flush/centred checks, `kind="shape"` to confirm an edit changed only what it should |
| `save_snapshot`, `restore_snapshot` | Undo point before anything risky |
| `validate` | Must pass (one watertight, manifold solid) before export |
| `bank_candidate`, `export` | Write the final STEP (only if it passes the gate); other formats |
| `analyze_printability` | Overhangs, thin walls and bed fit for anything printed |
| `script`, `design_audit` | The session's code as a starting point for the repo script; brittle parameters |

Read the server's `build123d://quickref` resource before writing build code (and
`build123d://skill/modeling` for a new part, `build123d://skill/edit` to change
one). Use `bd_warehouse` for fasteners, threads, gears and bearings.

`execute()` refuses imports of `os`, `sys`, `pathlib` and `yaml`, `open()`, and
any dunder name, so repo `build.py` scripts that read a `params.yaml` don't run
inside it: run them with a plain Python (see "Working on this machine"). Inside
`execute()`, build123d's own `import_step`, `export_stl` and `Mesher` read and
write repo paths. The server's `import_cad_file` and `export` tools have failed
on repo paths; import with `import_step` inside `execute()` instead.

To have the user review a model, give them the full path of the STEP file to
open in their CAD program.

## How to work

1. **Measure first, never guess.** Ask the user for caliper measurements of
   anything the part has to fit. For datasheet drawings in PDF, read the
   dimensions from the PDF's vector data (PyMuPDF) instead of estimating from an
   image. When something has to be assumed, say so and mark it as assumed in
   the params file.
2. **All dimensions in a params file.** The script holds no measurements of its
   own. Give every value a comment saying what it is and where it came from
   (measured, datasheet, assumed).
3. **Model the hardware too.** Build stand-ins for every bought part the design
   has to clear: boards, their tallest components, connectors, cables, speakers,
   screw heads, and clips in their opened position. Put them in an assembly
   file with the printed parts and check every pair for overlap after every
   change (`compare(kind="fit")`, or a loop of intersections in the build script).
4. **Verify by measuring the output.** After a change, slice or inspect the
   generated part to confirm the dimension you changed: hole sizes, wall
   thickness, positions. Don't rely on reading the code.
5. **Let the user review it.** Give them the assembly STEP's full path to open
   in CAD, and let them check it before calling a design done.
6. **Test-print critical fits.** For press fits and windows, export a small,
   quick test print of just that feature before the full part.

## Printer and printing

- **Printer:** Bambu Lab H2C, 330 × 320 mm bed, 325 mm tall. Bambu Studio for
  slicing.
- **Material:** PLA or PETG, 0.2 mm layers. Walls as the Bambu preset (2) unless
  the part needs more; a design that does sets `wall_loops` in its params.yaml
  `print` section.
- **Export every printed part in its print orientation,** as STEP, STL and 3MF,
  and also a Bambu Studio project with one part per plate. Write every 3MF with
  the shared writer (`write_bambu_project` in `bambu/bambu_project.py`) and the
  settings template, so it opens ready to slice (see `bambu/README.md`).
- **No supports.** Nothing facing down may be flatter than 45° from vertical;
  aim for 35° where it costs nothing. Check this numerically on the print-
  orientation part, face by face. Don't trust the eye.
- **Holes that run sideways** when printed are teardrops: a 45° point toward
  print-up.
- **No unsupported roofs.** Split parts so that roofs and caps print as part of
  a piece lying face-down, rather than bridging across a cavity.

## Fit values that have been print-tested

- Press-fit pocket for a glass panel: 0.25 mm clearance per side (0.15 mm on the
  edge it rests on).
- Window over a display: visible area + 0.5 mm per side, 45° bevel on the front.

## Fasteners

- Self-tapping pilot holes in PLA/PETG: M3 → 2.5 mm, M2.5 → 2.1 mm, M2 → 1.6 mm.
  Clearance holes: M3 → 3.4 mm, M2.5 → 2.8 mm.
- Check every screw length against its pilot depth, including plate and washer
  thickness, so it can't bottom out. Prefer one screw length per project; the
  Waveshare enclosure uses M3 × 8 throughout.

## Repo layout

- One folder per device or object, with a README (what it is, hardware list,
  printing, assembly) and, for anything with assembly steps, a build guide.
- Variants of one design share a `common/` folder (shared params and geometry
  library); each variant has its own `params.yaml`, `build.py`, `step/` and
  `print/`.
- Test prints (fit tests, coupons, test frames, probes) go in a `test-prints/`
  folder in the design's folder, never in `print/` or `step/`. Git ignores every
  `test-prints/`, so they stay local and the folder can simply be deleted;
  `build.py` writes them again.
- Every model appears in the model catalog site ([catalog/](catalog/README.md)),
  rebuilt by a GitHub workflow on push. Give a new model an entry in its
  collection's `catalog.yaml` (text, specs, downloads); without one it is
  listed from its README.
- `build.py` scripts regenerate every output file. After a refactor, regenerate
  and compare volumes against the previous files to prove nothing moved.

## Working on this machine (Claude Code)

- Run standalone build scripts with a plain build123d Python:
  `uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py`
  (tested on this machine; build123d 0.13 on Python 3.12). `python3` here is the
  Microsoft Store stub and hangs.
- Put multi-line Python in a script file rather than a shell heredoc.
- Extra tools for one-off jobs: `uv run --no-project --with <package> python ...`
  (for example `pymupdf` for PDFs).
- Commit messages and PRs: no Claude attribution lines. Ask before pushing.
