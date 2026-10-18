# Slot hook 2 test print: the hook (../panel.yaml slot_hook_2), the tall bridge
# hook (bridge_hook.tall_front) and a housing
# coupon that slides down onto it, with a stand-in for the panel to check that
# everything clears. Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py
# Writes test-prints/ (local only, git-ignored): the hook and coupon in hook
# coordinates, the assembly with the panel, and each part in print orientation
# (STEP, STL and plain 3MF, plus both on one plate). Also report.txt.
# Hook coordinates: x across (hook's flat side at 0), y out from the back of the
# hook, z up from the upper slot's bottom edge.
import copy
import math
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
P = yaml.safe_load((HERE / "params.yaml").read_text())
panel = yaml.safe_load((ROOT / "panel.yaml").read_text())
drawer = yaml.safe_load((ROOT / "arc-drawer" / "params.yaml").read_text())
exec((ROOT / "hook_geometry.py").read_text())
exec((ROOT / "core_3mf.py").read_text())

_export_step = export_step


def export_step(shape, path):
    """build123d 0.13 refuses to write some labelled shapes to STEP; retry as a plain solid."""
    try:
        return _export_step(shape, path)
    except RuntimeError:
        return _export_step(Solid(shape.wrapped), path)


pitch, sl = panel["pitch"], panel["slot"]
one, ts, CP = panel["slot_hook_1"], panel["slot_hook_2"], P["coupon"]
dm = copy.deepcopy(panel["dovetail_mount"])
dv, pk = dm["dovetail"], dm["pocket"]
for k in ("spine_clearance", "flank_gap"):
    pk[k] = drawer["housing"]["pocket"][k]               # print-tested housing pocket (coupon 3)
pk["ridge"]["height"] = drawer["housing"]["pocket"]["ridge_height"]
yp = one["panel_front_y"]                                # panel front face
yb_panel = one["panel_back_y"]                           # panel back face
H = one["height"]                                        # hook top = top of the upper slot
d = one["printed"]["rim_notch"]["depth"]
zl = -ts["lower_rim_below"]
z_front = zl - d                                         # bottom of the dovetail front
Hf = H - z_front                                         # dovetail front height
cx = dv["block_width"] / 2
lines = []
log = lines.append

# The hook.
hk = slot_hook_2(panel, ROOT)
hk.label = "slot hook 2"
bb = hk.bounding_box()
log(f"hook: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm (z {bb.min.Z:.2f} to {bb.max.Z:.2f}), volume {hk.volume:.1f} mm3, solids {len(hk.solids())}, valid {hk.is_valid}")

# Panel stand-in: one column of two in-line vertical slots, the horizontal slots
# beside them, across two cells each side.
row_top = H + ts["top_to_slot_row"]                      # horizontal slot row above the hook
pw, ph = 2 * pitch, 3 * pitch
pnl = Pos(cx, (yb_panel + yp) / 2, row_top - ph / 2 - pitch / 2) * Box(pw, yp - yb_panel, ph)
cut = []
for z0 in (0.0, zl):                                     # the two vertical slots
    cut.append(Pos(cx, (yb_panel + yp) / 2, z0 + sl["length"] / 2) * Box(sl["width"], 5, sl["length"]))
for zr in (row_top, row_top - pitch, row_top - 2 * pitch):   # horizontal slots either side
    for xs in (cx - pitch / 2, cx + pitch / 2):
        cut.append(Pos(xs, (yb_panel + yp) / 2, zr) * Box(sl["length"], 5, sl["width"]))
for c in cut:
    pnl = pnl - c
pnl.label = "panel"

