# Segmented pocket test: a plate with one pocket column and a seat on every hook row,
# and the short-head Slot hook 1U it hangs on (params.yaml says what each value is and
# where it came from). Hold the plate `push` high, push it straight onto the panel
# (each head goes into its window), push it down `push` (the lips slide over the
# heads, the ridges click into the notches, every seat sits on a hook top).
# The hook is Slot hook 1U with its dovetail head only on the top `head` mm; the
# plate's spine channel stays open from top to bottom, so the spine under each short
# head passes the roofs that seat the hooks below. Pocket lips, ridges and hooks come
# from ../../hook_geometry.py and ../../panel.yaml.
# Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py
# It writes test-prints/ (git-ignored): per print orientation (back: pocket face
# down, as the drawer housing; upright: as the tool bins) the plate's print STEP/STL
# and a Bambu Studio 3MF with the plate and the hooks; the hook's print STEP/STL;
# the plate on its hooks seated and held at the push height; and report.txt.
# Coordinates: x across (the hooks' flat side at 0), y out from the panel face
# (plate back at y = 0), z up from the top hook's slot's bottom edge.
import copy
import math
from pathlib import Path

import yaml
from build123d import *  # noqa: F403

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
P = yaml.safe_load((HERE / "params.yaml").read_text())
panel = yaml.safe_load((ROOT / "panel.yaml").read_text())
exec((ROOT / "hook_geometry.py").read_text())
exec((ROOT.parent / "bambu" / "bambu_project.py").read_text())
TEMPLATE = ROOT.parent / "bambu" / "project_settings.config"

U, HK, SG, PL = P["unit"], P["hook"], P["segment"], P["plate"]
NAME, ROWS = U["file_prefix"], U["rows"]
LIP, WINDOW, PUSH, HEAD = SG["lip"], SG["window"], SG["push"], HK["head"]
pitch = panel["pitch"]
s1 = panel["slot_hook_1u"]
TOP = s1["height"]                                               # hook top: the slot's top edge
FRONT = s1["height"] + s1["printed"]["rim_notch"]["depth"]       # dovetail front, top to bottom
YP = s1["panel_front_y"]
ROOF = pitch - LIP - WINDOW
seats = [TOP - k * pitch for k in range(ROWS)]                   # hook tops, top row first
assert ROOF > 0, "no roof left between segments"
assert LIP <= HEAD and PUSH >= LIP and PUSH + HEAD <= LIP + WINDOW, "the head doesn't fit the window at the push height"
lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


def solid(s):
    sols = s.solids() if hasattr(s, "solids") else [s]
    assert len(sols) == 1, f"expected one solid, got {len(sols)}"
    return sols[0]


def overlap(a, b):
    r = a & b
    return sum(s.volume for s in r.solids()) if r is not None else 0.0


def to_bed(s):
    bb = s.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * s


# ---------------------------------------------------------------- the hook
def short_head_hook():
    """Slot hook 1U as printed, its dovetail head cut off below the top HEAD mm (the
    spine stays the full height). Panel front at y = 0, slot's bottom edge at z = 0."""
    dv = panel["dovetail_mount"]["dovetail"]
    h = slot_hook_1u(panel, ROOT)
    y_neck = YP + dv["block_depth"]                              # the spine's front: neck and head start here
    z_cut = TOP - HEAD
    cut = Pos(-5, y_neck, -5) * Box(20, 20, z_cut + 5, align=Align.MIN)
    h = solid(h - cut)
    h = Pos(0, -YP, 0) * h
    h.label = "short-head slot hook 1U"
    return h


