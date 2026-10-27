# Omniwall lean bin: a bin whose front leans out from the panel, so tools lie back
# against the sloped front and lean toward you. It hangs on the same hooks as the
# arc drawers, trays and tool bins, by dovetail pockets in its back wall
# (params.yaml says what each size is and where its numbers came from).
# Hook pockets come from ../hook_geometry.py and ../panel.yaml, as the tool bins' do.
# Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py <size folder>
# params.yaml here holds the shared defaults; each size is a folder (such as
# 3x3x65) whose params.yaml overrides them section by section, key by key.
# It writes the size folder's step/ (the bin and the assembly on Bridge hook 1Us),
# print/ (STEP and STL laid as on the bed, one all-parts 3MF), test prints in
# test-prints/ (git-ignored) and report.txt.
# Coordinates: x across from the left face, y out from the panel face (back face
# at y = 0), z up from the bin's bottom edge. The bin prints as it hangs.
import copy
import math
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
if len(sys.argv) < 2:
    sys.exit("usage: build.py <size folder>, one of: " + ", ".join(sorted(p.parent.name for p in SRC.glob("*/params.yaml"))))
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

U, BN, PK = P["unit"], P["bin"], P["pocket"]
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
D = BN["depth"]
T = BN["wall"]
F = BN["floor"]
edge = BN["gap"] / 2
hook_z0 = (pitch - panel["slot"]["length"] / 2) - hook["bar_bottom"] - edge   # as the arc drawer, trays and bins
hook_rows = [hook_z0 + r * pitch for r in range(ROWS)]
hook_cols = [k * pitch - edge for k in range(1, BN["cells"])]
HH = hook["height"]
seat_z = hook_rows[-1] + HH + pk["top_clearance"]
cx = dv["block_width"] / 2
hh = dv["head_width"] / 2 + pk["side_clearance"]
yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]
yb = dv["block_depth"] + pk["spine_clearance"]
B = yf + hh + BN["back_front_wall"]                  # back wall thickness, as the trays and the bins
w_hook = max(dv["head_width"], dv["block_width"]) / 2               # hook front's half width
w_pocket = w_hook + pk["side_clearance"]                            # pocket's half width
eaves = seat_z - (w_pocket - w_hook)                                # gable meets the pocket walls here

# The side view (Zeid's sketch): a flat top at the back, the rim falling at rim_slope
# to the nose, the front leaning back at front_lean down to the foot. The rounded
# nose's furthest point is at `depth`, so the corner it rounds sits a little further out.
LEAN = math.radians(BN["front_lean"])
TL = math.tan(LEAN)
TR = math.tan(math.radians(BN["rim_slope"]))
TOPF = BN["top_flat"]
RN = BN["nose_radius"]
_a = Vector(math.sin(LEAN), math.cos(LEAN))                      # up the front (y, z)...
_b = Vector(-math.cos(math.atan(TR)), math.sin(math.atan(TR)))   # ...then back along the rim
_bis = (_b - _a).normalized()                                    # towards the nose arc's centre
_out = -_bis.X * RN / math.cos(math.acos(_a.dot(_b)) / 2) - RN  # corner's lead over the arc's furthest point
YN = D + _out                                                    # the nose's corner (before rounding)...
ZN = H - (YN - TOPF) * TR                                        # ...on the rim line
YFOOT = YN - ZN * TL                                             # the front's foot on the bed
UP = Vector(0, math.sin(LEAN), math.cos(LEAN))                   # up the front face
TOP = H + 5                                                      # cavities run up past the walls
RF = BN["plan_front_radius"]
RB = BN["inner_back_radius"]

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


# ---------------------------------------------------------------- 2D profiles (as the tool bins)
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


