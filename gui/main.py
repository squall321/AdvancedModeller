#!/usr/bin/env python3
"""KooMesh Modeller GUI - Entry Point"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.shell import AppShell


def main():
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Set default font
    font = QFont("Segoe UI", 10)
    if not font.exactMatch():
        font = QFont("Noto Sans", 10)
    app.setFont(font)

    # Create and show app shell
    window = AppShell()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
