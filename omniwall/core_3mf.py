# Plain 3MF writer (core spec only, no slicer metadata): one or more mesh objects
# in one file. Bambu Studio, Orca and PrusaSlicer import it as geometry onto the
# current plate without complaint. Used for test prints; the printed parts go
# through ../bambu/bambu_project.py, which writes full Bambu Studio projects.
import uuid
import zipfile


def write_3mf(objects, path):
    """objects: list of (name, vertices, triangles); vertices are (x, y, z) tuples
    in mm, triangles are index triples. Shared vertices are welded per object."""
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    res, items = [], []
    for i, (name, verts, tris) in enumerate(objects, start=1):
        index, out, remap = {}, [], []
        for v in verts:
            key = (round(v[0], 5), round(v[1], 5), round(v[2], 5))
            if key not in index:
                index[key] = len(out)
                out.append(key)
            remap.append(index[key])
        tri = [(remap[a], remap[b], remap[c]) for a, b, c in tris]
        tri = [t for t in tri if len(set(t)) == 3]
        vx = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in out)
        tx = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tri)
        res.append(f'  <object id="{i}" name="{name}" type="model"><mesh><vertices>{vx}</vertices>'
                   f'<triangles>{tx}</triangles></mesh></object>')
        items.append(f'  <item objectid="{i}"/>')
    model = (f'{head}<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
             f' <metadata name="Title">{objects[0][0] if len(objects) == 1 else "assembly"}</metadata>\n'
             ' <resources>\n' + "\n".join(res) + '\n </resources>\n <build>\n' + "\n".join(items) + '\n </build>\n</model>\n')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", f'{head}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                   ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                   ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n</Types>\n')
        z.writestr("_rels/.rels", f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                   ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
                   'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
        z.writestr("3D/3dmodel.model", model)


def shape_mesh(shape, dx=0.0, dy=0.0):
    """(vertices, triangles) of a build123d shape, shifted in the bed plane."""
    verts, tris = shape.tessellate(0.005, 0.1)
    return [(v.X + dx, v.Y + dy, v.Z) for v in verts], tris


def stl_mesh(path, dx=0.0, dy=0.0):
    """(vertices, triangles) read from a binary STL file."""
    import struct
    b = open(path, "rb").read()
    n = struct.unpack_from("<I", b, 80)[0]
    verts, tris = [], []
    for i in range(n):
        f = struct.unpack_from("<12f", b, 84 + 50 * i)
        base = len(verts)
        verts += [(f[3] + dx, f[4] + dy, f[5]), (f[6] + dx, f[7] + dy, f[8]), (f[9] + dx, f[10] + dy, f[11])]
        tris.append((base, base + 1, base + 2))
    return verts, tris