# ---------------------------------------------------------------- the bin's outside
def pocket(xc):
    """Pocket channel for one hook column, as the tool bins': the shared dovetail
    pocket from hook_geometry (open at the bottom, snap ridges under the seat), a
    ridge pair one pitch lower for every further row of hooks, and a 45 deg gable
    top through the hook's top corners at the seat height, so it prints upright."""
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


def side_profile():
    """The side view as a prism across the whole width. Its front runs 1 mm proud of
    the real front up to where the nose arc starts, so the front itself (and its
    rounded corners) comes from front_block() with no faces lying on each other."""
    pts = [(0, 0, 0), (YFOOT, 0, 0), (YN, ZN, RN), (TOPF, H, BN["top_bend"]), (0, H, 0)]
    nose = corners(pts)[2][1]
    t1 = nose[0]                                    # where the nose arc leaves the front line
    n = Vector(math.cos(LEAN), -math.sin(LEAN))     # the front's outward normal (y, z)
    prof = [(0, 0, 0), (YFOOT + 1 / math.cos(LEAN), 0, 0), (t1[0] + n.X, t1[1] + n.Y, 0),
            (t1[0], t1[1], 0), (YN, ZN, RN), (TOPF, H, BN["top_bend"]), (0, H, 0)]
    return extrude(face(prof, YZ(0)), W, dir=(1, 0, 0))


def front_block():
    """Everything behind the front face, its two front corners rounded plan_front_radius
    across the lean: a rounded rectangle on a plane square to the front face, run
    up and down the lean."""
    pl = Plane(origin=(0, YFOOT, 0), x_dir=(1, 0, 0), z_dir=UP)      # its y points out of the front face
    f = face([(0, -200, 0), (W, -200, 0), (W, 0, RF), (0, 0, RF)], lambda u, v: pl.from_local_coords((u, v)))
    return extrude(f, 200, both=True)


def shell():
    """Solid outer body: the side view, the front's corners rounded, every bottom edge
    chamfered (elephant's foot), pockets cut."""
    body = solid(side_profile() & front_block())
    bot = [e for e in body.edges() if e.bounding_box().max.Z < 1e-3]
    body = check("bed chamfer", body, solid(body.chamfer(BN["bed_chamfer"], None, bot)))
    for xc in hook_cols:
        body = check("pocket", body, solid(body - pocket(xc)))
    return body


# ---------------------------------------------------------------- the inside
def y_inside(z):
    """the inside of the front wall at height z"""
    return YFOOT - T / math.cos(LEAN) + z * TL


def cavity():
    """Inside space: back wall straight up, the front's inside leaning with the
    front, inside corners rounded (as the tool bins: 3.5 at the back, the front's
    corner radius less the wall at the front), coved into the floor."""
    c = extrude(face([(B, F, 0), (y_inside(F), F, 0), (y_inside(TOP), TOP, 0), (B, TOP, 0)], YZ(T)),
                W - 2 * T, dir=(1, 0, 0))
    back = [e for e in c.edges() if e.center().Y < B + 1e-3 and abs(e.center().X - W / 2) > W / 2 - T - 1e-3
            and e.bounding_box().size.Z > 1]
    c = check("inside back corners", c, solid(c.fillet(RB, back)))
    front = [e for e in c.edges() if e.center().Y > B + 1 and abs(e.center().X - W / 2) > W / 2 - T - 1e-3
             and e.bounding_box().size.Z > 1 and e.geom_type == GeomType.LINE]
    c = check("inside front corners", c, solid(c.fillet(RF - T, front)))
    floor = [e for e in c.edges() if e.bounding_box().max.Z < F + 1e-3]
    return check("cove", c, solid(c.fillet(BN["cove"], floor)))


