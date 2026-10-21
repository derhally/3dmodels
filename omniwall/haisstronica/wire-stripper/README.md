# Omniwall wire stripper holder

A holder for the Haisstronica 3-in-1 self-adjusting wire stripper (the blue and
yellow one with the clear length stop). The stripper hangs jaws down with its
back to the wall. Two prongs catch the bottoms of the blue grips and the black
head hangs between them, so the whole tool stays in view and comes straight up
out of the holder.

This is option B, the shoulder fork. Zeid picked it from four drawn options
(head-down cup, shoulder fork, side-on sleeve, wedge saddle).

| | |
|---|---|
| Size | 75.9 × 30.6 × 71 mm (W × D × H): a 3 × 2 back plate, 50.5 tall, with legs 20.5 below it |
| Hooks | 2 columns × 2 rows, Bridge hook 1U or Slot hook 1U (or a Slot hook 2U per column) |
| Files | `stripper_holder_*` |

## Fit

The tool's sizes are in `params.yaml`, each with its source. Haisstronica
publishes none, so they come from Zeid's calipers and his photos:

- J to G is 50. J is the jaw end; G is the low inner corner of each blue grip's
  bottom, against the black head.
- J to C is 53. C is the grip bottom's outer corner.
- The head is 48.5 wide at its widest.
- The grips measure 61.4 across at the pins and are 16 thick front to back.
- The bump on the back is 28.25 × 10.13, 2.7 proud, starting 33.5 from J.

The grip bottoms aren't square to the tool: they rise about 3 mm from G to C.
Each prong's seat slopes the same way, up and out from G at the side of the
head. The build works the angle out from the measurements (about 25°). The
grips sit flat on the seats, and the two seats form a V that centres the tool.
A 4 mm lip at the front of each prong, 1.5 mm clear of the grips, stops the tool
sliding forward. The head has 1.5 mm to each prong.

The back plate sits entirely above the bump. Between the legs, the plate's
bottom edge is a 45° gable that clears the bump by 1.6 mm. Each leg's inner face
reaches 18 mm from the tool's centre line, behind the head.

## How it hangs

Like the trays and tool bins: the back plate is 10.075 mm thick and carries one
dovetail pocket per slot column (`dovetail_mount` in `../../panel.yaml`, built by
`pocket_void()` in `../../hook_geometry.py`, with the drawer housing's print-tested
flank gap, and 0.40 mm snap ridges, print-tested upright: the drawer housing's 0.53 mm, tested printed on its back, jammed the hooks printed upright). Each pocket is open at the bottom and closed
at the top with a 45° gable. There is a ridge pair in every row. Slide the
holder down onto the hooks until the ridges click into the hooks' notches.
The pockets open on the slope of the gable between the legs, so on the uphill
side the plate and the neck lip climb at 45° from the pocket floor towards the
back face; nothing there starts in mid air (Bambu Studio flagged the plain cut as
floating), at the cost of the lowest 3–4 mm of that one lip on the bottom hook.

## Printing

It prints upright, as it hangs, standing on the legs' feet. No supports:
nothing faces down flatter than 45° from vertical, checked face by face. The
prongs' undersides are 45° or steeper. The bed edges have a 0.5 mm chamfer
against elephant's foot.

- `print/`: STEP and STL laid as on the bed, and `stripper_holder_all_parts.3mf`.
  That file is a Bambu Studio project with the settings of
  [`../../../bambu/`](../../../bambu/), plus `print` in `params.yaml` on top: 15%
  zig-zag infill, 4 walls, Arachne, seam at the back, 0.2 mm layers.
- `step/`: the holder in place, a stand-in for the stripper, and
  `stripper_holder_assembly.step` with the stripper and the Bridge hook 1Us it
  hangs on.
- `test-prints/` (git-ignored, written by `build.py`):
  - `*_seat_coupon_print.*` is the holder's bottom 42 mm with both prongs. Set
    the stripper in it by hand to check the seats before printing the whole
    holder.
  - `*_pocket_coupon_print.*` is the back plate round one pocket, to check the
    hook snap.
  - `*_ridge_coupons.3mf`: four upright pocket coupons with 0.30 to 0.45 mm ridges (height engraved on top, in hundredths), to pick the ridge height; 0.40 felt best.

## Building

From this folder:

```
uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py
```

It writes `step/`, `print/`, `test-prints/` and `report.txt`. The report has
the measured checks:

- the seat heights against the slope;
- the stand-in stripper against the holder (no overlap);
- the head's clearance to the prongs, and the bump's clearance to the plate;
- the hooks against the holder (only the snap ridges' overlap into the notches);
- the overhang check on every print part.

`tool_outline.json` is the stripper's outline traced from Zeid's photo. It is
used only for the stand-in.
