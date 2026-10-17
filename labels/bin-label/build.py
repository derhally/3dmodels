"""Front labels: a white plate with black text inlaid flush with the face, in
the sizes listed in params (the bins' pocket, the arc drawer's label holder).

    python build.py [params.yaml] [output_dir]

The text is auto-fitted: as large as fits inside the plate minus its size's margins,
capped at text.max_height, and centred on its actual glyph outline. Each label
is two solids, the plate (with the text cut into its face) and the text inlay
that fills the cut, so a two-colour print has a flat face.

Print orientation is face down: the text is the first layers on the bed (it
reads mirrored in the print files and correctly once the label is flipped).

Outputs, per label: step/<name>.step (both bodies), print/<name>.3mf (two
objects), print/<name>-plate.stl and print/<name>-text.stl. Plus one Bambu
Studio project, print/labels.3mf, with every label on one plate and the plate
and text on the filament slots set in params.
"""

import re
import sys
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import yaml
from build123d import *  # noqa: F403

here = Path(__file__).resolve().parent
P = yaml.safe_load((Path(sys.argv[1]) if len(sys.argv) > 1 else here / "params.yaml").read_text(encoding="utf-8"))
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else here
tx, SIZES = P["text"], P["sizes"]
depth = tx["inlay_depth"]
BED = (330, 320)   # Bambu Lab H2C


def fitted_text(txt, sz):
    """Text face at z=0, as large as the plate allows, centred on its glyphs."""
    bb = Text(txt, 10, font_path=tx["font_path"]).bounding_box()
    avail_w = sz["width"] - 2 * sz["margin_x"]
    avail_h = min(sz["height"] - 2 * sz["margin_y"], tx["max_height"])
    size = 10 * min(avail_w / bb.size.X, avail_h / bb.size.Y)
    face = Text(txt, size, font_path=tx["font_path"])
    c = face.bounding_box().center()
    return Pos(-c.X, -c.Y) * face


