# Bambu Studio project writer: one build plate per entry.
# Copied from the Waveshare library
# (waveshare-esp32-p4-wifi6-touch-lcd-7b/common/enclosure_lib.py).
import math
import uuid
import zipfile
from xml.sax.saxutils import quoteattr


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
