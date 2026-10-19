# Test print for a plate handle on a stand-off rib, like Zeid's HANDLE H2, held on the drawer
# face by two printed snap pins: a strip of drawer face, the handle and pins with three barb
# sizes, all in print orientation. Values in params.yaml (handle and handle_test); the
# geometry is handle_geometry.py, which build.py uses for the drawers.
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
T, FT6 = {**P["handle"], **P["handle_test"]}, P["drawer"]["front_thickness"]
exec((HERE.parent / "core_3mf.py").read_text())
exec((HERE / "handle_geometry.py").read_text())
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


def plate():
    """Top strip of the drawer face with the handle's pin holes."""
    w, h = T["strip_width"], T["strip_height"]
    return Pos(0, -FT6 / 2, Z_TOP - h / 2) * Box(w, FT6, h) - Pos(0, 0, ZH) * handle_face_cut(T, FT6)


pl = plate()
hds = [Pos(0, 0, ZH) * handle_part(T) for i in range(3)]
pins = [handle_pin(T, FT6, b, i) for i, b in enumerate(T["barbs"])]
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
# One set per pin variant: strip, handle and the pin pair, laid out in a column each
objs = []
for k, p in enumerate(pin_p):
    x0 = -60 + 60 * k
    objs.append((f"strip {'ABC'[k]}", *shape_mesh(pl_p, x0, 45)))
    objs.append((f"handle {'ABC'[k]}", *shape_mesh(hd_p[k], x0, 5)))
    for j in range(2):
        objs.append((f"pin {'ABC'[k]}{j + 1}", *shape_mesh(p, x0 - 7 + 14 * j, -30)))
write_3mf(objs, OUT / "handle_test_all_parts.3mf")
# Just the handle and a pair of the chosen pins, to try on a strip already printed
write_3mf([("handle", *shape_mesh(hd_p[0], 0, 5)), ("pin 1", *shape_mesh(pin_p[2], -7, -30)), ("pin 2", *shape_mesh(pin_p[2], 7, -30))],
          OUT / "handle_test_handle_and_pins_c.3mf")
export_step(Compound(children=[pl, hds[1]] + [Pos(x, -FT6, ZB) * Rot(0, 90, 0) * pins[1] for x in xs]), str(OUT / "handle_test_assembly.step"))
(OUT / "handle_test_report.txt").write_text("\n".join(log_lines) + "\n")
