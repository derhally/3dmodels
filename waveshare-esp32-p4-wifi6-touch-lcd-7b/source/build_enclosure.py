"""Generate the desk enclosure for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B.

Requires build123d and PyYAML:

    pip install build123d pyyaml
    python build_enclosure.py [params.yaml] [output_dir]

Defaults: enclosure.yaml next to this script, output into the device folder
(../step and ../print). All dimensions live in the YAML file.
"""

import math
import sys
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

here = Path(__file__).resolve().parent
params_path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "enclosure.yaml"
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else here.parent
P = yaml.safe_load(params_path.read_text(encoding="utf-8"))

dp, en, sp, sc = P["display"], P["enclosure"], P["speaker"], P["screws"]
th = math.radians(en["angle"]); co, si = math.cos(th), math.sin(th)
wall, t = en["wall"], en["plate_t"]
cl = en["pocket_clearance"]
pw, ph = dp["glass_w"] + 2 * cl, dp["glass_h"] + 2 * cl
W = pw + 2 * en["side_bezel"]

# --- speaker / chin -------------------------------------------------------
if sp["shape"] == "round":
    sw = sh = sp["diameter"]
else:
    sw, sh = sp["width"], sp["height"]
ring_w = 1.6
chin = sh + 2 * sp["fit"] + 2 * ring_w + 2 * sp["margin"]
L = chin + ph + en["top_bezel"]          # slope length of the front plate
s_g = chin + ph / 2                       # glass centre along the slope
s_sp = chin / 2                           # speaker centre along the slope
sp_back = t + sp["depth"] + 1.0
arm_t = sc["arm_thickness"]
arm_back = dp["standoff_end"] + arm_t + 2.5   # incl. screw head

# --- display geometry (glass-centred) ---------------------------------------
pcb_top = dp["glass_h"] / 2 - dp["pcb_top_inset"]
pcb_bot = pcb_top - dp["pcb_h"]
pcb_cy = (pcb_top + pcb_bot) / 2
hole_x = dp["pcb_w"] / 2 - dp["hole_inset"]
hole_ys = [pcb_top - dp["hole_inset"], pcb_bot + dp["hole_inset"]]
usb_y = pcb_bot + dp["usb_c_from_pcb_bottom"]

# Plate-local frame: x across, y up the slope (s), z out of the screen.
# Depth d behind the glass face is z = -d.  World: Rot(X=angle) then lift h0.
h0 = max(en["min_front_lip"],
         wall + 1 - (s_sp - sh / 2) * si + sp_back * co,
         wall + 2 - chin * si + (dp["depth"] + 1.5) * co,
         wall + 2 - (s_g + hole_ys[1] - 3) * si + arm_back * co)


def Pw(s, d):
    return (s * co + d * si, h0 + s * si - d * co)


def to_world(shape):
    return Pos(0, 0, h0) * (Rot(X=en["angle"]) * shape)


D = max(Pw(s_g + ph / 2, dp["depth"] + 1.5)[0],
        Pw(s_g + hole_ys[0] + 3, arm_back)[0],
        Pw(s_sp + sh / 2, sp_back)[0]) + en["rear_clearance"] + wall
D = max(D, L * co + 8)
Zc = h0 + L * si

# --- front plate -----------------------------------------------------------
plate = Box(W, L, t, align=(Align.CENTER, Align.MIN, Align.MAX))
trim = en["pocket_trim_bottom"]
plate -= Pos(0, s_g + trim / 2, 0) * Box(pw, ph - trim, 3 * t)

