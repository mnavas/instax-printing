"""Interactive crop widget: the whole source is shown with a frame the user can
drag, zoom (mouse wheel) and rotate. The frame is always kept inside the image so
the crop can never contain blank edges.

The output rectangle is parameterised (``out_w`` × ``out_h``), so the same widget
drives both the instax-mini sheet crop and arbitrary-aspect collage cells."""
from __future__ import annotations

import cv2
import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import QWidget

import imaging
import instax_config as cfg

_DEF_OUT_W, _DEF_OUT_H = cfg.INSTAX_W, cfg.INSTAX_H
_MAX_ZOOM = 8.0   # frame may shrink to 1/8 of the "fills the image" size


class CropCanvas(QWidget):
    changed = pyqtSignal()

    def __init__(self, out_w: int = _DEF_OUT_W, out_h: int = _DEF_OUT_H,
                 phys_w_mm: float = cfg.INSTAX_W_MM, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #161616;")

        self._out_w = out_w
        self._out_h = out_h
        self._phys_w_mm = phys_w_mm   # physical width of the output, for the DPI hint

        self._img: np.ndarray | None = None
        self._pix: QPixmap | None = None
        self._w = self._h = 0

        self.angle = 0.0        # degrees
        self.zoom = 1.0         # ≥ 1; multiplies the minimum (fills-image) scale
        self.cx = self.cy = 0.0  # frame centre in source pixels

        self._view_scale = 1.0
        self._view_off = QPointF(0, 0)
        self._drag_last: QPointF | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        return self._img is not None

    def set_output_size(self, out_w: int, out_h: int, phys_w_mm: float | None = None) -> None:
        """Change the crop's aspect ratio / target size (e.g. for a new collage
        layout). Keeps the loaded image but re-clamps the frame to stay valid."""
        self._out_w = out_w
        self._out_h = out_h
        if phys_w_mm is not None:
            self._phys_w_mm = phys_w_mm
        if self._img is not None:
            self._apply()
        else:
            self.update()   # refresh the empty target frame's aspect ratio

    def set_image(self, path) -> bool:
        img = imaging.imread(path)
        if img is None:
            return False
        self._img = img
        self._h, self._w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, self._w, self._h, 3 * self._w, QImage.Format.Format_RGB888)
        self._pix = QPixmap.fromImage(qimg.copy())
        self.reset_view()
        return True

    def reset_view(self) -> None:
        self.angle = 0.0
        self.zoom = 1.0
        self.cx, self.cy = self._w / 2, self._h / 2
        self._apply()

    def clear(self) -> None:
        """Unload the image and return to the empty 'Click Load' state."""
        self._img = None
        self._pix = None
        self._w = self._h = 0
        self.angle = 0.0
        self.zoom = 1.0
        self.cx = self.cy = 0.0
        self._drag_last = None
        self.update()
        self.changed.emit()

    def rotate_by(self, delta_deg: float) -> None:
        self.set_angle(self.angle + delta_deg)

    def set_angle(self, angle_deg: float) -> None:
        self.angle = ((angle_deg + 180) % 360) - 180   # wrap to (-180, 180]
        self._apply()

    def set_zoom(self, zoom: float) -> None:
        self.zoom = max(1.0, min(_MAX_ZOOM, zoom))
        self._apply()

    def scale(self) -> float:
        s_min = imaging.min_scale(self.angle, self._out_w, self._out_h, self._w, self._h)
        return s_min * self.zoom

    def get_output(self) -> np.ndarray | None:
        if self._img is None:
            return None
        return imaging.render_crop(
            self._img, self.angle, self.scale(), self.cx, self.cy, self._out_w, self._out_h
        )

    def source_dpi(self) -> float:
        """Effective print resolution of the current crop, in DPI. Below ~180
        the print will look soft."""
        if self._img is None:
            return 0.0
        # Output width self._out_w spans self._phys_w_mm; source contributes
        # self._out_w / scale px across that width.
        src_px = self._out_w / self.scale()
        inches = self._phys_w_mm / 25.4
        return src_px / inches

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _apply(self) -> None:
        if self._img is None:
            return
        self.cx, self.cy = imaging.clamp_center(
            self.cx, self.cy, self.angle, self.scale(),
            self._out_w, self._out_h, self._w, self._h
        )
        self.update()
        self.changed.emit()

    def _empty_frame_rect(self) -> QRectF:
        """Centred rectangle with the crop's aspect ratio, for the empty state."""
        margin = 14.0
        avail_w = max(1.0, self.width() - 2 * margin)
        avail_h = max(1.0, self.height() - 2 * margin)
        ar = self._out_w / self._out_h
        fw = avail_w
        fh = fw / ar
        if fh > avail_h:
            fh = avail_h
            fw = fh * ar
        return QRectF((self.width() - fw) / 2, (self.height() - fh) / 2, fw, fh)

    def _compute_view(self) -> None:
        if self._img is None:
            return
        vw, vh = self.width(), self.height()
        self._view_scale = min(vw / self._w, vh / self._h)
        dw, dh = self._w * self._view_scale, self._h * self._view_scale
        self._view_off = QPointF((vw - dw) / 2, (vh - dh) / 2)

    def _src_to_view(self, p) -> QPointF:
        return QPointF(p[0] * self._view_scale + self._view_off.x(),
                       p[1] * self._view_scale + self._view_off.y())

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#161616"))
        if self._img is None or self._pix is None:
            # Draw the instax target frame (correct aspect/orientation) so the
            # empty slot reads as portrait/landscape before any photo is loaded.
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rect = self._empty_frame_rect()
            painter.fillRect(rect, QColor("#1d1d1d"))
            pen = QPen(QColor("#3a5a80"), 2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect)
            painter.setPen(QColor("#8a8a8a"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter,
                             "Click Load\nto choose an image")
            return

        self._compute_view()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Source image, fit to widget
        dw = self._w * self._view_scale
        dh = self._h * self._view_scale
        painter.drawPixmap(
            int(self._view_off.x()), int(self._view_off.y()),
            int(round(dw)), int(round(dh)), self._pix
        )

        # Crop frame as a polygon in view space
        quad = imaging.crop_quad_src(self.angle, self.scale(), self.cx, self.cy,
                                     self._out_w, self._out_h)
        poly = QPolygonF([self._src_to_view(p) for p in quad])

        # Dim everything outside the frame
        outside = QPainterPath()
        outside.addRect(0.0, 0.0, float(self.width()), float(self.height()))
        inside = QPainterPath()
        inside.addPolygon(poly)
        inside.closeSubpath()
        painter.fillPath(outside.subtracted(inside), QColor(0, 0, 0, 130))

        # Frame outline + rule-of-thirds guides
        painter.setPen(QPen(QColor("#4a9eff"), 2))
        painter.drawPolygon(poly)
        painter.setPen(QPen(QColor(255, 255, 255, 90), 1))
        for i in (1, 2):
            f = i / 3.0
            top = poly[0] + (poly[1] - poly[0]) * f
            bot = poly[3] + (poly[2] - poly[3]) * f
            painter.drawLine(top, bot)
            left = poly[0] + (poly[3] - poly[0]) * f
            right = poly[1] + (poly[2] - poly[1]) * f
            painter.drawLine(left, right)

    def wheelEvent(self, event) -> None:
        if self._img is None:
            return
        step = 1.0015 ** event.angleDelta().y()   # smooth zoom
        self.set_zoom(self.zoom * step)

    def mousePressEvent(self, event) -> None:
        if self._img is not None and event.button() == Qt.MouseButton.LeftButton:
            self._drag_last = event.position()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_last is None or self._img is None:
            return
        pos = event.position()
        dx = (pos.x() - self._drag_last.x()) / self._view_scale
        dy = (pos.y() - self._drag_last.y()) / self._view_scale
        self._drag_last = pos
        # Dragging moves the frame in the drag direction.
        self.cx += dx
        self.cy += dy
        self._apply()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_last = None
