# Omniwall wall trays

Low trays for small parts that hang on the panel next to the arc drawers, on
the same hooks. They are one row tall and 60 mm deep, so they line up with the
60 mm drawer housings and tile with them (width = cells × 25.4 − 0.3). The
brief: minimal, no sharp edges, a lip so nothing falls off, curved insides for
scooping, and low side walls (trays, not bins). Every outside edge is rounded,
the side walls fall from the back wall to the lip in one S-curve, and the
outside bottom edge is a 45° chamfer rolling into a 4 mm radius.

Four trays, picked from five concepts
([concept sheet](https://claude.ai/artifact/KD8Tn5Qnvgaf2kHGjBgh8A)):

| Tray | Folder, file prefix | W × D × H, mm | Lip | Inside | Hook columns |
|---|---|---|---|---|---|
| Cove 3 × 1 | [`cove-3x1/`](cove-3x1/), `tray_cove_3x1_*` | 75.9 × 60 × 25.1 | 14.2 | flat 3 mm floor, R10 cove into every wall | 2 |
| Ramp 3 × 1 | [`ramp-3x1/`](ramp-3x1/), `tray_ramp_3x1_*` | 75.9 × 60 × 25.1 | 10 | floor tilts 6° down to the back wall, R10 into it, 2.6 mm bead at the front | 2 |
| Ramp 6 × 1 | [`ramp-6x1/`](ramp-6x1/), `tray_ramp_6x1_*` | 152.1 × 60 × 25.1 | 7.5 | the Ramp with less scoop: 3° tilt, R5 into the back wall | 5 |
| Lift-out dish 3 × 1 | [`dish-3x1/`](dish-3x1/), `tray_dish_3x1_*` | cradle 75.9 × 60 × 25.1, dish 70.3 × 46.7 × 12.6 | cradle 7, dish 15 | loose dish with R7.5 coves and a 3 mm pour dip in its front lip, 0.4 mm clearance in the cradle | 2 |

The Ramp's front inside corners keep a small crease where the tilted floor
meets the rounded corners (the cove fillet fails there).

## Hardware

Hooks only, no screws: a Bridge hook 1U or a Slot hook 1U (`../hook/`) in every
slot column inside the tray (2 for 3 cells, 5 for 6 cells), all in the same
slot row.

## How it hangs

The back wall is 10.075 mm thick and carries one dovetail pocket per slot
column, the same pocket as the drawer housings (`dovetail_mount` in
`../panel.yaml`, built by `pocket_void()` in `../hook_geometry.py`, with the
housing's print-tested flank gap, and 0.40 mm snap ridges, print-tested upright:
the housing's 0.53 mm jammed printed upright). Each pocket is open at the bottom
and closed at the top; slide the tray down onto the hooks until the snap ridges
click into the hooks' notches. The tray's bottom edge sits on a
peg-hole row, so the hooks sit 3.3 mm above it, as in a drawer housing's bottom
row.

Because the trays print upright, the pocket's closed top is a 45° gable instead
of a flat bridge. The gable passes through the hook's top corners at the seat
height (21.0 mm), so the tray hangs exactly where a flat seat would put it; it
meets the pocket walls 0.25 mm lower. The pocket's spine channel keeps
`panel.yaml`'s 0.15 mm clearance rather than the housing's −0.1 mm, which only
works with the gable a housing printed on its back has behind the lips.

## Printing

Every part prints upright, as it hangs, with no supports (checked face by face
on the print-orientation parts: nothing faces down flatter than 45° from
vertical). PLA or PETG, 0.2 mm layers, 3+ walls.

- `print/`: STEP and STL of each part laid as on the bed, and one
  `*_all_parts.3mf` with every part on one plate (the dish tray's cradle and
  dish side by side, far enough apart to print by object).
- `step/`: the parts in place for CAD, and `*_assembly.step` with the Bridge
  hook 1Us they hang on.
- `test-prints/` (git-ignored, written by `build.py`): a pocket coupon, the back
  wall round one pocket, printed upright like the tray. Print it first to check
  the snap before a whole tray: the drawer housings' pockets were tested printed
  on their back, not upright.

## Building

`params.yaml` holds the shared values with their sources; each tray folder's
`params.yaml` sets its style and only what differs (the 6-cell Ramp sets
`cells: 6` and its shallower ramp). From this folder:

```
uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py ramp-6x1
```

It writes the folder's `step/`, `print/`, `test-prints/` and `report.txt`. The
report has the measured checks: pocket gables and their heights, hooks against
the tray (only the snap ridges' 0.07 mm³ per ridge into the notches), dish
against cradle, and the overhang check on every print part.
