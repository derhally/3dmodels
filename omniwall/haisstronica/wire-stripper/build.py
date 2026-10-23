# Omniwall holder for the Haisstronica 3-in-1 wire stripper (option B, the shoulder
# fork): a back plate on the same hooks as the drawers, trays and bins, with two
# prongs that catch the bottoms of the blue grips; the black head hangs between
# them (params.yaml says what each size is and where it came from).
# Hook pockets come from ../../hook_geometry.py and ../../panel.yaml, as the bins' do.
# Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py
# It writes step/ (the holder, a stand-in for the tool, and the assembly on Bridge
# hook 1Us), print/ (STEP and STL laid as on the bed, one all-parts 3MF), a pocket
# coupon in test-prints/ (git-ignored) and report.txt.
# Coordinates: x across from the left face, y out from the panel face (back face
# at y = 0), z up from the plate's bottom edge; the legs hang below it to the bed.
# It prints as it hangs, on the legs' feet.
import copy
import json
import math
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

try:
    HERE = Path(__file__).resolve().parent
except NameError:                                     # run through build123d-mcp's execute_file
    HERE = Path(r"E:\source\3dmodels\omniwall\haisstronica\wire-stripper")
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
XC = W / 2                                            # tool axis
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
eaves = seat_z - (w_pocket - w_hook)

SEAT = HD["seat"]                                     # where the grip bottoms' low inner corners (G) rest
XP = XC - TL["head_width"] / 2                        # left seat's pivot: G, at the head's side
ANG = math.degrees(math.atan2(TL["j_to_c"] - TL["j_to_g"], (TL["root_width"] - TL["head_width"]) / 2))
TAN = math.tan(math.radians(ANG))                     # seats rise outward from G at the grip bottoms' slope, G to C
GAP = TL["head_width"] + 2 * HD["head_clearance"]     # between the prongs
L1 = XC - GAP / 2                                     # leg width: left face to the inner face of the left prong
YL = B + TL["grip_thickness"] + HD["grip_clearance"]  # lip's inner face
Y_TIP = YL + HD["lip_thickness"]                      # prong front
ZT = SEAT - HD["prong_tip"]                           # prong front's bottom
ZB = ZT - (Y_TIP - B)                                 # bed: the 45 deg underside reaches the plate face here
ZA = HD["gable_apex"]
LI = XC - HD["legs_inner"]                            # left leg's inner face (the plate's, behind the head)
ZK = ZA - HD["legs_inner"]                            # gable meets the legs' inner faces
J = SEAT - TL["j_to_g"]                               # tool's jaw end
BUMP = (SEAT - TL["j_to_g"] + TL["bump"]["from_j"], SEAT - TL["j_to_g"] + TL["bump"]["from_j"] + TL["bump"]["length"])

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
    return Pos(xc - cx, 0, seat_z - HH) * solid(v + roof)


def lip_lead_in(xc):
    """The pockets open on the gable's 45 deg slope, so on the uphill side (towards
    the tool axis) the gable's lowest edge runs along the pocket wall from the back
    face to the pocket floor over the open slot, held only at the floor end, and the
    neck lip there hangs from it: Bambu calls that floating. Cut the plate beside the
    wall and the lip to climb at 45 deg from the floor end towards the back face, so
    each layer rests on the one below."""
    hn = dv["neck_width"] / 2 + pk["side_clearance"]
    s = 1 if xc < XC else -1                          # uphill: towards the tool axis
    xh, xn = xc + s * hh, xc + s * hn
    zg = ZK + (min(xh, W - xh) - LI)                  # the gable's straight part at the pocket's side
    assert min(xh, W - xh) > LI + HD["notch_round"] * math.tan(math.radians(22.5)) / math.sqrt(2)
    o = (xh, yf, zg)                                  # the edge's foot, at the pocket floor
    a = Pos((xh + XC) / 2, (yf - 1) / 2, 0) * Box(abs(XC - xh), yf + 1, 60)        # the plate uphill of the wall
    a = a.split(Plane(origin=o, z_dir=(0, -1, -1)), keep=Keep.TOP)
    b = Pos((xn + xh) / 2, (yf - 1) / 2, 0) * Box(abs(xh - xn) + 0.01, yf + 1, 60)  # the lip
    b = b.split(Plane(origin=o, z_dir=(s, -1, -1)), keep=Keep.TOP)
    return a + b


