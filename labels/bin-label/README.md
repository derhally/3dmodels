# Front labels

Label plates with black text inlaid flush in a white face, so a label sits
flat in its holder. Each size in `sizes:` in [params.yaml](params.yaml) is one
holder:

| Size | Plate | Text margin (sides, top/bottom) | Holder |
|---|---|---|---|
| `bin` | 34.7 × 10.85 × 0.9 mm | 1.2, 1.2 mm | the bins' front label pocket |
| `arc-drawer` | 34.7 × 10.85 × 0.9 mm | 2.2, 1.2 mm | the U holder on the [Omniwall arc drawer](../../omniwall/arc-drawer/README.md)'s face |

The arc drawer's holder was sized for the bin plate, so both plates are the
same. The holder's side rails wrap 1.5 mm over each edge, though, so the
`arc-drawer` size keeps the text 2.2 mm from the sides: clear of the rails
even when the label sits 0.15 mm to one side in its slot. Nothing covers the
top or bottom edge.

## Making labels

1. Add the text to `labels:` in [params.yaml](params.yaml), one entry per label:
   plain text for a bin label (`- WAGO 221-2`), or
   `- {text: M3 SCREWS, size: arc-drawer}` for the drawer.
2. Run `python build.py` with build123d and PyYAML installed, for example
   `uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py`.

The text is sized automatically: Arial Bold, as large as fits inside the
size's margins and no taller than 6.5 mm, centred on the plate. Long text gets
smaller; `WAGO 221-3` comes out about 32.3 mm wide on a bin label and 30.3 mm
on a drawer label. The text is cut 0.4 mm (two layers) into the face, leaving
0.5 mm of white behind it.

## Outputs

`<name>` is the text in lower case with dashes, plus `-arc-drawer` for drawer
labels (`m3-screws-arc-drawer`).

| File | What |
|---|---|
| `step/<name>.step` | Plate and text as two bodies, face up |
| `print/labels.3mf` | Bambu Studio project: every label on one plate, plate and text on the filament slots set in `params.yaml` |
| `print/<name>.3mf` | One label, two objects |
| `print/<name>-plate.stl`, `print/<name>-text.stl` | One label, as separate meshes |

## Printing

Print face down (that's how the print files are oriented, so the text reads
mirrored in the slicer), on a smooth plate if you want a smooth face. The plate prints
with filament 2 (white) and the text with filament 1 (black); change `filament:` in
`params.yaml` if your AMS slots differ. The colour change happens only in
the first two layers. PLA or PETG at 0.2 mm layers; no supports needed.

A drawer label drops into its holder from above, face out.
