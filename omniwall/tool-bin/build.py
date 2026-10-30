# Omniwall tool bins: bins for picks, pencils and markers that hang on the same
# hooks as the arc drawers and trays, by dovetail pockets in their back wall, with
# a drop-in grid that rests on a ledge round the inside and snaps in with a spring
# tab in each side (params.yaml says what each part is and where its sizes came from).
# Hook pockets come from ../hook_geometry.py and ../panel.yaml, as the trays' do.
# Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py <bin folder>
# params.yaml here holds the shared defaults; each bin is a folder (such as
# caddy-3x2) whose params.yaml overrides them section by section, key by key.
# It writes the bin folder's step/ (the parts and the assembly on Bridge hook 1Us),
# print/ (STEP and STL per part laid as on the bed, one all-parts 3MF), test prints
# in test-prints/ (git-ignored) and report.txt.
# Coordinates: x across from the left face, y out from the panel face (back face
# at y = 0), z up from the bin's bottom edge. The bin prints as it hangs, the
# grid top face down.
import copy
import math
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
if len(sys.argv) < 2:
    sys.exit("usage: build.py <bin folder>, one of: " + ", ".join(sorted(p.parent.name for p in SRC.glob("*/params.yaml"))))
HERE = SRC / sys.argv[1]
P = yaml.safe_load((SRC / "params.yaml").read_text())
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

_export_step = export_step

U, BN, PK, LB, GR, SN = P["unit"], P["bin"], P["pocket"], P["label"], P["grid"], P["snap"]
NAME = U["file_prefix"]
pitch = panel["pitch"]
hook = panel["bridge_hook"]
dm = copy.deepcopy(panel["dovetail_mount"])
dv, pk = dm["dovetail"], dm["pocket"]
pk["spine_clearance"] = PK["spine_clearance"]     # the drawer housing's print-tested pocket (coupon 3)
pk["flank_gap"] = PK["flank_gap"]
pk["ridge"]["height"] = PK["ridge_height"]
ROWS = BN["rows"]
W = BN["cells"] * pitch - BN["gap"]
H = ROWS * pitch - BN["gap"]
HF = BN["front_height"] or H                          # front rim height (the tall bin's is lower)
D = BN["depth"]
T = BN["wall"]
F = BN["floor"]
edge = BN["gap"] / 2
hook_z0 = (pitch - panel["slot"]["length"] / 2) - hook["bar_bottom"] - edge   # as the arc drawer and trays
hook_rows = [hook_z0 + r * pitch for r in range(ROWS)]
hook_cols = pocket_columns(BN["cells"], pitch, edge, BN.get("channels"))
HH = hook["height"]
seat_z = hook_rows[-1] + HH + pk["top_clearance"]
cx = dv["block_width"] / 2
hh = dv["head_width"] / 2 + pk["side_clearance"]
yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]
yb = dv["block_depth"] + pk["spine_clearance"]
B = yf + hh + BN["back_front_wall"]                  # back wall thickness, as the trays and the housing's back plate
TOP = H + 1                                           # cavities run up past the walls
w_hook = max(dv["head_width"], dv["block_width"]) / 2               # hook front's half width
w_pocket = w_hook + pk["side_clearance"]                            # pocket's half width
eaves = seat_z - (w_pocket - w_hook)                                # gable meets the pocket walls here
RF = BN["plan_front_radius"]
RB = BN["inner_back_radius"]
TI = GR["thickness"]
ZL = HF - GR["below_rim"] - TI                        # ledge top: the grid rests here
ZM = ZL + TI / 2                                      # snap height: tab ridges and wall grooves
DIV = BN["divider"]
SEATS = GR.get("seats", True)                         # the ledge and tab grooves the grid snaps into
WITH_GRID = SEATS and GR.get("include", True)         # the grid itself, as a part and in the 3MF

lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


def export_step(shape, path):
    """build123d 0.13 refuses to write some labelled shapes to STEP; retry as a plain solid."""
    try:
        return _export_step(shape, str(path))
    except RuntimeError:
        return _export_step(Solid(shape.wrapped), str(path))


