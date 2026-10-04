"""instax-printing — main window with a menu to switch between the 4R print
sheet tool and the instax collage tool."""
from __future__ import annotations

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QActionGroup, QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import composite
import instax_config as cfg
import ui_common
from a4_page import A4Page
from collage_page import CollagePage
from crop_station import CropSlot

class PreviewDialog(QDialog):
    """Shows a composed print (4R sheet or A4 sheet) with Save / Print."""

    def __init__(self, canvas_bgr, parent=None,
                 title="4R print preview — 15×10 cm",
                 base_name="instax_4r", dpi=cfg.PRINT_DPI, render_fn=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet(f"background-color: {ui_common.BG}; color: {ui_common.INK};")
        self._bgr = canvas_bgr
        self._base_name = base_name
        self._dpi = dpi
        self._render_fn = render_fn   # optional (scale)->bgr for high-res output

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
        self._hires = ui_common.hires_checkbox() if render_fn else None
        if self._hires:
            row.addWidget(self._hires)
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

    def _output(self):
        """(bgr, dpi) honouring the high-resolution toggle."""
        if self._hires and self._hires.isChecked() and self._render_fn:
            s = ui_common.HIRES_SCALE
            return self._render_fn(s), self._dpi * s
        return self._bgr, self._dpi

    def _save(self) -> None:
        bgr, dpi = self._output()
        ui_common.save_image(self, bgr, self._base_name, dpi=dpi)

    def _print(self) -> None:
        bgr, dpi = self._output()
        ui_common.print_image(self, bgr, dpi=dpi)


class SheetPreviewDialog(QDialog):
    """Preview the 4R sheet, choose the border style here, then Save / Print."""

    def __init__(self, crops_fn, parent=None):
        super().__init__(parent)
        self.setWindowTitle("4R print preview — 15×10 cm")
        self.setStyleSheet(f"background-color: {ui_common.BG}; color: {ui_common.INK};")
        self._crops_fn = crops_fn
        self._base_crops = crops_fn(1)   # scale-1 crops for the preview
        self._bgr = None

        layout = QVBoxLayout(self)
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._img_lbl)

        brow = QHBoxLayout()
        brow.setSpacing(8)
        lbl = QLabel("Border")
        lbl.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
        brow.addWidget(lbl)
        self._border = QComboBox()
        self._border.addItem("Instax border (white frame, thick bottom)", True)
        self._border.addItem("Thin border only (bigger photos)", False)
        self._border.currentIndexChanged.connect(self._render)
        brow.addWidget(self._border)
        brow.addSpacing(16)
        self._hires = ui_common.hires_checkbox()
        brow.addWidget(self._hires)
        brow.addStretch()
        layout.addLayout(brow)

        self._hint = QLabel("")
        self._hint.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 11px;")
        self._hint.setWordWrap(True)
        layout.addWidget(self._hint)

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

    def _build(self, scale: int):
        instax = self._border.currentData()
        crops = self._base_crops if scale == 1 else self._crops_fn(scale)
        return composite.build_4r(crops, instax_border=instax, scale=scale)

    def _render(self) -> None:
        instax = self._border.currentData()
        self._bgr = composite.build_4r(self._base_crops, instax_border=instax)
        self._hint.setText(
            "Each photo inside a full instax card — white frame, thick bottom."
            if instax else
            "Each photo with only a thin white border — bigger image; cut along the lines."
        )
        rgb = cv2.cvtColor(self._bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg).scaledToWidth(
            840, Qt.TransformationMode.SmoothTransformation
        )
        self._img_lbl.setPixmap(pix)

    def _output(self):
        scale = ui_common.HIRES_SCALE if self._hires.isChecked() else 1
        bgr = self._bgr if scale == 1 else self._build(scale)
        return bgr, cfg.PRINT_DPI * scale

    def _save(self) -> None:
        bgr, dpi = self._output()
        ui_common.save_image(self, bgr, "instax_4r", dpi=dpi)

    def _print(self) -> None:
        bgr, dpi = self._output()
        ui_common.print_image(self, bgr, dpi=dpi)


