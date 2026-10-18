# Omniwall arc-pocket drawer: housing + drawer for one unit (cells x rows from
# params.yaml). Hook pockets come from ../hook_geometry.py and ../panel.yaml, so
# they match the print-tested hooks. Run it from this folder with a plain build123d
# Python (the build123d-mcp server's execute() blocks the os, pathlib and yaml imports):
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py [unit folder]
# With no argument it builds the 3 x 2 unit from params.yaml here. A unit folder
# (such as 2x2) holds a params.yaml whose sections override this one's key by key.
# It writes the unit folder's step/, print/ (STEP, STL and plain 3MF per part) and
# report.txt, and leaves the closed assembly in `result`.
# Unit coordinates: x across from the left outer face, y out from the panel face
# (housing back face at y = 0), z up from the unit's bottom edge.
import copy
import math
import os
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

SRC = Path(os.environ.get("ARC_DRAWER_DIR", Path(__file__).resolve().parent))   # this folder: base params.yaml
ROOT = SRC.parent
HERE = SRC / sys.argv[1] if len(sys.argv) > 1 else SRC                          # unit folder: its params and outputs
P = yaml.safe_load((SRC / "params.yaml").read_text())
if HERE != SRC:
    for k, v in yaml.safe_load((HERE / "params.yaml").read_text()).items():
        if isinstance(v, dict) and isinstance(P.get(k), dict):
            P[k].update(v)
        else:
            P[k] = v
panel = yaml.safe_load((ROOT / "panel.yaml").read_text())
exec((ROOT / "hook_geometry.py").read_text())
exec((ROOT / "core_3mf.py").read_text())

_export_step = export_step


def export_step(shape, path):
    """build123d 0.13 refuses to write some labelled shapes to STEP; retry as a plain solid."""
    try:
        return _export_step(shape, path)
    except RuntimeError:
        return _export_step(Solid(shape.wrapped), path)


pitch = panel["pitch"]
hook = panel["cross_slot_hook"]
U, HS, DR, PN, TR, LP, LB, FT = (P[k] for k in ("unit", "housing", "drawer", "pins", "track", "lip", "label", "fit_test"))
dm = copy.deepcopy(panel["dovetail_mount"])
dv, pk = dm["dovetail"], dm["pocket"]
pk["spine_clearance"] = HS["pocket"]["spine_clearance"]   # housing pocket from the print-tested coupon 3
pk["flank_gap"] = HS["pocket"]["flank_gap"]
pk["ridge"]["height"] = HS["pocket"]["ridge_height"]
SC = P["scoop"]
NAME = U.get("file_prefix", "arc_drawer")             # start of every output file name
K = math.sqrt(2)

W = U["cells"] * pitch - U["gap"]
H = U["rows"] * pitch - U["gap"]
D = U["depth"]
edge = U["gap"] / 2                                  # unit inset from its nominal cell on every side
# Hooks: the hook's top bar rests on the bottom edge of the upper vertical slot,
# which starts pitch - length/2 above the peg-hole row at the unit's bottom.
hook_z0 = (pitch - panel["slot"]["length"] / 2) - hook["bar_bottom"] - edge
hook_cols = [k * pitch - edge for k in range(1, U["cells"])]
hook_rows = [hook_z0 + r * pitch for r in range(U["rows"])]
HH = hook["height"]
seat_z = hook_rows[-1] + HH + pk["top_clearance"]    # closed top of every pocket channel
cx = dv["block_width"] / 2
hh = dv["head_width"] / 2 + pk["side_clearance"]     # half width of the pocket's head slot
bw = dv["block_width"] / 2 + pk["side_clearance"]    # half width of the spine channel
yb = dv["block_depth"] + pk["spine_clearance"]       # back of the lips
yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]   # pocket floor (at its edges)
plate_t = yf + hh + HS["back_front_wall"]            # back plate: floor gable rises hh at the centre

