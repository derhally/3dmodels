# Omniwall holder for the Neiko 6" digital caliper (option B, hanging): a back
# plate on the same hooks as the drawers, trays and bins, with a fork in front that
# the slider head sits on, jaws up; the beam hangs down through a slot open at the
# front and the thumb wheel drops into a pocket behind the left tine (params.yaml
# says what each size is and where it came from).
# Hook pockets come from ../../hook_geometry.py and ../../panel.yaml, as the bins' do.
# Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml --with shapely python build.py
# It writes step/ (the holder, a stand-in for the caliper, and the assembly on Bridge
# hook 1Us), print/ (STEP and STL laid as on the bed, one all-parts 3MF), coupons in
# test-prints/ (git-ignored) and report.txt.
# Coordinates: x across from the left face, y out from the panel face (back face
# at y = 0), z up from the bottom, on the bed. It prints as it hangs.
import copy
import json
import math
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403
from shapely import affinity
from shapely.geometry import Polygon as SPolygon, box as sbox
from shapely.ops import unary_union

try:
    HERE = Path(__file__).resolve().parent
except NameError:                                     # run through build123d-mcp's execute_file
    HERE = Path(r"E:\source\3dmodels\omniwall\neiko\caliper-6in")
ROOT = HERE.parent.parent                             # omniwall/
P = yaml.safe_load((HERE / "params.yaml").read_text())
panel = yaml.safe_load((ROOT / "panel.yaml").read_text())
exec((ROOT / "hook_geometry.py").read_text())
exec((ROOT / "core_3mf.py").read_text())
exec((ROOT.parent / "bambu" / "bambu_project.py").read_text())
TEMPLATE = ROOT.parent / "bambu" / "project_settings.config"   # printer, filament, process as saved from Bambu Studio

_export_step = export_step

U, TL, HD, PK = P["unit"], P["tool"], P["holder"], P["pocket"]
NAME = U["file_prefix"]
OUT = json.loads((HERE / TL["outline"]).read_text())["parts"]
pitch = panel["pitch"]
hook = panel["bridge_hook"]
dm = copy.deepcopy(panel["dovetail_mount"])
dv, pk = dm["dovetail"], dm["pocket"]
pk["spine_clearance"] = PK["spine_clearance"]     # the drawer housing's print-tested pocket (coupon 3)
pk["flank_gap"] = PK["flank_gap"]
pk["ridge"]["height"] = PK["ridge_height"]
ROWS = HD["rows"]
W = HD["cells"] * pitch - HD["gap"]
H = ROWS * pitch - HD["gap"]
XC = W / 2
edge = HD["gap"] / 2
hook_z0 = (pitch - panel["slot"]["length"] / 2) - hook["bar_bottom"] - edge   # as the drawers, trays and bins
hook_rows = [hook_z0 + r * pitch for r in range(ROWS)]
hook_cols = [k * pitch - edge for k in range(1, HD["cells"])]
HH = hook["height"]
seat_z = hook_rows[-1] + HH + pk["top_clearance"]
cx = dv["block_width"] / 2
hh = dv["head_width"] / 2 + pk["side_clearance"]
yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]
yb = dv["block_depth"] + pk["spine_clearance"]
B = yf + hh + HD["back_front_wall"]                   # back plate thickness, as the trays and bins
w_hook = max(dv["head_width"], dv["block_width"]) / 2
w_pocket = w_hook + pk["side_clearance"]

SEAT = HD["seat"]                                     # fork top: the head's bottom end
YH = B + TL["head_front"] - TL["back"]                # display face
YL = YH + HD["head_clearance"]                        # lip's inner face
YT = YL + HD["lip_thickness"]                         # fork front

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


# ---------------------------------------------------------------- the caliper, front view (x, z)
X_SHIFT = 0.0                                         # set below so the fork is centred on the plate


def to_front(px, py):
    """STEP (x, y) -> holder front view (x, z): jaws up, display out, so the outside jaws point
    left seen from the front (to +x: looking at the front, +x runs to the left); the head's
    bottom end on the fork"""
    return XC + X_SHIFT - (py - sum(TL["head"]) / 2), SEAT + (TL["head_end"] - px)


def front_poly(outline):
    return SPolygon([to_front(*p) for p in outline]).buffer(0)


def sweep_up(poly, h):
    """poly swept straight up by h: the room a part needs to drop in from above"""
    parts = [poly, affinity.translate(poly, 0, h)]
    for g in (poly.geoms if hasattr(poly, "geoms") else [poly]):
        c = list(g.exterior.coords)
        for a, b in zip(c, c[1:]):
            q = SPolygon([a, b, (b[0], b[1] + h), (a[0], a[1] + h)])
            if q.area > 1e-9:
                parts.append(q)
    return unary_union(parts)


