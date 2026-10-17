"""Draw panel-diagram.svg: a to-scale 4 x 4 cell view of the Omniwall panel and a
dimensioned close-up of one cell. All sizes come from panel.yaml.

    python diagram.py
"""
from pathlib import Path

import yaml

HERE = Path(__file__).parent
p = yaml.safe_load((HERE / "panel.yaml").read_text())

P = p["pitch"]                    # grid pitch
W = p["slot"]["width"]
L = p["slot"]["length"]
D = p["peg_hole"]["diameter"]
C = P / 2                         # hole centre to slot centreline
INNER = C - W / 2                 # hole centre to slot inner edge
HALF_L = L / 2
CELLS = 4

INK = "#222"
DIM = "#1f5fbf"
PANEL = "#d9dde2"
CUT = "#ffffff"
FONT = "font-family='Helvetica, Arial, sans-serif'"

out = []


def fmt(v):
    return f"{v:.1f}" if abs(round(v, 1) - v) < 1e-9 else f"{v:.2f}"


class View:
    """Maps panel mm (origin at a hole centre, y down) to drawing units."""

    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def pt(self, x, y):
        return self.ox + x * self.s, self.oy + y * self.s


def slots_around(cx, cy):
    """The four slots of the cell centred on (cx, cy), as (x0, y0, x1, y1)."""
    return [
        (cx + INNER, cy - HALF_L, cx + INNER + W, cy + HALF_L),   # right
        (cx - INNER - W, cy - HALF_L, cx - INNER, cy + HALF_L),   # left
        (cx - HALF_L, cy - INNER - W, cx + HALF_L, cy - INNER),   # top
        (cx - HALF_L, cy + INNER, cx + HALF_L, cy + INNER + W),   # bottom
    ]


def rect(v, x0, y0, x1, y1, fill, stroke=INK, sw=0.35, extra=""):
    ax, ay = v.pt(x0, y0)
    bx, by = v.pt(x1, y1)
    out.append(f"<rect x='{ax:.3f}' y='{ay:.3f}' width='{bx - ax:.3f}' height='{by - ay:.3f}' "
               f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}' {extra}/>")


def circle(v, x, y, r, fill=CUT, sw=0.35):
    cx, cy = v.pt(x, y)
    out.append(f"<circle cx='{cx:.3f}' cy='{cy:.3f}' r='{r * v.s:.3f}' fill='{fill}' "
               f"stroke='{INK}' stroke-width='{sw}'/>")


def line(ax, ay, bx, by, color=DIM, sw=0.3, dash=None, marker=False):
    d = f" stroke-dasharray='{dash}'" if dash else ""
    m = " marker-start='url(#a)' marker-end='url(#a)'" if marker else ""
    out.append(f"<line x1='{ax:.3f}' y1='{ay:.3f}' x2='{bx:.3f}' y2='{by:.3f}' "
               f"stroke='{color}' stroke-width='{sw}'{d}{m}/>")


def text(x, y, s, size=3.4, anchor="middle", rot=0, color=DIM, weight="normal"):
    r = f" transform='rotate({rot} {x:.3f} {y:.3f})'" if rot else ""
    out.append(f"<text x='{x:.3f}' y='{y:.3f}' font-size='{size}' text-anchor='{anchor}' "
               f"fill='{color}' font-weight='{weight}' {FONT}{r}>{s}</text>")


def hdim(v, x0, x1, y, label, ext_from=None, side=-1):
    """Horizontal dimension at panel height y. ext_from: panel y the extension lines start at."""
    ax, ay = v.pt(x0, y)
    bx, _ = v.pt(x1, y)
    if ext_from is not None:
        _, ey = v.pt(0, ext_from)
        for x in (ax, bx):
            line(x, ey, x, ay + side * 1.2, sw=0.2)
    line(ax, ay, bx, ay, marker=True)
    text((ax + bx) / 2, ay + (-1.2 if side < 0 else 4.2), label)


def vdim(v, y0, y1, x, label, ext_from=None, side=-1):
    """Vertical dimension at panel x. ext_from: panel x the extension lines start at."""
    ax, ay = v.pt(x, y0)
    _, by = v.pt(x, y1)
    if ext_from is not None:
        ex, _ = v.pt(ext_from, 0)
        for y in (ay, by):
            line(ex, y, ax + side * 1.2, y, sw=0.2)
    line(ax, ay, ax, by, marker=True)
    tx = ax + (-1.2 if side < 0 else 3.6)
    text(tx, (ay + by) / 2, label, rot=-90)


# ---- left: 4 x 4 grid, to scale ------------------------------------------
G = View(46, 76, 1.45)
span = (CELLS - 1) * P
margin = 6.0
rect(G, -C - margin, -C - margin, span + C + margin, span + C + margin, PANEL,
     stroke="#8a9099", sw=0.35, extra="stroke-dasharray='2 1.2'")
for i in range(CELLS):
    for j in range(CELLS):
        for s in slots_around(i * P, j * P):
            rect(G, *s, CUT)
        circle(G, i * P, j * P, D / 2)

# Shared slots are drawn twice; that's fine for a filled-white cutout.
hdim(G, 0, P, -C - margin - 6, f"{fmt(P)} pitch", ext_from=-C - 1)
hdim(G, -C, span + C, -C - margin - 14, f"{fmt(CELLS * P)} ({CELLS} cells, slot centreline to centreline)",
     ext_from=-C - margin - 6)
