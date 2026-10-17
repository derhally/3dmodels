# Pocket fit test for the arc drawer: three short pocket coupons that print on
# their back like the housing, to choose the lip and ridge values before the
# housing is printed again. Run from omniwall\arc-drawer:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python pocket_variants.py
# Writes print/arc_drawer_pocket_variants.{step,stl,3mf}.
#
# Why: the first coupon (pocket_coupon_print) was loose and did not click. The
# 45 deg gable behind the lips started at the back of the lips (y 2.65) and, as
# the lips are only 0.55 thick where they overhang 0.75, cut them to a knife
# edge. Here the gable starts 0.1 lower (beside the spine, clear of its corner)
# and the lip flank sits closer to the hook's flank (flank_gap), so the lips keep
# 0.33 at their tip and grip the full 0.5 per side. The ridges are drawn in each
# layer's outline in this orientation, so the three coupons try three heights.
# A fourth coupon is the print-tested pocket unchanged (square lip backs, which
# leave a 0.75 mm ledge in this orientation), to see what the orientation alone does.
# Coupons are told apart by 1 to 4 grooves across the front face at the top.
import copy
import math
import os
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

HERE = Path(os.environ.get("ARC_DRAWER_DIR", r"E:\source\3dmodels\omniwall\arc-drawer"))
ROOT = HERE.parent
P = yaml.safe_load((HERE / "params.yaml").read_text())
panel = yaml.safe_load((ROOT / "panel.yaml").read_text())
exec((ROOT / "hook_geometry.py").read_text())
exec((ROOT / "core_3mf.py").read_text())

dm0 = panel["dovetail_mount"]
dv = dm0["dovetail"]
hook = panel["cross_slot_hook"]
PV = P["pocket_variants"]
HH = hook["height"]


def pocket_variant(ridge_height):
    dm = copy.deepcopy(dm0)
    pk = dm["pocket"]
    tested = ridge_height is None   # the print-tested pocket as it is, square lip backs (a 0.75 ledge on its back)
    if not tested:
        pk["spine_clearance"] = -PV["gable_drop"]      # lips' back starts beside the spine; the gable clears the spine
        pk["flank_gap"] = PV["flank_gap"]
        pk["ridge"]["height"] = ridge_height
    cx = dv["block_width"] / 2
    hh = dv["head_width"] / 2 + pk["side_clearance"]
    bw = dv["block_width"] / 2 + pk["side_clearance"]
    yb = dv["block_depth"] + pk["spine_clearance"]
    yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]
    zl = -PV["below_hook"]
    v = pocket_void(dm, HH, 0.0, zl)
    e = 0.02
    chan = Polygon((cx - bw - e, yb), (cx + bw + e, yb), (cx, yb + bw + e), align=None)
    floor = Polygon((cx - hh - e, yf), (cx + hh + e, yf), (cx, yf + hh + e), align=None)
    v = v + Pos(0, 0, zl) * extrude(floor, HH - zl)
    if not tested:
        v = v + Pos(0, 0, zl) * extrude(chan, HH - zl)
    return v, yf + hh


def coupon(ridge_height, marks):
    v, depth = pocket_variant(ridge_height)
    t = depth + PV["front_wall"]
    w = PV["width"]
    cx = dv["block_width"] / 2
    z0, z1 = -PV["below_hook"], HH + PV["roof"]
    body = Pos(cx - w / 2, 0, z0) * Box(w, t, z1 - z0, align=Align.MIN)
    body = body - v
    # Marks: 45 deg grooves across the front face near the top (print top surface).
    g = PV["mark_depth"]
    for k in range(marks):
        zc = z1 - 2.0 - k * 1.6
        tri = Polygon((t + 0.01, zc - g - 0.01), (t + 0.01, zc + g + 0.01), (t - g, zc), align=None)
        body = body - extrude(Plane.YZ.offset(cx - w / 2 + 1.5) * tri, w - 3, dir=(1, 0, 0))
    return body


def to_print(s):
    s = Rot(90, 0, 0) * s
    bb = s.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * s


parts = []
for i, rh in enumerate(PV["ridge_heights"] + [None], start=1):
    c = coupon(rh, i)
    c.label = f"pocket variant {i} " + ("tested pocket" if rh is None else f"ridge {rh}")
    parts.append((c, to_print(c)))

result = Compound(children=[p for p, _ in parts])
out = HERE / "print"
pr = [Pos(((i - 1) % 2) * 25.0, ((i - 1) // 2) * 25.0, 0) * p for i, (_, p) in enumerate(parts, start=1)]
export_step(Compound(children=pr), str(out / "arc_drawer_pocket_variants.step"))
export_stl(Compound(children=pr), str(out / "arc_drawer_pocket_variants.stl"))
write_3mf([(f"pocket variant {i}", *shape_mesh(p)) for i, p in enumerate(pr, start=1)],
          out / "arc_drawer_pocket_variants.3mf")
