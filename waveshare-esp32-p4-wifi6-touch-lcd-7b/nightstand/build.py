"""Nightstand stand ("Stem"): the display in a near-upright case on a serrated
hinge, over a low base with a short tower behind the screen. The speaker lies in
the tower facing up, under a slot grille in the tower lid.

    pip install build123d pyyaml
    python build.py [params.yaml] [output_dir]

Defaults: params.yaml next to this script (merged over ../common/common.yaml),
output into ./step and ./print.

World: X across (+ right seen from the front), Y depth (+ back), Z up from the
nightstand. Parts are modelled with the case upright (screen face at Y = 0);
tilt() leans the case back about the hinge axis.
"""

import math
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / "common"))

from enclosure_lib import *  # noqa: E402,F403

P = load_params(Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].endswith(".yaml") else here / "params.yaml")
g = Geo(P)
dp, en, sp, cp, ca = P["display"], P["enclosure"], P["speaker"], P["clamps"], P["case"]
hg, kb, ba, gr, up, wr = P["hinge"], P["knob"], P["base"], P["grille"], P["usb_port"], P["wire"]
wall, t = g.wall, g.t

# --- layout ---------------------------------------------------------------------------
W = 2 * (g.wx + en["border"])                       # case width
L = 2 * g.wy + 2 * en["border"]                     # case height
s_w = en["border"] + g.wy                           # window centre above the case bottom
s_g = s_w - g.va_up                                 # glass centre
D_case = g.clamp_back + ca["rear_clearance"] + wall  # screen face to case back

bw = ba["wall"]
z_fi = bw                                           # base floor top
z_lid = z_fi + ba["deck_h"]                         # deck lid underside = top of the deck walls
deck_top = z_lid + ba["deck_lid_t"]
g.h0 = Z_cb = deck_top + ca["bottom_gap"]           # case bottom, upright

R_k = hg["knuckle_r"]
Y_h = D_case + hg["gap"] + R_k                      # hinge axis
Z_h = Z_cb + hg["height"]

Y_tf = D_case + ba["tower_gap"]                     # tower front face
Y_tw = Y_tf + bw                                    # back of the tower front wall
sw, sh, sd = sp["width"], sp["height"], sp["depth"]
Y_g0 = Y_h + max(R_k, kb["diameter"] / 2) + gr["clear"]   # grille slots' front ends
Y_sc = Y_g0 + gr["length"] / 2                      # speaker centre, under the slots
z_tl = ba["tower_h"]                                # tower lid underside
z_tt = z_tl + ba["tower_lid_t"]
z_sf = z_tl - ba["speaker_gasket"]                  # speaker face, up
x_ti = sw / 2 + ba["tower_side_room"]               # tower interior half-width
x_to = x_ti + bw
Y_back = Y_sc + sh / 2 + ba["tower_rear_room"] + bw  # back of the base
X_b = ba["width"] / 2
Y_fr = ba["front"]

ears = speaker_ears(sp)
z_ear = z_sf - sp["ear_front"] - sp["ear_t"]        # underside of the ears = post tops

assert z_tt <= Z_h - R_k - 1.0, "tower lid too close to the hinge knuckles"
assert z_sf - sd > z_fi + 5, "speaker too close to the floor"
assert Y_sc - sh / 2 >= Y_tw + 8, "no room for the wires in front of the speaker"

# hinge stack across X, centred: tower knuckle, teeth, case knuckle, then the knob
tooth_h = R_k * math.tan(math.pi / hg["teeth"])     # tooth height at the knuckle edge
stack = hg["tower_w"] + tooth_h + hg["face_gap"] + hg["case_w"]
xt0 = -stack / 2                                    # tower knuckle: left face (nut pocket)
xt1 = xt0 + hg["tower_w"]                           # tower knuckle: toothed face
xc0 = xt1 + tooth_h + hg["face_gap"]                # case knuckle: base of its teeth
xc1 = xc0 + hg["case_w"]                            # case knuckle: outer face, under the knob


def tilt(shape, deg):
    """Lean a case part back by `deg` about the hinge axis."""
    return Pos(0, Y_h, Z_h) * (Rot(X=-deg) * (Pos(0, -Y_h, -Z_h) * shape))


def labelled(shape, name):
    shape.label = name
    return shape


# --- hinge teeth ---------------------------------------------------------------------------

