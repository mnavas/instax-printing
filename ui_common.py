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

# ── instax-inspired palette ──────────────────────────────────────────────
# Clean light panels with the signature instax pink and a few playful accents;
# image areas stay dark for good photo contrast (like the real white-framed
# instax print on a colourful body).
INK     = "#2C2722"   # primary text (warm near-black)
MUTED   = "#8C847B"   # secondary text
BG      = "#F4F1EC"   # app background (warm off-white)
PANEL   = "#FFFFFF"   # cards / inputs
BORDER  = "#E4DED4"   # hairline borders
CANVAS  = "#201F23"   # image/crop background (dark)
PINK    = "#EC4C84"   # instax brand pink (primary accent)
PINK_DK = "#D6356F"   # pink hover/pressed
PINK_SOFT = "#FBE4EE" # pink tint (hover backgrounds)
MINT    = "#2FBBA4"   # playful accent
SKY     = "#3FA3E6"   # playful accent
SUN     = "#F6C544"   # playful accent
OK      = "#2EA06A"   # status: good
WARN    = "#D6364F"   # status: warning

STYLE_ACCENT = (
    f"QPushButton {{ background-color: {PINK}; color: #ffffff; border: none; "
    f"padding: 8px 20px; border-radius: 9px; font-size: 13px; font-weight: 700; }}"
    f"QPushButton:hover {{ background-color: {PINK_DK}; }}"
    f"QPushButton:disabled {{ background-color: #ECD6DF; color: #ffffff; }}"
)
STYLE_BTN = (
    f"QPushButton {{ background-color: {PANEL}; color: {INK}; "
    f"border: 1.5px solid {BORDER}; padding: 7px 16px; border-radius: 9px; "
    f"font-size: 12px; font-weight: 600; }}"
    f"QPushButton:hover {{ border-color: {PINK}; color: {PINK}; }}"
    f"QPushButton:disabled {{ color: #BEB6AC; border-color: #EEE9E1; }}"
)
STYLE_MINI = (
    f"QPushButton {{ background-color: #EFEAE1; color: {INK}; border: none; "
    f"padding: 5px 10px; border-radius: 7px; font-size: 12px; font-weight: 600; }}"
    f"QPushButton:hover {{ background-color: #E7E0D4; color: {PINK_DK}; }}"
)

# Global stylesheet applied once on the QApplication — makes the common widgets
# (checkboxes, combos, sliders, menus, tooltips) consistent and clearly visible.
APP_QSS = f"""
QWidget {{ color: {INK}; font-size: 12px; }}
QToolTip {{ background: {INK}; color: #ffffff; border: none; padding: 4px 8px; }}

QCheckBox {{ color: {INK}; spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px;
    border: 2px solid #B6ADA2; background: {PANEL}; }}
QCheckBox::indicator:hover {{ border-color: {PINK}; }}
QCheckBox::indicator:checked {{ background: {PINK}; border: 2px solid {PINK}; }}
QCheckBox::indicator:checked:hover {{ background: {PINK_DK}; border-color: {PINK_DK}; }}

QComboBox {{ background: {PANEL}; color: {INK}; border: 1.5px solid {BORDER};
    border-radius: 7px; padding: 4px 10px; }}
QComboBox:hover {{ border-color: {PINK}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{ background: {PANEL}; color: {INK};
    border: 1px solid {BORDER}; outline: none;
    selection-background-color: {PINK}; selection-color: #ffffff; }}

QSlider::groove:horizontal {{ height: 5px; border-radius: 3px; background: {BORDER}; }}
QSlider::sub-page:horizontal {{ background: {PINK}; border-radius: 3px; }}
QSlider::handle:horizontal {{ width: 15px; height: 15px; margin: -6px 0;
    border-radius: 8px; background: {PINK}; border: 2px solid #ffffff; }}
QSlider::handle:horizontal:hover {{ background: {PINK_DK}; }}

QMenuBar {{ background: {PANEL}; color: {INK}; border-bottom: 1px solid {BORDER}; }}
QMenuBar::item {{ padding: 7px 12px; background: transparent; }}
QMenuBar::item:selected {{ background: {PINK_SOFT}; color: {PINK_DK}; border-radius: 6px; }}
QMenu {{ background: {PANEL}; color: {INK}; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 6px 22px; border-radius: 5px; }}
QMenu::item:selected {{ background: {PINK_SOFT}; color: {PINK_DK}; }}
QMenu::item:checked {{ color: {PINK_DK}; font-weight: 700; }}

QMessageBox {{ background: {BG}; }}
"""

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