# Drawer and track positions.
z_floor = HS["floor"]
z_roof = H - HS["roof"]
y_back = plate_t + DR["back_clearance"]              # drawer back face, closed
y_pin = y_back + PN["from_back"]
z_pin = PN["height"]
y_stop = TR["stop"]
travel = y_stop - y_pin
piv = (D, z_floor)                                   # sill: the floor's front top edge (y, z)
rv = PN["diameter"] / 2 + TR["clearance"]            # track section radius
R = math.hypot(y_stop - piv[0], z_pin - piv[1])      # arc radius about the sill
a0 = math.degrees(math.atan2(z_pin - piv[1], y_stop - piv[0]))
tilt = TR["tilt"]
a1 = a0 - tilt                                       # nose-down: the pin swings clockwise in the y-z plane
pin_end = (piv[0] + R * math.cos(math.radians(a1)), piv[1] + R * math.sin(math.radians(a1)))
arc_top = pin_end[1] + rv
exit_z = arc_top + TR["exit_web"] + K * rv           # exit channel centre; its teardrop apex is exit_web above the arc
lift = exit_z - z_pin
notch_y = y_stop - TR["notch_back"]
body_top = z_roof - DR["headroom"]
plate_top = z_roof - DR["top_gap"]
shoulder_z = z_roof - lift - DR["lift_clearance"]


def solid(s):
    """One shape from whatever the algebra returned (a ShapeList when pieces were fused one by one)."""
    if isinstance(s, ShapeList):
        return s[0] if len(s) == 1 else Compound(list(s))
    return s


def tear(r, u, v):
    """Teardrop section: circle of radius r with a 45 deg point downward, centred (u, v)."""
    c = r / K
    return Pos(u, v) * (Circle(r) + Polygon((-c, -c), (c, -c), (0, -K * r), align=None))


def rect2(u0, v0, u1, v1):
    return Pos((u0 + u1) / 2, (v0 + v1) / 2) * Rectangle(u1 - u0, v1 - v0)


def track_region():
    """The track as a 2D region in the y-z plane: straight groove to the stop, the
    arc the pin sweeps while the drawer tilts about the sill, the lift notch behind
    the stop, and the exit channel from the notch's top to the front. Every piece is
    the pin's teardrop section swept, so the pin fits everywhere with the same
    clearance."""
    V = rect2(plate_t, z_pin - K * rv, y_stop, z_pin + rv) + tear(rv, y_stop, z_pin)
    # Arc: the section turns with the drawer, so its sweep is the annular sector
    # between the circle's nearest and farthest points plus the two end sections.
    L = (R + rv) / math.cos(math.radians(tilt / 2)) + 1
    ang = lambda a: (piv[0] + L * math.cos(math.radians(a)), piv[1] + L * math.sin(math.radians(a)))
    wedge = Polygon(piv, ang(a1), ang(a0), align=None)
    annulus = Pos(*piv) * (Circle(R + rv) - Circle(R - rv))
    end = Pos(*piv) * Rot(0, 0, -tilt) * Pos(-piv[0], -piv[1]) * tear(rv, y_stop, z_pin)
    V = V + (annulus & wedge) + end
    # Lift notch (section swept up) and exit channel (swept forward, open at the front).
    V = V + rect2(notch_y - rv, z_pin, notch_y + rv, exit_z) + tear(rv, notch_y, exit_z)
    V = V + rect2(notch_y, exit_z - K * rv, D + 1, exit_z + rv)
    return V


def track_void(x_face):
    """Track cut into the left wall's inner face at x_face, TR.depth deep toward -x.
    The housing prints on its back (print-up = +y), so every face of the track
    that would face down becomes one 45 deg ramp: the section is shifted +y by d
    at depth d from the groove floor, so each ceiling rises from the groove
    floor to the wall face and every layer of it is attached to the solid wall
    behind the groove (a two-sided tent left unattached slivers at the wall
    face, which Bambu Studio flagged as floating regions)."""
    V = track_region()
    dp = TR["depth"]
    base = extrude(Plane.YZ.offset(x_face - dp) * V, dp + 0.1, dir=(1, 0, 0))
    ramp = extrude(Plane.YZ.offset(x_face - dp) * V, dp * K, dir=(1, 1, 0))
    return solid(base + ramp)


