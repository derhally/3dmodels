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
along with the pockets' 45° gables. Every bottom edge has a 0.6 mm chamfer
against elephant's foot. Empty, its centre of mass sits over the foot, so it
does not lean forward on the bed. PLA or PETG, 0.2 mm layers, 3+ walls.

- `print/`: STEP and STL laid as on the bed, and `*_all_parts.3mf`, a Bambu
  Studio project that opens ready to slice (the printer, filament and settings
  of [`../../bambu/`](../../bambu/), with `print` in `params.yaml` on top).
- `step/`: the bin in place for CAD, and `*_assembly.step` with the Bridge hook
  1Us it hangs on.
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
hooks against the bin (only the snap ridges' overlap into the notches), where
the centre of mass sits on the bed, and the overhang check on every print part.
