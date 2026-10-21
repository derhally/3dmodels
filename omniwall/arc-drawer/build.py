# Omniwall arc-pocket drawer: housing + drawer for one unit (cells x rows from
# params.yaml). Hook pockets come from ../hook_geometry.py and ../panel.yaml, so
# they match the print-tested hooks. Run it from this folder with a plain build123d
# Python (the build123d-mcp server's execute() blocks the os, pathlib and yaml imports):
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py <unit folder>
# params.yaml here holds the shared defaults; each size is a unit folder (such as
# 2x2x60) whose params.yaml overrides them section by section, key by key.
# It writes the unit folder's step/, print/ (STEP and STL per part, one all-parts 3MF) and
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
if len(sys.argv) < 2:                                                           # this folder holds only the shared defaults (Zeid, 2026-10-19)
    sys.exit("usage: build.py <size folder>, one of: " + ", ".join(sorted(p.parent.name for p in SRC.glob("*/params.yaml"))))
HERE = SRC / sys.argv[1]                                                        # unit folder: its params and outputs
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
exec((ROOT.parent / "bambu" / "bambu_project.py").read_text())
TEMPLATE = ROOT.parent / "bambu" / "project_settings.config"   # printer, filament, process as saved from Bambu Studio
exec((SRC / "handle_geometry.py").read_text())

_export_step = export_step


def export_step(shape, path):
    """build123d 0.13 refuses to write some labelled shapes to STEP; retry as a plain solid."""
    try:
        return _export_step(shape, path)
    except RuntimeError:
        return _export_step(Solid(shape.wrapped), path)


pitch = panel["pitch"]
hook = panel["bridge_hook"]
U, HS, DR, PN, TR, LP, LB, FT = (P[k] for k in ("unit", "housing", "drawer", "pins", "track", "lip", "label", "fit_test"))
dm = copy.deepcopy(panel["dovetail_mount"])
dv, pk = dm["dovetail"], dm["pocket"]
pk["spine_clearance"] = HS["pocket"]["spine_clearance"]   # housing pocket from the print-tested coupon 3
pk["flank_gap"] = HS["pocket"]["flank_gap"]
pk["ridge"]["height"] = HS["pocket"]["ridge_height"]
SC, HD = P["scoop"], P["handle"]
SEP = P["front"]["pull"] in ("handle", "scoop_pins")   # a separate part on two snap pins
PT = {**HD, **P["scoop_pins"]} if P["front"]["pull"] == "scoop_pins" else HD
PULL = P["front"]["pull"]                            # handle (separate part on snap pins), scoop or lip
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
R = math.hypot(y_stop - piv[0], z_pin - piv[1])      # arc radius about the sill
a0 = math.degrees(math.atan2(z_pin - piv[1], y_stop - piv[0]))
tilt = TR["tilt"]
a1 = a0 - tilt                                       # nose-down: the pin swings clockwise in the y-z plane
pin_end = (piv[0] + R * math.cos(math.radians(a1)), piv[1] + R * math.sin(math.radians(a1)))
hw = (1 if PN.get("flat_point") else K) * PN["diameter"] / 2 + TR["clearance"]   # channel half width: the pin's reach (to its point, or its flat) + clearance, so it fits however the drawer turns
# Way out: from the arc's end (the apex, where the drawer hangs at full tilt) the
# drawer is pushed back along its own bottom, still on the sill (the gate), which lifts
# it, so let go there it slides back down to the apex. The gate curves up with the
# arc's radius, the arc mirrored at the apex, and runs into the hook, which curves up
# round the tongue of wall and forward into the exit channel.
Lh = lambda h: (-math.sin(math.radians(h)), math.cos(math.radians(h)))   # left of heading h (deg, 0 = forward)
ta = math.radians(tilt)
gate = TR["gate"]
gate_c = (pin_end[0] - R * Lh(180 - tilt)[0], pin_end[1] - R * Lh(180 - tilt)[1])   # leaves the apex heading back along the tilted bottom, turning up
g0 = 270 - tilt                                      # pin_end's angle about gate_c; the gate runs clockwise from it
g1 = g0 - math.degrees(gate / R)
hg = 180 - tilt - math.degrees(gate / R)             # heading at the gate's top
gate_top = (gate_c[0] + R * math.cos(math.radians(g1)), gate_c[1] + R * math.sin(math.radians(g1)))
r_h = TR["hook_radius"]
hook_c = (gate_top[0] - r_h * Lh(hg)[0], gate_top[1] - r_h * Lh(hg)[1])
exit_z = hook_c[1] + r_h
lift = exit_z - z_pin
branch_top = (hook_c[0], exit_z)                     # the exit channel starts here
arc_len, hook_len = R * ta, r_h * math.radians(hg)
path_len = arc_len + gate + hook_len


