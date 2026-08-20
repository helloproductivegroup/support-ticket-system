#!/usr/bin/env python3
"""
Trifold traveler's journal cover templates - V2.

Changes from V1:
  * Double-row eyelet clusters. Two rows of three at each end of the spine
    (12 elastic holes per cover) instead of a single row of three.
  * 2.5 mm elastic holes for 2.5 mm eyelets; 3.0 mm closure hole.
  * Panels sized to the maker's actual inserts (6 x 8 in and 4.25 x 8.25 in)
    rather than to ISO paper.
  * Spine geometry is set by the eyelet FLANGE, not the hole. Both covers use
    the identical spine cluster so one punch/setting layout serves both.
  * PDFs are US Letter PORTRAIT tiles: the piece is short enough to clear a
    portrait page's height, so every seam is vertical and there is only one
    row of tiles to tape. A5 = 3 tiles, A6 = 2 tiles.
  * Each PDF carries a dedicated instruction page and a dedicated scale-check
    page ahead of the tiles.

Layout, viewed OUTSIDE FACE UP, left to right:

    FRONT COVER | SPINE | BACK COVER | FLAP

The flap hangs off the back cover's fore-edge so that, when the book is
assembled, it folds IN over the top of the insert stack and the front cover
closes over it.

Emits:
  a5-cover-v2.svg                  outside face up  (cut grain-side up)
  a5-cover-v2-mirrored.svg         mirrored         (cut grain-side down)
  a6-cover-v2.svg                  outside face up
  a6-cover-v2-mirrored.svg         mirrored
  a5-cover-v2-letter.pdf           5 pages: instructions, scale, 3 tiles
  a6-cover-v2-letter.pdf           4 pages: instructions, scale, 2 tiles

No third-party dependencies - the PDF is written by hand.
"""

import os

OUT = os.path.dirname(os.path.abspath(__file__))
BLEED = 6.0       # template drawn this far beyond the piece edge on outer tiles
BAND = 10.0       # overlap either side of each split between tiles
CAPTION_W = 95.0  # width the longest hole caption needs
K = 0.5522847498307936          # circle/arc Bezier constant
PT = 72.0 / 25.4                # mm -> PostScript points
MM_PER_IN = 25.4


# ---------------------------------------------------------------- specs ----

class Cover:
    def __init__(self, name, slug, fits, panel_w, panel_h, spine_w, flap_w,
                 corner_r, hole_d, closure_d, flange_d, col_gap, row_gap,
                 y_inset, stack_mm, insert_w, insert_h, insert_label, tiles,
                 n_rows=2, legal_single=False):
        self.name = name
        self.slug = slug              # filename stem
        self.fits = fits              # one-line description of the book it makes
        self.panel_w = panel_w        # front / back cover panel width
        self.panel_h = panel_h        # full height of the piece
        self.spine_w = spine_w
        self.flap_w = flap_w
        self.corner_r = corner_r
        self.hole_d = hole_d          # elastic holes (eyelet barrel)
        self.closure_d = closure_d    # single closure hole
        self.flange_d = flange_d      # eyelet flange OD - drives all spacing
        self.col_gap = col_gap        # horizontal spacing of elastic columns
        self.row_gap = row_gap        # vertical spacing of the rows, if 2
        self.n_rows = n_rows          # rows of 3 at EACH end of the spine
        self.y_inset = y_inset        # outer row: distance from top/bottom edge
        self.stack_mm = stack_mm      # thickness of 3 inserts (flap rise)
        self.insert_w = insert_w
        self.insert_h = insert_h
        self.insert_label = insert_label
        self.tiles = tiles            # how many Letter-portrait tiles
        self.legal_single = legal_single   # also fits one Legal sheet, rotated

    # --- derived geometry -------------------------------------------------
    @property
    def total_w(self):
        return self.panel_w + self.spine_w + self.panel_w + self.flap_w

    @property
    def fold_spine_1(self):
        return self.panel_w

    @property
    def fold_spine_2(self):
        return self.panel_w + self.spine_w

    @property
    def fold_flap(self):
        return self.panel_w + self.spine_w + self.panel_w

    @property
    def fold_hinge(self):
        "Optional second score so the flap can climb over the insert stack."
        return self.fold_flap + self.stack_mm + 1

    @property
    def spine_center(self):
        return self.panel_w + self.spine_w / 2.0

    @property
    def elastic_columns(self):
        c = self.spine_center
        return [c - self.col_gap, c, c + self.col_gap]

    @property
    def rows_top(self):
        "Outer row first (nearer the edge), then the inner row if there is one."
        return [self.y_inset + i * self.row_gap for i in range(self.n_rows)]

    @property
    def rows_bottom(self):
        h = self.panel_h
        return [h - y for y in reversed(self.rows_top)]

    @property
    def inner_row(self):
        "y of the row closest to the middle of the cover."
        return self.rows_top[-1]

    @property
    def n_elastic(self):
        return 6 * self.n_rows

    @property
    def row_label(self):
        return 'DOUBLE ROW' if self.n_rows == 2 else 'SINGLE ROW'

    @property
    def row_desc(self):
        return (f'3 holes x {self.n_rows} rows' if self.n_rows == 2
                else 'one row of 3')

    def holes(self):
        """[(cx, cy, diameter, kind), ...] in punching order, top to bottom."""
        out = []
        for y in self.rows_top:
            for x in self.elastic_columns:
                out.append((x, y, self.hole_d, 'elastic'))
        out.append((self.spine_center, self.panel_h / 2.0,
                    self.closure_d, 'closure'))
        for y in self.rows_bottom:
            for x in self.elastic_columns:
                out.append((x, y, self.hole_d, 'elastic'))
        return out

    # --- printing ---------------------------------------------------------
    @property
    def splits(self):
        "x positions where the Letter tiling cuts the piece."
        return [self.total_w * (i + 1) / self.tiles for i in range(self.tiles - 1)]

    def tile_window(self, i):
        "(lo, hi) of tile i in piece coordinates, overlap bands included."
        sp = self.splits
        lo = -BLEED if i == 0 else sp[i - 1] - BAND
        hi = self.total_w + BLEED if i == self.tiles - 1 else sp[i] + BAND
        return lo, hi

    @property
    def callout_side(self):
        """Which side of the spine the hole captions go on.

        They have to live in the same printed tile as the cluster they point
        at, or a seam cuts every caption in half. Pick the side of the spine
        with more room inside that tile.
        """
        for i in range(self.tiles):
            lo, hi = self.tile_window(i)
            if lo <= self.spine_center <= hi:
                room_right = hi - self.fold_spine_2
                room_left = self.fold_spine_1 - lo
                return 'right' if room_right >= room_left else 'left'
        return 'right'

    # --- clearance checks -------------------------------------------------
    @property
    def flange_gap(self):
        "Bare leather between two neighbouring flanges."
        gaps = [self.col_gap] + ([self.row_gap] if self.n_rows > 1 else [])
        return min(gaps) - self.flange_d

    @property
    def flange_to_fold(self):
        "Bare leather between the outer flange and the spine fold line."
        return self.spine_w / 2.0 - self.col_gap - self.flange_d / 2.0

    @property
    def flange_to_edge(self):
        "Bare leather between the outer row's flange and the head of the cover."
        return self.y_inset - self.flange_d / 2.0