# Coupon: a slice of a housing back, its top edge just under the slot row above
# the hook, its bottom edge on the slot row `rows` pitches below.
eg = CP["edge_gap"]
z_top, z_bot = row_top - eg, row_top - CP["rows"] * pitch + eg
hh = dv["head_width"] / 2 + pk["side_clearance"]
yf = yp + dv["block_depth"] + dv["depth"] + pk["depth_clearance"]   # pocket floor (at its edges)
y_front = yf + hh + CP["back_front_wall"]                           # floor gable rises hh at the centre
cp = Pos(cx, (yp + y_front) / 2, (z_bot + z_top) / 2) * Box(CP["width"], y_front - yp, z_top - z_bot)
z_lo = z_bot - 1
void = Pos(0, 0, z_front) * pocket_void(dm, Hf, yp, z_lo - z_front)
# 45 deg gables on the spine channel's end and the pocket floor, so the coupon
# prints on its back like the drawer housings.
e, bw = 0.02, dv["block_width"] / 2 + pk["side_clearance"]
yb = yp + dv["block_depth"] + pk["spine_clearance"]
chan = Polygon((cx - bw - e, yb), (cx + bw + e, yb), (cx, yb + bw + e), align=None)
floor = Polygon((cx - hh - e, yf), (cx + hh + e, yf), (cx, yf + hh + e), align=None)
seat = H + pk["top_clearance"]
# A ridge pair every pitch lower, one per row, as in the drawer housings
# (housing.ridges_every_row): it clicks into a slot hook 1 in the lower slot, or
# into the lower notches of slot hook 2 and the tall bridge hook.
r = pk["ridge"]
y_ridge_end = yp + dv["block_depth"] + dv["depth"] - dv["notch"]["front_land"] - r["front_gap"]
for zc in (seat - r["below_top"] - k * pitch for k in range(1, CP["rows"])):
    for x_face, inward in ((cx + hh, -1), (cx - hh, 1)):
        void = void - v_groove_prism(x_face, inward, zc, yb, y_ridge_end, r["height"], r["flank_angle"], r["tip_radius"])
void = void + Pos(0, 0, z_lo) * extrude(chan, seat - z_lo) + Pos(0, 0, z_lo) * extrude(floor, seat - z_lo)
cp = cp - void
cp.label = "coupon"
cb = cp.bounding_box()
log(f"coupon: {cb.size.X:.2f} x {cb.size.Y:.2f} x {cb.size.Z:.2f} mm, volume {cp.volume:.1f} mm3, solids {len(cp.solids())}, valid {cp.is_valid}")
log(f"slot rows (horizontal slots) at z {row_top:.2f} and {row_top - pitch * CP['rows']:.2f}; coupon edges at {z_top:.2f} and {z_bot:.2f}; "
    f"seat (pocket top) at {seat:.2f}, {row_top - seat:.2f} below the slot row; roof above the seat {z_top - seat:.2f}")


def overlap(a, b):
    x = a & b
    if x is None:
        return 0.0
    return sum(s.volume for s in (x.solids() if hasattr(x, "solids") else [x]))


log(f"hook vs panel: {overlap(hk, pnl):.3f} mm3 (the rim notch is 1.5 wide on the 1.55 steel, a 0.05 clamp like the bridge hook's; slot hook 1 has the same)")
# Putting it on: finger through the upper slot and behind the panel, then the
# bottom swings in about the finger's hold until the lower foot snaps over the rim.
piv = Vector(0, yb_panel, H)
for a in (18, 14, 10, 8, 6, 4, 3, 2, 1):
    h = Pos(piv) * Rot(a, 0, 0) * Pos(-piv) * hk
    x = h & pnl
    sol = x.solids() if x else []
    parts = ", ".join(f"{s.volume:.2f} at z {s.bounding_box().min.Z:.1f}..{s.bounding_box().max.Z:.1f}" for s in sol if s.volume > 0.005)
    log(f"swing in, {a:2d} deg out: {sum(s.volume for s in sol):.2f} mm3 {parts}")
log(f"coupon vs panel: {overlap(cp, pnl):.3f} mm3")
log(f"hook vs coupon: {overlap(hk, cp):.3f} mm3 (the ridges reach {pk['ridge']['height'] - pk['side_clearance']:.3f} past the head's flank into its {dv['notch']['depth']} notches: a small overlap is expected)")
for label, dz in (("coupon 3 mm higher (sliding down, ridges not yet over the notches)", 3.0),):
    log(f"hook vs {label}: {overlap(hk, Pos(0, 0, dz) * cp):.3f} mm3")
# The same coupon on a slot hook 1 in each slot: the snaps must land in the same places.
ones = [Pos(0, 0, z) * slot_hook_1(panel, ROOT) for z in (0.0, zl)]
log(f"slot hook 1 in each slot vs coupon: {sum(overlap(o, cp) for o in ones):.3f} mm3 (both ridge pairs in notches); "
    f"3 mm higher: {sum(overlap(o, Pos(0, 0, 3.0) * cp) for o in ones):.3f} mm3; vs panel: {sum(overlap(o, pnl) for o in ones):.3f} mm3")
for o in ones:
    o.label = "slot hook 1"