def path_point(s):
    """Pin centre `s` along the path from the stop: up the arc, back along the gate, round the hook."""
    if s <= arc_len:
        a = math.radians(a0) - s / R
        return (piv[0] + R * math.cos(a), piv[1] + R * math.sin(a))
    if s <= arc_len + gate:
        g = math.radians(g0) - (s - arc_len) / R
        return (gate_c[0] + R * math.cos(g), gate_c[1] + R * math.sin(g))
    h = hg - math.degrees((s - arc_len - gate) / r_h)
    return (hook_c[0] + r_h * Lh(h)[0], hook_c[1] + r_h * Lh(h)[1])


body_top = z_roof - DR["headroom"]
plate_top = z_roof - DR["top_gap"]
shoulder_z = z_roof - lift - DR["lift_clearance"]


def solid(s):
    """One shape from whatever the algebra returned (a ShapeList when pieces were fused one by one)."""
    if isinstance(s, ShapeList):
        return s[0] if len(s) == 1 else Compound(list(s))
    return s


def tear(r, u, v):
    """Teardrop section: circle of radius r with a 45 deg point downward, centred (u, v);
    with pins.flat_point the point is cut flat at r, so the section stays inside the circle."""
    c = r / K
    tip = [(2 * c - r, -r), (r - 2 * c, -r)] if PN.get("flat_point") else [(0, -K * r)]
    return Pos(u, v) * (Circle(r) + Polygon((-c, -c), (c, -c), *tip, align=None))


def rect2(u0, v0, u1, v1):
    return Pos((u0 + u1) / 2, (v0 + v1) / 2) * Rectangle(u1 - u0, v1 - v0)


def rest_tilt(yp, zp):
    """Nose-down tilt of a drawer resting on the sill with its pins at (yp, zp)."""
    h = z_pin - z_floor
    gap = lambda t: (piv[0] - yp) * math.sin(t) + (piv[1] - zp) * math.cos(t) + h
    lo, hi = 0.0, math.radians(89)
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if gap(m) < 0 else (lo, m)
    return math.degrees(lo)


def slot(p, q, r):
    """Region swept by a circle of radius r from p to q."""
    dy, dz = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dy, dz)
    oy, oz = -dz / n * r, dy / n * r
    return (Polygon((p[0] + oy, p[1] + oz), (q[0] + oy, q[1] + oz), (q[0] - oy, q[1] - oz), (p[0] - oy, p[1] - oz), align=None)
            + Pos(*p) * Circle(r) + Pos(*q) * Circle(r))


def band(c, radius, a0_, a1_, r):
    """Region swept by a circle of radius r along the arc about c from angle a0_ to
    a1_ (deg, counter-clockwise), without its end circles."""
    L = (radius + r) * 2
    fan = Polygon(c, *[(c[0] + L * math.cos(math.radians(a)), c[1] + L * math.sin(math.radians(a)))
                       for a in (a0_ + (a1_ - a0_) * k / 8 for k in range(9))], align=None)
    return Pos(*c) * (Circle(radius + r) - Circle(radius - r)) & fan


def fillet_line_circle(V, p0, d, side, c0, Rc, r):
    """Round the point of wall where the track's straight wall (the line through p0 in
    direction d, the wall on the side of normal `side` * (-d.z, d.y)) meets its arc
    wall (circle Rc about c0, the wall outside it) to radius r: cut away the point."""
    nrm = (-d[1] * side, d[0] * side)
    def hit(off, rr):
        q = (p0[0] + off * nrm[0] - c0[0], p0[1] + off * nrm[1] - c0[1])
        b = q[0] * d[0] + q[1] * d[1]
        t = -b + math.sqrt(b * b - (q[0] ** 2 + q[1] ** 2 - rr ** 2))
        return (c0[0] + q[0] + t * d[0], c0[1] + q[1] + t * d[1])
    corner, c = hit(0, Rc), hit(r, Rc + r)
    t1 = (c[0] - r * nrm[0], c[1] - r * nrm[1])
    k = Rc / math.hypot(c[0] - c0[0], c[1] - c0[1])
    t2 = (c0[0] + (c[0] - c0[0]) * k, c0[1] + (c[1] - c0[1]) * k)
    return V + (Polygon(corner, t1, c, t2, align=None) - Pos(*c) * Circle(r))