# ---------------------------------------------------------------- the plate
def plate(orient):
    """The test plate for one print orientation ('back' or 'upright'), as it hangs."""
    o = P["orientations"][orient]
    dm = copy.deepcopy(panel["dovetail_mount"])
    dv, pk = dm["dovetail"], dm["pocket"]
    pk["spine_clearance"] = o["pocket"]["spine_clearance"]
    pk["flank_gap"] = o["pocket"]["flank_gap"]
    pk["ridge"]["height"] = o["pocket"]["ridge_height"]
    back = orient == "back"
    cx = dv["block_width"] / 2                                   # pocket centre
    w_hook = max(dv["head_width"], dv["block_width"]) / 2        # hook front's half width
    wp = w_hook + pk["side_clearance"]                           # pocket's (and spine channel's) half width
    wn = dv["neck_width"] / 2 + pk["side_clearance"]             # half width between the lips
    yb = dv["block_depth"] + pk["spine_clearance"]               # back of the lips and roofs
    yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]   # pocket floor
    depth = yf + (wp if back else 0.0) + PL["front_wall"]        # on its back the floor has a gable
    z_top = seats[0] + wp + PL["top"]
    z_bot = seats[-1] - LIP - WINDOW - SG["floor"]
    hw = PL["half_width"]
    body = Pos(cx, depth / 2, (z_top + z_bot) / 2) * Box(2 * hw, depth, z_top - z_bot)
    body = chamfer(body.edges(), PL["chamfer"])
    e = 0.02    # ramps and gables start a hair outside the walls on their 45 deg lines, so no flat strip is left
    # Spine channel: open from the top seat out through the bottom, so the spine
    # under each short head passes the roofs.
    z_chan = seats[0] if back else seats[0] - (wp - w_hook)      # upright: up to the top gable's eaves, no flat top
    void = Pos(cx, (yb - 1) / 2, (z_bot - 1 + z_chan) / 2) * Box(2 * wp, yb + 1, z_chan - z_bot + 1)
    if back:
        chan = Polygon((cx - wp - e, yb), (cx + wp + e, yb), (cx, yb + wp + e), align=None)
        void = void + Pos(0, 0, z_bot - 1) * extrude(chan, seats[0] - z_bot + 1)
    for S in seats:
        zr, zw = S - LIP, S - LIP - WINDOW
        ze = S - (wp - w_hook)                                   # gable eaves (upright)
        lips = pocket_void(dm, S, 0.0, zr)
        if not back:
            lips = lips & Pos(cx, yf / 2, (zr + ze) / 2) * Box(20, yf + 10, ze - zr)
        ramp = Plane.XZ * Polygon((cx - wp - e, zr - e), (cx + wp + e, zr - e), (cx + wn, zr + wp - wn),
                                  (cx - wn, zr + wp - wn), align=None)
        ramp = Pos(0, yf, 0) * extrude(ramp, yf + 1)            # Plane.XZ extrudes toward -y
        window = Pos(cx, (yf - 1) / 2, (zw + zr) / 2) * Box(2 * wp, yf + 1, WINDOW)
        seg = lips + ramp + window
        if back:
            floor = Polygon((cx - wp - e, yf), (cx + wp + e, yf), (cx, yf + wp + e), align=None)
            seg = seg + Pos(0, 0, zw) * extrude(floor, S - zw)
        else:
            roof = extrude(Plane.XZ * Polygon((cx - wp - e, ze - e), (cx + wp + e, ze - e), (cx, ze + wp), align=None), -(yf + 1))
            seg = seg + Pos(0, -1, 0) * roof
        void = void + seg
    body = solid(body - void)
    body.label = f"{NAME} plate ({orient})"
    return body, depth


def downward(part, limit=45.0):
    """(flattest downward face, deg from vertical; faces flatter than `limit`) off the bed"""
    worst, bad = 1.0, []
    lim = -math.cos(math.radians(limit)) - 1e-3
    for f in part.faces():
        fw = 1.0
        for u in (0.0, 0.1, 0.5, 0.9, 1.0):
            for w in (0.0, 0.1, 0.5, 0.9, 1.0):
                try:
                    n, p = f.normal_at(u, w), f.position_at(u, w)
                except Exception:
                    continue
                if p.Z > 0.05:
                    fw = min(fw, n.Z)
        worst = min(worst, fw)
        if fw < lim:
            bad.append((round(90 - math.degrees(math.acos(min(1, -fw))), 1), round(f.area, 2), f.center()))
    return (0.0 if worst >= 0 else round(90 - math.degrees(math.acos(min(1, -worst))), 1)), bad


def report_print(name, p):
    worst, bad = downward(p)
    bb = p.bounding_box()
    log(f"  {name} as printed: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, flattest downward face "
        f"{worst:.1f} deg from vertical, faces flatter than 45 deg: {len(bad)}")
    for b in sorted(bad, key=lambda t: -t[1])[:8]:
        log(f"    {b[0]} deg, {b[1]} mm2 at ({b[2].X:.1f}, {b[2].Y:.1f}, {b[2].Z:.1f})")