# ---------------------------------------------------------------- 2D profiles (as the trays)
def _unit(x, y):
    d = math.hypot(x, y)
    return x / d, y / d


def corners(pts):
    """(u, v, r) polygon -> list of (point, None) or (point, (t1, mid, t2, centre, r)) with tangent fillets."""
    out, n = [], len(pts)
    for i, (u, v, r) in enumerate(pts):
        if r == 0:
            out.append(((u, v), None))
            continue
        a = _unit(u - pts[i - 1][0], v - pts[i - 1][1])
        b = _unit(pts[(i + 1) % n][0] - u, pts[(i + 1) % n][1] - v)
        phi = math.acos(max(-1, min(1, a[0] * b[0] + a[1] * b[1])))
        t = r * math.tan(phi / 2)
        t1, t2 = (u - a[0] * t, v - a[1] * t), (u + b[0] * t, v + b[1] * t)
        bis = _unit(b[0] - a[0], b[1] - a[1])
        dc = r / math.cos(phi / 2)
        c = (u + bis[0] * dc, v + bis[1] * dc)
        m = _unit(u - c[0], v - c[1])
        out.append(((u, v), (t1, (c[0] + m[0] * r, c[1] + m[1] * r), t2, c, r)))
    return out


def face(pts, to3d):
    """Face from a filleted (u, v, r) polygon; to3d maps (u, v) to a 3D point."""
    seq = []
    for p, f in corners(pts):
        if f is None:
            seq.append(("p", p))
        else:
            seq.append(("p", f[0]))
            seq.append(("a", f[1], f[2]))
    edges = []
    start = cur = seq[0][1]
    for item in seq[1:] + [("p", start)]:
        if item[0] == "p":
            if math.dist(cur, item[1]) > 1e-6:
                edges.append(Line(to3d(*cur), to3d(*item[1])))
            cur = item[1]
        else:
            edges.append(ThreePointArc(to3d(*cur), to3d(*item[1]), to3d(*item[2])))
            cur = item[2]
    return Face(Wire(edges))


YZ = lambda x: (lambda u, v: (x, u, v))      # side profile at x: (y, z)
XZ = lambda y: (lambda u, v: (u, y, v))      # cross profile at y: (x, z)
XY = lambda z: (lambda u, v: (u, v, z))      # plan at z: (x, y)


def solid(s):
    """the one solid in s (booleans hand back Compounds or ShapeLists)"""
    sols = s.solids() if hasattr(s, "solids") else [s]
    assert len(sols) == 1, f"expected one solid, got {len(sols)}"
    return sols[0]


def check(name, before, after):
    """a boolean or fillet that changed nothing failed silently"""
    nb, na = len(before.faces()), len(after.faces())
    assert na != nb or abs(before.volume - after.volume) > 1e-3, f"{name}: no change ({nb} faces)"
    return after


def slab(f, z0, z1):
    """a plan face (at z = 0) extruded from z0 to z1"""
    return extrude(f.moved(Location((0, 0, z0))), z1 - z0)


def vprism(p0, along, out, length, h):
    """45 deg V prism: its base on a wall, centred at p0, sticking out along `out` by h,
    running `length` along `along` (a snap ridge, or the cutter for a V groove)"""
    p0, a, o = Vector(p0), Vector(along).normalized(), Vector(out).normalized()
    z = Vector(0, 0, 1)
    s = p0 - a * (length / 2) - o * 0.02            # base a hair inside the wall, so it fuses
    tri = Face(Wire.make_polygon([s + z * (h + 0.02), s + o * (h + 0.02), s - z * (h + 0.02)], close=True))
    return extrude(tri, length, dir=a)


