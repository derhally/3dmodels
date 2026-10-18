# Test print for a separate drawer handle that snaps onto the drawer face with two snap
# tabs on its posts: a strip of drawer face and three handles with different barb sizes,
# all in print orientation.
# Values in params.yaml (handle_test). Run from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python handle_test.py
# Writes test-prints/handle_test_* (STEP and STL per part, one 3MF with everything, the
# assembly with handle B snapped on, and a report).
# Use coordinates: x across the face, y out of the face (face front at y = 0), z up.
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


xs = (-(T["bar_width"] - T["post"]) / 2, (T["bar_width"] - T["post"]) / 2)   # post centres


def plate():
    """Strip of drawer face with a slot for each tab: straight sides, pointed 45 deg top."""
    w, h = T["plate_width"], T["plate_height"]
    p = Pos(0, -FT6 / 2, 0) * Box(w, FT6, h)
    hw, hh = T["hole"] / 2, T["hole_height"]
    for x in xs:
        sec = Polygon((-hw, -hh / 2), (hw, -hh / 2), (hw, hh / 2), (0, hh / 2 + hw), (-hw, hh / 2), align=None)
        p = p - Pos(x, -FT6 - 1, 0) * extrude(Plane.XZ * sec, FT6 + 2, dir=(0, 1, 0))
    return p


def tab_plan(barb):
    """Plan view (x, y) of one snap tab, centred on x = 0: from inside the post back through the face."""
    r, rb = T["tab"] / 2, barb / 2
    yb = -FT6 - T["barb_slack"]                      # barb back face, behind the face's back
    yf = yb - T["barb_flat"]
    yt = yf - (rb - T["tip"])                         # 45 deg lead-in
    tab = Polygon((-r, 1), (-r, yb), (-rb, yb), (-rb, yf), (-T["tip"], yt), (T["tip"], yt), (rb, yf), (rb, yb), (r, yb), (r, 1), align=None)
    return tab - Pos(0, (T["slot_into_post"] + yt - 1) / 2) * Rectangle(T["slot"], T["slot_into_post"] - yt + 1)


def handle(barb, notches):
    bw, po, dp, bar, h = T["bar_width"], T["post"], T["depth"], T["bar"], T["height"]
    u = Rectangle(bw, bar, align=(Align.CENTER, Align.MIN)).locate(Location((0, dp - bar))) \
        + sum((Pos(x, 0) * Rectangle(po, dp, align=(Align.CENTER, Align.MIN)) for x in xs), Sketch())
    xi = abs(xs[0]) - po / 2
    inner = [v for v in u.vertices() if abs(v.Y - (dp - bar)) < 1e-6 and abs(abs(v.X) - xi) < 1e-6]
    u = fillet([v for v in u.vertices() if v not in inner], T["round_out"])
    u = fillet([v for v in u.vertices() if abs(v.Y - (dp - bar)) < 1e-6 and abs(abs(v.X) - xi) < 1e-3], T["round_in"])
    hd = extrude(Plane.XY.offset(-h / 2) * u, h)
    hd = fillet([e for e in hd.edges() if abs(e.center().Z - h / 2) < 1e-6], T["top_round"])
    hd = chamfer([e for e in hd.edges() if abs(e.center().Z + h / 2) < 1e-6], T["bed_chamfer"])
    for x in xs:
        hd = hd + extrude(Plane.XY.offset(-h / 2) * (Pos(x, 0) * tab_plan(barb)), h)
        # carry the slot on into the post so the legs can flex
        hd = hd - Pos(x, T["slot_into_post"] / 2, 0) * Box(T["slot"], T["slot_into_post"], h + 2)
    for k in range(notches):                          # ID notches on the bar's top
        hd = hd - Pos(-3 + 3 * k, dp - bar / 2, h / 2) * Box(1.0, 3.0, 1.0)
    return hd


pl = plate()
hds = [handle(b, i + 1) for i, b in enumerate(T["barbs"])]
for name, s in [("plate", pl)] + [(f"handle {'ABC'[i]}", hd) for i, hd in enumerate(hds)]:
    bb = s.bounding_box()
    log(f"{name}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}, volume {s.volume:.1f} mm3, valid {s.is_valid}, solids {len(s.solids())}")
for i, (hd, b) in enumerate(zip(hds, T["barbs"])):
    log(f"handle {'ABC'[i]} snapped on: vs plate {(hd & pl).volume:.3f} mm3; barbs {b} squeeze {b / 2 - T['hole'] / 2:.2f} per side "
        f"through the {T['hole']} slot (the leg slot allows {T['slot'] / 2:.2f}); legs {T['slot_into_post'] + FT6 + T['barb_slack']:.1f} long to the barb")


def bad_faces(part, limit=45.0):
    """Faces facing down flatter than `limit` from horizontal, not counting the bed face."""
    z0 = part.bounding_box().min.Z
    out = []
    for f in part.faces():
        try:
            n = f.normal_at(f.center())
        except Exception:
            continue
        if n.Z < -1e-6 and math.degrees(math.acos(min(1.0, -n.Z))) < limit and f.area > 0.01 and f.bounding_box().max.Z > z0 + 0.01:
            out.append(f)
    return out


def to_bed(s, dx=0.0, dy=0.0):
    bb = s.bounding_box()
    return Pos(dx - bb.center().X, dy - bb.center().Y, -bb.min.Z) * s


# Print poses: the plate standing up like the drawer face, the handles on their bottom faces (both as built).
pl_p = to_bed(pl)
hd_p = [to_bed(hd) for hd in hds]
for name, s_ in [("handle_test_plate", pl_p)] + [(f"handle_test_handle_{'abc'[i]}", h_) for i, h_ in enumerate(hd_p)]:
    export_step(s_, str(OUT / f"{name}.step"))
    export_stl(s_, str(OUT / f"{name}.stl"))
    bad = bad_faces(s_)
    log(f"{name}: overhangs flatter than 45 deg: {len(bad)}" + "".join(f"\n    {f.area:.2f} mm2 at {tuple(round(v, 2) for v in f.center())}" for f in bad))
objs = [("plate", *shape_mesh(pl_p, 0, 34))] + [(f"handle {'ABC'[i]}", *shape_mesh(h_, -50 + 50 * i, 0)) for i, h_ in enumerate(hd_p)]
write_3mf(objs, OUT / "handle_test_all_parts.3mf")
assembly = Compound(children=[pl] + [hds[1]])
export_step(assembly, str(OUT / "handle_test_assembly.step"))
(OUT / "handle_test_report.txt").write_text("\n".join(log_lines) + "\n")
