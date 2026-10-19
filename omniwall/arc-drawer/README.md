# Omniwall arc-pocket drawer

A drawer unit that hangs on the printed bridge hooks (`../hook/`): a housing
with a floor, roof and side walls, and a drawer that slides out on two rear pins,
tilts down 30° at the end of its travel and stays captive. Units tile edge to
edge in any grid of widths and heights with 0.3 mm between them. `params.yaml`
holds every dimension with its source, and `build.py` makes all the files from it.

Four sizes so far. Units of the same depth tile together; the 84 mm and 60 mm
deep ones line up at the panel, not at the front.

| Size | Folder, file prefix | Housing W × D × H, mm | Drawer outside W × L × H | Drawer inside W × L × H | Hooks | Travel |
|---|---|---|---|---|---|---|
| 3 × 2, 84 deep | this folder, `arc_drawer_*` | 75.9 × 84 × 50.5 | 71.5 × 75.8 × 45.0 | 64.9 × 65.4 × 40 | 2 columns, 1 or 2 rows | 55.9 (76 %) |
| 2 × 2, 60 deep | [`2x2x60/`](2x2x60/), `arc_drawer_2x2x60_*` | 50.5 × 60 × 50.5 | 46.1 × 51.8 × 45.0 | 39.5 × 41.4 × 40 | 1 column on the centre line, 1 or 2 rows | 31.9 (65 %) |
| 3 × 2, 60 deep | [`3x2x60/`](3x2x60/), `arc_drawer_3x2x60_*` | 75.9 × 60 × 50.5 | 71.5 × 51.8 × 45.0 | 64.9 × 41.4 × 40 | 2 columns, 1 or 2 rows | 31.9 (65 %) |
| 3 × 3, 60 deep | [`3x3x60/`](3x3x60/), `arc_drawer_3x3x60_*` | 75.9 × 60 × 75.9 | 71.5 × 51.8 × 70.4 | 64.9 × 41.4 × 65.4 | 2 columns, 1 to 3 rows | 31.9 (65 %) |

Drawer lengths include the label holder; the scoop stands 11 mm further out. All of them tilt to 30° at the end of
their travel and have the same scoop and label holder. A size is a folder with a
`params.yaml` that sets only what differs (`2x2x60/params.yaml` sets `cells: 2` and `depth: 60`);
everything else comes from this folder's `params.yaml`. A 60 mm deep unit also
moves the track's stop to depth − 15.5 (44.5), so the arc, gate, hook and exit
channel sit the same distance from the front as in the 84 mm unit. Every pocket
channel has a ridge pair for each hook row (three on a 3-row unit), one pitch
apart.

## Where it sits on the panel

A bridge hook straddles the horizontal slot row, so it sits at a crossing of
the slot grid. Sideways the unit's edges sit on vertical slot columns, as the bins
do, so every slot column inside the unit takes a hook: 2 for 3 cells (3 for 4
cells). Vertically the unit's bottom edge sits on a peg-hole row, so both hook
rows of a 2-row unit are inside it (hooks 3.3 and 28.7 mm above the bottom
edge). Width and height are the cell size minus 0.3 mm, not the bins' +3.0 mm:
units with +3.0 mm cannot sit next to each other.

## One pocket channel per column, one or two rows of hooks

Each column has one dovetail channel from the unit's bottom edge up to a closed
seat at the top row's hook top. The channel is the shared pocket
(`dovetail_mount` in `../panel.yaml`, built by `pocket_void()` in
`../hook_geometry.py`): spine channel, 45° dovetail slot, 0.25 mm clearance,
snap ridges 2.75 mm below the seat, and another pair every pitch lower, one per hook row.
Three of its values are replaced by `housing.pocket` in params.yaml, from the
pocket coupon that clicked best when printed on its back (coupon 3 of
`pocket_variants.py`, tested 2026-10-17): the lips' back starts 0.1 mm lower
(`spine_clearance -0.1`), the lip flank sits 0.1 mm behind the hook's
(`flank_gap`, was 0.4) and the ridges are 0.53 mm (was 0.333). They reach 0.28 mm past
the hook's flank, 0.05 mm deeper than its 0.23 mm notches, so a seated hook is
held lightly squeezed.

