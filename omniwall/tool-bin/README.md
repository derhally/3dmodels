# Omniwall tool bins

Bins for 3D printer tools (picks, pencils, markers, tweezers) that hang on the
panel next to the arc drawers and trays, on the same hooks. Each bin has a
drop-in grid that rests on a ledge round the inside, so pencils and markers
stand upright. The grid clicks in with a spring tab on each side. Leave the grid
out and the bin is an open bin.

They follow the drawers and trays: 60 mm deep, width = cells × 25.4 − 0.3 so
they tile with them, every outside edge rounded, a 45° chamfer at the bed edge
rolling into a radius, a coved floor inside, and the drawers' U label holder on
the front for a [bin label](../../labels/bin-label/).

Five bins: four from the [concept sheet](https://claude.ai/artifact/1yvXStQUJkG4cpvx3zR3Z7)
(Zeid kept all four, and picked spring tabs for the snap), and the tall bin one
row taller:

| Bin | Folder, file prefix | W × D × H, mm | Grid | Hooks |
|---|---|---|---|---|
| Pencil cup 2 × 2 | [`cup-2x2/`](cup-2x2/), `tool_bin_cup_2x2_*` | 50.5 × 60 × 50.5 | honeycomb, 13 mm across the flats | 1 column × 2 rows |
| Tool caddy 3 × 2 | [`caddy-3x2/`](caddy-3x2/), `tool_bin_caddy_3x2_*` | 75.9 × 60 × 50.5 | 4 × Ø13 (markers), 12 × Ø8.6 (pencils, picks), a 62 × 7 slot (tweezers, scrapers) | 2 columns × 2 rows |
| Tall bin 3 × 3 | [`tall-3x3/`](tall-3x3/), `tool_bin_tall_3x3_*` | 75.9 × 60 × 75.9, 50.5 at the front | 4 × 3 cells of 14.4 × 13.2 | 2 columns × 3 rows |
| Tall bin 3 × 4 | [`tall-3x4/`](tall-3x4/), `tool_bin_tall_3x4_*` | 75.9 × 60 × 101.3, 75.9 at the front | 4 × 3 cells of 14.4 × 13.2 | 2 columns × 4 rows |
| Split bin 4 × 2 | [`split-4x2/`](split-4x2/), `tool_bin_split_4x2_*` | 101.3 × 60 × 50.5 | left half: 3 × 3 cells of 11.6 × 13.2; right half an open well | 3 columns × 2 rows |

The tall bins' side walls fall from the back to the front in one S of two arcs,
as on the trays, and the grid sits under the front rim.

## Hardware

Hooks only, no screws: a Bridge hook 1U or a Slot hook 1U (`../hook/`) in every
slot column inside the bin, in every row it spans (a Slot hook 2U can take the
place of two 1Us in a column).

## How it hangs

As the trays: the back wall is 10.075 mm thick and carries one dovetail pocket
per slot column (`dovetail_mount` in `../panel.yaml`, built by `pocket_void()` in
`../hook_geometry.py`, with the drawer housing's print-tested flank gap and
0.53 mm snap ridges). Each pocket is open at the bottom and closed at the top
with a 45° gable through the top hook's top corners, so the bin prints upright.
There is a ridge pair in every row, so every hook clicks in. Slide the bin down
onto the hooks until the ridges click into the hooks' notches.

## The grid

The grid is 8 mm thick, sits on a 2 mm ledge round the inside (45° underneath,
so it prints) with 0.4 mm clearance at the back and front and 0.2 mm at the
sides, and its top is 1 mm under the
front rim. A 0.6 mm chamfer leads into every hole.

Each side of the grid has a spring tab: a 20 mm beam, 1.6 mm thick, fixed at its
back end, with a 1.6 mm slot behind it. The slot's fixed sides have a 0.5 mm
chamfer at the grid's top, which is the bed side when printed, so first-layer
squish can't join the tab to the grid (a 1.2 mm tab with a 0.9 mm slot fused on
the first test prints). A 45° ridge on the tab (0.9 mm proud)
clicks into a 0.6 mm V groove in the bin wall. Push the grid down: each tab bends
0.7 mm to get past the wall, then clicks in. Pull it out by any hole. Seated, each
ridge still presses 0.1 mm into its groove, so the two tabs hold the grid centred
with no play (with 0.4 mm at the sides the caddy's snap test was loose side to
side).

## Printing

No supports anywhere (checked face by face on the print-orientation parts:
nothing faces down flatter than 45° from vertical). PLA or PETG, 0.2 mm layers,
3+ walls.

- The bin prints upright, as it hangs. The grid prints top face down, so its
  top is the smooth bed face and the hole chamfers sit on the bed.
- `print/`: STEP and STL of each part laid as on the bed, and one
  `*_all_parts.3mf` with the bin and grid on one plate.
- Every 3MF is a Bambu Studio project that opens ready to slice: the printer,
  filament and settings of [`../../bambu/`](../../bambu/), with `print` in
  `params.yaml` on top (infill, seam, wall generator for every part; 4 walls on
  the grid, so its tabs and ribs are solid walls).
- `step/`: the parts in place for CAD, and `*_assembly.step` with the Bridge
  hook 1Us they hang on.
- `test-prints/` (git-ignored, written by `build.py`): print these first.
  - `*_snap_test.3mf`: the bin's top band (from just under the ledge) and the
    whole grid, to check the grid's click.
  - `*_pocket_coupon_print.*`: the back wall round one pocket, printed upright,
    to check the hook snap (the drawer housings' pockets were tested printed on
    their back, not upright).

## Building

`params.yaml` holds the shared values with their sources; each bin folder's
`params.yaml` sets its size, hole pattern and only what differs. From this
folder:

```
uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py caddy-3x2
```

It writes the folder's `step/`, `print/`, `test-prints/` and `report.txt`. The
report has the measured checks: pocket gables and their heights, the ledge and
the grid's height under the rim, grid against bin (seated and on its way in),
hooks against the bin (only the snap ridges' overlap into the notches), and the
overhang check on every print part.
