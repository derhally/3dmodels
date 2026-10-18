# Waveshare ESP32-P4-WIFI6-Touch-LCD-7B desk enclosures

45° desk stands for the [Waveshare ESP32-P4-WIFI6-Touch-LCD-7B](https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B)
7" touch display, with a 100 × 45 mm speaker and a panel-mount USB-C port in
the back. Two variants share the same front facade, display mounting and port.

| Variant | Size (W × D × H) | Speaker | Printed parts |
|---|---|---|---|
| [chin-speaker](chin-speaker/) | 186 × 136 × 137 mm | In the chin under the screen, firing up and forward through a slotted grille | Front plate, body, 4 clamp tabs |
| [compact-ducted](compact-ducted/) | 188 × 95 × 111 mm | Stands at the back of the base; a duct carries the sound forward to a slot grille in the front lip | Front plate, body, duct, 4 clamp tabs |

The chin version sounds best: the speaker points straight at you. The compact
version is about a third smaller in depth and height; the duct narrows the sound
path to a 14 mm slot, which trims a little treble.

**Build guide:** [build-guide.md](build-guide.md) covers the hardware list, printing,
step-by-step assembly for both variants, and USB-C wiring.
[build-guide.html](build-guide.html) is the same guide with a variant switch, to-scale
side sections and a step checklist. Download it and open it in a browser.

## Shared design

- **Facade.** The display's black glass border is uneven (left 3.06, right
  6.64, top 4.02, bottom 8.73 mm). The front plate covers it with a 1.6 mm skin
  and a window 0.5 mm larger than the visible area, bevelled on its front edge
  and centred in the plate.
- **Display mounting.** The display goes into a pocket from behind, glass
  against the facade. Four printed clamp tabs bridge the board's M2.5 standoffs
  to columns on the plate, so the glass is clamped against the facade.
- **Top cap on the plate.** The roof over the back of the enclosure is part of
  the front plate, not the body. Printed face-down, it rises from the plate's top
  edge at 45°. The body is open-topped, so neither part needs supports. A rib
  under the cap locates it just inside the back wall.
- **Teardrop holes.** Every hole that runs sideways when its part is on the print
  bed is a teardrop, with a 45° point toward print-up, so its roof doesn't droop.
  That covers the side-wall screw holes and countersinks, the plate's side-boss
  pilots and the duct's lug holes. Screws only bear on the round part.
- **USB-C port.** A snap-in panel USB-C socket clips into a 14.1 × 5.75 mm
  rounded cutout (R1.3) in the 2.4 mm back wall, with its oval bezel on the
  outside. It needs no screws. Its four wires (V, D−, D+, G) end in a PH2.0 plug
  and are spliced inside to the right-angle cable that plugs into the board's
  USB-C port. Don't plug that PH2.0 into the board's 4-pin headers: they're
  I2C/UART/CAN/RS485, not USB.
- **Mics.** A 7-hole cluster in the bezel under each of the board's two
  rear-facing MEMS mics.

## Folders

| Folder | Contents |
|---|---|
| `common/` | `common.yaml` (display, speaker, port and shared dimensions) and `enclosure_lib.py` (shared geometry and exporters) |
| `<variant>/print/` | Print-ready parts, `.3mf` / `.stl` / `.step`, plus a Bambu Studio project with one part per plate |
| `<variant>/step/` | Parts in assembled position for CAD, plus an assembly with stand-ins for the display, speaker and port |
| `<variant>/build.py`, `params.yaml` | Generator and the variant's own dimensions |

Regenerate a variant:

```sh
pip install build123d pyyaml
python chin-speaker/build.py
python compact-ducted/build.py
```

A variant's `params.yaml` overrides `common/common.yaml` section by section.

## How these files were made

The models are code, not hand-drawn CAD. They were written in
[build123d](https://build123d.readthedocs.io/), a Python CAD library on the
OpenCascade kernel, so every file is an exact solid (B-rep) and imports into
CAD as editable bodies.

1. **Dimensions.**
   - Display outline, layer depths, mounting holes and edge connectors come from
     Waveshare's dimension drawing (PDF, 2025-11-08). The values were read from
     the PDF's vector data, not by eye.
   - Port, mic and connector positions were cross-checked against Waveshare's
     labelled board photos.
   - Measured on the real hardware with calipers: standoff depth (15 mm), the
     glass border widths, the speaker (size, depth, ear holes and their height),
     the right-angle USB-C plug, and the USB-C socket's panel cutout and panel
     thickness. The socket's other dimensions are from its drawing.
2. **Modelling.** Claude Code wrote the build123d scripts, using a build123d
   MCP server to run and check them; new work uses build123d-mcp. All
   dimensions come from the YAML files; the scripts contain no measurements of
   their own.
3. **Checking.**
   - Every revision was clash-checked against stand-ins for the display, its
     standoffs, the speaker, the USB plug and the port, to confirm no overlaps.
   - Every revision was reviewed by opening the STEP in CAD.
   - The glass pocket was confirmed with a printed test frame. `test-prints/p4_7b_facade_test_frame` (built by `build.py`) checks the facade window the same way.
   - Bambu Studio projects were checked for watertight, outward-facing meshes.
4. **Exports.** The print files are the same solids, rotated into print
   orientation.
