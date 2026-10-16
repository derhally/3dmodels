# 3D modeling

Models in this repo are designed in code for 3D printing: Python
[build123d](https://build123d.readthedocs.io/) scripts on the OpenCascade kernel,
run through the `shapr3d` MCP server (`E:\source\shapr3d-mcp`). Shapr3D is used to
review them visually. Everything is exact B-rep geometry, exported as STEP for CAD
and STL/3MF for printing.

## The shapr3d MCP tools

| Tool | Use it to |
|---|---|
| `build123d_guide` | Recall build123d syntax before writing a script |
| `create_model` | Run a build123d script (assigns `result`) and export STEP/STL/3MF/glTF/BREP. Pass `params_file` to feed it a YAML/JSON of dimensions as `params` |
| `modify_model` | Import a file as `imported`, change it in code, re-export. Also used to pull single solids out of an assembly or rotate parts into print orientation |
| `inspect_model` | Size, volume, solids, faces of a STEP/STL/3MF/BREP/IGES file |
| `detect_clash` | Pairwise overlap check between all solids in one or more files |
| `render_preview` | Rough shaded PNG, for a quick sanity check only |
| `convert_model` | Convert between formats |
| `open_in_shapr3d` | Hand a file to Shapr3D for review (see Windows note below) |
| `shapr3d_status`, `activate_shapr3d`, `screenshot_shapr3d` | Check, launch and capture the Shapr3D window |

Scripts run inside the server: never `print()` from a `create_model` or
`modify_model` script (stdout is the MCP transport). Generated files land in
`E:\source\shapr3d-mcp\models`, which is scratch space. Finished designs are
copied into this repo.

**Windows + Shapr3D:** Shapr3D on Windows is a Store app and won't accept STEP
files from other programs. `open_in_shapr3d` brings Shapr3D to the front and
puts the file's path on the clipboard; the user imports it by hand (Import,
Ctrl+V, Enter). Don't try to automate the Import dialog. After they import,
`screenshot_shapr3d` can confirm what they see.

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
   file with the printed parts and run `detect_clash` after every change.
4. **Verify by measuring the output.** After a change, slice or inspect the
   generated part to confirm the dimension you changed: hole sizes, wall
   thickness, positions. Don't rely on reading the code.
5. **Review in Shapr3D.** Send the assembly with `open_in_shapr3d` and let the
   user check it before calling a design done.
6. **Test-print critical fits.** For press fits and windows, export a small,
   quick test print of just that feature before the full part.

## Printer and printing

- **Printer:** Bambu Lab H2C, 330 × 320 mm bed, 325 mm tall. Bambu Studio for
  slicing.
- **Material:** PLA or PETG, 0.2 mm layers, 3+ walls.
- **Export every printed part in its print orientation,** as STEP, STL and 3MF,
  and also a Bambu Studio project with one part per plate. The 3dmodels
  Waveshare library has a working writer (`write_bambu_project` in
  `waveshare-esp32-p4-wifi6-touch-lcd-7b/common/enclosure_lib.py`).
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
- `build.py` scripts regenerate every output file. After a refactor, regenerate
  and compare volumes against the previous files to prove nothing moved.

## Working on this machine (Claude Code)

- Run standalone build scripts with the server's Python:
  `E:\source\shapr3d-mcp\.venv\Scripts\python.exe`. `python3` here is the
  Microsoft Store stub and hangs.
- Put multi-line Python in a script file rather than a shell heredoc.
- Extra tools for one-off jobs: `uv run --no-project --with <package> python ...`
  (for example `pymupdf` for PDFs).
- Commit messages and PRs: no Claude attribution lines. Ask before pushing.
