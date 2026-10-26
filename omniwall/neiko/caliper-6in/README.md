# Omniwall caliper holder (Neiko 6")

A holder that the Neiko 6" digital caliper hangs from, jaws up, with its back to
the wall and the display facing out. The slider head sits on a fork and the beam
hangs down through a slot that is open at the front. The fixed jaw hangs on the
slider's jaw, so the caliper always rests closed.

To take it out, lift it about 16 mm, until the thumb wheel clears its pocket
and the head clears the lip, then pull it forward. To put it back, slide the beam
into the slot from the front and lower the caliper until the head sits on the fork.

This is option B, jaws up on a fork. Zeid asked for it to hang, like the wire
stripper holder. The other option drawn was A, jaws down standing in a cup.

| | |
|---|---|
| Size | 75.9 × 28.1 × 50.5 mm (W × D × H): a 3 × 2 back plate with the fork at its foot |
| Hooks | 2 columns × 2 rows, Bridge hook 1U or Slot hook 1U (or a Slot hook 2U per column) |
| Files | `caliper_holder_*` |

## Fit

The caliper's sizes come from a STEP of it (`tool_outline.json` holds its front
outline part by part, with each part's thickness). The STEP is a cut-out style
model, so the sizes are envelopes:

- The slider head is 30 across at its flat bottom end and 14 thick, from its back
  to the display.
- The beam is 16 wide and 4 thick, and its back is 2 in front of the head's back.
- The thumb wheel is a 12 mm disc just under the head on the left, 7 thick.
- It is 290.5 long overall, which is long for a 6" caliper. Below the holder,
  the beam hangs about 200 mm down the wall.

The fork's top is 16 above the bed and the head's bottom end sits on it. The beam
has 0.75 clearance to each side of the slot. The wheel's pocket is the wheel's
outline 0.8 larger, carried straight up, with a 3.2 floor. The left tine runs in
front of the wheel, so the head rests on it there and on the right tine beside
the beam. A 4 mm lip along the front, 1 mm clear of the display face, stops the
head sliding forward. The wheel sits off to one side, so the caliper hangs off
centre and the fork is centred on the plate.

## How it hangs

It hangs like the trays and tool bins. The back plate is 10.075 mm thick and has
a dovetail pocket for each slot column (`dovetail_mount` in `../../panel.yaml`,
built by `pocket_void()` in `../../hook_geometry.py`). Each pocket is open at the
bottom and closed at the top with a 45° gable. There is a pair of 0.40 mm snap
ridges in every row; that height was print-tested upright. Slide the holder
down onto the hooks until the ridges click into the hooks' notches.

## Printing

It prints upright, as it hangs, standing on the plate and the fork. The slot
and the wheel pocket are open at the top, so nothing faces down: there are no
overhangs and no floating regions. Both were checked layer by layer. The bed
edges have a 0.5 mm chamfer against elephant's foot.

- `print/`: STEP and STL laid as on the bed, with the front toward the plate's
  front so Bambu Studio's "back" seam lands on the back plate. `caliper_holder_all_parts.3mf`
  is a Bambu Studio project with the settings in [`../../../bambu/`](../../../bambu/),
  plus the `print` section of `params.yaml` on top: 15% zig-zag infill, 4 walls,
  Arachne, seam at the back, 0.2 mm layers.
- `step/`: the holder in place, a stand-in for the caliper, and
  `caliper_holder_assembly.step` with the caliper and the Bridge hook 1Us.
- `test-prints/` (git-ignored, written by `build.py`):
  - `*_fork_coupon_print.*` is the holder's bottom 22 mm: the fork, the lip and a
    strip of plate. Hang the caliper in it by hand to check the fit before
    printing the whole holder.
  - `*_pocket_coupon_print.*` is the back plate around one pocket, to check the
    hook snap.

## Building

From this folder:

```
uv run --no-project --python 3.12 --with build123d --with pyyaml --with shapely python build.py
```

It writes `step/`, `print/`, `test-prints/` and `report.txt`. The report has
the measured checks:

- the caliper stand-in against the holder: no overlap, 1 mm from the head to the
  lip, 0.75 from the beam to the slot, 0.8 from the wheel to its pocket;
- the seat height under the head on both tines;
- how far to lift the caliper before it comes straight out;
- the hooks against the holder (they overlap only at the snap ridges);
- the overhang check on every print part.
