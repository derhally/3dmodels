# Waveshare ESP32-P4-WIFI6-Touch-LCD-7B desk enclosure

A 45° desk stand for the [Waveshare ESP32-P4-WIFI6-Touch-LCD-7B](https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B)
7" touch display. The glass sits flush in the front plate, a 100 × 45 mm
speaker sits in the chin behind a slotted grille, and the USB-C cable leaves
through a notch at the bottom of the back wall.

Overall size: 186 W × 128 D × 136 H mm. Two printed parts.

## Files

| Folder | Contents |
|---|---|
| `print/` | Print-ready parts in print orientation (`.3mf`, `.stl`, `.step`) |
| `step/` | Parts in assembled position, for viewing or editing in CAD |
| `source/` | Parametric generator (`build_enclosure.py`) and all dimensions (`enclosure.yaml`) |

`step/p4_7b_enclosure_assembly.step` also contains stand-ins for the display,
its standoffs, the speaker and the USB plug, to check fit. `step/p4_7b_enclosure_only.step`
is just the two printed parts.

## Hardware

| Qty | Part | Used for |
|---|---|---|
| 1 | Waveshare ESP32-P4-WIFI6-Touch-LCD-7B | The display |
| 1 | Box speaker, 100 × 45 × 20.75 mm, four Ø6.2 mm corner ears 10 mm behind the cone face, centres 91.2 × 36.2 mm | Audio; plugs into the board's PH2.0 `SPK` header (lead needs ~12 cm) |
| 1 | Right-angle USB-C cable with a flat ribbon (head 11.2 × 7.8 × 3.5 mm, ribbon 5 × 1 mm) | Power and data, into the board's middle `USB` port |
| 4 | M2.5 × 6 screw | Display: through the plate's hook arms into the board's threaded standoffs |
| 4 | M3 × 8 countersunk (90° flat head) screw | Front plate to body, through the side walls |
| 4 | M3 × 12 pan-head screw | Speaker: down through each ear into its standoff |
| 4 | M3 washer, 7 mm OD or larger (9 mm fender washer preferred) | Speaker: clamps the ear; must bridge the 6.2 mm hole |
| 4 | Rubber foot, 10 mm diameter (optional) | Recesses in the base, 1 mm deep |

The M3 screws thread directly into 2.5 mm pilot holes in the plastic.

## Printing

Test the screen cutout first: print `p4_7b_cutout_test_frame` (a few minutes)
face-down and check the glass fits. The triangle marks the bottom edge.

| Part | Orientation | Supports |
|---|---|---|
| `p4_7b_front_plate_print` | Face-down (as exported) | Build-plate only, for the four display hook arms |
| `p4_7b_body_print` | Standing on its floor (as exported) | None |

Both fit a 256 × 256 mm bed. PLA or PETG, 0.2 mm layers, 3+ walls.

## Assembly

1. Fit the speaker into the ring on the back of the plate, cones toward the
   grille. Each ear drops over a standoff spigot; fix it with an M3 × 12 and washer.
2. Drop the display into the plate from the front and fix it from behind with
   the four M2.5 × 6 screws through the hook arms.
3. Plug the speaker into the `SPK` header at the top of the board.
4. Plug the right-angle USB-C into the middle `USB` port (left edge, seen from
   the front) with the ribbon pointing back, and route it to the notch in the
   back wall.
5. Lower the plate into the body and fit the four M3 countersunk screws through
   the side walls.

## Notes

- The power switch and the RESET/BOOT buttons end up inside. Leave the switch
  on; flashing over USB normally doesn't need the buttons.
- The two MEMS mics face into the enclosure. A 7-hole cluster in the bezel under
  each mic gives sound a short path in.
- Screen cutout: 0.25 mm clearance at the top and sides, 0.15 mm at the bottom.
- The back has vertical vent slots near the top.

## How these files were made

The model is code, not hand-drawn CAD. It was written in
[build123d](https://build123d.readthedocs.io/), a Python CAD library on the
OpenCascade kernel, so every file here is an exact solid (B-rep) and imports
into Shapr3D as editable bodies.

1. **Dimensions.**
   - Display outline, layer depths, mounting holes and edge connectors come from
     Waveshare's dimension drawing (PDF, 2025-11-08). The values were read from
     the PDF's vector data, not by eye.
   - Port, mic and connector positions were cross-checked against Waveshare's
     labelled board photos.
   - Measured on the real hardware with calipers: standoff depth (15 mm), the
     speaker (size, depth, ear holes and their height), and the right-angle USB-C
     plug.
2. **Modelling.** Claude Code wrote the build123d script and ran it through
   [shapr3d-mcp](https://github.com/derhally/shapr3d-mcp), an MCP server that
   runs build123d scripts and exports STEP/STL/3MF. All dimensions come from
   `source/enclosure.yaml`; the script contains no measurements of its own.
3. **Checking.**
   - Each revision was clash-checked against stand-ins for the display, its
     standoffs, the speaker and the USB plug, to confirm no overlaps.
   - Each revision was reviewed by importing the STEP into Shapr3D.
   - The screen cutout was confirmed with a printed test frame.
4. **Exports.** The print files are the same solids, rotated into print
   orientation.

`source/build_enclosure.py` is that script as a standalone program. It
regenerates every file in `step/` and `print/`, and its output has the same
volumes as the committed files.

## Changing the design

All dimensions, including the angle, bezels, clearances and speaker size, are in
`source/enclosure.yaml`. Regenerate everything with:

```sh
pip install build123d pyyaml
python source/build_enclosure.py
```

Display dimensions come from Waveshare's dimension drawing (2025-11-08) plus
measurements of the real board (standoff depth 15 mm).
