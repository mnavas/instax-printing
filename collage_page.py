"""The Instax Collage tool: pick an instax format and a preset grid layout, fill
each cell with a photo, and export the collage — as a bare image for an instax
printer, or with the white instax border drawn on."""
from __future__ import annotations

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import collage
import instax_config as cfg
import ui_common
from crop_station import CropSlot

_COMBO = (
    "QComboBox { background-color: #2a2a2a; color: #ddd; border: 1px solid #444; "
    "padding: 3px 8px; border-radius: 3px; font-size: 12px; }"
)


class CollagePage(QWidget):
    """Format + layout pickers over a rows×cols grid of crop stations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        intro = QLabel(
            "Build a collage sized for an instax print. Pick a format and a "
            "layout, load a photo into each cell, then export — as a plain image "
            "for an instax printer, or with the white instax border."
        )
        intro.setStyleSheet("color: #aaa; font-size: 12px;")
        intro.setWordWrap(True)
        root.addWidget(intro)

        # Controls row
        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.addWidget(self._tag("Format"))
        self._fmt = QComboBox()
        self._fmt.setStyleSheet(_COMBO)
        for f in cfg.INSTAX_FORMATS:
            self._fmt.addItem(f.label, f.key)
        self._fmt.currentIndexChanged.connect(self._rebuild_cells)
        controls.addWidget(self._fmt)

        controls.addWidget(self._tag("Layout"))
        self._layout = QComboBox()
        self._layout.setStyleSheet(_COMBO)
        for name, rows, cols in cfg.COLLAGE_LAYOUTS:
            self._layout.addItem(name, (rows, cols))
        self._layout.currentIndexChanged.connect(self._rebuild_cells)
        controls.addWidget(self._layout)

        controls.addStretch()
        self._new = QPushButton("New collage")
        self._new.setStyleSheet(ui_common.STYLE_BTN)
        self._new.clicked.connect(self._on_new)
        controls.addWidget(self._new)
        root.addLayout(controls)

        # Cell grid
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(8)
        root.addWidget(self._grid_host, stretch=1)

        # Bottom bar
        bottom = QHBoxLayout()
        self._status = QLabel("")
        self._status.setStyleSheet("color: #999; font-size: 12px;")
        bottom.addWidget(self._status)
        bottom.addStretch()
        self._export = QPushButton("Export collage…")
        self._export.setStyleSheet(ui_common.STYLE_ACCENT)
        self._export.clicked.connect(self._on_export)
        bottom.addWidget(self._export)
        root.addLayout(bottom)

        self._slots: list[CropSlot] = []
        self._rebuild_cells()

    @staticmethod
    def _tag(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #999; font-size: 12px;")
        return lbl

    # -- layout management --
    def _current(self):
        fmt = cfg.format_by_key(self._fmt.currentData())
        rows, cols = self._layout.currentData()
        return fmt, rows, cols

    def _rebuild_cells(self) -> None:
        # Tear down the old grid of stations.
        for slot in self._slots:
            self._grid.removeWidget(slot)
            slot.deleteLater()
        self._slots = []

        fmt, rows, cols = self._current()
        out_w, out_h, phys_w_mm = collage.cell_output_size(fmt, rows, cols)
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                slot = CropSlot(idx, self._update_state, out_w, out_h, phys_w_mm,
                                label=f"Load #{idx + 1}")
                self._grid.addWidget(slot, r, c)
                self._slots.append(slot)
        self._update_state()

    def _on_new(self) -> None:
        if any(s.is_ready() for s in self._slots):
            resp = QMessageBox.question(
                self, "New collage",
                "Clear every photo in this collage and start over?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
        for s in self._slots:
            s.clear()
        self._update_state()

    def _update_state(self) -> None:
        total = len(self._slots)
        ready = sum(1 for s in self._slots if s.is_ready())
        self._export.setEnabled(ready == total and total > 0)
        self._new.setEnabled(ready > 0)
        if ready < total:
            self._status.setText(f"{ready} / {total} photos loaded — fill every cell to export.")
            self._status.setStyleSheet("color: #999; font-size: 12px;")
        else:
            low = [i + 1 for i, s in enumerate(self._slots) if s.canvas.source_dpi() < 180]
            if low:
                self._status.setText(
                    f"Ready — note: cell(s) {', '.join(map(str, low))} are below 180 DPI "
                    "and may look soft."
                )
                self._status.setStyleSheet("color: #ff8080; font-size: 12px;")
            else:
                self._status.setText("All cells ready and at good resolution ✓")
                self._status.setStyleSheet("color: #6ab86a; font-size: 12px;")

    def _on_export(self) -> None:
        crops = [s.get_output() for s in self._slots]
        if any(c is None for c in crops):
            QMessageBox.warning(self, "Not ready", "Every cell must have a photo first.")
            return
        fmt, rows, cols = self._current()
        CollagePreviewDialog(fmt, rows, cols, crops, self).exec()


class CollagePreviewDialog(QDialog):
    """Preview the collage with a border toggle, then Save / Print."""

    def __init__(self, fmt, rows, cols, crops, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{fmt.label} collage preview")
        self.setStyleSheet("background-color: #111; color: #ddd;")
        self._fmt = fmt
        self._rows, self._cols = rows, cols
        self._crops = crops
        self._bgr = None

        layout = QVBoxLayout(self)
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setMinimumSize(360, 360)
        layout.addWidget(self._img_lbl)

        self._border = QCheckBox("Add white instax border  (off = image only, for an instax printer)")
        self._border.setStyleSheet("color: #ccc; font-size: 12px;")
        self._border.toggled.connect(self._render)
        layout.addWidget(self._border)

        row = QHBoxLayout()
        row.addStretch()
        save = QPushButton("Save…")
        save.setStyleSheet(ui_common.STYLE_ACCENT)
        save.clicked.connect(self._save)
        printb = QPushButton("Print…")
        printb.setStyleSheet(ui_common.STYLE_BTN)
        printb.clicked.connect(self._print)
        close = QPushButton("Close")
        close.setStyleSheet(ui_common.STYLE_BTN)
        close.clicked.connect(self.reject)
        for w in (save, printb, close):
            row.addWidget(w)
        layout.addLayout(row)

        self._render()

    def _render(self) -> None:
        self._bgr = collage.build_collage(
            self._fmt, self._rows, self._cols, self._crops, self._border.isChecked()
        )
        rgb = cv2.cvtColor(self._bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg).scaled(
            720, 560, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._img_lbl.setPixmap(pix)

    def _save(self) -> None:
        tail = "border" if self._border.isChecked() else "image"
        ui_common.save_image(self, self._bgr, f"instax_{self._fmt.key}_collage_{tail}",
                             dpi=round(self._fmt.dpi_x))

    def _print(self) -> None:
        ui_common.print_image(self, self._bgr, dpi=round(self._fmt.dpi_x))