def tooth_ring(n, r_out, r_in):
    """Radial V teeth on the plane z = 0, pointing +z, one ridge on +x: n tetrahedra
    with their apex on the axis, so the flanks lean 45 deg at every radius (for a
    90 deg tooth). Returns (teeth, mate). The mate is the complement of the teeth
    in a ring of their full height, in its own frame (z = 0 toward the teeth), so
    placed a face gap further out it meshes. Both are trimmed by a 45 deg cone at
    the rim, so no tooth end faces down whichever way the knuckle prints."""
    a = math.pi / n
    h = r_out * math.tan(a)
    teeth = []
    for k in range(n):
        c = 2 * a * k
        O = Vector(0, 0, 0)
        A = Vector(r_out * math.cos(c - a), r_out * math.sin(c - a), 0)
        B = Vector(r_out * math.cos(c + a), r_out * math.sin(c + a), 0)
        C = Vector(r_out * math.cos(c), r_out * math.sin(c), h)
        faces = [Face(Wire.make_polygon(pts, close=True)) for pts in
                 ([O, B, A], [O, A, C], [O, C, B], [A, B, C])]
        teeth.append(Solid(Shell(faces)))
    ring = Cylinder(r_out, h, align=(CENTER, CENTER, MIN))
    if r_in > 0:
        ring -= Cylinder(r_in, 3 * h)
    solid = (Part() + teeth) & ring
    r_c = r_out * math.cos(a)                       # the teeth's chord ends
    trimmed = solid & Cone(r_c, r_c - h, h, align=(CENTER, CENTER, MIN))
    mate = (ring - solid) & Cone(r_c - h, r_c, h, align=(CENTER, CENTER, MIN))
    return trimmed, mate


TEETH, MATE = tooth_ring(hg["teeth"], R_k, hg["tooth_r_in"])


def soft_edges(part, edges, n, level, c, r):
    """Round the perimeter `edges` of a face that lies on the print bed: a 45 deg
    chamfer `c`, then a fillet `r` where the chamfer meets the sides, so no face is
    flatter than 45 deg. `n` is the face's outward normal, `level` its position
    along it."""
    n = Vector(*n)
    orig = Compound(list(edges))
    part = chamfer(list(edges), c)
    seam = [e for e in part.edges()
            if abs(e.center().dot(n) - (level - c)) < 0.01 and e.distance_to(orig) < 1.5 * c + 0.05]
    return fillet(seam, r)


sn = P["snap"]
SNAP_E = sn["barb"] + sn["ridge"] - sn["gap"]       # barb / ridge overlap = insertion deflection


def snap_frame(root, out, along):
    """Plane at a snap arm's root on its outer face: x toward the wall, z along the arm."""
    return Plane(origin=root, x_dir=out, z_dir=along)


def snap_arm(frame, w=None, length=None, barb=None):
    """Cantilever arm from the root plane along +z, outer face at x = 0, with a 45 deg
    barb toward +x whose tip-most point is `length` from the root."""
    w = w or sn["arm_w"]
    length = length or sn["arm_l"]
    b = barb or sn["barb"]
    arm = Pos(-sn["arm_t"] / 2, 0, length / 2) * Box(sn["arm_t"], w, length + 0.02)
    tooth = extrude(Plane.XZ * Polygon((0, length - 2 * b), (b, length - b), (0, length), align=None),
                    amount=w / 2, both=True)
    return frame.location * (arm + tooth)


def snap_ridge(frame, w=None, length=None):
    """The wall ridge an arm built on the same frame snaps behind: 45 deg flanks,
    its tip-side flank flush against the barb's root-side flank."""
    w = (w or sn["arm_w"]) + 2
    length = length or sn["arm_l"]
    g, h = sn["gap"], sn["ridge"]
    z = length - sn["barb"] - SNAP_E                  # ridge apex along the arm
    tri = Polygon((g + 0.3, z - h - 0.3), (g, z - h), (g - h, z), (g, z + h), (g + 0.3, z + h + 0.3), align=None)
    return frame.location * extrude(Plane.XZ * tri, amount=w / 2, both=True)


def plate_snaps():
    """Frames (plate frame) of the front plate's snaps: arms run back from the plate's
    back face, a snap gap inside the shell's walls."""
    xw, s0, s1 = W / 2 - wall, wall, L - wall
    z0, back = -t, (0, 0, -1)
    frames = []
    for sx in (-1, 1):
        for s_ in ca["snaps_s"]:
            frames.append(snap_frame((sx * (xw - sn["gap"]), s_, z0), (sx, 0, 0), back))
    for x_ in ca["snaps_x"]:
        frames.append(snap_frame((x_, s0 + sn["gap"], z0), (0, -1, 0), back))
        frames.append(snap_frame((x_, s1 - sn["gap"], z0), (0, 1, 0), back))
    return frames


def deck_snaps():
    """Frames (world) of the deck lid's snaps: arms run down from the lid's underside."""
    xw, yf, down = X_b - bw, Y_fr + bw, (0, 0, -1)
    frames = []
    for sx in (-1, 1):
        for y_ in ba["lid_snaps_y"]:
            frames.append(snap_frame((sx * (xw - sn["gap"]), y_, z_lid), (sx, 0, 0), down))
    for x_ in ba["lid_snaps_x"]:
        frames.append(snap_frame((x_, yf + sn["gap"], z_lid), (0, -1, 0), down))
    return frames


