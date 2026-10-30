# Segmented pocket test plate, layout A: one pocket column with a seat on every hook
# row (params.yaml says what each value is and where it came from). The plate hangs
# on a Bridge hook 1U in each of 3 rows: hold it `push` high, push it straight on
# (each head goes into its window), push it down `push` (the lips slide over the
# heads, the ridges click into the notches, every seat sits on a hook top).
# Pocket lips, ridges and hooks come from ../../hook_geometry.py and ../../panel.yaml.
# It prints on its back, pocket face down, like the drawer housing (Zeid, 2026-10-30).
# Run it from this folder with a plain build123d Python:
#     uv run --no-project --python 3.12 --with build123d --with pyyaml python build.py
# It writes test-prints/ (git-ignored: print STEP/STL, a Bambu Studio 3MF, the
# plate on its hooks seated and held at the push height) and report.txt.
# Coordinates: x across (the hooks' flat side at 0), y out from the panel face
# (plate back at y = 0), z up from the top hook's foot.
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
exec((ROOT / "core_3mf.py").read_text())
exec((ROOT.parent / "bambu" / "bambu_project.py").read_text())
TEMPLATE = ROOT.parent / "bambu" / "project_settings.config"

U, SG, PL, PK = P["unit"], P["segment"], P["plate"], P["pocket"]
NAME, ROWS = U["file_prefix"], U["rows"]
LIP, WINDOW, PUSH = SG["lip"], SG["window"], SG["push"]
pitch = panel["pitch"]
hook = panel["bridge_hook"]
HH = hook["height"]
dm = copy.deepcopy(panel["dovetail_mount"])
dv, pk = dm["dovetail"], dm["pocket"]
pk["spine_clearance"] = PK["spine_clearance"]
pk["flank_gap"] = PK["flank_gap"]
pk["ridge"]["height"] = PK["ridge_height"]

cx = dv["block_width"] / 2                                       # pocket centre
w_hook = max(dv["head_width"], dv["block_width"]) / 2            # hook front's half width
wp = w_hook + pk["side_clearance"]                               # pocket's half width
wn = dv["neck_width"] / 2 + pk["side_clearance"]                 # half width between the lips
yb = dv["block_depth"] + pk["spine_clearance"]                   # back of the lips
yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]     # pocket floor
seats = [HH - k * pitch for k in range(ROWS)]                    # hook tops, top row first
bw = dv["block_width"] / 2 + pk["side_clearance"]               # spine channel's half width
z_top = seats[0] + PL["top"]
z_bot = seats[-1] - LIP - WINDOW - SG["floor"]
assert LIP + WINDOW < pitch, "no roof left between segments"
assert PUSH >= LIP and PUSH + HH <= LIP + WINDOW, "head doesn't fit the window at the push height"
lines = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    lines.append(s)


def solid(s):
    sols = s.solids() if hasattr(s, "solids") else [s]
    assert len(sols) == 1, f"expected one solid, got {len(sols)}"
    return sols[0]


# ---------------------------------------------------------------- the plate
def segment(S):
    """Void for the seat at z = S: the shared pocket's lips and snap ridges for
    `lip` under the seat (closed flat seat on top), a 45 deg ramp on the lips'
    bottom ends, the full-width window under them, and the drawer housing's 45 deg
    gables on the spine channel's end and the pocket floor, so it prints on its back."""
    lips = pocket_void(dm, S, 0.0, S - LIP)
    zr, rp = S - LIP, wp - wn                                  # the ramp at 45 deg rises as far as the lips reach in
    e = 0.02    # ramp and gables start a hair outside the walls, on their 45 deg lines, so no flat strip is left
    ramp = Plane.XZ * Polygon((cx - wp - e, zr - e), (cx + wp + e, zr - e), (cx + wn, zr + rp), (cx - wn, zr + rp), align=None)
    ramp = Pos(0, yf, 0) * extrude(ramp, yf + 1)                # Plane.XZ extrudes toward -y: the pocket floor to past the back
    zw = zr - WINDOW
    window = Pos(cx, (yf - 1) / 2, (zw + zr) / 2) * Box(2 * wp, yf + 1, WINDOW)
    chan = Polygon((cx - bw - e, yb), (cx + bw + e, yb), (cx, yb + bw + e), align=None)
    floor = Polygon((cx - wp - e, yf), (cx + wp + e, yf), (cx, yf + wp + e), align=None)
    gables = Pos(0, 0, zw) * (extrude(chan, S - zw) + extrude(floor, S - zw))
    return lips + ramp + window + gables