def circles_meet(c1, r1, c2, r2, near):
    """The crossing point of two circles nearer `near`."""
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    dd = math.hypot(dx, dy)
    a = (r1 * r1 - r2 * r2 + dd * dd) / (2 * dd)
    h = math.sqrt(r1 * r1 - a * a)
    m = (c1[0] + a * dx / dd, c1[1] + a * dy / dd)
    ps = [(m[0] + s_ * h * dy / dd, m[1] - s_ * h * dx / dd) for s_ in (1, -1)]
    return min(ps, key=lambda p: math.hypot(p[0] - near[0], p[1] - near[1]))


def fillet_circles(V, c1, r1, c2, r2, r, near):
    """Round the point of wall where two arc walls of the track meet (circles r1 about
    c1 and r2 about c2, the wall outside both) to radius r: cut away the point."""
    corner = circles_meet(c1, r1, c2, r2, near)
    c = circles_meet(c1, r1 + r, c2, r2 + r, near)
    ts = [(o[0] + (c[0] - o[0]) * rr / math.hypot(c[0] - o[0], c[1] - o[1]),
           o[1] + (c[1] - o[1]) * rr / math.hypot(c[0] - o[0], c[1] - o[1])) for o, rr in ((c1, r1), (c2, r2))]
    return V + (Polygon(corner, ts[0], c, ts[1], align=None) - Pos(*c) * Circle(r))


def track_region():
    """The track as a 2D region in the y-z plane: the pin centre's path (the straight
    groove to the stop, the arc it sweeps while the drawer tilts about the sill, the
    gate back from the arc's end, the hook round the tongue, the exit channel to the
    front) swept by a circle of radius hw, which holds the teardrop pin however the
    drawer turns. Every wall is a line or an arc at hw from that path; the two points
    of wall where it forks are rounded."""
    V = slot((y_pin, z_pin), (y_stop, z_pin), hw)
    V = V + band(piv, R, a1, a0, hw) + Pos(*pin_end) * Circle(hw)
    V = V + band(gate_c, R, g1, g0, hw)
    V = V + band(hook_c, r_h, 90, 90 + hg, hw)
    V = V + slot(branch_top, (D + hw + 1, exit_z), hw)
    # Where the groove's ceiling meets the arc's outer wall, across from the stop, and
    # the nub between the arc's outer wall and the gate's lower wall.
    V = fillet_line_circle(V, (y_stop, z_pin + hw), (-1, 0), -1, piv, R + hw, TR["stop_round"])
    # The nub's round meets the gate's outer wall, or the hook's if the gate is too short.
    near, rn = (pin_end[0] - 3 * hw, pin_end[1]), TR["nub_round"]
    c = circles_meet(piv, R + hw + rn, gate_c, R + hw + rn, near)
    on_gate = g1 <= math.degrees(math.atan2(c[1] - gate_c[1], c[0] - gate_c[0])) % 360 <= g0
    V = fillet_circles(V, piv, R + hw, *((gate_c, R + hw) if on_gate else (hook_c, r_h + hw)), rn, near)
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
    ridge pair one pitch lower for every further row of hooks, and 45 deg gables
    on the spine channel's end and the pocket floor so it prints on its back."""
    zl = -(seat_z - HH) - 1
    zt = HH + pk["top_clearance"]
    v = pocket_void(dm, HH, 0.0, zl)
    r = pk["ridge"]
    y_ridge_end = dv["block_depth"] + dv["depth"] - dv["notch"]["front_land"] - r["front_gap"]
    for k in range(1, U["rows"] if HS["ridges_every_row"] else 1):
        zc = zt - r["below_top"] - k * pitch
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
    if PULL == "scoop":
        lip = scoop()
    elif SEP:
        lip = None                                   # a separate part: only its pin holes are cut, below
    else:
        pr, fh = LP["proud"], LP["front_height"]
        lip = Polygon((D - 1, plate_top - pr - fh - 1), (D, plate_top - pr - fh), (D + pr, plate_top - fh),
                      (D + pr, plate_top), (D - 1, plate_top), align=None)
        lip = extrude(Plane.YZ.offset(x0) * lip, x1 - x0, dir=(1, 0, 0))
    pin = extrude(Plane.YZ.offset(s - PN["reach"]) * tear(PN["diameter"] / 2, y_pin, z_pin), x0 + 0.5 - (s - PN["reach"]), dir=(1, 0, 0))
    if PN.get("flat_point"):
        # Chamfer the flat under the pin at 45 deg, rising from the wall to the pin's end, so nothing faces flat down.
        xt, zb = s - PN["reach"], z_pin - PN["diameter"] / 2
        wedge = Polygon((x0, zb), (xt - 0.1, zb + x0 - xt + 0.1), (xt - 0.1, zb - 1), (x0, zb - 1), align=None)
        pin = pin - Pos(0, y_pin, 0) * extrude(Plane.XZ * wedge, PN["diameter"], both=True)
    d = body + plate + label_holder((x0 + x1) / 2) + pin + mirror(pin, Plane.YZ.offset(W / 2))
    d = solid(d + lip if lip is not None else d)
    if PULL == "scoop" and SC["blend"] > 0:
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
    if SEP:
        d = solid(d - Pos((x0 + x1) / 2, D, plate_top - PT["below_top"]) * pull_face_cut(PT, ft))
    d.label = "drawer"
    return d


