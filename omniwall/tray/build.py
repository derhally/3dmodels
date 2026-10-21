# Omniwall wall trays: low trays that hang on the same hooks as the arc drawers,
# by dovetail pockets in their back wall (params.yaml says what each style is).
# Hook pockets come from ../hook_geometry.py and ../panel.yaml, as the drawer
# housing's do. Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py <tray folder>
# params.yaml here holds the shared defaults; each tray is a folder (such as
# ramp-6x1) whose params.yaml overrides them section by section, key by key.
# It writes the tray folder's step/ (the parts and the assembly on Bridge hook 1Us),
# print/ (STEP and STL per part laid as on the bed, one all-parts 3MF), a pocket
# test print in test-prints/ (git-ignored) and report.txt.
# Coordinates: x across from the left face, y out from the panel face (back face
# at y = 0), z up from the tray's bottom edge. Trays print as they hang.
import copy
import math
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
if len(sys.argv) < 2:
    sys.exit("usage: build.py <tray folder>, one of: " + ", ".join(sorted(p.parent.name for p in SRC.glob("*/params.yaml"))))
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

U, TR, PK = P["unit"], P["tray"], P["pocket"]
NAME = U["file_prefix"]
pitch = panel["pitch"]
hook = panel["bridge_hook"]
dm = copy.deepcopy(panel["dovetail_mount"])
dv, pk = dm["dovetail"], dm["pocket"]
pk["spine_clearance"] = PK["spine_clearance"]     # the drawer housing's print-tested pocket (coupon 3)
pk["flank_gap"] = PK["flank_gap"]
pk["ridge"]["height"] = PK["ridge_height"]
W = TR["cells"] * pitch - TR["gap"]
H = TR["rows"] * pitch - TR["gap"]
D = TR["depth"]
T = TR["wall"]
edge = TR["gap"] / 2
hook_z0 = (pitch - panel["slot"]["length"] / 2) - hook["bar_bottom"] - edge   # as the arc drawer
hook_cols = [k * pitch - edge for k in range(1, TR["cells"])]
HH = hook["height"]
seat_z = hook_z0 + (TR["rows"] - 1) * pitch + HH + pk["top_clearance"]
cx = dv["block_width"] / 2
hh = dv["head_width"] / 2 + pk["side_clearance"]
yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]
B = yf + hh + TR["back_front_wall"]                  # back wall thickness, as the housing's back plate
TOP = H + 1                                           # cavities run up past the back wall
w_hook = max(dv["head_width"], dv["block_width"]) / 2               # hook front's half width
w_pocket = w_hook + pk["side_clearance"]                            # pocket's half width
eaves = seat_z - (w_pocket - w_hook)                                # gable meets the pocket walls here

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


# ---------------------------------------------------------------- 2D profiles
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


# ---------------------------------------------------------------- shared shell
def pocket(xc):
    """Pocket channel for one hook column: the shared dovetail pocket from
    hook_geometry, open at the bottom, with snap ridges. Its top is a 45 deg
    gable along the pocket through the hook's top corners at the seat height,
    so it prints upright without a flat bridge and the tray hangs where a flat
    seat would put it."""
    zl = -(seat_z - HH) - 1
    zt = HH + pk["top_clearance"]
    ze = zt - (w_pocket - w_hook)
    v = pocket_void(dm, HH, 0.0, zl)
    v = solid(v & Pos(cx, yf / 2, (zl - 1 + ze) / 2) * Box(20, yf + 10, ze - zl + 1))
    e = 0.02    # gable starts a hair wider and lower than the walls, so no flat strip is left
    roof = extrude(face([(cx - w_pocket - e, ze - e, 0), (cx + w_pocket + e, ze - e, 0),
                         (cx, ze + w_pocket, 0)], XZ(-1)), yf + 1, dir=(0, 1, 0))
    return Pos(xc - cx, 0, seat_z - HH) * solid(v + roof)


