# Plate handle for the arc drawer, like Zeid's HANDLE H2: a plate leaning out from the
# face on a stand-off rib, held by two printed snap pins that push through the face from
# inside and click into sockets in the rib's end bosses. Shared by build.py (the drawers)
# and handle_test.py (the test print); exec'd into them, so it uses their build123d import.
# Frame: x across the face (0 = the handle's middle), y out of the face (its front at
# y = 0), z up (0 = the handle's top). T is the params.yaml handle: section.
import math


def tear_xz(r):
    """Teardrop section in the x-z plane (point up), radius r."""
    c = r / math.sqrt(2)
    return Circle(r) + Polygon((-c, c), (0, math.sqrt(2) * r), (c, c), align=None)


def bore_y(sec, y0, y1, x, z):
    """Extrude a section drawn in the x-z plane along +y from y0 to y1, centred (x, z)."""
    return Pos(x, y0, z) * extrude(Plane.XZ * sec, y1 - y0, dir=(0, 1, 0))


def handle_face_cut(T, ft):
    """What to cut from a drawer face `ft` thick for the handle: a hole for each pin, cut to
    the pin's width, with a counterbore for its head on the inside; teardrops, point up."""
    zb, cut = -T["socket_down"], None
    for x in (-T["boss_x"], T["boss_x"]):
        c = bore_y(tear_xz(T["hole"] / 2) & Rectangle(T["hole_width"], 20), -ft - 1, 1, x, zb)
        c = c + bore_y(tear_xz(T["counterbore"] / 2), -ft - 1, -ft + T["counterbore_depth"], x, zb)
        cut = c if cut is None else cut + c
    return cut


def handle_part(T):
    """Plate leaning `lean` out from the face, hung from a rib that stands it `standoff` off the
    face; the rib grows into a flat-topped boss at each end holding a socket for a snap pin."""
    W, L, t, so = T["width"], T["drop"], T["thickness"], T["standoff"]
    lean = math.radians(T["lean"])
    # Plate, built upright (x across, y its thickness, z up along it), then leaned out about its top inner edge
    pl = Box(W, t, L + 3, align=(Align.CENTER, Align.MIN, Align.MAX))
    pl = Pos(0, 0, 3) * pl
    pl = fillet(pl.edges().filter_by(Axis.Y).filter_by(lambda e: e.center().Z < -L + 0.1), T["corner_radius"])
    h = Pos(0, so, 0) * Rot(T["lean"], 0, 0) * pl
    # Rib, front-view section: middle bar, tapers tangent to the bosses, bosses flat on top and round below
    r, rb, zc = T["boss"] / 2, T["rib"], T["boss_height"] - T["boss"] / 2   # zc: boss's round end's centre below the top
    sec = Rectangle(2 * T["boss_x"], rb, align=(Align.CENTER, Align.MAX))
    xs = (-T["boss_x"], T["boss_x"])
    for x in xs:
        sec = sec + Pos(x, -zc) * Circle(r) + Pos(x, 0) * Rectangle(2 * r, zc, align=(Align.CENTER, Align.MAX))
        q = (abs(x) - T["taper"], -rb)               # taper starts here on the rib's underside
        dx, dz = abs(x) - q[0], -zc - q[1]
        d = math.hypot(dx, dz)
        a = math.atan2(dz, dx) - math.asin(r / d)     # lower tangent from q to the boss circle
        tx, tz = q[0] + math.sqrt(d * d - r * r) * math.cos(a), q[1] + math.sqrt(d * d - r * r) * math.sin(a)
        sx = math.copysign(1, x)
        sec = sec + Polygon((sx * q[0], q[1]), (sx * tx, tz), (sx * abs(x), -zc), (sx * abs(x), q[1]), align=None)
    rib = Pos(0, 0, 0) * extrude(Plane.XZ * sec, so + t, dir=(0, 1, 0))
    h = h + rib
    # Keep the rib inside the plate's outer face, and nothing above the top
    h = h & (Pos(0, so, 0) * Rot(T["lean"], 0, 0) * Box(200, 200, 200, align=(Align.CENTER, Align.MAX, Align.CENTER)).moved(Location((0, t, 0))))
    h = h & Pos(0, 0, 0) * Box(200, 200, 200, align=(Align.CENTER, Align.CENTER, Align.MAX))
    # 45 deg chamfers on the top corners (on the bed as printed)
    c = T["top_chamfer"]
    for sx in (-1, 1):
        tri = Polygon((sx * (W / 2 + 1), 1), (sx * (W / 2 + 1), -c - 1), (sx * (W / 2 - c - 1), 1), align=None)
        h = h - Pos(0, -1, 0) * extrude(Plane.XZ * tri, 40, dir=(0, 1, 0))
    # Sockets: teardrops pointing down in use (up as printed); the shoulder at entry depth is vertical as printed
    flip = Rot(0, 0, 180)
    for x in xs:
        h = h - bore_y(flip * (tear_xz(T["socket_entry"] / 2) & Rectangle(T["hole_width"], 20)), -1, T["socket_entry_depth"] + 0.01, x, -T["socket_down"])
        h = h - bore_y(flip * tear_xz(T["socket_chamber"] / 2), T["socket_entry_depth"], T["socket_depth"], x, -T["socket_down"])
    return h


