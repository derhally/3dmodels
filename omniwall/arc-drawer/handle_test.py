# Test print for a plate handle on a stand-off rib, like Zeid's HANDLE H2, held on the drawer
# face by two printed snap pins: a strip of drawer face, the handle and pins with three barb
# sizes, all in print orientation. Values in params.yaml (handle_test).
# Run from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python handle_test.py
# Writes test-prints/handle_test_* (STEP and STL per part, one 3MF with everything, the
# assembly with pins B, and a report).
# Use coordinates: x across the face (0 = middle of the handle), y out of the face (face
# front at y = 0), z up (the face's top at Z_TOP, as on the 3x2 drawer).
import math
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

HERE = Path(__file__).resolve().parent
P = yaml.safe_load((HERE / "params.yaml").read_text())
T, FT6 = P["handle_test"], P["drawer"]["front_thickness"]
exec((HERE.parent / "core_3mf.py").read_text())
K = math.sqrt(2)
OUT = HERE / "test-prints"
OUT.mkdir(exist_ok=True)
log_lines = []


def log(s):
    print(s)
    log_lines.append(s)


Z_TOP = 48.0                                         # face top on the 3x2 drawer (only sets where the strip sits)
ZH = Z_TOP - T["below_top"]                          # handle top: rib top and plate top edge, the bed as printed
ZB = ZH - T["socket_down"]                           # pin and socket axis height
xs = (-T["boss_x"], T["boss_x"])


def tear(r):
    """Teardrop section in the x-z plane (point up), radius r."""
    c = r / K
    return Circle(r) + Polygon((-c, c), (0, K * r), (c, c), align=None)


def bore_y(sec, y0, y1, x, z):
    """Extrude a section drawn in the x-z plane along +y from y0 to y1, centred (x, z)."""
    return Pos(x, y0, z) * extrude(Plane.XZ * sec, y1 - y0, dir=(0, 1, 0))


def plate():
    """Top strip of the drawer face with a counterbored teardrop hole for each pin."""
    w, h = T["strip_width"], T["strip_height"]
    p = Pos(0, -FT6 / 2, Z_TOP - h / 2) * Box(w, FT6, h)
    for x in xs:
        p = p - bore_y(tear(T["hole"] / 2) & Rectangle(T["hole_width"], 20), -FT6 - 1, 1, x, ZB)
        p = p - bore_y(tear(T["counterbore"] / 2), -FT6 - 1, -FT6 + T["counterbore_depth"], x, ZB)
    return p


def handle():
    """Plate leaning `lean` out from the face, hung from a rib that stands it `standoff` off the
    face; the rib grows into a flat-topped boss at each end holding a socket for a snap pin."""
    W, L, t, so = T["width"], T["drop"], T["thickness"], T["standoff"]
    lean = math.radians(T["lean"])
    # Plate, built upright (x across, y its thickness, z up along it), then leaned out about its top inner edge
    pl = Box(W, t, L + 3, align=(Align.CENTER, Align.MIN, Align.MAX))
    pl = Pos(0, 0, 3) * pl
    pl = fillet(pl.edges().filter_by(Axis.Y).filter_by(lambda e: e.center().Z < -L + 0.1), T["corner_radius"])
    h = Pos(0, so, ZH) * Rot(T["lean"], 0, 0) * pl
    # Rib, front-view section: middle bar, tapers tangent to the bosses, bosses flat on top and round below
    r, rb, zc = T["boss"] / 2, T["rib"], T["boss_height"] - T["boss"] / 2   # zc: boss's round end's centre below the top
    sec = Rectangle(2 * T["boss_x"], rb, align=(Align.CENTER, Align.MAX))
    for x in xs:
        sec = sec + Pos(x, -zc) * Circle(r) + Pos(x, 0) * Rectangle(2 * r, zc, align=(Align.CENTER, Align.MAX))
        q = (abs(x) - T["taper"], -rb)               # taper starts here on the rib's underside
        dx, dz = abs(x) - q[0], -zc - q[1]
        d = math.hypot(dx, dz)
        a = math.atan2(dz, dx) - math.asin(r / d)     # lower tangent from q to the boss circle
        tx, tz = q[0] + math.sqrt(d * d - r * r) * math.cos(a), q[1] + math.sqrt(d * d - r * r) * math.sin(a)
        sx = math.copysign(1, x)
        sec = sec + Polygon((sx * q[0], q[1]), (sx * tx, tz), (sx * abs(x), -zc), (sx * abs(x), q[1]), align=None)
    rib = Pos(0, 0, ZH) * extrude(Plane.XZ * sec, so + t, dir=(0, 1, 0))
    h = h + rib
    # Keep the rib inside the plate's outer face, and nothing above the top
    h = h & (Pos(0, so, ZH) * Rot(T["lean"], 0, 0) * Box(200, 200, 200, align=(Align.CENTER, Align.MAX, Align.CENTER)).moved(Location((0, t, 0))))
    h = h & Pos(0, 0, ZH) * Box(200, 200, 200, align=(Align.CENTER, Align.CENTER, Align.MAX))
    # 45 deg chamfers on the top corners (on the bed as printed)
    c = T["top_chamfer"]
    for sx in (-1, 1):
        tri = Polygon((sx * (W / 2 + 1), ZH + 1), (sx * (W / 2 + 1), ZH - c - 1), (sx * (W / 2 - c - 1), ZH + 1), align=None)
        h = h - Pos(0, -1, 0) * extrude(Plane.XZ * tri, 40, dir=(0, 1, 0))
    # Sockets: teardrops pointing down in use (up as printed); the shoulder at entry depth is vertical as printed
    flip = Rot(0, 0, 180)
    for x in xs:
        h = h - bore_y(flip * (tear(T["socket_entry"] / 2) & Rectangle(T["hole_width"], 20)), -1, T["socket_entry_depth"] + 0.01, x, ZB)
        h = h - bore_y(flip * tear(T["socket_chamber"] / 2), T["socket_entry_depth"], T["socket_depth"], x, ZB)
    return h


