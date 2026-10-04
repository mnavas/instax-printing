"""Assemble three instax-mini cards into a print-ready 4R (15×10 cm) canvas.

Each photo is placed inside a full 54×86 mm instax card (white border, thin at
the top, thick at the bottom) so that after printing and cutting along the marks
the results look like real instax minis.
"""
from __future__ import annotations

import cv2
import numpy as np

import instax_config as cfg


def make_instax_card(crop: np.ndarray, scale: int = 1) -> np.ndarray:
    """Render one instax card at `scale`× native size: white 54×86 mm with the
    crop in the 46×62 mm image area (centred horizontally, offset toward the top)."""
    cw, ch = cfg.CARD_W * scale, cfg.CARD_H * scale
    iw, ih = cfg.INSTAX_W * scale, cfg.INSTAX_H * scale
    ox, oy = cfg.image_offset()
    ox, oy = ox * scale, oy * scale
    card = np.full((ch, cw, 3), 255, dtype=np.uint8)
    card[oy:oy + ih, ox:ox + iw] = cv2.resize(crop, (iw, ih), interpolation=cv2.INTER_AREA)
    return card


def _draw_cut_marks(canvas: np.ndarray, positions, cw: int, ch: int, scale: int = 1) -> None:
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
        cv2.line(canvas, (x, 0), (x, cfg.CANVAS_H * scale), gray, g, cv2.LINE_AA)
    # Bottom trim across the full width
    cv2.line(canvas, (x_left, y_bot), (x_right, y_bot), gray, g, cv2.LINE_AA)


def make_thin_card(crop: np.ndarray, border_px: int, scale: int = 1) -> np.ndarray:
    """The instax image area with only a thin uniform white border on every side
    (no instax frame) — a near-borderless print. `border_px` is already scaled."""
    iw, ih = cfg.INSTAX_W * scale, cfg.INSTAX_H * scale
    b = border_px
    card = np.full((ih + 2 * b, iw + 2 * b, 3), 255, dtype=np.uint8)
    card[b:b + ih, b:b + iw] = cv2.resize(crop, (iw, ih), interpolation=cv2.INTER_AREA)
    return card


def _build_4r_instax(crops: list[np.ndarray], scale: int = 1) -> np.ndarray:
    """Three full instax cards, packed edge-to-edge and flush to the top, with cut
    marks only where cuts are needed."""
    canvas = np.full((cfg.CANVAS_H * scale, cfg.CANVAS_W * scale, 3), 255, dtype=np.uint8)
    cw, ch = cfg.card_print_size()
    cw, ch = cw * scale, ch * scale
    positions = [(x * scale, y * scale) for x, y in cfg.card_positions()]
    for (x, y), crop in zip(positions, crops):
        card = make_instax_card(crop, scale)
        resized = cv2.resize(card, (cw, ch), interpolation=cv2.INTER_AREA)
        canvas[y:y + ch, x:x + cw] = resized
    _draw_cut_marks(canvas, positions, cw, ch, scale)
    return canvas


def _build_4r_thin(crops: list[np.ndarray], border_mm: float, scale: int = 1) -> np.ndarray:
    """Three thin-bordered (near-borderless) photos tiled across the 4R, centred,
    each outlined with a cut line."""
    b = cfg.mm_to_px(border_mm) * scale
    W, H = cfg.CANVAS_W * scale, cfg.CANVAS_H * scale
    native_w, native_h = cfg.INSTAX_W * scale + 2 * b, cfg.INSTAX_H * scale + 2 * b
    # Size the cards so three fit across the 4R width (capped at native size).
    w = min(native_w, W // 3)
    h = round(w * native_h / native_w)
    if h > H:
        h = H
        w = round(h * native_w / native_h)

    canvas = np.full((H, W, 3), 255, dtype=np.uint8)
    x0 = (W - 3 * w) // 2
    y0 = (H - h) // 2
    for i, crop in enumerate(crops):
        card = cv2.resize(make_thin_card(crop, b, scale), (w, h), interpolation=cv2.INTER_AREA)
        x = x0 + i * w
        canvas[y0:y0 + h, x:x + w] = card
        cv2.rectangle(canvas, (x, y0), (x + w - 1, y0 + h - 1),
                      cfg.TRIM_LINE_COLOR, 1, cv2.LINE_AA)
    return canvas


def build_4r(crops: list[np.ndarray], instax_border: bool = True,
             thin_border_mm: float = 2.0, scale: int = 1) -> np.ndarray:
    """Return a (CANVAS_W×scale)×(CANVAS_H×scale) BGR 4R sheet of three photos.

    `instax_border=True` places each photo in a full instax card (white frame,
    thick bottom). `instax_border=False` gives each photo only a thin uniform
    white border (bigger image). `scale` multiplies the output resolution (2 =
    600 DPI). `crops` must hold exactly three instax-ratio images, rendered at the
    same `scale`.
    """
    if len(crops) != 3:
        raise ValueError("build_4r expects exactly three crops")
    if instax_border:
        return _build_4r_instax(crops, scale)
    return _build_4r_thin(crops, thin_border_mm, scale)
