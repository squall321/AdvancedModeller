#!/usr/bin/env python3
"""Model Viewer 테스트 스크립트"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core" / "kfile_parser"))

# Qt 환경 변수
os.environ.setdefault('QT_API', 'pyside6')

from PySide6.QtWidgets import QApplication
from gui.modules.model_viewer.module import ModelViewerModule
from gui.app_context import AppContext

def main():
    app = QApplication(sys.argv)

    # AppContext 생성
    ctx = AppContext()

    # Model Viewer 생성
    viewer = ModelViewerModule(ctx)
    viewer.setWindowTitle("Model Viewer - 테스트")
    viewer.resize(1024, 768)
    viewer.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
