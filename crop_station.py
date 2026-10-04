"""CropSlot — one crop station: a CropCanvas plus load / rotate / reset controls,
zoom and angle sliders, and a live effective-DPI readout. Used by both the 4R
sheet tool and the collage tool (the only difference is the crop's output size)."""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import instax_config as cfg
import ui_common
from crop_canvas import CropCanvas
from ui_common import STYLE_MINI


class CropSlot(QWidget):
    """Image + load/rotate/reset + zoom/angle sliders + DPI hint."""

    _last_dir = ""   # remembered across every slot, both tools

    # Extensions we can decode; both cases are listed because the native (OS)
    # file dialog matches glob patterns case-sensitively, so plain "*.jpg" would
    # hide ".JPG" photos and make the folder look empty.
    _IMG_EXTS = ("jpg", "jpeg", "jpe", "jfif", "png", "tif", "tiff", "bmp", "webp")

    def __init__(self, index: int, on_change, out_w: int = cfg.INSTAX_W,
                 out_h: int = cfg.INSTAX_H, phys_w_mm: float = cfg.INSTAX_W_MM,
                 label: str | None = None, parent=None):
        super().__init__(parent)
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.canvas = CropCanvas(out_w, out_h, phys_w_mm)
        self.canvas.changed.connect(self._sync_from_canvas)
        layout.addWidget(self.canvas, stretch=1)

        # Load / rotate / reset row
        row = QHBoxLayout()
        row.setSpacing(4)
        load = QPushButton(label or f"Load #{index + 1}")
        load.setStyleSheet(STYLE_MINI)
        load.clicked.connect(self._on_load)
        rot_l = QPushButton("⟲ 90")
        rot_l.setStyleSheet(STYLE_MINI)
        rot_l.clicked.connect(lambda: self._rotate(-90))
        rot_r = QPushButton("⟳ 90")
        rot_r.setStyleSheet(STYLE_MINI)
        rot_r.clicked.connect(lambda: self._rotate(90))
        reset = QPushButton("Reset")
        reset.setStyleSheet(STYLE_MINI)
        reset.clicked.connect(self._reset)
        for w in (load, rot_l, rot_r, reset):
            row.addWidget(w)
        layout.addLayout(row)

        # Zoom slider
        zrow = QHBoxLayout()
        zrow.addWidget(self._tag("Zoom"))
        self._zoom = QSlider(Qt.Orientation.Horizontal)
        self._zoom.setRange(100, 800)   # 1.00× … 8.00×
        self._zoom.setValue(100)
        self._zoom.valueChanged.connect(self._on_zoom_slider)
        zrow.addWidget(self._zoom)
        layout.addLayout(zrow)

        # Angle slider
        arow = QHBoxLayout()
        arow.addWidget(self._tag("Angle"))
        self._angle = QSlider(Qt.Orientation.Horizontal)
        self._angle.setRange(-180, 180)
        self._angle.setValue(0)
        self._angle.valueChanged.connect(self._on_angle_slider)
        arow.addWidget(self._angle)
        layout.addLayout(arow)

        self._dpi_lbl = QLabel("")
        self._dpi_lbl.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 11px;")
        self._dpi_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._dpi_lbl)

    @staticmethod
    def _tag(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 11px;")
        lbl.setFixedWidth(40)
        return lbl

    # -- actions --
    def _on_load(self) -> None:
        start = self._last_dir or os.path.expanduser("~")
        patterns = " ".join(f"*.{e} *.{e.upper()}" for e in self._IMG_EXTS)
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose an image", start,
            f"Images ({patterns});;All files (*)",
        )
        if not path:
            return
        CropSlot._last_dir = os.path.dirname(path)
        if not self.canvas.set_image(path):
            QMessageBox.warning(self, "Load failed", "Could not read that image.")
            return
        self._sync_from_canvas()
        self._on_change()

    def _rotate(self, delta: int) -> None:
        self.canvas.rotate_by(delta)

    def _reset(self) -> None:
        if self.canvas.is_ready():
            self.canvas.reset_view()

    def _on_zoom_slider(self, value: int) -> None:
        self.canvas.set_zoom(value / 100.0)

    def _on_angle_slider(self, value: int) -> None:
        self.canvas.set_angle(float(value))

    def _sync_from_canvas(self) -> None:
        """Reflect wheel/drag changes back into the sliders and DPI hint."""
        for slider, val in ((self._zoom, round(self.canvas.zoom * 100)),
                            (self._angle, round(self.canvas.angle))):
            slider.blockSignals(True)
            slider.setValue(int(val))
            slider.blockSignals(False)
        if self.canvas.is_ready():
            dpi = self.canvas.source_dpi()
            warn = "  ⚠ low-res" if dpi < 180 else ""
            self._dpi_lbl.setText(f"≈ {dpi:.0f} DPI{warn}")
            self._dpi_lbl.setStyleSheet(
                f"color: {ui_common.WARN}; font-size: 11px; font-weight: 600;" if dpi < 180
                else f"color: {ui_common.MUTED}; font-size: 11px;"
            )
        self._on_change()

    def set_output_size(self, out_w: int, out_h: int, phys_w_mm: float) -> None:
        self.canvas.set_output_size(out_w, out_h, phys_w_mm)

    def clear(self) -> None:
        """Unload this slot's photo and reset its controls."""
        self.canvas.clear()   # emits changed → sliders reset via _sync_from_canvas
        self._dpi_lbl.setText("")

    def is_ready(self) -> bool:
        return self.canvas.is_ready()

    def get_output(self, scale: int = 1):
        return self.canvas.get_output(scale)
