r"""Check the SolidCraft build of the arc drawer against the build123d one.

    E:\source\shapr3d-mcp\.venv\Scripts\python.exe solidcraft\check_solidcraft.py

Run from omniwall\arc-drawer after build.py. Compares the SolidCraft housing
and drawer with step/ (volumes and the volume each has that the other lacks),
checks the SolidCraft housing against the hooks from the closed assembly, and
counts faces flatter than 45 deg on the SolidCraft print files. Writes
solidcraft/check_report.txt.
"""
import math
from pathlib import Path

from build123d import import_step

HERE = Path(__file__).resolve().parent.parent
SC = HERE / "solidcraft"
lines = []
log = lines.append


def vol(shape):
    """Total solid volume of whatever a boolean returned (None when empty)."""
    if shape is None:
        return 0.0
    if isinstance(shape, (list, tuple)):
        return sum(vol(s) for s in shape)
    return sum(s.volume for s in shape.solids())


def diff(a, b):
    return vol(a - b)


def bad_faces(part, limit=45.0):
    lim = -math.cos(math.radians(limit)) - 1e-3
    n_bad = 0
    for f in part.faces():
        worst = 1.0
        for u in (0.1, 0.5, 0.9):
            for w in (0.1, 0.5, 0.9):
                n = f.normal_at(u, w)
                if f.position_at(u, w).Z > 0.05 and n.Z < worst:
                    worst = n.Z
        if worst < lim:
            n_bad += 1
    return n_bad


for name in ("housing", "drawer"):
    ref = import_step(str(HERE / "step" / f"arc_drawer_{name}.step"))
    sc = import_step(str(SC / f"arc_drawer_{name}.step"))
    bb = sc.bounding_box()
    log(f"{name}: SolidCraft {bb.size.X:.3f} x {bb.size.Y:.3f} x {bb.size.Z:.3f} mm, volume {vol(sc):.3f} mm3, "
        f"solids {len(sc.solids())}, valid {sc.is_valid}; build123d volume {vol(ref):.3f} mm3")
    log(f"    only in SolidCraft {diff(sc, ref):.4f} mm3, only in build123d {diff(ref, sc):.4f} mm3")

asm = import_step(str(HERE / "step" / "arc_drawer_assembly_closed.step"))
sc_h = import_step(str(SC / "arc_drawer_housing.step"))
hooks = [s for s in asm.solids() if s.volume < 2000]
log(f"hooks vs SolidCraft housing: {sum(vol(sc_h & k) for k in hooks):.4f} mm3 over {len(hooks)} hooks "
    f"(0.083 mm ridge interference per side is expected but sits in the hooks' notches)")

for stem in ("arc_drawer_housing_print", "arc_drawer_drawer_print"):
    p = import_step(str(SC / f"{stem}.step"))
    bb = p.bounding_box()
    log(f"{stem}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}, z from {bb.min.Z:.3f}, "
        f"faces {len(p.faces())}, faces flatter than 45 deg: {bad_faces(p)}")

(SC / "check_report.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
