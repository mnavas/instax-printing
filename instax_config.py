"""Physical dimensions and derived pixel sizes for the instax-printing layout.

Everything is anchored to real millimetres and rendered at PRINT_DPI so the
exported 4R file has correct physical proportions when printed at 15×10 cm.
"""
from __future__ import annotations

PRINT_DPI = 300
_MM_PER_INCH = 25.4


def mm_to_px(mm: float) -> int:
    """Convert millimetres to pixels at PRINT_DPI (rounded)."""
    return round(mm / _MM_PER_INCH * PRINT_DPI)


# 4R print — 6×4 inch ≈ 15.2×10.2 cm, landscape. This is the standard lab 4R
# and the closest common size to the requested 15×10 cm.
CANVAS_W_MM = 152.4
CANVAS_H_MM = 101.6
CANVAS_W = mm_to_px(CANVAS_W_MM)   # 1800
CANVAS_H = mm_to_px(CANVAS_H_MM)   # 1200

# Instax mini IMAGE AREA — 46×62 mm, portrait. This is the photo content that
# the user's crop fills (the white frame is not part of the picture).
INSTAX_W_MM = 46.0
INSTAX_H_MM = 62.0
INSTAX_W = mm_to_px(INSTAX_W_MM)   # 543
INSTAX_H = mm_to_px(INSTAX_H_MM)   # 732
INSTAX_RATIO = INSTAX_W / INSTAX_H  # ≈ 0.742 (w/h, portrait)

# Instax mini CARD — the full 54×86 mm print with its white border. The image
# area sits centred horizontally, offset toward the top so the bottom border is
# the thick one (the classic instax look): 4 mm sides, 8 mm top, 16 mm bottom.
CARD_W_MM = 54.0
CARD_H_MM = 86.0
CARD_W = mm_to_px(CARD_W_MM)   # 638
CARD_H = mm_to_px(CARD_H_MM)   # 1016
CARD_RATIO = CARD_W / CARD_H
TOP_BORDER_MM = 8.0
TOP_BORDER_PX = mm_to_px(TOP_BORDER_MM)   # ~94; bottom border is the remainder (~16 mm)

# Layout: three instax cards packed edge-to-edge and flush to the top of the 4R.
# No outer margins and no gaps, so the sheet's own trim edges are the outer
# borders (nothing to cut on the left, right, or top) and the two boundaries
# between cards need a single cut each. Three 54 mm cards (162 mm) are wider than
# the 4R (152 mm), so they print a little under full size.
GAP_MM = 0.0
MARGIN_MM = 0.0
GAP_PX = mm_to_px(GAP_MM)
MARGIN_PX = mm_to_px(MARGIN_MM)

# Cut marks: light-grey trim lines along the cuts that are actually needed.
TRIM_LINE_COLOR = (205, 205, 205)   # BGR, light grey


def image_offset() -> tuple[int, int]:
    """Top-left (x, y) of the image area inside a native-size card."""
    x = (CARD_W - INSTAX_W) // 2
    return x, TOP_BORDER_PX