def exit_tilt(yp):
    """Nose-down tilt of a drawer resting on the sill with its pins in the exit channel at y yp."""
    return rest_tilt(yp, exit_z)


def resting(d, yp, zp):
    """Drawer resting on the sill with its pins at (yp, zp)."""
    return (Pos(0, yp - y_pin, zp - z_pin) * d).rotate(Axis((0, yp, zp), (1, 0, 0)), -rest_tilt(yp, zp))


def drawer_at(d, state, angle=None, y=None):
    """closed; open (at the stop, level); tilted (nose down `angle` on the arc, by
    default hanging at full tilt); pushed (`y` along the path from the stop, resting
    on the sill; by default at the gate's top, on its way out); exit
    (pins in the exit channel `y` in front of its start, resting on the sill); held
    (same, held level)."""
    if state == "closed":
        return d
    if state == "open":
        return Pos(0, travel, 0) * d
    if state == "tilted" and angle is not None:
        return (Pos(0, travel, 0) * d).rotate(Axis((0, piv[0], piv[1]), (1, 0, 0)), -angle)
    if state in ("tilted", "pushed"):
        s_ = (s_hang if state == "tilted" else arc_len + gate) if y is None else y
        return resting(d, *path_point(s_))
    if state in ("exit", "held"):
        yp = branch_top[0] + (y or 0)
        if state == "held":
            return Pos(0, yp - y_pin, lift) * d
        return resting(d, yp, exit_z)
    raise ValueError(state)


def hooks(rows=None):
    hk = bridge_hook(panel, ROOT)
    out = []
    for xc in hook_cols:
        for z in (hook_rows if rows is None else rows):
            h = Pos(xc - cx, -hook["panel_front_y"], z) * hk
            h.label = f"hook x{xc:.1f} z{z:.1f}"
            out.append(h)
    return out


def overlap(a, b):
    """Volume shared by a and b, solid by solid (booleans on a whole compound proved unreliable)."""
    v = 0.0
    for sa in a.solids():
        for sb in b.solids():
            r = sa & sb
            v += sum(s.volume for s in (r if isinstance(r, (list, ShapeList)) else [r]) if s is not None)
    return v


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
if SEP:
    # The handle and its two pins, fitted; the motion checks below move them with the drawer
    xm = W / 2
    zh = plate_top - PT["below_top"]
    hd = Pos(xm, D, zh) * pull_part(PT)
    hpin = handle_pin(PT, DR["front_thickness"] - PT.get("recess", 0), PT["barb"])
    fitted = [Pos(xm + sx * PT["boss_x"], D - DR["front_thickness"], zh - PT["socket_down"]) * Rot(0, 90, 0) * hpin for sx in (-1, 1)]
    hd.label = "handle"
    da = Compound(children=[d, hd, *fitted])        # what moves
    da.label = "drawer"
else:
    da = d
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
    f"arc radius {R:.2f} to {tilt} deg  gate {gate}  hook radius {r_h} about ({hook_c[0]:.2f}, {hook_c[1]:.2f})  exit channel z {exit_z:.2f} from y {branch_top[0]:.2f}  lift {lift:.2f}  channel width {2 * hw:.2f}  shoulder z {shoulder_z:.2f}  "
    f"hook columns {[round(x, 2) for x in hook_cols]}  hook bottoms {[round(z, 2) for z in hook_rows]}  seat z {seat_z:.2f}")