# ---------------------------------------------------------------- the bin's outside
def pocket(xc):
    """Pocket channel for one hook column: the shared dovetail pocket from
    hook_geometry (open at the bottom, snap ridges under the seat), a ridge pair
    one pitch lower for every further row of hooks, and a 45 deg gable top through
    the hook's top corners at the seat height, so it prints upright without a flat
    bridge and the bin hangs where a flat seat would put it (as the trays)."""
    zl = -(seat_z - HH) - 1
    zt = HH + pk["top_clearance"]
    ze = zt - (w_pocket - w_hook)
    v = pocket_void(dm, HH, 0.0, zl)
    r = pk["ridge"]
    y_ridge_end = dv["block_depth"] + dv["depth"] - dv["notch"]["front_land"] - r["front_gap"]
    for k in range(1, ROWS if PK["ridges_every_row"] else 1):
        zc = zt - r["below_top"] - k * pitch
        for x_face, inward in ((cx + hh, -1), (cx - hh, 1)):
            v = v - v_groove_prism(x_face, inward, zc, yb, y_ridge_end, r["height"], r["flank_angle"], r["tip_radius"])
    v = solid(v & Pos(cx, yf / 2, (zl - 1 + ze) / 2) * Box(20, yf + 10, ze - zl + 1))
    e = 0.02    # gable starts a hair wider and lower than the walls, so no flat strip is left
    roof = extrude(face([(cx - w_pocket - e, ze - e, 0), (cx + w_pocket + e, ze - e, 0),
                         (cx, ze + w_pocket, 0)], XZ(-1)), yf + 1, dir=(0, 1, 0))
    return Pos(xc - cx, 0, seat_z - HH) * solid(v + roof)


def shell():
    """Solid outer body: plan with rounded front corners, H tall; the tall bin's
    side walls fall to the front height in one S of two arcs (as the trays');
    outside bottom edges a 45 deg chamfer rolling into a radius; pockets cut."""
    body = extrude(face([(0, 0, 0), (W, 0, 0), (W, D, RF), (0, D, RF)], XY(0)), H)
    if HF < H:
        a, b = (BN["side_s_start"], HF), (BN["side_s_end"], H)
        th = math.atan2(H - HF, a[0] - b[0])
        t = min(0.47 * math.dist(a, b), D - a[0] - 1, b[0] - 1)   # tangent length: two arcs, a straight between
        R = t / math.tan(th / 2)
        # The top bend starts in front of the back wall, so the back wall's top is one
        # flat face (as the trays: a big arc over it sliced into wide stepped strips)
        tb = min(t, b[0] - B - BN["back_top_flat"])
        Rb = tb / math.tan(th / 2)
        side = extrude(face([(0, 0, 0), (D, 0, 0), (D, HF, 0), (a[0], a[1], R), (b[0], b[1], Rb), (0, H, 0)], YZ(0)),
                       W, dir=(1, 0, 0))
        body = solid(body & side)
    bot = [e for e in body.edges() if e.center().Z < 1e-3 and e.center().Y > 0.5]
    body = check("bed chamfer", body, solid(body.chamfer(BN["bed_chamfer"], None, bot)))
    back = [e for e in body.edges() if e.center().Z < 1e-3 and e.center().Y < 0.5]
    body = solid(body.chamfer(BN["back_bed_chamfer"], None, back))
    c = BN["bed_chamfer"]
    roll = [e for e in body.edges() if abs(e.center().Z - c) < 1e-3 and e.center().Y > 0.5
            and min(e.center().X, W - e.center().X, D - e.center().Y) < c + 0.01]
    body = check("bed round", body, solid(body.fillet(BN["bed_round"], roll)))
    for xc in hook_cols:
        body = check("pocket", body, solid(body - pocket(xc)))
    return body


def round_tops(body, r, zmin):
    """Round the top edges of the walls: every edge of an upward face at or above
    zmin, except edges two such faces share (tangent seams) and the panel side (as the trays)."""
    tops = [f for f in body.faces() if f.center().Z > zmin - 1e-3 and f.normal_at(f.center()).Z > 0.3
            and not (f.center().Y < yf + 1 and f.center().Z < seat_z + 0.01)]   # not the pockets' ridges
    count = {}
    for f in tops:
        for e in f.edges():
            count.setdefault(e, 0)
            count[e] += 1
    edges = [e for e, n in count.items() if n == 1 and e.bounding_box().max.Y > 0.05]
    return check("round tops", body, solid(body.fillet(r, edges)))