def label(txt, sz):
    """(plate, inlay) in use orientation: face up at z = thickness, back at z = 0."""
    T = sz["thickness"]
    blank = Box(sz["width"], sz["height"], T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if sz["corner_radius"] > 0:
        blank = fillet(blank.edges().filter_by(Axis.Z), sz["corner_radius"])
    inlay = Pos(0, 0, T - depth) * extrude(fitted_text(txt, sz), depth)
    return blank - inlay, inlay


def to_print(shape, sz):
    """Face down on the bed."""
    return Pos(0, 0, sz["thickness"]) * Rot(180, 0, 0) * shape


def slug(txt):
    return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")


def mesh(shape):
    raw_v, raw_t = shape.tessellate(0.002, 0.1)
    index, verts, remap = {}, [], []
    for v in raw_v:
        key = (round(v.X, 5), round(v.Y, 5), round(v.Z, 5))
        if key not in index:
            index[key] = len(verts)
            verts.append(key)
        remap.append(index[key])
    tris = [(remap[a], remap[b], remap[c]) for a, b, c in raw_t]
    tris = [t for t in tris if len(set(t)) == 3]
    return ("<mesh><vertices>"
            + "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in verts)
            + "</vertices><triangles>"
            + "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
            + "</triangles></mesh>")


def write_bambu_labels(labels, path):
    """Bambu Studio 3MF: one object per label, each with a plate part and a
    text part on the filament slots from params, all on build plate 1."""
    ns = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
          'requiredextensions="p"')
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rels_ns = 'xmlns="http://schemas.openxmlformats.org/package/2006/relationships"'
    model_rel = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
    sub = "3D/Objects/labels.model"
    sub_objs, resources, items, cfg_objects, instances = [], [], [], [], []
    # a column of labels, wrapping into more columns when the bed is full
    pitch_x = max(sz["width"] for *_, sz in labels) + 5
    pitch_y = max(sz["height"] for *_, sz in labels) + 5
    rows = min(len(labels), int((BED[1] - 20) // pitch_y))
    cols = -(-len(labels) // rows)
    next_id = 1
    for i, (name, plate, inlay, _) in enumerate(labels):
        col, row = divmod(i, rows)
        x = BED[0] / 2 + (col - (cols - 1) / 2) * pitch_x
        y = BED[1] / 2 + ((rows - 1) / 2 - row) * pitch_y
        parts = []
        for part_name, shape, extruder in ((f"{name} plate", plate, P["filament"]["plate"]),
                                         (f"{name} text", inlay, P["filament"]["text"])):
            sub_objs.append(f'  <object id="{next_id}" p:UUID="{uuid.uuid4()}" type="model">{mesh(shape)}</object>')
            parts.append((next_id, part_name, extruder))
            next_id += 1
        oid, next_id = next_id, next_id + 1
        comps = "".join(f'<component p:path="/{sub}" objectid="{pid}" p:UUID="{uuid.uuid4()}" '
                        'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>' for pid, _, _ in parts)
        resources.append(f'  <object id="{oid}" p:UUID="{uuid.uuid4()}" type="model">'
                         f'<components>{comps}</components></object>')
        items.append(f'  <item objectid="{oid}" p:UUID="{uuid.uuid4()}" printable="1" '
                     f'transform="1 0 0 0 1 0 0 0 1 {x:.5f} {y:.5f} 0"/>')
        cfg_objects.append(
            f'  <object id="{oid}">\n    <metadata key="name" value={quoteattr(name)}/>\n'
            f'    <metadata key="extruder" value="{P['filament']['plate']}"/>\n'
            + "".join(f'    <part id="{pid}" subtype="normal_part">\n'
                      f'      <metadata key="name" value={quoteattr(pn)}/>\n'
                      f'      <metadata key="extruder" value="{ex}"/>\n    </part>\n'
                      for pid, pn, ex in parts)
            + '  </object>')
        instances.append(f'    <model_instance>\n      <metadata key="object_id" value="{oid}"/>\n'
                         '      <metadata key="instance_id" value="0"/>\n'
                         f'      <metadata key="identify_id" value="{1000 + oid}"/>\n    </model_instance>')
    files = {
        "[Content_Types].xml": (
            f'{head}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
            '</Types>\n'),
        "_rels/.rels": (
            f'{head}<Relationships {rels_ns}>\n'
            f' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="{model_rel}"/>\n</Relationships>\n'),
        "3D/3dmodel.model": (
            f'{head}<model unit="millimeter" xml:lang="en-US" {ns}>\n'
            ' <metadata name="Application">BambuStudio-02.08.04.57</metadata>\n'
            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
            ' <resources>\n' + "\n".join(resources) + '\n </resources>\n'
            f' <build p:UUID="{uuid.uuid4()}">\n' + "\n".join(items) + '\n </build>\n</model>\n'),
        "3D/_rels/3dmodel.model.rels": (
            f'{head}<Relationships {rels_ns}>\n'
            f' <Relationship Target="/{sub}" Id="rel-1" Type="{model_rel}"/>\n</Relationships>\n'),
        sub: (
            f'{head}<model unit="millimeter" xml:lang="en-US" {ns}>\n'
            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
            + "\n".join(sub_objs) + '\n </resources>\n <build/>\n</model>\n'),
        "Metadata/model_settings.config": (
            f'{head}<config>\n' + "\n".join(cfg_objects)
            + '\n  <plate>\n    <metadata key="plater_id" value="1"/>\n'
            '    <metadata key="plater_name" value="Labels"/>\n'
            '    <metadata key="locked" value="false"/>\n'
            + "\n".join(instances) + '\n  </plate>\n</config>\n'),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    print("wrote", path)


(out_dir / "step").mkdir(parents=True, exist_ok=True)
(out_dir / "print").mkdir(parents=True, exist_ok=True)
bambu = []
for entry in P["labels"]:
    txt, size = (entry, "bin") if isinstance(entry, str) else (entry["text"], entry.get("size", "bin"))
    sz = SIZES[size]
    name = slug(txt) if size == "bin" else f"{slug(txt)}-{size}"
    plate, inlay = label(txt, sz)
    export_step(Compound([plate, inlay]), str(out_dir / "step" / f"{name}.step"))
    pp, pi = to_print(plate, sz), to_print(inlay, sz)
    export_stl(pp, str(out_dir / "print" / f"{name}-plate.stl"))
    export_stl(pi, str(out_dir / "print" / f"{name}-text.stl"))
    m = Mesher()
    m.add_shape(pp, part_number="plate")
    m.add_shape(pi, part_number="text")
    m.write(str(out_dir / "print" / f"{name}.3mf"))
    bambu.append((txt if size == "bin" else f"{txt} ({size})", pp, pi, sz))
    bb, tb = Compound([plate, inlay]).bounding_box(), inlay.bounding_box()
    print(f"{txt} ({size}): {bb.size.X:.3f} x {bb.size.Y:.3f} x {bb.size.Z:.3f} mm, "
          f"text {tb.size.X:.2f} x {tb.size.Y:.2f} mm, "
          f"plate {plate.volume:.2f} + text {inlay.volume:.2f} mm3")
write_bambu_labels(bambu, out_dir / "print" / "labels.3mf")
