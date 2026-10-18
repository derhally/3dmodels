# Test print for Zeid's scoop as a separate part held on the drawer face by two printed
# snap pins: a strip of drawer face, three scoops and pins with three barb sizes, all in
# print orientation. Values in params.yaml (handle_test; the scoop's shape from scoop).
# Run from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python handle_test.py
# Writes test-prints/handle_test_* (STEP and STL per part, one 3MF with everything, the
# assembly with pins B, and a report).
# Use coordinates: x across the face (0 = middle of the scoop), y out of the face (face
# front at y = 0), z up (the face's top at plate_top, as on the drawer).
import math
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

HERE = Path(__file__).resolve().parent
P = yaml.safe_load((HERE / "params.yaml").read_text())
T, SC, FT6 = P["handle_test"], P["scoop"], P["drawer"]["front_thickness"]
exec((HERE.parent / "core_3mf.py").read_text())
K = math.sqrt(2)
OUT = HERE / "test-prints"
OUT.mkdir(exist_ok=True)
log_lines = []


def log(s):
    print(s)
    log_lines.append(s)


Z_TOP = 48.0                                         # face top on the 3x2 drawer (only sets where the strip sits)
ang = SC["angle"]
s_, c_ = math.sin(math.radians(ang)), math.cos(math.radians(ang))
Z0 = Z_TOP - SC["below_top"] - SC["depth"] * (s_ + c_)   # scoop's lowest edge at the face, as in build.py
xs = (-T["boss_x"], T["boss_x"])
ZB = Z0 + T["boss_z"]                                # pin and boss axis height


def tear(r):
    """Teardrop section in the x-z plane (point up), radius r."""
    c = r / K
    return Circle(r) + Polygon((-c, c), (0, K * r), (c, c), align=None)


def bore_y(sec, y0, y1, x, z):
    """Extrude a section drawn in the x-z plane along +y from y0 to y1, centred (x, z)."""
    return Pos(x, y0, z) * extrude(Plane.XZ * sec, y1 - y0, dir=(0, 1, 0))


def plate():
    """Top strip of the drawer face with a counterbored teardrop hole for each pin."""
    w, h = T["plate_width"], T["plate_height"]
    p = Pos(0, -FT6 / 2, Z_TOP - h / 2) * Box(w, FT6, h)
    for x in xs:
        p = p - bore_y(tear(T["hole"] / 2), -FT6 - 1, 1, x, ZB)
        p = p - bore_y(tear(T["counterbore"] / 2), -FT6 - 1, -FT6 + T["counterbore_depth"], x, ZB)
    return p