# ---------------------------------------------------------------- the inside
def compartments():
    """Plan outlines (x0, x1, rb_left, rb_right, rf_left, rf_right) of the inside spaces;
    the first one takes the grid"""
    rf = RF - T
    if not DIV:
        return [(T, W - T, RB, RB, rf, rf)]
    xm = W / 2
    return [(T, xm - DIV / 2, RB, RB, rf, RB), (xm + DIV / 2, W - T, RB, RB, RB, rf)]


def outline(c, grow=0.0, xgrow=None):
    """plan face (z = 0) of a compartment, grown by `grow` (negative shrinks);
    `xgrow`, if given, for the side walls instead"""
    x0, x1, rbl, rbr, rfl, rfr = c
    g = grow
    gx = g if xgrow is None else xgrow
    r = max(g, gx)                                          # corners: the smaller shrink
    return face([(x0 - gx, B - g, max(rbl + r, 0)), (x1 + gx, B - g, max(rbr + r, 0)),
                 (x1 + gx, D - T + g, max(rfr + r, 0)), (x0 - gx, D - T + g, max(rfl + r, 0))], XY(0))


def cavity(c, ledge):
    """Inside space: coved into the floor; with a ledge, a ring of 2 mm at ZL whose
    underside is 45 deg (so it prints upright), straight walls above."""
    cv = BN["cove"]
    if not ledge:
        box = slab(outline(c), F, TOP)
        return solid(box.fillet(cv, [e for e in box.edges() if e.center().Z < F + 1e-3]))
    L = GR["ledge"]
    low = slab(outline(c), F, ZL - L)
    low = solid(low.fillet(cv, [e for e in low.edges() if e.center().Z < F + 1e-3]))
    taper = loft([outline(c).moved(Location((0, 0, ZL - L))), outline(c, -L).moved(Location((0, 0, ZL)))])
    up = slab(outline(c), ZL, TOP)
    return solid(low + taper + up)


def snap_grooves(c):
    """V grooves in the walls either side of the grid's compartment, for the tabs' ridges"""
    x0, x1 = c[0], c[1]
    ym = (B + D - T) / 2
    ln = SN["tab_length"] + 2 * SN["groove_extra"]
    return [vprism((x0, ym, ZM), (0, 1, 0), (-1, 0, 0), ln, SN["groove"]),
            vprism((x1, ym, ZM), (0, 1, 0), (1, 0, 0), ln, SN["groove"])]


def label_holder(xm):
    """The arc drawers' U holder on the front face, open at the top: a bottom rail
    with a 45 deg underside, and two side rails that wrap over the label's edges;
    its top is below_rim under the front rim."""
    rail, ret = LB["rail"], LB["return"]
    hd = rail + LB["thickness"] + LB["thickness_clearance"]        # how far the holder stands proud
    inner = LB["width"] + 2 * LB["side_clearance"]
    z_top = HF - LB["below_rim"]
    z_seat = z_top - LB["top_clear"] - LB["height"]                 # the label rests here
    za = z_seat - hd - rail
    half = inner / 2 + rail
    prof = Polygon((D - 1, za), (D, za), (D + hd, za + hd), (D + hd, z_seat), (D - 1, z_seat), align=None)
    bottom = extrude(Plane.YZ.offset(xm - half) * prof, 2 * half, dir=(1, 0, 0))
    post = Pos(xm - half, D - 1, z_seat - 0.1) * Box(rail, hd + 1, z_top - z_seat + 0.1, align=Align.MIN)
    wrap = Pos(xm - half + rail - 0.01, D + hd - rail, z_seat - 0.1) * Box(ret + 0.01, rail, z_top - z_seat + 0.1, align=Align.MIN)
    side = post + wrap
    assert half < W / 2 - RF, f"label holder ({2 * half:.1f}) wider than the flat front ({W - 2 * RF:.1f})"
    return solid(bottom + side + mirror(side, Plane.YZ.offset(xm)))