# The spine cluster is identical on all three covers. It is sized by the eyelet
# FLANGE (5.5 mm assumed for a 2.5 mm eyelet), not by the 2.5 mm hole: three
# columns on 7 mm centres leaves 1.5 mm of leather between flanges and 2.25 mm
# from the outer flange to the fold line, which fixes the spine at 24 mm. One
# punch-and-set layout therefore serves every size in the lineup.
SPINE_W = 24.0
COL_GAP = 7.0
ROW_GAP = 7.0
HOLE_D = 2.5
CLOSURE_D = 3.0
FLANGE_D = 5.5

A5 = Cover(
    name='A5', slug='a5',
    fits='3 inserts at 6 x 8 in',
    # inserts 6 x 8 in = 152.4 x 203.2 mm; panel adds ~4.5 mm overhang
    panel_w=157.0, panel_h=212.0, spine_w=SPINE_W, flap_w=100.0,
    corner_r=6.0,
    hole_d=HOLE_D, closure_d=CLOSURE_D, flange_d=FLANGE_D,
    col_gap=COL_GAP, row_gap=ROW_GAP, y_inset=11.0,
    stack_mm=15.0,
    insert_w=152.4, insert_h=203.2, insert_label='6 x 8 in',
    tiles=3,
)

# Panel size copied from the WANDERINGS Regular cover the maker likes:
# 4.5 x 8.5 in, rounded to the nearest half millimetre. Standard Traveler's
# Company Regular refills are 110 x 210 mm, which this holds with 4.5 mm of
# overhang on the fore-edge and 3 mm at head and tail.
REGULAR = Cover(
    name='Regular', slug='regular',
    fits='3 Traveler\'s Regular inserts at 110 x 210 mm',
    panel_w=114.5, panel_h=216.0, spine_w=SPINE_W, flap_w=72.0,
    corner_r=5.0,
    hole_d=HOLE_D, closure_d=CLOSURE_D, flange_d=FLANGE_D,
    col_gap=COL_GAP, row_gap=ROW_GAP, y_inset=11.0,
    stack_mm=13.0,
    insert_w=110.0, insert_h=210.0, insert_label="Traveler's Regular",
    tiles=2,
)

# True ISO A6: 105 x 148 mm inserts. Short enough that the whole flat piece
# fits on ONE US Legal sheet turned 90 degrees - no tiling, no tape.
A6 = Cover(
    name='A6', slug='a6',
    fits='3 inserts at A6, 105 x 148 mm',
    panel_w=110.0, panel_h=157.0, spine_w=SPINE_W, flap_w=68.0,
    corner_r=5.0,
    hole_d=HOLE_D, closure_d=CLOSURE_D, flange_d=FLANGE_D,
    col_gap=COL_GAP, row_gap=ROW_GAP, y_inset=10.0,
    stack_mm=12.0,
    insert_w=105.0, insert_h=148.0, insert_label='A6',
    tiles=2, legal_single=True,
)

# Passport keeps V1's panel and its SINGLE row of three at each end, but on
# the new hardware: 2.5 mm eyelets for the elastics, 3 mm for the closure.
# Three columns of 5.5 mm flanges still need a 24 mm spine, which is wide for
# a 9 mm stack - see the tuning notes.
PASSPORT = Cover(
    name='Passport', slug='passport',
    fits="3 Traveler's Passport inserts at 89 x 124 mm",
    panel_w=93.0, panel_h=132.0, spine_w=SPINE_W, flap_w=62.0,
    corner_r=4.0,
    hole_d=HOLE_D, closure_d=CLOSURE_D, flange_d=FLANGE_D,
    col_gap=COL_GAP, row_gap=ROW_GAP, y_inset=10.0,
    stack_mm=9.0,
    insert_w=89.0, insert_h=124.0, insert_label="Traveler's Passport",
    tiles=2, n_rows=1, legal_single=True,
)

COVERS = (A5, REGULAR, A6, PASSPORT)


# ------------------------------------------------------------- geometry ----

def rounded_rect_d(x, y, w, h, r):
    """SVG path data, y-down."""
    return (f"M {x + r:g},{y:g} H {x + w - r:g} A {r:g},{r:g} 0 0 1 {x + w:g},{y + r:g} "
            f"V {y + h - r:g} A {r:g},{r:g} 0 0 1 {x + w - r:g},{y + h:g} "
            f"H {x + r:g} A {r:g},{r:g} 0 0 1 {x:g},{y + h - r:g} "
            f"V {y + r:g} A {r:g},{r:g} 0 0 1 {x + r:g},{y:g} Z")


def circle_d(cx, cy, r):
    """SVG path data for a circle, as two arcs."""
    return (f"M {cx - r:g},{cy:g} a {r:g},{r:g} 0 1 0 {2 * r:g},0 "
            f"a {r:g},{r:g} 0 1 0 {-2 * r:g},0 Z")


# ------------------------------------------------------------------ SVG ----