def scoop(notches):
    """Zeid's scoop tray (walls tapering to the front wall, no back wall), its floor tilted
    `angle` up and out from the face and opening downward, cut at the face; built in the
    tray's own frame (u along the floor, v out of its open side towards the floor), then
    turned into place."""
    w, dp, h, t, fw = SC["width"], SC["depth"], SC["height"], SC["wall"], SC["front_width"]
    fl, fr = (w - fw) / 2, (w + fw) / 2
    a = t * math.hypot(fl, dp) / dp
    b = fl * (dp - t) / dp + a
    out = [(x - w / 2, u) for x, u in ((0, 0), (fl, dp), (fr, dp), (w, 0))]
    walls_pl = [(x - w / 2, u) for x, u in ((0, 0), (fl, dp), (fr, dp), (w, 0), (w - a, 0), (w - b, dp - t), (b, dp - t), (a, 0))]
    walls = extrude(Polygon(*walls_pl, align=None), h, dir=(0, 0, 1))
    floor = Pos(0, 0, h - t) * extrude(Polygon(*out, align=None), t + dp, dir=(0, 0, 1))   # runs on into the face, as in build.py
    tray = Pos(0, 0, Z0) * Rot(ang, 0, 0) * (walls + floor)
    sc = tray & Pos(0, 20, Z0 - 20) * Box(80, 40, 80, align=(Align.CENTER, Align.CENTER, Align.MIN))   # cut at the face
    # The open inside of the tray, so the bosses can't fill it
    cavity = Pos(0, 0, Z0) * Rot(ang, 0, 0) * (extrude(Polygon(*out, align=None), h - t, dir=(0, 0, 1)) - walls)
    for x in xs:
        # Boss: a stadium out from the face, from inside the side wall to the socket, so the
        # pull goes straight into the wall; clipped where it would enter the tray's inside
        xw = math.copysign(abs(x) - T["boss_reach"], x)
        st = Pos((x + xw) / 2, 0) * SlotCenterToCenter(abs(x - xw), T["boss"])
        boss = bore_y(st, 0, T["boss_length"], 0, ZB)
        L = T["boss_length"]
        boss = chamfer(boss.edges().filter_by(lambda e: e.bounding_box().min.Y > L - 0.01), T["boss_chamfer"])
        boss = boss - cavity
        sc = sc + boss
        sc = sc - bore_y(Circle(T["socket_entry"] / 2), -1, T["socket_entry_depth"], x, ZB)
        sc = sc - bore_y(Circle(T["socket_chamber"] / 2), T["socket_entry_depth"], T["socket_depth"], x, ZB)
        rc = T["socket_chamber"] / 2                  # 45 deg cone at the end: it is the socket's roof as printed
        sc = sc - Pos(x, T["socket_depth"] - 0.01, ZB) * Rot(-90, 0, 0) * Cone(rc + 0.01, 0, rc + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # ID notches across the front wall's rim (the open side, facing down in use)
    for k in range(notches):
        rim = Pos(0, 0, Z0) * Rot(ang, 0, 0) * Pos(-3 + 3 * k, dp - t / 2, 0) * Box(1.0, t + 1, 1.2)
        sc = sc - rim
    return sc


def pin(barb, notches):
    """Snap pin, axis along +y from the head's back face at y = 0, lying on a flat."""
    r, rb, hr, ht = T["shank"] / 2, barb / 2, T["head"] / 2, T["head_thick"]
    ub = FT6 + T["socket_entry_depth"] + T["barb_slack"]
    uf = ub + T["barb_flat"]
    ut = uf + (rb - T["tip"])
    prof = Polygon((0, 0), (0, hr), (ht, hr), (ht, r), (ub, r), (ub, rb), (uf, rb), (ut, T["tip"]), (ut, 0), align=None)
    body = Rot(0, 0, 90) * revolve(Plane.XY * prof, Axis.X)
    body = body & Box(30, 60, T["flats"])
    body = body - Pos(0, (T["slot_start"] + ut + 1) / 2, 0) * Box(T["slot"], ut + 1 - T["slot_start"], 10)
    for k in range(notches):
        body = body - Pos(hr, 0.3 + 0.7 * k + 0.15, 0) * Box(1.0, 0.3, 10)
    return body


pl = plate()
scs = [scoop(i + 1) for i in range(3)]
pins = [pin(b, i + 1) for i, b in enumerate(T["barbs"])]
for name, s in [("plate", pl), ("scoop", scs[0])] + [(f"pin {'ABC'[i]}", p) for i, p in enumerate(pins)]:
    bb = s.bounding_box()
    log(f"{name}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}, volume {s.volume:.1f} mm3, valid {s.is_valid}, solids {len(s.solids())}")
log(f"scoop vs plate: {(scs[0] & pl).volume:.3f} mm3")
for i, (p, b) in enumerate(zip(pins, T["barbs"])):
    asm = [Pos(x, -FT6, ZB) * p for x in xs]
    log(f"pin {'ABC'[i]} installed: vs plate {sum((a & pl).volume for a in asm):.3f} mm3, vs scoop {sum((a & scs[0]).volume for a in asm):.3f} mm3; "
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


# Print poses: the strip standing up like the drawer face; the scoop on its back (the face
# it sits on), so the sockets stand upright; the pins lying on a flat (as built).
pl_p = to_bed(pl)
sc_p = [to_bed(Rot(90, 0, 0) * s) for s in scs]
pin_p = [to_bed(p) for p in pins]
parts = [("handle_test_plate", pl_p)] + [(f"handle_test_scoop_{k + 1}", s) for k, s in enumerate(sc_p)] + [(f"handle_test_pin_{'abc'[i]}", p) for i, p in enumerate(pin_p)]
for name, s in parts:
    export_step(s, str(OUT / f"{name}.step"))
    export_stl(s, str(OUT / f"{name}.stl"))
    bad = bad_faces(s)
    log(f"{name}: overhangs flatter than 45 deg: {len(bad)}" + "".join(f"\n    {f.area:.2f} mm2 at {tuple(round(v, 2) for v in f.center())}" for f in bad))
objs = [("plate", *shape_mesh(pl_p, 0, 40))] + [(f"scoop {k + 1}", *shape_mesh(s, -50 + 50 * k, 0)) for k, s in enumerate(sc_p)]
for i, p in enumerate(pin_p):
    for k in range(2):
        objs.append((f"pin {'ABC'[i]}{k + 1}", *shape_mesh(p, -25 + 20 * i + 8 * k, -35)))
write_3mf(objs, OUT / "handle_test_all_parts.3mf")
export_step(Compound(children=[pl, scs[1]] + [Pos(x, -FT6, ZB) * pins[1] for x in xs]), str(OUT / "handle_test_assembly.step"))
(OUT / "handle_test_report.txt").write_text("\n".join(log_lines) + "\n")
