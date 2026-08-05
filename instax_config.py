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

# Instax mini image area — 46×62 mm, portrait. This is the actual photo content
# of an instax mini (the white frame is not part of the picture).
INSTAX_W_MM = 46.0
INSTAX_H_MM = 62.0
INSTAX_W = mm_to_px(INSTAX_W_MM)   # 543
INSTAX_H = mm_to_px(INSTAX_H_MM)   # 732
INSTAX_RATIO = INSTAX_W / INSTAX_H  # ≈ 0.742 (w/h, portrait)

# Layout: three instax photos across the 4R width, centred, with small gaps.
GAP_MM = 4.0
MARGIN_MM = 4.0
GAP_PX = mm_to_px(GAP_MM)
MARGIN_PX = mm_to_px(MARGIN_MM)

# Corner cut-mark crosses.
CROSS_ARM_MM = 2.0          # length of each arm from the corner
CROSS_ARM_PX = mm_to_px(CROSS_ARM_MM)
CROSS_THICKNESS = 2         # px


def photo_size() -> tuple[int, int]:
    """Printed size (px) of each instax photo so three fit across the 4R width.

    Capped at the native instax size, so photos are never upscaled — with the
    default margins they come out a hair under full instax size.
    """
    avail_w = CANVAS_W - 2 * MARGIN_PX - 2 * GAP_PX
    w = min(INSTAX_W, avail_w // 3)
    h = round(w / INSTAX_RATIO)
    return w, h


def photo_positions() -> list[tuple[int, int]]:
    """Top-left (x, y) of each of the three photos on the canvas."""
    w, h = photo_size()
    block_w = 3 * w + 2 * GAP_PX
    x0 = (CANVAS_W - block_w) // 2
    y = (CANVAS_H - h) // 2
    return [(x0 + i * (w + GAP_PX), y) for i in range(3)]