def outer_face(part, axis, value):
    """The face of `part` normal to `axis` (X, Y or Z) at `value`."""
    k = "XYZ".index(axis)
    return next(f for f in part.faces().filter_by(getattr(Axis, axis))
                if abs(tuple(f.center())[k] - value) < 0.01)


def face_plane(x, side):
    """Plane on the knuckle face at x, normal pointing to +X (side = 1) or -X,
    local x along world +Y so that a ridge sits on the knuckle's front."""
    return Plane(origin=(x, Y_h, Z_h), x_dir=(0, 1, 0), z_dir=(side, 0, 0))


# --- case: front plate, back shell, hinge bracket ---------------------------------------

def build_plate():
    """Front plate in its own frame (x across, y up the screen, z out of the face)."""
    col_x, col_s, gap = cp["column"], cp["column_s"], cp["column_gap"]
    col_cx = g.pw / 2 + gap + col_x / 2
    assert g.gx + col_cx + col_x / 2 <= W / 2 - wall - 0.2, "side border too narrow for the clamp columns"
    columns = []
    for sx in (-1, 1):
        for hy in g.hole_ys:
            hs = s_g + hy
            shift = cp["column_shift"] if hy > 0 else -cp["column_shift"]
            columns.append((g.gx + sx * g.hole_x, hs, g.gx + sx * col_cx, hs + shift))
    plate = facade_plate(g, W, L, s_g)
    plate = add_clamp_columns(plate, g, [(cx, cs) for _, _, cx, cs in columns], (col_x, col_s))
    for fr in plate_snaps():
        plate += snap_arm(fr)
    with BuildSketch() as outline:                  # rounded corners seen from the front
        with Locations((0, L / 2)):
            RectangleRounded(W, L, ca["corner_r"])
    env = Pos(0, 0, -50) * extrude(outline.sketch, amount=50)
    c, r = ca["soft_edge"]                          # soft front edge (on the bed when printed)
    env = soft_edges(env, outer_face(env, "Z", 0).edges(), (0, 0, 1), 0, c, r)
    return plate & env, columns


def build_shell():
    """Back shell (world, upright): side walls from the plate back to the back panel.
    Printed on its back panel, so sideways holes point toward the screen (-Y)."""
    x0, z0, z1 = W / 2, Z_cb, Z_cb + L
    rc = ca["corner_r"]

    def prism(y0, y1, inset):
        with BuildSketch(Plane(origin=(0, y0, z0 + L / 2), x_dir=(1, 0, 0), z_dir=(0, 1, 0))) as sk:
            RectangleRounded(W - 2 * inset, L - 2 * inset, rc - inset)
        return extrude(sk.sketch, amount=y1 - y0)

    c, r = ca["soft_edge"]                          # soft back edge (on the bed when printed)
    shell = prism(t, D_case, 0)
    shell = soft_edges(shell, outer_face(shell, "Y", D_case).edges(), (0, 1, 0), D_case, c, r)
    shell -= prism(t - 1, D_case - wall, wall)
    for fr in plate_snaps():                         # ridges the front plate snaps behind
        shell += g.to_world(snap_ridge(fr))
    n = ca["vent_slots"]
    for i in range(n):                               # vent slots near the top of the back panel
        shell -= Pos((i - (n - 1) / 2) * 8, D_case - wall / 2, z1 - 22) * Box(3, 3 * wall, 24)
    # wire pass facing the tower front's, for the USB-C cable and the speaker lead
    shell -= extrude(wire_hole(Plane.XZ.offset(-(D_case + 0.01)), wr["x"], wr["z0"]), amount=wall + 0.5)
    for dx, dz in hg["plate_screws"]:                # hinge bracket screws, M3 clearance
        shell -= Pos(dx, D_case - wall / 2, Z_h + dz) * Cylinder(
            P["screws"]["side_clear"] / 2, 3 * wall, rotation=(90, 0, 0))
    return labelled(shell, "back_shell")


def knuckle(x0, x1):
    """Lug from the case back to the axis plus the round knuckle, between x0 < x1."""
    w = x1 - x0
    lug = Pos((x0 + x1) / 2, D_case, Z_h - R_k) * Box(w, Y_h - D_case, 2 * R_k,
                                                            align=(CENTER, MIN, MIN))
    disc = Pos((x0 + x1) / 2, Y_h, Z_h) * Cylinder(R_k, w, rotation=(0, 90, 0))
    return lug + disc