def shell(lip):
    """Solid outer body: plan with rounded front corners, back wall H tall, side
    walls falling to lip height in one S, outside bottom edges a 45 deg chamfer
    rolling into a radius. Pockets cut. Cavities are cut by each style."""
    rf = TR["plan_front_radius"]
    plan = extrude(face([(0, 0, 0), (W, 0, 0), (W, D, rf), (0, D, rf)], XY(0)), H)
    a, b = (TR["side_s_start"], lip), (TR["side_s_end"], H)
    th = math.atan2(H - lip, a[0] - b[0])
    t = min(0.47 * math.dist(a, b), 12.0)              # tangent length: two arcs, a short straight between
    R = t / math.tan(th / 2)
    side = extrude(face([(0, 0, 0), (D, 0, 0), (D, lip, 0), (a[0], a[1], R), (b[0], b[1], R), (0, H, 0)], YZ(0)),
                   W, dir=(1, 0, 0))
    body = solid(plan & side)
    bot = [e for e in body.edges() if e.center().Z < 1e-3 and e.center().Y > 0.5]
    body = check("bed chamfer", body, solid(body.chamfer(TR["bed_chamfer"], None, bot)))
    back = [e for e in body.edges() if e.center().Z < 1e-3 and e.center().Y < 0.5]
    body = solid(body.chamfer(TR["back_bed_chamfer"], None, back))
    c = TR["bed_chamfer"]
    roll = [e for e in body.edges() if abs(e.center().Z - c) < 1e-3 and e.center().Y > 0.5
            and min(e.center().X, W - e.center().X, D - e.center().Y) < c + 0.01]
    body = check("bed round", body, solid(body.fillet(TR["bed_round"], roll)))
    for xc in hook_cols:
        body = check("pocket", body, solid(body - pocket(xc)))
    return body


def round_tops(body, r, zmin):
    """Round the top edges of the walls: every edge of an upward face at or above
    zmin, except edges two such faces share (tangent seams) and the panel side."""
    tops = [f for f in body.faces() if f.center().Z > zmin - 1e-3 and f.normal_at(f.center()).Z > 0.3
            and not (f.center().Y < yf + 1 and f.center().Z < seat_z + 0.01)]   # not the pockets' ridges
    count = {}
    for f in tops:
        for e in f.edges():
            count.setdefault(e, 0)
            count[e] += 1
    edges = [e for e, n in count.items() if n == 1 and e.bounding_box().max.Y > 0.05]
    return check("round tops", body, solid(body.fillet(r, edges)))


def prism_cavity(x0, x1, y0, y1, rb, rf, z0, cove):
    """Rounded-rect cavity from z0 up, its bottom edges coved"""
    box = extrude(face([(x0, y0, rb), (x1, y0, rb), (x1, y1, rf), (x0, y1, rf)], XY(z0)), TOP - z0)
    bot = [e for e in box.edges() if e.center().Z < z0 + 1e-3]
    return solid(box.fillet(cove, bot)) if cove else box


def profile_cavity(pts, side_cove):
    """Side profile (y, z) extruded between the side walls, its edges against
    the side walls coved (the vertical edge at the back included)"""
    cav = extrude(face(pts, YZ(T)), W - 2 * T, dir=(1, 0, 0))
    sides = [f for f in cav.faces() if abs(abs(f.normal_at(f.center()).X) - 1) < 1e-6]
    edges = [e for f in sides for e in f.edges()
             if e.bounding_box().min.Z < TOP - 0.5 and not (e.bounding_box().min.Y > D - T - 0.01)]
    return solid(cav.fillet(side_cove, edges))


# ---------------------------------------------------------------- the styles
def cove():
    c = P["cove"]
    r = c["cove"]
    body = shell(c["lip"])
    cav = prism_cavity(T, W - T, B, D - T, r, TR["plan_front_radius"] - T, c["floor"], r)
    body = check("cove cavity", body, solid(body - cav))
    body = round_tops(body, TR["lip_round"], c["lip"])
    body.label = "tray"
    return [body]