SVG_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!-- {title}\n'
    '     Piece: {w:g} x {h:g} mm. Verify this size after importing.\n'
    '     Layer "CUT"  = outline + {nh} holes ({ne} elastic @ {hd:g} mm, 1 closure @ {cd:g} mm).\n'
    '     Layer "FOLD" = score lines: set FOLD to Pen/Draw or delete it.\n'
    '     Do NOT leave FOLD set to Cut - it will slice the cover into strips. -->\n'
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    '     width="{w:g}mm" height="{h:g}mm" viewBox="0 0 {w:g} {h:g}">\n'
)


def svg(cover, mirrored=False):
    w, h = cover.total_w, cover.panel_h
    title = f"{cover.name} trifold traveler's cover V2" + (" (MIRRORED)" if mirrored else "")
    parts = [SVG_HEAD.format(title=title, w=w, h=h, nh=len(cover.holes()),
                             ne=cover.n_elastic,
                             hd=cover.hole_d, cd=cover.closure_d)]

    # Mirror by baking x' = W - x into the coordinates rather than using a
    # scale(-1,1) transform: Cricut Design Space is unreliable with negative
    # determinant transforms, and the outline itself is symmetric anyway.
    def mx(x):
        return w - x if mirrored else x

    # --- cut layer: outline + holes as one even-odd path -------------------
    d = [rounded_rect_d(0, 0, w, h, cover.corner_r)]
    for cx, cy, dia, _kind in cover.holes():
        d.append(circle_d(mx(cx), cy, dia / 2.0))
    parts.append('<g id="CUT">\n')
    parts.append('  <path fill="#000000" fill-rule="evenodd" stroke="none"\n')
    parts.append('        d="' + ' '.join(d) + '"/>\n')
    parts.append('</g>\n')

    # --- fold layer --------------------------------------------------------
    parts.append('<g id="FOLD" fill="none" stroke="#e2001a" stroke-width="0.25">\n')
    for x in (cover.fold_spine_1, cover.fold_spine_2, cover.fold_flap):
        parts.append(f'  <line x1="{mx(x):g}" y1="0" x2="{mx(x):g}" y2="{h:g}"/>\n')
    parts.append(f'  <line x1="{mx(cover.fold_hinge):g}" y1="0" '
                 f'x2="{mx(cover.fold_hinge):g}" y2="{h:g}" stroke-dasharray="4 3"/>\n')
    parts.append('</g>\n')

    parts.append('</svg>\n')
    return ''.join(parts)


# ------------------------------------------------------------------ PDF ----

