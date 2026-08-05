"""Assemble three instax crops into a print-ready 4R (15×10 cm) canvas."""
from __future__ import annotations

import cv2
import numpy as np

import instax_config as cfg


def _draw_cross(canvas: np.ndarray, x: int, y: int) -> None:
    """Small black plus centred on (x, y) marking a cut corner."""
    arm = cfg.CROSS_ARM_PX
    t = cfg.CROSS_THICKNESS
    black = (0, 0, 0)
    cv2.line(canvas, (x - arm, y), (x + arm, y), black, t, cv2.LINE_AA)
    cv2.line(canvas, (x, y - arm), (x, y + arm), black, t, cv2.LINE_AA)


def build_4r(crops: list[np.ndarray]) -> np.ndarray:
    """Return a CANVAS_W×CANVAS_H BGR image with the three instax crops laid
    out horizontally, centred, with cut-mark crosses at every photo corner.

    `crops` must hold exactly three instax-ratio images (any size; they are
    resized to the printed photo size).
    """
    if len(crops) != 3:
        raise ValueError("build_4r expects exactly three crops")

    canvas = np.full((cfg.CANVAS_H, cfg.CANVAS_W, 3), 255, dtype=np.uint8)
    pw, ph = cfg.photo_size()

    for (x, y), crop in zip(cfg.photo_positions(), crops):
        resized = cv2.resize(crop, (pw, ph), interpolation=cv2.INTER_AREA)
        canvas[y:y + ph, x:x + pw] = resized
        # Cut crosses at the four corners of this photo.
        for cx, cy in ((x, y), (x + pw, y), (x, y + ph), (x + pw, y + ph)):
            _draw_cross(canvas, cx, cy)

    return canvas
