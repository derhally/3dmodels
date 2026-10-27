# Omniwall lean bin

A bin whose front leans out from the panel, so screwdrivers, pencils and markers
lie back against the sloped front with their handles toward you: easy to see
what is in it and easy to grab. It hangs on the same hooks as the arc drawers,
trays and [tool bins](../tool-bin/).

Zeid picked the lean option from the
[mockups](https://claude.ai/artifact/WeGnPMjU9gYLkcH7NsHo1D) and sketched the
side view, leaning more than the mockup's 15°: a flat top at the back, the rim
falling to a rounded nose, the front leaning back down to a short foot.

| Bin | Folder, file prefix | W × D × H, mm | Hooks |
|---|---|---|---|
| Lean bin 3 × 3 | [`3x3x65/`](3x3x65/), `lean_bin_3x3x65_*` | 75.9 × 65 × 75.9 | 2 columns × 3 rows |

## The shape

In the side view:

- The back is 75.9 mm tall (three rows) with a 16.5 mm flat top.
- The rim falls 32° below level from the flat top to the nose, so the opening
  faces you.
- The nose is rounded R6 and is 65 mm out from the panel, flush with the
  drawers, trays and tool bins.
- The front leans 42° from vertical, down to a 29 mm deep foot. Its inside is
  the ramp the tools lie on: 50.8 mm long up the lean and 71.1 mm wide.

The width is cells × 25.4 − 0.3, so it tiles with the other parts. The walls
and floor are 2.4 mm, the inside corners are rounded and coved into the floor,
the front's outside corners are rounded R6 across the lean, and the top edges
are rounded 1 mm. There is no label holder, because the front leans under and
the drawers' U holder would not print there.

## The grid (optional insert)

Leave it out and tools lie back on the ramp; drop it in and they stand in holes,
fanned out: the back row nearly upright, the front row leaning about 30°, so
every row shows over the one in front. It is the tool bins' grid, tilted: an
8 mm plate square to the rim's slope, its top 6 mm under it (3 mm under the flat
top at the back wall), with 11 holes from the back: 4 × Ø9.5 (pencils, picks),
3 × Ø11 between them (screwdrivers) and 4 × Ø13 (markers, fat drivers). Each
hole points at a spot on the floor, so a tool's tip lands there.

It rests on a 2 mm ledge on the back wall and a ledge on the ramp under its
front edge, both 45° underneath so the bin still prints without supports, with
0.4 mm clearance at the back and front. It clicks in with the tool bins' spring
tabs (a 20 mm beam, 1.6 mm thick, with a 1.6 mm slot behind it, in each side)
into a V groove in each side wall; the side walls are square to the grid, so
the snap is the tested one unchanged, with 0.2 mm clearance at the sides and the
ridges pressing 0.1 mm into the grooves. Push it in square to the rim; pull it
out by any hole.

## Hardware

Hooks only, no screws: a Bridge hook 1U or a Slot hook 1U (`../hook/`) in every
slot column inside the bin, in every row it spans.

## How it hangs

As the tool bins: the back wall is 10.075 mm thick and carries one dovetail
pocket per slot column (`dovetail_mount` in `../panel.yaml`, built by
`pocket_void()` in `../hook_geometry.py`), with 0.40 mm snap ridges (tested
printed upright) and a ridge pair in every row. Each pocket is open at the
bottom and closed at the top with a 45° gable, so the bin prints upright.
Slide the bin down onto the hooks until the ridges click into the hooks'
notches.

## Printing

Upright, as it hangs, with the front toward the plate's front, so the seam
lands on the back wall. No supports: the front's 42° is the steepest overhang,
along with the pockets' and ledges' 45°. Every bottom edge has a 0.6 mm chamfer
against elephant's foot. Empty, its centre of mass sits over the foot, so it
does not lean forward on the bed. PLA or PETG, 0.2 mm layers, 3+ walls.

The grid prints top face down, so its top is the smooth bed face and the hole
chamfers sit on the bed; the slanted holes lean at most 29° from vertical.

- `print/`: STEP and STL of each part laid as on the bed, and `*_all_parts.3mf`,
  a Bambu Studio project with the bin and the grid on one plate, far enough
  apart to print by object, that opens ready to slice (the printer, filament and
  settings of [`../../bambu/`](../../bambu/), with `print` in `params.yaml` on
  top; 4 walls on the grid, as the tool bins').
- `step/`: the bin and the grid in place for CAD, and `*_assembly.step` with the
  Bridge hook 1Us it hangs on.
- `test-prints/` (git-ignored, written by `build.py`):
  `*_pocket_coupon_print.*`, the back wall round one pocket, printed upright, to
  check the hook snap.

## Building

`params.yaml` holds the shared values with their sources; each size folder's
`params.yaml` sets its size. From this folder:

```
uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py 3x3x65
```

It writes the folder's `step/`, `print/`, `test-prints/` and `report.txt`. The
report has the measured checks: pocket gables and their heights, the ramp,
each grid hole's lean and where its tip lands, the thinnest rib, grid against
bin (seated and on its way in), hooks against the bin (only the snap ridges' overlap into the notches), where
the centre of mass sits on the bed, and the overhang check on every print part.
