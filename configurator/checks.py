"""Reads a builder's report.txt and says, check by check, whether the part is
fine to print. The builders already measure everything (validity, hooks,
overhangs, the drawer's motion); this only grades those lines.

Each check: {"label", "status": "ok" | "warn" | "fail", "detail"}.
"""
import re

TEST_PRINTS = ("coupon", "fit_test", "snap_test", "band")      # test-prints/ parts: not part of the model


def _nums(text):
    return [float(x) for x in re.findall(r"(-?\d+(?:\.\d+)?) mm3", text)]


def evaluate(kind, report, cfg=None, ok=True, error=""):
    cfg = cfg or {}
    out = []

    def add(label, status, detail):
        out.append({"label": label, "status": status, "detail": detail})

    if not ok:
        add("Build", "fail", error or "build.py stopped")
        return out
    add("Build", "ok", "build.py finished")

    lines = report.splitlines()

    # every solid valid (the builders log "valid True" per part)
    bad = [l.split(":")[0] for l in lines if "valid False" in l]
    n = sum("valid True" in l for l in lines)
    add("Solids", "fail" if bad else "ok", ("not valid: " + ", ".join(bad)) if bad else f"{n} parts, all valid")

    # overhangs on the print parts (test prints left out); faces at expected
    # heights (the arc drawer's 0.4 hull slot roof) are fine to bridge
    flat_ok = cfg.get("expected_flat_z", [])
    worst, notes = "ok", []
    for i, l in enumerate(lines):
        m = re.match(r"(\S+_print):.*overhangs flatter than 45 deg: (\d+)", l)
        if not m or any(t in m.group(1) for t in TEST_PRINTS):
            continue
        faces = []
        for f in lines[i + 1:i + 1 + int(m.group(2))]:
            fm = re.search(r"([\d.]+) deg from vertical, area ([\d.]+) mm2, at \(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", f)
            if fm:
                faces.append((float(fm.group(1)), float(fm.group(2)), float(fm.group(5))))
        odd = [f for f in faces if not any(abs(f[2] - z) < 0.15 for z in flat_ok)]
        part = m.group(1).split("_")[-2]
        if odd:
            area = sum(f[1] for f in odd)
            status = "warn" if area < 25 else "fail"
            worst = "fail" if "fail" in (worst, status) else status
            notes.append(f"{part}: {len(odd)} face{'s' * (len(odd) > 1)} flatter than 45° ({area:.0f} mm²)")
        elif faces:
            notes.append(f"{part}: only the hull slot's roof (a 0.4 mm bridge)")
    add("Prints without supports", worst, "; ".join(notes) or "no face flatter than 45° on any part")

    # hooks: the builders model the Bridge hook 1U seated in every pocket
    for l in lines:
        m = re.match(r"hooks vs (\w+): ([\d.]+) mm3(?: total)? over (\d+)", l)
        if m:
            per = float(m.group(2)) / max(1, int(m.group(3)))
            add(f"Hooks fit the {m.group(1)}", "ok" if per <= 0.2 else "fail",
                f"{m.group(3)} hooks, {per:.2f} mm³ overlap each (the snap ridges)" if per > 0.001 else f"{m.group(3)} hooks, no overlap")

    # segmented pockets (hooks on chosen rows): the part goes straight on held up
    # by segmented.push, then pushes down onto its seats (ridges ride over the heads)
    for l in lines:
        m = re.search(r"segmented fitting: held ([\d.]+) high, pushed straight on: worst overlap ([\d.]+) mm3; pushed down "
                      r"[\d.]+: worst ([\d.]+) mm3 per hook.*goes on straight held (never|[\d.]+ to [\d.]+ high)"
                      r"; Bridge hook 1Us on the same seats: ([\d.]+) mm3", l)
        if m:
            on, down, br = float(m.group(2)), float(m.group(3)), float(m.group(5))
            good = on < 1e-3 and down <= 1.0
            add("Goes on its hooks", "ok" if good else "fail",
                (f"in through the windows held {m.group(1)} mm up, then down onto the seats "
                 f"({down:.2f} mm³ per hook where the snap ridges ride over); Bridge hook 1Us fit the same seats" + ("" if br < 1 else f" ({br:.1f} mm³)"))
                if good else f"pushed on: {on:.2f} mm³ overlap, pushed down: {down:.2f} mm³ per hook")

    # grids: seated without play, ridges in their grooves
    for l in lines:
        m = re.search(r"grid vs bin seated: overlap ([\d.]+) mm3.*clearance ([\d.]+)", l)
        if m:
            add("Insert snaps in", "ok" if float(m.group(1)) < 10 else "fail", "spring tabs seat in their grooves")
        m = re.search(r"thinnest rib between holes ([\d.]+), thinnest frame at the edge ([\d.]+)", l)
        if m:
            rib = min(float(m.group(1)), float(m.group(2)))
            add("Insert ribs", "ok" if rib >= 1.6 else "warn", f"thinnest rib {rib:.1f} mm" + ("" if rib >= 1.6 else " (under 4 perimeters)"))

    # lean bins: tips over on the bed?
    for l in lines:
        if l.startswith("on the bed: centre of mass"):
            over = "over the foot" in l
            add("Stands on the bed", "ok" if over else "fail", "centre of mass over the foot" if over else "centre of mass outside the foot: it tips over")
        m = re.search(r"front leans ([\d.]+) deg", l)
        if m:
            a = float(m.group(1))
            add("Front lean", "ok" if a <= 45 else "fail", f"{a:.0f}° from vertical" + ("" if a <= 45 else ", over 45°: needs supports"))

    # arc drawers: the drawer's whole path, and the drawer of the unit above
    moves = [l for l in lines if re.match(r"(closed|open|tilted|pushed): drawer vs housing", l)
             or l.startswith(("tilt sweep", "along the gate", "pulled out", "sliding"))]
    if moves:
        hit = max((x for l in moves for x in _nums(l.split(":", 1)[1] if l.startswith(("closed", "open", "tilted", "pushed")) else l)), default=0)
        add("Drawer moves freely", "ok" if hit < 0.01 else "fail",
            "closed, open, tilted, along the arc and out: no overlap" if hit < 0.01 else f"overlaps {hit:.1f} mm³ somewhere on its path")
    for l in lines:
        if l.startswith("drawer of the unit above"):
            hits = re.findall(r"(\w+(?: [\d.]+)?): ([\d.]+), [\d.]+", l.split("):", 1)[1])
            bad = [(s, float(v)) for s, v in hits if float(v) > 0.01]
            add("Clears the drawer above", "warn" if bad else "ok",
                ("its scoop meets the drawer above at the end of the pull (" + ", ".join(s for s, _ in bad) + "), as on main's drawers") if bad
                else "the scoop clears the drawer above all the way out")
    return out
