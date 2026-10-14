"""Shared geometry and exporters for the Waveshare ESP32-P4-WIFI6-Touch-LCD-7B
enclosure variants.

Coordinates: world X across (+ = right seen from the front), Y depth (+ = back),
Z up. The front plate is modelled flat in its own frame -- x across, y up the
slope ("s"), z out of the front face (depth d behind the face is z = -d) -- and
placed with Geo.to_world().
"""

import math
import uuid
import zipfile
from pathlib import Path
from types import SimpleNamespace
from xml.sax.saxutils import quoteattr

import yaml
from build123d import *  # noqa: F403

COMMON = Path(__file__).resolve().parent
CENTER, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX


def load_params(variant_yaml):
    """common.yaml with the variant's params.yaml merged over it (per section)."""
    params = yaml.safe_load((COMMON / "common.yaml").read_text(encoding="utf-8"))
    for key, value in yaml.safe_load(Path(variant_yaml).read_text(encoding="utf-8")).items():
        if isinstance(value, dict) and isinstance(params.get(key), dict):
            params[key].update(value)
        else:
            params[key] = value
    return params


class Geo(SimpleNamespace):
    """Derived display/facade dimensions plus the plate -> world transform."""

    def __init__(self, P):
        dp, en = P["display"], P["enclosure"]
        th = math.radians(en["angle"])
        f = en["facade_t"]
        cl = en["pocket_clearance"]
        pcb_top = dp["glass_h"] / 2 - dp["pcb_top_inset"]
        pcb_bot = pcb_top - dp["pcb_h"]
        super().__init__(
            P=P, dp=dp, en=en, angle=en["angle"], co=math.cos(th), si=math.sin(th),
            wall=en["wall"], f=f, t=f + en["pocket_depth"], cl=cl,
            trim=en["pocket_trim_bottom"],
            pw=dp["glass_w"] + 2 * cl, ph=dp["glass_h"] + 2 * cl,
            # visible area is off-centre on the glass; the window is centred in
            # the plate, so the glass shifts by half the border difference
            gx=(dp["border_right"] - dp["border_left"]) / 2,
            va_up=(dp["border_bottom"] - dp["border_top"]) / 2,
            wx=dp["va_w"] / 2 + en["window_reveal"],
            wy=dp["va_h"] / 2 + en["window_reveal"],
            pcb_top=pcb_top, pcb_bot=pcb_bot, pcb_cy=(pcb_top + pcb_bot) / 2,
            hole_x=dp["pcb_w"] / 2 - dp["hole_inset"],
            hole_ys=[pcb_top - dp["hole_inset"], pcb_bot + dp["hole_inset"]],
            usb_y=pcb_bot + dp["usb_c_from_pcb_bottom"],
            z_se=-(f + dp["standoff_end"]),
            clamp_back=f + dp["standoff_end"] + P["clamps"]["tab_t"] + 2.5,  # incl. screw heads
            h0=None,
        )

    def Pw(self, s, d):
        """World (Y, Z) of plate point s up the slope, d behind the front face."""
        return (s * self.co + d * self.si, self.h0 + s * self.si - d * self.co)

    def to_world(self, shape):
        return Pos(0, 0, self.h0) * (Rot(X=self.angle) * shape)


# --- holes -----------------------------------------------------------------------------

def teardrop(plane, centre, r, length, up, both=False, taper=0.0):
    """Cutter for a hole that runs sideways when printed: a circle with a 45-degree
    point toward `up` (the print's up direction, as a world vector), so the roof of
    the hole is self-supporting instead of drooping. Extruded along the plane normal
    from `centre` (world point on the plane); `taper` shrinks it as it goes
    (used for countersinks)."""
    lc = plane.to_local_coords(Vector(*centre))
    ux, uy = Vector(*up).dot(plane.x_dir), Vector(*up).dot(plane.y_dir)
    tip = math.atan2(uy, ux)
    pts = [(r * math.cos(tip + s * math.pi / 4), r * math.sin(tip + s * math.pi / 4)) for s in (-1, 1)]
    with BuildSketch(plane) as sk:
        with Locations((lc.X, lc.Y)):
            Circle(r)
            Polygon(pts[0], (r * math.sqrt(2) * math.cos(tip), r * math.sqrt(2) * math.sin(tip)),
                    pts[1], (0, 0), align=None)
    return extrude(sk.sketch, amount=length, both=both, taper=taper)


