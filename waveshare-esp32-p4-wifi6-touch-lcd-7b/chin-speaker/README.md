# Chin-speaker variant

The speaker sits in the chin under the screen, behind a slotted grille on the
45° face, so it fires up and forward at you. 186 W × 136 D × 137 H mm.

See the [device README](../README.md) for the shared facade, display mounting,
USB-C port and how the files were made.

## Files

| File | What |
|---|---|
| `print/p4_7b_bambu_project.3mf` | Bambu Studio project: front plate, body, and clamp tabs on separate plates (laid out for a 330 × 320 mm bed) |
| `print/p4_7b_front_plate_print.*` | Front plate, facade on the bed |
| `print/p4_7b_body_print.*` | Body, standing on its floor |
| `print/p4_7b_clamp_tabs_print.*` | All four clamp tabs, flat |
| `test-prints/p4_7b_facade_test_frame.*` (built locally, not in git) | Quick print of the facade: window, bevel and a shallow glass pocket. Drop the glass in from behind to check the fit and that the window sits evenly over the screen |
| `step/p4_7b_enclosure_assembly.step` | Assembled, with stand-ins for the display, speaker and port |
| `step/p4_7b_enclosure_only.step` | Just the printed parts, assembled |

## Hardware

| Qty | Part | Used for |
|---|---|---|
| 1 | Waveshare ESP32-P4-WIFI6-Touch-LCD-7B | The display |
| 1 | Box speaker 100 × 45 × 20.75 mm, four Ø6.2 mm corner ears 10 mm behind the cone face | Audio, into the board's PH2.0 `SPK` header (lead ~12 cm) |
| 1 | Flanged panel-mount USB-C connector: 25.2 × 8.2 mm flange, two Ø2.5 mm holes at 17 mm, socket 1.3 mm proud of the flange | Power and data port in the back wall, two screws from outside |
| 1 | Right-angle USB-C cable with flat ribbon | Board's middle `USB` port, spliced to the socket's four wires |
| 4 | M2.5 × 6 screw | Clamp tabs into the display's standoffs |
| 8 | M3 × 8 pan-head screw | 4 clamp tabs into the plate's columns, 4 speaker ears onto their standoffs |
| 4 | M3 × 8 countersunk (90°) screw | Front plate to body, through the side walls |
| 4 | M3 washer, 7 mm OD or larger (9 mm fender washer preferred) | Under the speaker-ear screws, bridging the 6.2 mm ear holes |
| 4 | Rubber foot, 10 mm (optional) | Recesses in the base |

## Printing

| Part | Orientation | Supports |
|---|---|---|
| Front plate | Facade on the bed | None |
| Body | On its floor | None |
| Clamp tabs | Flat | None |

PLA or PETG, 0.2 mm layers, 3+ walls. Black plate filament hides the 0.5 mm of
black glass that shows around the screen.

## Assembly

1. Fit the speaker into the ring on the back of the plate, cones toward the
   grille. Each ear drops over a standoff spigot; fix it with an M3 × 8 and washer.
2. Lay the plate face-down and set the display into the pocket from behind. At
   each corner, a clamp tab goes across the standoff and the column next to it:
   M2.5 × 6 into the standoff, M3 × 8 through the slot into the column.
3. Plug the speaker into the `SPK` header at the top of the board.
4. Set the USB-C connector's flange into the pocket inside the back wall and fit
   its two screws from outside. Splice its four wires (V, D−, D+, G) to the right-angle cable and
   plug that into the board's middle `USB` port, ribbon pointing back. Never plug
   the socket's PH2.0 plug into the board's 4-pin headers.
5. Lower the plate into the body; its top cap lands on the back wall, with the
   rib just inside it. Fit the four M3 countersunk screws through the side walls.

## Notes

- The power switch and the RESET/BOOT buttons end up inside. Leave the switch on.
- For a cable pass-through instead of the port, set `usb_port.enabled: false`
  and `usb_notch.enabled: true` in `params.yaml`.
