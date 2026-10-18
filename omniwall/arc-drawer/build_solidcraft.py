r"""SolidCraft version of the Omniwall arc-pocket drawer.

Reads the same params.yaml and ../panel.yaml as build.py and writes
solidcraft/solidcraft_commands.json: the SolidCraft commands (as the MCP `batch` tool
takes them, run against an empty design) that build the housing and the drawer in unit
coordinates (x across from the left outer face, y out from the panel face, z up
from the unit's bottom edge), the same frame build.py uses.

SolidCraft sketch points take plain numbers, not expressions, so every position
is computed here from the params and written into the commands. To change the
design, edit params.yaml and run this script again. The track's arcs are drawn as
polylines within 0.003 mm of the true arcs (see `arc`); everything else is exact.
After the build the commands also place drawer copies open, tilted and lifted,
run SolidCraft's interference check on each against the housing, and make the
print-orientation copies housing_print and drawer_print.

    uv run --no-project --with pyyaml python build_solidcraft.py   (any Python 3 with PyYAML)
"""
import json
import math
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
P = yaml.safe_load((HERE / "params.yaml").read_text())
panel = yaml.safe_load((HERE.parent / "panel.yaml").read_text())

pitch = panel["pitch"]
hook = panel["bridge_hook"]
dm = panel["dovetail_mount"]
dv, pk = dm["dovetail"], dm["pocket"]
U, HS, DR, PN, TR, LP, LB = (P[k] for k in ("unit", "housing", "drawer", "pins", "track", "lip", "label"))
K = math.sqrt(2)

# ---- derived numbers: the same formulas as build.py ----
W = U["cells"] * pitch - U["gap"]
H = U["rows"] * pitch - U["gap"]
D = U["depth"]
edge = U["gap"] / 2
hook_z0 = (pitch - panel["slot"]["length"] / 2) - hook["bar_bottom"] - edge
hook_cols = [k * pitch - edge for k in range(1, U["cells"])]
hook_rows = [hook_z0 + r * pitch for r in range(U["rows"])]
HH = hook["height"]
seat_z = hook_rows[-1] + HH + pk["top_clearance"]
cx = dv["block_width"] / 2
sc = pk["side_clearance"]
hh = dv["head_width"] / 2 + sc
hn = dv["neck_width"] / 2 + sc
bw = dv["block_width"] / 2 + sc
yb = dv["block_depth"] + pk["spine_clearance"]
yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]
plate_t = yf + hh + HS["back_front_wall"]

z_floor = HS["floor"]
z_roof = H - HS["roof"]
y_back = plate_t + DR["back_clearance"]
y_pin = y_back + PN["from_back"]
z_pin = PN["height"]
y_stop = TR["stop"]
piv = (D, z_floor)
rv = PN["diameter"] / 2 + TR["clearance"]
R = math.hypot(y_stop - piv[0], z_pin - piv[1])
a0 = math.degrees(math.atan2(z_pin - piv[1], y_stop - piv[0]))
tilt = TR["tilt"]
a1 = a0 - tilt
pin_end = (piv[0] + R * math.cos(math.radians(a1)), piv[1] + R * math.sin(math.radians(a1)))
arc_top = pin_end[1] + rv
exit_z = arc_top + TR["exit_web"] + K * rv
notch_y = y_stop - TR["notch_back"]
body_top = z_roof - DR["headroom"]
plate_top = z_roof - DR["top_gap"]
lift = exit_z - z_pin
shoulder_z = z_roof - lift - DR["lift_clearance"]

cmds = []


def r6(v):
    return round(float(v), 6)


def pt(u, v):
    return [r6(u), r6(v)]


def add(command, **params):
    cmds.append({"command": command, "params": params})