def pocket(xc):
    """Pocket channel for one hook column: the shared dovetail pocket from
    hook_geometry (open at the bottom, closed seat at the top, snap ridges), a
    second ridge pair one pitch lower for a second row of hooks, and 45 deg gables
    on the spine channel's end and the pocket floor so it prints on its back."""
    zl = -(seat_z - HH) - 1
    zt = HH + pk["top_clearance"]
    v = pocket_void(dm, HH, 0.0, zl)
    if HS["second_ridges"] and U["rows"] > 1:
        r = pk["ridge"]
        zc = zt - r["below_top"] - pitch
        y_ridge_end = dv["block_depth"] + dv["depth"] - dv["notch"]["front_land"] - r["front_gap"]
        for x_face, inward in ((cx + hh, -1), (cx - hh, 1)):
            v = v - v_groove_prism(x_face, inward, zc, yb, y_ridge_end, r["height"], r["flank_angle"], r["tip_radius"])
    e = 0.02   # gables start a hair wider than the channel, so no flat strip is left at the corners
    chan = Polygon((cx - bw - e, yb), (cx + bw + e, yb), (cx, yb + bw + e), align=None)
    floor = Polygon((cx - hh - e, yf), (cx + hh + e, yf), (cx, yf + hh + e), align=None)
    v = v + Pos(0, 0, zl) * extrude(chan, zt - zl) + Pos(0, 0, zl) * extrude(floor, zt - zl)
    return Pos(xc - cx, 0, seat_z - HH) * solid(v)


def housing():
    s = HS["side"]
    body = Box(W, D, H, align=Align.MIN)
    body = body - Pos(s, plate_t, z_floor) * Box(W - 2 * s, D, z_roof - z_floor, align=Align.MIN)
    for xc in hook_cols:
        body = body - pocket(xc)
    left = track_void(s)
    body = solid(body - left - mirror(left, Plane.YZ.offset(W / 2)))
    body.label = "housing"
    return body


def label_holder(xm):
    """U holder on the front face, open at the top: a bottom rail with a 45 deg
    underside, and two side rails that wrap over the label's edges."""
    rail, ret = LB["rail"], LB["return"]
    hd = rail + LB["thickness"] + LB["thickness_clearance"]        # how far the holder stands proud
    inner = LB["width"] + 2 * LB["side_clearance"]
    za = z_floor + LB["bottom_clear"]
    z_seat = za + hd + rail                                           # the label rests here
    z_top = z_seat + LB["height"] + LB["top_clear"]
    half = inner / 2 + rail
    prof = Polygon((D - 1, za), (D, za), (D + hd, za + hd), (D + hd, z_seat), (D - 1, z_seat), align=None)
    bottom = extrude(Plane.YZ.offset(xm - half) * prof, 2 * half, dir=(1, 0, 0))
    post = Pos(xm - half, D - 1, z_seat - 0.1) * Box(rail, hd + 1, z_top - z_seat + 0.1, align=Align.MIN)
    wrap = Pos(xm - half + rail - 0.01, D + hd - rail, z_seat - 0.1) * Box(ret + 0.01, rail, z_top - z_seat + 0.1, align=Align.MIN)
    side = post + wrap
    return solid(bottom + side + mirror(side, Plane.YZ.offset(xm)))