# --- front plate ------------------------------------------------------------------

def facade_plate(g, W, L, s_g):
    """Plate with the glass pocket, bevelled window and mic holes (plate frame)."""
    f, t = g.f, g.t
    s_w = s_g + g.va_up
    plate = Box(W, L, t, align=(CENTER, MIN, MAX))
    plate -= Pos(g.gx, s_g + g.trim / 2, -f) * Box(g.pw, g.ph - g.trim, t, align=(CENTER, CENTER, MAX))
    plate -= Pos(0, s_w, 0) * Box(2 * g.wx, 2 * g.wy, 3 * f)
    c = g.en["window_chamfer"]
    with BuildSketch(Plane.XY.offset(-c)) as win:
        with Locations((0, s_w)):
            Rectangle(2 * g.wx, 2 * g.wy)
    plate -= extrude(win.sketch, amount=c + 1, taper=-45)
    mh = g.P["mic_holes"]
    for sx in (-1, 1):
        cx, cy = g.gx + sx * g.dp["mic_x"], s_g - g.ph / 2 - mh["below_opening"]
        pts = [(cx, cy)] + [(cx + mh["pitch"] * math.cos(math.radians(a)),
                             cy + mh["pitch"] * math.sin(math.radians(a))) for a in range(0, 360, 60)]
        for px, py in pts:
            plate -= Pos(px, py, 0) * Cylinder(mh["diameter"] / 2, 3 * t)
    return plate


def add_clamp_columns(plate, g, centres, size):
    """Columns (plate frame) whose tops sit flush with the display standoff ends."""
    cp = g.P["clamps"]
    col_h = -g.z_se - g.t
    for at in centres:
        plate += Pos(*at, -g.t + 0.5) * Box(*size, col_h + 0.5, align=(CENTER, CENTER, MAX))
        plate -= Pos(*at, g.z_se - 0.01) * Cylinder(
            cp["pilot"] / 2, cp["pilot_depth"], align=(CENTER, CENTER, MIN))
    return plate


def clamp_tab(g, reaches):
    """Tab with the standoff hole at the origin and a slot along +y covering `reaches`."""
    cp = g.P["clamps"]
    slot_mid = sum(reaches) / len(reaches)
    slot_sep = max(reaches) - min(reaches) + 0.2
    tw = cp["tab_w"]
    tab = Box(tw, slot_mid, cp["tab_t"], align=(CENTER, MIN, MAX))
    for y in (0, slot_mid):
        tab += Pos(0, y, 0) * Cylinder(tw / 2, cp["tab_t"], align=(CENTER, CENTER, MAX))
    tab -= Cylinder(cp["standoff_hole"] / 2, 3 * cp["tab_t"])
    with BuildSketch() as ts:
        with Locations((0, slot_mid)):
            SlotCenterToCenter(slot_sep, cp["column_slot"], rotation=90)
    tab -= extrude(ts.sketch, amount=3 * cp["tab_t"], both=True)
    return tab


def place_tabs(g, tab, s_g, columns):
    """World tabs: one per (hole_x, hole_s, column_x, column_s), pointing at its column."""
    tabs = []
    for hx, hs, cx, cs in columns:
        heading = math.degrees(math.atan2(cs - hs, cx - hx)) - 90
        placed = g.to_world(Pos(hx, hs, g.z_se) * (Rot(Z=heading) * tab))
        placed.label = "clamp_tab"
        tabs.append(placed)
    return tabs


