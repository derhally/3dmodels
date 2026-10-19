# build123d script for create_model (params = pocket-test/params.yaml).
# Builds the test plate: two dovetail pockets with snap ridges, one or more cells
# apart, that slide down onto two identical hooks of either kind. MODE =
# "assembly" gives the plate with two hooks (HOOK = "bridge" for Bridge hook 1U or
# "slot_1u" for Slot hook 1U)
# in place for a clash check; "print" gives the plate alone, upside down (closed
# pocket tops on the bed, so nothing overhangs). Pocket and hooks come from
# ../panel.yaml through ../hook_geometry.py.
from pathlib import Path
import yaml

MODE = "assembly"
HOOK = "bridge"
ROOT = Path(r"E:\source\3dmodels\omniwall")
panel = yaml.safe_load((ROOT / "panel.yaml").read_text())
hook = panel["bridge_hook"]       # the tallest hook sets the pocket length
dm = panel["dovetail_mount"]
dv, pk = dm["dovetail"], dm["pocket"]
pl = params["plate"]
exec((ROOT / "hook_geometry.py").read_text())

H = hook["height"]
spacing = pl["hook_spacing_cells"] * panel["pitch"]
place_right = lambda s: Pos(spacing, 0, 0) * s
cx = dv["block_width"] / 2                           # head centre (centred on the hooks)
half = dv["head_width"] / 2 + pk["side_clearance"]
yb = hook["panel_front_y"]                           # plate back face flush on the panel
yf = yb + dv["block_depth"] + dv["depth"] + pk["depth_clearance"]   # pocket floor
x0 = cx - half - pl["side_wall"]
x1 = spacing + cx + half + pl["side_wall"]
y1 = yf + pl["front_wall"]
z0 = -pl["below_hook"]
z1 = H + pk["top_clearance"] + pl["roof"]
plate = Pos((x0 + x1) / 2, (yb + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - yb, z1 - z0)
pocket = pocket_void(dm, H, hook["panel_front_y"], z0 - 1)
plate = plate - pocket - place_right(pocket)
plate.label = "pocket test plate"

if MODE == "print":
    p = Rot(X=180) * plate
    bb = p.bounding_box()
    result = Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * p
else:
    # Stand-ins: the printed hooks in both slots, their tops against the pocket tops.
    h1 = bridge_hook(panel, ROOT) if HOOK == "bridge" else slot_hook_1u(panel, ROOT)
    hk = panel["bridge_hook" if HOOK == "bridge" else "slot_hook_1u"]
    h1 = Pos(0, hook["panel_front_y"] - hk["panel_front_y"], H - hk["height"]) * h1
    h1.label = "hook left"
    h2 = place_right(h1)
    h2.label = "hook right"
    result = Compound(children=[plate, h1, h2])