# mic holes: 7-hole hex cluster in the bezel under each mic
mh = P["mic_holes"]
for sx in (-1, 1):
    cx, cy = sx * dp["mic_x"], chin - mh["below_opening"]
    pts = [(cx, cy)] + [(cx + mh["pitch"] * math.cos(math.radians(a)),
                         cy + mh["pitch"] * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    for px, py in pts:
        plate -= Pos(px, py, 0) * Cylinder(mh["diameter"] / 2, 3 * t)

# display hooks: columns beside the glass, arms seat on the standoff ends
zc = -dp["standoff_end"]
cx0 = pw / 2 + 0.2
cx1 = cx0 + 4.0
col_h = dp["standoff_end"] + arm_t - t
for sx in (-1, 1):
    for hy in hole_ys:
        yy = s_g + hy
        plate += Pos(sx * (cx0 + cx1) / 2, yy, -t + 0.5) * Box(
            cx1 - cx0, 6, col_h + 0.5, align=(Align.CENTER, Align.CENTER, Align.MAX))
        plate += Pos(sx * (hole_x + cx1) / 2, yy, zc) * Box(
            cx1 - hole_x, 6, arm_t, align=(Align.CENTER, Align.CENTER, Align.MAX))
        plate += Pos(sx * hole_x, yy, zc) * Cylinder(
            3, arm_t, align=(Align.CENTER, Align.CENTER, Align.MAX))
        plate -= Pos(sx * hole_x, yy, zc) * Cylinder(1.4, 4 * arm_t)

# speaker retaining ring, ear standoffs, slotted grille
fw, fh = sw + 2 * sp["fit"], sh + 2 * sp["fit"]
if sp["shape"] == "round":
    ring = Cylinder(fw / 2 + ring_w, sp["ring_height"]) - Cylinder(fw / 2, 3 * sp["ring_height"])
else:
    ring = Box(fw + 2 * ring_w, fh + 2 * ring_w, sp["ring_height"]) - Box(fw, fh, 3 * sp["ring_height"])
plate += Pos(0, s_sp, -t - sp["ring_height"] / 2 + 0.25) * ring
slot_r = 1.2
slot_half = sw / 2 - 6
ears = []
if sp.get("hole_d"):
    so_r = sp["standoff_d"] / 2
    slot_half = min(slot_half, sp["hole_dx"] / 2 - so_r - 1.5 - slot_r)
    ear_z = -(t + sp["ear_front"])
    for px in (-1, 1):
        for py in (-1, 1):
            ears.append((px * sp["hole_dx"] / 2, py * sp["hole_dy"] / 2))
            at = (px * sp["hole_dx"] / 2, s_sp + py * sp["hole_dy"] / 2)
            plate += Pos(*at, -t + 0.5) * Cylinder(
                so_r, sp["ear_front"] + 0.5, align=(Align.CENTER, Align.CENTER, Align.MAX))
            plate += Pos(*at, ear_z + 0.01) * Cylinder(
                sp["spigot_d"] / 2, sp["spigot_h"] + 0.01,
                align=(Align.CENTER, Align.CENTER, Align.MAX))
            plate -= Pos(*at, ear_z - sp["spigot_h"] - 0.01) * Cylinder(
                sp["pilot"] / 2, t + sp["ear_front"] + sp["spigot_h"] - 1.2,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
slot_pitch = 4.5
n_slots = int((sh - 8) // slot_pitch) + 1
with BuildSketch() as g:
    with GridLocations(0, slot_pitch, 1, n_slots):
        SlotCenterToCenter(2 * slot_half, 2 * slot_r)
plate -= Pos(0, s_sp, 0) * extrude(g.sketch, amount=3 * t, both=True)

# side bosses for the M3 screws that hold the plate in the body
bx1 = W / 2 - wall - 0.2
bx0 = bx1 - 6
boss_s = [10.0, L - 6.0]
boss_z = -(t + 4)
body_cut = []
for sx in (-1, 1):
    for sb in boss_s:
        plate += Pos(sx * (bx0 + bx1) / 2, sb, -t + 0.5) * Box(
            bx1 - bx0, 8, 8.5, align=(Align.CENTER, Align.CENTER, Align.MAX))
        plate -= Pos(sx * (bx1 - 4), sb, boss_z) * Cylinder(
            sc["side_pilot"] / 2, 8.5, rotation=(0, 90, 0))
        body_cut.append(Pos(sx * (W / 2 - wall / 2), sb, boss_z) * Cylinder(
            sc["side_clear"] / 2, 3 * wall, rotation=(0, 90, 0)))
        body_cut.append(Pos(sx * (W / 2 + 0.01), sb, boss_z) * Cone(
            3.2, sc["side_clear"] / 2, 1.6, rotation=(0, -90 * sx, 0),
            align=(Align.CENTER, Align.CENTER, Align.MIN)))
plate = to_world(plate)
plate.label = "front_plate"

# --- body ------------------------------------------------------------------
profile = Plane.YZ * Polygon((0, 0), (0, h0), (L * co, Zc), (D, Zc), (D, 0), align=None)
outer = extrude(profile, amount=W / 2, both=True)
inner = extrude(offset(profile, amount=-wall, kind=Kind.INTERSECTION),
                amount=W / 2 - wall, both=True)
body = outer - to_world(Box(W, L, t, align=(Align.CENTER, Align.MIN, Align.MAX))) - inner
for cut in body_cut:
    body -= to_world(cut)
un = P["usb_notch"]
r = un["width"] / 2
body -= Pos(un["x"], D - wall / 2, -1) * Box(un["width"], 3 * wall, un["height"] - r + 1,
                                            align=(Align.CENTER, Align.CENTER, Align.MIN))
body -= Pos(un["x"], D - wall / 2, un["height"] - r) * Cylinder(r, 3 * wall, rotation=(90, 0, 0))
for i in range(9):   # vertical vent slots: short bridges print cleanly
    body -= Pos((i - 4) * 8, D - wall / 2, Zc - 22) * Box(3, 3 * wall, 24)
ft = P["feet"]
for fx in (-1, 1):
    for fy in (ft["inset"], D - ft["inset"]):
        body -= Pos(fx * (W / 2 - ft["inset"]), fy, 0) * Cylinder(
            ft["diameter"] / 2, 2 * ft["depth"])
body.label = "body"


# --- stand-ins for fit and clash checks ---------------------------------------
def dummy(shape, name):
    s = to_world(shape)
    s.label = name
    return s


glass = dummy(Pos(0, s_g, -1) * Box(dp["glass_w"], dp["glass_h"], 2), "display_glass")
lcd = dummy(Pos(0, s_g + pcb_cy, -(2 + dp["lcd_back"]) / 2) * Box(
    dp["pcb_w"], 97.1, dp["lcd_back"] - 2), "display_lcd")
pcb = dummy(Pos(0, s_g + pcb_cy, -(dp["pcb_front"] + dp["pcb_back"]) / 2) * Box(
    dp["pcb_w"], dp["pcb_h"], dp["pcb_back"] - dp["pcb_front"]), "display_pcb")
comp_h = dp["depth"] - dp["pcb_back"]
comps = Pos(0, s_g + pcb_cy, -dp["pcb_back"] - comp_h / 2) * Box(
    dp["pcb_w"] - 0.4, dp["pcb_h"] - 0.4, comp_h)
so_h = dp["standoff_end"] - dp["pcb_back"]
standoffs = []
for sx in (-1, 1):
    for hy in hole_ys:
        comps -= Pos(sx * hole_x, s_g + hy, -dp["pcb_back"] - comp_h / 2) * Box(9, 9, 2 * comp_h)
        standoffs.append(Pos(sx * hole_x, s_g + hy, -dp["pcb_back"]) * Cylinder(
            dp["standoff_d"] / 2, so_h, align=(Align.CENTER, Align.CENTER, Align.MAX)))
comps = dummy(comps, "display_components")
standoffs = [dummy(s, "standoff") for s in standoffs]
plug = dummy(Pos(-(dp["pcb_w"] / 2 + 1 + 1.75), s_g + usb_y, -10.4) * Box(3.5, 11.2, 7.8),
             "usb_plug")
# speaker: box with corner notches in front of and behind each mounting ear
spk = Box(sw, sh, sp["depth"], align=(Align.CENTER, Align.CENTER, Align.MAX))
for ex, ey in ears:
    spk -= Pos(ex, ey, 0.01) * Cylinder(
        sp["notch_r"], sp["ear_front"] + 0.01, align=(Align.CENTER, Align.CENTER, Align.MAX))
    spk -= Pos(ex, ey, -(sp["ear_front"] + sp["ear_t"])) * Cylinder(
        sp["notch_r"], sp["depth"], align=(Align.CENTER, Align.CENTER, Align.MAX))
    spk -= Pos(ex, ey, 0) * Cylinder(sp["hole_d"] / 2, 3 * sp["depth"])
speaker = dummy(Pos(0, s_sp, -t) * spk, "speaker")

# --- cutout test frame: same opening as the plate, thin rim --------------------
rim, frame_t = 6.0, 1.2
test_frame = Box(pw + 2 * rim, ph - trim + 2 * rim, frame_t,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
test_frame -= Box(pw, ph - trim, 3 * frame_t)
with BuildSketch() as m:
    Triangle(a=4, b=4, c=4)   # marks the trimmed (bottom) edge
test_frame -= Pos(0, -(ph - trim) / 2 - rim / 2, 0) * extrude(m.sketch, amount=3 * frame_t, both=True)


# --- export --------------------------------------------------------------------
def on_bed(shape):
    bb = shape.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * shape


def write(shape, path, formats):
    path.parent.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        out = path.parent / f"{path.name}.{fmt}"
        if fmt == "step":
            export_step(shape, str(out))
        elif fmt == "stl":
            export_stl(shape, str(out))
        elif fmt == "3mf":
            mesher = Mesher()
            mesher.add_shape(shape)
            mesher.write(str(out))
        print("wrote", out)


step_dir, print_dir = out_dir / "step", out_dir / "print"
stand_ins = [glass, lcd, pcb, comps, plug, speaker, *standoffs]
write(Compound(children=[plate, body, *stand_ins]), step_dir / "p4_7b_enclosure_assembly", ["step"])
write(Compound(children=[plate, body]), step_dir / "p4_7b_enclosure_only", ["step"])
write(plate, step_dir / "p4_7b_front_plate", ["step"])
write(body, step_dir / "p4_7b_body", ["step"])
# Plate prints face-down: undo the tilt and flip the glass face onto the bed.
write(on_bed(Rot(X=180 - en["angle"]) * plate), print_dir / "p4_7b_front_plate_print",
      ["step", "stl", "3mf"])
write(body, print_dir / "p4_7b_body_print", ["step", "stl", "3mf"])
write(test_frame, print_dir / "p4_7b_cutout_test_frame", ["step", "stl", "3mf"])