PART = {p["name"]: p for p in OUT}
PARTS = {}                                            # the stand-in's solids by name (caliper())


def wire_xz(coords, y):
    pts = [Vector(x, y, z) for x, z in coords[:-1]]
    return Wire.make_polygon(pts, close=True)


def prism_xz(poly, y0, y1):
    """front-view shapely polygon extruded from y0 to y1"""
    return extrude(Face(wire_xz(list(poly.exterior.coords), y0)), y1 - y0, dir=(0, 1, 0))
# ---------------------------------------------------------------- 2D profiles (as the trays and bins)
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
XZ = lambda y: (lambda u, v: (u, y, v))      # front profile at y: (x, z)


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


# ---------------------------------------------------------------- the holder
def pocket(xc):
    """Pocket channel for one hook column, as the bins': the shared dovetail pocket
    from hook_geometry (open at the bottom, snap ridges under the seat), a ridge pair
    one pitch lower for every further row, and a 45 deg gable top through the hook's
    top corners at the seat height, so it prints upright without a flat bridge."""
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
    e = 0.0     # the bins' 0.02 lip left 4 unshared edges per pocket (validate fails); flush closes it
    roof = extrude(face([(cx - w_pocket - e, ze - e, 0), (cx + w_pocket + e, ze - e, 0),
                         (cx, ze + w_pocket, 0)], XZ(-1)), yf + 1, dir=(0, 1, 0))
    n = pk.get("tooth_notch", 0.0)    # the spine channel on up over the seat for Slot hook 1U's tooth, with its own gable
    if n:
        roof = roof + Pos(cx, (yb - 1) / 2, (ze + zt + n) / 2) * Box(2 * w_pocket, yb + 1, zt + n - ze) + notch_gable(dm, HH, 0.0)
    return Pos(xc - cx, 0, seat_z - HH) * solid(v + roof)




def plate():
    """Back plate seen from the front, B thick, its top corners and front edges rounded."""
    tr = HD["top_round"]
    p = extrude(face([(0, 0, 0), (W, 0, 0), (W, H, tr), (0, H, tr)], XZ(0)), B, dir=(0, 1, 0))
    front = [e for e in p.edges() if e.bounding_box().min.Y > B - 1e-3 and e.bounding_box().max.Z > 1e-3]
    return check("plate edges", p, solid(p.fillet(HD["edge_round"], front)))


def fork_x():
    """the fork's sides: past the wheel pocket on one side and the head on the other, each with a side wall"""
    wheel = front_poly(PART["wheel"]["outline"]).buffer(HD["wheel_clearance"])
    xs = [wheel.bounds[0], wheel.bounds[2]] + [to_front(TL["head_end"], y)[0] for y in TL["head"]]
    return min(xs) - HD["side_wall"], max(xs) + HD["side_wall"]


_f = fork_x()
X_SHIFT = XC - (_f[0] + _f[1]) / 2                    # the fork centred on the plate (the wheel sits off to the left)
FX0, FX1 = fork_x()
_bx = sorted(to_front(0, y)[0] for y in TL["beam"])
BX0, BX1 = _bx[0] - HD["beam_clearance"], _bx[1] + HD["beam_clearance"]
WHEEL = sweep_up(front_poly(PART["wheel"]["outline"]).buffer(HD["wheel_clearance"]), 40)
YW = B + PART["wheel"]["z"][1] - TL["back"] + HD["wheel_clearance"]   # wheel pocket's front wall
ZW = WHEEL.bounds[1]                                  # wheel pocket's floor


def fork():
    """Block in front of the plate from the bed to the seat, with the lip along its front;
    seen from above its front corners are round, its front edges rounded. The slot and the
    wheel pocket are cut later."""
    fr, lr = HD["fork_round"], HD["lip_round"]
    top = face([(FX0, B - 0.5, 0), (FX1, B - 0.5, 0), (FX1, YT, fr), (FX0, YT, fr)], lambda u, v: (u, v, 0))
    f = extrude(top, SEAT)
    keep = [e for e in f.edges() if e.bounding_box().min.Y > B + 1e-3 and e.bounding_box().min.Z > SEAT - 1e-3]
    f = check("fork edges", f, solid(f.fillet(HD["edge_round"], keep)))
    lip = extrude(face([(YL, SEAT - 1, 0), (YT, SEAT - 1, 0), (YT, SEAT + HD["lip_height"], lr),
                        (YL, SEAT + HD["lip_height"], lr)], YZ(FX0 - 1)), FX1 - FX0 + 2, dir=(1, 0, 0))
    lip = solid(lip & extrude(top, SEAT + HD["lip_height"] + 2))     # trimmed to the fork's rounded outline
    return solid((f + lip).clean())