class Pdf:
    """Minimal single-font PDF writer. All drawing is in mm, y-down."""

    def __init__(self):
        self.pages = []   # (width_mm, height_mm, content_str)

    def page(self, w_mm, h_mm, body):
        self.pages.append((w_mm, h_mm, body))

    def build(self):
        objs = {}
        n_pages = len(self.pages)
        # 1 catalog, 2 pages tree, 3 font, 4 bold font, then page + content
        page_ids = [5 + 2 * i for i in range(n_pages)]
        cont_ids = [6 + 2 * i for i in range(n_pages)]

        objs[1] = "<< /Type /Catalog /Pages 2 0 R >>"
        kids = ' '.join(f"{i} 0 R" for i in page_ids)
        objs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>"
        objs[3] = ("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                   "/Encoding /WinAnsiEncoding >>")
        objs[4] = ("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                   "/Encoding /WinAnsiEncoding >>")

        for i, (w, h, body) in enumerate(self.pages):
            # flip to y-down mm: x' = s*x, y' = H*s - s*y
            head = f"q {PT:.6f} 0 0 {-PT:.6f} 0 {h * PT:.4f} cm\n"
            stream = head + body + "\nQ\n"
            objs[page_ids[i]] = (
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {w * PT:.4f} {h * PT:.4f}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {cont_ids[i]} 0 R >>")
            objs[cont_ids[i]] = ("<< /Length %d >>\nstream\n%s\nendstream"
                                 % (len(stream), stream))

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = {}
        for num in sorted(objs):
            offsets[num] = len(out)
            out += f"{num} 0 obj\n{objs[num]}\nendobj\n".encode('latin-1')

        xref_at = len(out)
        top = max(objs) + 1
        out += f"xref\n0 {top}\n".encode()
        out += b"0000000000 65535 f \n"
        for num in range(1, top):
            out += f"{offsets[num]:010d} 00000 n \n".encode()
        out += (f"trailer\n<< /Size {top} /Root 1 0 R >>\nstartxref\n"
                f"{xref_at}\n%%EOF\n").encode()
        return bytes(out)


# --- content-stream helpers (mm, y-down) -----------------------------------

def _n(v):
    return f"{v:.4f}".rstrip('0').rstrip('.')


def p_line(x1, y1, x2, y2, lw=0.3, dash=None, gray=0.0):
    d = f"[{dash[0]} {dash[1]}] 0 d\n" if dash else "[] 0 d\n"
    return (f"q {gray:g} G {lw:g} w {d}"
            f"{_n(x1)} {_n(y1)} m {_n(x2)} {_n(y2)} l S Q\n")


def p_rect(x, y, w, h, lw=0.3, gray=0.0, dash=None):
    d = f"[{dash[0]} {dash[1]}] 0 d " if dash else "[] 0 d "
    return (f"q {gray:g} G {lw:g} w {d}{_n(x)} {_n(y)} {_n(w)} {_n(h)} re S Q\n")


def p_fill_rect(x, y, w, h, gray=0.9):
    return f"q {gray:g} g {_n(x)} {_n(y)} {_n(w)} {_n(h)} re f Q\n"


def p_rounded_rect(x, y, w, h, r, lw=0.4, gray=0.0):
    k = K * r
    s = [f"q {gray:g} G {lw:g} w [] 0 d"]
    s.append(f"{_n(x + r)} {_n(y)} m")
    s.append(f"{_n(x + w - r)} {_n(y)} l")
    s.append(f"{_n(x + w - r + k)} {_n(y)} {_n(x + w)} {_n(y + r - k)} {_n(x + w)} {_n(y + r)} c")
    s.append(f"{_n(x + w)} {_n(y + h - r)} l")
    s.append(f"{_n(x + w)} {_n(y + h - r + k)} {_n(x + w - r + k)} {_n(y + h)} {_n(x + w - r)} {_n(y + h)} c")
    s.append(f"{_n(x + r)} {_n(y + h)} l")
    s.append(f"{_n(x + r - k)} {_n(y + h)} {_n(x)} {_n(y + h - r + k)} {_n(x)} {_n(y + h - r)} c")
    s.append(f"{_n(x)} {_n(y + r)} l")
    s.append(f"{_n(x)} {_n(y + r - k)} {_n(x + r - k)} {_n(y)} {_n(x + r)} {_n(y)} c")
    s.append("h S Q")
    return ' '.join(s) + "\n"


def p_circle(cx, cy, r, lw=0.3, gray=0.0, dash=None):
    k = K * r
    d = f"[{dash[0]} {dash[1]}] 0 d" if dash else "[] 0 d"
    s = [f"q {gray:g} G {lw:g} w {d}"]
    s.append(f"{_n(cx + r)} {_n(cy)} m")
    s.append(f"{_n(cx + r)} {_n(cy + k)} {_n(cx + k)} {_n(cy + r)} {_n(cx)} {_n(cy + r)} c")
    s.append(f"{_n(cx - k)} {_n(cy + r)} {_n(cx - r)} {_n(cy + k)} {_n(cx - r)} {_n(cy)} c")
    s.append(f"{_n(cx - r)} {_n(cy - k)} {_n(cx - k)} {_n(cy - r)} {_n(cx)} {_n(cy - r)} c")
    s.append(f"{_n(cx + k)} {_n(cy - r)} {_n(cx + r)} {_n(cy - k)} {_n(cx + r)} {_n(cy)} c")
    s.append("h S Q")
    return ' '.join(s) + "\n"


def p_disc(cx, cy, r, gray=0.0):
    k = K * r
    s = [f"q {gray:g} g"]
    s.append(f"{_n(cx + r)} {_n(cy)} m")
    s.append(f"{_n(cx + r)} {_n(cy + k)} {_n(cx + k)} {_n(cy + r)} {_n(cx)} {_n(cy + r)} c")
    s.append(f"{_n(cx - k)} {_n(cy + r)} {_n(cx - r)} {_n(cy + k)} {_n(cx - r)} {_n(cy)} c")
    s.append(f"{_n(cx - r)} {_n(cy - k)} {_n(cx - k)} {_n(cy - r)} {_n(cx)} {_n(cy - r)} c")
    s.append(f"{_n(cx + k)} {_n(cy - r)} {_n(cx + r)} {_n(cy - k)} {_n(cx + r)} {_n(cy)} c")
    s.append("f Q")
    return ' '.join(s) + "\n"


def p_cross(cx, cy, arm=5.0, lw=0.3, gray=0.0):
    return (p_line(cx - arm, cy, cx + arm, cy, lw, gray=gray) +
            p_line(cx, cy - arm, cx, cy + arm, lw, gray=gray))


def _esc(t):
    return t.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


def _adv(text, size):
    """Rough Helvetica advance width, good enough for centring labels."""
    return sum(0.55 if c not in 'iljtfrI .,' else 0.30 for c in text) * size


def p_text(x, y, text, size=3.2, gray=0.0, align='left', bold=False):
    font = '/F2' if bold else '/F1'
    w = _adv(text, size)
    if align == 'center':
        x -= w / 2.0
    elif align == 'right':
        x -= w
    return (f"q {gray:g} g BT {font} {size:g} Tf 1 0 0 -1 {_n(x)} {_n(y)} Tm "
            f"({_esc(text)}) Tj ET Q\n")


def p_vtext(x, y, text, size=3.2, gray=0.0, bold=False):
    """Text rotated 90 degrees CCW, reading bottom-to-top, centred on y."""
    font = '/F2' if bold else '/F1'
    w = _adv(text, size)
    return (f"q {gray:g} g BT {font} {size:g} Tf 0 -1 -1 0 "
            f"{_n(x)} {_n(y + w / 2.0)} Tm ({_esc(text)}) Tj ET Q\n")


def p_clip(x, y, w, h):
    return f"{_n(x)} {_n(y)} {_n(w)} {_n(h)} re W n\n"


def p_para(x, y, lines, size=3.0, gray=0.2, leading=4.2):
    s = []
    for i, ln in enumerate(lines):
        s.append(p_text(x, y + i * leading, ln, size, gray))
    return ''.join(s)


# --- the full-size template artwork ----------------------------------------

def artwork(c, ox, oy):
    """Full-size template artwork, translated to (ox, oy) on the page."""
    def X(v):
        return v + ox

    def Y(v):
        return v + oy

    s = []
    w, h = c.total_w, c.panel_h
    mid = h / 2.0

    # cut outline
    s.append(p_rounded_rect(X(0), Y(0), w, h, c.corner_r, lw=0.6))

    # fold lines
    for x in (c.fold_spine_1, c.fold_spine_2, c.fold_flap):
        s.append(p_line(X(x), Y(0), X(x), Y(h), lw=0.4, dash=(3, 2), gray=0.3))
    s.append(p_line(X(c.fold_hinge), Y(0), X(c.fold_hinge), Y(h),
                    lw=0.35, dash=(1, 1.6), gray=0.55))

    # holes: the cut circle, the eyelet flange footprint, and a centre cross
    for cx, cy, dia, kind in c.holes():
        s.append(p_circle(X(cx), Y(cy), c.flange_d / 2.0, lw=0.2, gray=0.62,
                          dash=(0.8, 0.8)))
        s.append(p_circle(X(cx), Y(cy), dia / 2.0, lw=0.4))
        s.append(p_cross(X(cx), Y(cy), arm=4.0, lw=0.12, gray=0.45))

    # panel labels, lifted clear of the mid-height band
    lab, dim = mid - 30, mid - 24
    s.append(p_text(X(c.panel_w / 2.0), Y(lab), 'FRONT COVER', 4.6, 0.2, 'center', bold=True))
    s.append(p_text(X(c.panel_w / 2.0), Y(dim), f'{c.panel_w:g} x {c.panel_h:g} mm',
                    3.0, 0.45, 'center'))
    bx = c.panel_w + c.spine_w + c.panel_w / 2.0
    s.append(p_text(X(bx), Y(lab), 'BACK COVER', 4.6, 0.2, 'center', bold=True))
    s.append(p_text(X(bx), Y(dim), f'{c.panel_w:g} x {c.panel_h:g} mm', 3.0, 0.45, 'center'))
    fx = c.fold_flap + c.flap_w / 2.0
    s.append(p_text(X(fx), Y(lab), 'FLAP', 4.6, 0.2, 'center', bold=True))
    s.append(p_text(X(fx), Y(dim), f'{c.flap_w:g} mm wide', 3.0, 0.45, 'center'))
    s.append(p_text(X(fx), Y(dim + 5), '(folds IN over the inserts)', 2.8, 0.5, 'center'))

    # spine label, set vertically in the spine itself
    s.append(p_vtext(X(c.spine_center) + 1.6, Y(mid + 22),
                     f'SPINE {c.spine_w:g} mm', 3.2, 0.35))

    # Hole callouts. They sit on whichever side of the spine falls inside the
    # same printed tile as the spine cluster, so no caption is ever cut in half
    # by a seam: to the right of the spine on the A5, to the left on the A6.
    if c.callout_side == 'right':
        cx0, al = c.fold_spine_2 + 6, 'left'
    else:
        cx0, al = c.fold_spine_1 - 6, 'right'

    def cap(dy, text, size=2.7, gray=0.4, bold=False):
        s.append(p_text(X(cx0), Y(dy), text, size, gray, al, bold=bold))

    cap(c.y_inset, f'{c.row_label} - {c.row_desc}, this end and the other',
        3.0, 0.15, bold=True)
    cap(c.y_inset + 5,
        f'{c.n_elastic} elastic holes total, {c.hole_d:g} mm dia for {c.hole_d:g} mm eyelets')
    cap(c.y_inset + 9, f'columns on {c.col_gap:g} mm centres'
        + (f', rows on {c.row_gap:g} mm centres' if c.n_rows > 1 else ''))
    cap(c.y_inset + 13, f'dotted ring = {c.flange_d:g} mm eyelet flange footprint')
    cap(c.y_inset + 17, f'({c.flange_gap:g} mm of leather between flanges)')

    cap(mid, f'CLOSURE - {c.closure_d:g} mm dia, one eyelet', 3.0, 0.15, bold=True)
    cap(mid + 5, 'on the spine centreline at half the cover height')
    cap(mid + 9, 'set this eyelet and knot the closure FIRST')

    cap(h - c.y_inset - 13,
        f'fits 3 inserts at {c.insert_label}', 3.0, 0.15, bold=True)
    cap(h - c.y_inset - 8, f'({c.insert_w:g} x {c.insert_h:g} mm each)')
    cap(h - c.y_inset - 4, f'corners rounded R{c.corner_r:g} mm')

    s.append(p_text(X(c.fold_hinge) + 2, Y(h) - 8, 'optional', 2.7, 0.5))
    s.append(p_text(X(c.fold_hinge) + 2, Y(h) - 4.5, 'hinge score', 2.7, 0.5))

    # orientation note along the head of the piece
    s.append(p_text(X(0), Y(-4), 'OUTSIDE FACE UP   -   '
                    f"{c.name} trifold cover V2   -   flat piece is {w:g} x {h:g} mm",
                    3.6, 0.1, bold=True))

    return ''.join(s)


# --- pages -----------------------------------------------------------------

W_LETTER, H_LETTER = 215.9, 279.4     # US Letter PORTRAIT
W_LEGAL,  H_LEGAL  = 215.9, 355.6     # US Legal  PORTRAIT
MARGIN = 14.0
LEGAL_TOP = 25.0  # top of the rotated piece on a Legal sheet, below the header


def page_frame(c, n, total, subtitle, W=W_LETTER):
    s = [p_text(MARGIN, 12, f"{c.name.upper()} TRIFOLD TRAVELER'S COVER  -  V2",
                4.4, 0.1, bold=True)]
    s.append(p_text(W - MARGIN, 12, f'page {n} of {total}', 3.2, 0.45, 'right'))
    s.append(p_line(MARGIN, 15, W - MARGIN, 15, lw=0.5, gray=0.25))
    s.append(p_text(MARGIN, 20.5, subtitle, 3.4, 0.35))
    return ''.join(s)


def instruction_page(c, n, total, single, W=W_LETTER):
    s = [page_frame(c, n, total,
                    'READ THIS FIRST  -  printing, transferring, punching, setting',
                    W)]
    y = 32

    def head(t):
        nonlocal y
        s.append(p_text(MARGIN, y, t, 4.0, 0.1, bold=True))
        s.append(p_line(MARGIN, y + 1.8, W - MARGIN, y + 1.8, lw=0.3, gray=0.6))
        y += 7

    def body(lines):
        nonlocal y
        s.append(p_para(MARGIN + 2, y, lines, 3.0, 0.2, 4.3))
        y += len(lines) * 4.3 + 5

    head('1  PRINT AT 100%')
    body([
        'Print every page at 100% / Actual Size. Turn OFF "fit to page", "shrink to fit" and',
        '"scale to paper size" - they are on by default in most print dialogs and they are the',
        'single most common way a template comes out the wrong size.',
        f'Then go to page {n + 1} and measure the scale bars before you cut anything.',
    ])

    if single:
        head('2  ONE SHEET, NO TAPE')
        body([
            f'The whole {c.total_w:g} x {c.panel_h:g} mm template is on page {n + 2}, turned 90 '
            'degrees to fit',
            'a single US Legal sheet. Turn the paper sideways to read it.',
            'Check the length across the assembled piece against the flat-piece dimension',
            f'printed along its head edge ({c.total_w:g} mm) before you trust it.',
        ])
    else:
        head('2  ASSEMBLE THE TILES')
        body([
            f'The full-size template is split across {c.tiles} pages ({n + 2} to {total}), '
            f'side by side, left to right.',
            'Every seam is vertical, so there is only one line of tape per joint.',
            'Trim the first tile along its right-hand TRIM LINE, lay it over the next page so',
            'the + registration marks sit exactly on top of each other, and tape the overlap.',
            'Each seam has two + marks, one near the head and one near the tail: get both onto',
            'their partners or the joint can pivot. Work left to right, then check the assembled',
            f'length against the flat-piece dimension printed on the template ({c.total_w:g} mm).',
        ])

    head('3  TRANSFER TO LEATHER')
    body([
        f'You need a piece at least {c.total_w + 12:g} x {c.panel_h + 12:g} mm '
        f'({(c.total_w + 12) / MM_PER_IN:.1f} x {(c.panel_h + 12) / MM_PER_IN:.1f} in) '
        'to have something to hold on to.',
        'Cut the paper template out and lay it OUTSIDE FACE UP on the grain side of the leather.',
        'The outline is a symmetric rounded rectangle, so it traces the same either way up - but',
        'the flap must end up on the BACK cover, so keep track of which panel is which.',
        'Mark the corners and the four fold lines lightly with a scratch awl, and prick all',
        f'{len(c.holes())} hole centres through the paper.',
    ])

    head('4  PUNCH THE HOLES  -  BEFORE YOU CREASE THE FOLDS')
    body([
        f'{c.hole_d:g} mm round punch for the {c.n_elastic} elastic holes, '
        f'{c.closure_d:g} mm for the single closure hole.',
        'A folded panel will not sit flat under a punch, so all punching happens while the piece',
        'is still flat. Punch into end grain or a poly board.',
        'The dotted ring around each hole on the template is the eyelet FLANGE footprint, drawn',
        f'at {c.flange_d:g} mm. Set one eyelet in a scrap first and measure its flange: if yours is',
        f'wider than {c.flange_d:g} mm, neighbouring flanges will touch and you should open the',
        'column and row spacing in the build script before cutting the real piece.',
    ])

    head('5  SET THE EYELETS')
    body([
        f'{c.n_elastic} eyelets at {c.hole_d:g} mm for the elastics, '
        f'1 at {c.closure_d:g} mm for the closure.',
        'Set from the OUTSIDE so the finished flange shows on the outside of the spine and the',
        'rolled side sits inside where the inserts run.',
        'Work from the middle of each cluster outward, and check the piece stays flat - a spine',
        f'with {c.n_elastic} eyelets in it will bow if you over-set them.',
    ])

    head('6  CREASE, THEN ASSEMBLE')
    body([
        'Dampen the grain slightly and run a bone folder along a straight edge on each of the',
        'three solid fold lines. Fold away from the grain side.',
        'Closure elastic first, then the three insert elastics.',
        ('Each one goes out through the INNER hole of a cluster, across the '
         f'{c.row_gap:g} mm bar, back in through the OUTER hole, stopper knot inside.'
         if c.n_rows > 1 else
         'Each one goes out through its hole and is stopped with a knot on the inside.'),
    ])

    return ''.join(s)


def scale_page(c, n, total, W=W_LETTER):
    s = [page_frame(c, n, total,
                    'SCALE CHECK  -  measure these before you cut anything', W)]
    y = 30

    # --- 100 mm metric bar ---
    s.append(p_text(MARGIN, y, 'A.  This bar must measure exactly 100 mm.', 3.6, 0.1, bold=True))
    y += 8
    bx = MARGIN + 4
    s.append(p_line(bx, y, bx + 100, y, lw=0.6))
    for i in range(11):
        t = 4.0 if i % 5 == 0 else 2.2
        s.append(p_line(bx + i * 10, y, bx + i * 10, y - t, lw=0.45))
        if i % 5 == 0:
            s.append(p_text(bx + i * 10, y - 5.5, f'{i * 10}', 2.8, 0.35, 'center'))
    s.append(p_text(bx + 104, y, '100 mm', 3.2, 0.35))
    y += 12

    # --- 6 inch imperial bar ---
    s.append(p_text(MARGIN, y, 'B.  This bar must measure exactly 6 inches.', 3.6, 0.1, bold=True))
    y += 8
    s.append(p_line(bx, y, bx + 6 * MM_PER_IN, y, lw=0.6))
    for i in range(13):
        half = (i % 2 == 1)
        t = 2.2 if half else 4.0
        s.append(p_line(bx + i * MM_PER_IN / 2.0, y, bx + i * MM_PER_IN / 2.0, y - t, lw=0.45))
        if not half:
            s.append(p_text(bx + i * MM_PER_IN / 2.0, y - 5.5, f'{i // 2}', 2.8, 0.35, 'center'))
    s.append(p_text(bx + 6 * MM_PER_IN + 4, y, '6 in', 3.2, 0.35))
    y += 12

    s.append(p_para(MARGIN, y, [
        'If either bar is short, your print dialog scaled the page. Reprint at 100% / Actual Size',
        'with "fit to page" off. Do not try to compensate by cutting slightly bigger.',
    ], 3.0, 0.25, 4.3))
    y += 14

    # --- true-size hole reference ---
    s.append(p_text(MARGIN, y, 'C.  Holes and eyelet flanges, shown at true size.',
                    3.6, 0.1, bold=True))
    y += 9
    hx = MARGIN + 10
    for label, dia in ((f'{c.hole_d:g} mm', c.hole_d),
                       (f'{c.closure_d:g} mm', c.closure_d)):
        s.append(p_circle(hx, y, dia / 2.0, lw=0.4))
        s.append(p_text(hx, y + 8, label, 2.8, 0.3, 'center'))
        hx += 22
    s.append(p_circle(hx, y, c.flange_d / 2.0, lw=0.3, gray=0.5, dash=(0.8, 0.8)))
    s.append(p_circle(hx, y, c.hole_d / 2.0, lw=0.4))
    s.append(p_text(hx, y + 8, f'flange {c.flange_d:g} mm', 2.8, 0.3, 'center'))
    s.append(p_para(hx + 22, y - 2, [
        'Drop one of your own eyelets on top of the dotted ring.',
        f'If its flange is wider than {c.flange_d:g} mm the spacing in this',
        'template is too tight - see the tuning notes in the guide.',
    ], 2.8, 0.3, 4.0))
    y += 20

    # --- 1:1 spine cluster detail ---
    s.append(p_text(MARGIN, y, 'D.  Top of the spine at true size - punch layout.',
                    3.6, 0.1, bold=True))
    y += 6
    dx = MARGIN + 26
    dy = y + 4
    sw, cluster_h = c.spine_w, c.y_inset + c.row_gap + 22

    # spine band + head edge
    s.append(p_fill_rect(dx, dy, sw, cluster_h, gray=0.95))
    s.append(p_line(dx - 10, dy, dx + sw + 10, dy, lw=0.8))
    s.append(p_text(dx + sw + 12, dy + 1, 'head of the cover', 2.7, 0.35))
    for fx in (dx, dx + sw):
        s.append(p_line(fx, dy, fx, dy + cluster_h, lw=0.4, dash=(3, 2), gray=0.3))

    for ry in c.rows_top:
        for ci in (-1, 0, 1):
            cx = dx + sw / 2.0 + ci * c.col_gap
            cy = dy + ry
            s.append(p_circle(cx, cy, c.flange_d / 2.0, lw=0.25, gray=0.55, dash=(0.8, 0.8)))
            s.append(p_circle(cx, cy, c.hole_d / 2.0, lw=0.45))
            s.append(p_cross(cx, cy, arm=3.5, lw=0.12, gray=0.4))

    # dimensions
    dim_y = dy + c.y_inset + c.row_gap + 12
    left_c = dx + sw / 2.0 - c.col_gap
    s.append(p_line(left_c, dim_y, left_c + 2 * c.col_gap, dim_y, lw=0.3, gray=0.4))
    for i in range(3):
        xx = left_c + i * c.col_gap
        s.append(p_line(xx, dim_y - 2, xx, dim_y + 2, lw=0.3, gray=0.4))
    s.append(p_text(left_c + c.col_gap / 2.0, dim_y + 5, f'{c.col_gap:g}', 2.8, 0.3, 'center'))
    s.append(p_text(left_c + 1.5 * c.col_gap, dim_y + 5, f'{c.col_gap:g}', 2.8, 0.3, 'center'))

    dim_x = dx - 12
    s.append(p_line(dim_x, dy, dim_x, dy + c.y_inset + c.row_gap, lw=0.3, gray=0.4))
    for yy in (dy, dy + c.y_inset, dy + c.y_inset + c.row_gap):
        s.append(p_line(dim_x - 2, yy, dim_x + 2, yy, lw=0.3, gray=0.4))
    s.append(p_text(dim_x - 3, dy + c.y_inset / 2.0, f'{c.y_inset:g}', 2.8, 0.3, 'right'))
    s.append(p_text(dim_x - 3, dy + c.y_inset + c.row_gap / 2.0,
                    f'{c.row_gap:g}', 2.8, 0.3, 'right'))

    sp_y = dy + cluster_h + 6
    s.append(p_line(dx, sp_y, dx + sw, sp_y, lw=0.3, gray=0.4))
    s.append(p_line(dx, sp_y - 2, dx, sp_y + 2, lw=0.3, gray=0.4))
    s.append(p_line(dx + sw, sp_y - 2, dx + sw, sp_y + 2, lw=0.3, gray=0.4))
    s.append(p_text(dx + sw / 2.0, sp_y + 5, f'{sw:g} mm spine', 2.8, 0.3, 'center'))

    s.append(p_para(dx + sw + 12, dy + 12, [
        'Lay a punched scrap over this and the holes should',
        'disappear. The tail of the spine is the mirror of',
        'this about the horizontal centreline of the cover.',
        '',
        f'{c.flange_gap:g} mm of leather between flanges.',
        f'{c.flange_to_fold:g} mm from the outer flange to the fold line.',
        f'{c.flange_to_edge:g} mm from the top flange to the head edge.',
    ], 2.8, 0.3, 4.0))

    return ''.join(s)


def tile_pages(c, first_page_no, total):
    """US Letter portrait tiles, split vertically only."""
    pages = []
    n = c.tiles
    oy = (H_LETTER - c.panel_h) / 2.0 + 2.0
    splits = c.splits

    for i in range(n):
        lo, hi = c.tile_window(i)
        ox = (W_LETTER - (hi - lo)) / 2.0 - lo

        # everything that must be windowed goes inside one q ... Q with a clip
        body = "q\n" + p_clip(ox + lo, 0, hi - lo, H_LETTER)
        body += artwork(c, ox, oy)

        # registration crosses + trim/tape lines on each split this tile touches
        for sx in splits:
            if not (lo - 0.1 <= sx <= hi + 0.1):
                continue
            body += p_line(ox + sx, oy - 18, ox + sx, oy + c.panel_h + 18,
                           lw=0.3, dash=(2, 2), gray=0.55)
            for ry in (26.0, c.panel_h - 26.0):
                body += p_cross(ox + sx, oy + ry, arm=7, lw=0.35, gray=0.3)
                body += p_circle(ox + sx, oy + ry, 3.0, lw=0.2, gray=0.55)
            # A split at this tile's right edge gets a right-aligned label; one
            # at its left edge gets a left-aligned label. Either way the text
            # runs into the tile, never out through the clip.
            right_edge = sx > (lo + hi) / 2.0
            body += p_text(ox + sx + (-4 if right_edge else 4),
                           oy + c.panel_h + 14, 'TRIM / TAPE LINE', 2.8, 0.45,
                           'right' if right_edge else 'left')
        body += "Q\n"

        pos = 'LEFT' if i == 0 else ('RIGHT' if i == n - 1 else f'MIDDLE {i}')
        sub = (f'FULL-SIZE TEMPLATE  -  tile {i + 1} of {n} ({pos})  -  '
               f'print at 100%, overlay the + marks, tape')
        body += page_frame(c, first_page_no + i, total, sub)
        body += p_text(MARGIN, H_LETTER - 10,
                       f'{c.name} V2  -  flat piece {c.total_w:g} x {c.panel_h:g} mm  -  '
                       f'outside face up  -  tile {i + 1}/{n}', 3.0, 0.4)
        pages.append(body)
    return pages


def legal_page(c, n, total):
    """The whole piece on one US Legal sheet, rotated 90 degrees.

    The content stream is already in y-down millimetres, so the extra matrix
    maps template (x, y) -> page (e - y, f + x): the piece's length runs down
    the sheet and its height runs across it.
    """
    e = (W_LEGAL + c.panel_h) / 2.0        # piece occupies page-x [e - panel_h, e]
    f = LEGAL_TOP                          # piece occupies page-y [f, f + total_w]
    body = f"q 0 1 -1 0 {_n(e)} {_n(f)} cm\n" + artwork(c, 0, 0) + "Q\n"
    body += page_frame(c, n, total,
                       'FULL-SIZE TEMPLATE  -  one sheet, no tiling  -  '
                       'turn the page 90 degrees', W_LEGAL)
    body += p_text(MARGIN, H_LEGAL - 10,
                   f'{c.name} V2  -  flat piece {c.total_w:g} x {c.panel_h:g} mm  -  '
                   f'outside face up  -  US Legal, printed at 100%', 3.0, 0.4)
    return body


def build_pdf(c, mode):
    """mode 'letter' -> tiled Letter portrait; 'legal' -> one rotated Legal sheet."""
    single = (mode == 'legal')
    total = 3 if single else 2 + c.tiles
    # Every page in a given PDF is the same size, so the whole file prints from
    # one paper tray without touching the dialog between pages.
    W, H = (W_LEGAL, H_LEGAL) if single else (W_LETTER, H_LETTER)
    pdf = Pdf()
    pdf.page(W, H, instruction_page(c, 1, total, single, W))
    pdf.page(W, H, scale_page(c, 2, total, W))
    if single:
        pdf.page(W, H, legal_page(c, 3, total))
    else:
        for body in tile_pages(c, 3, total):
            pdf.page(W, H, body)
    fname = f'{c.slug}-cover-v2-{mode}.pdf'
    path = os.path.join(OUT, fname)
    with open(path, 'wb') as fh:
        fh.write(pdf.build())
    return path


# ----------------------------------------------------------------- main ----

def check(c):
    """Fail loudly if the hardware or the paper will not take the geometry."""
    problems = []
    if c.flange_gap < 0.8:
        problems.append(f'{c.name}: only {c.flange_gap:g} mm between eyelet flanges')
    if c.flange_to_fold < 1.5:
        problems.append(f'{c.name}: only {c.flange_to_fold:g} mm from outer flange to fold line')
    if c.flange_to_edge < 5.0:
        problems.append(f'{c.name}: only {c.flange_to_edge:g} mm from flange to the head edge')
    # the closure hole must not crowd the inner row
    closure_gap = c.panel_h / 2.0 - c.inner_row - c.flange_d
    if closure_gap < 10.0:
        problems.append(f'{c.name}: only {closure_gap:g} mm between the inner row and the closure')
    if c.panel_w - c.insert_w < 3.0:
        problems.append(f'{c.name}: panel is less than 3 mm wider than the insert')
    if c.panel_h - c.insert_h < 5.0:
        problems.append(f'{c.name}: panel is less than 5 mm taller than the insert')
    # every tile must fit inside the printable width of a Letter portrait page
    widest = c.total_w / c.tiles + max(BAND + BLEED, 2 * BAND)
    if widest > W_LETTER - 2 * MARGIN:
        problems.append(f'{c.name}: tile width {widest:g} mm exceeds the printable area')
    if c.panel_h > H_LETTER - 2 * MARGIN - 16:
        problems.append(f'{c.name}: piece height {c.panel_h:g} mm will not clear the page margins')
    # the hole captions must fit in the tile that carries the spine cluster
    for i in range(c.tiles):
        lo, hi = c.tile_window(i)
        if not lo <= c.spine_center <= hi:
            continue
        room = (hi - c.fold_spine_2) if c.callout_side == 'right' else (c.fold_spine_1 - lo)
        if room < CAPTION_W:
            problems.append(f'{c.name}: only {room:g} mm for the hole captions on tile '
                            f'{i + 1}, need {CAPTION_W:g}')
    if c.legal_single:
        if c.panel_h > W_LEGAL - 2 * MARGIN:
            problems.append(f'{c.name}: piece height {c.panel_h:g} mm is too wide for Legal')
        if c.total_w > H_LEGAL - LEGAL_TOP - MARGIN:
            problems.append(f'{c.name}: piece length {c.total_w:g} mm is too long for Legal')
    return problems


def main():
    files = []

    for cover in COVERS:
        for suffix, mirror in (('.svg', False), ('-mirrored.svg', True)):
            fname = f'{cover.slug}-cover-v2{suffix}'
            path = os.path.join(OUT, fname)
            with open(path, 'w') as fh:
                fh.write(svg(cover, mirrored=mirror))
            files.append(path)

    for cover in COVERS:
        files.append(build_pdf(cover, 'letter'))
        if cover.legal_single:
            files.append(build_pdf(cover, 'legal'))

    all_problems = []
    for c in COVERS:
        all_problems += check(c)
        print(f"\n{c.name}: flat piece {c.total_w:g} x {c.panel_h:g} mm "
              f"({c.total_w / MM_PER_IN:.2f} x {c.panel_h / MM_PER_IN:.2f} in)")
        print(f"  holds    {c.fits}")
        print(f"  insert   {c.insert_w:g} x {c.insert_h:g} mm  ->  "
              f"overhang {c.panel_w - c.insert_w:g} fore-edge, "
              f"{(c.panel_h - c.insert_h) / 2:g} head and tail")
        print(f"  panels   front {c.panel_w:g} | spine {c.spine_w:g} | "
              f"back {c.panel_w:g} | flap {c.flap_w:g}")
        print(f"  folds at x = {c.fold_spine_1:g}, {c.fold_spine_2:g}, "
              f"{c.fold_flap:g} (+ optional hinge {c.fold_hinge:g})")
        print(f"  clearance  flange-to-flange {c.flange_gap:g} | "
              f"flange-to-fold {c.flange_to_fold:g} | flange-to-edge {c.flange_to_edge:g}")
        print(f"  paper    {c.tiles} Letter tile(s)"
              + ("  +  1 Legal sheet, rotated" if c.legal_single else ""))
        rows = ' / '.join(f'{y:g}' for y in c.rows_top + c.rows_bottom)
        cols = ' / '.join(f'{x:g}' for x in c.elastic_columns)
        print(f"  holes    columns x = {cols} | rows y = {rows} | "
              f"closure ({c.spine_center:g}, {c.panel_h / 2:g})")

    print("\nWrote:")
    for path in files:
        print(f"  {os.path.basename(path):32s} {os.path.getsize(path):>8,d} bytes")

    if all_problems:
        print("\n!! PROBLEMS:")
        for problem in all_problems:
            print("   " + problem)
    else:
        print("\nAll clearance and page-fit checks passed.")


if __name__ == '__main__':
    main()