def handle_pin(T, ft, barb, notches=0):
    """Snap pin, axis along +y from the head's back face at y = 0, lying on a flat (as printed;
    fitted turned a quarter turn, flats sideways, so the legs spring up and down)."""
    r, rb, hr, ht = T["shank"] / 2, barb / 2, T["head"] / 2, T["head_thick"]
    tr = math.tan(math.radians(T["barb_ramp"]))
    rc = T["socket_entry"] / 2 + T["barb_preload"]   # ramp radius that sits on the shoulder edge
    ub = ft + T["socket_entry_depth"] + (rb - rc) * tr   # barb's full radius starts here
    ub0 = ub - (rb - r) * tr
    uf = ub + T["barb_flat"]
    ut = uf + (rb - T["tip"])
    prof = Polygon((0, 0), (0, hr), (ht, hr), (ht, r), (ub0, r), (ub, rb), (uf, rb), (ut, T["tip"]), (ut, 0), align=None)
    body = Rot(0, 0, 90) * revolve(Plane.XY * prof, Axis.X)
    body = body & Box(30, 60, T["flats"])
    body = body - Pos(0, (T["slot_start"] + ut + 1) / 2, 0) * Box(T["slot"], ut + 1 - T["slot_start"], 10)
    n = T.get("id_notch", 0)
    for sx in (1, -1)[:notches]:                     # V notch through the head at one end (B) or both (C)
        body = body - extrude(Polygon((sx * (hr + 1), -0.5), (sx * (hr - n), ht / 2), (sx * (hr + 1), ht + 0.5), align=None), 10, both=True)
    return body


