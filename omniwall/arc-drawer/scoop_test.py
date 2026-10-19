# Test print for the scoop on snap pins (front.pull: scoop_pins): a strip of the drawer face
# with the recess and pin holes, the scoop and its pins, all in print orientation. Values in
# params.yaml (handle, scoop_pins, scoop_test); the geometry is handle_geometry.py, which
# build.py uses for the drawers.
# Run from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python scoop_test.py
# Writes test-prints/scoop_test_* (STEP and STL per part, one 3MF with everything, the
# assembly, and a report).
# Use coordinates: x across the face (0 = middle of the scoop), y out of the face (face
# front at y = 0), z up (the face's top at Z_TOP, as on the drawers).
import math
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

HERE = Path(__file__).resolve().parent
P = yaml.safe_load((HERE / "params.yaml").read_text())
T, FT6 = {**P["handle"], **P["scoop_pins"], **P["scoop_test"]}, P["drawer"]["front_thickness"]
exec((HERE.parent / "core_3mf.py").read_text())
exec((HERE / "handle_geometry.py").read_text())
OUT = HERE / "test-prints"
OUT.mkdir(exist_ok=True)
log_lines = []


def log(s):
    print(s)
    log_lines.append(s)


def ov(a, b):
    return sum(((x & y).volume if (x & y) else 0) for x in a.solids() for y in b.solids())


Z_TOP = 48.0                                         # face top on the drawers (only sets where the strip sits)
ZH = Z_TOP - T["below_top"]                          # scoop top
ZB = ZH - T["socket_down"]                           # pin and socket axis height
xs = (-T["boss_x"], T["boss_x"])

w, h = T["strip_width"], T["strip_height"]
strip = Pos(0, -FT6 / 2, Z_TOP - h / 2) * Box(w, FT6, h) - Pos(0, 0, ZH) * scoop_pins_face_cut(T, FT6)
sc = Pos(0, 0, ZH) * scoop_pins_part(T)
pin = handle_pin(T, FT6 - T["recess"], T["barb"])
fitted = [Pos(x, -FT6, ZB) * Rot(0, 90, 0) * pin for x in xs]
for name, s in (("strip", strip), ("scoop", sc), ("pin", pin)):
    bb = s.bounding_box()
    log(f"{name}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}, volume {s.volume:.1f} mm3, valid {s.is_valid}, solids {len(s.solids())}")
log(f"scoop vs strip: {ov(sc, strip):.3f} mm3")
log(f"pins fitted: vs strip {sum(ov(f, strip) for f in fitted):.3f} mm3, vs scoop {sum(ov(f, sc) for f in fitted):.3f} mm3 (the barb ramps pressing on the shoulder edges: the preload)")


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


def to_bed(s):
    bb = s.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * s


# Print poses: the strip standing up like the drawer face, the scoop on its back, the pins lying on a flat
parts = [("scoop_test_strip", to_bed(strip)), ("scoop_test_scoop", to_bed(pull_print_rot(T) * scoop_pins_part(T))), ("scoop_test_pin", to_bed(pin))]
for name, s in parts:
    export_step(s, str(OUT / f"{name}.step"))
    export_stl(s, str(OUT / f"{name}.stl"))
    bad = bad_faces(s)
    log(f"{name}: overhangs flatter than 45 deg: {len(bad)}" + "".join(f"\n    {f.area:.2f} mm2 at {tuple(round(v, 2) for v in f.center())}" for f in bad))
sp, scp, pp = (p for _, p in parts)
objs = [("strip", *shape_mesh(sp, 0, 30)), ("scoop", *shape_mesh(scp, 0, 0))]
objs += [(f"pin {j + 1}", *shape_mesh(pp, -21 + 14 * j, -25)) for j in range(T["pins"])]
write_3mf(objs, OUT / "scoop_test_all_parts.3mf")
export_step(Compound(children=[strip, sc, *fitted]), str(OUT / "scoop_test_assembly.step"))
(OUT / "scoop_test_report.txt").write_text("\n".join(log_lines) + "\n")