# Measured on the solids, not read from the code.
seats = [f for f in faces_at_z(h, seat_z) if f.normal_at().Z < 0]
log(f"measured: pocket seats at z {sorted(round(f.center().Z, 3) for f in seats)} (expect {seat_z:.3f} x{len(hook_cols)})")
xs = sorted({round(f.center().X, 3) for f in h.faces() if abs(abs(f.normal_at().X) - 1) < 1e-3 and 0.5 < f.center().Y < D - 0.5})
log(f"measured: housing x faces at {xs} (groove floors expect {HS['side'] - TR['depth']:.1f} and {W - HS['side'] + TR['depth']:.1f}, bay walls {HS['side']} and {W - HS['side']})")
pin_faces = sorted({round(f.center().X, 3) for f in d.faces() if abs(abs(f.normal_at().X) - 1) < 1e-3})
log(f"measured: drawer x faces at {pin_faces} (pin tips expect {HS['side'] - PN['reach']:.1f} and {W - HS['side'] + PN['reach']:.1f})")
for b_ in BLENDS:
    log(b_)
export_step(h, str(HERE / "step" / f"{NAME}_housing.step"))
export_step(d, str(HERE / "step" / f"{NAME}_drawer.step"))

hks = hooks()
log(f"hooks vs housing: {sum(overlap(h, k) for k in hks):.3f} mm3 total over {len(hks)} hooks (ridges reach {pk['ridge']['height'] - pk['side_clearance']:.3f} past the hook flank into its {dv['notch']['depth']} notches: a small overlap is expected)")
cgv = da.center()


def cg_z(s_):
    """Height of the drawer's centre of gravity resting on the sill with its pins s_ along the path."""
    yp, zp = path_point(s_)
    t = math.radians(rest_tilt(yp, zp))
    return zp - (cgv.Y - y_pin) * math.sin(t) + (cgv.Z - z_pin) * math.cos(t)


ss = [arc_len * 0.5 + (path_len - arc_len * 0.5) * k / 400 for k in range(401)]
cz = [cg_z(x) for x in ss]
k_hang = next(k for k in range(1, 400) if cz[k] <= cz[k - 1] and cz[k] < cz[k + 1])
s_hang = ss[k_hang]
cg_lift = max(cz[k_hang:]) - cz[k_hang]
for state in ("closed", "open", "tilted", "pushed"):
    moved = drawer_at(da, state)
    moved.label = f"drawer {state}"
    log(f"{state}: drawer vs housing {overlap(h, moved):.3f} mm3, vs hooks {sum(overlap(moved, k) for k in hks):.3f} mm3")
    export_step(Compound(children=[h, moved, *hks]), str(HERE / "step" / f"{NAME}_assembly_{state}.step"))
log("tilt sweep on the arc (deg: mm3): " + ", ".join(f"{a}: {overlap(h, drawer_at(da, 'tilted', angle=a)):.3f}" for a in range(0, tilt + 1, 5)))
log(f"hangs open at {rest_tilt(*path_point(s_hang)):.1f} deg, {s_hang - arc_len:.1f} mm past the arc's end; pushing it out over the top lifts its centre of gravity {cg_lift:.2f} mm")
log("along the gate and hook, resting on the sill (mm from the arc's end: deg, mm3): " + ", ".join(
    f"{s_ - arc_len:.1f}: {rest_tilt(*path_point(s_)):.1f}, {overlap(h, drawer_at(da, 'pushed', y=s_)):.3f}"
    for s_ in (arc_len + (gate + hook_len) * k / 10 for k in range(11))))
ex = [round((D - branch_top[0] - 1) * k / 4, 1) for k in range(5)]
log("pulled out along the exit, resting on the sill (mm: deg, mm3): " + ", ".join(
    f"{y}: {exit_tilt(branch_top[0] + y):.0f}, {overlap(h, drawer_at(da, 'exit', y=y)):.3f}" for y in ex))