def scoop():
    """Zeid's scoop (openscad/omniwall/drawers/scoop_prototype.scad) turned 180 deg
    so it opens downward: a tray (side walls tapering to a narrow front wall, no
    back wall) whose floor is tilted 45 deg up and out from the drawer face, top
    flush with the plate top, centred. The floor runs on past the walls into the
    face, then everything behind the face is cut off. Fingers go up into it from
    below; the cavity's ceiling and the rim are 45 deg, so it prints upright."""
    w, dp, h, t, fw = SC["width"], SC["depth"], SC["height"], SC["wall"], SC["front_width"]
    fl, fr = (w - fw) / 2, (w + fw) / 2
    a = t * math.hypot(fl, dp) / dp                 # side wall thickness measured along x
    b = fl * (dp - t) / dp + a                      # inner corner of the front wall
    s = math.sin(math.radians(SC["angle"]))
    c = math.cos(math.radians(SC["angle"]))
    top = dp * (s + c)                              # floor top meets the face this far above the pivot
    pl = Plane(origin=(W / 2 - w / 2, D, plate_top - SC["below_top"] - top), x_dir=(1, 0, 0), z_dir=(0, -s, c))
    walls = extrude(pl * Polygon((0, 0), (fl, dp), (fr, dp), (w, 0), (w - a, 0), (w - b, dp - t), (b, dp - t), (a, 0), align=None), h, dir=(0, -s, c))
    floor = extrude(pl.offset(h - t) * Polygon((0, 0), (fl, dp), (fr, dp), (w, 0), align=None), t + dp, dir=(0, -s, c))   # runs on into the face, as in the scad
    keep = Pos(W / 2, D - SC["embed"] + 20, plate_top - top / 2) * Box(w + 2, 40, top + 10)
    sc = solid((walls + floor) & keep)
    if SC["lip_flat"] > 0:
        # The front wall's lip starts as a knife edge hanging across the cavity, so its first
        # layers are a thin line in the air. Cut it flat so they print as a short bridge
        # anchored on the side walls (only between the side walls' inner corners).
        z_lip = pl.origin.Z + (dp - t) * s
        y_lip = D + (dp - t) * c
        cut = Pos(W / 2 - w / 2 + b, y_lip - SC["lip_flat"] - 0.5, z_lip - 5) * Box(w - 2 * b, t * s + SC["lip_flat"] + 2, 5 + SC["lip_flat"], align=Align.MIN)
        sc = solid(sc - cut)
    return sc


BLENDS = []


def blend_scoop(d):
    """Round the scoop where it meets the drawer face (Zeid asked, 2026-10-17):
    first the two convex edges at the top of the front, so the face blend can
    turn the corner, then every edge where the scoop meets the face."""
    r = SC["blend"]
    xs = (W / 2 - SC["width"] / 2 - 0.1, W / 2 + SC["width"] / 2 + 0.1)
    zs = (plate_top - SC["below_top"] - SC["depth"] * K - 0.1, plate_top - SC["below_top"] + 0.1)
    def near_scoop(e):
        m = e.center()
        return xs[0] < m.X < xs[1] and zs[0] < m.Z < zs[1]
    corners = [e for e in d.edges() if near_scoop(e) and e.center().Y > D + 1 and abs(e.center().Z - (plate_top - SC["below_top"] - SC["depth"] * math.cos(math.radians(SC["angle"])) / 2)) < 0.5
               and abs(abs(e.center().X - W / 2) - SC["front_width"] / 2) < 0.1]
    d = fillet(corners, r) if corners else d
    def at_face(d):
        return [e for e in d.edges() if near_scoop(e) and all(abs(v.Y - D) < 1e-3 for v in (e.center(), e.start_point(), e.end_point()))]
    flat = lambda e: abs(e.start_point().Z - e.end_point().Z) < 1e-3
    z_top = plate_top - SC["below_top"]
    # Outside first (top and the two side walls), then the cavity's ceiling, then
    # its side walls if the kernel can (they end in the narrow rim at the bottom).
    groups = [("outside", lambda e: (flat(e) and abs(e.center().Z - z_top) < 0.01) or (not flat(e) and e.length > 15)),
              ("ceiling", lambda e: flat(e) and e.length > 10 and abs(e.center().Z - z_top) > 0.01),
              ("cavity sides", lambda e: not flat(e) and e.length <= 15)]
    done = []
    for name, pick in groups:
        edges = [e for e in at_face(d) if pick(e)]
        try:
            d = d.fillet(r, edges)
            done.append(f"{name} ({len(edges)})")
        except ValueError:
            done.append(f"{name} not blended (kernel refused r {r})")
    return d, len(corners), ", ".join(done)


