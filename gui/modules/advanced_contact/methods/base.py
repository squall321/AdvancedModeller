"""Base class for contact methods"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.app_context import AppContext


class BaseContactMethod(QWidget):
    """
    Contact 모듈의 메소드별 UI/로직 베이스

    새 메소드 추가 시:
    1. 이 클래스 상속
    2. method_id, method_name 구현
    3. _setup_ui() 구현
    4. generate_script() 구현
    5. methods/__init__.py의 CONTACT_METHODS에 등록
    """
    logMessage = Signal(str, str)  # message, level

    def __init__(self, ctx: 'AppContext', parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._setup_ui()

    @property
    @abstractmethod
    def method_id(self) -> str:
        """고유 메소드 ID"""
        pass

    @property
    @abstractmethod
    def method_name(self) -> str:
        """메소드 표시 이름"""
        pass

    @abstractmethod
    def _setup_ui(self):
        """메소드별 옵션 UI"""
        pass

    @abstractmethod
    def generate_script(self, k_filename: str) -> str:
        """display.txt 형식 스크립트 생성"""
        pass

    def validate(self) -> tuple:
        """
        입력 검증
        Returns: (is_valid, error_message)
        """
        return True, ""

    def log(self, message: str, level: str = "info"):
        """로그 메시지 출력"""
        self.logMessage.emit(message, level)
