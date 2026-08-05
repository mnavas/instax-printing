"""Assemble three instax-mini cards into a print-ready 4R (15×10 cm) canvas.

Each photo is placed inside a full 54×86 mm instax card (white border, thin at
the top, thick at the bottom) so that after printing and cutting along the marks
the results look like real instax minis.
"""
from __future__ import annotations

import cv2
import numpy as np

import instax_config as cfg


def make_instax_card(crop: np.ndarray) -> np.ndarray:
    """Render one instax card at native size: white 54×86 mm with the crop placed
    in the 46×62 mm image area (centred horizontally, offset toward the top)."""
    card = np.full((cfg.CARD_H, cfg.CARD_W, 3), 255, dtype=np.uint8)
    img = cv2.resize(crop, (cfg.INSTAX_W, cfg.INSTAX_H), interpolation=cv2.INTER_AREA)
    ox, oy = cfg.image_offset()
    card[oy:oy + cfg.INSTAX_H, ox:ox + cfg.INSTAX_W] = img
    return card


def _draw_cut_marks(canvas: np.ndarray, x: int, y: int, w: int, h: int) -> None:
    """Light-grey trim rectangle plus black corner crosses for one card."""
    x2, y2 = x + w, y + h
    cv2.rectangle(canvas, (x, y), (x2, y2), cfg.TRIM_LINE_COLOR, 1, cv2.LINE_AA)
    arm, t = cfg.CROSS_ARM_PX, cfg.CROSS_THICKNESS
    for cx, cy in ((x, y), (x2, y), (x, y2), (x2, y2)):
        cv2.line(canvas, (cx - arm, cy), (cx + arm, cy), cfg.CROSS_COLOR, t, cv2.LINE_AA)
        cv2.line(canvas, (cx, cy - arm), (cx, cy + arm), cfg.CROSS_COLOR, t, cv2.LINE_AA)


def build_4r(crops: list[np.ndarray]) -> np.ndarray:
    """Return a CANVAS_W×CANVAS_H BGR image with three instax cards laid out
    horizontally, centred, with cut marks at every card corner.

    `crops` must hold exactly three instax-ratio (image-area) images.
    """
    if len(crops) != 3:
        raise ValueError("build_4r expects exactly three crops")

    canvas = np.full((cfg.CANVAS_H, cfg.CANVAS_W, 3), 255, dtype=np.uint8)
    cw, ch = cfg.card_print_size()

    for (x, y), crop in zip(cfg.card_positions(), crops):
        card = make_instax_card(crop)
        resized = cv2.resize(card, (cw, ch), interpolation=cv2.INTER_AREA)
        canvas[y:y + ch, x:x + cw] = resized
        _draw_cut_marks(canvas, x, y, cw, ch)

    return canvas