def blend_label(d, xm):
    """Round the label holder's outside edges where it meets the drawer face
    (bottom rail, outer ends, post tops). The corners inside the slot stay sharp:
    a blend there would push the label off the face."""
    rail = LB["rail"]
    half = (LB["width"] + 2 * LB["side_clearance"]) / 2 + rail
    za = z_floor + LB["bottom_clear"]
    hd = rail + LB["thickness"] + LB["thickness_clearance"]
    z_top = za + hd + rail + LB["height"] + LB["top_clear"]
    def outside(e):
        m = e.center()
        if not all(abs(v.Y - D) < 1e-3 for v in (e.start_point(), e.end_point(), m)):
            return False
        if not (xm - half - 0.1 < m.X < xm + half + 0.1 and za - 0.1 < m.Z < z_top + 0.1):
            return False
        inner_x = abs(abs(m.X - xm) - (half - rail)) < 0.01
        in_slot = abs(m.X - xm) < half - rail - 0.01 and m.Z > za + 0.1
        return not (inner_x or in_slot)
    edges = [e for e in d.edges() if outside(e)]
    return d.fillet(LB["blend"], edges), len(edges)


def drawer():
    """Drawer in unit coordinates, closed."""
    s, c = HS["side"], DR["side_clearance"]
    x0, x1 = s + c, W - s - c
    w, fl, ft = DR["wall"], DR["floor"], DR["front_thickness"]
    y_front = D - ft
    body = Pos(x0, y_back, z_floor) * Box(x1 - x0, y_front - y_back, body_top - z_floor, align=Align.MIN)
    body = body - Pos(x0 - 1, y_back - 1, shoulder_z) * Box(x1 - x0 + 2, DR["shoulder_length"] + 1, body_top, align=Align.MIN)
    body = body - Pos(x0 + w, y_back + w, z_floor + fl) * Box(x1 - x0 - 2 * w, y_front - y_back - w, body_top, align=Align.MIN)
    plate = Pos(x0, y_front, z_floor) * Box(x1 - x0, ft, plate_top - z_floor, align=Align.MIN)
    if P["front"]["pull"] == "scoop":
        lip = scoop()
    else:
        pr, fh = LP["proud"], LP["front_height"]
        lip = Polygon((D - 1, plate_top - pr - fh - 1), (D, plate_top - pr - fh), (D + pr, plate_top - fh),
                      (D + pr, plate_top), (D - 1, plate_top), align=None)
        lip = extrude(Plane.YZ.offset(x0) * lip, x1 - x0, dir=(1, 0, 0))
    pin = extrude(Plane.YZ.offset(s - PN["reach"]) * tear(PN["diameter"] / 2, y_pin, z_pin), x0 + 0.5 - (s - PN["reach"]), dir=(1, 0, 0))
    d = solid(body + plate + lip + label_holder((x0 + x1) / 2) + pin + mirror(pin, Plane.YZ.offset(W / 2)))
    if P["front"]["pull"] == "scoop" and SC["blend"] > 0:
        d, nc, nf = blend_scoop(d)
        BLENDS.append(f"scoop blend r {SC['blend']}: {nc} front corners; at the face: {nf}")
    if LB["blend"] > 0:
        d, nl = blend_label(d, (x0 + x1) / 2)
        BLENDS.append(f"label holder blend r {LB['blend']}: {nl} outside edges at the face")
    r = DR["corner_radius"]
    if r > 0:
        # Round the face's top corners: cut the square corner outside a radius-r arc along the whole drawer.
        L = D - y_back + 2
        for xc, sx in ((x0 + r, -1), (x1 - r, 1)):
            block = Pos(xc + sx * (r + 1) / 2, y_back - 1 + L / 2, plate_top - r + (r + 1) / 2) * Box(r + 1, L, r + 1)
            arc = Pos(xc, y_back - 1 + L / 2, plate_top - r) * Rot(90, 0, 0) * Cylinder(r, L + 2)
            d = solid(d - (block - arc))
        BLENDS.append(f"front top corners r {r}")
    d.label = "drawer"
    return d


def drawer_at(d, state, angle=None, y=None):
    """closed; open (at the stop, level); tilted (at the stop, nose down `angle`,
    default the full tilt); lifted (pushed back to the notch, raised into the exit
    channel, pulled out by `y` from there)."""
    if state == "closed":
        return d
    if state == "open":
        return Pos(0, travel, 0) * d
    if state == "tilted":
        return (Pos(0, travel, 0) * d).rotate(Axis((0, piv[0], piv[1]), (1, 0, 0)), -(tilt if angle is None else angle))
    if state == "lifted":
        return Pos(0, travel - TR["notch_back"] + (y or 0), lift) * d
    raise ValueError(state)


