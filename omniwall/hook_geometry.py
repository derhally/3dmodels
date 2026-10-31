# Shared build123d helpers for the dovetail front every printed hook carries and
# the matching pocket in objects, exec'd by hook/build_hooks.py and
# pocket-test/pocket_plate.py so hooks and pockets always come from the same
# numbers (panel.yaml, dovetail_mount).
# Hook coordinates: x across (hook's flat side at 0), y out from the back of the
# hook, z up from the bottom of the foot.
import copy
import math


def pocket_columns(cells, pitch, edge, count=None):
    """x of the hook pocket columns across an object `cells` wide: one at every
    seam between cells (cells - 1), or `count` of them (Zeid, 2026-10-30): both
    end seams always, then pairs working inward from the edges, and for an odd
    count the centre seam. An odd count on an odd width (no centre seam) would be
    lopsided, so it is refused."""
    seams = list(range(1, cells))
    n = len(seams) if count is None else int(count)
    if n >= len(seams):
        keep = seams
    else:
        assert n >= 2, f"at least 2 pocket columns (asked for {n})"
        assert n % 2 == 0 or len(seams) % 2, (f"{n} pocket columns can't be centred on {cells} cells "
                                              "(Zeid, 2026-10-30: no lopsided layouts)")
        k = n // 2
        keep = seams[:k] + seams[len(seams) - k:]
        if n % 2:
            keep.append(cells // 2)
    return [s * pitch - edge for s in sorted(keep)]


def dovetail_xy(cx, y_front, y_back, head_half, neck_half, flat, flank_deg, z0, z1, front_chamfer=0.0):
    """Dovetail prism: flat-sided head at the front (y_front), flanks back to the
    neck, neck running back to y_back. Plan profile extruded from z0 to z1.
    front_chamfer bevels the head's front corner on the +x side (the top when the
    hook prints on its flat side); the bed-side corner stays square."""
    run = (head_half - neck_half) * math.tan(math.radians(flank_deg))
    y_flank = y_front - flat
    y_neck = y_flank - run
    fc = front_chamfer
    prof = Polygon((cx - neck_half, y_back), (cx + neck_half, y_back),
                   (cx + neck_half, y_neck), (cx + head_half, y_flank),
                   (cx + head_half, y_front - fc), (cx + head_half - fc, y_front),
                   (cx - head_half, y_front),
                   (cx - head_half, y_flank), (cx - neck_half, y_neck), align=None)
    return Pos(0, 0, z0) * extrude(prof, z1 - z0)


def v_groove_prism(x_face, inward, zc, y0, y1, depth, flank_deg, radius, embed=0.2):
    """Rounded V profile across z (centred on zc) on the face x = x_face, reaching
    `depth` in the direction `inward` (+1 or -1 in x), as a prism from y0 to y1.
    Used for the head's notches (cut away) and the pocket's ridges (left in)."""
    th = math.radians(flank_deg)
    apex = depth + radius * (1 / math.cos(th) - 1)   # sharp V depth before rounding
    a = (apex + embed) / math.tan(th)
    # Local u runs along z; local v = z_dir x x_dir points along `inward`.
    pl = Plane(origin=(x_face, y0, zc), x_dir=(0, 0, 1), z_dir=(0, inward, 0))
    v_tri = Polygon((-a, -embed), (a, -embed), (0, apex), align=None)
    tip = v_tri.vertices().sort_by(Axis.Y)[-1]
    sk = fillet(tip, radius)
    return extrude(pl * sk, amount=y1 - y0, dir=(0, 1, 0))


def hook_front(dm, H, y_panel, spine_start=None, pitch=None):
    """Spine and dovetail head for a hook whose panel front is at y_panel and whose
    front is H tall. The spine runs from spine_start (default: the panel front) to
    the neck, which always sits block_depth in front of the panel. With pitch,
    snap notches repeat every pitch down the front for as long as they fit, so
    they meet a housing's ridges at every hook row; none in between."""
    dv = dm["dovetail"]
    y0 = y_panel if spine_start is None else spine_start
    yb = y_panel + dv["block_depth"]
    yf = yb + dv["depth"]
    cx = dv["block_width"] / 2   # head centred on the hook
    hh, hn = dv["head_width"] / 2, dv["neck_width"] / 2
    bw = dv["block_width"]
    e = dv["edge_chamfer"]
    # Spine: as wide as the hook, so it passes through a slot while the hook is
    # tilted on. Chamfers on its end edges, but none on the flat (bed) side, so
    # its first layers keep their full footprint. Its front is under the neck.
    block = extrude(Polygon((0, y0), (bw, y0), (bw, yb), (0, yb), align=None), H)
    ends = Plane.XZ * Polygon((0, 0), (bw - e, 0), (bw, e), (bw, H - e), (bw - e, H), (0, H), align=None)
    block = block & Pos(0, yb + 1, 0) * extrude(ends, yb - y0 + 2)   # Plane.XZ extrudes toward -y
    head = dovetail_xy(cx, yf, yb - 0.05, hh, hn, dv["head_flat"], dv["flank_angle"], 0, H,
                       front_chamfer=dv["head_front_chamfer"])
    # Head's front face: chamfer its top edge (the bottom end stays square).
    face = Plane.YZ * Polygon((yb - 1, 0), (yf, 0), (yf, H - e), (yf - e, H), (yb - 1, H), align=None)
    head = head & Pos(-1, 0, 0) * extrude(face, 2 * hh + 2)
    # Lead-in: 45 degree chamfers on the head's sides at the top, down to the neck
    # width. Objects slide down from above, so the bottom end needs none.
    c = dv["end_chamfer"]
    lead = Plane.XZ * Polygon((cx - hh, 0), (cx + hh, 0), (cx + hh, H - c),
                              (cx + hh - c, H), (cx - hh + c, H), (cx - hh, H - c), align=None)
    lead = Pos(0, yf + 1, 0) * extrude(lead, yf - yb + 2)   # Plane.XZ extrudes toward -y
    head = head & lead
    # Snap notches across both sides of the head, stopping short of the front so
    # the head's strip on the bed stays in one piece.
    n = dv["notch"]
    y_flank_end = yf - dv["head_flat"] - (hh - hn) * math.tan(math.radians(dv["flank_angle"]))
    zcs = [H - n["below_top"]]
    while pitch and zcs[-1] - pitch >= n["repeat_min_z"]:
        zcs.append(zcs[-1] - pitch)
    for zc in zcs:
        for x_face, inward in ((cx + hh, -1), (cx - hh, 1)):
            head = head - v_groove_prism(x_face, inward, zc, y_flank_end, yf - n["front_land"],
                                         n["depth"], n["flank_angle"], n["bottom_radius"])
    return block + head, (cx, yb, yf)


def pocket_void(dm, H, y_panel, z_lo):
    """Cut-out in an object's back for one hook (front H tall, panel front at
    y_panel): a channel for the spine, so the object's back sits flush on the
    panel, then the dovetail slot with the snap ridges left in. Open from z_lo up
    to the closed top, which rests on the top of the hook."""
    dv, pk = dm["dovetail"], dm["pocket"]
    cx = dv["block_width"] / 2
    y0 = y_panel
    yb = y0 + dv["block_depth"] + pk["spine_clearance"]    # back of the lips behind the head
    yf = y0 + dv["block_depth"] + dv["depth"] + pk["depth_clearance"]
    sc = pk["side_clearance"]
    hh, hn = dv["head_width"] / 2 + sc, dv["neck_width"] / 2 + sc
    top = H + pk["top_clearance"]
    # The neck slot starts at the spine's front, so the neck (wider than the spine) clears.
    void = dovetail_xy(cx, yf, y0 + dv["block_depth"] - 0.1, hh, hn, dv["head_flat"] + pk["flank_gap"],
                       dv["flank_angle"], z_lo, top)
    r = pk["ridge"]
    zc = top - r["below_top"]
    # Ridges stop short of the head's unnotched front land.
    y_ridge_end = y0 + dv["block_depth"] + dv["depth"] - dv["notch"]["front_land"] - r["front_gap"]
    for x_face, inward in ((cx + hh, -1), (cx - hh, 1)):
        void = void - v_groove_prism(x_face, inward, zc, yb, y_ridge_end,
                                     r["height"], r["flank_angle"], r["tip_radius"])
    bw = dv["block_width"] / 2 + sc
    # The spine channel runs on up `tooth_notch` over the seat for Slot hook 1U's tooth.
    top_n = top + pk.get("tooth_notch", 0.0)
    channel = Pos(dv["block_width"] / 2, (y0 - 1 + yb) / 2, (z_lo + top_n) / 2) * Box(2 * bw, yb - y0 + 1, top_n - z_lo)
    return void + channel


def notch_gable(dm, H, y_panel):
    """45 deg gable over the tooth notch's flat top (pocket_void with its seat at H),
    for pockets printed upright: the spine channel's width, from behind the back face to the lips."""
    dv, pk = dm["dovetail"], dm["pocket"]
    cx, bw = dv["block_width"] / 2, dv["block_width"] / 2 + pk["side_clearance"]
    yb = y_panel + dv["block_depth"] + pk["spine_clearance"]
    zn, e = H + pk["top_clearance"] + pk.get("tooth_notch", 0.0), 0.02
    g = Plane.XZ * Polygon((cx - bw - e, zn - e), (cx + bw + e, zn - e), (cx, zn + bw + e), align=None)
    return Pos(0, y_panel - 1, 0) * extrude(g, -(yb - y_panel + 1))   # Plane.XZ extrudes toward -y; from y_panel - 1 to yb


def seat_rows(dm, rows, picked=None):
    """Hook rows with a seat, counted from the bottom (0) up: `picked` lists rows
    counted from the top (1 = top row), or None for the default: the top row only
    (one channel) on parts under segmented.min_rows, the top and the bottom row on
    taller ones (Zeid, 2026-10-31)."""
    sg = dm["segmented"]
    if picked is None:
        picked = [1] if rows < sg["min_rows"] else [1, rows]
    rs = sorted({rows - int(k) for k in picked}, reverse=True)
    assert rs and all(0 <= r < rows for r in rs), f"hook rows {picked} outside 1..{rows}"
    assert all(a - b >= sg["rows_apart"] for a, b in zip(rs, rs[1:])), \
        f"hook rows {picked}: seats must be {sg['rows_apart']}+ rows apart"
    return rs


def segmented_pocket_void(dm, seats, back=False, z_bottom=0.0):
    """Cut-out for one hook column with a seat at each z in `seats` (hook tops, as
    pocket_void's H, panel front at y = 0): under each seat the dovetail lips
    (segmented.lip, a 45 deg lead-in ramp at their bottom), the snap ridges under
    the seat and the tooth notch over it, and a full-width window under the lips
    (segmented.window) the head goes in by; under the lowest seat the pocket is
    open down past z_bottom instead. Printed upright (back False) each seat and
    notch gets a 45 deg gable; printed on its back (the drawer housing) the spine
    channel and the floor get 45 deg gables along their length. Print-tested as
    pocket-test/segmented's plate()."""
    dv, pk, sg = dm["dovetail"], dm["pocket"], dm["segmented"]
    lip, window = sg["lip"], sg["window"]
    cx = dv["block_width"] / 2
    w_hook = max(dv["head_width"], dv["block_width"]) / 2           # hook front's half width
    wp = w_hook + pk["side_clearance"]                              # pocket's (and spine channel's) half width
    wn = dv["neck_width"] / 2 + pk["side_clearance"]                # half width between the lips
    yb = dv["block_depth"] + pk["spine_clearance"]                  # back of the lips
    yf = dv["block_depth"] + dv["depth"] + pk["depth_clearance"]    # pocket floor
    notch = pk.get("tooth_notch", 0.0)
    e = 0.02    # ramps and gables start a hair outside the walls on their 45 deg lines, so no flat strip is left

    def channel(z0, z1):
        v = Pos(cx, (yb - 1) / 2, (z0 + z1) / 2) * Box(2 * wp, yb + 1, z1 - z0)
        if back:
            v = v + Pos(0, 0, z0) * extrude(Polygon((cx - wp - e, yb), (cx + wp + e, yb), (cx, yb + wp + e), align=None), z1 - z0)
        return v

    void = None
    seats = sorted(seats, reverse=True)
    for S in seats:
        last = S == seats[-1]
        zr = S - lip                                                # bottom of the lips
        zw = z_bottom - 1 if last else zr - window                  # bottom of the window (or past the part's bottom)
        ze = S - (wp - w_hook)                                      # gable eaves (upright)
        lips = pocket_void(dm, S, 0.0, zr)
        if not back:
            lips = lips & Pos(cx, yf / 2, (zr - 1 + ze) / 2) * Box(20, yf + 10, ze - zr + 1)
        ramp = Plane.XZ * Polygon((cx - wp - e, zr - e), (cx + wp + e, zr - e), (cx + wn, zr + wp - wn),
                                  (cx - wn, zr + wp - wn), align=None)
        ramp = Pos(0, yf, 0) * extrude(ramp, yf + 1)                 # Plane.XZ extrudes toward -y
        win = Pos(cx, (yf - 1) / 2, (zw + zr) / 2) * Box(2 * wp, yf + 1, zr - zw)
        top = S + notch if notch else (S if back else ze)
        seg = lips + ramp + win + channel(zw, top)
        if back:
            floor = Polygon((cx - wp - e, yf), (cx + wp + e, yf), (cx, yf + wp + e), align=None)
            seg = seg + Pos(0, 0, zw) * extrude(floor, S - zw)
        else:
            roof = extrude(Plane.XZ * Polygon((cx - wp - e, ze - e), (cx + wp + e, ze - e), (cx, ze + wp), align=None), -(yf + 1))
            seg = seg + Pos(0, -1, 0) * roof
            if notch:
                seg = seg + notch_gable(dm, S, 0.0)
        void = seg if void is None else void + seg
    return void


def hook_overlaps(body, hooks, lift=0.0, out=(0.0,)):
    """Worst overlap (mm3) of body, raised `lift` and `out` from the panel (each
    value tried), with any of the hooks."""
    worst = 0.0
    for dy in out:
        b = Pos(0, dy, lift) * body
        for h in hooks:
            r = b & h
            worst = max(worst, sum(s.volume for s in r.solids()) if r is not None else 0.0)
    return worst


def segmented_fit(dm, body, hooks):
    """(worst overlap pushing the part straight on held segmented.push high, worst
    overlap pushing it down to its seats, held heights it goes on straight at) for
    a part (or a slice of its back) on its seated hooks."""
    push = dm["segmented"]["push"]
    sweep = [12, 9, 7, 6, 5, 4, 3, 2.5, 2, 1.5, 1, 0.5, 0.25, 0]
    on = hook_overlaps(body, hooks, push, sweep)
    down = max(hook_overlaps(body, hooks, push * i / 20) for i in range(21))
    ok = [l / 2 for l in range(round(2 * (push - 4)), round(2 * (push + 6)) + 1)
          if hook_overlaps(body, hooks, l / 2, sweep) < 1e-4]
    return on, down, ok


def keep_below_y(shape, y, h):
    """The part of shape with y < y (everything behind that plane)."""
    return shape & Pos(10, y / 2 - 5, h / 2) * Box(40, y + 10, h + 10)


def bridge_hook(panel, root):
    """Bridge hook 1U as printed: measured back half plus the dovetail front."""
    dm, hook = panel["dovetail_mount"], panel["bridge_hook"]
    real = import_step(str(root / hook["step"]))
    H = hook["height"]
    front, _ = hook_front(dm, H, hook["panel_front_y"], pitch=panel["pitch"])
    return keep_below_y(real, hook["panel_front_y"], hook["height"]) + front


def slot_hook_body(panel, root, fill_gap=False):
    """Slot hook 1U's measured body as printed, without its dovetail front or
    rim notch: shorter cavity, thinner foot, chamfered finger. Hook coordinates,
    the slot's bottom edge at z = 0. fill_gap fills the cavity solid (Slot hook
    2U's top body, which has no snap) before chamfering, so the chamfer runs on
    down the back."""
    hook = panel["slot_hook_1u"]
    real = import_step(str(root / hook["step"]))
    H, cav, pr = hook["height"], hook["cavity"], hook["printed"]
    y_c, r = pr["cavity_front_y"], cav["fillet"]
    # Keep the body behind the shortened cavity's end; the spine closes the cavity there.
    body = keep_below_y(real, y_c, hook["finger_top"])
    # Thin the foot from the top so the shorter foot flexes like the original.
    body = body - Pos(0, (y_c - 1) / 2, (pr["foot_top"] + cav["bottom"]) / 2) * Box(20, y_c + 1, cav["bottom"] - pr["foot_top"])
    # Fillets in the cavity's two front corners, as on the original.
    cove = Plane.YZ * (Pos(y_c - r / 2, r / 2) * Rectangle(r, r) - Pos(y_c - r, r) * Circle(r))
    cove = extrude(cove, hook["thickness"])
    body = body + Pos(0, 0, pr["foot_top"]) * cove + Pos(0, 0, cav["top"]) * mirror(cove, Plane.XY)
    t, eps = hook["thickness"], 1e-3
    z_low = cav["top"]
    if fill_gap:
        # 0.1 past the cut face, overlapping the spine.
        body = body + extrude(Plane.YZ * Polygon((0, pr["foot_top"] - 0.1), (y_c + 0.1, pr["foot_top"] - 0.1),
                                                 (y_c + 0.1, cav["top"] + 0.1), (0, cav["top"] + 0.1), align=None), t)
        z_low = eps   # down to the foot's back corner, not its bottom (it rests on the steel)
    # Chamfer the finger and the body's top above the cavity: the edges on the top
    # side (x = thickness, up when printing) and the finger's top corners. None on
    # the flat (bed) side, and none on the cut face at y_c, where the front joins.
    def finger_edge(e):
        bb = e.bounding_box()
        if bb.min.Z < z_low - eps or bb.max.Z < z_low + eps or bb.max.Y > y_c + eps or bb.min.Y > y_c - eps:
            return False
        on_top_side = bb.min.X > t - eps
        top_corner = bb.max.X - bb.min.X > t - eps and bb.min.Z > hook["finger_top"] - eps
        return on_top_side or top_corner
    return chamfer([e for e in body.edges() if finger_edge(e)], pr["top_chamfer"])


def rim_notch_foot(hook, z):
    """Pieces that turn a foot whose bottom sits on a slot's bottom rim (at z) into
    a snap: (added, cut). The foot reaches below the rim with a notch cut up into
    it for the rim. The back lip's bottom is one ramp from the top of the foot's
    lead-in to the notch's back edge, so pushing the bottom in rides it over the
    rim until it drops into the notch. The notch's front edge is chamfered to
    guide the rim in. rim_notch.tip_land (optional) ends the ramp that far short
    of the notch, so the lip's tip is a flat instead of a knife edge."""
    pr, t = hook["printed"], hook["thickness"]
    rn, li, yp, y_c = pr["rim_notch"], hook["foot_lead_in"], hook["panel_front_y"], pr["cavity_front_y"]
    d, y_n, c = rn["depth"], yp - rn["width"], rn["mouth_chamfer"]
    y_r = y_n - rn.get("tip_land", 0.0)              # where the ramp meets the lip's bottom
    below = Plane.YZ * Polygon((0, li), (y_r, -d), (y_c, -d), (y_c, li), align=None)
    under_ramp = Plane.YZ * Polygon((-1, -d - 1), (y_r, -d - 1), (y_r, -d), (0, li), (-1, li), align=None)
    notch = Plane.YZ * Polygon((y_n, -d - 0.1), (yp + c, -d - 0.1), (yp + c, -d), (yp, -d + c),
                               (yp, 0), (y_n, 0), align=None)
    return Pos(0, 0, z) * extrude(below, t), Pos(0, 0, z) * (extrude(under_ramp, t) + extrude(notch, t))


def slot_hook_1u(panel, root):
    """Slot hook 1U as printed: measured body with a shorter cavity and a
    thinner foot, plus the dovetail front."""
    dm, hook = panel["dovetail_mount"], panel["slot_hook_1u"]
    H, y_c, d = hook["height"], hook["printed"]["cavity_front_y"], hook["printed"]["rim_notch"]["depth"]
    # Foot below the slot, with a notch for the slot's bottom rim.
    added, cut = rim_notch_foot(hook, 0)
    body = slot_hook_body(panel, root) + added - cut
    # The dovetail front reaches down to the same bottom, keeping its top (and
    # so the snap) where it was.
    front, _ = hook_front(dm, H + d, hook["panel_front_y"], spine_start=y_c, pitch=panel["pitch"])
    return body + Pos(0, 0, -d) * front + slot_tooth(hook)


def slot_tooth(hook):
    """Slot hook 1U's front tooth: over the slot's top edge in front of the steel,
    `gap` off it, so a part's back can't tip the hook's top into the slot while
    the part is fitted (Zeid, 2026-10-31). Profile in y-z across the hook's thickness."""
    T, H, YP = hook["printed"]["tooth"], hook["height"], hook["panel_front_y"]
    y0, y1, zt, c = YP + T["gap"], YP + T["depth"], H + T["height"], T["chamfer"]
    prof = Polygon((y0, H - T["below"]), (y1, H - T["below"]), (y1, zt), (y0 + c, zt), (y0, zt - c), align=None)
    return extrude(Plane.YZ * prof, hook["thickness"])


def slot_hook_2u(panel, root, lower_foot=None):
    """Slot hook 1U carried on down into the next slot in line (Zeid's idea,
    2026-10-18). The top is Slot hook 1U's body filling the upper slot, resting
    on that slot's bottom edge, with its finger behind the panel above it; no snap
    there. One pitch lower, Slot hook 1U's foot and rim-notch snap sit in the
    lower slot. A spine in front of the panel joins them across the steel between
    the slots, and one dovetail front runs the whole height, its top (and snap
    notches) where Slot hook 1U's are. A second notch pair one pitch lower
    sits where a Slot hook 1U's notches would be in the lower slot, so a housing
    with ridges for two rows of Slot hook 1Us clicks onto this hook too.
    lower_foot: overrides for the lower foot and its rim notch (foot_top,
    rim_notch keys), on top of slot_hook_2u.lower_foot, for snap test variants."""
    dm, hook, ts = panel["dovetail_mount"], panel["slot_hook_1u"], panel["slot_hook_2u"]
    H, yp, y_c, t = hook["height"], hook["panel_front_y"], hook["printed"]["cavity_front_y"], hook["thickness"]
    # The lower foot starts as Slot hook 1U's and takes slot_hook_2u.lower_foot's changes.
    lfh = copy.deepcopy(hook)
    for over in (ts.get("lower_foot") or {}, lower_foot or {}):
        lfh["printed"]["foot_top"] = over.get("foot_top", lfh["printed"]["foot_top"])
        lfh["printed"]["rim_notch"].update(over.get("rim_notch", {}))
    lft, d = lfh["printed"]["foot_top"], lfh["printed"]["rim_notch"]["depth"]
    zl = -ts["lower_rim_below"]                       # the lower slot's bottom rim
    # Lower foot: Slot hook 1U's foot (bottom on the rim, thinned top), a
    # cantilever off the spine so it flexes over the rim, with the rim notch below.
    foot = Pos(0, 0, zl) * extrude(Plane.YZ * Polygon((0, 0), (y_c, 0), (y_c, lft), (0, lft), align=None), t)
    added, cut = rim_notch_foot(lfh, zl)
    foot = foot + added - cut
    # Spine across the steel and down the lower slot: from the panel's front face
    # (Slot hook 1U body fills the upper slot behind y_c).
    fill = extrude(Plane.YZ * Polygon((yp, zl - d), (y_c, zl - d), (y_c, 0), (yp, 0), align=None), t)
    front, _ = hook_front(dm, H - zl + d, yp, spine_start=y_c, pitch=panel["pitch"])
    # Fillets in the inside corners where the bars meet the front (Zeid marked
    # them A, C and E on the side profile, 2026-10-18): under the top bar,
    # on the top body's foot, and at the root of the lower foot.
    cav, ft, fl = hook["cavity"], hook["printed"]["foot_top"], ts["fillets"]
    def cove(y, z, r, sz):
        """Fillet of radius r in the inside corner at (y, z), the open side
        toward -y and toward sz in z."""
        sq = Pos(y - r / 2, z + sz * r / 2) * Rectangle(r, r)
        return extrude(Plane.YZ * (sq - Pos(y - r, z + sz * r) * Circle(r)), t)
    coves = cove(yp, zl + lft, fl["lower_foot_root"], 1)
    # The top body has no snap, so its gap needn't flex: fill_top_gap fills it
    # solid (in slot_hook_body, so its back edge is chamfered all the way down).
    if not ts["fill_top_gap"]:
        coves = coves + cove(y_c, cav["top"], fl["under_top_bar"], -1) + cove(y_c, ft, fl["top_foot"], 1)
    # Reliefs at the corners the panel's edges sit in (D: the finger's front face
    # meets the top; F: the top body's underside meets the spine, over the steel
    # between the slots): a fillet would push into the steel, so a round groove
    # is cut into the hook instead, which takes the sharp corner out of it.
    out = slot_hook_body(panel, root, ts["fill_top_gap"]) + foot + fill + coves + Pos(0, 0, zl - d) * front
    # Chamfer the lower foot's free edges on the top side (its back, and its top
    # round to the spine), like the top body's, and on up the spine's back to
    # the top body, so the chamfer ends in a corner rather than a step. The
    # ramp and the rim notch, which ride over and hold the rim, stay square.
    if ts["lower_foot_chamfer"] > 0:
        eps, z0, z1 = 1e-3, zl + hook["foot_lead_in"], zl + lft + fl["lower_foot_root"]
        def foot_edge(e):
            bb = e.bounding_box()
            if bb.min.X < t - eps or bb.max.Y > yp + eps or bb.min.Z < z0 - eps:
                return False
            spine_back = bb.min.Y > yp - eps and bb.min.Z > z1 - eps and bb.max.Z < eps
            return bb.max.Z < z1 + eps or spine_back
        out = chamfer([e for e in out.edges() if foot_edge(e)], ts["lower_foot_chamfer"])
    for r, y, z in ((fl["d_relief"], hook["panel_back_y"], H), (fl["f_relief"], yp, 0.0)):
        if r > 0:
            out = out - extrude(Plane.YZ * Pos(y, z) * Circle(r), t)
    if ts.get("bed_chamfer"):
        # Chamfer the bed side like the top side: keep what the hook shares with
        # its mirror image across its mid-plane.
        out = out & mirror(out, Plane.YZ.offset(t / 2))
        out = out.solids()[0] if len(out.solids()) == 1 else out
    return out
