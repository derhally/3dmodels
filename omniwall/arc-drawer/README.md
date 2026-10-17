# Omniwall arc-pocket drawer

A drawer unit that hangs on the printed cross-slot hooks (`../hook/`): a housing
with a floor, roof and side walls, and a drawer that slides out on two rear pins,
tilts down 30° at the end of its travel and stays captive. Units tile edge to
edge in any grid of widths and heights with 0.3 mm between them. `params.yaml`
holds every dimension with its source, and `build.py` makes all the files from it.

Two sizes so far, which tile together (same height and depth):

| | 3 cells × 2 rows (this folder) | 2 cells × 2 rows ([`2x2/`](2x2/)) |
|---|---|---|
| Housing W × D × H, mm | 75.9 × 84 × 50.5 | 50.5 × 84 × 50.5 |
| Drawer, outside W × L × H | 73.1 × 80.5 × 44.5 | 47.7 × 80.5 × 44.5 |
| Drawer inside | 66.5 wide × 65.5 long × 40 tall (walls 2, floor 2) | 41.1 wide, otherwise the same |
| Hooks | 2 columns, 1 or 2 rows | 1 column on the centre line, 1 or 2 rows |
| Files | `step/`, `print/arc_drawer_*` | `2x2/step/`, `2x2/print/arc_drawer_2x2_*` |

Both have 55.9 mm of travel, then tilt to 30°, and the same scoop and label
holder. A size is a folder with a `params.yaml` that sets only what differs
(`2x2/params.yaml` sets `cells: 2`); everything else comes from this folder's
`params.yaml`.

## Where it sits on the panel

A cross-slot hook straddles the horizontal slot row, so it sits at a crossing of
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
`housing.pocket` fixes. `print/arc_drawer_pocket_coupon_print.*` is one
column of the back plate to check this pocket before printing the housing.

## How the drawer works

- **Slide.** The drawer sits on the housing floor and pulls out on a teardrop
  pin (Ø3, 45° point down) on each rear side face, running in a matching groove
  1.2 mm deep in each housing wall, 0.25 mm clearance all round.
- **Stop and tilt.** 56 mm out, the pins reach the end of the groove. The groove
  continues as an arc centred on the sill (the floor's front edge), so the
  drawer rocks forward on the sill and the pins ride up the arc until it ends at
  30°. The arc is closed: the drawer cannot fall out. The front plate's top
  back corner rises 0.4 mm while tilting and clears the roof by 0.6 mm; the
  drawer of the unit above, tilted the same way, clears this drawer's scoop.
- **Removing.** Level the drawer, push it back 8.5 mm, lift its back 12.5 mm, pull
  it out: a vertical notch there leads into an exit channel to the housing's
  front face. The rear 30 mm of the drawer's side walls are 6 mm lower so the
  back can rise that far under the roof. A 5 mm tooth separates the notch
  from the arc, and 2 mm of wall separates the arc's top from the exit channel.
- **Loading.** Hold the drawer level with its back 12.5 mm up, push it in until
  the pins stop at the end of the exit channel, let go: the pins drop down the
  notch onto the groove. Push home.
- **Front.** Zeid's scoop (`E:\source\openscad\omniwall\drawers\scoop_prototype.scad`,
  values in `scoop:` in params.yaml) turned 180° so it opens downward: a tray
  40 mm wide at the face narrowing to 16 mm, tilted 45° out from the face, top
  2 mm below the plate top, standing 7.1 mm proud. Fingers go up into it from
  below. It is blended into the face with a 2 mm radius (top, outer sides and
  the cavity's ceiling; the kernel won't fit one where the cavity's side walls
  meet the face). The scad's 0.5 mm edge rounding is left out, since the rim's
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

- **Housing: on its back,** panel side on the bed, open front up. Floor, roof,
  walls and back plate all stand vertical, so no roof is bridged. The pockets
  are trenches in the bed face with 45° gables; in the track groove, arc, notch
  and exit channel every face that would hang flat is a 45° ramp rising from the
  groove floor to the wall face, so each layer of it is attached to the outer
  wall (a two-sided tent left floating slivers at the wall face).
- **Drawer: upright** on its floor. Pins (point down), scoop (45° rim and ceiling) and
  label holder (45° under the bottom rail) print without support.
- **Fit test plate first** (`print/arc_drawer_fit_test_plate.3mf`, one plate): the
  front 34 mm of the housing (arc, notch, exit) with the rear 40 mm of the drawer
  (pins, shoulder), plus the pocket coupon. Checks the pin in the groove, the
  drop-in load, the lift-out, and the pocket with two hooks.
- PLA or PETG, 0.2 mm layers, 3+ walls. `report.txt` lists every face flatter
  than 45° from vertical on each print part: none.

## Regenerating

`build.py` with no argument builds the 3 × 2 unit; `build.py 2x2` builds the
2 × 2 into `2x2/`. Any new size is a new folder with its own `params.yaml`.

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
