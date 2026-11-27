# Nightstand stand ("Stem")

A bedside alternative to the 55° desk stands. The display sits in a slim case
on a toothed hinge, upright or leaned back up to 30° in 10° steps. Behind the
screen, a short tower about 60 mm wide holds the speaker lying face up under a
3-slot grille in the tower lid. 188 W × 101 D × 141 H mm upright.

See the [device README](../README.md) for the shared facade, display mounting,
USB-C port and how the files were made.

**Status: not printed yet.** The display and speaker masses in `params.yaml`
are assumed (230 g and 25 g), so the tip numbers below are estimates until
they're weighed. Print the hinge test and the snap test first.

## Files

| File | What |
|---|---|
| `step/p4_7b_nightstand_assembly.step` | Assembled upright, with stand-ins for the display, speaker, gasket, port, USB-C cable, bolt and nut |
| `step/p4_7b_nightstand_assembly_tilt30.step` | The same, case leaned back 30° |
| `step/p4_7b_nightstand_enclosure_only.step` | Just the printed parts, assembled |
| `step/p4_7b_nightstand_<part>.step` | Each printed part in its assembled position |
| `print/p4_7b_nightstand_all_parts.3mf` | Every printed part in one file, laid out side by side (more than one plate's worth: arrange in Bambu Studio) |
| `print/p4_7b_nightstand_<part>_print.*` | Each part in print orientation, `.3mf` / `.stl` / `.step` |
| `test-prints/p4_7b_nightstand_hinge_test.*` (built locally, not in git) | The case bracket, the knob, and the tower lid's knuckle on a small piece of lid: checks the tooth mesh, the bolt, the captured nut and the knob |
| `test-prints/p4_7b_nightstand_snap_test.*` (built locally, not in git) | A corner of the front plate with one snap arm and the matching piece of shell wall: checks how firmly the snaps hold and that they release |
| `report.txt` | Output of `check.py`: clashes at every tilt step, overhangs, bed fit, mass and tip stability |

## Parts

| Part | What it does |
|---|---|
| Front plate | The shared facade and display pocket, as the desk stands; a light-sealing lip round its back; snaps into the back shell |
| Back shell | Closed box behind the plate: vents and a wire pass in its back panel |
| Case hinge | Bracket screwed to the shell's back from inside: carries the case knuckle and its teeth |
| Knob | Knurled thumb knob holding the M4 bolt's head |
| Base | Floor, outer walls, the tower's walls, the two speaker posts, the tower lid screw bosses, the USB-C connector's pocket |
| Deck lid | Top of the deck and wings; snaps onto the base |
| Tower lid | Closes the tower: speaker grille, the tower knuckle with its teeth and the captured nut |
| Clamp tabs (4) | The shared display clamps |

## How it works

- **Hinge.** A rosette joint: the tower knuckle and the case knuckle sit side by
  side on an M4 bolt, with 36 radial teeth between them (10° steps). The nut is
  captured deep in the tower knuckle; the bolt's head is in the knob. Loosen the
  knob about 1.5 turns, the case knuckle slides 1 mm off the teeth, tilt, and
  tighten. The case falls forward under its own weight (about 0.1 N m), which the
  teeth hold.
- **Sound.** The speaker lies face up on two posts, each ear screwed down with
  an M2 × 6, and the tower lid presses on it through a foam gasket round the
  cone opening on its face. Its sound goes straight up through 3 slots, 4 mm
  wide with 4.4 mm bars, running front to back. Each slot is cut to length to
  stay over the Ø25 mm cone opening; the longest is 22 mm. The slots start 2 mm
  behind the knob, so the hinge never sits over them. Leaned back, the case
  hangs over the grille and reflects some of the sound backward. The tower
  leaves 11 mm spare behind the speaker: that keeps the base 100.9 mm deep, so
  the stand doesn't tip more easily.
- **Wires.** One cable does it all: a screw-on USB-C socket, a flat ribbon
  (7.9 × 1.5 mm, 300 mm long) and a 90° plug with an 11 × 11 mm head. The socket
  is centred in the tower's back wall, between the speaker posts. The ribbon
  runs forward along the floor, up the inside of the tower front, and out
  through a wire pass near its top, 14 mm left of centre. A matching pass in
  the case's back panel faces it across the 1.5 mm gap. Inside the case the
  ribbon lies flat on the back panel, then runs forward along the left wall to
  the plug in the board's middle `USB` port on the left edge. The plug's head
  sits beside the board, about 4 mm from the side wall, with the ribbon leaving
  toward the back. Both passes are 13 mm wide and
  17.5 mm tall, so the plug goes through ribbon last. The ribbon crosses the gap
  lying flat, so it bends with the tilt. The speaker lead takes the same passes
  to the `SPK` header. The route uses about 200 mm of the cable, including the
  loop across the gap: leave about 25 mm of slack there for the 30° tilt and
  coil the spare inside the tower, under the speaker.
- **Snaps.** The front plate clips into the back shell (12 snaps, arms 2 mm thick,
  12 mm wide and 15 mm long with a 1 mm catch) and the deck lid onto the base (6).
  Each plate arm grows out of the light-seal lip, which holds its first 3 mm, so
  12 mm still bends. The arms have 45° barbs that hook behind 45° ridges, so a
  firm pull releases them for service. To open the case, take it off the hinge
  (or tilt it back) and lever the plate off with a coin or flat screwdriver in
  the two slots in the shell's bottom rim, 65 mm either side of centre. The tower lid keeps screws because it carries the hinge; the hinge
  bracket and the clamp tabs keep theirs too.
- **Light seal.** A 0.8 mm lip runs round the back of the front plate, 3 mm deep,
  just inside the back shell's walls. It covers the seam so the backlight doesn't
  show at the sides, and lines the two parts up as they close.
- **No supports.** Every part is split so its roofs print face-down or as walls.
  `check.py` checks every face in print orientation: the only faces flatter than
  45° are the tops of the USB-C connector's opening and flange pocket, short
  bridges, the same as the desk stands.

## Hardware

| Qty | Part | Used for |
|---|---|---|
| 1 | Waveshare ESP32-P4-WIFI6-Touch-LCD-7B | The display |
| 1 | Enclosed speaker 28 × 31 × 15 mm, 4 Ω 3 W, JST-PH2.0 plug ([Amazon, pack of 4](https://www.amazon.com/dp/B0FN7G4ZMC)), one cone, two side ears with Ø2.2 mm holes 36.75 mm apart, 6.65 mm behind the speaker face | Audio, into the board's `SPK` header at the top edge of the board, through the wire passes |
| 1 | Foam tape, about 1.5 mm thick and 3 mm wide | Gasket round the cone opening on the speaker's face, squeezed to 1 mm by the tower lid |
| 1 | Flat USB-C extension cable, 30 cm: screw-on panel socket (25.2 × 8.2 mm flange, screws 17 mm apart) to a 90° plug (11 × 11 mm head), ribbon 7.9 × 1.5 mm | Power and data: socket in the tower's back wall (two screws from outside), plug in the board's middle `USB` port |
| 1 | M4 × 30 hex-head bolt (DIN 933) | Hinge, head in the knob |
| 1 | M4 hex nut | Captured in the tower knuckle |
| 4 | M2.5 × 6 screw | Clamp tabs into the display's standoffs |
| 7 | M3 × 8 pan-head screw | 4 clamp tabs into the plate's columns, 3 case hinge bracket from inside the case |
| 4 | M3 × 8 countersunk (90°) screw | Tower lid into the base |
| 2 | M2 × 6 self-tapping screw | Speaker ears onto their posts |
| 4 | Stick-on rubber foot, 10 mm | In the 1 mm recesses under the base, 10 mm in from the corners |

## Printing

| Part | Orientation (as exported) |
|---|---|
| Front plate | Facade on the bed |
| Back shell | Back panel on the bed |
| Case hinge | Knob-side face on the bed, teeth facing up (crisp teeth, and the lug is built with the plate in every layer) |
| Knob | Flat face on the bed, hex pocket up |
| Base | Upright, on its floor |
| Deck lid | Top face on the bed, snap arms up |
| Tower lid | Underside on the bed, knuckle up |
| Clamp tabs | Flat |

PLA or PETG, 0.2 mm layers, 3+ walls, no supports. Sideways holes are teardrops
and blind pilots that face down end in a 90° point.

## Assembly

1. Set the cable's USB-C socket flange into the pocket inside the tower's back
   wall, socket through the opening, and fit its two screws from outside.
2. Feed the cable's 90° plug, metal first, from inside the tower up the inside
   of the tower front, out through its wire pass and in through the case's
   pass, with the ribbon following flat. Pass the speaker lead's plug out
   through the same two holes into the case.
3. Stick the foam tape round the cone opening on the speaker's face. Set the
   speaker face up on the two posts and screw each ear down with an M2 × 6.
4. Snap the deck lid onto the base.
5. Put the M4 nut into the pocket in the tower knuckle's left face, then screw
   the tower lid down (4 × M3 countersunk). It presses on the speaker through
   the gasket.
6. Screw the case hinge to the back shell from inside (3 × M3 × 8 pan head).
7. Mount the display in the front plate with the clamp tabs, as the desk stands.
8. Set the case knuckle against the tower knuckle's teeth, push the bolt through
   from the right and turn the knob to pull the nut to the bottom of its pocket.
9. Inside the case, lay the ribbon flat on the back panel, leaving about 25 mm of slack
   for the tilt, and plug it into the middle `USB` port with the ribbon pointing
   toward the back. Plug the speaker into
   `SPK`. Snap the front plate into the shell.

## Open points

- **Masses.** Weigh the display (with board) and the speaker and put the values
  in `params.yaml` under `mass:`; `check.py` then gives real tip numbers.
- **Tipping.** With the assumed masses the whole stand weighs about 540 g. A
  push of about 2.2 N straight back at the top of the screen tips it upright
  (1.8 N at 30°), and about 0.8 N forward (1.0 N at 30°). If it rocks, the deck
  and wings are empty and can take ballast.
- **Speaker screws.** The ears take M2 × 6 self-tapping screws into Ø1.6 mm
  pilots in the posts. This fit hasn't been confirmed by a print yet.
- **Speaker cone.** The grille is centred on the speaker's single cone; its
  Ø25 mm opening is measured.
- **Hinge.** Print the hinge test before the full parts, at 0.12 mm layers if you can.
  The tower lid's teeth are on a vertical face as it prints, so they come out less
  crisp than the case hinge's.

## Regenerate

```sh
uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py   # writes step/, print/ and test-prints/
uv run --no-project --python 3.12 --with build123d --with pyyaml python check.py   # writes report.txt
```