def holder():
    body = solid((plate() + fork()).clean())
    bed = [e for e in body.edges() if e.bounding_box().max.Z < 1e-3]
    body = check("bed chamfer", body, solid(body.chamfer(HD["bed_chamfer"], None, bed)))
    slot = Pos((BX0 + BX1) / 2, (B + YT + 2) / 2, SEAT / 2) * Box(BX1 - BX0, YT + 2 - B, SEAT + 2 * HD["lip_height"] + 4)
    body = check("beam slot", body, solid(body - slot))
    body = check("wheel pocket", body, solid(body - prism_xz(WHEEL, B, YW)))
    for xc in hook_cols:
        body = check("pocket", body, solid(body - pocket(xc)))
    body.label = "holder"
    return body


# ---------------------------------------------------------------- stand-in for the caliper (checks and the assembly)
def caliper():
    """The caliper from Zeid's STEP, part by part: each front silhouette extruded over
    its thickness, hanging jaws up with the head's bottom end on the seat and its back
    on the plate (PARTS gets each part by name)."""
    parts = []
    for p in OUT:
        z0, z1 = p["z"]
        parts.append(prism_xz(front_poly(p["outline"]), B + z0 - TL["back"], B + z1 - TL["back"]))
        parts[-1].label = p["name"]
        PARTS[p["name"]] = parts[-1]
    t = Compound(children=parts)
    t.label = "caliper"
    return t


if __name__ != "__main__" or Path(sys.argv[0]).name != "build.py":    # build123d-mcp: show the holder
    result = holder()
# ---------------------------------------------------------------- checks (as the trays and bins)
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
    s = Rot(0, 0, 180) * s     # front toward the plate's front: Bambu Studio's seam at "back" is the plate's back, so it lands on the back plate
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


def write_print(stem, p, folder):
    export_step(p, folder / f"{stem}.step")
    export_stl(p, str(folder / f"{stem}.stl"))
    bad = bad_faces(p)
    bb = p.bounding_box()
    log(f"{stem}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, faces {len(p.faces())}, "
        f"overhangs flatter than 45 deg: {len(bad)}")
    for b in sorted(bad, key=lambda t: -t[1])[:10]:
        log(f"    {b[0]:.1f} deg from vertical, area {b[1]} mm2, at ({b[2].X:.1f}, {b[2].Y:.1f}, {b[2].Z:.1f})")


def plate_3mf(items, path):
    """parts side by side on one plate, far enough apart to print by object (bambu_object_gap): a Bambu Studio project with the
    template's settings, print.project on top and each part's own print.<kind>"""
    gap = bambu_object_gap(TEMPLATE)
    widths = [p.bounding_box().size.X for _, p, _ in items]
    x = -(sum(widths) + gap * (len(items) - 1)) / 2
    objs = []
    for (label, p, kind), wd in zip(items, widths):
        objs.append((label, Pos(x + wd / 2, 0, 0) * p, P["print"].get(kind) or {}))
        x += wd + gap
    write_bambu_project([(NAME, objs)], path, template=TEMPLATE, settings=P["print"]["project"])