def scoop_pins_part(T):
    """Zeid's scoop look as a separate part on the same snap pins: a hollow hood, open below,
    whose top slopes 45 deg down from the face to a front lip and whose sides taper from
    `width` at the face to `front_width` at the lip. Its back is a plate that sits `recess`
    deep in the face. The sockets are tubes in the hood's back corners, out of the finger's way.
    T is the plate handle's section with params.yaml scoop_pins: on top."""
    W0, WF, L, H, rec, t, lip = T["width"], T["front_width"], T["reach"], T["height"], T["recess"], T["wall"], T["lip"]
    k = t * math.sqrt(2)                             # wall thickness measured vertically under the 45 deg top
    plan = Polygon((-W0 / 2, -rec), (W0 / 2, -rec), (W0 / 2, 0), (WF / 2, L), (-WF / 2, L), (-W0 / 2, 0), align=None)
    # The back plate's top edge is cut back 45 deg, continuing the top's slope into the face, so the
    # recess's ceiling in the face is 45 deg too (the drawer prints upright)
    side = Polygon((-rec, -rec), (0, 0), (L, -L), (L, -L - lip), (0, -H), (-rec, -H), align=None)
    outer = (Pos(0, 0, -H - 1) * extrude(plan, H + 2)) & extrude(Plane.YZ * side, W0 / 2 + 1, both=True)
    r = T.get("round", 0)
    if r > 0:
        # Round every edge that shows (out from the face); the back plate in the recess keeps its edges
        outer = outer.fillet(r, outer.edges().filter_by(lambda e: e.center().Y > 0.05))
    # Hollow: side walls `wall` thick (along x), roof `wall` thick under the 45 deg top, open below and at the lip
    a = t * math.hypot(W0 - WF, 2 * L) / (2 * L)
    cplan = Polygon((-W0 / 2 + a, 0), (W0 / 2 - a, 0), (WF / 2 - a, L + 1), (-WF / 2 + a, L + 1), align=None)
    cside = Polygon((0, -k), (L + 2, -L - 2 - k), (L + 2, -H - 5), (0, -H - 5), align=None)
    cav = (Pos(0, 0, -H - 6) * extrude(cplan, H + 8)) & extrude(Plane.YZ * cside, W0 / 2 + 1, both=True)
    h = outer - cav
    # Socket tubes, kept inside the hood's outline, then the sockets: entry cut to the pin's width,
    # the shoulder at the face plane, a chamber just past the barbs, closed by a 45 deg cone
    # (the tubes stand upright as printed, so the cone is the chamber's roof)
    za, ent = -T["socket_down"], T["socket_entry_depth"]
    tr = math.tan(math.radians(T["barb_ramp"]))
    rc = T["socket_entry"] / 2 + T["barb_preload"]
    cyl = (T["barb"] / 2 - rc) * tr + T["barb_flat"] + T["chamber_past_barbs"]
    rch = T["socket_chamber"] / 2
    for x in (-T["boss_x"], T["boss_x"]):
        tube = bore_y(Circle(T["tube"] / 2), -rec, T["tube_end"], x, za) & outer
        h = h + tube
    for x in (-T["boss_x"], T["boss_x"]):
        y0 = -rec + ent
        h = h - bore_y(Circle(T["socket_entry"] / 2) & Rectangle(T["hole_width"], 20), -rec - 1, y0 + 0.01, x, za)
        prof = Polygon((0, y0 - 0.01), (rch, y0 - 0.01), (rch, y0 + cyl), (0, y0 + cyl + rch), align=None)
        h = h - Pos(x, 0, za) * revolve(Plane.XY * prof, Axis.Y)
    return h


def scoop_pins_face_cut(T, ft):
    """The pin holes and counterbores (as for the plate handle) and the recess the scoop's back sits in."""
    c, rec, H = T["recess_clearance"], T["recess"], T["height"]
    k = c * math.sqrt(2)                             # ceiling at 45 deg, `c` clear of the scoop's cut-back top edge
    prof = Polygon((1, k + 1), (-rec, k - rec), (-rec, -H - c), (1, -H - c), align=None)
    return handle_face_cut(T, ft) + extrude(Plane.YZ * prof, T["width"] / 2 + c, both=True)


def pull_part(T):
    return scoop_pins_part(T) if T.get("kind") == "scoop_pins" else handle_part(T)


def pull_face_cut(T, ft):
    return scoop_pins_face_cut(T, ft) if T.get("kind") == "scoop_pins" else handle_face_cut(T, ft)


def pull_print_rot(T):
    """Print orientation: the scoop on its back, the plate handle on its top."""
    return Rot(90, 0, 0) if T.get("kind") == "scoop_pins" else Rot(180, 0, 0)