def bin_body():
    body = shell()
    comps = compartments()
    for i, c in enumerate(comps):
        body = check("cavity", body, solid(body - cavity(c, ledge=(i == 0 and SEATS))))
    body = round_tops(body, BN["lip_round"], HF)
    for g in snap_grooves(comps[0]) if SEATS else []:
        body = check("snap groove", body, solid(body - g))
    body = check("label holder", body, solid(body + label_holder(W / 2)))
    body.label = "bin"
    return body


# ---------------------------------------------------------------- the grid
def rect(x0, y0, x1, y1):
    return face([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], XY(0))


def hole_faces(x0, y0, x1, y1):
    """plan faces (z = 0) of the grid's holes inside the box x0..x1, y0..y1 (before clipping)"""
    rib, pat = GR["rib"], U["pattern"]
    out = []
    if pat == "square":
        def fit(L, s=GR["square_cell"]):
            n = max(1, int((L + rib) // (s + rib)))
            return n, (L - (n - 1) * rib) / n
        nx, sx = fit(x1 - x0)
        ny, sy = fit(y1 - y0)
        for i in range(nx):
            for j in range(ny):
                out.append(Pos(x0 + sx / 2 + i * (sx + rib), y0 + sy / 2 + j * (sy + rib)) * RectangleRounded(sx, sy, 1.2))
    elif pat == "hex":
        af = GR["hex_flats"]
        p = af + rib
        r = af / math.sqrt(3)
        cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
        for j in range(-6, 7):
            for i in range(-7, 8):
                hx = cx0 + i * p + (p / 2 if j % 2 else 0)
                hy = cy0 + j * p * math.sqrt(3) / 2
                if x0 - af / 4 <= hx <= x1 + af / 4 and y0 - r / 3 <= hy <= y1 + r / 3:
                    out.append(Pos(hx, hy) * Rot(0, 0, 30) * RegularPolygon(r, 6))
    elif pat == "mixed":
        (db, nb), (ds, ns, rs) = GR["mixed"]["big"], GR["mixed"]["small"]
        Lx = x1 - x0
        # a count left null fills the space: as many holes across as fit with a rib
        # between, as many small rows as leave the front slot mixed.slot_min deep
        nb = nb or max(1, int((Lx + rib) // (db + rib)))
        ns = ns or max(1, int((Lx + rib) // (ds + rib)))
        if rs is None:
            rs = max(0, int((y1 - y0 - db - rib - GR["mixed"].get("slot_min", 8.0)) // (ds + rib)))

        def row(d, n, y):
            if n == 1:
                return [Pos((x0 + x1) / 2, y) * Circle(d / 2)]
            step = (Lx - d) / (n - 1)
            assert step - d >= rib - 1e-6, f"holes of {d} too close ({step - d:.2f} between)"
            return [Pos(x0 + d / 2 + k * step, y) * Circle(d / 2) for k in range(n)]
        out += row(db, nb, y0 + db / 2)
        y = y0 + db + rib
        for _ in range(rs):
            out += row(ds, ns, y + ds / 2)
            y += ds + rib
        assert y1 - y > 4, f"no room for the front slot ({y1 - y:.1f})"
        out.append(Pos((x0 + x1) / 2, (y + y1) / 2) * SlotOverall(Lx, y1 - y))
    return out


def spring_tab(g, xe, inward, yc):
    """Spring tab in the grid's side at x edge xe (inward +1 on the left side, -1 on
    the right): a beam tab_thickness wide, fixed at its back end, a slot behind it
    and across its front end; a 45 deg ridge on its outer face at ZM."""
    t, s, L = SN["tab_thickness"], SN["slot"], SN["tab_length"]
    xs0, xs1 = sorted((xe + inward * t, xe + inward * (t + s)))
    slot = Pos((xs0 + xs1) / 2, yc, ZM) * Box(s, L, TI + 2)
    xa, xb = sorted((xe - inward * 1.0, xe + inward * (t + s)))
    end = Pos((xa + xb) / 2, yc + L / 2 + s / 2, ZM) * Box(xb - xa, s, TI + 2)
    g = check("tab slot", g, solid(g - slot - end))
    # 45 deg chamfer on the slot's fixed sides at the grid top (the bed side when
    # printed), so first-layer squish can't bridge the slot to the tab
    c, zt, xf = SN["slot_chamfer"], ZL + TI, xe + inward * (t + s)
    side = vprism((xf, yc + s / 2, zt), (0, 1, 0), (inward, 0, 0), L + s, c)
    far = vprism(((xa + xb) / 2, yc + L / 2 + s, zt), (1, 0, 0), (0, 1, 0), xb - xa, c)
    g = check("slot chamfer", g, solid(g - side - far))
    ridge = vprism((xe, yc + 1.0, ZM), (0, 1, 0), (-inward, 0, 0), L - 4, SN["ridge"])
    return check("tab ridge", g, solid(g + ridge))


def grid():
    c = compartments()[0]
    cl, bd, pad = GR["clearance"], GR["border"], SN["pad"]
    plate = outline(c, -cl, -GR["side_clearance"])
    bb = plate.bounding_box()
    x0, x1, y0, y1 = bb.min.X + pad, bb.max.X - pad, bb.min.Y + bd, bb.max.Y - bd
    g = slab(plate, ZL, ZL + TI)
    clip = outline(c, -cl - bd) & rect(x0, y0, x1, y1)
    cut, n = None, 0
    for h in hole_faces(x0, y0, x1, y1):
        hf = (h & clip).faces()
        if not hf or sum(f.area for f in hf) < GR["min_hole_area"]:
            continue
        s = slab(hf[0], ZL - 1, ZL + TI + 1)
        cut = s if cut is None else cut + s
        n += 1
    g = check("holes", g, solid(g - cut))
    top = [e for e in g.edges() if e.bounding_box().min.Z > ZL + TI - 1e-3]
    g = check("top chamfer", g, solid(g.chamfer(GR["top_chamfer"], None, top)))
    yc = (bb.min.Y + bb.max.Y) / 2
    g = spring_tab(g, bb.min.X, 1, yc)
    g = spring_tab(g, bb.max.X, -1, yc)
    g.label = "grid"
    return g, n


# ---------------------------------------------------------------- checks (as the trays)
def tolerance(s):
    from OCP.BRep import BRep_Tool
    return max(BRep_Tool.Tolerance_s(e.wrapped) for e in s.edges())


def hooks():
    hk = bridge_hook(panel, ROOT)
    out = []
    for xc in hook_cols:
        for z in hook_rows:
            h = Pos(xc - cx, -hook["panel_front_y"], z) * hk
            h.label = "hook"
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


def bad_faces(part, limit=45.0):
    """Faces of a print-orientation part that face down flatter than `limit`
    degrees from vertical and are not on the bed: (deg from vertical, area, point)."""
    lim = -math.cos(math.radians(limit)) - 1e-3
    out = []
    for f in part.faces():
        worst, where = 1.0, None
        for u in (0.0, 0.1, 0.5, 0.9, 1.0):
            for w in (0.0, 0.1, 0.5, 0.9, 1.0):
                try:
                    n = f.normal_at(u, w)
                except Exception:                            # degenerate point (a fillet's pole)
                    continue
                p = f.position_at(u, w)
                if p.Z > 0.05 and n.Z < worst:
                    worst, where = n.Z, p
        if worst < lim:
            out.append((round(90 - math.degrees(math.acos(min(1, -worst))), 1), round(f.area, 2), where))
    return out


def steepest_down(part):
    """flattest downward-facing angle (deg from vertical) on any face off the bed"""
    worst = 1.0
    for f in part.faces():
        for u in (0.0, 0.1, 0.5, 0.9, 1.0):
            for w in (0.0, 0.1, 0.5, 0.9, 1.0):
                if f.position_at(u, w).Z > 0.05:
                    try:
                        worst = min(worst, f.normal_at(u, w).Z)
                    except Exception:
                        pass
    return 0.0 if worst >= 0 else round(90 - math.degrees(math.acos(min(1, -worst))), 1)


def write_print(stem, p, folder):
    export_step(p, folder / f"{stem}.step")
    export_stl(p, str(folder / f"{stem}.stl"))
    bad = bad_faces(p)
    bb = p.bounding_box()
    log(f"{stem}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, faces {len(p.faces())}, "
        f"flattest face pointing down {steepest_down(p):.1f} deg from vertical, overhangs flatter than 45 deg: {len(bad)}")
    for b in sorted(bad, key=lambda t: -t[1])[:10]:
        log(f"    {b[0]:.1f} deg from vertical, area {b[1]} mm2, at ({b[2].X:.1f}, {b[2].Y:.1f}, {b[2].Z:.1f})")


def plate(items, path):
    """parts side by side on one plate, far enough apart to print by object (bambu_object_gap), centred on the plate: a Bambu
    Studio project with the template's settings, print.project on top and each
    part's own print.<kind> (items are (label, part, kind))"""
    gap = bambu_object_gap(TEMPLATE)
    # lowest first: by object, Bambu Studio prints the parts in this order, and a
    # part taller than the head's clearance under its rod has to come last
    items = sorted(items, key=lambda it: it[1].bounding_box().size.Z)
    objs = [(label, p, P["print"].get(kind) or {}) for label, p, kind in items]
    plates, row = plates_in_a_row(NAME, objs, gap, bambu_bed(bambu_config(TEMPLATE))[0])  # too wide: a plate each
    write_bambu_project(plates, path, template=TEMPLATE, settings=P["print"]["project"])
    return row if len(plates) == 1 else None


# ---------------------------------------------------------------- build
if __name__ == "__main__":
    for sub in ("step", "print", "test-prints"):
        (HERE / sub).mkdir(exist_ok=True)
    body = bin_body()
    gr, nholes = grid() if WITH_GRID else (None, 0)
    parts = [body, gr] if WITH_GRID else [body]
    log(f"{NAME}: {W:.1f} wide, {D:g} deep, {H:.1f} tall" + (f" at the back, {HF:.1f} at the front" if HF < H else "")
        + f"; back wall {B:.3f} thick; pockets at x {[round(x, 2) for x in hook_cols]}, hook bottoms z "
        f"{[round(z, 2) for z in hook_rows]}, seat z {seat_z:.2f}, gable eaves z {eaves:.2f}"
        + (f"; ledge top z {ZL:.2f}, snap z {ZM:.2f}" if SEATS else "; no grid ledge or tab grooves")
        + ("" if WITH_GRID else "; no grid part"))
    for s in parts:
        bb = s.bounding_box()
        tol = tolerance(s)
        assert tol < 1e-3, f"{s.label}: edge tolerance {tol:.4f} (SolidCraft opens it as an open body)"
        log(f"{s.label}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {s.volume:.1f} mm3, "
            f"{len(s.faces())} faces, solids {len(s.solids())}, valid {s.is_valid}, max edge tolerance {tol:.1e}")
        export_step(s, HERE / "step" / f"{NAME}_{s.label}.step")
    if WITH_GRID:
        log(f"grid: {U['pattern']} pattern, {nholes} holes")

    # Measured on the solids, not read from the code.
    roof = [f for f in body.faces() if f.center().Y < yf + 0.5 and abs(f.normal_at(f.center()).Z + math.sqrt(0.5)) < 1e-3
            and abs(f.normal_at(f.center()).X) > 0.5]
    zs = [v.Z for f in roof for v in f.vertices()]
    log(f"measured: {len(roof)} gable faces in the pockets (expect {2 * len(hook_cols)}), z {min(zs):.3f} to {max(zs):.3f} "
        f"(eaves {eaves:.3f}, the hook's top corners at {seat_z:.3f})")
    if SEATS:
        ledge = [f for f in body.faces() if abs(f.center().Z - ZL) < 1e-3 and f.normal_at(f.center()).Z > 0.99]
        log(f"measured: ledge faces at z {ZL:.2f}: {len(ledge)}, area {sum(f.area for f in ledge):.1f} mm2"
            + (f"; grid underside z {gr.bounding_box().min.Z:.3f}, grid top {gr.bounding_box().max.Z:.3f} ({HF - gr.bounding_box().max.Z:.2f} under the front rim)" if WITH_GRID else ""))
    if WITH_GRID:
        log(f"grid vs bin seated: overlap {overlap(body, gr):.4f} mm3 (the tab ridges pressing {SN['ridge'] - GR['side_clearance'] - SN['groove']:.2f} into the grooves, the preload that holds the grid centred); "
            f"grid lifted 0.05: clearance {body.distance_to(Pos(0, 0, 0.05) * gr):.3f}")
        push = 2.0                                         # grid held this much higher: ridges against the plain wall above the grooves
        log(f"grid {push:.1f} higher (on its way in): overlap {overlap(body, Pos(0, 0, push) * gr):.3f} mm3, the ridges "
            f"{SN['ridge'] - GR['side_clearance']:.1f} into the walls: what each tab bends to get past")
    hks = hooks()
    interf = sum(overlap(body, k) for k in hks)
    log(f"hooks vs bin: {interf:.3f} mm3 over {len(hks)} Bridge hook 1Us ({len(hook_cols)} columns x {ROWS} rows; ridges "
        f"{pk['ridge']['height']:.2f} tall, room for {dv['notch']['depth'] + pk['side_clearance']:.2f} in a seated hook's notch: "
        f"overlap only if taller)")
    if WITH_GRID:
        log(f"hooks vs grid: {sum(overlap(gr, k) for k in hks):.3f} mm3")
    export_step(Compound(children=[*parts, *hks], label=NAME), HERE / "step" / f"{NAME}_assembly.step")

    # Print orientation: the bin as it hangs, the grid top face down.
    pb = to_bed(Rot(0, 0, 180) * body)    # front toward the plate's front, so Bambu Studio's seam at "back" lands on the back wall
    write_print(f"{NAME}_bin_print", pb, HERE / "print")
    if WITH_GRID:
        pg = to_bed(Rot(180, 0, 0) * gr)
        write_print(f"{NAME}_grid_print", pg, HERE / "print")
        wd = plate([("bin", pb, "bin"), ("grid", pg, "grid")], HERE / "print" / f"{NAME}_all_parts.3mf")
        log(f"{NAME}_all_parts.3mf: bin and grid " + (f"on one plate, {wd:.1f} wide" if wd else "on a plate each (too wide together for the bed)"))
    else:
        wd = plate([("bin", pb, "bin")], HERE / "print" / f"{NAME}_all_parts.3mf")
        log(f"{NAME}_all_parts.3mf: the bin, {wd:.1f} wide")

    # Test prints: the back wall round the first pocket; the bin's top band with the whole grid (snap test).
    hc = P["coupon"]["half_width"]
    cp = to_bed(Rot(0, 0, 180) * solid(body & Pos(hook_cols[0], B / 2 - 0.5, H / 2) * Box(2 * hc, B + 1, H + 2)))
    write_print(f"{NAME}_pocket_coupon_print", cp, HERE / "test-prints")
    plate([("pocket coupon", cp, "bin")], HERE / "test-prints" / f"{NAME}_pocket_coupon_print.3mf")
    if WITH_GRID:
        z0 = ZL - GR["ledge"] - P["coupon"]["ring_below_ledge"]
        zt = min(H, HF + 3) + 1                           # the tall bin: cut its rising back off just above the front rim
        band = body & Pos(W / 2, D / 2, (z0 + zt) / 2) * Box(W + 10, D + 10, zt - z0)
        band = max(band.solids(), key=lambda s: s.volume)
        rb = Pos(0, 0, -z0) * band
        rb = Pos(-rb.bounding_box().center().X, -rb.bounding_box().center().Y, 0) * rb
        write_print(f"{NAME}_snap_test_band_print", rb, HERE / "test-prints")
        wd = plate([("snap test band", rb, "bin"), ("grid", pg, "grid")], HERE / "test-prints" / f"{NAME}_snap_test.3mf")
        log(f"snap test (test-prints): the bin from z {z0:.1f} to {min(zt, H):.1f} ({min(zt, H) - z0:.1f} tall band) and the whole grid, " + (f"one plate {wd:.1f} wide" if wd else "a plate each (too wide together for the bed)"))
    (HERE / "report.txt").write_text("\n".join(lines) + "\n")