def ramp():
    c = P["ramp"]
    pts = [(B, TOP, 0), (B, c["back_floor"], c["back_cove"]), (D - T, c["front_floor"], c["bead_round"]),
           (D - T, TOP, 0)]
    cav = profile_cavity(pts, c["side_cove"])
    # round the front corners seen from above like the other trays, then cove where they meet the floor
    rf = TR["plan_front_radius"] - T
    plan = extrude(face([(T, B - 1, 0), (W - T, B - 1, 0), (W - T, D - T, rf), (T, D - T, rf)], XY(-1)), TOP + 2)
    cut = solid(cav & plan)
    new = [e for e in cut.edges() if e.bounding_box().min.Y > D - T - rf - 0.01 and e.bounding_box().max.Z < c["lip"]
           and e.geom_type != GeomType.LINE and min(e.center().X - T, W - T - e.center().X) > 0.05
           and min(e.center().X - T, W - T - e.center().X) < rf]
    try:
        cut = solid(cut.fillet(c["side_cove"], new))
    except ValueError:
        log("ramp: the front inside corners keep a small crease where the floor meets them (the cove fillet fails there)")
    body = shell(c["lip"])
    body = check("ramp cavity", body, solid(body - cut))
    body = round_tops(body, TR["lip_round"], c["lip"])
    body.label = "tray"
    return [body]