def ridge_coupons():
    """Upright pocket coupons, one per height in coupon.ridge_heights: the back plate
    round a top-row pocket, from below its hook to the top, so the hook slides in
    from the bottom, passes the snap ridge pair and clicks in as on the holder; the
    ridge height (hundredths of a mm) is engraved in the top face, reading from the front."""
    hc, keep, out = P["coupon"]["half_width"], pk["ridge"]["height"], []
    z0 = hook_rows[-1] - P["coupon"]["below_hook"]
    xc = hook_cols[0]
    try:
        for h in P["coupon"]["ridge_heights"]:
            pk["ridge"]["height"] = h
            c = solid(Pos(xc, B / 2, (z0 + H) / 2) * Box(2 * hc, B, H - z0) - pocket(xc))
            pl = Plane(origin=(xc, B / 2, H), x_dir=(-1, 0, 0), z_dir=(0, 0, 1))       # top face, reads from the front
            c = check(f"ridge {h} label", c, solid(c - extrude(pl * Text(f"{round(h * 100)}", font_size=5), amount=-0.4)))
            c.label = f"ridge {h}"
            out.append((h, c))
    finally:
        pk["ridge"]["height"] = keep
    return out


def plate():
    """Back plate and legs seen from the front, B thick, front edges rounded: rounded
    top corners; between the legs the bottom is a 45 deg gable that clears the tool's
    back bump and rises to the apex, with the legs' inner faces (behind the head,
    clear of the bump) turning into it on a round."""
    nr = HD["notch_round"]
    pts = [(0, ZB, 0), (LI, ZB, 0), (LI, ZK, nr), (XC, ZA, 0), (W - LI, ZK, nr), (W - LI, ZB, 0),
           (W, ZB, 0), (W, H, HD["top_round"]), (0, H, HD["top_round"])]
    p = extrude(face(pts, XZ(0)), B, dir=(0, 1, 0))
    front = [e for e in p.edges() if e.bounding_box().min.Y > B - 1e-3 and e.bounding_box().max.Z > ZB + 1e-3]
    return check("plate edges", p, solid(p.fillet(HD["edge_round"], front)))


def prong(x0, x1):
    """The left prong on the front of the left leg, from x0 to x1: a lip at the front,
    the underside 45 deg up to the prong's front, all tilted about G at the head's side
    so the seat rises outward at the grip bottoms' slope; its side edges rounded
    (it is rounded on its own and then joined to the plate, flat on the plate face:
    rounding them on the joined body left edges SolidCraft and meshers reject)."""
    lr = HD["lip_round"]
    pts = [(B, ZB, 0), (Y_TIP, ZT, HD["tip_round"]), (Y_TIP, SEAT + HD["lip_height"], lr),
           (YL, SEAT + HD["lip_height"], lr), (YL, SEAT, 0.8), (B, SEAT, 0)]
    p = extrude(face(pts, YZ(x0 - 20)), x1 - x0 + 40, dir=(1, 0, 0))
    p = Pos(XP, 0, SEAT) * Rot(0, ANG, 0) * Pos(-XP, 0, -SEAT) * p     # outer end up
    p = solid(p & Pos((x0 + x1) / 2, (B + Y_TIP) / 2 + 5, (ZB + H) / 2) * Box(x1 - x0, Y_TIP - B + 10, H - ZB))   # bed to top
    sides = [e for e in p.edges() if abs(e.bounding_box().max.X - e.bounding_box().min.X) < 1e-3
             and (e.bounding_box().min.Y > B + 1e-3 or (e.bounding_box().max.Y > B + 1e-3 and e.bounding_box().max.Z > ZB + 1e-3))]
    return check("prong edges", p, solid(p.fillet(HD["edge_round"], sides)))