def hooks(rows=None):
    hk = cross_slot_hook(panel, ROOT)
    out = []
    for xc in hook_cols:
        for z in (hook_rows if rows is None else rows):
            h = Pos(xc - cx, -hook["panel_front_y"], z) * hk
            h.label = f"hook x{xc:.1f} z{z:.1f}"
            out.append(h)
    return out


def overlap(a, b):
    r = a & b
    return sum(s.volume for s in (r if isinstance(r, (list, ShapeList)) else [r]) if s is not None)


def to_bed(s):
    bb = s.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * s


def print_housing(h):
    """On its back: the back face (panel side) on the bed, front up."""
    return to_bed(Rot(90, 0, 0) * h)


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


def faces_at_z(part, z, tol=0.05):
    return [f for f in part.faces() if abs(f.center().Z - z) < tol and abs(f.normal_at().Z) > 0.99]


lines = []
log = lines.append

h = housing()
d = drawer()
for sub in ("step", "print"):
    (HERE / sub).mkdir(exist_ok=True)
for part in (h, d):
    bb = part.bounding_box()
    log(f"{part.label}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {part.volume:.0f} mm3, "
        f"solids {len(part.solids())}, valid {part.is_valid}")
    for so in part.solids():
        if len(part.solids()) > 1:
            b2 = so.bounding_box()
            log(f"    solid volume {so.volume:.2f} at x {b2.min.X:.2f}..{b2.max.X:.2f} y {b2.min.Y:.2f}..{b2.max.Y:.2f} z {b2.min.Z:.2f}..{b2.max.Z:.2f}")
log(f"back plate {plate_t:.3f}  pin closed y {y_pin:.3f}  travel {travel:.2f} ({travel / (D - y_back) * 100:.0f} % of the drawer)  "
    f"arc radius {R:.2f}  arc top z {arc_top:.2f}  exit channel z {exit_z:.2f}  lift {lift:.2f}  shoulder z {shoulder_z:.2f}  "
    f"hook columns {[round(x, 2) for x in hook_cols]}  hook bottoms {[round(z, 2) for z in hook_rows]}  seat z {seat_z:.2f}")
# Measured on the solids, not read from the code.
seats = [f for f in faces_at_z(h, seat_z) if f.normal_at().Z < 0]
log(f"measured: pocket seats at z {sorted(round(f.center().Z, 3) for f in seats)} (expect {seat_z:.3f} x{len(hook_cols)})")
xs = sorted({round(f.center().X, 3) for f in h.faces() if abs(abs(f.normal_at().X) - 1) < 1e-3 and 0.5 < f.center().Y < D - 0.5})
log(f"measured: housing x faces at {xs} (groove floors expect {TR['depth']:.1f} and {W - TR['depth']:.1f}, bay walls {HS['side']} and {W - HS['side']})")
pin_faces = sorted({round(f.center().X, 3) for f in d.faces() if abs(abs(f.normal_at().X) - 1) < 1e-3})
log(f"measured: drawer x faces at {pin_faces} (pin tips expect {HS['side'] - PN['reach']:.1f} and {W - HS['side'] + PN['reach']:.1f})")
for b_ in BLENDS:
    log(b_)
export_step(h, str(HERE / "step" / f"{NAME}_housing.step"))
export_step(d, str(HERE / "step" / f"{NAME}_drawer.step"))

hks = hooks()
log(f"hooks vs housing: {sum(overlap(h, k) for k in hks):.3f} mm3 total over {len(hks)} hooks (ridges reach {pk['ridge']['height'] - pk['side_clearance']:.3f} past the hook flank into its {dv['notch']['depth']} notches: a small overlap is expected)")
for state in ("closed", "open", "tilted", "lifted"):
    moved = drawer_at(d, state)
    moved.label = f"drawer {state}"
    log(f"{state}: drawer vs housing {overlap(h, moved):.3f} mm3, vs hooks {sum(overlap(moved, k) for k in hks):.3f} mm3")
    export_step(Compound(children=[h, moved, *hks]), str(HERE / "step" / f"{NAME}_assembly_{state}.step"))