def dish():
    c = P["dish"]
    rf = TR["plan_front_radius"] - T
    cradle = shell(c["rim"])
    cav = prism_cavity(T, W - T, B, D - T, rf, rf, c["cradle_floor"], c["cradle_cove"])
    cradle = check("cradle cavity", cradle, solid(cradle - cav))
    cradle = round_tops(cradle, TR["lip_round"], c["rim"])
    g, w = c["clearance"], c["dish_wall"]
    x0, x1, y0, y1 = T + g, W - T - g, B + g, D - T - g
    rc = rf - g
    z0, z1 = c["cradle_floor"], c["dish_lip"]
    d = extrude(face([(x0, y0, rc), (x1, y0, rc), (x1, y1, rc), (x0, y1, rc)], XY(z0)), z1 - z0)
    bot = [e for e in d.edges() if e.center().Z < z0 + 1e-3]
    d = solid(d.chamfer(c["dish_chamfer"], None, bot))
    inner = prism_cavity(x0 + w, x1 - w, y0 + w, y1 - w, rc - w, rc - w, z0 + c["dish_floor"], c["dish_cove"])
    d = check("dish cavity", d, solid(d - inner))
    pr = c["pour_radius"]
    pour = Pos(W / 2, y1 - w - 1, z1 + pr - c["pour_depth"]) * Rot(-90, 0, 0) * Cylinder(pr, w + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    d = check("pour dip", d, solid(d - pour))
    d = round_tops(d, c["dish_lip_round"], z1 - c["pour_depth"] - 0.01)
    cradle.label, d.label = "cradle", "dish"
    return [cradle, d]


# ---------------------------------------------------------------- checks
def tolerance(s):
    from OCP.BRep import BRep_Tool
    return max(BRep_Tool.Tolerance_s(e.wrapped) for e in s.edges())


def hooks():
    hk = bridge_hook(panel, ROOT)
    out = []
    for xc in hook_cols:
        h = Pos(xc - cx, -hook["panel_front_y"], hook_z0) * hk
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
                n = f.normal_at(u, w)
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
                    worst = min(worst, f.normal_at(u, w).Z)
    return 0.0 if worst >= 0 else round(90 - math.degrees(math.acos(min(1, -worst))), 1)


# ---------------------------------------------------------------- build
parts = {"cove": cove, "ramp": ramp, "dish": dish}[U["style"]]()
for sub in ("step", "print", "test-prints"):
    (HERE / sub).mkdir(exist_ok=True)
log(f"{NAME} ({U['style']}): {W:.1f} wide, {D:g} deep, back wall {H:.1f} tall and {B:.3f} thick; "
    f"pockets at x {[round(x, 2) for x in hook_cols]}, hook bottoms z {hook_z0:.2f}, seat z {seat_z:.2f}, gable eaves z {eaves:.2f}")
for s in parts:
    bb = s.bounding_box()
    tol = tolerance(s)
    assert tol < 1e-3, f"{s.label}: edge tolerance {tol:.4f} (SolidCraft opens it as an open body)"
    log(f"{s.label}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {s.volume:.1f} mm3, "
        f"{len(s.faces())} faces, solids {len(s.solids())}, valid {s.is_valid}, max edge tolerance {tol:.1e}")
    export_step(s, HERE / "step" / f"{NAME}{'' if len(parts) == 1 else '_' + s.label}.step")

# Measured on the solid, not read from the code: the pocket roofs.
body = parts[0]
roof = [f for f in body.faces() if f.center().Y < yf + 0.5 and abs(f.normal_at(f.center()).Z + math.sqrt(0.5)) < 1e-3
        and abs(f.normal_at(f.center()).X) > 0.5]
zs = [v.Z for f in roof for v in f.vertices()]
log(f"measured: {len(roof)} gable faces in the pockets (expect {2 * len(hook_cols)}), z {min(zs):.3f} to {max(zs):.3f} "
    f"(eaves {eaves:.3f}, the hook's top corners at {seat_z:.3f}, ridge {seat_z + w_hook:.3f})")

hks = hooks()
interf = sum(overlap(body, k) for k in hks)
raised = sum(overlap(body, Pos(0, 0, 0.1) * k) for k in hks)
log(f"hooks vs tray: {interf:.3f} mm3 over {len(hks)} Bridge hook 1Us (snap ridges reach "
    f"{pk['ridge']['height'] - pk['side_clearance']:.2f} into the hooks' {dv['notch']['depth']} notches: a small overlap is expected); "
    f"with the hooks 0.1 higher {raised:.3f} mm3 (more: the hooks' tops bear on the gables)")
if len(parts) == 2:
    cr, di = parts
    log(f"dish vs cradle: overlap {overlap(cr, di):.3f} mm3; dish lifted 0.05: clearance {cr.distance_to(Pos(0, 0, 0.05) * di):.3f} "
        f"(floor), side gap {P['dish']['clearance']} by construction")
export_step(Compound(children=[*parts, *hks], label=NAME), HERE / "step" / f"{NAME}_assembly.step")

# Print orientation: as it hangs, bottom edge on the bed.
printed = []
for s in parts:
    stem = f"{NAME}{'' if len(parts) == 1 else '_' + s.label}_print"
    p = to_bed(s)
    export_step(p, HERE / "print" / f"{stem}.step")
    export_stl(p, str(HERE / "print" / f"{stem}.stl"))
    bad = bad_faces(p)
    bb = p.bounding_box()
    log(f"{stem}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, faces {len(p.faces())}, "
        f"flattest face pointing down {steepest_down(p):.1f} deg from vertical, overhangs flatter than 45 deg: {len(bad)}")
    for b in sorted(bad, key=lambda t: -t[1])[:10]:
        log(f"    {b[0]:.1f} deg from vertical, area {b[1]} mm2, at ({b[2].X:.1f}, {b[2].Y:.1f}, {b[2].Z:.1f})")
    printed.append((s.label, p))
# One plate: the parts side by side, 10 mm apart, centred on the origin: a Bambu
# Studio project with the template's settings.
gap = 10.0
widths = [p.bounding_box().size.X for _, p in printed]
x = -(sum(widths) + gap * (len(printed) - 1)) / 2
objs = []
for (label, p), wd in zip(printed, widths):
    objs.append((label, Pos(x + wd / 2, 0, 0) * p))
    x += wd + gap
write_bambu_project([(NAME, objs)], HERE / "print" / f"{NAME}_all_parts.3mf", template=TEMPLATE)
log(f"{NAME}_all_parts.3mf: {', '.join(l for l, _ in printed)} on one plate, {sum(widths) + gap * (len(printed) - 1):.1f} wide")

# Pocket test print: the back wall round the first pocket, upright like the tray.
hc = P["coupon"]["half_width"]
cp = solid(body & Pos(hook_cols[0], B / 2 - 0.5, H / 2) * Box(2 * hc, B + 1, H + 2))
cpp = to_bed(cp)
export_step(cpp, HERE / "test-prints" / f"{NAME}_pocket_coupon_print.step")
export_stl(cpp, str(HERE / "test-prints" / f"{NAME}_pocket_coupon_print.stl"))
write_3mf([("pocket coupon", *shape_mesh(cpp))], HERE / "test-prints" / f"{NAME}_pocket_coupon_print.3mf")
log(f"pocket coupon (test-prints): {cpp.bounding_box().size.X:.1f} x {cpp.bounding_box().size.Y:.1f} x {cpp.bounding_box().size.Z:.1f}, "
    f"overhangs flatter than 45 deg: {len(bad_faces(cpp))}")
(HERE / "report.txt").write_text("\n".join(lines) + "\n")
result = Compound(children=[*parts, *hks])
