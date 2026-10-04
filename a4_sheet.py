"""Pack the maximum number of instax cards onto a landscape A4 page for home
printing: real white-bordered instax cards tiled in a centred block (kept a few
mm inside the A4 so it prints centred without edge-clipping), with light-grey cut
lines around each card so they're easy to cut out.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

import instax_config as cfg

A4_W_MM, A4_H_MM = 297.0, 210.0        # A4 landscape
A4_W = cfg.mm_to_px(A4_W_MM)           # 3508 @ 300 DPI
A4_H = cfg.mm_to_px(A4_H_MM)           # 2480 @ 300 DPI
EDGE_MARGIN_MM = 4.0                    # keep the card block this far inside the A4


def card_px(fmt: cfg.InstaxFormat) -> tuple[int, int]:
    """Full instax card size in pixels at 300 DPI (physical print size)."""
    return cfg.mm_to_px(fmt.card_w_mm), cfg.mm_to_px(fmt.card_h_mm)


def max_grid(fmt: cfg.InstaxFormat) -> tuple[int, int]:
    """(cols, rows) — the most cards of this format that fit on a landscape A4
    while staying a small margin inside the page."""
    cols = int((A4_W_MM - 2 * EDGE_MARGIN_MM) // fmt.card_w_mm)
    rows = int((A4_H_MM - 2 * EDGE_MARGIN_MM) // fmt.card_h_mm)
    return max(1, cols), max(1, rows)


def max_count(fmt: cfg.InstaxFormat) -> int:
    cols, rows = max_grid(fmt)
    return cols * rows


def make_card(fmt: cfg.InstaxFormat, crop: np.ndarray, scale: int = 1) -> np.ndarray:
    """One full instax card at `scale`× 300 DPI: white border with the crop placed
    in the image area (centred horizontally, thin top, thick bottom)."""
    cw, ch = card_px(fmt)
    cw, ch = cw * scale, ch * scale
    iw, ih = cfg.mm_to_px(fmt.img_w_mm) * scale, cfg.mm_to_px(fmt.img_h_mm) * scale
    side = (cw - iw) // 2
    top = cfg.mm_to_px(fmt.top_border_mm) * scale
    card = np.full((ch, cw, 3), 255, dtype=np.uint8)
    card[top:top + ih, side:side + iw] = cv2.resize(crop, (iw, ih), interpolation=cv2.INTER_AREA)
    return card


def build_a4(fmt: cfg.InstaxFormat, crops: list[np.ndarray], scale: int = 1) -> np.ndarray:
    """Return an A4-landscape (`scale`× 300 DPI) white canvas with up to
    `max_count(fmt)` instax cards packed in a centred block, each outlined with a
    cut line. `scale` multiplies the output resolution (2 = 600 DPI).

    `crops` are instax image-area crops (one per card, rendered at the same
    `scale`); extras beyond the page capacity are ignored.
    """
    cols, rows = max_grid(fmt)
    k = min(len(crops), cols * rows)
    if k == 0:
        raise ValueError("build_a4 needs at least one crop")

    cw, ch = card_px(fmt)
    cw, ch = cw * scale, ch * scale
    w_px, h_px = A4_W * scale, A4_H * scale
    cols_used = min(k, cols)
    rows_used = math.ceil(k / cols)
    block_w, block_h = cols_used * cw, rows_used * ch
    x0 = (w_px - block_w) // 2
    y0 = (h_px - block_h) // 2

    canvas = np.full((h_px, w_px, 3), 255, dtype=np.uint8)
    for i, crop in enumerate(crops[:k]):
        r, c = divmod(i, cols)
        x, y = x0 + c * cw, y0 + r * ch
        canvas[y:y + ch, x:x + cw] = make_card(fmt, crop, scale)
        cv2.rectangle(canvas, (x, y), (x + cw - 1, y + ch - 1),
                      cfg.TRIM_LINE_COLOR, 1, cv2.LINE_AA)
    return canvas
