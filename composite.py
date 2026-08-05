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


def _cross(canvas: np.ndarray, x: int, y: int) -> None:
    arm, t = cfg.CROSS_ARM_PX, cfg.CROSS_THICKNESS
    cv2.line(canvas, (x - arm, y), (x + arm, y), cfg.CROSS_COLOR, t, cv2.LINE_AA)
    cv2.line(canvas, (x, y - arm), (x, y + arm), cfg.CROSS_COLOR, t, cv2.LINE_AA)


def _draw_cut_marks(canvas: np.ndarray, positions, cw: int, ch: int) -> None:
    """Only the cuts that are actually needed with the edge-to-edge, top-flush
    layout: two vertical cuts between the three cards and one horizontal trim at
    the card bottom. The left, right and top borders are the sheet's own edges.
    """
    gray, g = cfg.TRIM_LINE_COLOR, 1
    y_top = positions[0][1]
    y_bot = y_top + ch
    x_left = positions[0][0]
    x_right = positions[2][0] + cw
    boundaries = [positions[1][0], positions[2][0]]   # card1|card2 and card2|card3

    # Vertical cuts (full sheet height for an easy straight cut)
    for x in boundaries:
        cv2.line(canvas, (x, 0), (x, cfg.CANVAS_H), gray, g, cv2.LINE_AA)
    # Bottom trim across the full width
    cv2.line(canvas, (x_left, y_bot), (x_right, y_bot), gray, g, cv2.LINE_AA)

    # Crosses at the cut endpoints and intersections to line the blade up
    for x in boundaries:
        _cross(canvas, x, y_top)   # top of each vertical cut (sheet top edge)
        _cross(canvas, x, y_bot)   # where a vertical meets the bottom trim
    _cross(canvas, x_left, y_bot)
    _cross(canvas, x_right, y_bot)


def build_4r(crops: list[np.ndarray]) -> np.ndarray:
    """Return a CANVAS_W×CANVAS_H BGR image with three instax cards packed
    edge-to-edge and flush to the top, with cut marks only where cuts are needed.

    `crops` must hold exactly three instax-ratio (image-area) images.
    """
    if len(crops) != 3:
        raise ValueError("build_4r expects exactly three crops")

    canvas = np.full((cfg.CANVAS_H, cfg.CANVAS_W, 3), 255, dtype=np.uint8)
    cw, ch = cfg.card_print_size()
    positions = cfg.card_positions()

    for (x, y), crop in zip(positions, crops):
        card = make_instax_card(crop)
        resized = cv2.resize(card, (cw, ch), interpolation=cv2.INTER_AREA)
        canvas[y:y + ch, x:x + cw] = resized

    _draw_cut_marks(canvas, positions, cw, ch)
    return canvas
