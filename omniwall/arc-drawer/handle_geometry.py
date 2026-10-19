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
