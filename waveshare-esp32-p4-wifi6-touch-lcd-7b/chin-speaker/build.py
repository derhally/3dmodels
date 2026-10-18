"""45-degree desk enclosure with the speaker in the chin under the screen.

    pip install build123d pyyaml
    python build.py [params.yaml] [output_dir]

Defaults: params.yaml next to this script (merged over ../common/common.yaml),
output into ./step and ./print.
"""

import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / "common"))

from enclosure_lib import *  # noqa: E402,F403

P = load_params(Path(sys.argv[1]) if len(sys.argv) > 1 else here / "params.yaml")
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else here
g = Geo(P)
dp, en, sp, cp = P["display"], P["enclosure"], P["speaker"], P["clamps"]
co, si, wall, t = g.co, g.si, g.wall, g.t
W = 2 * (g.wx + en["border"])

# --- layout along the slope: speaker chin, then the glass ----------------------
sw, sh = sp["width"], sp["height"]
ring_w = 1.6
chin = sh + 2 * sp["fit"] + 2 * ring_w + 2 * sp["margin"]
s_g = chin + g.ph / 2                     # glass centre along the slope
L = s_g + g.va_up + g.wy + en["border"]   # slope length of the front plate
s_sp = chin / 2                           # speaker centre along the slope
sp_back = t + sp["depth"] + 1.0

# clamp columns sit just above and below the pocket, in line with each standoff
col, gap = cp["column"], cp["column_gap"]
col_s = [chin + g.ph + gap + col / 2, chin + g.trim - gap - col / 2]   # top, bottom

g.h0 = max(en["min_front_lip"],
           wall + 1 - (s_sp - sh / 2) * si + sp_back * co,
           wall + 2 - chin * si + (g.f + dp["depth"] + 1.5) * co,
           wall + 1 - (col_s[1] - col / 2) * si + g.clamp_back * co)
D = max(g.Pw(s_g + g.ph / 2, g.f + dp["depth"] + 1.5)[0],
        g.Pw(col_s[0] + col / 2, g.clamp_back)[0],
        g.Pw(s_sp + sh / 2, sp_back)[0]) + en["rear_clearance"] + wall
D = max(D, L * co + 8)

# --- front plate -------------------------------------------------------------------
plate = facade_plate(g, W, L, s_g)
plate = add_clamp_columns(plate, g, [(g.gx + sx * g.hole_x, cs) for sx in (-1, 1) for cs in col_s],
                          (col, col))

# speaker retaining ring, ear standoffs, slotted grille
fw, fh = sw + 2 * sp["fit"], sh + 2 * sp["fit"]
ring = Box(fw + 2 * ring_w, fh + 2 * ring_w, sp["ring_height"]) - Box(fw, fh, 3 * sp["ring_height"])
plate += Pos(0, s_sp, -t - sp["ring_height"] / 2 + 0.25) * ring
slot_r = 1.2
so_r = sp["standoff_d"] / 2
slot_half = min(sw / 2 - 6, sp["hole_dx"] / 2 - so_r - 1.5 - slot_r)
ears = speaker_ears(sp)
ear_z = -(t + sp["ear_front"])
for ex, ey in ears:
    at = (ex, s_sp + ey)
    plate += Pos(*at, -t + 0.5) * Cylinder(so_r, sp["ear_front"] + 0.5, align=(CENTER, CENTER, MAX))
    plate += Pos(*at, ear_z + 0.01) * Cylinder(
        sp["spigot_d"] / 2, sp["spigot_h"] + 0.01, align=(CENTER, CENTER, MAX))
    plate -= Pos(*at, ear_z - sp["spigot_h"] - 0.01) * Cylinder(
        sp["pilot"] / 2, t + sp["ear_front"] + sp["spigot_h"] - 1.2, align=(CENTER, CENTER, MIN))
n_slots = int((sh - 8) // 4.5) + 1
with BuildSketch() as grille:
    with GridLocations(0, 4.5, 1, n_slots):
        SlotCenterToCenter(2 * slot_half, 2 * slot_r)
plate -= Pos(0, s_sp, 0) * extrude(grille.sketch, amount=3 * t, both=True)

plate, body_cut = add_side_bosses(plate, g, W, [10.0, L - 6.0])
plate = g.to_world(plate) + top_cap(g, W, L, D)
plate.label = "front_plate"

# --- clamp tabs, body, stand-ins ------------------------------------------------------
holes = [(g.gx + sx * g.hole_x, s_g + hy) for sx in (-1, 1) for hy in g.hole_ys]
columns = [(hx, hs, hx, col_s[0] if hs > s_g else col_s[1]) for hx, hs in holes]
tab = clamp_tab(g, [abs(cs - hs) for _, hs, _, cs in columns])
tabs = place_tabs(g, tab, s_g, columns)

body, Zc = body_shell(g, W, L, D, body_cut)

stand_ins = display_stand_ins(g, s_g)
speaker = g.to_world(Pos(0, s_sp, -t) * speaker_stand_in(sp, ears))
speaker.label = "speaker"
stand_ins.append(speaker)
if P["usb_port"]["enabled"]:
    stand_ins.append(usb_port_stand_in(P, D))

# --- export ----------------------------------------------------------------------------
step_dir, print_dir = out_dir / "step", out_dir / "print"
parts = [plate, body, *tabs]
write(Compound(children=parts + stand_ins), step_dir / "p4_7b_enclosure_assembly", ["step"])
write(Compound(children=parts), step_dir / "p4_7b_enclosure_only", ["step"])
write(plate, step_dir / "p4_7b_front_plate", ["step"])
write(body, step_dir / "p4_7b_body", ["step"])
write(tab, step_dir / "p4_7b_clamp_tab", ["step"])

plate_print = on_bed(Rot(X=180 - g.angle) * plate)   # facade on the bed
body_print = on_bed(body)
tab_print = on_bed(tab)
write(plate_print, print_dir / "p4_7b_front_plate_print", ["step", "stl", "3mf"])
write(body_print, print_dir / "p4_7b_body_print", ["step", "stl", "3mf"])
tw = cp["tab_w"]
write(on_bed(Compound(children=[Pos(i * (tw + 4), 0, 0) * tab for i in range(4)])),
      print_dir / "p4_7b_clamp_tabs_print", ["step", "stl", "3mf"])
write(facade_test_frame(g, W, L, s_g), out_dir / "test-prints" / "p4_7b_facade_test_frame", ["step", "stl", "3mf"])

tb = tab_print.bounding_box()
write_bambu_project(
    [("Front plate", [("Front plate", plate_print)]),
     ("Body", [("Body", body_print)]),
     ("Clamp tabs", [(f"Clamp tab {i + 1}",
                      Pos((i % 2 - 0.5) * (tb.size.X + 10), (i // 2 - 0.5) * (tb.size.Y + 10), 0) * tab_print)
                     for i in range(4)])],
    print_dir / "p4_7b_bambu_project.3mf",
    bed=P["print_bed"],
)
