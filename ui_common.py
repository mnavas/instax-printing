"""Styles and save/print helpers shared by the sheet and collage tools."""
from __future__ import annotations

import os

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox

import imaging
import instax_config as cfg

STYLE_BTN = (
    "QPushButton { background-color: #333; color: #ddd; border: 1px solid #555; "
    "padding: 5px 12px; border-radius: 4px; font-size: 12px; }"
    "QPushButton:hover { background-color: #444; }"
    "QPushButton:disabled { color: #666; border-color: #333; }"
)
STYLE_MINI = (
    "QPushButton { background-color: #2a2a2a; color: #bbb; border: 1px solid #444; "
    "padding: 3px 8px; border-radius: 3px; font-size: 12px; }"
    "QPushButton:hover { background-color: #383838; }"
)
STYLE_ACCENT = (
    "QPushButton { background-color: #1e4a1e; color: #a8e0a8; border: 1px solid #3a7a3a; "
    "padding: 7px 18px; border-radius: 4px; font-size: 13px; font-weight: bold; }"
    "QPushButton:hover { background-color: #2a6a2a; }"
    "QPushButton:disabled { background-color: #262626; color: #666; border-color: #333; }"
)

# Folder the user saved to last, shared across both tools for the session.
_last_save_dir = ""


def save_image(parent, bgr: np.ndarray, base_name: str, dpi: int = cfg.PRINT_DPI) -> None:
    """Save `bgr` with DPI metadata, starting in the last-used folder and
    suggesting the next free `base_name[_N].jpg` so nothing is overwritten."""
    global _last_save_dir
    start_dir = _last_save_dir or os.path.expanduser("~")
    default_path = imaging.next_available_path(start_dir, base_name, ".jpg")
    path, _ = QFileDialog.getSaveFileName(
        parent, "Save image", default_path,
        "JPEG (*.jpg);;PNG (*.png);;TIFF (*.tif)",
    )
    if not path:
        return
    _last_save_dir = os.path.dirname(path)
    if imaging.imwrite_print(path, bgr, dpi):
        QMessageBox.information(parent, "Saved", f"Saved at {dpi} DPI:\n{path}")
    else:
        QMessageBox.warning(parent, "Save failed", "Could not write the file.")


def print_image(parent, bgr: np.ndarray, dpi: int = cfg.PRINT_DPI) -> None:
    """Send `bgr` to a printer, scaled to fit the page and centred."""
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setResolution(dpi)
    dlg = QPrintDialog(printer, parent)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
    painter = QPainter(printer)
    rect = painter.viewport()
    scaled = qimg.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    x = (rect.width() - scaled.width()) // 2
    y = (rect.height() - scaled.height()) // 2
    painter.drawImage(x, y, scaled)
    painter.end()