def holder():
    ins = HD["prong_inset"]
    left = prong(ins, L1)
    right = mirror(left, about=Plane.YZ.offset(XC))
    body = solid((plate() + left + right).clean())
    bed = [e for e in body.edges() if e.bounding_box().max.Z < ZB + 1e-3
           and e.bounding_box().max.Y < B + 1e-3
           and not (abs(e.bounding_box().min.Y - B) < 1e-3 and abs(e.bounding_box().max.Y - B) < 1e-3)]   # the plate's only: not the prongs' feet
    body = check("bed chamfer", body, solid(body.chamfer(HD["bed_chamfer"], None, bed)))
    for xc in hook_cols:
        body = check("pocket", body, solid(body - pocket(xc)))
        body = check("lip lead-in", body, solid(body - lip_lead_in(xc)))
    body.label = "holder"
    return body


# ---------------------------------------------------------------- stand-in for the stripper (checks and the assembly)
def stripper():
    """The tool as measured, hanging with its grip bottoms (G) on the seat and its back
    on the plate face: the grips and the head above G from the traced outline, 16
    thick; the black head below G 21 thick (side photo) with the clear stop and knob
    on its front out to the 30.4 thickness; the bump on its back."""
    o = json.loads((HERE / "tool_outline.json").read_text())
    pts = [(XC + x, SEAT + z - o["z_g"]) for x, z in o["points"]]
    plan = Face(Wire.make_polygon([Vector(x, B, z) for x, z in pts], close=True))
    top = extrude(plan, TL["grip_thickness"], dir=(0, 1, 0))
    top = solid(top & Pos(XC, B + 50, SEAT + 150) * Box(200, 100, 300))     # G and up
    cut = Pos(XP, 0, SEAT) * Rot(0, ANG, 0) * Pos(-100, B + 50, -100) * Box(200, 100, 200)
    cut = cut + mirror(cut, about=Plane.YZ.offset(XC))
    top = solid(top - cut)                                                     # grip bottoms at the seats' slope
    hw = TL["head_width"] / 2
    head = Pos(XC, B + 10.5, (J + SEAT) / 2 + 1) * Box(2 * hw, 21, SEAT - J + 2)
    gadgets = Pos(XC - 5, B + 21 + (TL["thickness"] - TL["bump"]["height"] - 21) / 2, J + 17) * \
        Box(38, TL["thickness"] - TL["bump"]["height"] - 21 + 0.2, 30)          # clear stop and knob (side photo)
    bp = TL["bump"]
    bump = Pos(XC, B - bp["height"] / 2 + 0.1, (BUMP[0] + BUMP[1]) / 2) * Box(bp["width"], bp["height"] + 0.2, bp["length"])
    t = solid((top + head + gadgets + bump).clean())
    t.label = "stripper"
    return t, head, bump


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
    tool, head, bump = stripper()
    bb = body.bounding_box()
    tol = tolerance(body)
    assert tol < 1e-3, f"holder: edge tolerance {tol:.4f} (SolidCraft opens it as an open body)"
    log(f"{NAME}: {W:.1f} wide x {H:.1f} tall plate ({HD['cells']} cells x {ROWS} rows), {B:.3f} thick; legs to z {ZB:.2f}, "
        f"prongs out to y {Y_TIP:.3f}; overall {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}, volume {body.volume:.1f} mm3, "
        f"{len(body.faces())} faces, valid {body.is_valid}, max edge tolerance {tol:.1e}")
    log(f"pockets at x {[round(x, 2) for x in hook_cols]}, hook bottoms z {[round(z, 2) for z in hook_rows]}, seat z {seat_z:.2f}; "
        f"prong seat z {SEAT:.2f} at G, gap {GAP:.2f} (head {TL['head_width']}), lip inner face y {YL:.3f}, gable apex z {ZA:.2f}")
    for x in (L1 - 1, HD["prong_inset"] + 1):     # measured on the solid: seat top 1 in from each side, between plate and lip
        hit = body & Pos(x, (B + YL) / 2, SEAT + 20) * Box(0.01, 0.01, 40)
        log(f"seat at {XC - x:.2f} from the axis: z {hit.bounding_box().max.Z:.2f} "
            f"(expected {SEAT + (XP - x) * TAN:.2f}: {ANG:.1f} deg up from G at {XC - XP:.2f})")

    # Measured on the solids, not read from the code.
    log(f"stripper stand-in: {tool.bounding_box().size.X:.1f} x {tool.bounding_box().size.Y:.1f} x {tool.bounding_box().size.Z:.1f}, "
        f"jaw end z {J:.2f}, bump z {BUMP[0]:.2f} to {BUMP[1]:.2f}")
    log(f"stripper vs holder: overlap {overlap(body, tool):.4f} mm3; lifted 0.05: clearance {body.distance_to(Pos(0, 0, 0.05) * tool):.3f}")
    front = body & Pos(XC, B + 25, 0) * Box(200, 50 - 0.02, 200)
    log(f"head to the prongs: {front.distance_to(head):.3f} (its back rests on the plate and legs); "
        f"bump to holder: {body.distance_to(bump):.3f}")
    hks = hooks()
    log(f"hooks vs holder: {sum(overlap(body, k) for k in hks):.3f} mm3 over {len(hks)} Bridge hook 1Us (ridges "
        f"{pk['ridge']['height']:.2f} tall, room for {dv['notch']['depth'] + pk['side_clearance']:.2f} in a seated hook's notch: "
        f"overlap only if taller)")
    log(f"hooks vs stripper: {sum(overlap(tool, k) for k in hks):.3f} mm3")
    export_step(body, HERE / "step" / f"{NAME}.step")
    export_step(tool, HERE / "step" / f"{NAME}_stripper_standin.step")
    export_step(Compound(children=[body, tool, *hks], label=NAME), HERE / "step" / f"{NAME}_assembly.step")

    # Print orientation: as it hangs, on the legs' feet.
    pb = to_bed(body)
    write_print(f"{NAME}_print", pb, HERE / "print")
    plate_3mf([("holder", pb, "holder")], HERE / "print" / f"{NAME}_all_parts.3mf")
    log(f"{NAME}_all_parts.3mf: the holder, upright on the legs")

    # Test print: the back plate round the first pocket.
    hc = P["coupon"]["half_width"]
    cp = to_bed(solid(body & Pos(hook_cols[0], B / 2 - 0.5, H / 2) * Box(2 * hc, B + 1, H + 2)))
    write_print(f"{NAME}_pocket_coupon_print", cp, HERE / "test-prints")
    plate_3mf([("pocket coupon", cp, "holder")], HERE / "test-prints" / f"{NAME}_pocket_coupon_print.3mf")
    # Test print: the bottom of the holder with both prongs, to check the seats on the tool.
    st = P["coupon"]["seat_top"]
    sc = to_bed(solid(body & Pos(XC, B, (ZB + st) / 2 - 1) * Box(W + 2, 2 * B + 60, st - ZB + 2)))
    write_print(f"{NAME}_seat_coupon_print", sc, HERE / "test-prints")
    plate_3mf([("seat coupon", sc, "holder")], HERE / "test-prints" / f"{NAME}_seat_coupon_print.3mf")
    # Test print: upright pocket coupons with lower snap ridges (the holder's jammed printed upright).
    rc = [(h, to_bed(c)) for h, c in ridge_coupons()]
    for h, c in rc:
        write_print(f"{NAME}_ridge_{round(h * 100)}_coupon_print", c, HERE / "test-prints")
        log(f"    ridge {h}: {h - pk['side_clearance']:.2f} interference per side")
    plate_3mf([(f"ridge {h}", c, "holder") for h, c in rc], HERE / "test-prints" / f"{NAME}_ridge_coupons.3mf")
    (HERE / "report.txt").write_text("\n".join(lines) + "\n")