def round_tops(body, r):
    """Round the top edges of the walls: every edge of a face on the rim (the side
    view's top: flat top, bend, rim, nose), except edges two such faces share
    (tangent seams) and the panel side (as the tool bins)."""
    ref = [f for f in side_profile().faces() if f.normal_at(f.center()).Z > 0.2]
    tops = [f for f in body.faces() if f.normal_at(f.center()).Z > 0.2
            and min(g.distance_to(f.center()) for g in ref) < 1e-4]
    count = {}
    for f in tops:
        for e in f.edges():
            count.setdefault(e, 0)
            count[e] += 1
    edges = [e for e, n in count.items() if n == 1 and e.bounding_box().max.Y > 0.05]
    return check("round tops", body, solid(body.fillet(r, edges)))


def bin_body():
    body = shell()
    body = check("cavity", body, solid(body - cavity()))
    body = round_tops(body, BN["lip_round"])
    body.label = "bin"
    return body


# ---------------------------------------------------------------- checks (as the tool bins)
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


def bad_faces(part, limit=45.0, above=None):
    """Faces of a print-orientation part that face down flatter than `limit`
    degrees from vertical and are not on the bed: (deg from vertical, area, point).
    The bed chamfer (under `above`) is left out: 0.6 mm of it faces the bed under the leaning front."""
    lim = -math.cos(math.radians(limit)) - 1e-3
    out = []
    for f in part.faces():
        if above is not None and f.bounding_box().max.Z < above:
            continue
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


def steepest_down(part, above=0.05):
    """flattest downward-facing angle (deg from vertical) on any face reaching above `above`"""
    worst = 1.0
    for f in part.faces():
        if f.bounding_box().max.Z < above:
            continue
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
    above = BN["bed_chamfer"] + 0.01
    bad = bad_faces(p, above=above)
    bb = p.bounding_box()
    log(f"{stem}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, faces {len(p.faces())}, "
        f"flattest face pointing down {steepest_down(p, above):.1f} deg from vertical (above the {BN['bed_chamfer']} bed chamfer), "
        f"overhangs flatter than 45 deg: {len(bad)}")
    for b in sorted(bad, key=lambda t: -t[1])[:10]:
        log(f"    {b[0]:.1f} deg from vertical, area {b[1]} mm2, at ({b[2].X:.1f}, {b[2].Y:.1f}, {b[2].Z:.1f})")


def plate(items, path):
    """parts side by side on one plate, far enough apart to print by object, centred on the
    plate: a Bambu Studio project with the template's settings, print.project on top and
    each part's own print.<kind> (items are (label, part, kind)), as the tool bins"""
    gap = bambu_object_gap(TEMPLATE)
    items = sorted(items, key=lambda it: it[1].bounding_box().size.Z)
    widths = [p.bounding_box().size.X for _, p, _ in items]
    x = -(sum(widths) + gap * (len(items) - 1)) / 2
    objs = []
    for (label, p, kind), wd in zip(items, widths):
        objs.append((label, Pos(x + wd / 2, 0, 0) * p, P["print"].get(kind) or {}))
        x += wd + gap
    write_bambu_project([(NAME, objs)], path, template=TEMPLATE, settings=P["print"]["project"])
    return sum(widths) + gap * (len(items) - 1)


