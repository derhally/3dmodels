"""Compact 45-degree desk enclosure: speaker standing at the back of the base,
with a printed duct carrying its sound forward to a slot grille in the front lip.

    pip install build123d pyyaml
    python build.py [params.yaml] [output_dir]

Defaults: params.yaml next to this script (merged over ../common/common.yaml),
output into ./step and ./print.
"""

import math
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / "common"))

from enclosure_lib import *  # noqa: E402,F403

P = load_params(Path(sys.argv[1]) if len(sys.argv) > 1 else here / "params.yaml")
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else here
g = Geo(P)
dp, en, sp, cp, du = P["display"], P["enclosure"], P["speaker"], P["clamps"], P["duct"]
co, si, wall, t = g.co, g.si, g.wall, g.t
W = 2 * (g.wx + en["border"])

# --- layout along the slope: even border all round, no chin -------------------------
s_w = en["border"] + g.wy                 # window centre along the slope
s_g = s_w - g.va_up                       # glass centre
L = s_w + g.wy + en["border"]

# clamp columns beside the pocket, level with each standoff
col_x, col_s, gap = cp["column"], cp["column_s"], cp["column_gap"]
col_cx = g.pw / 2 + gap + col_x / 2       # from glass centre
assert g.gx + col_cx + col_x / 2 <= W / 2 - wall - 0.2, "side border too narrow for the clamp columns"
columns = []
for sx in (-1, 1):
    for hy in g.hole_ys:
        hs = s_g + hy
        shift = cp["column_shift"] if hy > 0 else -cp["column_shift"]
        columns.append((g.gx + sx * g.hole_x, hs, g.gx + sx * col_cx, hs + shift))

# --- duct and speaker (world YZ) -------------------------------------------------------
dt, inset, clear = du["wall_t"], du["rim_inset"], du["ceiling_clear"]
sw, sh = sp["width"], sp["height"]
z_fi = wall + dt                                   # duct interior floor
# lowest point of the display: bottom edge of the PCB at the rear component depth
s_pb, d_back = s_g + g.pcb_bot, g.f + dp["depth"]
g.h0 = max(en["min_front_lip"],
           du["mouth_h"] + z_fi + clear + dt - s_pb * si + d_back * co)
Y_v, Z_v = g.Pw(s_pb, d_back)
z_mt = Z_v - clear - dt                             # mouth interior top
z_rt = z_fi + sh - 2 * inset                        # rear interior top (speaker face less rim)
# The roof rises from just under the display's lowest point at roof_angle. At or
# below the screen angle it never meets the display, and it is also the lean of
# the duct wall when printed mouth-down, so a lower angle prints more cleanly.
roof = math.radians(min(du["roof_angle"], en["angle"]))
tan_r = math.tan(roof)
slope0 = Z_v - clear - dt / math.cos(roof)          # interior roof at Y_v


def roof_y(z):
    """Y where the sloped interior roof reaches height z."""
    return Y_v + (z - slope0) / tan_r


Yf = roof_y(z_rt) + du["speaker_margin"]           # speaker face plane
sp_bottom = z_fi - inset
sp_cz = sp_bottom + sh / 2

D = max(g.Pw(s_g + g.ph / 2, g.f + dp["depth"] + 1.5)[0],
        g.Pw(s_g + g.hole_ys[0] + 3.5, g.clamp_back)[0],
        Yf + sp["depth"] + 3 + 1) + en["rear_clearance"] + wall
D = max(D, L * co + 8)

# --- front plate -----------------------------------------------------------------------
plate = facade_plate(g, W, L, s_g)
plate = add_clamp_columns(plate, g, [(cx, cs) for _, _, cx, cs in columns], (col_x, col_s))
plate, body_cut = add_side_bosses(plate, g, W, [4.5, L - 6.0])
plate = g.to_world(plate) + top_cap(g, W, L, D)
plate.label = "front_plate"

