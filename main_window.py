"""instax-printing — arrange three instax-mini crops onto a print-ready 4R sheet."""
from __future__ import annotations

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import composite
import imaging
import instax_config as cfg
from crop_canvas import CropCanvas

_BTN = (
    "QPushButton { background-color: #333; color: #ddd; border: 1px solid #555; "
    "padding: 5px 12px; border-radius: 4px; font-size: 12px; }"
    "QPushButton:hover { background-color: #444; }"
    "QPushButton:disabled { color: #666; border-color: #333; }"
)
_MINI = (
    "QPushButton { background-color: #2a2a2a; color: #bbb; border: 1px solid #444; "
    "padding: 3px 8px; border-radius: 3px; font-size: 12px; }"
    "QPushButton:hover { background-color: #383838; }"
)
_ACCENT = (
    "QPushButton { background-color: #1e4a1e; color: #a8e0a8; border: 1px solid #3a7a3a; "
    "padding: 7px 18px; border-radius: 4px; font-size: 13px; font-weight: bold; }"
    "QPushButton:hover { background-color: #2a6a2a; }"
    "QPushButton:disabled { background-color: #262626; color: #666; border-color: #333; }"
)


class CropSlot(QWidget):
    """One of the three crop stations: image + load/rotate/reset + zoom/angle sliders."""

    def __init__(self, index: int, on_change, parent=None):
        super().__init__(parent)
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.canvas = CropCanvas()
        self.canvas.changed.connect(self._sync_from_canvas)
        layout.addWidget(self.canvas, stretch=1)

        # Load / rotate / reset row
        row = QHBoxLayout()
        row.setSpacing(4)
        load = QPushButton(f"Load #{index + 1}")
        load.setStyleSheet(_MINI)
        load.clicked.connect(self._on_load)
        rot_l = QPushButton("⟲ 90")
        rot_l.setStyleSheet(_MINI)
        rot_l.clicked.connect(lambda: self._rotate(-90))
        rot_r = QPushButton("⟳ 90")
        rot_r.setStyleSheet(_MINI)
        rot_r.clicked.connect(lambda: self._rotate(90))
        reset = QPushButton("Reset")
        reset.setStyleSheet(_MINI)
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
        self._dpi_lbl.setStyleSheet("color: #888; font-size: 11px;")
        self._dpi_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._dpi_lbl)

    @staticmethod
    def _tag(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #999; font-size: 11px;")
        lbl.setFixedWidth(40)
        return lbl

    # -- actions --
    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose an image", "",
            "Images (*.jpg *.jpeg *.png *.tif *.tiff *.webp);;All files (*)",
        )
        if not path:
            return
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
                "color: #ff8080; font-size: 11px;" if dpi < 180
                else "color: #888; font-size: 11px;"
            )
        self._on_change()

    def is_ready(self) -> bool:
        return self.canvas.is_ready()

    def get_output(self):
        return self.canvas.get_output()


class PreviewDialog(QDialog):
    """Shows the composed 4R sheet with Save / Print."""

    def __init__(self, canvas_bgr, parent=None):
        super().__init__(parent)
        self.setWindowTitle("4R print preview — 15×10 cm")
        self.setStyleSheet("background-color: #111; color: #ddd;")
        self._bgr = canvas_bgr

        layout = QVBoxLayout(self)
        rgb = cv2.cvtColor(canvas_bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg).scaledToWidth(
            900, Qt.TransformationMode.SmoothTransformation
        )
        img_lbl = QLabel()
        img_lbl.setPixmap(pix)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(img_lbl)

        row = QHBoxLayout()
        row.addStretch()
        save = QPushButton("Save…")
        save.setStyleSheet(_ACCENT)
        save.clicked.connect(self._save)
        printb = QPushButton("Print…")
        printb.setStyleSheet(_BTN)
        printb.clicked.connect(self._print)
        close = QPushButton("Close")
        close.setStyleSheet(_BTN)
        close.clicked.connect(self.reject)
        for w in (save, printb, close):
            row.addWidget(w)
        layout.addLayout(row)

    def _save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save 4R sheet", "instax_4r.jpg",
            "JPEG (*.jpg);;PNG (*.png);;TIFF (*.tif)",
        )
        if not path:
            return
        if imaging.imwrite_print(path, self._bgr, cfg.PRINT_DPI):
            QMessageBox.information(self, "Saved", f"Saved at {cfg.PRINT_DPI} DPI:\n{path}")
        else:
            QMessageBox.warning(self, "Save failed", "Could not write the file.")

    def _print(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setResolution(cfg.PRINT_DPI)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        rgb = cv2.cvtColor(self._bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
        from PyQt6.QtGui import QPainter
        painter = QPainter(printer)
        rect = painter.viewport()
        scaled = qimg.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
        x = (rect.width() - scaled.width()) // 2
        y = (rect.height() - scaled.height()) // 2
        painter.drawImage(x, y, scaled)
        painter.end()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("instax-printing — 3 × instax mini on a 4R sheet")
        self.resize(1240, 860)
        self.setStyleSheet("background-color: #111; color: #ddd;")

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        intro = QLabel(
            "Load three photos, then drag / mouse-wheel-zoom / rotate each so the "
            "instax frame covers what you want. When all three are ready, generate "
            "the 4R sheet."
        )
        intro.setStyleSheet("color: #aaa; font-size: 12px;")
        intro.setWordWrap(True)
        root.addWidget(intro)

        slots_row = QHBoxLayout()
        slots_row.setSpacing(8)
        self.slots = [CropSlot(i, self._update_state) for i in range(3)]
        for slot in self.slots:
            slots_row.addWidget(slot, stretch=1)
        root.addLayout(slots_row, stretch=1)

        bottom = QHBoxLayout()
        self._status = QLabel("")
        self._status.setStyleSheet("color: #999; font-size: 12px;")
        bottom.addWidget(self._status)
        bottom.addStretch()
        self._generate = QPushButton("Generate 4R sheet")
        self._generate.setStyleSheet(_ACCENT)
        self._generate.clicked.connect(self._on_generate)
        bottom.addWidget(self._generate)
        root.addLayout(bottom)

        self._update_state()

    def _update_state(self) -> None:
        ready = sum(1 for s in self.slots if s.is_ready())
        self._generate.setEnabled(ready == 3)
        if ready < 3:
            self._status.setText(f"{ready} / 3 images loaded — load all three to continue.")
            self._status.setStyleSheet("color: #999; font-size: 12px;")
        else:
            low = [i + 1 for i, s in enumerate(self.slots)
                   if s.canvas.source_dpi() < 180]
            if low:
                self._status.setText(
                    f"Ready — note: photo(s) {', '.join(map(str, low))} are below 180 DPI "
                    "and may look soft."
                )
                self._status.setStyleSheet("color: #ff8080; font-size: 12px;")
            else:
                self._status.setText("All three ready and at good resolution ✓")
                self._status.setStyleSheet("color: #6ab86a; font-size: 12px;")

    def _on_generate(self) -> None:
        crops = [s.get_output() for s in self.slots]
        if any(c is None for c in crops):
            QMessageBox.warning(self, "Not ready", "All three images must be loaded first.")
            return
        sheet = composite.build_4r(crops)
        PreviewDialog(sheet, self).exec()