def build_case_bracket():
    """Hinge bracket screwed to the case back: a plate and the case knuckle, whose
    left face carries the mating teeth. Printed on its right end, teeth up (up = -X):
    the teeth print face up and the lug grows with the plate in every layer."""
    z0, z1 = hg["plate_z"]
    br = Pos(0, D_case, Z_h + z0) * Box(2 * xc1, hg["plate_t"], z1 - z0, align=(CENTER, MIN, MIN))
    corners = br.edges().filter_by(Axis.Y)
    br = fillet(corners.filter_by_position(Axis.X, -xc1 - 1, 0), hg["plate_corner_r"])
    br = chamfer(br.edges().filter_by(Axis.Y).filter_by_position(Axis.X, xc1 - 0.01, xc1 + 0.01),
                 hg["plate_corner_r"])           # bed side: 45 deg, no overhang
    # room for the tower knuckle and its fin: the knuckle sweeps a cylinder, the fin
    # rises from below
    xl, xr = -xc1 - 1, xc0 - 0.01
    br -= Pos((xl + xr) / 2, Y_h, Z_h) * Cylinder(R_k + 0.6, xr - xl, rotation=(0, 90, 0))
    br -= Pos((xl + xr) / 2, D_case - 1, Z_h + z0 - 1) * Box(xr - xl, hg["plate_t"] + 2, -z0 + 1,
                                                           align=(CENTER, MIN, MIN))
    br += knuckle(xc0, xc1)
    # mating teeth: the complement of the tower knuckle's teeth, a face gap away
    br += face_plane(xt1 + hg["face_gap"], 1).location * MATE
    into_plate = Plane(origin=(0, D_case - 0.01, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    for dx, dz in hg["plate_screws"]:               # sideways in print: teardrops, point up (-X)
        br -= teardrop(into_plate, (dx, D_case - 0.01, Z_h + dz), hg["pilot"] / 2,
                       hg["pilot_depth"] + 0.01, up=(-1, 0, 0))
    # bolt hole: upright in print, so plain round
    br -= Pos(0, Y_h, Z_h) * Cylinder(hg["bolt_hole"] / 2, 2 * xc1 + 2, rotation=(0, 90, 0))
    return labelled(br, "case_hinge")


def build_knob():
    """Knurled thumb knob on the right end of the bolt, the bolt's hex head in its pocket."""
    d, th = kb["diameter"], kb["thickness"]
    knob = Cylinder(d / 2, th, align=(CENTER, CENTER, MIN))
    for k in range(kb["knurls"]):
        a = 2 * math.pi * k / kb["knurls"]
        knob -= Pos(d / 2 * math.cos(a), d / 2 * math.sin(a), 0) * Cylinder(kb["knurl_r"], 3 * th)
    knob = chamfer(knob.edges().group_by(Axis.Z)[-1], 0.6)  # top rim: grip edge
    knob -= Cylinder(hg["bolt_hole"] / 2, 3 * th)
    with BuildSketch(Plane.XY.offset(kb["base_t"])) as hx:
        RegularPolygon(kb["head_af"] / math.sqrt(3), 6)
    knob -= extrude(hx.sketch, amount=th)
    return knob                                     # print frame: axis Z, pocket up


def place_knob(knob):
    """World: the knob's base on the case knuckle's outer face, axis along +X."""
    return labelled(Pos(xc1, Y_h, Z_h) * (Rot(Y=90) * knob), "knob")


def hardware():
    """M4 bolt and nut stand-ins on the hinge axis."""
    hx_r = 7.0 / math.sqrt(3)
    x_head = xc1 + kb["base_t"]
    bolt_len = hg["bolt"][1]
    with BuildSketch(Plane.XY.offset(kb["base_t"])) as hd:   # knob frame, as its pocket
        RegularPolygon(hx_r, 6)
    bolt = Pos(xc1, Y_h, Z_h) * (Rot(Y=90) * extrude(hd.sketch, amount=2.8))
    bolt += Pos(x_head - bolt_len / 2, Y_h, Z_h) * Cylinder(1.95, bolt_len, rotation=(0, 90, 0))
    x_nut = xt0 + hg["nut_pocket"]                  # nut pulled to the bottom of its pocket
    with BuildSketch(Plane(origin=(x_nut, Y_h, Z_h), x_dir=(0, 0, 1), z_dir=(-1, 0, 0))) as nt:
        RegularPolygon(hx_r, 6)
    nut = extrude(nt.sketch, amount=hg["nut_t"])
    nut -= Pos(x_nut, Y_h, Z_h) * Cylinder(2.0, 20, rotation=(0, 90, 0))
    return [labelled(bolt, "m4_bolt"), labelled(nut, "m4_nut")]


# --- base: body, deck lid, tower lid -------------------------------------------------------
#
# The base body prints upright and open-topped: floor, outer walls up to the deck,
# the tower's walls, the speaker posts and the lid screw bosses. Its roofs are
# separate so nothing bridges: the deck lid (printed top face down, snap arms up)
# and the tower lid with the grille and the hinge's tower knuckle (printed on its
# underside). The speaker sits face up on the posts, held down by the tower lid.

lid_t = ba["deck_lid_t"]
pil, pil_d = ba["pilot"], ba["pilot_depth"]
rb = ba["tower_boss_d"] / 2
tb_x = x_ti - rb + 0.4                              # tower lid screw bosses, in the corners,
tb_ys = (Y_tw + rb - 0.4, Y_back - bw - rb + 0.4)    # set into the walls (not tangent)
assert tb_x - rb >= sw / 2 + 0.5, "lid screw boss hits the speaker"
assert tb_x + 3.2 <= x_to - ba["tower_lid_edge_r"], "countersink runs into the lid's rounded edge"
Y_spk0 = Y_sc - sh / 2                              # speaker front
z_w = wr["z0"] + wr["ribbon"][1] / 2 + 0.5          # ribbon height through the wire holes


def wire_hole(plane, x, z0):
    """Wire pass: straight sides, then a 45 deg roof to a point (no bridge in print)."""
    w, side = wr["width"], wr["side"]
    with BuildSketch(plane) as sk:
        Polygon((x - w / 2, z0), (x + w / 2, z0), (x + w / 2, z0 + side), (x, z0 + side + w / 2),
                (x - w / 2, z0 + side), align=None)
    return sk.sketch


def ribbon(points, normals, w, t):
    """Flat cable stand-in through `points`: one strip per segment, lying flat
    against the plane whose normal is given for that segment."""
    pts = [Vector(*p) for p in points]
    out = Part()
    for a, b, n in zip(pts, pts[1:], normals):
        v = b - a
        d = v.normalized()
        strip = Box(w, t, v.length + t, align=(CENTER, CENTER, CENTER))
        out += Plane(origin=(a + b) * 0.5, x_dir=Vector(*n).cross(d), z_dir=d).location * strip
    return out


def route_length(points):
    return sum((Vector(*b) - Vector(*a)).length for a, b in zip(points, points[1:]))


def footprint(z0, z1, inset=0.0):
    """The base outline (rounded corners) between heights z0 and z1."""
    r = ba["corner_r"] - inset
    w, d = 2 * X_b - 2 * inset, Y_back - Y_fr - 2 * inset
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        with Locations((0, (Y_fr + Y_back) / 2)):
            RectangleRounded(w, d, r)
    return extrude(sk.sketch, amount=z1 - z0)


def countersink_up(x, y, z_top, depth):
    """M3 countersunk screw from above: clearance hole plus a 90 deg countersink."""
    c = Pos(x, y, z_top + 0.01) * Cylinder(P["screws"]["side_clear"] / 2, depth + 0.02,
                                           align=(CENTER, CENTER, MAX))
    c += Pos(x, y, z_top + 0.01) * Cone(1.5, 3.2, 1.7 + 0.01, align=(CENTER, CENTER, MAX))
    return c


def build_base():
    base = footprint(0, z_lid)
    c, r = ba["floor_edge"]                         # soft bottom edge (on the bed)
    base = soft_edges(base, outer_face(base, "Z", 0).outer_wire().edges(), (0, 0, -1), 0, c, r)
    base -= footprint(z_fi, z_lid + 1, bw)
    # tower: front, side and back walls from the floor up to the tower lid
    tower = Pos(0, Y_tf, z_fi - 0.01) * Box(2 * x_to, Y_back - Y_tf, z_tl - z_fi + 0.01,
                                            align=(CENTER, MIN, MIN))
    tower = fillet(tower.edges().filter_by(Axis.Z).filter_by(lambda e: abs(e.center().Y - Y_tf) < 0.01),
                   ba["tower_corner_r"])
    base += tower
    base -= Pos(0, Y_tw, z_fi) * Box(2 * x_ti, Y_back - bw - Y_tw, z_tl, align=(CENTER, MIN, MIN))
    # speaker posts from the floor to its ears, a spigot into each ear hole
    for ex, ey in ears:
        base += Pos(ex, Y_sc + ey, z_fi - 0.01) * Cylinder(sp["standoff_d"] / 2, z_ear - z_fi + 0.01,
                                                          align=(CENTER, CENTER, MIN))
        base += Pos(ex, Y_sc + ey, z_ear - 0.01) * Cylinder(sp["spigot_d"] / 2, sp["spigot_h"] + 0.01,
                                                           align=(CENTER, CENTER, MIN))
    # tower lid screw bosses in the four corners
    for sx in (-1, 1):
        for y_ in tb_ys:
            base += Pos(sx * tb_x, y_, z_fi - 0.01) * Cylinder(rb, z_tl - z_fi + 0.01, align=(CENTER, CENTER, MIN))
            base -= Pos(sx * tb_x, y_, z_tl + 0.01) * Cylinder(pil / 2, pil_d, align=(CENTER, CENTER, MAX))
    # wire pass in the tower front, facing the case's
    base -= extrude(wire_hole(Plane.XZ.offset(-(Y_tw + 0.01)), wr["x"], wr["z0"]), amount=bw + 0.02)
    for fr in deck_snaps():                         # ridges the deck lid snaps under
        base += snap_ridge(fr)
    base = usb_port_mount(base, up, Y_back, bw)
    return labelled(base, "base")


def build_deck_lid():
    """Deck top over the front and both wings; snap arms under it clip behind ridges
    on the base's walls. Printed top face down."""
    lid = footprint(z_lid, z_lid + lid_t)
    c, r = ba["deck_edge"]                          # soft top edge (on the bed when printed)
    lid = soft_edges(lid, outer_face(lid, "Z", z_lid + lid_t).outer_wire().edges(), (0, 0, 1),
                     z_lid + lid_t, c, r)
    lid -= Pos(0, Y_tf, z_lid - 1) * Box(2 * x_to, Y_back, lid_t + 2, align=(CENTER, MIN, MIN))
    for fr in deck_snaps():
        lid += snap_arm(fr)
    return labelled(lid, "deck_lid")


def build_tower_lid():
    """Tower lid with the speaker grille, and the hinge's tower knuckle on a fin, teeth
    on its right face and the nut captured in its left face. Printed on its underside."""
    tl = Pos(0, Y_tf, z_tl) * Box(2 * x_to, Y_back - Y_tf, z_tt - z_tl, align=(CENTER, MIN, MIN))
    tl = fillet(tl.edges().filter_by(Axis.Z).filter_by(lambda e: abs(e.center().Y - Y_tf) < 0.01),
                ba["tower_corner_r"])
    tl = fillet(outer_face(tl, "Z", z_tt).outer_wire().edges(), ba["tower_lid_edge_r"])
    xm, w = (xt0 + xt1) / 2, xt1 - xt0
    # the fin runs down the full lid thickness, so its front stays flush over the soft edge
    tl += Pos(xm, Y_h, z_tl) * Box(w, 2 * R_k, Z_h - z_tl, align=(CENTER, CENTER, MIN))
    tl += Pos(xm, Y_h, Z_h) * Cylinder(R_k, w, rotation=(0, 90, 0))
    tl += face_plane(xt1, 1).location * TEETH
    tl -= teardrop(Plane.YZ.offset(xm), (xm, Y_h, Z_h), hg["bolt_hole"] / 2, w / 2 + 2, up=(0, 0, 1), both=True)
    # captured nut from the left face: a vertex toward print-up (+Z) under a 45 deg roof
    rn = hg["nut_af"] / math.sqrt(3)
    with BuildSketch(Plane(origin=(xt0 - 0.01, Y_h, Z_h), x_dir=(0, 0, 1), z_dir=(1, 0, 0))) as nut:
        RegularPolygon(rn, 6, rotation=0)
        vx, vy = rn / 2, rn * math.sqrt(3) / 2      # upper side vertices
        Polygon((vx, vy), (vx + vy, 0), (vx, -vy), align=None)
    tl -= extrude(nut.sketch, amount=hg["nut_pocket"] + 0.01)
    for sx in (-1, 1):
        for y_ in tb_ys:
            tl -= countersink_up(sx * tb_x, y_, z_tt, z_tt - z_tl)
    pitch, n = gr["slot"] + gr["bar"], gr["slots"]
    assert (n - 1) * pitch + gr["slot"] <= sw - 2, "grille wider than the speaker face"
    with BuildSketch(Plane.XY.offset(z_tl - 0.01)) as sk:
        with Locations(*[((i - (n - 1) / 2) * pitch, Y_sc) for i in range(n)]):
            SlotOverall(gr["length"], gr["slot"], rotation=90)
    tl -= extrude(sk.sketch, amount=z_tt - z_tl + 0.02)
    return labelled(tl, "tower_lid")


def usb_plug_frame():
    """The 90 deg plug in the board's left-edge port (upright): edge x, metal centre y, z."""
    return g.gx - dp["pcb_w"] / 2, g.f + 10.4, Z_cb + s_g + g.usb_y   # as the shared plug stand-in


def usb_plug():
    """The cable's 90 deg USB-C plug: the head beside the board, and the metal up to the
    board edge (the rest is inside the port, part of the board stand-in)."""
    xe, yc, zc = usb_plug_frame()
    (hw, hd, hh), (mw, mt, _) = wr["plug"], wr["plug_metal"]
    head = Pos(xe - wr["plug_gap"], yc - wr["plug_front"], zc) * Box(
        hh, hd, hw, align=(MAX, MIN, CENTER))
    metal = Pos(xe - wr["plug_gap"] - 0.1, yc, zc) * Box(wr["plug_gap"], mt, mw, align=(MIN, CENTER, CENTER))
    return labelled(head + metal, "usb_plug")


def plug_exit():
    """Where the ribbon leaves the plug head: its back face, on the metal's side."""
    xe, yc, zc = usb_plug_frame()
    w, t_ = wr["ribbon"]
    return (xe - wr["plug_gap"] - t_ / 2 - 0.5, yc - wr["plug_front"] + wr["plug"][1] + t_ / 2 + 0.1, zc)


def cable_routes():
    """The USB-C ribbon's route: in the case, from the board's plug back behind the
    board and down the inside of the back panel to the wire pass; in the base, from
    the tower's wire pass down the inside of the tower front and back along the floor
    to the connector. Points, and per segment the normal of the plane it lies flat on."""
    w, t_ = wr["ribbon"]
    x0, y0, z_plug = plug_exit()
    y_run = D_case - wall - t_ / 2 - 0.3             # flat on the inside of the back panel
    in_case = [(x0, y0, z_plug), (x0, y_run, z_plug), (wr["x"], y_run, z_w + w),
               (wr["x"], y_run, z_w), (wr["x"], D_case - t_, z_w)]
    case_n = [(1, 0, 0), (0, 1, 0), (0, 1, 0), (0, 0, 1)]
    z_f = z_fi + t_ / 2 + 0.2
    y_d = Y_tw + t_ / 2 + 2.0                         # down the inside of the tower front
    y_sock = usb_port_stand_in(P, Y_back).bounding_box().min.Y   # the connector's back end
    in_base = [(wr["x"], Y_tf + t_, z_w), (wr["x"], y_d, z_w), (wr["x"], y_d, z_f),
               (up["x"], y_d + 12, z_f), (up["x"], y_sock - 3, z_f)]
    base_n = [(0, 0, 1), (0, 1, 0), (0, 0, 1), (0, 0, 1)]
    return (in_case, case_n), (in_base, base_n)


def cables():
    """USB-C ribbon stand-ins, in the case and in the base. The loop across the gap
    between the wire passes changes with the tilt and isn't modelled."""
    w, t_ = wr["ribbon"]
    (pc, nc), (pb, nb) = cable_routes()
    return (labelled(ribbon(pc, nc, w, t_), "usb_cable_case"),
            labelled(ribbon(pb, nb, w, t_), "usb_cable_base"))


def gasket():
    """Foam tape on the speaker face's rim, compressed under the tower lid."""
    t_ = ba["speaker_gasket"]
    ring = Pos(0, Y_sc, z_sf) * Box(sw, sh, t_, align=(CENTER, CENTER, MIN))
    ring -= Pos(0, Y_sc, z_sf) * Box(sw - 6, sh - 6, 3 * t_)
    return labelled(ring, "speaker_gasket")


# --- assembly -------------------------------------------------------------------------------

def build_all():
    """Every part in world position with the case upright, plus print orientations."""
    plate_pf, columns = build_plate()
    tab = clamp_tab(g, [math.hypot(cx - hx, cs - hs) for hx, hs, cx, cs in columns])
    knob = build_knob()
    case = [labelled(g.to_world(plate_pf), "front_plate"), build_shell(), build_case_bracket(),
            place_knob(knob)]
    bolt, nut = hardware()                          # the nut stays in the tower knuckle
    cable_case, cable_base = cables()
    stand_ins = [d for d in display_stand_ins(g, s_g) if d.label != "usb_plug"]   # straight plug
    case_hw = [bolt, cable_case, usb_plug()] + stand_ins + place_tabs(g, tab, s_g, columns)
    base = [build_base(), build_deck_lid(), build_tower_lid()]
    speaker = labelled(Pos(0, Y_sc, z_sf) * speaker_stand_in(sp, ears), "speaker")
    base_hw = [speaker, gasket(), usb_port_stand_in(P, Y_back), nut, cable_base]
    front_plate, shell, bracket, _ = case
    body, deck, tower_lid = base
    prints = {                                      # name: (part in print orientation, how)
        "front_plate": (on_bed(Rot(X=180) * plate_pf), "face down"),
        "back_shell": (on_bed(Rot(X=-90) * shell), "back panel down"),
        "case_hinge": (on_bed(Rot(Y=90) * bracket), "outer face down, teeth up"),
        "knob": (on_bed(knob), "flat face down, pocket up"),
        "base": (on_bed(body), "upright"),
        "deck_lid": (on_bed(Rot(X=180) * deck), "top face down, snap arms up"),
        "tower_lid": (on_bed(tower_lid), "underside down, knuckle up"),
        "clamp_tab": (on_bed(tab), "flat"),
    }
    return case, case_hw, base, base_hw, prints


def hinge_test(prints):
    """Quick print of the hinge: the case bracket and knob as they are, and the tower
    lid's knuckle and fin on a small piece of the lid. Checks the tooth mesh, the
    bolt, the captured nut and the knob."""
    tl = build_tower_lid() & Pos((xt0 + xt1) / 2, Y_h, z_tl) * Box(xt1 - xt0 + 16, 2 * R_k + 8, 100,
                                                                    align=(CENTER, CENTER, MIN))
    return on_bed(tl), prints["case_hinge"][0], prints["knob"][0]


def snap_test():
    """Quick print of one plate-to-shell snap: a corner of the plate's border with its
    arm, and the matching piece of shell side wall with its ridge, each in its print
    orientation. Checks how firmly the snap holds and that it releases."""
    s_ = ca["snaps_s"][0]
    plate_pf, _ = build_plate()
    keep = Pos(W / 2, s_, 0) * Box(24, 20, 60, align=(MAX, CENTER, MAX))
    piece = on_bed(Rot(X=180) * (plate_pf & keep))
    z = Z_cb + s_
    wall_piece = build_shell() & Pos(W / 2, 0, z) * Box(14, 200, 20, align=(MAX, CENTER, CENTER))
    return piece, on_bed(Rot(X=-90) * wall_piece)


def layout(parts, gap=8.0, width=320.0):
    """Lay print-orientation parts out in rows on the bed plane, centred."""
    out, x, y, row_h = [], 0.0, 0.0, 0.0
    for p in sorted(parts, key=lambda s: -s.bounding_box().size.Y):
        bb = p.bounding_box()
        if x and x + bb.size.X > width:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        out.append(Pos(x - bb.min.X, y - bb.min.Y, 0) * p)
        x += bb.size.X + gap
        row_h = max(row_h, bb.size.Y)
    return out


if __name__ == "__main__":
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else here
    step_dir, print_dir, test_dir = out_dir / "step", out_dir / "print", out_dir / "test-prints"
    name = "p4_7b_nightstand"
    case, case_hw, base, base_hw, prints = build_all()
    t_max = P["tilt"]["max"]
    for s in case + base:                           # before the assemblies: a part that has a
        write(s, step_dir / f"{name}_{s.label}", ["step"])   # parent compound won't export alone
    write(Compound(children=case + case_hw + base + base_hw), step_dir / f"{name}_assembly", ["step"])
    write(Compound(children=[tilt(s, t_max) for s in case + case_hw] + base + base_hw),
          step_dir / f"{name}_assembly_tilt{t_max}", ["step"])
    write(Compound(children=case + base), step_dir / f"{name}_enclosure_only", ["step"])
    for key, (part, how) in prints.items():
        if key != "clamp_tab":                      # the tabs go out as a set of four below
            write(part, print_dir / f"{name}_{key}_print", ["step", "stl", "3mf"])
    tab = prints["clamp_tab"][0]
    tw = tab.bounding_box().size.X
    tabs4 = on_bed(Compound(children=[Pos(i * (tw + 4), 0, 0) * tab for i in range(4)]))
    write(tabs4, print_dir / f"{name}_clamp_tabs_print", ["step", "stl", "3mf"])
    # every printed part in one Bambu Studio project, one part per plate
    every = [(k.replace("_", " ").capitalize(), p) for k, (p, _) in prints.items() if k != "clamp_tab"]
    every.append(("Clamp tabs", tabs4))
    plates = []
    for label, p in every:
        c = p.bounding_box().center()
        plates.append((label, [(label, Pos(-c.X, -c.Y, 0) * p)]))
    print_dir.mkdir(parents=True, exist_ok=True)
    write_bambu_project(plates, print_dir / f"{name}_all_parts.3mf", template=TEMPLATE, settings=PRINT)
    print("wrote", print_dir / f"{name}_all_parts.3mf")
    write(Compound(children=layout(list(hinge_test(prints)))), test_dir / f"{name}_hinge_test", ["step", "stl", "3mf"])
    write(Compound(children=layout(list(snap_test()))), test_dir / f"{name}_snap_test", ["step", "stl", "3mf"])
    H = Z_cb + L
    print(f"case {W:.1f} x {L:.1f} x {D_case:.1f}; base {2 * X_b:.1f} W x {Y_back - Y_fr:.1f} D; "
          f"{H:.1f} tall upright; hinge axis Y {Y_h:.2f} Z {Z_h:.2f}")