tab = clamp_tab(g, [math.hypot(cx - hx, cs - hs) for hx, hs, cx, cs in columns])
tabs = place_tabs(g, tab, s_g, columns)

# --- duct ------------------------------------------------------------------------------
xi = sw / 2 - inset                                 # interior half-width
xo = xi + dt
y0 = wall - 0.5
interior = Plane.YZ * Polygon(
    (y0, z_fi), (Yf + 1, z_fi), (Yf + 1, z_rt), (roof_y(z_rt), z_rt),
    (roof_y(z_mt), z_mt), (y0, z_mt), align=None)
envelope = extrude(offset(interior, amount=dt, kind=Kind.INTERSECTION), amount=xo, both=True)
envelope &= Pos(0, (wall + Yf) / 2, 0) * Box(4 * xo, Yf - wall, 400)
duct = envelope - extrude(interior, amount=xi, both=True)

ears = speaker_ears(sp)
ear_y = Yf + sp["ear_front"]
keep = envelope + Pos(0, Yf - 0.01, 0) * Box(4 * xo, sp["ear_front"] + 0.02, 400, align=(CENTER, MIN, CENTER))
for ex, ey in ears:
    at_x, at_z = ex, sp_cz + ey
    # run each standoff the full length of the duct so it grows from the bed when
    # printed mouth-down; the roof clips the upper pair where it slopes away
    column = Pos(at_x, ear_y, at_z) * Cylinder(
        sp["standoff_d"] / 2, ear_y - wall, rotation=(90, 0, 0), align=(CENTER, CENTER, MIN))
    duct += column & keep
    duct += Pos(at_x, ear_y - 0.01, at_z) * Cylinder(
        sp["spigot_d"] / 2, sp["spigot_h"] + 0.01, rotation=(-90, 0, 0), align=(CENTER, CENTER, MIN))
    duct -= Pos(at_x, ear_y + sp["spigot_h"] + 0.01, at_z) * Cylinder(
        sp["pilot"] / 2, 10, rotation=(90, 0, 0), align=(CENTER, CENTER, MIN))

lug_w, lug_t = du["lug"]
z_lug = wall + du["lug_height"]
lug_spots = [(sx * (xo + lug_w / 2), ly) for sx in (-1, 1) for ly in (wall + 6, Yf - 6)]
for lx, ly in lug_spots:
    # 45 deg lead-in on the front side: printed mouth-down, each lug grows out of
    # the duct wall instead of starting in mid-air
    sx = math.copysign(1, lx)
    x_in, x_out = sx * (xo - 1), sx * (xo + lug_w)
    outline = [(x_in, ly - lug_w / 2 - lug_w - 1), (x_out, ly - lug_w / 2),
               (x_out, ly + lug_w / 2), (x_in, ly + lug_w / 2)]
    lug = extrude(Plane.XY.offset(z_lug) * Polygon(*outline, align=None), amount=lug_t)
    lug &= Pos(0, wall, 0) * Box(4 * xo, Yf, 400, align=(CENTER, MIN, CENTER))
    # printed mouth-down, "up" is toward the speaker end (+Y)
    duct += lug - teardrop(Plane.XY.offset(z_lug), (lx, ly, z_lug), du["lug_hole"] / 2, 3 * lug_t,
                           up=(0, 1, 0), both=True)
duct.label = "duct"

# --- body ------------------------------------------------------------------------------
body, Zc = body_shell(g, W, L, D, body_cut)
for lx, ly in lug_spots:                            # floor bosses for the duct lugs
    body += Pos(lx, ly, wall - 0.5) * Cylinder(3.5, z_lug - wall + 0.5, align=(CENTER, CENTER, MIN))
    body -= Pos(lx, ly, z_lug + 0.01) * Cylinder(
        du["lug_pilot"] / 2, z_lug - du["lug_pilot_skin"], align=(CENTER, CENTER, MAX))
