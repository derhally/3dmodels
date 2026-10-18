# Two-slot hook (test print)

A version of the [one-slot hook](../hook/) that carries on down into the next
vertical slot in line, so one hook holds in two slots one cell apart (Zeid's
idea, 2026-10-18). This folder is a test print: the hook plus a short housing
coupon, to check that it goes on, snaps and holds before any drawer changes.

## The hook

- **Top:** the one-slot hook's body fills the upper slot and rests on its bottom
  edge, with the finger behind the panel above it. It has no snap of its own.
- **Bottom:** one pitch (25.4 mm) lower, the one-slot hook's foot with its rim
  notch sits in the lower slot and snaps over that slot's bottom rim.
- **Front:** a spine joins the two across the steel between the slots, and one
  dovetail front runs the whole 45.7 mm. Its top and snap notches are where the
  one-slot hook's are, and a second notch pair one cell lower sits where a
  one-slot hook's notches would be in the lower slot. So one housing fits both:
  a pocket with ridges for two rows clicks onto two one-slot hooks or onto one
  two-slot hook (Zeid, 2026-10-18).

It is 2.95 × 11.15 × 45.7 mm, 826.2 mm³. The geometry is `two_slot_hook()` in
[hook_geometry.py](../hook_geometry.py), with its values in
[panel.yaml](../panel.yaml) (`two_slot_hook`, and `one_slot_hook` for everything
it shares).

## The coupon

A one-cell-wide slice (25.1 mm) of a 2-row housing back, 50.5 mm tall, with the
drawer housings' print-tested pocket and its second ridge pair one cell lower (`housing.pocket` in
[arc-drawer/params.yaml](../arc-drawer/params.yaml)). The pocket's closed top
rests on the hook's top, which puts the coupon's top and bottom edges 0.15 mm
inside the horizontal slot rows above and below. That is the lining-up a drawer
would get if it hung on this hook.

## Files

`build.py` writes these to `test-prints/`, which git ignores (test prints stay
local), plus `report.txt` here.

| File | What |
|---|---|
| `test-prints/two_slot_test_plate.3mf` | Hook and coupon on one plate, in print orientation |
| `test-prints/two_slot_hook_print.*`, `test-prints/two_slot_coupon_print.*` | Each part on its own (STEP, STL, 3MF) |
| `test-prints/two_slot_assembly.step` | Hook and coupon hung on a stand-in for the panel |
| `test-prints/one_slot_pair_assembly.step` | The same coupon on two one-slot hooks instead |
| `test-prints/two_slot_hook.step`, `test-prints/two_slot_coupon.step` | Each part in hook coordinates |
| `report.txt` | Sizes and the checks below |

Rebuild with
`uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py`
from this folder.

## Checks (report.txt)

- Hook vs panel 0.12 mm³: the rim notch is 1.5 mm wide on the 1.55 mm steel,
  the same 0.05 mm clamp as the printed one-slot and cross-slot hooks.
- Swinging the bottom in about the finger: the foot rides over the lower rim in
  the last 3° (up to 2.0 mm³, about what the one-slot hook's snap does). Between
  14° and 6° the top body's lower back corner rubs the upper rim by up to 0.2 mm,
  so the hook lifts that much while it swings.
- Coupon vs panel 0. On the two-slot hook and on two one-slot hooks the
  coupon's overlap is the same 0.28 mm³: both ridge pairs sit in notches either
  way. Sliding down onto the two-slot hook, the lower ridges ride the head's
  flank on the way (that is the click); on one-slot hooks they ride over the
  upper hook the same way.
- Print: hook on its flat side, coupon on its back. No floating regions. The
  coupon has nothing flatter than 45°. The hook has the same two small bridges
  as the one-slot hook (the neck's 0.95 mm under the head, and the bed-side
  notches' 0.23 mm roofs).

## Printing

PLA or PETG. The hooks print best on a 0.4 nozzle at 0.12 mm layers; the coupon
is fine at 0.2 mm. No supports, no brim needed.

## What to test

1. Put the hook on: finger through the upper slot and behind the panel, then
   push the bottom in until the lower foot clicks over the rim.
2. It should sit flat with no rattle in either slot, and need a deliberate pull
   at the bottom to come off.
3. Slide the coupon down onto it: it should click at the bottom, sit flush on
   the panel, and its top and bottom edges should line up with the horizontal
   slots.
4. Pull and twist the coupon to see whether one hook in two slots feels steadier
   than the one-slot hook.
5. If you have two one-slot hooks, hang them in the same two slots and check the
   same coupon clicks onto them as well.
