#!/usr/bin/env python3
"""KooMesh Modeller GUI - Entry Point"""
import sys
import os
from pathlib import Path

# Windows 콘솔 UTF-8 인코딩 설정 (한글 깨짐 방지)
if sys.platform == 'win32':
    try:
        # Python 3.7+ Windows UTF-8 모드
        if hasattr(sys, 'set_utf8_mode'):
            sys.set_utf8_mode(True)
        # 콘솔 인코딩 강제 설정
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        # 환경변수 설정
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

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
