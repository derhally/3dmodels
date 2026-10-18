"""Floating-region check for a print-orientation part (what Bambu Studio warns
about): slice the solid into layers and report any layer region that touches
nothing in the layer below.

    uv run --no-project --python 3.12 --with build123d --with pyyaml python check_islands.py print\\arc_drawer_housing_print.step [layer=0.2]

Each slab overlaps the one below by 0.01 mm, so a region is attached when its
intersection with any region of the previous layer has volume.
"""
import sys
from build123d import *

path = sys.argv[1]
layer = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
part = import_step(path)
bb = part.bounding_box()
sx, sy = bb.size.X + 2, bb.size.Y + 2
cx, cy = (bb.min.X + bb.max.X) / 2, (bb.min.Y + bb.max.Y) / 2
over = 0.01



def touches(s, p):
    r = s & p
    if r is not None and r.volume > 1e-9:
        return True
    return s.volume + p.volume - (s + p).volume > 1e-9


prev = []
islands = []
n = 0
z = bb.min.Z
while z < bb.max.Z - 1e-6:
    z0 = z - (over if n else 0)
    z1 = min(z + layer, bb.max.Z)
    slab = Pos(cx, cy, (z0 + z1) / 2) * Box(sx, sy, z1 - z0)
    cut = part & slab
    sols = list(cut.solids()) if hasattr(cut, "solids") else []
    if n:
        for s in sols:
            # s & p is None when the solids do not overlap. The kernel's intersection
            # sometimes returns nothing for a thin overlap it should find (whole wall
            # sections reported floating), so check a miss again with a fuse.
            if not any(touches(s, p) for p in prev):
                c = s.center()
                islands.append((round(z, 2), round(s.volume / layer, 3), round(c.X, 2), round(c.Y, 2)))
    prev = sols
    z += layer
    n += 1

print(f"{path}: {n} layers of {layer} mm, {len(islands)} floating regions")
for z, area, x, y in islands:
    print(f"  z={z:7.2f}  area~{area:7.3f} mm2  at x={x:7.2f} y={y:7.2f}")