class SheetPage(QWidget):
    """The original tool: three instax-mini crops laid onto a 4R print sheet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        intro = QLabel(
            "Load three photos, then drag / mouse-wheel-zoom / rotate each so the "
            "instax frame covers what you want. When all three are ready, generate "
            "the 4R sheet."
        )
        intro.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
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
        self._status.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
        bottom.addWidget(self._status)
        bottom.addStretch()
        self._newsheet = QPushButton("New sheet")
        self._newsheet.setStyleSheet(ui_common.STYLE_BTN)
        self._newsheet.clicked.connect(self._on_new_sheet)
        bottom.addWidget(self._newsheet)
        self._generate = QPushButton("Generate 4R sheet")
        self._generate.setStyleSheet(ui_common.STYLE_ACCENT)
        self._generate.clicked.connect(self._on_generate)
        bottom.addWidget(self._generate)
        root.addLayout(bottom)

        self._update_state()

    def _update_state(self) -> None:
        ready = sum(1 for s in self.slots if s.is_ready())
        self._generate.setEnabled(ready == 3)
        self._newsheet.setEnabled(ready > 0)
        if ready < 3:
            self._status.setText(f"{ready} / 3 images loaded — load all three to continue.")
            self._status.setStyleSheet(f"color: {ui_common.MUTED}; font-size: 12px;")
        else:
            low = [i + 1 for i, s in enumerate(self.slots)
                   if s.canvas.source_dpi() < 180]
            if low:
                self._status.setText(
                    f"Ready — note: photo(s) {', '.join(map(str, low))} are below 180 DPI "
                    "and may look soft."
                )
                self._status.setStyleSheet(f"color: {ui_common.WARN}; font-size: 12px; font-weight: 600;")
            else:
                self._status.setText("All three ready and at good resolution ✓")
                self._status.setStyleSheet(f"color: {ui_common.OK}; font-size: 12px; font-weight: 600;")

    def _on_new_sheet(self) -> None:
        """Clear all three photos to start a fresh sheet (asks first)."""
        if any(s.is_ready() for s in self.slots):
            resp = QMessageBox.question(
                self, "New sheet",
                "Clear all three photos and start a new sheet?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
        for s in self.slots:
            s.clear()
        self._update_state()

    def _on_generate(self) -> None:
        if any(not s.is_ready() for s in self.slots):
            QMessageBox.warning(self, "Not ready", "All three images must be loaded first.")
            return
        SheetPreviewDialog(lambda scale=1: [s.get_output(scale) for s in self.slots], self).exec()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("instax-printing")
        self.resize(1240, 860)
        self.setStyleSheet(f"background-color: {ui_common.BG}; color: {ui_common.INK};")

        self._stack = QStackedWidget()
        self._sheet_page = SheetPage()
        self._collage_page = CollagePage()
        self._a4_page = A4Page(
            lambda bgr, parent, render_fn=None: PreviewDialog(
                bgr, parent, title="A4 instax sheet — 297×210 mm",
                base_name="instax_a4", dpi=cfg.PRINT_DPI, render_fn=render_fn)
        )
        self._stack.addWidget(self._sheet_page)     # index 0
        self._stack.addWidget(self._collage_page)   # index 1
        self._stack.addWidget(self._a4_page)        # index 2
        self.setCentralWidget(self._stack)

        self._build_menu()

    def _build_menu(self) -> None:
        bar = self.menuBar()

        file_menu = bar.addMenu("File")
        quit_act = file_menu.addAction("Quit")
        quit_act.setShortcut("Ctrl+Q")
        quit_act.triggered.connect(self.close)

        tools = bar.addMenu("Tools")
        group = QActionGroup(self)
        group.setExclusive(True)

        self._sheet_act = tools.addAction("4R Print Sheet (3 instax mini)")
        self._sheet_act.setCheckable(True)
        self._sheet_act.setChecked(True)
        self._sheet_act.triggered.connect(lambda: self._show_page(0))
        group.addAction(self._sheet_act)

        self._collage_act = tools.addAction("Instax Collage")
        self._collage_act.setCheckable(True)
        self._collage_act.triggered.connect(lambda: self._show_page(1))
        group.addAction(self._collage_act)

        self._a4_act = tools.addAction("A4 Instax Sheet")
        self._a4_act.setCheckable(True)
        self._a4_act.triggered.connect(lambda: self._show_page(2))
        group.addAction(self._a4_act)

    def _show_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        title = {0: "4R Print Sheet", 1: "Instax Collage", 2: "A4 Instax Sheet"}[index]
        self.setWindowTitle(f"instax-printing — {title}")