# ---------------------------------------------------------------- build
if __name__ == "__main__":
    for sub in ("step", "print", "test-prints"):
        (HERE / sub).mkdir(exist_ok=True)
    body = bin_body()
    log(f"{NAME}: {W:.1f} wide, {H:.1f} tall at the back, nose {D:g} out at z {ZN:.1f} (rounded R{RN:g}), "
        f"foot {YFOOT:.1f} deep; front leans {BN['front_lean']:g} deg, rim falls {BN['rim_slope']:g} deg from a "
        f"{TOPF:g} flat top; back wall {B:.3f} thick; pockets at x {[round(x, 2) for x in hook_cols]}, hook bottoms z "
        f"{[round(z, 2) for z in hook_rows]}, seat z {seat_z:.2f}, gable eaves z {eaves:.2f}")
    bb = body.bounding_box()
    tol = tolerance(body)
    assert tol < 1e-3, f"bin: edge tolerance {tol:.4f} (SolidCraft opens it as an open body)"
    log(f"bin: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {body.volume:.1f} mm3, "
        f"{len(body.faces())} faces, solids {len(body.solids())}, valid {body.is_valid}, max edge tolerance {tol:.1e}")
    export_step(body, HERE / "step" / f"{NAME}_bin.step")

    # Measured on the solid, not read from the code.
    roof = [f for f in body.faces() if f.center().Y < yf + 0.5 and abs(f.normal_at(f.center()).Z + math.sqrt(0.5)) < 1e-3
            and abs(f.normal_at(f.center()).X) > 0.5]
    zs = [v.Z for f in roof for v in f.vertices()]
    log(f"measured: {len(roof)} gable faces in the pockets (expect {2 * len(hook_cols)}), z {min(zs):.3f} to {max(zs):.3f} "
        f"(eaves {eaves:.3f}, the hook's top corners at {seat_z:.3f})")
    ramp = [f for f in body.faces() if f.geom_type == GeomType.PLANE and f.center().Y > B + 1
            and abs(f.normal_at(f.center()).Y + math.cos(LEAN)) < 1e-3 and abs(f.normal_at(f.center()).Z - math.sin(LEAN)) < 1e-3]
    rz = [v.Z for f in ramp for v in f.vertices()]
    log(f"measured: inside of the front (the ramp the tools lie on): {len(ramp)} face, z {min(rz):.1f} to {max(rz):.1f}, "
        f"{(max(rz) - min(rz)) / math.cos(LEAN):.1f} long up the lean, {W - 2 * T:.1f} wide between the walls")
    hks = hooks()
    interf = sum(overlap(body, k) for k in hks)
    log(f"hooks vs bin: {interf:.3f} mm3 over {len(hks)} Bridge hook 1Us ({len(hook_cols)} columns x {ROWS} rows; ridges "
        f"{pk['ridge']['height']:.2f} tall, room for {dv['notch']['depth'] + pk['side_clearance']:.2f} in a seated hook's notch: "
        f"overlap only if taller)")
    export_step(Compound(children=[body, *hks], label=NAME), HERE / "step" / f"{NAME}_assembly.step")

    # Print orientation: the bin as it hangs, front toward the plate's front, so
    # Bambu Studio's seam at "back" lands on the back wall (as the tool bins).
    pb = to_bed(Rot(0, 0, 180) * body)
    com = pb.center(CenterOf.MASS)
    pbb = pb.bounding_box()
    foot = [v.Y for f in pb.faces() if f.bounding_box().max.Z < 1e-3 for v in f.vertices()]
    log(f"on the bed: centre of mass y {com.Y:.1f}, z {com.Z:.1f}; foot from y {min(foot):.1f} to {max(foot):.1f} "
        f"(the bin runs {pbb.min.Y:.1f} to {pbb.max.Y:.1f}): the centre of mass is "
        + ("over the foot" if min(foot) <= com.Y <= max(foot) else "OUTSIDE the foot"))
    write_print(f"{NAME}_bin_print", pb, HERE / "print")
    wd = plate([("bin", pb, "bin")], HERE / "print" / f"{NAME}_all_parts.3mf")
    log(f"{NAME}_all_parts.3mf: the bin on one plate, {wd:.1f} wide")

    # Test print: the back wall round the first pocket, upright (as the tool bins).
    hc = P["coupon"]["half_width"]
    cp = to_bed(Rot(0, 0, 180) * solid(body & Pos(hook_cols[0], B / 2 - 0.5, H / 2) * Box(2 * hc, B + 1, H + 2)))
    write_print(f"{NAME}_pocket_coupon_print", cp, HERE / "test-prints")
    plate([("pocket coupon", cp, "bin")], HERE / "test-prints" / f"{NAME}_pocket_coupon_print.3mf")
    (HERE / "report.txt").write_text("\n".join(lines) + "\n")
