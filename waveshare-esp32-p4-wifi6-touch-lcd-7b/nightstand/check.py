"""Checks for the nightstand stand: clashes at every tilt step, overhangs on the
print-orientation parts, bed fit, and tip stability with the assumed masses.

    python check.py            (writes report.txt next to this script)
"""

import math
from itertools import combinations

import build as b
from build import P, Vector, Box, Pos

lines = []


def log(s=""):
    print(s)
    lines.append(s)


def overlap(x, y, tol=0.01):
    bx, by = x.bounding_box(), y.bounding_box()
    if (bx.min.X > by.max.X or by.min.X > bx.max.X or bx.min.Y > by.max.Y or by.min.Y > bx.max.Y
            or bx.min.Z > by.max.Z or by.min.Z > bx.max.Z):
        return 0.0
    v = (x & y).volume
    return v if v > tol else 0.0


def bad_faces(part, limit=45.0):
    """Faces facing down flatter than `limit` deg from vertical, not on the bed."""
    lim = -math.cos(math.radians(limit)) - 1e-3
    out = []
    for f in part.faces():
        worst, where = 1.0, None
        for u in (0.1, 0.5, 0.9):
            for w in (0.1, 0.5, 0.9):
                n, p = f.normal_at(u, w), f.position_at(u, w)
                if p.Z > 0.05 and n.Z < worst:
                    worst, where = n.Z, p
        if worst < lim:
            out.append((round(90 - math.degrees(math.acos(min(1, -worst))), 1), round(f.area, 2), where))
    return out


case, case_hw, base, base_hw, prints = b.build_all()
moving, fixed = case + case_hw, base + base_hw

log("== Clashes (overlap > 0.01 mm3) ==")
for group, label in ((moving, "case"), (fixed, "base")):
    hits = [(x.label, y.label, v) for x, y in combinations(group, 2) if (v := overlap(x, y))]
    log(f"{label} parts with each other: " + (", ".join(f"{a} / {c} {v:.2f}" for a, c, v in hits) or "none"))
for deg in range(P["tilt"]["min"], P["tilt"]["max"] + 1, 360 // P["hinge"]["teeth"]):
    tilted = [b.tilt(s, deg) for s in moving]
    hits = [(x.label, y.label, v) for x in tilted for y in fixed if (v := overlap(x, y))]
    gaps = []
    for x in tilted:
        bb = x.bounding_box()
        gaps.append(bb.min.Z)
    log(f"tilt {deg:2d} deg: " + (", ".join(f"{a} / {c} {v:.2f}" for a, c, v in hits) or "no clashes")
        + f"; case bottom {min(gaps):.1f} above the table")

log()
log("== Print orientation: overhangs flatter than 45 deg from vertical, bed fit ==")
bed = P["print_bed"]
for key, (part, how) in prints.items():
    bb = part.bounding_box()
    bad = bad_faces(part)
    fits = sorted([bb.size.X, bb.size.Y])[1] <= max(bed) and min(bb.size.X, bb.size.Y) <= min(bed) and bb.size.Z <= 325
    log(f"{key} ({how}): {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, {len(part.solids())} solid, "
        f"vol {part.volume / 1000:.1f} cm3, {'fits' if fits else 'DOES NOT FIT'}, overhangs: {len(bad)}")
    for d, a, at in sorted(bad, key=lambda t: -t[1])[:8]:
        log(f"    {d:.1f} deg, {a} mm2 at ({at.X:.1f}, {at.Y:.1f}, {at.Z:.1f})")

log()
log("== Mass and tip stability (display and speaker masses ASSUMED) ==")
m = P["mass"]
rho = m["pla_density"] * m["pla_fill"] / 1000          # g per mm3
names = {s.label for s in moving}


def com_and_mass(deg):
    items = []                                             # (mass g, centre)
    for s in case:
        items.append((s.volume * rho, b.tilt(s, deg).center()))
    for s in base:
        items.append((s.volume * rho, s.center()))
    tabs = [s for s in case_hw if s.label.startswith("clamp")]
    items += [(s.volume * rho, b.tilt(s, deg).center()) for s in tabs]
    disp = [s for s in case_hw if s.label.startswith("display")]
    dc = sum((s.center() * s.volume for s in disp), Vector()) / sum(s.volume for s in disp)
    items.append((m["display"], b.tilt(Pos(dc) * Box(1, 1, 1), deg).center()))
    spk = next(s for s in base_hw if s.label == "speaker")
    items.append((m["speaker"], spk.center()))
    items.append((m["hardware"], Vector(0, b.Y_h, b.Z_h)))
    tot = sum(w for w, _ in items)
    c = sum((p * w for w, p in items), Vector()) / tot
    case_items = items[:len(case)] + items[len(case) + len(base):len(case) + len(base) + len(tabs) + 1]
    cm = sum(w for w, _ in case_items)
    cc = sum((p * w for w, p in case_items), Vector()) / cm
    return tot, c, cm, cc


ft = P["feet"]
y_front, y_back = b.Y_fr + ft["inset"], b.Y_back - ft["inset"]   # rubber feet carry it
for deg in (P["tilt"]["min"], P["tilt"]["max"]):
    tot, c, cm, cc = com_and_mass(deg)
    top = b.tilt(Pos(0, 0, b.Z_cb + b.L) * Box(1, 1, 1), deg).center()
    f_back = tot * 9.81e-3 * (y_back - c.Y) / top.Z                 # N, pushed back at the top
    f_fwd = tot * 9.81e-3 * (c.Y - y_front) / top.Z
    hinge = cm * 9.81e-3 * (cc.Y - b.Y_h) / 1000                     # N m, + leans back
    log(f"tilt {deg:2d}: total {tot:.0f} g, centre of mass Y {c.Y:.1f} Z {c.Z:.1f} (feet Y {y_front:.1f}..{y_back:.1f}); "
        f"screen top at Y {top.Y:.1f} Z {top.Z:.1f}; tips back with {f_back:.2f} N at the top, forward with {f_fwd:.2f} N; "
        f"case {cm:.0f} g, hinge holds {abs(hinge):.3f} N m ({'back' if hinge > 0 else 'forward'})")

log()
log("== USB-C cable length ==")
(pc, _), (pb, _) = b.cable_routes()
gap = math.dist(pc[-1], pb[0])
y, z = pc[-1][1] - b.Y_h, pc[-1][2] - b.Z_h              # case-side pass at full tilt
th = math.radians(P["tilt"]["max"])
moved = (pc[-1][0], b.Y_h + y * math.cos(th) + z * math.sin(th), b.Z_h - y * math.sin(th) + z * math.cos(th))
loop = math.dist(moved, pb[0])
need = b.route_length(pc) + b.route_length(pb) + loop + 20
log(f"route: {b.route_length(pc):.0f} mm in the case, {b.route_length(pb):.0f} mm in the base, "
    f"{gap:.1f} mm across the gap upright, {loop:.0f} mm at {P['tilt']['max']} deg; with 20 mm for the "
    f"bends it needs {need:.0f} mm of the {P['wire']['cable_len']:.0f} mm cable")

(b.here / "report.txt").write_text("\n".join(lines) + "\n")
