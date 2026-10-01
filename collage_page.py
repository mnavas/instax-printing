"""The Instax Collage tool: pick an instax format, a preset layout, and a gutter
size, fill each cell with a photo, and export the collage — as a bare image for
an instax printer (the film supplies the border), or wrapped in a white instax
card for a normal printer."""
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
_MAX_GRID_LINES = 10   # for clearing old row/column stretches on rebuild


class CollagePage(QWidget):
    """Format + layout + gutter pickers over a grid of crop stations that
    mirrors the chosen layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        intro = QLabel(
            "Build a collage sized for an instax print. Pick a format, a layout, "
            "and the gutter between photos, load a photo into each cell, then "
            "export — a plain image for an instax printer (the film adds the white "
            "border), or wrapped in a border for a normal printer."
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
        controls.addWidget(self._fmt)

        controls.addWidget(self._tag("Layout"))
        self._layout = QComboBox()
        self._layout.setStyleSheet(_COMBO)
        for name, template in cfg.COLLAGE_LAYOUTS:
            self._layout.addItem(name, template)
        controls.addWidget(self._layout)

        controls.addWidget(self._tag("Gutter"))
        self._gap = QComboBox()
        self._gap.setStyleSheet(_COMBO)
        for name, mm in cfg.COLLAGE_GAP_CHOICES:
            self._gap.addItem(name, mm)
        self._gap.setCurrentIndex(1)   # "Thin" default
        controls.addWidget(self._gap)

        controls.addStretch()
        self._new = QPushButton("New collage")
        self._new.setStyleSheet(ui_common.STYLE_BTN)
        self._new.clicked.connect(self._on_new)
        controls.addWidget(self._new)
        root.addLayout(controls)

        # Connect after populating so no premature rebuild fires
        self._fmt.currentIndexChanged.connect(self._rebuild_cells)
        self._layout.currentIndexChanged.connect(self._rebuild_cells)
        self._gap.currentIndexChanged.connect(self._rebuild_cells)

        # Cell grid (mirrors the layout)
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)
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
        template = self._layout.currentData()
        gap_mm = self._gap.currentData()
        return fmt, template, gap_mm

    def _rebuild_cells(self) -> None:
        for slot in self._slots:
            self._grid.removeWidget(slot)
            slot.deleteLater()
        self._slots = []
        for i in range(_MAX_GRID_LINES):     # clear stale spans/stretches
            self._grid.setColumnStretch(i, 0)
            self._grid.setRowStretch(i, 0)

        fmt, template, gap_mm = self._current()
        sizes = collage.cell_output_sizes(fmt, template, gap_mm)

        # Map the layout's cut lines to grid rows/columns so the stations mirror
        # the actual collage arrangement (spans + proportional stretch).
        xs = sorted({round(c[0], 4) for c in template} | {round(c[0] + c[2], 4) for c in template})
        ys = sorted({round(c[1], 4) for c in template} | {round(c[1] + c[3], 4) for c in template})
        col_of = {v: i for i, v in enumerate(xs)}
        row_of = {v: i for i, v in enumerate(ys)}

        for i, ((nx, ny, nw, nh), (w, h, phys)) in enumerate(zip(template, sizes)):
            slot = CropSlot(i, self._update_state, w, h, phys, label=f"Load #{i + 1}")
            r0, r1 = row_of[round(ny, 4)], row_of[round(ny + nh, 4)]
            c0, c1 = col_of[round(nx, 4)], col_of[round(nx + nw, 4)]
            self._grid.addWidget(slot, r0, c0, r1 - r0, c1 - c0)
            self._slots.append(slot)

        for i in range(len(xs) - 1):
            self._grid.setColumnStretch(i, max(1, round((xs[i + 1] - xs[i]) * 1000)))
        for i in range(len(ys) - 1):
            self._grid.setRowStretch(i, max(1, round((ys[i + 1] - ys[i]) * 1000)))

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
        fmt, template, gap_mm = self._current()
        CollagePreviewDialog(fmt, template, crops, gap_mm, self).exec()


class CollagePreviewDialog(QDialog):
    """Preview the collage with an optional instax border, then Save / Print."""

    def __init__(self, fmt, template, crops, gap_mm, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{fmt.label} collage preview")
        self.setStyleSheet("background-color: #111; color: #ddd;")
        self._fmt = fmt
        self._template = template
        self._crops = crops
        self._gap_mm = gap_mm
        self._bgr = None

        layout = QVBoxLayout(self)
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setMinimumSize(360, 360)
        layout.addWidget(self._img_lbl)

        self._border = QCheckBox(
            "Add white instax border — for a normal printer "
            "(an instax printer adds its own, so leave this off for instax)"
        )
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
            self._fmt, self._template, self._crops, self._border.isChecked(), self._gap_mm
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