def pin(barb, notches):
    """Snap pin, axis along +y from the head's back face at y = 0, lying on a flat (as printed;
    fitted turned a quarter turn, flats sideways, so the legs spring up and down)."""
    r, rb, hr, ht = T["shank"] / 2, barb / 2, T["head"] / 2, T["head_thick"]
    tr = math.tan(math.radians(T["barb_ramp"]))
    rc = T["socket_entry"] / 2 + T["barb_preload"]   # ramp radius that sits on the shoulder edge
    ub = FT6 + T["socket_entry_depth"] + (rb - rc) * tr   # barb's full radius starts here
    ub0 = ub - (rb - r) * tr
    uf = ub + T["barb_flat"]
    ut = uf + (rb - T["tip"])
    prof = Polygon((0, 0), (0, hr), (ht, hr), (ht, r), (ub0, r), (ub, rb), (uf, rb), (ut, T["tip"]), (ut, 0), align=None)
    body = Rot(0, 0, 90) * revolve(Plane.XY * prof, Axis.X)
    body = body & Box(30, 60, T["flats"])
    body = body - Pos(0, (T["slot_start"] + ut + 1) / 2, 0) * Box(T["slot"], ut + 1 - T["slot_start"], 10)
    n = T["id_notch"]
    for sx in (1, -1)[:notches]:                     # V notch through the head at one end (B) or both (C)
        body = body - extrude(Polygon((sx * (hr + 1), -0.5), (sx * (hr - n), ht / 2), (sx * (hr + 1), ht + 0.5), align=None), 10, both=True)
    return body


pl = plate()
hds = [handle() for i in range(3)]
pins = [pin(b, i) for i, b in enumerate(T["barbs"])]
for name, s in [("plate", pl), ("handle", hds[0])] + [(f"pin {'ABC'[i]}", p) for i, p in enumerate(pins)]:
    bb = s.bounding_box()
    log(f"{name}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}, volume {s.volume:.1f} mm3, valid {s.is_valid}, solids {len(s.solids())}")
log(f"handle vs plate: {(hds[0] & pl).volume:.3f} mm3")
for i, (p, b) in enumerate(zip(pins, T["barbs"])):
    asm = [Pos(x, -FT6, ZB) * Rot(0, 90, 0) * p for x in xs]
    log(f"pin {'ABC'[i]} installed: vs plate {sum((a & pl).volume for a in asm):.3f} mm3, vs handle {sum((a & hds[0]).volume for a in asm):.3f} mm3 (the barb ramps pressing on the shoulder edges: the preload); "
        f"barbs {b} squeeze {b / 2 - T['hole'] / 2:.2f} per side through the {T['hole']} hole (slot allows {T['slot'] / 2:.2f}), "
        f"{T['socket_chamber'] / 2 - b / 2:.2f} clear in the chamber")


def bad_faces(part, limit=45.0):
    """Faces facing down flatter than `limit` from horizontal, not counting the bed face."""
    z0 = part.bounding_box().min.Z
    out = []
    for f in part.faces():
        try:
            n = f.normal_at(f.center())
        except Exception:
            continue
        if n.Z < -1e-6 and math.degrees(math.acos(min(1.0, -n.Z))) < limit - 0.5 and f.area > 0.01 and f.bounding_box().max.Z > z0 + 0.01:
            out.append(f)
    return out


def to_bed(s, dx=0.0, dy=0.0):
    bb = s.bounding_box()
    return Pos(dx - bb.center().X, dy - bb.center().Y, -bb.min.Z) * s


# Print poses: the strip standing up like the drawer face; the handle on its top; the pins
# lying on a flat (as built).
pl_p = to_bed(pl)
hd_p = [to_bed(Rot(180, 0, 0) * s) for s in hds]
pin_p = [to_bed(p) for p in pins]
parts = [("handle_test_plate", pl_p)] + [(f"handle_test_handle_{k + 1}", s) for k, s in enumerate(hd_p)] + [(f"handle_test_pin_{'abc'[i]}", p) for i, p in enumerate(pin_p)]
for name, s in parts:
    export_step(s, str(OUT / f"{name}.step"))
    export_stl(s, str(OUT / f"{name}.stl"))
    bad = bad_faces(s)
    log(f"{name}: overhangs flatter than 45 deg: {len(bad)}" + "".join(f"\n    {f.area:.2f} mm2 at {tuple(round(v, 2) for v in f.center())}" for f in bad))
objs = [("plate", *shape_mesh(pl_p, 0, 40))] + [(f"handle {k + 1}", *shape_mesh(s, -50 + 50 * k, 0)) for k, s in enumerate(hd_p)]
for i, p in enumerate(pin_p):
    for k in range(2):
        objs.append((f"pin {'ABC'[i]}{k + 1}", *shape_mesh(p, -25 + 20 * i + 8 * k, -35)))
write_3mf(objs, OUT / "handle_test_all_parts.3mf")
export_step(Compound(children=[pl, hds[1]] + [Pos(x, -FT6, ZB) * Rot(0, 90, 0) * pins[1] for x in xs]), str(OUT / "handle_test_assembly.step"))
(OUT / "handle_test_report.txt").write_text("\n".join(log_lines) + "\n")
