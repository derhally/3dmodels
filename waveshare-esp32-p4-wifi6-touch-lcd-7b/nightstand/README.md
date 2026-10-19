# Nightstand stand ("Stem")

A bedside alternative to the 45° desk stands. The display sits in a slim case
on a toothed hinge, upright or leaned back up to 30° in 10° steps. Behind the
screen, a short tower holds the speaker lying face up under an 11-slot grille
in the tower lid. 188 W × 101 D × 141 H mm upright.

See the [device README](../README.md) for the shared facade, display mounting,
USB-C port and how the files were made.

**Status: not printed yet.** The display and speaker masses in `params.yaml`
are assumed (230 g and 70 g), so the tip numbers below are estimates until
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
| Front plate | The shared facade and display pocket, as the desk stands; snaps into the back shell |
| Back shell | Closed box behind the plate: vents and a wire pass in its back panel |
| Case hinge | Bracket screwed to the shell's back from inside: carries the case knuckle and its teeth |
| Knob | Knurled thumb knob holding the M4 bolt's head |
| Base | Floor, outer walls, the tower's walls, the four speaker posts, the tower lid screw bosses, the USB-C connector's pocket |
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
- **Sound.** The speaker lies face up on four posts, its ears on the posts'
  spigots, and the tower lid holds it down through a foam gasket on the rim of
  its face. Its sound goes straight up through 11 slots, 4 mm wide with 4.4 mm
  bars, running front to back. The slots start 2 mm behind the knob, so the hinge
  never sits over them. Leaned back, the case hangs over the grille and reflects
  some of the sound backward.
- **Wires.** One cable does it all: a screw-on USB-C socket, a flat ribbon
  (7.9 × 1.5 mm, 300 mm long) and a 90° plug with an 11 × 11 mm head. The socket
  is in the tower's back wall, under the speaker. The ribbon runs forward along
  the floor, up the inside of the tower front, and out through a wire pass near
  its top. A matching pass in the case's back panel faces it across the 1.5 mm
  gap. Inside the case the ribbon lies flat on the back panel, then runs forward
  along the left wall to the plug in the board's middle `USB` port on the left
  edge. The plug's head sits beside the board, about 4 mm from the side wall,
  with the ribbon leaving toward the back. Both passes are 13 mm wide and
  17.5 mm tall, so the plug goes through ribbon last. The ribbon crosses the gap
  lying flat, so it bends with the tilt. The speaker lead takes the same passes
  to the `SPK` header. The route uses about 175 mm of the cable, including the
  loop across the gap: leave about 25 mm of slack there for the 30° tilt and
  coil the spare inside the tower, under the speaker.
- **Snaps.** The front plate clips into the back shell (8 snaps) and the deck lid
  onto the base (6). The arms have 45° barbs that hook behind 45° ridges, so a
  firm pull releases them for service. The tower lid keeps screws because it
  carries the hinge; the hinge bracket and the clamp tabs keep theirs too.
- **No supports.** Every part is split so its roofs print face-down or as walls.
  `check.py` checks every face in print orientation: the only faces flatter than
  45° are the tops of the USB-C connector's opening and flange pocket, short
  bridges, the same as the desk stands.

## Hardware

| Qty | Part | Used for |
|---|---|---|
| 1 | Waveshare ESP32-P4-WIFI6-Touch-LCD-7B | The display |
| 1 | Box speaker 100 × 45 × 20.75 mm, four Ø6.2 mm corner ears 10 mm behind the cone face | Audio, into the board's `SPK` header at the top edge of the board. The lead needs about 20 cm to get there through the wire passes: plan on an extension |
| 1 | Foam tape, about 1.5 mm thick and 3 mm wide | Gasket round the speaker face's rim, squeezed to 1 mm by the tower lid |
| 1 | Flat USB-C extension cable, 30 cm: screw-on panel socket (25.2 × 8.2 mm flange, screws 17 mm apart) to a 90° plug (11 × 11 mm head), ribbon 7.9 × 1.5 mm | Power and data: socket in the tower's back wall (two screws from outside), plug in the board's middle `USB` port |
| 1 | M4 × 30 hex-head bolt (DIN 933) | Hinge, head in the knob |
| 1 | M4 hex nut | Captured in the tower knuckle |
| 4 | M2.5 × 6 screw | Clamp tabs into the display's standoffs |
| 7 | M3 × 8 pan-head screw | 4 clamp tabs into the plate's columns, 3 case hinge bracket from inside the case |
| 4 | M3 × 8 countersunk (90°) screw | Tower lid into the base |
| 4 | Stick-on rubber foot, 10 mm | Under the base, 10 mm in from the corners |

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
3. Stick the foam tape round the rim of the speaker's face. Set the speaker face
   up on the posts, each ear over a spigot.
4. Snap the deck lid onto the base.
5. Put the M4 nut into the pocket in the tower knuckle's left face, then screw
   the tower lid down (4 × M3 countersunk). It presses the speaker onto its posts.
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
- **Tipping.** With the assumed masses the whole stand weighs about 600 g. A
  push of about 2.3 N straight back at the top of the screen tips it upright
  (1.9 N at 30°), and about 1.1 N forward. If it rocks, the deck and wings are
  empty and can take ballast.
- **Speaker cones.** The cone positions aren't measured; the grille assumes they
  sit under the middle of the face.
- **Hinge.** Print the hinge test before the full parts, at 0.12 mm layers if you can.
  The tower lid's teeth are on a vertical face as it prints, so they come out less
  crisp than the case hinge's.

## Regenerate

```sh
uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py   # writes step/, print/ and test-prints/
uv run --no-project --python 3.12 --with build123d --with pyyaml python check.py   # writes report.txt
```
