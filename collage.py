"""Compose several photos into one instax-format collage.

The photos are laid out in a preset rows×cols grid that fills the instax image
area (at the printer's native resolution), with a thin white gutter between and
around the cells. The result can be exported either as the bare image area —
ready to send to an instax printer, which adds the physical border itself — or
with the white instax border drawn on, for printing on a normal printer.
"""
from __future__ import annotations

import cv2
import numpy as np

import instax_config as cfg


def grid_cells(rows: int, cols: int, width: int, height: int, gap: int):
    """Pixel (x, y, w, h) of each cell in a rows×cols grid inside width×height,
    with a uniform `gap` gutter on every side and between cells (reading order)."""
    cw = (width - (cols + 1) * gap) / cols
    ch = (height - (rows + 1) * gap) / rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            x = round(gap + c * (cw + gap))
            y = round(gap + r * (ch + gap))
            cells.append((x, y, round(cw), round(ch)))
    return cells


def cell_output_size(fmt: cfg.InstaxFormat, rows: int, cols: int,
                     gap_mm: float = cfg.COLLAGE_GAP_MM):
    """The pixel (w, h) each cell's crop should render at, plus the physical
    width (mm) of a cell — for the per-cell DPI readout."""
    gap = fmt.gap_px(gap_mm)
    _, _, w, h = grid_cells(rows, cols, fmt.print_px_w, fmt.print_px_h, gap)[0]
    phys_w_mm = fmt.img_w_mm * w / fmt.print_px_w
    return w, h, phys_w_mm


def build_collage(fmt: cfg.InstaxFormat, rows: int, cols: int,
                  crops: list[np.ndarray], with_border: bool,
                  gap_mm: float = cfg.COLLAGE_GAP_MM, bg=cfg.COLLAGE_BG) -> np.ndarray:
    """Assemble the collage. `crops` must hold exactly rows*cols images. Returns
    the bare image area (``with_border=False``) or the full instax card."""
    if len(crops) != rows * cols:
        raise ValueError("build_collage expects exactly rows*cols crops")

    w_px, h_px = fmt.print_px_w, fmt.print_px_h
    gap = fmt.gap_px(gap_mm)
    area = np.full((h_px, w_px, 3), bg, dtype=np.uint8)
    for (x, y, cw, ch), crop in zip(grid_cells(rows, cols, w_px, h_px, gap), crops):
        area[y:y + ch, x:x + cw] = cv2.resize(crop, (cw, ch), interpolation=cv2.INTER_AREA)

    if not with_border:
        return area

    side, top, bottom = fmt.borders_px()
    card = np.full((top + h_px + bottom, side + w_px + side, 3), 255, dtype=np.uint8)
    card[top:top + h_px, side:side + w_px] = area
    return card
