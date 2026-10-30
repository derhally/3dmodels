# Segmented pocket test: a plate with one pocket column and a seat on several hook rows,
# and the Slot hook 1U it hangs on, for each design in params.yaml (it says what each
# value is and where it came from). Hold the plate `push` high, push it straight onto the panel
# (each head goes into its window), push it down `push` (the lips slide over the
# heads, the ridges click into the notches, every seat sits on a hook top).
# short_head: Slot hook 1U with its dovetail head only on the top `head` mm; the
# plate's spine channel stays open from top to bottom, so the spine under each short
# head passes the roofs that seat the hooks below. skip_row: normal Slot hook 1U, a
# seat on every second row, solid wall between the segments. Pocket lips, ridges and hooks come
# from ../../hook_geometry.py and ../../panel.yaml.
# Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py
# It writes test-prints/ (git-ignored), per design: per print orientation (back: pocket face
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

U, PL = P["unit"], P["plate"]
ROWS = U["rows"]
pitch = panel["pitch"]
s1 = panel["slot_hook_1u"]
TOP = s1["height"]                                               # hook top: the slot's top edge
FRONT = s1["height"] + s1["printed"]["rim_notch"]["depth"]       # dovetail front, top to bottom
YP = s1["panel_front_y"]


class Design:
    """One segmented pocket design from params.yaml's designs."""
    def __init__(self, d):
        self.name = d["file_prefix"]
        self.head = d["head"] or FRONT                           # dovetail head length (null: the whole front)
        self.short = self.head < FRONT
        self.every, self.lip, self.window, self.push = d["every"], d["lip"], d["window"], d["push"]
        self.roof = self.every * pitch - self.lip - self.window   # solid between a window and the seat under it
        self.rows = list(range(0, ROWS, self.every))             # rows with a seat, top first
        self.seats = [TOP - k * pitch for k in self.rows]        # hook tops
        assert self.roof > 0, "no roof left between segments"
        assert self.lip <= self.head and self.push >= self.lip and self.push + self.head <= self.lip + self.window, \
            "the head doesn't fit the window at the push height"


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
def hook(D):
    """Slot hook 1U, its dovetail head cut off below the top D.head mm on a short-head
    design (the spine stays the full height). Panel front at y = 0, slot's bottom edge at z = 0."""
    dv = panel["dovetail_mount"]["dovetail"]
    h = slot_hook_1u(panel, ROOT)
    if D.short:
        y_neck = YP + dv["block_depth"]                          # the spine's front: neck and head start here
        cut = Pos(-5, y_neck, -5) * Box(20, 20, TOP - D.head + 5, align=Align.MIN)
        h = solid(h - cut)
    h = Pos(0, -YP, 0) * h
    h.label = "short-head slot hook 1U" if D.short else "slot hook 1U"
    return h


