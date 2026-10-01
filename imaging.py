"""Image I/O and the crop-transform maths shared by the crop view and export.

The crop model: the output is a fixed instax-ratio rectangle. The user positions
an instax-shaped frame over the source by moving it (cx, cy in source pixels),
scaling it (scale), and rotating it (angle, degrees). A larger `scale` means the
frame is smaller in source space, i.e. a tighter, more zoomed-in crop.

    p_out = scale · R(angle) · (p_src − c) + o          (c = (cx, cy), o = output centre)

`min_scale` / `clamp_center` keep the (rotated) frame fully inside the image so
the crop never includes blank borders.
"""
from __future__ import annotations

import math
import os

import cv2
import numpy as np


def next_available_path(directory: str, base: str, ext: str) -> str:
    """A path in `directory` for `base+ext` that doesn't exist yet, appending
    _1, _2, … so successive saves never overwrite a previous file."""
    candidate = os.path.join(directory, f"{base}{ext}")
    if not os.path.exists(candidate):
        return candidate
    i = 1
    while True:
        candidate = os.path.join(directory, f"{base}_{i}{ext}")
        if not os.path.exists(candidate):
            return candidate
        i += 1


# ----------------------------------------------------------------------
# I/O — unicode-safe, and DPI-aware saving via Pillow
# ----------------------------------------------------------------------

def imread(path) -> np.ndarray | None:
    """Read an image as BGR uint8. Handles non-ASCII paths on all platforms."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        if data.size == 0:
            return None
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def imwrite_print(path, img_bgr: np.ndarray, dpi: int = 300) -> bool:
    """Save a BGR image with DPI metadata so it prints at the right physical size."""
    try:
        from PIL import Image

        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        Image.fromarray(rgb).save(str(path), dpi=(dpi, dpi))
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------
# Crop transform maths
# ----------------------------------------------------------------------

def _abs_cos_sin(angle_deg: float) -> tuple[float, float]:
    r = math.radians(angle_deg)
    return abs(math.cos(r)), abs(math.sin(r))


def min_scale(angle_deg: float, out_w: int, out_h: int, img_w: int, img_h: int) -> float:
    """Smallest scale at which the rotated output frame still fits in the image."""
    c, s = _abs_cos_sin(angle_deg)
    need_w = (out_w * c + out_h * s) / img_w
    need_h = (out_w * s + out_h * c) / img_h
    return max(need_w, need_h)


def _half_extents(angle_deg: float, scale: float, out_w: int, out_h: int) -> tuple[float, float]:
    c, s = _abs_cos_sin(angle_deg)
    hx = (out_w * c + out_h * s) / (2 * scale)
    hy = (out_w * s + out_h * c) / (2 * scale)
    return hx, hy


def clamp_center(cx: float, cy: float, angle_deg: float, scale: float,
                 out_w: int, out_h: int, img_w: int, img_h: int) -> tuple[float, float]:
    """Clamp the frame centre so the rotated frame stays inside the image."""
    hx, hy = _half_extents(angle_deg, scale, out_w, out_h)
    if hx * 2 >= img_w:
        cx = img_w / 2
    else:
        cx = max(hx, min(img_w - hx, cx))
    if hy * 2 >= img_h:
        cy = img_h / 2
    else:
        cy = max(hy, min(img_h - hy, cy))
    return cx, cy


def _rotation(angle_deg: float) -> np.ndarray:
    r = math.radians(angle_deg)
    ca, sa = math.cos(r), math.sin(r)
    return np.array([[ca, -sa], [sa, ca]], dtype=np.float64)


def crop_matrix(angle_deg: float, scale: float, cx: float, cy: float,
                out_w: int, out_h: int) -> np.ndarray:
    """2×3 affine mapping source pixels → output pixels for cv2.warpAffine."""
    R = _rotation(angle_deg)
    sr = scale * R
    o = np.array([out_w / 2.0, out_h / 2.0])
    c = np.array([cx, cy])
    t = o - sr @ c
    return np.array([[sr[0, 0], sr[0, 1], t[0]],
                     [sr[1, 0], sr[1, 1], t[1]]], dtype=np.float64)


def render_crop(img: np.ndarray, angle_deg: float, scale: float, cx: float, cy: float,
                out_w: int, out_h: int) -> np.ndarray:
    """Produce the instax-ratio crop as a fresh out_w×out_h BGR image."""
    M = crop_matrix(angle_deg, scale, cx, cy, out_w, out_h)
    return cv2.warpAffine(
        img, M, (out_w, out_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def crop_quad_src(angle_deg: float, scale: float, cx: float, cy: float,
                  out_w: int, out_h: int) -> np.ndarray:
    """The four output-rectangle corners expressed in source pixels (for the
    preview overlay). Returns a 4×2 array in TL, TR, BR, BL order."""
    Rt = _rotation(-angle_deg)
    o = np.array([out_w / 2.0, out_h / 2.0])
    c = np.array([cx, cy])
    corners = np.array([[0, 0], [out_w, 0], [out_w, out_h], [0, out_h]], dtype=np.float64)
    return np.array([c + (Rt @ (p - o)) / scale for p in corners])
