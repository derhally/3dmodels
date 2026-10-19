# Shared build123d helpers for the dovetail front every printed hook carries and
# the matching pocket in objects, exec'd by hook/build_hooks.py and
# pocket-test/pocket_plate.py so hooks and pockets always come from the same
# numbers (panel.yaml, dovetail_mount).
# Hook coordinates: x across (hook's flat side at 0), y out from the back of the
# hook, z up from the bottom of the foot.
import copy
import math


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
    channel = Pos(dv["block_width"] / 2, (y0 - 1 + yb) / 2, (z_lo + top) / 2) * Box(2 * bw, yb - y0 + 1, top - z_lo)
    return void + channel


def keep_below_y(shape, y, h):
    """The part of shape with y < y (everything behind that plane)."""
    return shape & Pos(10, y / 2 - 5, h / 2) * Box(40, y + 10, h + 10)


def bridge_hook(panel, root, size=1):
    """A bridge hook as printed: measured back half plus the dovetail front.
    size=1: Bridge hook 1U, the measured height. size=2: Bridge hook 2U, the
    front moved up (bridge_hook.front_2u) so its top and snap notches sit where
    Slot hook 1U's do, and housings take either hook."""
    dm, hook = panel["dovetail_mount"], panel["bridge_hook"]
    real = import_step(str(root / hook["step"]))
    H = hook["height"]
    if size == 2:
        # The front still runs down to the foot (it is the only link to it); its
        # notches repeat a pitch lower, where a housing's next ridges sit.
        H += hook["front_2u"]["rise"]
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
    return body + Pos(0, 0, -d) * front


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
