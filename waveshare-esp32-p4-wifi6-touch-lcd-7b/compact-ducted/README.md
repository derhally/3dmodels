# Compact ducted variant

The speaker stands upright at the back of the base, cones facing forward. A
printed duct carries its sound forward under the display to a slot grille in
the front lip. With no chin, the screen sits low and the frame is an even
16.3 mm all round. 188 W × 95 D × 111 H mm.

See the [device README](../README.md) for the shared facade, display mounting,
USB-C port and how the files were made.

## Files

| File | What |
|---|---|
| `print/p4_7b_compact_bambu_project.3mf` | Bambu Studio project: front plate, body, and duct + clamp tabs on separate plates (laid out for a 330 × 320 mm bed) |
| `print/p4_7b_compact_front_plate_print.*` | Front plate, facade on the bed |
| `print/p4_7b_compact_body_print.*` | Body, standing on its floor |
| `print/p4_7b_compact_duct_print.*` | Duct, mouth on the bed, speaker standoffs up |
| `print/p4_7b_compact_clamp_tabs_print.*` | All four clamp tabs, flat |
| `print/p4_7b_facade_test_frame.*` | Quick print of the facade: window, bevel and a shallow glass pocket. Drop the glass in from behind to check the fit and that the window sits evenly over the screen |
| `step/p4_7b_compact_assembly.step` | Assembled, with stand-ins for the display, speaker and port |
| `step/p4_7b_compact_enclosure_only.step` | Just the printed parts, assembled |

## How the duct works

- The speaker's face seals against the duct's rear rim, which overlaps the edge
  of the speaker face by 1 mm. Its corner ears sit on four standoffs at the
  duct's rear corners, located by spigots in the ear holes.
- The duct runs forward along the floor. Its roof slopes down at 35° to pass
  1 mm under the display's lowest point, then levels out to a 98 × 14 mm mouth.
  35° is gentler than the 45° screen, so the roof stays clear of the display and
  leans only 35° when printed. `duct.roof_angle` in `params.yaml` sets it.
- The mouth butts against the inside of the front lip, behind 17 vertical slots.
- Sound never enters the rest of the enclosure. That keeps the case from
  buzzing and keeps the speaker away from the mics.

## Hardware

| Qty | Part | Used for |
|---|---|---|
| 1 | Waveshare ESP32-P4-WIFI6-Touch-LCD-7B | The display |
| 1 | Box speaker 100 × 45 × 20.75 mm, four Ø6.2 mm corner ears 10 mm behind the cone face | Audio, into the board's PH2.0 `SPK` header (lead ~10 cm) |
| 1 | Snap-in panel USB-C socket, 14.1 × 5.75 mm panel cutout, 4 wires (V, D−, D+, G) to a PH2.0 plug | Power and data in the back wall, no screws |
| 1 | Right-angle USB-C cable with flat ribbon | Board's middle `USB` port, spliced to the socket's four wires |
| 4 | M2.5 × 6 screw | Clamp tabs into the display's standoffs |
| 12 | M3 × 8 pan-head screw | 4 clamp tabs into the plate's columns, 4 speaker ears onto the duct's standoffs, 4 duct lugs into the floor bosses |
| 4 | M3 × 8 countersunk (90°) screw | Front plate to body, through the side walls |
| 4 | M3 washer, 7 mm OD or larger (9 mm fender washer preferred) | Under the speaker-ear screws, bridging the 6.2 mm ear holes |
| 4 | Rubber foot, 10 mm (optional) | Recesses in the base |

## Printing

| Part | Orientation | Supports |
|---|---|---|
| Front plate | Facade on the bed | None |
| Body | On its floor | None |
| Duct | Mouth on the bed (as exported) | None. The widest wall leans 35°, and the standoffs and lugs grow from the bed or the duct wall |
| Clamp tabs | Flat | None |

PLA or PETG, 0.2 mm layers, 3+ walls.

## Assembly

1. Screw the speaker onto the duct: cones against the rim, each ear over a
   standoff spigot, M3 × 8 and washer from behind.
2. Set the duct in the body with its mouth against the front lip and screw its
   four lugs to the floor bosses (M3 × 8).
3. Push the USB-C socket into the cutout in the back wall from outside until its
   clips snap.
4. Lay the plate face-down and set the display into the pocket from behind. At
   each corner, a clamp tab goes across the standoff and the column beside it:
   M2.5 × 6 into the standoff, M3 × 8 into the column.
5. Plug the speaker into the `SPK` header. Splice the socket's four wires
   (V, D−, D+, G) to the right-angle cable and plug that into the board's middle
   `USB` port. Never plug the socket's PH2.0 plug into the board's 4-pin headers.
6. Lower the plate into the body; its top cap lands on the back wall, with the
   rib just inside it. Fit the four M3 countersunk screws through the side walls.

## Notes

- The front lip is 25.7 mm tall to fit the 14 mm duct mouth under the display.
  `duct.mouth_h` in `params.yaml` trades mouth size against overall height:
  roughly 1 mm of height per 1 mm of mouth.
