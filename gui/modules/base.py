"""Base module class for all modules"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from abc import abstractmethod
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gui.app_context import AppContext


class BaseModule(QWidget):
    """
    모든 모듈의 부모 클래스

    새 모듈 추가 시:
    1. 이 클래스 상속
    2. module_id property 구현
    3. _setup_ui() 구현

    선택 구현:
    - on_activate() - 모듈 활성화 시
    - on_deactivate() - 모듈 비활성화 시
    - get_actions() - 모듈별 액션 버튼
    """

    # 시그널 - Shell에서 연결
    statusMessage = Signal(str)           # 상태바 메시지
    logMessage = Signal(str, str)         # 로그 (message, level)

    def __init__(self, ctx: 'AppContext', parent=None):
        super().__init__(parent)
        self.ctx = ctx  # 공유 컨텍스트
        self._setup_ui()

    @property
    @abstractmethod
    def module_id(self) -> str:
        """고유 모듈 ID (예: 'advanced_laminate')"""
        pass

    @abstractmethod
    def _setup_ui(self):
        """UI 초기화 - 서브클래스에서 구현"""
        pass

    def on_activate(self):
        """모듈이 화면에 표시될 때 호출"""
        pass

    def on_deactivate(self):
        """다른 모듈로 전환될 때 호출"""
        pass

    def get_actions(self) -> List[Dict[str, Any]]:
        """
        모듈별 액션 버튼 정의
        반환 예시: [
            {'id': 'generate', 'name': '생성', 'icon': 'fa5s.file-code', 'primary': True},
            {'id': 'preview', 'name': '미리보기', 'icon': 'fa5s.eye'},
        ]
        """
        return []

    def on_action(self, action_id: str):
        """액션 버튼 클릭 시 호출"""
        pass

    def log(self, message: str, level: str = "info"):
        """로그 메시지 출력"""
        self.logMessage.emit(message, level)

    def status(self, message: str):
        """상태바 메시지 출력"""
        self.statusMessage.emit(message)