def add_side_bosses(plate, g, W, boss_s):
    """Bosses for the M3 screws through the side walls; returns (plate, body cutters)."""
    sc, wall, t = g.P["screws"], g.wall, g.t
    bx1 = W / 2 - wall - 0.2
    bx0 = bx1 - 6
    boss_z = -(t + 4)
    body_cut = []
    head_r, clear_r = 3.2, sc["side_clear"] / 2
    for sx in (-1, 1):
        for sb in boss_s:
            plate += Pos(sx * (bx0 + bx1) / 2, sb, -t + 0.5) * Box(
                bx1 - bx0, 8, 8.5, align=(CENTER, CENTER, MAX))
            # pilot: the plate prints face-down, so "up" is away from the facade (-z)
            px = sx * (bx1 - 4)
            plate -= teardrop(Plane.YZ.offset(px), (px, sb, boss_z), sc["side_pilot"] / 2, 4.25,
                              up=(0, 0, -1), both=True)
            # clearance hole and countersink in the body, which prints upright (+Z)
            Y, Z = g.Pw(sb, -boss_z)
            xw = sx * (W / 2 - wall / 2)
            body_cut.append(teardrop(Plane.YZ.offset(xw), (xw, Y, Z), clear_r, 1.5 * wall,
                                     up=(0, 0, 1), both=True))
            outer = Plane(origin=(sx * (W / 2 + 0.01), 0, 0), x_dir=(0, 1, 0), z_dir=(-sx, 0, 0))
            body_cut.append(teardrop(outer, (sx * (W / 2 + 0.01), Y, Z), head_r, head_r - clear_r,
                                     up=(0, 0, 1), taper=45))
    return plate, body_cut


# --- body --------------------------------------------------------------------------

def top_cap(g, W, L, D):
    """Roof over the back of the body, printed as part of the front plate.

    Runs from the plate's top edge back over the back wall. With the plate printed
    face-down it rises at the plate angle, so it needs no supports, and the body
    stays open-topped. A rib under it locates it just inside the back wall.
    """
    wall, tan = g.wall, g.si / g.co
    Yc, Zc = L * g.co, g.h0 + L * g.si
    cap = extrude(Plane.YZ * Polygon((Yc, Zc), (D, Zc), (D, Zc - wall), (Yc + wall * tan, Zc - wall),
                                     align=None), amount=W / 2, both=True)
    rib_y = D - wall - 0.2
    cap += Pos(0, rib_y, Zc - wall + 0.01) * Box(W - 2 * wall - 0.4 - 2 * 8, 1.2, 2.0,
                                                 align=(CENTER, MAX, MAX))
    return cap


def body_shell(g, W, L, D, body_cut):
    """Open-topped hollow wedge under the plate, with feet, vents and the USB port or notch."""
    P, wall, co, tan = g.P, g.wall, g.co, g.si / g.co
    Yc, Zc = L * co, g.h0 + L * g.si
    # the top cap belongs to the front plate, so the body stops a wall below the top
    profile = Plane.YZ * Polygon((0, 0), (0, g.h0), (Yc, Zc), (Yc + wall * tan, Zc - wall),
                                 (D, Zc - wall), (D, 0), align=None)
    body = extrude(profile, amount=W / 2, both=True)
    body -= g.to_world(Box(W, L, g.t, align=(CENTER, MIN, MAX)))
    # cavity: floor, front lip, back and side walls are `wall` thick; open at the
    # top. The plate slab above already clears everything along the slope.
    body -= Pos(0, wall, wall) * Box(W - 2 * wall, D - 2 * wall, Zc, align=(CENTER, MIN, MIN))
    for cut in body_cut:
        body -= cut
    un = P["usb_notch"]
    if un["enabled"]:
        r = un["width"] / 2
        body -= Pos(un["x"], D - wall / 2, -1) * Box(un["width"], 3 * wall, un["height"] - r + 1,
                                                    align=(CENTER, CENTER, MIN))
        body -= Pos(un["x"], D - wall / 2, un["height"] - r) * Cylinder(r, 3 * wall, rotation=(90, 0, 0))
    up = P["usb_port"]
    if up["enabled"]:
        body = usb_port_mount(body, up, D, wall)
    for i in range(9):   # vertical vent slots: short bridges print cleanly
        body -= Pos((i - 4) * 8, D - wall / 2, Zc - 22) * Box(3, 3 * wall, 24)
    ft = P["feet"]
    for fx in (-1, 1):
        for fy in (ft["inset"], D - ft["inset"]):
            body -= Pos(fx * (W / 2 - ft["inset"]), fy, 0) * Cylinder(ft["diameter"] / 2, 2 * ft["depth"])
    body.label = "body"
    return body, Zc


