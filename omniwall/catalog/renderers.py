# Omniwall's render functions for the model catalog (catalog/build.py). Each
# takes the renderer and a part's context and returns its images and the meshes
# for its 3D view; catalog.yaml's `kind` picks the function.
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

from core import labelled_solids, rel, write_mesh  # noqa: F401  (catalog/core.py)

OW = Path(__file__).resolve().parent.parent      # omniwall/
REPO = OW.parent
panel = yaml.safe_load((OW / "panel.yaml").read_text())
P, SL = panel["pitch"], panel["slot"]


# Panel stand-in: 18 ga steel with the slot and peg-hole grid. A vertical slot
# column is centred on x = cx, one of its slots has its bottom edge at z = zs, and
# the panel's front face is at y = yf (it runs back to yf - thickness).
def panel_sheet(cx, zs, yf, x0, x1, z0, z1):
    t, w, L = panel["panel"]["thickness"], SL["width"], SL["length"]
    yc = yf - t / 2
    sheet = Pos((x0 + x1) / 2, yc, (z0 + z1) / 2) * Box(x1 - x0, t, z1 - z0)
    cuts = []
    n0, n1 = int((x0 - cx) // P) - 1, int((x1 - cx) // P) + 2
    m0, m1 = int((z0 - zs) // P) - 1, int((z1 - zs) // P) + 2
    for n in range(n0, n1):
        for m in range(m0, m1):
            x, z = cx + n * P, zs + m * P
            cuts.append(Pos(x, yc, z + L / 2) * Box(w, 2 * t, L))                  # vertical slot
            cuts.append(Pos(x + P / 2, yc, z + L / 2 + P / 2) * Box(L, 2 * t, w))  # horizontal slot
            cuts.append(Pos(x + P / 2, yc, z + L / 2) * Rot(X=90) * Cylinder(panel["peg_hole"]["diameter"] / 2, 2 * t))
    return sheet - Compound(children=cuts)


STEEL = dict(metalness=0.15, roughness=0.5)
_hook_panel = {}


def hook(r, ctx):
    """A hook: alone, on the panel from the front (see-through) and the back,
    side profile on the panel, as printed."""
    col, stem = ctx.colors, ctx.part["file"]
    cx, yf = panel["dovetail_mount"]["dovetail"]["block_width"] / 2, panel["slot_hook_1u"]["panel_front_y"]
    z0, z1 = -P - 16, SL["length"] + 16                           # two slots of one column, a little more
    if not _hook_panel:                                           # the same panel pieces for every hook
        _hook_panel["piece"] = write_mesh(panel_sheet(cx, 0, yf, cx - 0.9 * P, cx + 0.9 * P, z0, z1), ctx.shared("hook_panel.stl"))
        _hook_panel["strip"] = write_mesh(panel_sheet(cx, 0, yf, cx - 1.4, cx + 1.4, z0, z1), ctx.cache("../hook_panel_strip.stl"))
    piece, strip = _hook_panel["piece"], _hook_panel["strip"]
    steel = dict(color=col["panel"], **STEEL)
    mesh = write_mesh(import_step(str(OW / "hook" / "step" / f"{stem}.step")), ctx.model(f"{stem}.stl"))
    flat = OW / "hook" / "print" / f"{stem}.stl"
    blue = dict(stl=mesh, color=col["hook"])
    frame = dict(center=[cx, 5.5, -4.5], halfHeight=27)            # every hook at the same scale
    images = [
        (r.shot(ctx.img("hook.png"), [blue], w=640, h=800, view=[1, 1.3, 0.7], **frame), "The hook: dovetail front on the right, finger and foot on the left go through the panel"),
        # see-through: the front covers the slot exactly, so solid it hides which steel it grips
        (r.shot(ctx.img("front.png"), [dict(blue, opacity=0.45), dict(stl=piece, **steel)], w=640, h=800, view=[0.7, 1.6, 0.8], **frame),
         "On the panel, from the front, the hook drawn see-through so the steel behind it shows. Objects slide down onto the dovetail"),
        (r.shot(ctx.img("back.png"), [blue, dict(stl=piece, **steel)], w=640, h=800, view=[0.7, -1.6, 0.6], **frame), "From behind the panel"),
        (r.shot(ctx.img("side.png"), [blue, dict(stl=strip, **steel)], w=640, h=800, view=[1, 0, 0], **frame), "Side view: wall on the left, steel in grey"),
        (r.shot(ctx.img("print.png"), [dict(stl=flat, color=col["hook"])], w=800, h=500, view=[0.35, -1, 0.9], pad=1.2), "As printed: on its flat side, no supports"),
    ]
    # cards: the hook alone, filling the picture (the gallery keeps all hooks at one scale)
    card = r.shot(ctx.img("card.png"), [blue], w=800, h=600, view=[1, 1.3, 0.7], pad=1.3)
    return {"images": images, "viewer": [dict(stl=mesh, color=col["hook"]), dict(stl=piece, **steel)], "thumb": card}


def drawer_roles(step):
    """{role: [solids]} of an arc drawer assembly STEP: housing, drawer, handle, pin, hook."""
    out = {}
    for lab, so in labelled_solids(step):
        role = ("housing" if lab == "housing" else "hook" if lab.startswith("hook") else
                "handle" if lab == "handle" else "drawer" if lab == "drawer" else "pin")
        out.setdefault(role, []).append(so)
    return out


def drawer(r, ctx):
    """An arc drawer size: closed, open and tilted on the panel, the back with
    its hooks, and the print parts laid out."""
    col, folder, prefix = ctx.colors, ctx.folder, ctx.part["prefix"]
    bh = panel["bridge_hook"]
    roles = {s: drawer_roles(folder / "step" / f"{prefix}_assembly_{s}.step") for s in ("closed", "open", "tilted")}
    fixed = roles["closed"]
    housing = write_mesh(fixed["housing"][0], ctx.model("housing.stl"), tol=0.05)
    hooks_ = write_mesh(Compound(children=fixed["hook"]), ctx.model("hooks.stl"), tol=0.03)
    moving = {}
    for s, rl in roles.items():
        where = ctx.model if s == "open" else ctx.cache            # the 3D view shows it open
        moving[s] = [dict(stl=write_mesh(Compound(children=rl[k]), where(f"{k}_{s}.stl"), tol=0.05), color=col[k])
                     for k in ("drawer", "handle", "pin")]
    # The panel behind: the hooks' column and the upper slot they hang from.
    hb = fixed["hook"][0].bounding_box()
    hz = min(h.bounding_box().min.Z for h in fixed["hook"])
    b = fixed["housing"][0].bounding_box()
    sheet = panel_sheet((hb.min.X + hb.max.X) / 2, hz + bh["bar_bottom"], 0.0,
                        b.min.X - 0.75 * P, b.max.X + 0.75 * P, b.min.Z - 0.75 * P, b.max.Z + 0.75 * P)
    pnl = write_mesh(sheet, ctx.cache("panel.stl"))
    base = [dict(stl=housing, color=col["housing"]), dict(stl=hooks_, color=col["hook_on_drawer"])]
    wall = [dict(stl=pnl, color=col["panel"], noFit=True, **STEEL)]
    # Print parts side by side, as on the bed.
    layout, x = [], 0.0
    for k in ("housing", "drawer", "handle", "handle_pin"):
        stl = folder / "print" / f"{prefix}_{k}_print.stl"
        bb = import_step(str(stl.with_suffix(".step"))).bounding_box()
        layout.append(dict(stl=stl, color=col["housing" if k == "housing" else "pin" if k == "handle_pin" else k],
                           offset=[x - bb.min.X, -bb.min.Y, -bb.min.Z]))
        x += bb.size.X + 8
    view = dict(w=1000, h=750, view=[0.75, 1.7, 0.85])
    images = [
        (r.shot(ctx.img("closed.png"), base + moving["closed"] + wall, **view), "Closed, on the panel"),
        (r.shot(ctx.img("open.png"), base + moving["open"] + wall, **view), "Pulled out to its stop"),
        (r.shot(ctx.img("tilted.png"), base + moving["tilted"] + wall, w=1000, h=750, view=[1.6, 0.9, 0.45]), "Tilted down 30° at the end of its travel"),
        (r.shot(ctx.img("back.png"), base + moving["closed"], w=1000, h=750, view=[0.8, -1.6, 0.7]), "The back: dovetail pockets on the hooks"),
        (r.shot(ctx.img("print.png"), layout, w=1200, h=600, view=[0.3, -1, 1.1], pad=1.05), "Print parts: housing on its back, drawer upright, scoop, snap pin"),
    ]
    return {"images": images, "viewer": base + moving["open"]}


def label(r, ctx):
    """Every label in the folder's step/, face up: white plate, black text."""
    col = ctx.colors
    images, viewer = [], []
    for step in sorted((ctx.folder / "step").glob("*.step")):
        bodies = sorted(import_step(str(step)).solids(), key=lambda so: -so.volume)
        where = ctx.cache if viewer else ctx.model                 # the 3D view shows the first one
        plate = write_mesh(bodies[0], where(f"{step.stem}-plate.stl"), tol=0.01)
        text = write_mesh(Compound(children=bodies[1:]), where(f"{step.stem}-text.stl"), tol=0.01)
        ps = [dict(stl=plate, color=col["label_plate"], edgeOpacity=0.25), dict(stl=text, color=col["label_text"], edges=False)]
        images.append((r.shot(ctx.img(f"{step.stem}.png"), ps, w=900, h=360, view=[0, -0.4, 1], up=[0, 1, 0], pad=1.08), step.stem))
        viewer = viewer or ps
    return {"images": images, "viewer": viewer}


RENDERERS = {"hook": hook, "drawer": drawer, "label": label}