def plate_body():
    hw = PL["half_width"]
    d = yf + wp + PL["front_wall"]                             # floor gable's apex + the front wall
    body = Pos(cx, d / 2, (z_top + z_bot) / 2) * Box(2 * hw, d, z_top - z_bot)
    body = chamfer(body.edges(), PL["chamfer"])
    for S in seats:
        body = solid(body - segment(S))
    body.label = NAME
    return body


def hooks():
    hk = bridge_hook(panel, ROOT)
    out = []
    for k in range(ROWS):
        h = Pos(0, -hook["panel_front_y"], -k * pitch) * hk
        h.label = f"hook {k + 1}"
        out.append(h)
    return out


def overlap(a, b):
    r = a & b
    return sum(s.volume for s in r.solids()) if r is not None else 0.0


def to_bed(s):
    bb = s.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * s


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


# ---------------------------------------------------------------- build
if __name__ == "__main__":
    out = HERE / "test-prints"
    out.mkdir(exist_ok=True)
    body = plate_body()
    hks = hooks()
    bb = body.bounding_box()
    log(f"{NAME}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {body.volume:.1f} mm3, valid {body.is_valid}; "
        f"{ROWS} seats at z {[round(s, 2) for s in seats]} (hook tops), each: lips {LIP} (45 deg ramp {wp - wn:.2f}), "
        f"window {WINDOW}, roof {pitch - LIP - WINDOW:.1f}")
    # Fit against the hooks: seated, going on at the push height, pushed down.
    log(f"seated: overlap with each hook {[round(overlap(body, h), 3) for h in hks]} mm3")
    sweep = [12, 9, 7, 6, 5, 4, 3, 2.5, 2, 1.5, 1, 0.5, 0.25, 0]
    def going_on(lift):
        return max(overlap(Pos(0, dy, lift) * body, h) for dy in sweep for h in hks)
    log(f"held {PUSH} high, pushed straight on from 12 mm out: worst overlap {going_on(PUSH):.4f} mm3")
    down = [max(overlap(Pos(0, 0, PUSH * i / 24) * body, h) for h in hks) for i in range(25)]
    log(f"pushed down {PUSH} to seated: worst overlap {max(down):.3f} mm3 per hook (the snap ridges riding over the heads)")
    ok = [l / 20 for l in range(60, 121) if going_on(l / 20) < 1e-4]
    log(f"goes on straight when held {min(ok):.2f} to {max(ok):.2f} high" if ok else "never goes on straight")
    for lift in (0.0, 2.0, 6.0):
        log(f"control, held {lift} high: worst overlap going on {going_on(lift):.2f} mm3 (must hit)")
    # Print orientation: on its back, the back face (panel side) on the bed, front up, as the drawer housing.
    pb = to_bed(Rot(90, 0, 0) * body)
    worst, bad = downward(pb)
    log(f"print: flattest downward face {worst:.1f} deg from vertical, faces flatter than 45 deg: {len(bad)}")
    for b in sorted(bad, key=lambda t: -t[1])[:8]:
        log(f"    {b[0]} deg, {b[1]} mm2 at ({b[2].X:.1f}, {b[2].Y:.1f}, {b[2].Z:.1f})")
    export_step(pb, str(out / f"{NAME}_print.step"))
    export_stl(pb, str(out / f"{NAME}_print.stl"))
    write_bambu_project([(NAME, [("plate", pb, P["print"].get("plate") or {})])], out / f"{NAME}_print.3mf",
                        template=TEMPLATE, settings=P["print"]["project"])
    export_step(Compound(children=[body, *hks], label=f"{NAME} seated"), str(out / f"{NAME}_assembly_seated.step"))
    export_step(Compound(children=[Pos(0, 0, PUSH) * body, *hks], label=f"{NAME} pushed on"),
                str(out / f"{NAME}_assembly_pushed_on.step"))
    (HERE / "report.txt").write_text("\n".join(lines) + "\n")
