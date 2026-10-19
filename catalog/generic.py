# Render functions for any model with an assembly STEP and print files, so a
# new model gets pictures without code of its own. A part entry (kind
# `assembly`) may name:
#   assembly: STEP in the model folder (default: the first step/*assembly*.step)
#   front:    the direction the model faces, [x, y, z] (default [0, -1, 0])
#   states:   more assembly STEPs to show, [{file, caption}]
#   prints:   print files in the order to lay them out (default: print/*.stl)
#   section:  false to leave out the cut-away view
# Solids are coloured by their STEP label through the collection's `colors`
# (exact label, else the longest key the label starts with, else `hardware`).
from pathlib import Path

from build123d import Keep, Plane, Vector

from core import labelled_solids, merged, stl_bounds, write_mesh


def find_assembly(folder):
    steps = sorted((folder / "step").glob("*.step")) if (folder / "step").is_dir() else []
    asm = [s for s in steps if "assembly" in s.stem]
    return asm[0] if asm else (steps[0] if steps else None)


def find_prints(folder):
    pdir = folder / "print"
    return sorted(pdir.glob("*.stl")) if pdir.is_dir() else []


def color_of(label, colors):
    if label in colors:
        return colors[label]
    keys = [k for k in colors if label.startswith(k)]
    return colors[max(keys, key=len)] if keys else colors.get("hardware", "#8c939c")


def tol_for(shape):
    return max(0.02, min(0.1, shape.bounding_box().diagonal / 2500))


def groups(solids, colors):
    """{colour: [solids]}, keeping the STEP's order."""
    out = {}
    for label, so in solids:
        out.setdefault(color_of(label, colors), []).append(so)
    return out


def meshes(solids, colors, where, stem):
    """One mesh per colour: [{stl, color}]."""
    parts = []
    for i, (col, sols) in enumerate(groups(solids, colors).items()):
        shape = merged(sols)
        parts.append(dict(stl=write_mesh(shape, where(f"{stem}_{i}.stl"), tol=tol_for(shape)), color=col))
    return parts


def cut(solids, origin, normal):
    """The solids on the back side of the plane, cut open on it."""
    plane = Plane(origin=origin, z_dir=normal)
    out = []
    for label, so in solids:
        bb = so.bounding_box()
        d = [(Vector(x, y, z) - origin).dot(normal) for x in (bb.min.X, bb.max.X)
             for y in (bb.min.Y, bb.max.Y) for z in (bb.min.Z, bb.max.Z)]
        if max(d) <= 0:
            out.append((label, so))
        elif min(d) < 0:
            try:
                piece = so.split(plane, keep=Keep.BOTTOM)
                if piece is not None and piece.volume > 1e-3:
                    out.append((label, piece))
            except Exception:  # a solid the kernel can't split: leave it out
                pass
    return out


def layout(files, gap=10.0):
    """Print files laid out flat on the bed in rows: [(file, offset)]."""
    items = []
    for f in files:
        lo, hi = stl_bounds(f)
        items.append((f, lo, hi[0] - lo[0], hi[1] - lo[1]))
    area = sum(w * d for _, _, w, d in items)
    row_w = max(max(w for *_, w, _ in items), (area ** 0.5) * 1.7)
    placed, x, y, row_d = [], 0.0, 0.0, 0.0
    for f, lo, w, d in sorted(items, key=lambda it: -it[3]):
        if x > 0 and x + w > row_w:
            x, y, row_d = 0.0, y - row_d - gap, 0.0
        placed.append((f, [x - lo[0], y - d - lo[1], -lo[2]]))
        x += w + gap
        row_d = max(row_d, d)
    return placed


def assembly(r, ctx):
    part, folder, colors = ctx.part, ctx.folder, ctx.colors
    step = folder / part["assembly"] if part.get("assembly") else find_assembly(folder)
    images, viewer, start = [], [], None
    view = dict(w=1000, h=750)
    if step:
        solids = labelled_solids(step)
        f = Vector(*part.get("front", [0, -1, 0])).normalized()
        up = Vector(0, 0, 1)
        s = f.cross(up).normalized()                     # to the model's right, seen from the front
        v = lambda a, b, c: (lambda w: [w.X, w.Y, w.Z])(f * a + s * b + up * c)
        shown = meshes(solids, colors, ctx.model, "assembly")
        viewer, start = shown, v(1.7, -0.9, 0.9)
        images.append((r.shot(ctx.img("front.png"), shown, view=v(1.7, -0.9, 0.9), **view), part.get("caption_front", "Assembled, from the front")))
        images.append((r.shot(ctx.img("back.png"), shown, view=v(-1.7, -0.8, 0.8), **view), "From the back"))
        images.append((r.shot(ctx.img("side.png"), shown, view=v(0, -1, 0.0001), **view), "Side view"))
        if part.get("section", True):
            bb = merged([so for _, so in solids]).bounding_box()
            c = (bb.min + bb.max) * 0.5
            half = meshes(cut(solids, c, s * -1), colors, ctx.cache, "section")
            images.append((r.shot(ctx.img("section.png"), half, view=v(0.5, -1.6, 0.5), **view), "Cut in half down the middle"))
        for i, st in enumerate(part.get("states", [])):
            other = meshes(labelled_solids(folder / st["file"]), colors, ctx.cache, f"state{i}")
            images.append((r.shot(ctx.img(f"state{i}.png"), other, view=v(1.7, -0.9, 0.9), **view), st["caption"]))
    files = [folder / p for p in part["prints"]] if part.get("prints") else find_prints(folder)
    if files:
        cols = list(dict.fromkeys(colors.get("print", ["#3b74d4", "#e8a33d", "#e6e8ec", "#2b5fb3"])))
        laid = [dict(stl=fl, color=cols[i % len(cols)], offset=off) for i, (fl, off) in enumerate(layout(files))]
        images.append((r.shot(ctx.img("print.png"), laid, w=1200, h=700, view=[0.25, -0.9, 1.2], pad=1.05),
                       part.get("caption_print", "Print parts, as they lie on the bed")))
        if not viewer:
            viewer = [dict(stl=Path(d["stl"]), color=d["color"], offset=d["offset"]) for d in laid]
    return {"images": images, "viewer": viewer, "view": start}