- With hooks in the top row only, the unit hangs from them and the lower part of
  each channel is empty.
- With hooks in both rows, the top hooks carry the weight on the seats and the
  lower hooks add their dovetail grip and snap into the lower ridges. The upper
  hooks pass through the lower ridges on the way down (they click through, as
  on the test plate).

Two separate closed pockets in one column cannot work: the upper hook would have
to pass through the lower pocket's closed top. So a lower hook never has its own
seat; it only adds grip.

The housing prints on its back (see Printing), so two faces of the pocket that
would hang flat over the bed got 45° gables: the back of the lips (the lip is
now a 90° wedge, its 45° bearing flank unchanged) and the pocket floor (the back
plate grows from 8.35 to 10.1 mm). The first coupon printed this way was loose:
the lips' gable started at their back face and cut them to a knife edge, which
`housing.pocket` fixes. `test-prints/arc_drawer_pocket_coupon_print.*` is one
column of the back plate to check this pocket before printing the housing.

## How the drawer works

- **Slide.** The drawer sits on the housing floor and pulls out on a pin (Ø3)
  on each rear side face, running in a groove 1.2 mm deep in each housing wall.
  The pin is a teardrop (45° point down) with its point cut flat at the pin's
  radius, and that flat is chamfered 45° from the drawer wall up to the pin's end
  (Zeid's choice, 2026-10-18), so it prints with nothing facing flat down and
  stays inside a 3 mm circle however the drawer turns. The whole track is that
  circle's path plus 0.25 mm clearance: one channel 3.5 mm wide, every wall a
  line or an arc. The side walls
  are 3.2 mm, so 2 mm of wall is left behind the groove (with 1.2 mm the
  track showed through on the outside of Zeid's 2 × 2 print).
- **Stop and tilt.** 56 mm out, the pins reach the end of the groove. The groove
  continues as an arc centred on the sill (the floor's front edge), so the
  drawer rocks forward on the sill and the pins ride up the arc until it ends at
  30°. The corner where the groove's ceiling meets the arc, above the stop,
  is rounded to 3 mm (`track.stop_round`). The arc is closed: the drawer cannot fall out. The face is already out
  of the housing when it tilts, so the 0.5 mm gap between the face and the roof
  only has to clear the slide; a sweep through slide, tilt, gate, hook and exit finds
  no overlap. The drawer of the unit above, tilted or pushed back the same way,
  clears this drawer's scoop by 6.2 mm (3 × 2); pulled out along its exit channel and
  let rest on its sill, its nose touches the scoop only in the last couple of
  millimetres before it comes free (`report.txt` lists each state), so hold it
  up as it comes out.
- **Removing.** Pull the drawer out until it tips to 30°, push it back about
  6 mm, then pull it out. From the end of the arc (the apex) the gate runs back
  and up, curving with the arc's own 19 mm radius: the arc mirrored at the apex
  (Zeid's sketch, 2026-10-18). The drawer slides back on the sill and its pins
  climb 3.8 mm, which raises the empty drawer's centre of gravity by up to
  2.0 mm, so let go in the gate and it slides back to the apex. The gate runs
  into the hook (radius 2.8), which curves up round the tongue of wall and
  forward into the exit channel to the housing's front face; on the hook the
  drawer's weight tips it further (33° to 45°). The tongue's tip is rounded
  1.05 mm, the nub between the arc and the gate 1.0 mm (`track.nub_round`).
  The groove has no opening above it: the old lift notch, 8.5 mm behind the
  stop, let a drawer that was let go as its pins passed under it rise into it
  and fall out (Zeid's 2 × 2 print). The rear 30 mm of the drawer's side walls
  are lowered so the back clears the roof.
- **Loading.** Tip the drawer nose-down, put its pins in the exit channel at
  the face and push it in until they stop at the back of the hook. Let the face
  drop so the pins run down round the hook and forward through the gate to the
  apex, then level the drawer and push it home.
- **Front.** The face's top two corners are rounded to 4 mm
  (`drawer.corner_radius`); the cut runs the length of the drawer, so the side
  walls' outer top edges follow the same curve. The face's top is 0.5 mm under
  the housing roof (`drawer.top_gap`). The pull (`front.pull: scoop_pins`,
  `scoop_pins:` in params.yaml, `handle_geometry.py`) is Zeid's scoop look as a
  separate part on two snap pins: a hollow hood, open below, 46 mm wide at the
  face and 30 at its lip (40 and 24 on the 2 × 2, whose face is narrower, so the sides keep the same angle), its top sloping 45° down to the lip 11 mm out, every
  visible edge rounded 1 mm. Its back plate sits in a 2 mm recess in the face
  (the recess's top is 45°, so the drawer still prints upright). The pins (barbs
  6.4 mm and the legs of pin C from the handle test, the neck 2 mm shorter to
  suit the recess) push through the face from inside, flats sideways, and click
  into socket tubes in the scoop's back corners, leaving 17.7 mm (2 × 2: 14.7) between them
  for a finger; the backs of their barbs slope 30° and stay 0.25 mm squeezed, so
  they pull the scoop tight against the face. The pin holes are cut to the pin's
  width with a counterbore for the head, so it sits flush inside the drawer.
  The scoop's bottom stays 11.6 mm above the label holder, so a label still
  drops in from above. `scoop_test.py` writes its test print (a strip of face,
  the scoop, four pins) to `test-prints/`. `front.pull: handle` is the plate
  handle after Zeid's HANDLE H2 (`handle:`, `handle_test.py`), `scoop` his
  original scoop built into the face, and `lip` the old 8 mm lip. The label holder
  is a U at the bottom of the face, open at the top: the 34.7 × 10.85 × 0.9 mm
  bin label (`../../labels/bin-label`) drops in from above and sits behind
  1.5 mm returns. Make its labels with the `arc-drawer` size in
  `../../labels/bin-label`, which keeps the text clear of the returns.

`build.py` checks the drawer against the housing in every position (closed,
sliding, at the stop, every 5° of the tilt, pushed back through the gate and round the hook and pulled out
along the exit channel, both resting on the sill and held level) and the hooks against the housing; all overlaps are 0 mm³
(`report.txt`), apart from the hooks' intended 0.56 mm³ in total where the
snap ridges squeeze the seated hooks.

## Printing

`step/` holds the parts as designed, in their places in the assembly, for
CAD. `print/` holds the same parts turned to the way they lie on the bed, as
STEP and STL per part, plus one plain 3MF for the printer (written with
`../core_3mf.py`; Bambu Studio 2.x keeps only the geometry of the multi-plate
projects `../bambu_project.py` writes, so it is a plain one-plate 3MF).

**The one 3MF:** `print/arc_drawer_all_parts.3mf` (and
`<size>/print/arc_drawer_<size>_all_parts.3mf` for the other sizes) holds the housing, the drawer, the scoop and
its two pins on one plate, already in print orientation. Open it in Bambu Studio and slice. The drawer label is a separate two-colour print in
[labels/bin-label](../../labels/bin-label/README.md).

- **Housing: on its back,** panel side on the bed, open front up. Floor, roof,
  walls and back plate all stand vertical, so no roof is bridged. The pockets
  are trenches in the bed face with 45° gables; in the track groove, arc, gate,
  hook and exit channel every face that would hang flat is a 45° ramp rising from the
  groove floor to the wall face, so each layer of it is attached to the outer
  wall (a two-sided tent left floating slivers at the wall face).
- **Drawer: upright** on its floor. Pins (chamfered point down), the face's
  teardrop pin holes and the label holder (45° under the bottom rail) print
  without support.
- **Scoop: on its back** (`*_handle_print`), so the socket tubes stand upright
  with 45° cones closing the chambers, and the hood's 45° roof needs no support.
  **Pins** lie on a flat; print two per drawer (`*_handle_pin_print`). The
  all-parts 3MF has the scoop and both pins.
- **Fit test plate first** (`test-prints/arc_drawer_fit_test_plate.3mf`, one plate; `build.py` writes it, git ignores it): the
  front 34 mm of the housing (arc, gate, hook, exit) with the rear 40 mm of the drawer
  (pins, shoulder), plus the pocket coupon. Checks the pin in the groove, the
  drop-in load, the way out through the gate and hook, and the pocket with two hooks.
- PLA or PETG, 0.2 mm layers, 3+ walls. `report.txt` lists every face flatter
  than 45° from vertical on each print part: none.

## Regenerating

`build.py` with no argument builds the 3 × 2 unit; `build.py 2x2x60` builds the
2 × 2 into `2x2x60/`, and likewise `3x2x60` and `3x3x60`. Any new size is a new
folder with its own `params.yaml`.

    uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py

(the build123d-mcp server's `execute()` sandbox blocks the os, pathlib and yaml imports, so the
script runs in a plain build123d Python; `uv` fetches build123d and PyYAML the first time). It rewrites
`step/` (housing, drawer, assemblies with hooks: closed, open, tilted, pushed back through the gate),
`print/` and `report.txt`.

    uv run --no-project --python 3.12 --with build123d --with pyyaml python check_islands.py print\arc_drawer_housing_print.step

slices a print-orientation part into 0.2 mm layers and lists any region with
nothing under it (the "floating regions" Bambu Studio warns about), which the
face-angle check in `report.txt` cannot see. Run it on each print file after a
change to the track or pockets.

## SolidCraft version

`solidcraft/` holds the same housing and drawer rebuilt in SolidCraft, from the
same `params.yaml`. `arc_drawer_3x2.solidcraft` is the editable design;
`arc_drawer_assembly_states.step` has the housing with the drawer closed, open,
tilted and lifted. It predates the branch (2026-10-18) and still has the old lift notch; the `_print` files are in print orientation (one 3MF per part).

To rebuild it: run `build_solidcraft.py`, which writes
`solidcraft/solidcraft_commands.json`, then send that command list to the
SolidCraft MCP `batch` tool against an empty design. The app must be running
with its control port (`solidcraft.exe --control 7878`). The SolidCraft MCP only
reads and writes files in its own temp folder, so exports land there and are
copied in; SolidCraft's `--allow-path DIR` flag would let it write here directly.

Every arc in the track (groove and ramp) is drawn as a polyline that stays
within 0.003 mm of the true arc. With real arcs, SolidCraft's boolean failed
where the ramp meets the groove almost tangentially. This leaves sub-0.05 mm2
facets on the wall face, which the face-angle check counts as flat (46 on the
housing) but which are far below one extrusion line; `check_islands.py`
reports 0 floating regions on both print files.

`solidcraft/check_solidcraft.py` compares the result with `step/`. Housing
volume 79536.80 vs 79536.70 mm3, drawer 46323.459 vs 46323.459 mm3, same
bounding boxes and centroids, no hook clash.

## Untested

- Pin and groove fit (0.25 mm clearance) and the drop-in load.
- The way out: whether pushing the tipped drawer 6 mm back through the curved gate feels natural, whether it slides back down by itself, and whether the gate's 2 mm rise keeps a tipped drawer in when it is pushed by accident.
- The narrower 3.5 mm track and the chamfered pins: how they slide and how the chamfer prints.
- The scoop on its pins: the shorter-necked pin and the recess (`test-prints/scoop_test_all_parts.3mf`); the label fit (0.15 mm per side).
- The drawer drops to 30° whenever it is pulled to the stop.
