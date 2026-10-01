"""Compose several photos into one instax-format collage.

The photos tile the instax image area edge-to-edge (at the printer's native
resolution), separated only by a thin gutter between neighbours — there is **no
outer margin**, because the instax film already supplies the physical white
border. Export the bare image area to send to an instax printer; the optional
bordered variant (for a *normal* printer) wraps it in a full white instax card.
"""
from __future__ import annotations

import cv2
import numpy as np

import instax_config as cfg

_EPS = 1e-6


def cell_rects(template, width: int, height: int, gap: int):
    """Pixel (x, y, w, h) for each normalised cell in `template`, filling
    width×height edge-to-edge with a `gap` gutter only *between* neighbours
    (outer edges stay flush — the film border covers them)."""
    half = gap / 2.0
    out = []
    for (nx, ny, nw, nh) in template:
        x0, y0 = nx * width, ny * height
        x1, y1 = (nx + nw) * width, (ny + nh) * height
        hl = half if nx > _EPS else 0.0            # inset only internal edges
        ht = half if ny > _EPS else 0.0
        hr = half if (nx + nw) < 1 - _EPS else 0.0
        hb = half if (ny + nh) < 1 - _EPS else 0.0
        X0, Y0 = round(x0 + hl), round(y0 + ht)
        X1, Y1 = round(x1 - hr), round(y1 - hb)
        out.append((X0, Y0, max(1, X1 - X0), max(1, Y1 - Y0)))
    return out


def cell_output_sizes(fmt: cfg.InstaxFormat, template, gap_mm: float = cfg.COLLAGE_GAP_MM):
    """Per-cell (w, h, physical_width_mm) — each crop renders at its own cell
    size (cells may differ) and the physical width feeds the DPI readout."""
    gap = fmt.gap_px(gap_mm)
    rects = cell_rects(template, fmt.print_px_w, fmt.print_px_h, gap)
    return [(w, h, fmt.img_w_mm * w / fmt.print_px_w) for (_, _, w, h) in rects]


def build_collage(fmt: cfg.InstaxFormat, template, crops: list[np.ndarray],
                  gap_mm: float = cfg.COLLAGE_GAP_MM, bg=cfg.COLLAGE_BG) -> np.ndarray:
    """Assemble the bare collage image area (the instax printer's native size).
    `crops` must hold exactly len(template) images. Add a border afterwards with
    `add_border` if printing on a normal printer."""
    if len(crops) != len(template):
        raise ValueError("build_collage expects exactly len(template) crops")

    w_px, h_px = fmt.print_px_w, fmt.print_px_h
    gap = fmt.gap_px(gap_mm)
    area = np.full((h_px, w_px, 3), bg, dtype=np.uint8)
    for (x, y, cw, ch), crop in zip(cell_rects(template, w_px, h_px, gap), crops):
        area[y:y + ch, x:x + cw] = cv2.resize(crop, (cw, ch), interpolation=cv2.INTER_AREA)
    return area


# Border modes for export (chosen in the print preview).
BORDER_NONE = "none"    # image only — for an instax printer (film adds the border)
BORDER_EVEN = "even"    # a plain white border of a chosen width on all sides
BORDER_FILM = "film"    # the real instax card border (thin top/sides, thick bottom)


def add_border(area: np.ndarray, fmt: cfg.InstaxFormat, mode: str,
               even_mm: float = 4.0) -> np.ndarray:
    """Wrap the collage image area in a border for a normal printer.

    `BORDER_NONE` returns it unchanged; `BORDER_EVEN` adds `even_mm` of white on
    every side; `BORDER_FILM` reproduces the asymmetric instax card border.
    """
    h, w = area.shape[:2]
    if mode == BORDER_FILM:
        side, top, bottom = fmt.borders_px()
        card = np.full((top + h + bottom, side + w + side, 3), 255, dtype=np.uint8)
        card[top:top + h, side:side + w] = area
        return card
    if mode == BORDER_EVEN:
        m = max(0, round(even_mm / 25.4 * fmt.dpi_x))
        if m == 0:
            return area
        out = np.full((h + 2 * m, w + 2 * m, 3), 255, dtype=np.uint8)
        out[m:m + h, m:m + w] = area
        return out
    return area
