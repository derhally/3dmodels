# Compact ducted variant

The speaker stands upright in the base behind the screen, cone facing forward. A
printed duct carries its sound forward under the display to a slot grille in
the front lip. With no chin, the screen sits low and the frame is an even
16.3 mm all round. 188 W × 83 D × 122 H mm.

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
| `test-prints/p4_7b_facade_test_frame.*` (built locally, not in git) | Quick print of the facade: window, bevel and a shallow glass pocket. Drop the glass in from behind to check the fit and that the window sits evenly over the screen |
| `step/p4_7b_compact_assembly.step` | Assembled, with stand-ins for the display, speaker and port |
| `step/p4_7b_compact_enclosure_only.step` | Just the printed parts, assembled |

## How the duct works

- The speaker's face seals against the duct's rear rim, which overlaps the edge
  of the speaker face by 1 mm. Its two ears sit on two standoffs beside the
  duct, each joined to the duct's side wall by a web. The standoffs run the
  full length of the duct, so they grow from the bed when it is printed
  mouth-down.
- The duct is 26 mm wide inside and runs forward along the floor. Its roof
  slopes down at 45° to pass 1 mm under the display's lowest point and 0.5 mm
  under the front plate's lower back edge, then levels out to a 26 × 14 mm
  mouth. 45° is gentler than the 55° screen, so the roof stays clear of the
  display, and it is the lean of the duct's widest wall when printed. It also
  keeps the duct short: the speaker sits forward and leaves 11 mm between its
  back and the USB-C connector in the middle of the back wall, for the
  connector's ribbon to bend. `duct.roof_angle` in `params.yaml` sets it.
- The mouth butts against the inside of the front lip, behind 5 vertical slots.
- Sound never enters the rest of the enclosure. That keeps the case from
  buzzing and keeps the speaker away from the mics.

## Hardware

| Qty | Part | Used for |
|---|---|---|
| 1 | Waveshare ESP32-P4-WIFI6-Touch-LCD-7B | The display |
| 1 | Enclosed speaker 28 × 31 × 15 mm, 4 Ω 3 W, JST-PH2.0 plug ([Amazon, pack of 4](https://www.amazon.com/dp/B0FN7G4ZMC)), one cone, two side ears with Ø2.2 mm holes 36.75 mm apart, 6.65 mm behind the speaker face | Audio, into the board's PH2.0 `SPK` header |
| 1 | Flanged panel-mount USB-C connector: 25.2 × 8.2 mm flange, two Ø2.5 mm holes at 17 mm, socket 1.3 mm proud of the flange | Power and data port in the back wall, two screws from outside |
| 1 | Right-angle USB-C cable with flat ribbon | Board's middle `USB` port, spliced to the socket's four wires |
| 4 | M2.5 × 6 screw | Clamp tabs into the display's standoffs |
| 8 | M3 × 8 pan-head screw | 4 clamp tabs into the plate's columns, 4 duct lugs into the floor bosses |
| 4 | M3 × 8 countersunk (90°) screw | Front plate to body, through the side walls |
| 2 | M2 × 6 self-tapping screw | Speaker ears onto the duct's standoffs, from behind |
| 4 | Rubber foot, 10 mm (optional) | Recesses in the base |

## Printing

| Part | Orientation | Supports |
|---|---|---|
| Front plate | Facade on the bed | None |
| Body | On its floor | None |
| Duct | Mouth on the bed (as exported) | None. The widest wall leans 45°, and the standoffs and lugs grow from the bed or the duct wall |
| Clamp tabs | Flat | None |

PLA or PETG, 0.2 mm layers, 3+ walls.

## Assembly

1. Screw the speaker onto the duct: face against the rim, each ear on its
   standoff, an M2 × 6 through each ear from behind.
2. Set the duct in the body with its mouth against the front lip and screw its
   four lugs to the floor bosses (M3 × 8).
3. Set the USB-C connector's flange into the pocket inside the back wall and fit
   its two screws from outside.
4. Lay the plate face-down and set the display into the pocket from behind. At
   each corner, a clamp tab goes across the standoff and the column beside it:
   M2.5 × 6 into the standoff, M3 × 8 into the column.
5. Plug the speaker into the `SPK` header. Splice the socket's four wires
   (V, D−, D+, G) to the right-angle cable and plug that into the board's middle
   `USB` port. Never plug the socket's PH2.0 plug into the board's 4-pin headers.
6. Lower the plate into the body; its top cap lands on the back wall, with the
   rib just inside it. Fit the four M3 countersunk screws through the side walls.

## Notes

- The front lip is 23.3 mm tall to fit the 14 mm duct mouth under the front
  plate's lower edge. `duct.mouth_h` in `params.yaml` trades mouth size against
  overall height: roughly 1 mm of height per 1 mm of mouth.
- The speaker ears take M2 × 6 self-tapping screws into Ø1.6 mm pilots in the
  standoffs. This fit hasn't been confirmed by a print yet.