def usb_port_mount(body, up, D, wall):
    """Rounded-rectangle cutout for a snap-in panel USB-C socket.

    The socket's clips latch on a panel of `panel_t`. If the back wall is thinner
    than that by more than 0.2 mm it is thickened on the inside around the hole;
    if thicker, it is thinned with a pocket that also leaves the clips room to open.
    The flange sits on the outside of the wall.
    """
    x, z = up["x"], up["z"]
    pt = up["panel_t"]
    fw, fh, _ = up["flange"]
    pad_w, pad_h = fw + 2 * up["pad_margin"], fh + 2 * up["pad_margin"]
    inner = D - wall
    if pt > wall + 0.2:
        body += Pos(x, inner, z) * Box(pad_w, pt - wall, pad_h, align=(CENTER, MAX, CENTER))
    elif pt < wall:
        body -= Pos(x, inner + 0.01, z) * Box(pad_w, wall - pt + 0.01, pad_h, align=(CENTER, MAX, CENTER))
    cw, ch = up["cutout"]
    with BuildSketch(Plane.XZ.offset(-(D + 0.01))) as hole:
        with Locations((x, z)):
            RectangleRounded(cw, ch, up["corner_r"])
    body -= extrude(hole.sketch, amount=max(pt, wall) + 0.5)
    return body


# --- stand-ins for fit and clash checks ----------------------------------------------

def display_stand_ins(g, s_g):
    dp, f = g.dp, g.f

    def dummy(shape, name):
        s = g.to_world(shape)
        s.label = name
        return s

    out = [
        dummy(Pos(g.gx, s_g, -f - 1) * Box(dp["glass_w"], dp["glass_h"], 2), "display_glass"),
        dummy(Pos(g.gx, s_g + g.pcb_cy, -f - (2 + dp["lcd_back"]) / 2) * Box(
            dp["pcb_w"], 97.1, dp["lcd_back"] - 2), "display_lcd"),
        dummy(Pos(g.gx, s_g + g.pcb_cy, -f - (dp["pcb_front"] + dp["pcb_back"]) / 2) * Box(
            dp["pcb_w"], dp["pcb_h"], dp["pcb_back"] - dp["pcb_front"]), "display_pcb"),
    ]
    comp_h = dp["depth"] - dp["pcb_back"]
    comp_z = -f - dp["pcb_back"] - comp_h / 2
    comps = Pos(g.gx, s_g + g.pcb_cy, comp_z) * Box(dp["pcb_w"] - 0.4, dp["pcb_h"] - 0.4, comp_h)
    so_h = dp["standoff_end"] - dp["pcb_back"]
    for sx in (-1, 1):
        for hy in g.hole_ys:
            comps -= Pos(g.gx + sx * g.hole_x, s_g + hy, comp_z) * Box(9, 9, 2 * comp_h)
            out.append(dummy(Pos(g.gx + sx * g.hole_x, s_g + hy, -f - dp["pcb_back"]) * Cylinder(
                dp["standoff_d"] / 2, so_h, align=(CENTER, CENTER, MAX)), "standoff"))
    out.append(dummy(comps, "display_components"))
    out.append(dummy(Pos(g.gx - (dp["pcb_w"] / 2 + 1 + 1.75), s_g + g.usb_y, -f - 10.4) * Box(
        3.5, 11.2, 7.8), "usb_plug"))
    return out