# ---------------------------------------------------------------- build
if __name__ == "__main__" and Path(sys.argv[0]).name == "build.py":
    for sub in ("step", "print", "test-prints"):
        (HERE / sub).mkdir(exist_ok=True)
    body = holder()
    tool = caliper()
    bb = body.bounding_box()
    tol = tolerance(body)
    assert tol < 1e-3, f"holder: edge tolerance {tol:.4f} (SolidCraft opens it as an open body)"
    log(f"{NAME}: {W:.1f} wide x {H:.1f} tall plate ({HD['cells']} cells x {ROWS} rows), {B:.3f} thick; fork x {FX0:.2f} to {FX1:.2f}, "
        f"out to y {YT:.3f}, seat z {SEAT:.2f}, lip to z {SEAT + HD['lip_height']:.2f}; overall {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}, "
        f"volume {body.volume:.1f} mm3, {len(body.faces())} faces, valid {body.is_valid}, max edge tolerance {tol:.1e}")
    log(f"pockets at x {[round(x, 2) for x in hook_cols]}, hook bottoms z {[round(z, 2) for z in hook_rows]}, seat z {seat_z:.2f}; "
        f"beam slot x {BX0:.2f} to {BX1:.2f}, wheel pocket x {WHEEL.bounds[0]:.2f} to {WHEEL.bounds[2]:.2f}, back to y {YW:.3f}, floor z {ZW:.2f}")

    # Measured on the solids, not read from the code.
    tb = tool.bounding_box()
    log(f"caliper stand-in: {tb.size.X:.1f} x {tb.size.Y:.1f} x {tb.size.Z:.1f}, from z {tb.min.Z:.2f} to {tb.max.Z:.2f}, back on y {tb.min.Y:.3f}")
    log(f"caliper vs holder: overlap {overlap(body, tool):.4f} mm3; lifted 0.05: clearance {body.distance_to(Pos(0, 0, 0.05) * tool):.3f} "
        f"(back on the plate face)")
    hd, bm, wh = (PARTS[n] for n in ("head", "beam", "wheel"))
    front = body & Pos(XC, YL + 25, 0) * Box(200, 50, 200)
    log(f"head to the lip: {front.distance_to(hd):.3f}; beam to the slot: {(body & Pos(XC, B + 50 + 0.01, SEAT / 2) * Box(200, 100, SEAT - 0.2)).distance_to(bm):.3f}; "
        f"wheel to its pocket: {(body & Pos(XC, B + 50 + 0.01, 0) * Box(200, 100, 2 * SEAT - 0.02)).distance_to(wh):.3f}")
    for x in (FX0 + 2, BX0 - 2, BX1 + 2, FX1 - 2):   # seat height under the head, measured on the solid
        hit = body & Pos(x, YH - 2, SEAT) * Box(0.01, 0.01, 2 * SEAT)
        log(f"    seat at x {x:.1f}, y {YH - 2:.2f}: z {hit.bounding_box().max.Z:.2f}" if hit is not None and hit.solids() else f"    x {x:.1f}: nothing")
    def blocked(lift):                                # anything in the way pulling it straight forward at this lift
        return any(overlap(body, Pos(0, d / 2, lift) * tool) > 1e-6 for d in range(1, 41))
    lift = 0.0                                        # how far to lift it before it comes forward: the wheel over the tine, the head over the lip
    while blocked(lift) and lift < 40:
        lift += 0.5
    log(f"to take it out: lift {lift:.1f}, then pull straight forward")
    hks = hooks()
    log(f"hooks vs holder: {sum(overlap(body, k) for k in hks):.3f} mm3 over {len(hks)} Bridge hook 1Us (ridges "
        f"{pk['ridge']['height']:.2f} tall, room for {dv['notch']['depth'] + pk['side_clearance']:.2f} in a seated hook's notch: "
        f"overlap only if taller)")
    log(f"hooks vs caliper: {sum(overlap(tool, k) for k in hks):.3f} mm3")
    export_step(body, HERE / "step" / f"{NAME}.step")
    export_step(tool, HERE / "step" / f"{NAME}_caliper_standin.step")
    export_step(Compound(children=[body, *tool.solids(), *hks], label=NAME), HERE / "step" / f"{NAME}_assembly.step")

    # Print orientation: as it hangs, on the plate's and the fork's bottom.
    pb = to_bed(body)
    write_print(f"{NAME}_print", pb, HERE / "print")
    plate_3mf([("holder", pb, "holder")], HERE / "print" / f"{NAME}_all_parts.3mf")
    log(f"{NAME}_all_parts.3mf: the holder, upright")

    # Test print: the back plate round the first pocket.
    hc = P["coupon"]["half_width"]
    cp = to_bed(solid(body & Pos(hook_cols[0], B / 2 - 0.5, H / 2) * Box(2 * hc, B + 1, H + 2)))
    write_print(f"{NAME}_pocket_coupon_print", cp, HERE / "test-prints")
    plate_3mf([("pocket coupon", cp, "holder")], HERE / "test-prints" / f"{NAME}_pocket_coupon_print.3mf")
    # Test print: the fork with a strip of plate behind it, to hang the caliper in and check the fit.
    ft = P["coupon"]["fork_top"]
    fc = to_bed(solid(body & Pos(XC, B, ft / 2) * Box(W + 2, 2 * B + 60, ft)))
    write_print(f"{NAME}_fork_coupon_print", fc, HERE / "test-prints")
    plate_3mf([("fork coupon", fc, "holder")], HERE / "test-prints" / f"{NAME}_fork_coupon_print.3mf")
    (HERE / "report.txt").write_text("\n".join(lines) + "\n")