log("pulled out along the exit, held level (mm: mm3): " + ", ".join(f"{y}: {overlap(h, drawer_at(da, 'held', y=y)):.3f}" for y in ex))
log("sliding (pin y: mm3): " + ", ".join(f"{y_pin + t:.0f}: {overlap(h, Pos(0, t, 0) * da):.3f}" for t in (travel * 0.25, travel * 0.5, travel * 0.75, travel - 3)))
if True:
    # The drawer of the unit above, moving through its own states, against what stands proud of this drawer's face
    proud = hd if SEP else solid(d & Pos(0, D + 0.01, 0) * Box(W, 50, H, align=Align.MIN))
    above = Pos(0, 0, U["rows"] * pitch)
    st_ = [("closed", None), ("open", None), ("tilted", None), ("pushed", None)] + [(f"exit {y}", ("exit", y)) for y in ex] + [(f"held {y}", ("held", y)) for y in ex]
    res = []
    for name_, spec in st_:
        m = above * (drawer_at(da, spec[0], y=spec[1]) if spec else drawer_at(da, name_))
        res.append(f"{name_}: {overlap(m, proud):.3f}, {m.distance_to(proud):.2f}")
    log(f"drawer of the unit above vs this drawer's {PULL} (state: mm3, clearance mm): " + "; ".join(res))

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
extra = []
if SEP:
    # Plate handle on its top (rib top and plate top edge on the bed), scoop on its back, pin lying on a flat
    hdp, pnp = to_bed(pull_print_rot(PT) * pull_part(PT)), to_bed(hpin)
    extra = [(hdp, f"{NAME}_handle_print", HERE / "print"), (pnp, f"{NAME}_handle_pin_print", HERE / "print")]
for part, stem, out in ((hp, f"{NAME}_housing_print", HERE / "print"), (dp, f"{NAME}_drawer_print", HERE / "print"), *extra,
                        (htp, f"{NAME}_fit_test_housing_print", TEST), (dtp, f"{NAME}_fit_test_drawer_print", TEST),
                        (cpp, f"{NAME}_pocket_coupon_print", TEST)):
    export_step(part, str(out / f"{stem}.step"))
    export_stl(part, str(out / f"{stem}.stl"))
    if out == TEST:                                  # print/ gets one 3MF only, the all-parts plate (Zeid, 2026-10-19)
        write_3mf([(stem, *shape_mesh(part))], out / f"{stem}.3mf")
    bad = bad_faces(part)
    bb = part.bounding_box()
    log(f"{stem}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, faces {len(part.faces())}, overhangs flatter than 45 deg: {len(bad)}")
    for b in sorted(bad, key=lambda t: -t[1])[:10]:
        log(f"    {b[0]:.1f} deg from vertical, area {b[1]} mm2, at ({b[2].X:.1f}, {b[2].Y:.1f}, {b[2].Z:.1f})")
# The fit test pieces on one plate (plain 3MF: Bambu Studio imports every object onto the current plate).
write_3mf([("housing front", *shape_mesh(htp, -60, 0)), ("drawer rear", *shape_mesh(dtp, 40, 0)),
           ("pocket coupon", *shape_mesh(cpp, 0, 60))], TEST / f"{NAME}_fit_test_plate.3mf")
# Housing and drawer side by side on one plate, 10 mm apart, centred on the origin:
# a Bambu Studio project with the template's settings.
gap = 10.0
hb, db = hp.bounding_box(), dp.bounding_box()
hx = -(hb.size.X + gap + db.size.X) / 2 - hb.min.X
dx = hx + hb.max.X + gap - db.min.X
objs = [("housing", Pos(hx, -hb.center().Y, 0) * hp), ("drawer", Pos(dx, -db.center().Y, 0) * dp)]
if SEP:
    # The handle and its two pins in a row in front of them
    yr = -max(hb.size.Y, db.size.Y) / 2 - gap - hdp.bounding_box().size.Y / 2
    objs += [("handle", Pos(-15, yr, 0) * hdp), ("pin 1", Pos(15, yr, 0) * pnp), ("pin 2", Pos(30, yr, 0) * pnp)]
write_bambu_project([(NAME, objs)], HERE / "print" / f"{NAME}_all_parts.3mf", template=TEMPLATE)
log(f"{NAME}_all_parts: housing and drawer on one plate, {hb.size.X + gap + db.size.X:.1f} x {max(hb.size.Y, db.size.Y):.1f}" + (", the handle and two pins in front" if SEP else ""))
(HERE / "report.txt").write_text("\n".join(lines) + "\n")
result = Compound(children=[h, da, *hks])