def speaker_stand_in(sp, ears):
    """Speaker box, cone face at z = 0 and back toward -z, with notched corner ears."""
    spk = Box(sp["width"], sp["height"], sp["depth"], align=(CENTER, CENTER, MAX))
    for ex, ey in ears:
        spk -= Pos(ex, ey, 0.01) * Cylinder(sp["notch_r"], sp["ear_front"] + 0.01, align=(CENTER, CENTER, MAX))
        spk -= Pos(ex, ey, -(sp["ear_front"] + sp["ear_t"])) * Cylinder(
            sp["notch_r"], sp["depth"], align=(CENTER, CENTER, MAX))
        spk -= Pos(ex, ey, 0) * Cylinder(sp["hole_d"] / 2, 3 * sp["depth"])
    spk.label = "speaker"
    return spk


def speaker_ears(sp):
    return [(px * sp["hole_dx"] / 2, py * sp["hole_dy"] / 2) for px in (-1, 1) for py in (-1, 1)]


def usb_port_stand_in(P, D):
    """Oval flange on the outside of the back wall, body and opened clips behind it."""
    up = P["usb_port"]
    x, z = up["x"], up["z"]
    fw, fh, ft = up["flange"]
    bw, bh, bl = up["body"]
    cw, cl = up["clip_span"]
    panel = max(up["panel_t"], P["enclosure"]["wall"])
    with BuildSketch(Plane.XZ.offset(-(D + ft))) as fl:
        with Locations((x, z)):
            SlotOverall(fw, fh)
    port = extrude(fl.sketch, amount=ft)                                    # Y: D .. D + ft
    port += Pos(x, D, z) * Box(bw, bl, bh, align=(CENTER, MAX, CENTER))      # through the hole
    port += Pos(x, D - panel, z) * Box(cw, cl, bh, align=(CENTER, MAX, CENTER))  # clips, opened
    port.label = "usb_port"
    return port


def facade_test_frame(g, W, L, s_g, rim=3.0, pocket=2.5):
    """Quick print of the front plate's facade: window, bevel and a shallow glass
    pocket, trimmed to `rim` around the pocket. Checks the glass fit and the
    window's alignment over the visible area. Print orientation, facade on the bed."""
    plate = facade_plate(g, W, L, s_g)
    keep = Pos(g.gx, s_g + g.trim / 2, 0) * Box(
        g.pw + 2 * rim, g.ph - g.trim + 2 * rim, g.f + pocket, align=(CENTER, CENTER, MAX))
    return on_bed(Rot(X=180) * (plate & keep))


# --- export --------------------------------------------------------------------------

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