pitch = du["grille_slot"] + du["grille_bar"]
n_slots = du.get("grille_count") or int((2 * xi - 2 + du["grille_bar"]) // pitch)
slot_r, slot_h = du["grille_slot"] / 2, z_mt - z_fi
for i in range(n_slots):                            # slot grille in the front lip
    x = (i - (n_slots - 1) / 2) * pitch
    # vertical slots with round ends: printed standing up, each top is a short arch
    body -= Pos(x, wall / 2, z_fi + slot_h / 2) * Box(du["grille_slot"], 3 * wall, slot_h - 2 * slot_r)
    for zc in (z_fi + slot_r, z_mt - slot_r):
        body -= Pos(x, wall / 2, zc) * Cylinder(slot_r, 3 * wall, rotation=(90, 0, 0))
body.label = "body"

# --- stand-ins ---------------------------------------------------------------------------
stand_ins = display_stand_ins(g, s_g)
speaker = Pos(0, Yf, sp_cz) * (Rot(X=90) * speaker_stand_in(sp, ears))   # cones face -Y
speaker.label = "speaker"
stand_ins.append(speaker)
if P["usb_port"]["enabled"]:
    stand_ins.append(usb_port_stand_in(P, D))

# --- export ------------------------------------------------------------------------------
step_dir, print_dir = out_dir / "step", out_dir / "print"
parts = [plate, body, duct, *tabs]
write(Compound(children=parts + stand_ins), step_dir / "p4_7b_compact_assembly", ["step"])
write(Compound(children=parts), step_dir / "p4_7b_compact_enclosure_only", ["step"])
write(plate, step_dir / "p4_7b_compact_front_plate", ["step"])
write(body, step_dir / "p4_7b_compact_body", ["step"])
write(duct, step_dir / "p4_7b_compact_duct", ["step"])
write(tab, step_dir / "p4_7b_compact_clamp_tab", ["step"])

plate_print = on_bed(Rot(X=180 - g.angle) * plate)   # facade on the bed
body_print = on_bed(body)
duct_print = on_bed(Rot(X=90) * duct)                 # mouth on the bed, standoffs up
tab_print = on_bed(tab)
write(plate_print, print_dir / "p4_7b_compact_front_plate_print", ["step", "stl", "3mf"])
write(body_print, print_dir / "p4_7b_compact_body_print", ["step", "stl", "3mf"])
write(duct_print, print_dir / "p4_7b_compact_duct_print", ["step", "stl", "3mf"])
tw = cp["tab_w"]
write(on_bed(Compound(children=[Pos(i * (tw + 4), 0, 0) * tab for i in range(4)])),
      print_dir / "p4_7b_compact_clamp_tabs_print", ["step", "stl", "3mf"])
write(facade_test_frame(g, W, L, s_g), out_dir / "test-prints" / "p4_7b_facade_test_frame", ["step", "stl", "3mf"])

tb, db = tab_print.bounding_box(), duct_print.bounding_box()
tab_x0 = db.size.X / 2 + 12 + tb.size.X / 2
write_bambu_project(
    [("Front plate", [("Front plate", plate_print)]),
     ("Body", [("Body", body_print)]),
     ("Duct and clamp tabs",
      [("Duct", Pos(-tb.size.X, 0, 0) * duct_print)]
      + [(f"Clamp tab {i + 1}",
          Pos(tab_x0 - tb.size.X + (i % 2) * (tb.size.X + 8), (i // 2 - 0.5) * (tb.size.Y + 8), 0) * tab_print)
         for i in range(4)])],
    print_dir / "p4_7b_compact_bambu_project.3mf",
    template=TEMPLATE,                                # plates spaced for the template's printer
    settings=PRINT,
)

print(f"overall {W:.1f} W x {D:.1f} D x {Zc:.1f} H mm; lip {g.h0:.1f}; speaker face at Y {Yf:.1f}")
