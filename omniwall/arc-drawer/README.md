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
| 3 × 2, 84 deep | this folder, `arc_drawer_*` | 75.9 × 84 × 50.5 | 73.1 × 80.5 × 45.0 | 66.5 × 65.4 × 40 | 2 columns, 1 or 2 rows | 55.9 (76 %) |
| 2 × 2, 84 deep | [`2x2/`](2x2/), `arc_drawer_2x2_*` | 50.5 × 84 × 50.5 | 47.7 × 80.5 × 45.0 | 41.1 × 65.4 × 40 | 1 column on the centre line, 1 or 2 rows | 55.9 (76 %) |
| 3 × 2, 60 deep | [`3x2x60/`](3x2x60/), `arc_drawer_3x2x60_*` | 75.9 × 60 × 50.5 | 73.1 × 56.5 × 45.0 | 66.5 × 41.4 × 40 | 2 columns, 1 or 2 rows | 31.9 (65 %) |
| 3 × 3, 60 deep | [`3x3x60/`](3x3x60/), `arc_drawer_3x3x60_*` | 75.9 × 60 × 75.9 | 73.1 × 56.5 × 70.4 | 66.5 × 41.4 × 65.4 | 2 columns, 1 to 3 rows | 31.9 (65 %) |

Drawer lengths include the 7.1 mm scoop. All of them tilt to 30° at the end of
their travel and have the same scoop and label holder. A size is a folder with a
`params.yaml` that sets only what differs (`2x2/params.yaml` sets `cells: 2`);
everything else comes from this folder's `params.yaml`. A 60 mm deep unit also
moves the track's stop to depth − 15.5 (44.5), so the arc, notch and exit
channel sit the same distance from the front as in the 84 mm unit. On a 3-row
unit the pocket channels have snap ridges for the top two hook rows; a hook in
the bottom row slides into the same channel and holds the back to the panel
without a click.

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
snap ridges 2.75 mm below the seat. A second ridge pair sits one pitch lower.
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

- **Slide.** The drawer sits on the housing floor and pulls out on a teardrop
  pin (Ø3, 45° point down) on each rear side face, running in a matching groove
  1.2 mm deep in each housing wall, 0.25 mm clearance all round.
- **Stop and tilt.** 56 mm out, the pins reach the end of the groove. The groove
  continues as an arc centred on the sill (the floor's front edge), so the
  drawer rocks forward on the sill and the pins ride up the arc until it ends at
  30°. The arc is closed: the drawer cannot fall out. The face is already out
  of the housing when it tilts, so the 0.5 mm gap between the face and the roof
  only has to clear the slide; a sweep through slide, tilt, lift and exit finds
  no overlap. The drawer of the unit above, tilted the same way, clears this
  drawer's scoop.
- **Removing.** Level the drawer, push it back 8.5 mm, lift its back 12.5 mm, pull
  it out: a vertical notch there leads into an exit channel to the housing's
  front face. The rear 30 mm of the drawer's side walls are 6 mm lower so the
  back can rise that far under the roof. A 5 mm tooth separates the notch
  from the arc, and 2 mm of wall separates the arc's top from the exit channel.
- **Loading.** Hold the drawer level with its back 12.5 mm up, push it in until
  the pins stop at the end of the exit channel, let go: the pins drop down the
  notch onto the groove. Push home.
- **Front.** The face's top two corners are rounded to 4 mm
  (`drawer.corner_radius`); the cut runs the length of the drawer, so the side
  walls' outer top edges follow the same curve. The face's top is 0.5 mm under
  the housing roof (`drawer.top_gap`). Zeid's scoop (`E:\source\openscad\omniwall\drawers\scoop_prototype.scad`,
  values in `scoop:` in params.yaml) turned 180° so it opens downward: a tray
  40 mm wide at the face narrowing to 16 mm, tilted 45° out from the face, top
  2 mm below the plate top, standing 7.1 mm proud. Fingers go up into it from
  below. It is blended into the face with a 2 mm radius (top, outer sides and
  the cavity's ceiling; the kernel won't fit one where the cavity's side walls
  meet the face). The front wall's lip would start as a knife edge hanging
  across the cavity, so its first layers were a thin line in the air (Zeid's
  2 × 2 print). Its underside is cut flat 1.5 mm up (`scoop.lip_flat`), so it
  starts as a 14.5 × 2.8 mm bridge between the side walls. That bridge is the
  one face `report.txt` lists as flatter than 45°, on purpose. The scad's 0.5 mm edge rounding is left out, since the rim's
  would face down flatter than 45°. `front.pull: lip` brings back the old 8 mm
  lip. The label holder
  is a U at the bottom of the face, open at the top: the 34.7 × 10.85 × 0.9 mm
  bin label (`../../labels/bin-label`) drops in from above and sits behind
  1.5 mm returns. Make its labels with the `arc-drawer` size in
  `../../labels/bin-label`, which keeps the text clear of the returns.