log("tilt sweep (deg: mm3): " + ", ".join(f"{a}: {overlap(h, drawer_at(d, 'tilted', angle=a)):.3f}" for a in range(0, tilt + 1, 5)))
log("lifted, pulled out from the notch by (mm: mm3): " + ", ".join(
    f"{y}: {overlap(h, drawer_at(d, 'lifted', y=y)):.3f}" for y in (0, 5, 10, 15, 20, 24)))
log("sliding (pin y: mm3): " + ", ".join(f"{y_pin + t:.0f}: {overlap(h, Pos(0, t, 0) * d):.3f}" for t in (travel * 0.25, travel * 0.5, travel * 0.75, travel - 3)))

# Print orientation: housing on its back, drawer upright.
hp, dp = print_housing(h), to_bed(d)
# Fit test pieces: the housing's front part, the drawer's rear part, one pocket coupon.
ht = solid(h & Pos(0, D - FT["housing_length"], 0) * Box(W, FT["housing_length"] + 1, H, align=Align.MIN))
dt = solid(d & Pos(0, y_back - 1, 0) * Box(W, FT["drawer_length"] + 1, H, align=Align.MIN))
xc0 = hook_cols[0]
cp = solid(h & Pos(xc0 - FT["coupon_half_width"], 0, FT["coupon_bottom"]) * Box(2 * FT["coupon_half_width"], plate_t, H, align=Align.MIN))
ht.label, dt.label, cp.label = "fit test housing front", "fit test drawer rear", "pocket coupon"
htp, dtp, cpp = print_housing(ht), to_bed(dt), print_housing(cp)
plates = []
TEST = HERE / "test-prints"                          # fit tests: local only (git-ignored)
TEST.mkdir(exist_ok=True)
for part, stem, out in ((hp, f"{NAME}_housing_print", HERE / "print"), (dp, f"{NAME}_drawer_print", HERE / "print"),
                        (htp, f"{NAME}_fit_test_housing_print", TEST), (dtp, f"{NAME}_fit_test_drawer_print", TEST),
                        (cpp, f"{NAME}_pocket_coupon_print", TEST)):
    export_step(part, str(out / f"{stem}.step"))
    export_stl(part, str(out / f"{stem}.stl"))
    write_3mf([(stem, *shape_mesh(part))], out / f"{stem}.3mf")
    bad = bad_faces(part)
    bb = part.bounding_box()
    log(f"{stem}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, faces {len(part.faces())}, overhangs flatter than 45 deg: {len(bad)}")
    for b in sorted(bad, key=lambda t: -t[1])[:10]:
        log(f"    {b[0]:.1f} deg from vertical, area {b[1]} mm2, at ({b[2].X:.1f}, {b[2].Y:.1f}, {b[2].Z:.1f})")
# The fit test pieces on one plate (plain 3MF: Bambu Studio imports every object onto the current plate).
write_3mf([("housing front", *shape_mesh(htp, -60, 0)), ("drawer rear", *shape_mesh(dtp, 40, 0)),
           ("pocket coupon", *shape_mesh(cpp, 0, 60))], TEST / f"{NAME}_fit_test_plate.3mf")
# Housing and drawer side by side on one plate, 10 mm apart, centred on the origin.
gap = 10.0
hb, db = hp.bounding_box(), dp.bounding_box()
hx = -(hb.size.X + gap + db.size.X) / 2 - hb.min.X
dx = hx + hb.max.X + gap - db.min.X
write_3mf([("housing", *shape_mesh(hp, hx, -hb.center().Y)), ("drawer", *shape_mesh(dp, dx, -db.center().Y))],
          HERE / "print" / f"{NAME}_all_parts.3mf")
log(f"{NAME}_all_parts: housing and drawer on one plate, {hb.size.X + gap + db.size.X:.1f} x {max(hb.size.Y, db.size.Y):.1f}")
(HERE / "report.txt").write_text("\n".join(lines) + "\n")
result = Compound(children=[h, d, *hks])