vdim(G, 0, P, -C - margin - 6, f"{fmt(P)} pitch", ext_from=-C - 1)
gx, gy = G.pt(-C - margin, span + C + margin)
text(gx, gy + 6, "4 × 4 cells, to scale. Outlined cell is enlarged on the right. Panel edge margin not known.",
     size=3.2, anchor="start", color=INK)
tx, ty = G.pt(-C - margin, -C - margin - 22)
text(tx, ty - 4, "Omniwall panel grid", size=5, anchor="start", color=INK, weight="bold")

# Mark the cell enlarged on the right.
rect(G, -C, -C, C, C, "none", stroke=DIM, sw=0.4, extra="stroke-dasharray='1.5 1'")

# ---- right: one cell enlarged, dimensioned -------------------------------
S = 4.0
WIN_S = 20.0 * S
V = View(G.pt(span + C + margin, 0)[0] + 20 + WIN_S, G.pt(0, span / 2)[1], S)   # beside the grid, centred
WIN = 20.0                                        # panel mm shown around the hole
wx0, wy0 = V.pt(-WIN, -WIN)
out.append(f"<clipPath id='win'><rect x='{wx0:.3f}' y='{wy0:.3f}' width='{2 * WIN * S:.3f}' "
           f"height='{2 * WIN * S:.3f}'/></clipPath>")
out.append("<g clip-path='url(#win)'>")
rect(V, -WIN, -WIN, WIN, WIN, PANEL, stroke="none")
for i in (-1, 0, 1):
    for j in (-1, 0, 1):
        for s in slots_around(i * P, j * P):
            rect(V, *s, CUT, sw=0.4)
for x in (-C, C):   # slot centrelines
    a = V.pt(x, -WIN)
    b = V.pt(x, WIN)
    line(*a, *b, color="#8a9099", sw=0.2, dash="3 1 0.6 1")
for y in (-C, C):
    a = V.pt(-WIN, y)
    b = V.pt(WIN, y)
    line(*a, *b, color="#8a9099", sw=0.2, dash="3 1 0.6 1")
out.append("</g>")
rect(V, -WIN, -WIN, WIN, WIN, "none", stroke="#8a9099", sw=0.35)
circle(V, 0, 0, D / 2, sw=0.4)
a = V.pt(-D / 2 - 1.5, 0)
b = V.pt(D / 2 + 1.5, 0)
line(*a, *b, color=INK, sw=0.15)
a = V.pt(0, -D / 2 - 1.5)
b = V.pt(0, D / 2 + 1.5)
line(*a, *b, color=INK, sw=0.15)

# Hole diameter, with a leader.
hx, hy = V.pt(-D / 2 * 0.707, -D / 2 * 0.707)
line(hx, hy, hx - 9, hy - 9, sw=0.25)
text(hx - 9.5, hy - 9.5, f"Ø{fmt(D)} peg hole", anchor="end")

# Hole centre to slot centreline and to slot inner edge.
hdim(V, 0, C, -4.8, f"{fmt(C)} to centreline", ext_from=-0.5)
hdim(V, 0, INNER, 5.2, f"{fmt(INNER)} to inner edge", ext_from=0.5, side=1)

# Slot width and length.
hdim(V, INNER, INNER + W, -HALF_L - 2.2, f"{fmt(W)}", ext_from=-HALF_L)
vdim(V, -HALF_L, HALF_L, -INNER - W - 2.2, f"{fmt(L)} slot length", ext_from=-INNER - W)

# Clear gap between parallel slots.
hdim(V, -INNER, INNER, -16.3, f"{fmt(P - W)} clear between slots", ext_from=-HALF_L)

# Hole edge to slot.
vdim(V, D / 2, INNER, -4.2, f"{fmt(INNER - D / 2)}", ext_from=-0.4)

# Gap between in-line slot ends (along the right slot centreline).
vdim(V, HALF_L, P - HALF_L, C, f"{fmt(P - L)}", side=1)

# Corner gap between a slot end and the crossing slot.
hdim(V, HALF_L, INNER, -C, f"{fmt(INNER - HALF_L)}", side=-1)

dx, dy = V.pt(-WIN, -WIN)
text(dx, dy - 4, f"One cell, enlarged {S / G.s:.1f}×", size=5, anchor="start",
     color=INK, weight="bold")
ex, ey = V.pt(-WIN, WIN)
for k, note in enumerate([
    "All dimensions in mm. Slots assumed centred on each cell edge.",
    "Not known yet: panel thickness, slot end shape (drawn square), hole depth.",
]):
    text(ex, ey + 6 + k * 4.6, note, size=3.2, anchor="start", color=INK)

# ---- assemble --------------------------------------------------------------
Wd, Ht = round(V.pt(WIN, 0)[0] + 12), round(V.pt(0, WIN)[1] + 20)
svg = (
    f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {Wd} {Ht}' width='{Wd * 4}' height='{Ht * 4}'>\n"
    "<defs><marker id='a' viewBox='0 0 10 10' refX='9' refY='5' markerUnits='userSpaceOnUse' markerWidth='2.6' markerHeight='2.6' "
    f"orient='auto-start-reverse'><path d='M0,1 L9,5 L0,9 z' fill='{DIM}'/></marker></defs>\n"
    f"<rect width='{Wd}' height='{Ht}' fill='#fff'/>\n"
    + "\n".join(out)
    + "\n</svg>\n"
)
(HERE / "panel-diagram.svg").write_text(svg, encoding="utf-8")
