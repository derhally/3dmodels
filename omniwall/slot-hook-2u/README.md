# Slot hook 2U (test print)

A version of the [Slot hook 1U](../hook/) that carries on down into the next
vertical slot in line, so one hook holds in two slots one cell apart (Zeid's
idea, 2026-10-18). This folder is a test print: the hook plus a short housing
coupon, to check that it goes on, snaps and holds before any drawer changes.
Zeid has printed it and picked its lower-foot snap from two rounds of test
variants (below).

## The hook

- **Top:** Slot hook 1U's body fills the upper slot and rests on its bottom
  edge, with the finger behind the panel above it. It has no snap of its own.
- **Bottom:** one pitch (25.4 mm) lower, a foot with a rim notch sits in the
  lower slot and snaps over that slot's bottom rim. It started as Slot hook
  1U's, but that popped out too easily here, so it is firmer (see Lower-foot
  snap).
- **Front:** a spine joins the two across the steel between the slots, and one
  dovetail front runs the whole 45.7 mm. Its top and snap notches are where the
  Slot hook 1U's are, and a second notch pair one cell lower sits where a
  Slot hook 1U's notches would be in the lower slot. So one housing fits both:
  a pocket with ridges for two rows clicks onto a Slot hook 1U in each slot or onto one
  Slot hook 2U (Zeid, 2026-10-18).

The top body's gap (Slot hook 1U's flex gap, between the top bar and the
foot) is filled solid, since the top has no snap and needn't flex
(`slot_hook_2u.fill_top_gap`; false gives 3 mm fillets in its corners instead).
The lower foot's root has a 1.5 mm fillet, kept small so the foot still flexes
to snap. Filling the gap adds no contact with the panel while swinging the hook
on, checked about four pivot points. The two corners the panel's edges sit in (D:
the finger's front face meets the top; F: the top body's underside meets the
spine, over the steel between the slots) stay sharp: a fillet would push into
the steel, and a 0.5 mm relief groove (`fillets.d_relief`, `f_relief`, now 0)
cut the finger's root from 3.4 to 2.9 mm deep for little gain.

Every edge has a 0.5 mm chamfer on both sides, except the bottom end, the ramp
and rim notch (the snap's working faces) and the inside corners. The bed side
is chamfered too (`slot_hook_2u.bed_chamfer`): Zeid printed it next to the plain
one and it held the bed fine, with about 10% less first-layer area. The lower
foot's chamfer runs from its back, over its top and up the spine to the top
body (`lower_foot_chamfer`).

### Lower-foot snap

Slot hook 1U's foot (3.44 mm tall, a 1.5 mm rim notch on the 1.55 mm steel, a
lip 0.8 mm under the rim ending in a knife edge) let go too easily on this hook.
Two rounds of test variants, printed bed-chamfered (`params.yaml`
`snap_variants`, now empty, with both rounds recorded there), led to snap E,
Zeid's pick for the most satisfying snap and enough grip
(`slot_hook_2u.lower_foot` in panel.yaml):

| | Slot hook 1U | Slot hook 2U (E) |
|---|---|---|
| Foot height | 3.44 | 4.0 |
| Rim notch on the 1.55 steel | 1.5 (0.05 grip) | 1.45 (0.10 grip) |
| Lip under the rim | 0.8 | 0.9 |
| Lip tip | knife edge | 0.4 flat |

The hook's bottom is 0.1 mm lower to go with the deeper lip. Slot hook 1U is
unchanged.

It is 2.95 × 11.15 × 45.8 mm, 988.5 mm³. The geometry is `slot_hook_2u()` in
[hook_geometry.py](../hook_geometry.py), with its values in
[panel.yaml](../panel.yaml) (`slot_hook_2u`, and `slot_hook_1u` for everything
it shares).

## Bridge hook 2U

Bridge hook 1U's top sits 12.0 mm lower than Slot hook 1U's in the same slot, so
its snap misses the ridges of a housing made for slot hooks. Bridge hook 2U
raises its dovetail front 12.0 mm, to the upper slot's top, with a second notch
pair one cell lower; the part behind the panel is unchanged. 2.95 × 11.1 × 29.7
mm, 609.1 mm³. The front still has to run down to the foot (it's the only link
to it), so two Bridge hook 2Us, or a Bridge hook 2U over a Slot hook 1U,
can't go one row apart in the same column: they overlap by 4.3 mm. Swinging it
on clashes no more than Bridge hook 1U does.

## The coupon

A one-cell-wide slice (25.1 mm) of a 2-row housing back, 50.5 mm tall, with the
drawer housings' print-tested pocket and a ridge pair for each row (two here), one cell apart (`housing.pocket` in
[arc-drawer/params.yaml](../arc-drawer/params.yaml)). The pocket's closed top
rests on the hook's top, which puts the coupon's top and bottom edges 0.15 mm
inside the horizontal slot rows above and below. That is the lining-up a drawer
would get if it hung on this hook.

## Files

`build.py` writes these to `test-prints/`, which git ignores (test prints stay
local), plus `report.txt` here.

| File | What |
|---|---|
| `test-prints/slot_hook_2u_test_plate.3mf` | Slot hook 2U, the Bridge hook 2U and the coupon on one plate, in print orientation |
| `test-prints/slot_hook_2u_print.*`, `test-prints/slot_hook_2u_coupon_print.*` | Each part on its own (STEP, STL, 3MF) |
| `test-prints/slot_hook_2u_assembly.step` | Hook and coupon hung on a stand-in for the panel |
| `test-prints/slot_hook_1u_pair_assembly.step` | The same coupon on a Slot hook 1U in each slot instead |
| `test-prints/bridge_hook_2u_assembly.step`, `test-prints/bridge_hook_2u_print.*` | The Bridge hook 2U on the same coupon, and on its own for printing |
| `test-prints/slot_hook_2u.step`, `test-prints/slot_hook_2u_coupon.step` | Each part in hook coordinates |
| `report.txt` | Sizes and the checks below |

Rebuild with
`uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py`
from this folder.

## Checks (report.txt)

- Hook vs panel 0.27 mm³: the lower rim notch grips the steel by 0.10 mm.
- Swinging the bottom in about the finger: the foot rides over the lower rim in
  the last 3° (up to 3.0 mm³, against 2.0 for Slot hook 1U's foot; Zeid was
  fine with more force to put it on). Between
  14° and 6° the top body's lower back corner rubs the upper rim by up to 0.2 mm,
  so the hook lifts that much while it swings.
- Coupon vs panel 0. On Slot hook 2U, and on a Slot hook 1U in each slot, the
  coupon's overlap is the same 0.28 mm³: both ridge pairs sit in notches either
  way. Sliding down onto Slot hook 2U, the lower ridges ride the head's
  flank on the way (that is the click); on Slot hook 1Us they ride over the
  upper hook the same way.
- Print: hook on its flat side, coupon on its back. No floating regions. The
  coupon has nothing flatter than 45°. The hook has the same two small bridges
  as Slot hook 1U (the neck's 0.95 mm under the head, and the bed-side
  notches' 0.23 mm roofs).
- Slicer: Arachne walls, 5+ walls or 100% infill. Inner/outer/inner wall
  order suits it: the fit faces are outer walls and it keeps them accurate.

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
   than Slot hook 1U.
5. Do the same with the Bridge hook 2U (its top bar on the upper slot's bottom
   edge, foot under the lower slot's top edge).
6. If you have two Slot hook 1Us, hang one in each of the same two slots and check the
   same coupon clicks onto them as well.