def write_bambu_project(plates, path, bed):
    """Write a Bambu Studio 3MF with one build plate per entry in `plates`.

    `plates` is a list of (plate_name, [(object_name, shape), ...]) with shapes
    in print orientation, laid out around the plate centre (x, y) with z >= 0.
    Mirrors the layout Bambu Studio itself writes: one mesh file per object
    under 3D/Objects, plates in Metadata/model_settings.config, and plate i
    placed at a 1.2x-bed-size stride in a grid of ~sqrt(n) columns.
    """
    bw, bd = bed
    root_v = math.sqrt(len(plates))
    cols = int(round(root_v)) + (1 if root_v > round(root_v) else 0)
    ns = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
          'requiredextensions="p"')
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    files, resources, items, rels, cfg_objects, cfg_plates = {}, [], [], [], [], []
    obj_id = 0
    for p_idx, (plate_name, shapes) in enumerate(plates):
        px = (p_idx % cols) * bw * 1.2 + bw / 2
        py = -(p_idx // cols) * bd * 1.2 + bd / 2
        instances = []
        for name, shape in shapes:
            part_id, obj_id = obj_id + 1, obj_id + 2
            c = shape.bounding_box().center()
            raw_verts, raw_tris = shape.tessellate(0.005, 0.1)
            # tessellate() gives each face its own copy of its boundary
            # vertices; weld them so neighbouring faces share edges.
            index, verts, remap = {}, [], []
            for v in raw_verts:
                key = (round(v.X - c.X, 5), round(v.Y - c.Y, 5), round(v.Z - c.Z, 5))
                if key not in index:
                    index[key] = len(verts)
                    verts.append(key)
                remap.append(index[key])
            tris = [(remap[a], remap[b], remap[d]) for a, b, d in raw_tris]
            tris = [tr for tr in tris if len(set(tr)) == 3]
            mesh = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{zz:.5f}"/>' for x, y, zz in verts)
            mesh_t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{d}"/>' for a, b, d in tris)
            sub = f"3D/Objects/object_{part_id}.model"
            files[sub] = (f'{head}<model unit="millimeter" xml:lang="en-US" {ns}>\n'
                          ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                          f'  <object id="{part_id}" p:UUID="{uuid.uuid4()}" type="model">\n'
                          f'   <mesh><vertices>{mesh}</vertices><triangles>{mesh_t}</triangles></mesh>\n'
                          '  </object>\n </resources>\n <build/>\n</model>\n')
            rels.append(f' <Relationship Target="/{sub}" Id="rel-{len(rels) + 1}" '
                        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
            resources.append(
                f'  <object id="{obj_id}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
                f'    <component p:path="/{sub}" objectid="{part_id}" p:UUID="{uuid.uuid4()}" '
                'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>\n  </object>')
            items.append(f'  <item objectid="{obj_id}" p:UUID="{uuid.uuid4()}" printable="1" '
                         f'transform="1 0 0 0 1 0 0 0 1 {px + c.X:.5f} {py + c.Y:.5f} {c.Z:.5f}"/>')
            cfg_objects.append(
                f'  <object id="{obj_id}">\n    <metadata key="name" value={quoteattr(name)}/>\n'
                '    <metadata key="extruder" value="1"/>\n'
                f'    <part id="{part_id}" subtype="normal_part">\n'
                f'      <metadata key="name" value={quoteattr(name)}/>\n    </part>\n  </object>')
            instances.append(
                f'    <model_instance>\n      <metadata key="object_id" value="{obj_id}"/>\n'
                '      <metadata key="instance_id" value="0"/>\n'
                f'      <metadata key="identify_id" value="{100 + obj_id}"/>\n    </model_instance>')
        cfg_plates.append(
            f'  <plate>\n    <metadata key="plater_id" value="{p_idx + 1}"/>\n'
            f'    <metadata key="plater_name" value={quoteattr(plate_name)}/>\n'
            '    <metadata key="locked" value="false"/>\n' + "\n".join(instances) + "\n  </plate>")
    files["3D/3dmodel.model"] = (
        f'{head}<model unit="millimeter" xml:lang="en-US" {ns}>\n'
        ' <metadata name="Application">BambuStudio-02.08.04.57</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        ' <resources>\n' + "\n".join(resources) + '\n </resources>\n'
        f' <build p:UUID="{uuid.uuid4()}">\n' + "\n".join(items) + '\n </build>\n</model>\n')
    files["3D/_rels/3dmodel.model.rels"] = (
        f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "\n".join(rels) + '\n</Relationships>\n')
    files["Metadata/model_settings.config"] = (
        f'{head}<config>\n' + "\n".join(cfg_objects + cfg_plates) + '\n</config>\n')
    files["[Content_Types].xml"] = (
        f'{head}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        ' <Default Extension="png" ContentType="image/png"/>\n</Types>\n')
    files["_rels/.rels"] = (
        f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ["[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model",
                     "3D/_rels/3dmodel.model.rels", "Metadata/model_settings.config"]:
            z.writestr(name, files.pop(name))
        for name, data in files.items():
            z.writestr(name, data)
    print("wrote", path)