`build.py` checks the drawer against the housing in every position (closed,
sliding, at the stop, every 5° of the tilt, lifted and pulled out along the
exit channel) and the hooks against the housing; all overlaps are 0 mm³
(`report.txt`), apart from the hooks' intended 0.56 mm³ in total where the
snap ridges squeeze the seated hooks.

## Printing

Everything in `print/` is in print orientation, as STEP, STL and plain 3MF
(written by build123d's `Mesher` through the build123d-mcp server; `build.py`
writes the same kind of file with `../core_3mf.py`). Bambu Studio 2.x rejects the multi-plate projects written by
`../bambu_project.py` as "created by an old version" and keeps only their
geometry, so there is one file per part instead; arrange plates in Bambu Studio.

**Everything in one file:** `print/arc_drawer_all_parts.3mf` (and
`<size>/print/arc_drawer_<size>_all_parts.3mf` for the other sizes) holds the housing and the drawer side
by side on one plate, already in print orientation, 10 mm apart. Open it in
Bambu Studio and slice. The drawer label is a separate two-colour print in
[labels/bin-label](../../labels/bin-label/README.md).

- **Housing: on its back,** panel side on the bed, open front up. Floor, roof,
  walls and back plate all stand vertical, so no roof is bridged. The pockets
  are trenches in the bed face with 45° gables; in the track groove, arc, notch
  and exit channel every face that would hang flat is a 45° ramp rising from the
  groove floor to the wall face, so each layer of it is attached to the outer
  wall (a two-sided tent left floating slivers at the wall face).
- **Drawer: upright** on its floor. Pins (point down), scoop (45° rim and ceiling) and
  label holder (45° under the bottom rail) print without support.
- **Fit test plate first** (`test-prints/arc_drawer_fit_test_plate.3mf`, one plate; `build.py` writes it, git ignores it): the
  front 34 mm of the housing (arc, notch, exit) with the rear 40 mm of the drawer
  (pins, shoulder), plus the pocket coupon. Checks the pin in the groove, the
  drop-in load, the lift-out, and the pocket with two hooks.
- PLA or PETG, 0.2 mm layers, 3+ walls. `report.txt` lists every face flatter
  than 45° from vertical on each print part: only the drawer's scoop-lip bridge.

## Regenerating

`build.py` with no argument builds the 3 × 2 unit; `build.py 2x2` builds the
2 × 2 into `2x2/`, and likewise `3x2x60` and `3x3x60`. Any new size is a new
folder with its own `params.yaml`.

    uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py

(the build123d-mcp server's `execute()` sandbox blocks the os, pathlib and yaml imports, so the
script runs in a plain build123d Python; `uv` fetches build123d and PyYAML the first time). It rewrites
`step/` (housing, drawer, assemblies with hooks: closed, open, tilted, lifted),
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
tilted and lifted; the `_print` files are in print orientation (one 3MF per part).

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
- Lift of 12.5 mm to remove: whether that feels deliberate enough.
- The scoop's grip from below; the label fit (0.15 mm per side).
- The drawer drops to 30° whenever it is pulled to the stop.