def card_print_size() -> tuple[int, int]:
    """Printed size (px) of each instax card so three fit across the 4R width,
    capped at native so cards are never upscaled."""
    avail_w = CANVAS_W - 2 * MARGIN_PX - 2 * GAP_PX
    w = min(CARD_W, avail_w // 3)
    h = round(w / CARD_RATIO)
    max_h = CANVAS_H - 2 * MARGIN_PX
    if h > max_h:
        h = max_h
        w = round(h * CARD_RATIO)
    return w, h


def card_positions() -> list[tuple[int, int]]:
    """Top-left (x, y) of each of the three cards on the canvas. Flush to the top
    (top border aligned with the sheet's top edge) and centred horizontally —
    which, with zero margin, means flush left/right and filling the full width."""
    w, h = card_print_size()
    block_w = 3 * w + 2 * GAP_PX
    x0 = (CANVAS_W - block_w) // 2
    y = MARGIN_PX
    return [(x0 + i * (w + GAP_PX), y) for i in range(3)]


# ----------------------------------------------------------------------
# Sheet layouts for the main 4R tool — chosen from a dropdown in the window.
# Besides the classic 3-up instax mini (with/without the white frame), the sheet
# can hold a plain grid of photos separated by white gutters you cut along.
# ----------------------------------------------------------------------
from dataclasses import dataclass   # noqa: E402

GRID_MARGIN_MM = 2.0   # outer white trim border of a grid sheet
GRID_GAP_MM = 3.0      # white gutter between photos (you cut down its middle)


def grid_cell_px(cols: int, rows: int, scale: int = 1) -> tuple[int, int]:
    """Pixel size of one photo cell in a cols×rows grid on the 4R sheet."""
    m = mm_to_px(GRID_MARGIN_MM) * scale
    g = mm_to_px(GRID_GAP_MM) * scale
    cw = (CANVAS_W * scale - 2 * m - (cols - 1) * g) // cols
    ch = (CANVAS_H * scale - 2 * m - (rows - 1) * g) // rows
    return cw, ch


def grid_cell_phys_w_mm(cols: int) -> float:
    return (CANVAS_W_MM - 2 * GRID_MARGIN_MM - (cols - 1) * GRID_GAP_MM) / cols


@dataclass(frozen=True)
class SheetLayout:
    key: str
    label: str
    kind: str          # "instax" | "instax_thin" | "grid"
    cols: int
    rows: int

    @property
    def n(self) -> int:
        return self.cols * self.rows

    def crop_size(self) -> tuple[int, int, float]:
        """(out_w, out_h, phys_w_mm) for each crop station in this layout.

        Instax layouts always crop UPRIGHT (portrait 46×62) — the rotated layout
        turns the finished print on the sheet, not the crop you compose."""
        if self.kind in ("instax", "instax_thin", "instax_portrait"):
            return INSTAX_W, INSTAX_H, INSTAX_W_MM
        cw, ch = grid_cell_px(self.cols, self.rows)
        return cw, ch, grid_cell_phys_w_mm(self.cols)


SHEET_LAYOUTS = [
    SheetLayout("instax3",      "3 × Instax mini — white frame",         "instax",          3, 1),
    SheetLayout("instax4_p",    "4 × Instax mini — no frame (portrait)", "instax_portrait", 2, 2),
    SheetLayout("grid2x2",      "2 × 2 grid — 4 photos",                 "grid",            2, 2),
    SheetLayout("grid3x2",      "3 × 2 grid — 6 photos",                 "grid",            3, 2),
    SheetLayout("grid2x3",      "2 × 3 grid — 6 photos",                 "grid",            2, 3),
]


def sheet_layout_by_key(key: str) -> SheetLayout:
    for l in SHEET_LAYOUTS:
        if l.key == key:
            return l
    return SHEET_LAYOUTS[0]


# ----------------------------------------------------------------------
# Instax formats — used by the Collage tool. Each format is defined in real
# millimetres plus the native image-area pixel size of its instax printer, so a
# collage exports at the right resolution to send straight to the printer.
# ----------------------------------------------------------------------
from dataclasses import dataclass   # noqa: E402  (grouped with its use)


@dataclass(frozen=True)
class InstaxFormat:
    key: str
    label: str
    img_w_mm: float          # image area (the photo content)
    img_h_mm: float
    card_w_mm: float         # full card including the white border
    card_h_mm: float
    top_border_mm: float     # top border (8 mm); bottom is the remainder (thick)
    print_px_w: int          # instax printer image-area resolution
    print_px_h: int

    @property
    def dpi_x(self) -> float:
        return self.print_px_w / (self.img_w_mm / 25.4)

    @property
    def dpi_y(self) -> float:
        return self.print_px_h / (self.img_h_mm / 25.4)

    def side_border_mm(self) -> float:
        return (self.card_w_mm - self.img_w_mm) / 2.0

    def gap_px(self, gap_mm: float) -> int:
        return round(gap_mm / 25.4 * self.dpi_x)

    def borders_px(self) -> tuple[int, int, int]:
        """(side, top, bottom) border thickness in pixels at print resolution."""
        side = round(self.side_border_mm() / 25.4 * self.dpi_x)
        top = round(self.top_border_mm / 25.4 * self.dpi_y)
        bottom_mm = self.card_h_mm - self.img_h_mm - self.top_border_mm
        bottom = round(bottom_mm / 25.4 * self.dpi_y)
        return side, top, bottom


# Pixel sizes are the image-area resolutions reported for Fujifilm's instax
# printers (SP-2 / Link for mini, SQ/SP-3 for square, Link Wide for wide).
INSTAX_FORMATS = [
    # All three share a 86 mm frame / 62 mm image → 24 mm vertical border,
    # split 8 mm top / 16 mm bottom. Only the side border differs by width.
    InstaxFormat("mini",   "Instax Mini",   46.0, 62.0,  54.0, 86.0, 8.0,  600, 800),
    InstaxFormat("square", "Instax Square", 62.0, 62.0,  72.0, 86.0, 8.0,  800, 800),
    InstaxFormat("wide",   "Instax Wide",   99.0, 62.0, 108.0, 86.0, 8.0, 1260, 840),
]


def format_by_key(key: str) -> InstaxFormat:
    for f in INSTAX_FORMATS:
        if f.key == key:
            return f
    return INSTAX_FORMATS[0]


# Preset collage layouts: (label, [cells]) where each cell is a normalised
# (x, y, w, h) rectangle in the instax frame (0–1). Cells fill the frame
# edge-to-edge in reading order — the instax film supplies the outer white
# border, so the collage itself adds none (only a thin gutter between photos).
def _grid(rows: int, cols: int):
    return [(c / cols, r / rows, 1 / cols, 1 / rows)
            for r in range(rows) for c in range(cols)]


COLLAGE_LAYOUTS = [
    ("1 photo",            _grid(1, 1)),
    ("2 — side by side",   _grid(1, 2)),
    ("2 — stacked",        _grid(2, 1)),
    ("3 — columns",        _grid(1, 3)),
    ("3 — rows",           _grid(3, 1)),
    ("3 — 1 top + 2",      [(0, 0, 1, 0.6), (0, 0.6, 0.5, 0.4), (0.5, 0.6, 0.5, 0.4)]),
    ("3 — 1 bottom + 2",   [(0, 0.4, 1, 0.6), (0, 0, 0.5, 0.4), (0.5, 0, 0.5, 0.4)]),
    ("3 — 1 left + 2",     [(0, 0, 0.6, 1), (0.6, 0, 0.4, 0.5), (0.6, 0.5, 0.4, 0.5)]),
    ("3 — 1 right + 2",    [(0.4, 0, 0.6, 1), (0, 0, 0.4, 0.5), (0, 0.5, 0.4, 0.5)]),
    ("4 — grid (2×2)",     _grid(2, 2)),
    ("4 — columns",        _grid(1, 4)),
    ("4 — rows",           _grid(4, 1)),
    ("5 — 1 top + 4",      [(0, 0, 1, 0.6),
                            (0.0, 0.6, 0.25, 0.4), (0.25, 0.6, 0.25, 0.4),
                            (0.5, 0.6, 0.25, 0.4), (0.75, 0.6, 0.25, 0.4)]),
    ("6 — grid (3×2)",     _grid(3, 2)),
    ("9 — grid (3×3)",     _grid(3, 3)),
]

# Gutter between photos (NOT an outer border — the film border covers the edge).
COLLAGE_GAP_CHOICES = [("None", 0.0), ("Thin", 0.8), ("Medium", 1.6)]
COLLAGE_GAP_MM = 0.8           # default: a thin hairline between photos
COLLAGE_BG = (255, 255, 255)   # BGR — the gutter colour