# ---------------------------------------------------------------- the plate
def plate(D, orient):
    """D's test plate for one print orientation ('back' or 'upright'), as it hangs."""
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
    seats, LIP, WINDOW = D.seats, D.lip, D.window
    z_top = seats[0] + wp + PL["top"]
    z_bot = seats[-1] - LIP - WINDOW - P["floor"]
    hw = PL["half_width"]
    body = Pos(cx, depth / 2, (z_top + z_bot) / 2) * Box(2 * hw, depth, z_top - z_bot)
    body = chamfer(body.edges(), PL["chamfer"])
    e = 0.02    # ramps and gables start a hair outside the walls on their 45 deg lines, so no flat strip is left
    def channel(z0, z1):
        """Spine channel from z0 to z1 (on its back with a 45 deg gable over it)."""
        v = Pos(cx, (yb - 1) / 2, (z0 + z1) / 2) * Box(2 * wp, yb + 1, z1 - z0)
        if back:
            chan = Polygon((cx - wp - e, yb), (cx + wp + e, yb), (cx, yb + wp + e), align=None)
            v = v + Pos(0, 0, z0) * extrude(chan, z1 - z0)
        return v
    # short head: the spine channel is open from the top seat out through the bottom, so
    # the spine under each short head passes the roofs. Upright it stops at the top
    # gable's eaves (no flat top). Full rail: a channel per segment, solid wall between.
    top_of = (lambda S: S) if back else (lambda S: S - (wp - w_hook))
    void = channel(z_bot - 1, top_of(seats[0])) if D.short else None
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
        if not D.short:
            seg = seg + channel(zw if S != seats[-1] else z_bot - 1, top_of(S))
        if back:
            floor = Polygon((cx - wp - e, yf), (cx + wp + e, yf), (cx, yf + wp + e), align=None)
            seg = seg + Pos(0, 0, zw) * extrude(floor, S - zw)
        else:
            roof = extrude(Plane.XZ * Polygon((cx - wp - e, ze - e), (cx + wp + e, ze - e), (cx, ze + wp), align=None), -(yf + 1))
            seg = seg + Pos(0, -1, 0) * roof
        void = seg if void is None else void + seg
    body = solid(body - void)
    body.label = f"{D.name} plate ({orient})"
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
def build(D, out, gap):
    NAME, LIP, WINDOW, PUSH = D.name, D.lip, D.window, D.push
    hk = hook(D)
    hks = []
    for k in D.rows:
        h = Pos(0, 0, -k * pitch) * hk
        h.label = f"hook row {k + 1}"
        hks.append(h)
    log(f"\n{NAME}: {hk.label}, head on the top {D.head:.1f} of its {FRONT:.1f} front, volume {hk.volume:.1f} mm3, valid {hk.is_valid}")
    hp = to_bed(Rot(Y=-90) * hk)                                 # on its flat side, as ../../hook/build_hooks.py
    report_print("hook", hp)
    export_step(hp, str(out / f"{NAME}_hook_print.step"))
    export_stl(hp, str(out / f"{NAME}_hook_print.stl"))
    log(f"{len(D.seats)} seats at z {[round(s, 2) for s in D.seats]} (hook tops = slot tops, rows {[k + 1 for k in D.rows]} of {ROWS}); "
        f"each: lips {LIP} (45 deg ramp at the bottom), window {WINDOW}, {'roof' if D.short else 'wall'} {D.roof:.1f}; push {PUSH}")
    sweep = [12, 9, 7, 6, 5, 4, 3, 2.5, 2, 1.5, 1, 0.5, 0.25, 0]
    for orient in ("back", "upright"):
        body, depth = plate(D, orient)
        bb = body.bounding_box()
        log(f"{orient}: plate {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {body.volume:.1f} mm3, valid {body.is_valid}")
        def going_on(lift):
            return max(overlap(Pos(0, dy, lift) * body, h) for dy in sweep for h in hks)
        log(f"  seated: overlap with each hook {[round(overlap(body, h), 3) for h in hks]} mm3 (the snap ridges, if any)")
        log(f"  held {PUSH} high, pushed straight on from 12 mm out: worst overlap {going_on(PUSH):.4f} mm3")
        down = [max(overlap(Pos(0, 0, PUSH * i / 30) * body, h) for h in hks) for i in range(31)]
        log(f"  pushed down {PUSH} to seated: worst overlap {max(down):.3f} mm3 per hook (the snap ridges riding over the heads)")
        lo, hi = round((PUSH - 5) * 10), round((PUSH + 5) * 10)
        ok = [l / 10 for l in range(lo, hi + 1) if going_on(l / 10) < 1e-4]
        log(f"  goes on straight when held {min(ok):.1f} to {max(ok):.1f} high" if ok else "  never goes on straight")
        for lift in (0.0, round(PUSH - 6, 1), round(PUSH + 6, 1)):
            log(f"  control, held {lift} high: worst overlap going on {going_on(lift):.2f} mm3 (must hit)")
        pb = to_bed(Rot(90, 0, 0) * body) if orient == "back" else to_bed(Rot(0, 0, 180) * body)
        report_print("plate", pb)
        stem = f"{NAME}_{orient}"
        export_step(pb, str(out / f"{stem}_plate_print.step"))
        export_stl(pb, str(out / f"{stem}_plate_print.stl"))
        # One plate: the hooks first (short), then the plate a print-head clearance away (by-object order).
        # The hooks are one object: printed by object, separate hooks 10 apart conflict once the
        # plate (taller than the nozzle) is on the bed too (Bambu Studio error -63 on zd-01).
        hw, n = hp.bounding_box().size.X, len(D.seats)
        hooks = Compound(children=[Pos(i * (hw + 10.0), 0, 0) * hp for i in range(n)])
        objs = [("hooks", hooks, P["print"]["hook"])]
        x_hooks = (n - 1) * (hw + 10.0) + hw / 2
        objs.append(("plate", Pos(x_hooks + gap + pb.bounding_box().size.X / 2, 0, 0) * pb, P["orientations"][orient]["print"]))
        span = x_hooks + gap + pb.bounding_box().size.X + hw / 2
        objs = [(nm, Pos(-span / 2 + hw / 2, 0, 0) * s, st) for nm, s, st in objs]
        write_bambu_project([(f"{NAME} {orient}", objs)], out / f"{stem}_print.3mf", template=TEMPLATE)
        log(f"  {stem}_print.3mf: {n} hooks (one object) and the plate on one plate, {span:.0f} wide")
        if orient == "back":
            export_step(Compound(children=[body, *hks], label=f"{NAME} seated"), str(out / f"{NAME}_assembly_seated.step"))
            export_step(Compound(children=[Pos(0, 0, PUSH) * body, *hks], label=f"{NAME} pushed on"),
                        str(out / f"{NAME}_assembly_pushed_on.step"))


if __name__ == "__main__":
    out = HERE / "test-prints"
    out.mkdir(exist_ok=True)
    gap = bambu_object_gap(TEMPLATE)
    for d in P["designs"].values():
        build(Design(d), out, gap)
    (HERE / "report.txt").write_text("\n".join(lines).lstrip("\n") + "\n", newline="\n")
