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
# area sits centred horizontally with a thin top border and a thick bottom
# border (the classic instax look): 4 mm sides, 4 mm top, 20 mm bottom.
CARD_W_MM = 54.0
CARD_H_MM = 86.0
CARD_W = mm_to_px(CARD_W_MM)   # 638
CARD_H = mm_to_px(CARD_H_MM)   # 1016
CARD_RATIO = CARD_W / CARD_H
TOP_BORDER_MM = 4.0
TOP_BORDER_PX = mm_to_px(TOP_BORDER_MM)   # ~47; bottom border is the remainder (~20 mm)

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
    top_border_mm: float     # top/side borders are equal; bottom is the thick one
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
    InstaxFormat("mini",   "Instax Mini",   46.0, 62.0,  54.0, 86.0, 4.0,  600, 800),
    InstaxFormat("square", "Instax Square", 62.0, 62.0,  72.0, 86.0, 5.0,  800, 800),
    InstaxFormat("wide",   "Instax Wide",   99.0, 62.0, 108.0, 86.0, 4.0, 1260, 840),
]


def format_by_key(key: str) -> InstaxFormat:
    for f in INSTAX_FORMATS:
        if f.key == key:
            return f
    return INSTAX_FORMATS[0]


# Preset collage layouts: (label, rows, cols). Cells fill one instax frame in
# reading order (left→right, top→bottom).
COLLAGE_LAYOUTS = [
    ("1 photo",          1, 1),
    ("2 — stacked",      2, 1),
    ("2 — side by side", 1, 2),
    ("3 — rows",         3, 1),
    ("3 — columns",      1, 3),
    ("4 — grid (2×2)",   2, 2),
]

COLLAGE_GAP_MM = 2.0            # white gutter between (and around) collage cells
COLLAGE_BG = (255, 255, 255)   # BGR — the gutter / background colour