# The bridge hook with its front raised (bridge_hook.tall_front): its top
# bar on the upper slot's bottom edge, its foot under the lower slot's top edge.
cs = panel["bridge_hook"]
place_cs = lambda s: Pos(0, yp - cs["panel_front_y"], -cs["bar_bottom"]) * s
tall = place_cs(bridge_hook(panel, ROOT, tall=True))
tall.label = "bridge hook, tall front"
tb = tall.bounding_box()
log(f"tall bridge hook: {tb.size.X:.2f} x {tb.size.Y:.2f} x {tb.size.Z:.2f} mm (z {tb.min.Z:.2f} to {tb.max.Z:.2f}), volume {tall.volume:.1f} mm3, solids {len(tall.solids())}, valid {tall.is_valid}")
log(f"tall bridge hook vs coupon: {overlap(tall, cp):.3f} mm3 (both ridge pairs in notches, as on the slot hooks); "
    f"the standard one: {overlap(place_cs(bridge_hook(panel, ROOT)), cp):.3f} mm3 (its top is {cs['tall_front']['rise']} lower, so the ridges pinch its flank)")
log(f"tall bridge hook stacked one row below another: {overlap(tall, Pos(0, 0, -pitch) * tall):.1f} mm3, "
    f"over a slot hook 1 in the slot below: {overlap(tall, ones[1]):.1f} mm3 (one per column)")


def bad_faces(part, limit=45.0):
    """Faces of a print-orientation part that face down flatter than `limit`
    degrees from vertical and are not on the bed: (deg from vertical, area, point)."""
    lim = -math.cos(math.radians(limit)) - 1e-3
    out = []
    for f in part.faces():
        worst, where = 1.0, None
        for u in (0.1, 0.5, 0.9):
            for w in (0.1, 0.5, 0.9):
                n = f.normal_at(u, w)
                p = f.position_at(u, w)
                if p.Z > 0.05 and n.Z < worst:
                    worst, where = n.Z, p
        if worst < lim:
            out.append((round(90 - math.degrees(math.acos(min(1, -worst))), 1), round(f.area, 2), where))
    return out


def to_bed(s):
    bb = s.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * s


OUT = HERE / "test-prints"
OUT.mkdir(exist_ok=True)
export_step(hk, str(OUT / "slot_hook_2.step"))
export_step(cp, str(OUT / "slot_hook_2_coupon.step"))
export_step(Compound(children=[pnl, hk, cp]), str(OUT / "slot_hook_2_assembly.step"))
export_step(Compound(children=[pnl, *ones, copy.copy(cp)]), str(OUT / "slot_hook_1_pair_assembly.step"))
export_step(Compound(children=[copy.copy(pnl), tall, copy.copy(cp)]), str(OUT / "bridge_hook_tall_assembly.step"))

hp = to_bed(Rot(0, -90, 0) * hk)        # on its flat side, like the other hooks
tp = to_bed(Rot(0, -90, 0) * tall)
cpp = to_bed(Rot(90, 0, 0) * cp)        # on its back, like the drawer housings
for part, stem in ((hp, "slot_hook_2_print"), (tp, "bridge_hook_tall_print"), (cpp, "slot_hook_2_coupon_print")):
    export_step(part, str(OUT / f"{stem}.step"))
    export_stl(part, str(OUT / f"{stem}.stl"))
    write_3mf([(stem, *shape_mesh(part))], OUT / f"{stem}.3mf")
    b = part.bounding_box()
    bad = bad_faces(part)
    log(f"{stem}: {b.size.X:.1f} x {b.size.Y:.1f} x {b.size.Z:.1f}, overhangs flatter than 45 deg: {len(bad)}"
        + (" (the neck's 0.95 mm bridge 0.75 above the bed and the bed-side snap notches' 0.23 roofs, as on the printed hooks)" if stem.endswith("hook_print") else ""))
    for x in sorted(bad, key=lambda t: -t[1])[:10]:
        log(f"    {x[0]:.1f} deg from vertical, area {x[1]} mm2, at ({x[2].X:.1f}, {x[2].Y:.1f}, {x[2].Z:.1f})")
hb, cb, tb = hp.bounding_box(), cpp.bounding_box(), tp.bounding_box()
write_3mf([("slot hook 2", *shape_mesh(hp, -(cb.size.X / 2 + 8 + hb.size.X / 2), 0)), ("coupon", *shape_mesh(cpp)),
           ("tall bridge hook", *shape_mesh(tp, -(cb.size.X / 2 + 8 + hb.size.X / 2), hb.size.Y / 2 + 6 + tb.size.Y / 2))],
          OUT / "slot_hook_2_test_plate.3mf")
(HERE / "report.txt").write_text("\n".join(lines) + "\n")
result = Compound(children=[pnl, hk, cp])
