"""pytest configuration file"""
import sys
import os
from pathlib import Path
import pytest

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core" / "kfile_parser"))


# 헤드리스 환경을 위한 환경 변수 설정
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


# QApplication 픽스처
_qapp = None

@pytest.fixture(scope="session")
def qapp():
    """테스트 세션 동안 사용할 QApplication 인스턴스"""
    global _qapp
    from PySide6.QtWidgets import QApplication

    if _qapp is None:
        _qapp = QApplication.instance()
        if _qapp is None:
            _qapp = QApplication([])

    yield _qapp


@pytest.fixture(autouse=True)
def auto_qapp(qapp):
    """모든 테스트에 자동으로 QApplication 적용"""
    yield