def plane_x(x):
    """Sketch plane square to x at x: sketch u = world y, v = world z, normal +x."""
    return {"origin": [r6(x), 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}


def sketch(plane, name):
    add("sketch.create", plane=plane, name=name)


def poly(points):
    add("sketch.line", points=[pt(*p) for p in points], closed=True)


def rect(u0, v0, u1, v1):
    add("sketch.rectangle.two_point", p0=pt(u0, v0), p1=pt(u1, v1))


def rot(p, ang, about):
    a = math.radians(ang)
    du, dv_ = p[0] - about[0], p[1] - about[1]
    return (about[0] + du * math.cos(a) - dv_ * math.sin(a), about[1] + du * math.sin(a) + dv_ * math.cos(a))


POLY = {"on": False}     # True while drawing the track: arcs become inscribed polylines
SAG = 0.003              # mm, largest gap between such a polyline and its true arc


def arc(center, start, sweep, end=None):
    """Arc about `center` from `start`, `sweep` degrees (ccw positive). While
    POLY is on it is drawn as an inscribed polyline whose chords stay within SAG
    of the arc. The groove and its print ramp meet at shallow angles near the
    groove floor, and SolidCraft's boolean can only resolve that between planar
    faces ("the exact fallback ... takes planar faces only"), so the whole track
    is drawn with polylines."""
    if not POLY["on"]:
        add("sketch.arc.center_point", center=pt(*center), start=pt(*start), sweep=r6(sweep))
        return
    r = math.hypot(start[0] - center[0], start[1] - center[1])
    step = 2 * math.degrees(math.acos(1 - SAG / r))
    n = max(2, math.ceil(abs(sweep) / step))
    a0_ = math.atan2(start[1] - center[1], start[0] - center[0])
    pts = [start] + [(center[0] + r * math.cos(a0_ + math.radians(sweep) * k / n),
                      center[1] + r * math.sin(a0_ + math.radians(sweep) * k / n)) for k in range(1, n)]
    pts.append(end if end is not None else (center[0] + r * math.cos(a0_ + math.radians(sweep)),
                                            center[1] + r * math.sin(a0_ + math.radians(sweep))))
    add("sketch.line", points=[pt(*p) for p in pts])


def teardrop(r, u, v, ang=0.0, about=None):
    """Circle of radius r at (u, v) with a 45 deg point straight down, turned by
    ang degrees about `about`: one 270 deg arc and two lines tangent to it."""
    c = r / K
    A, B, apex, C = (u + c, v - c), (u - c, v - c), (u, v - K * r), (u, v)
    if ang:
        A, B, apex, C = (rot(p, ang, about) for p in (A, B, apex, C))
    arc(C, A, 270, end=B)
    add("sketch.line", points=[pt(*B), pt(*apex), pt(*A)])


def track_profiles(du=0.0, pieces=(0, 1, 2, 3)):
    """The track region in the y-z plane (shifted du along y), drawn as four
    closed outlines that overlap: 0 groove + its end, 1 arc sector, 2 the end
    section turned with the drawer, 3 lift notch + exit channel."""
    s = du
    c = rv / K
    if 0 in pieces:   # straight groove from the back plate to the stop, ending in the pin section
        add("sketch.line", points=[pt(y_stop + c + s, z_pin - c), pt(y_stop + s, z_pin - K * rv),
                                   pt(plate_t + s, z_pin - K * rv), pt(plate_t + s, z_pin + rv),
                                   pt(y_stop + s, z_pin + rv)])
        arc((y_stop + s, z_pin), (y_stop + c + s, z_pin - c), 135, end=(y_stop + s, z_pin + rv))
    P = (piv[0] + s, piv[1])
    if 1 in pieces:   # arc: annular sector about the sill from a1 to a0
        on = lambda rr, a: (P[0] + rr * math.cos(math.radians(a)), P[1] + rr * math.sin(math.radians(a)))
        ro, ri = R + rv, R - rv
        arc(P, on(ro, a1), tilt, end=on(ro, a0))
        add("sketch.line", points=[pt(*on(ro, a0)), pt(*on(ri, a0))])
        arc(P, on(ri, a0), -tilt, end=on(ri, a1))
        add("sketch.line", points=[pt(*on(ri, a1)), pt(*on(ro, a1))])
    if 2 in pieces:   # end of the arc: the pin section turned with the drawer
        teardrop(rv, y_stop + s, z_pin, -tilt, P)
    if 3 in pieces:   # lift notch (section swept up) with the exit channel (swept forward, open at the front)
        nl, nr = notch_y - rv + s, notch_y + rv + s
        add("sketch.line", points=[pt(notch_y + s, exit_z + rv), pt(D + 1 + s, exit_z + rv), pt(D + 1 + s, exit_z - K * rv),
                                   pt(nr, exit_z - K * rv), pt(nr, z_pin), pt(nl, z_pin), pt(nl, exit_z)])
        arc((notch_y + s, exit_z), (nl, exit_z), -90, end=(notch_y + s, exit_z + rv))


def box(corner, size, op, name, body_name=None, targets=None):
    p = {"length": r6(size[0]), "width": r6(size[1]), "height": r6(size[2]),
         "corner": [r6(v) for v in corner], "operation": op, "name": name}
    if body_name:
        p["body_name"] = body_name
    if targets:
        p["targets"] = targets
    cmds.append({"command": "solid.box", "params": p})


# ---------------- housing ----------------
s = HS["side"]
box((0, 0, 0), (W, D, H), "new", "Housing block", body_name="housing")
box((s, plate_t, z_floor), (W - 2 * s, D, z_roof - z_floor), "cut", "Housing bay", targets=["housing"])

e = 0.02
run = (hh - hn) * math.tan(math.radians(dv["flank_angle"]))
y_flank = yf - (dv["head_flat"] + pk["flank_gap"])
y_neck = y_flank - run
y_neck_back = dv["block_depth"] - 0.1
r = pk["ridge"]
th = math.radians(r["flank_angle"])
embed = 0.2
apex = r["height"] + r["tip_radius"] * (1 / math.cos(th) - 1)
ra = (apex + embed) / math.tan(th)
y_ridge_end = dv["block_depth"] + dv["depth"] - dv["notch"]["front_land"] - r["front_gap"]
ridge_z = [seat_z - r["below_top"]]
if HS["second_ridges"] and U["rows"] > 1:
    ridge_z.append(seat_z - r["below_top"] - pitch)
zl = -1.0
for i, xc in enumerate(hook_cols, 1):
    # Dovetail slot and spine channel, open at the bottom, closed seat at seat_z.
    sketch("XY", f"Pocket {i} slot")
    poly([(xc - hn, y_neck_back), (xc + hn, y_neck_back), (xc + hn, y_neck), (xc + hh, y_flank),
          (xc + hh, yf), (xc - hh, yf), (xc - hh, y_flank), (xc - hn, y_neck)])
    rect(xc - bw, -1, xc + bw, yb)
    add("sketch.finish")
    add("solid.extrude", profiles="all", distance=r6(seat_z - zl), start_offset=r6(zl), operation="cut",
        targets=["housing"], name=f"Pocket {i} slot")
    # Snap ridges on both slot walls, for each hook row.
    for j, zc in enumerate(ridge_z, 1):
        for side, (x_face, inward) in (("L", (xc - hh, 1)), ("R", (xc + hh, -1))):
            nm = f"Pocket {i} ridge {j}{side}"
            # u along +-z, v into the slot; normal = u x v = +y.
            sketch({"origin": [r6(x_face), r6(yb), r6(zc)], "x_dir": [0, 0, inward], "y_dir": [inward, 0, 0]}, nm)
            poly([(-ra, -embed), (ra, -embed), (0, apex)])
            add("sketch.fillet", point="l2.end", radius=r6(r["tip_radius"]))
            add("sketch.finish")
            add("solid.extrude", profiles="all", distance=r6(y_ridge_end - yb), operation="join",
                targets=["housing"], name=nm)
    # 45 deg gables on the spine channel's end and the slot floor (the housing prints on its back).
    sketch("XY", f"Pocket {i} gables")
    poly([(xc - bw - e, yb), (xc + bw + e, yb), (xc, yb + bw + e)])
    poly([(xc - hh - e, yf), (xc + hh + e, yf), (xc, yf + hh + e)])
    add("sketch.finish")
    add("solid.extrude", profiles="all", distance=r6(seat_z - zl), start_offset=r6(zl), operation="cut",
        targets=["housing"], name=f"Pocket {i} gables")

# Track in the left wall, then mirrored to the right wall.
dp = TR["depth"]
POLY["on"] = True
sketch(plane_x(s - dp), "Track")
track_profiles()
add("sketch.finish")
add("solid.extrude", profiles="all", distance=r6(dp + 0.1), operation="new", name="Track groove", body_name="track_L")
# Print relief: every ceiling becomes one 45 deg ramp from the groove floor up to
# the wall face (section shifted +y by d at depth d), so each layer is attached
# to the outer wall. Each outline is swept from just past the wall face back to
# just above the groove floor (RAMP_PAST, RAMP_START keep the ramp's end faces
# off the groove's and the bay's), one body per outline, because SolidCraft
# cannot fuse them with the groove first.
RAMP_START, RAMP_PAST = 0.005, 0.05
sketch({"origin": [0, 0, r6(z_pin)], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, "Track ramp path")
add("sketch.line", points=[pt(s + RAMP_PAST, plate_t + dp + RAMP_PAST), pt(s - dp + RAMP_START, plate_t + RAMP_START)])
add("sketch.finish")
for k, label in enumerate(("groove", "arc", "arc end", "notch")):
    sketch(plane_x(s + RAMP_PAST), f"Track ramp {label}")
    track_profiles(du=dp + RAMP_PAST, pieces=(k,))
    add("sketch.finish")
    add("solid.sweep", sketch=f"Track ramp {label}", profiles="all", path_sketch="Track ramp path", path=["l1"],
        orientation="parallel", operation="new", name=f"Track ramp {label}", body_name=f"ramp_{k}_L")
POLY["on"] = False
track_bodies = ["track_L"] + [f"ramp_{k}_L" for k in range(4)]
add("solid.mirror", bodies=track_bodies, plane={"origin": [r6(W / 2), 0, 0], "normal": [1, 0, 0]})
for b_ in track_bodies:
    add("solid.combine", target="housing", tools=[b_], operation="cut")
for b_ in track_bodies:
    add("solid.combine", target="housing", tools=[b_ + " (2)"], operation="cut")

# ---------------- drawer ----------------
c = DR["side_clearance"]
x0, x1 = s + c, W - s - c
w, fl, ft = DR["wall"], DR["floor"], DR["front_thickness"]
y_front = D - ft
box((x0, y_back, z_floor), (x1 - x0, y_front - y_back, body_top - z_floor), "new", "Drawer body", body_name="drawer")
box((x0 - 1, y_back - 1, shoulder_z), (x1 - x0 + 2, DR["shoulder_length"] + 1, body_top), "cut", "Drawer shoulder", targets=["drawer"])
box((x0 + w, y_back + w, z_floor + fl), (x1 - x0 - 2 * w, y_front - y_back - w, body_top), "cut", "Drawer bin", targets=["drawer"])
box((x0, y_front, z_floor), (x1 - x0, ft, plate_top - z_floor), "join", "Drawer front", targets=["drawer"])
pr, fh = LP["proud"], LP["front_height"]
sketch(plane_x(x0), "Lip")
poly([(D - 1, plate_top - pr - fh - 1), (D, plate_top - pr - fh), (D + pr, plate_top - fh), (D + pr, plate_top), (D - 1, plate_top)])
add("sketch.finish")
add("solid.extrude", profiles="all", distance=r6(x1 - x0), operation="join", targets=["drawer"], name="Lip")
# Label holder: bottom rail with a 45 deg underside, side rails wrapping the label's edges.
xm = (x0 + x1) / 2
rail, ret = LB["rail"], LB["return"]
hd = rail + LB["thickness"] + LB["thickness_clearance"]
inner = LB["width"] + 2 * LB["side_clearance"]
za = z_floor + LB["bottom_clear"]
z_seat = za + hd + rail
z_top = z_seat + LB["height"] + LB["top_clear"]
half = inner / 2 + rail
sketch(plane_x(xm - half), "Label rail")
poly([(D - 1, za), (D, za), (D + hd, za + hd), (D + hd, z_seat), (D - 1, z_seat)])
add("sketch.finish")
add("solid.extrude", profiles="all", distance=r6(2 * half), operation="join", targets=["drawer"], name="Label rail")
hz = z_top - z_seat + 0.1
box((xm - half, D - 1, z_seat - 0.1), (rail, hd + 1, hz), "join", "Label post L", targets=["drawer"])
box((xm - half + rail - 0.01, D + hd - rail, z_seat - 0.1), (ret + 0.01, rail, hz), "join", "Label wrap L", targets=["drawer"])
box((xm + half - rail, D - 1, z_seat - 0.1), (rail, hd + 1, hz), "join", "Label post R", targets=["drawer"])
box((xm + half - rail - ret, D + hd - rail, z_seat - 0.1), (ret + 0.01, rail, hz), "join", "Label wrap R", targets=["drawer"])
# Teardrop pins, point down, reaching PN.reach into the grooves.
x_tip = s - PN["reach"]
pin_len = x0 + 0.5 - x_tip
for nm, xs in (("Pin L", x_tip), ("Pin R", W - x_tip - pin_len)):
    sketch(plane_x(xs), nm)
    teardrop(PN["diameter"] / 2, y_pin, z_pin)
    add("sketch.finish")
    add("solid.extrude", profiles="all", distance=r6(pin_len), operation="join", targets=["drawer"], name=nm)

# ---------------- drawer positions (for clash checks) and print copies ----------------
travel = y_stop - y_pin
add("solid.move", bodies=["drawer"], translate=[0, r6(travel), 0], copy=True)
add("body.rename", body="drawer (2)", name="drawer_open")
# tilted: the open drawer turned nose-down about the sill (move to the origin, turn, move back)
add("solid.move", bodies=["drawer_open"], translate=[0, r6(-piv[0]), r6(-piv[1])], copy=True)
add("body.rename", body="drawer_open (2)", name="drawer_tilted")
add("solid.move", bodies=["drawer_tilted"], axis=[1, 0, 0], angle=f"{r6(-tilt)} deg")
add("solid.move", bodies=["drawer_tilted"], translate=[0, r6(piv[0]), r6(piv[1])])
# lifted: pushed back to the notch and raised into the exit channel
add("solid.move", bodies=["drawer"], translate=[0, r6(travel - TR["notch_back"]), r6(lift)], copy=True)
add("body.rename", body="drawer (2)", name="drawer_lifted")
add("inspect.interference", bodies=["housing", "drawer"])
for st in ("open", "tilted", "lifted"):
    add("inspect.interference", bodies=["housing", f"drawer_{st}"])
# Print orientation: housing on its back (panel side on the bed), drawer upright; centred on the origin.
add("solid.move", bodies=["housing"], axis=[1, 0, 0], angle="90 deg", copy=True)
add("body.rename", body="housing (2)", name="housing_print")
add("solid.move", bodies=["housing_print"], translate=[r6(-W / 2), r6(H / 2), 0])
add("solid.move", bodies=["drawer"], translate=[r6(-W / 2), r6(-(y_back + D + LP["proud"]) / 2), r6(-z_floor)], copy=True)
add("body.rename", body="drawer (2)", name="drawer_print")
add("browser.visibility", visible=False, items=["drawer_open", "drawer_tilted", "drawer_lifted", "housing_print", "drawer_print"])

derived = {k: r6(v) for k, v in dict(W=W, H=H, D=D, plate_t=plate_t, y_back=y_back, y_pin=y_pin, z_pin=z_pin,
                                       travel=y_stop - y_pin, R=R, a0=a0, a1=a1, arc_top=arc_top, exit_z=exit_z,
                                       lift=lift, notch_y=notch_y, notch_back=TR["notch_back"], body_top=body_top,
                                       plate_top=plate_top, shoulder_z=shoulder_z, seat_z=seat_z, piv_y=piv[0],
                                       piv_z=piv[1], tilt=tilt).items()}
derived["hook_cols"] = [r6(v) for v in hook_cols]
derived["hook_rows"] = [r6(v) for v in hook_rows]
(HERE / "solidcraft").mkdir(exist_ok=True)
out = HERE / "solidcraft" / "solidcraft_commands.json"
out.write_text(json.dumps({"derived": derived, "commands": cmds}, indent=1))
print(f"{len(cmds)} commands -> {out}")
print(json.dumps(derived))