# ---------------------------------------------------------------- build
if __name__ == "__main__":
    out = HERE / "test-prints"
    out.mkdir(exist_ok=True)
    hk = short_head_hook()
    hks = []
    for k in range(ROWS):
        h = Pos(0, 0, -k * pitch) * hk
        h.label = f"hook {k + 1}"
        hks.append(h)
    log(f"short-head Slot hook 1U: head on the top {HEAD} of its {FRONT:.1f} front, volume {hk.volume:.1f} mm3, valid {hk.is_valid}")
    hp = to_bed(Rot(Y=-90) * hk)                                 # on its flat side, as ../../hook/build_hooks.py
    report_print("hook", hp)
    export_step(hp, str(out / f"{NAME}_hook_print.step"))
    export_stl(hp, str(out / f"{NAME}_hook_print.stl"))
    log(f"{ROWS} seats at z {[round(s, 2) for s in seats]} (hook tops = slot tops); each row: lips {LIP} (45 deg ramp at the bottom), "
        f"window {WINDOW}, roof {ROOF:.1f} behind the spine channel; push {PUSH}")
    sweep = [12, 9, 7, 6, 5, 4, 3, 2.5, 2, 1.5, 1, 0.5, 0.25, 0]
    gap = bambu_object_gap(TEMPLATE)
    for orient in ("back", "upright"):
        body, depth = plate(orient)
        bb = body.bounding_box()
        log(f"{orient}: plate {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {body.volume:.1f} mm3, valid {body.is_valid}")
        def going_on(lift):
            return max(overlap(Pos(0, dy, lift) * body, h) for dy in sweep for h in hks)
        log(f"  seated: overlap with each hook {[round(overlap(body, h), 3) for h in hks]} mm3 (the snap ridges, if any)")
        log(f"  held {PUSH} high, pushed straight on from 12 mm out: worst overlap {going_on(PUSH):.4f} mm3")
        down = [max(overlap(Pos(0, 0, PUSH * i / 30) * body, h) for h in hks) for i in range(31)]
        log(f"  pushed down {PUSH} to seated: worst overlap {max(down):.3f} mm3 per hook (the snap ridges riding over the heads)")
        ok = [l / 10 for l in range(80, 151) if going_on(l / 10) < 1e-4]
        log(f"  goes on straight when held {min(ok):.1f} to {max(ok):.1f} high" if ok else "  never goes on straight")
        for lift in (0.0, 6.0, 14.0):
            log(f"  control, held {lift} high: worst overlap going on {going_on(lift):.2f} mm3 (must hit)")
        pb = to_bed(Rot(90, 0, 0) * body) if orient == "back" else to_bed(Rot(0, 0, 180) * body)
        report_print("plate", pb)
        stem = f"{NAME}_{orient}"
        export_step(pb, str(out / f"{stem}_plate_print.step"))
        export_stl(pb, str(out / f"{stem}_plate_print.stl"))
        # One plate: the hooks first (short), then the plate a print-head clearance away (by-object order).
        hw = hp.bounding_box().size.X
        objs = [(f"hook {i + 1}", Pos(i * (hw + 10.0), 0, 0) * hp, P["print"]["hook"]) for i in range(U["hooks_on_plate"])]
        x_hooks = (U["hooks_on_plate"] - 1) * (hw + 10.0) + hw / 2
        objs.append(("plate", Pos(x_hooks + gap + pb.bounding_box().size.X / 2, 0, 0) * pb, P["orientations"][orient]["print"]))
        span = x_hooks + gap + pb.bounding_box().size.X + hw / 2
        objs = [(n, Pos(-span / 2 + hw / 2, 0, 0) * s, st) for n, s, st in objs]
        write_bambu_project([(f"{NAME} {orient}", objs)], out / f"{stem}_print.3mf", template=TEMPLATE)
        log(f"  {stem}_print.3mf: {U['hooks_on_plate']} hooks and the plate on one plate, {span:.0f} wide")
        if orient == "back":
            export_step(Compound(children=[body, *hks], label=f"{NAME} seated"), str(out / f"{NAME}_assembly_seated.step"))
            export_step(Compound(children=[Pos(0, 0, PUSH) * body, *hks], label=f"{NAME} pushed on"),
                        str(out / f"{NAME}_assembly_pushed_on.step"))
    (HERE / "report.txt").write_text("\n".join(lines) + "\n", newline="\n")
