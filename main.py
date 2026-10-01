"""instax-printing — entry point."""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

import ui_common
from main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(ui_common.APP_QSS)   # instax-inspired global styling
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
