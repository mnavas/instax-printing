"""The A4 Instax Sheet tool: pick an instax format, load photos into a grid of
the most cards that fit on a landscape A4, and generate a print-ready A4 sheet
(true-size instax cards with cut lines, centred) for home printing."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import a4_sheet
import instax_config as cfg
import ui_common
from crop_station import CropSlot

_MAX_GRID_LINES = 12


class A4Page(QWidget):
    """Format picker over a grid of the max crop stations that fit on an A4."""

    def __init__(self, preview_factory, parent=None):
        super().__init__(parent)
        self._preview_factory = preview_factory   # (bgr, parent) -> QDialog
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        intro = QLabel(
            "Fill as many cards as you like (you don't have to fill them all), "
            "then generate a print-ready A4: true-size instax cards with cut lines, "
            "centred on the page for home printing — print it and cut them out."
        )
        intro.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
        intro.setWordWrap(True)
        root.addWidget(intro)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        lbl = QLabel("Format")
        lbl.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
        controls.addWidget(lbl)
        self._fmt = QComboBox()
        for f in cfg.INSTAX_FORMATS:
            self._fmt.addItem(f.label, f.key)
        controls.addWidget(self._fmt)
        self._cap = QLabel("")
        self._cap.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
        controls.addWidget(self._cap)
        controls.addStretch()
        self._new = QPushButton("New sheet")
        self._new.setStyleSheet(ui_common.STYLE_BTN)
        self._new.clicked.connect(self._on_new)
        controls.addWidget(self._new)
        root.addLayout(controls)

        self._fmt.currentIndexChanged.connect(self._rebuild_cells)

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)
        root.addWidget(self._grid_host, stretch=1)

        bottom = QHBoxLayout()
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
        bottom.addWidget(self._status)
        bottom.addStretch()
        self._generate = QPushButton("Generate A4 sheet")
        self._generate.setStyleSheet(ui_common.STYLE_ACCENT)
        self._generate.clicked.connect(self._on_generate)
        bottom.addWidget(self._generate)
        root.addLayout(bottom)

        self._slots: list[CropSlot] = []
        self._rebuild_cells()

    def _current(self) -> cfg.InstaxFormat:
        return cfg.format_by_key(self._fmt.currentData())

    def _rebuild_cells(self) -> None:
        fmt = self._current()
        cols, rows = a4_sheet.max_grid(fmt)
        n = cols * rows
        iw, ih = cfg.mm_to_px(fmt.img_w_mm), cfg.mm_to_px(fmt.img_h_mm)

        while len(self._slots) < n:
            idx = len(self._slots)
            self._slots.append(CropSlot(idx, self._update_state, iw, ih, fmt.img_w_mm,
                                        label=f"Load #{idx + 1}"))
        while len(self._slots) > n:
            extra = self._slots.pop()
            self._grid.removeWidget(extra)
            extra.deleteLater()

        for i in range(_MAX_GRID_LINES):
            self._grid.setColumnStretch(i, 0)
            self._grid.setRowStretch(i, 0)

        for i, slot in enumerate(self._slots):
            self._grid.removeWidget(slot)
            slot.set_output_size(iw, ih, fmt.img_w_mm)
            self._grid.addWidget(slot, i // cols, i % cols)
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        for r in range(rows):
            self._grid.setRowStretch(r, 1)

        self._cap.setText(f"— up to {n} per A4 ({cols}×{rows})")
        self._update_state()

    def _on_new(self) -> None:
        if any(s.is_ready() for s in self._slots):
            resp = QMessageBox.question(
                self, "New sheet",
                "Clear every photo and start a new A4 sheet?",
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
        self._generate.setEnabled(ready > 0)
        self._new.setEnabled(ready > 0)
        low = [i + 1 for i, s in enumerate(self._slots)
               if s.is_ready() and s.canvas.source_dpi() < 180]
        if ready == 0:
            self._status.setText(f"0 / {total} cards loaded — load at least one.")
            self._status.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
        elif low:
            self._status.setText(
                f"{ready} / {total} loaded — card(s) {', '.join(map(str, low))} are below "
                "180 DPI and may look soft."
            )
            self._status.setStyleSheet(f"color: {ui_common.WARN}; font-size: 12px; font-weight: 600;")
        else:
            self._status.setText(f"{ready} / {total} cards loaded and at good resolution ✓")
            self._status.setStyleSheet(f"color: {ui_common.OK}; font-size: 12px; font-weight: 600;")

    def _on_generate(self) -> None:
        crops = [s.get_output() for s in self._slots if s.is_ready()]
        if not crops:
            QMessageBox.warning(self, "Not ready", "Load at least one photo first.")
            return
        sheet = a4_sheet.build_a4(self._current(), crops)
        self._preview_factory(sheet, self).exec()
