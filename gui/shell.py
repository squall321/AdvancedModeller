"""App shell - main container with sidebar and content"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QStackedWidget, QStatusBar,
                                QMenuBar, QMenu, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction
from typing import Dict, Optional

from gui.app_context import AppContext
from gui.sidebar import Sidebar
from gui.home_screen import HomeScreen
from gui.widgets.log_viewer import LogViewerWidget
from gui.modules import ModuleRegistry, load_modules
from gui.modules.base import BaseModule
from gui.styles import DARK_STYLE


class AppShell(QMainWindow):
    """메인 앱 컨테이너"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KooMesh Modeller")
        self.setMinimumSize(1600, 950)

        self.ctx = AppContext()
        self._active_module: Optional[BaseModule] = None
        self._module_cache: Dict[str, BaseModule] = {}

        # 모듈 로드
        load_modules()

        self._setup_ui()
        self._setup_menubar()
        self._setup_statusbar()
        self._connect_signals()

        # 스타일 적용
        self.setStyleSheet(DARK_STYLE)

        # 모듈 버튼 생성
        self.sidebar.populate_modules()
        self.home_screen.populate_modules()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 사이드바 (홈에서는 숨김)
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setVisible(False)
        main_layout.addWidget(self.sidebar)

        # 컨텐츠 영역
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 스플리터로 컨텐츠/로그 분리
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 모듈 스택
        self.content_stack = QStackedWidget()
        splitter.addWidget(self.content_stack)

        # 하단 로그 (공용)
        self.log_viewer = LogViewerWidget()
        self.log_viewer.setMinimumHeight(100)
        self.log_viewer.setMaximumHeight(200)
        splitter.addWidget(self.log_viewer)

        splitter.setSizes([700, 150])
        content_layout.addWidget(splitter)

        main_layout.addWidget(content_container, 1)

        # 홈 화면 추가
        self.home_screen = HomeScreen()
        self.content_stack.addWidget(self.home_screen)

    def _setup_menubar(self):
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        home_action = QAction("홈으로", self)
        home_action.setShortcut("Ctrl+H")
        home_action.triggered.connect(self._show_home)
        file_menu.addAction(home_action)

        file_menu.addSeparator()

        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 모듈 메뉴
        module_menu = menubar.addMenu("모듈(&M)")
        for info in ModuleRegistry.get_all():
            action = QAction(info.name, self)
            action.triggered.connect(lambda checked, mid=info.module_id: self._switch_to_module(mid))
            module_menu.addAction(action)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")

        about_action = QAction("정보(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("준비")

    def _connect_signals(self):
        self.sidebar.moduleSelected.connect(self._switch_to_module)
        self.sidebar.methodSelected.connect(self._switch_to_method)
        self.sidebar.homeRequested.connect(self._show_home)
        self.home_screen.moduleSelected.connect(self._switch_to_module)

    @Slot(str)
    def _switch_to_module(self, module_id: str):
        """모듈 전환"""
        # 현재 모듈 비활성화
        if self._active_module:
            self._active_module.on_deactivate()

        # 캐시에 없으면 생성
        if module_id not in self._module_cache:
            info = ModuleRegistry.get(module_id)
            if not info:
                self.log_viewer.append(f"모듈을 찾을 수 없음: {module_id}", "error")
                return

            module = info.module_class(self.ctx)
            module.logMessage.connect(self.log_viewer.append)
            module.statusMessage.connect(self.statusbar.showMessage)
            self._module_cache[module_id] = module
            self.content_stack.addWidget(module)

        # 모듈 활성화
        self._active_module = self._module_cache[module_id]
        self._active_module.on_activate()
        self.content_stack.setCurrentWidget(self._active_module)

        # 사이드바 표시 및 활성 상태 업데이트
        self.sidebar.setVisible(True)
        self.sidebar.set_active(module_id)

        info = ModuleRegistry.get(module_id)
        self.statusbar.showMessage(f"{info.name} 모듈 활성화")
        self.log_viewer.append(f"{info.name} 모듈로 전환", "info")

    @Slot(str, str)
    def _switch_to_method(self, module_id: str, method_id: str):
        """메소드 전환 (모듈 활성화 후 메소드 선택)"""
        # 현재 모듈 비활성화
        if self._active_module:
            self._active_module.on_deactivate()

        # 캐시에 없으면 생성
        if module_id not in self._module_cache:
            info = ModuleRegistry.get(module_id)
            if not info:
                self.log_viewer.append(f"모듈을 찾을 수 없음: {module_id}", "error")
                return

            module = info.module_class(self.ctx)
            module.logMessage.connect(self.log_viewer.append)
            module.statusMessage.connect(self.statusbar.showMessage)
            self._module_cache[module_id] = module
            self.content_stack.addWidget(module)

        # 모듈 활성화
        self._active_module = self._module_cache[module_id]
        self._active_module.on_activate()

        # 메소드 선택 (모듈이 지원하면)
        if hasattr(self._active_module, 'select_method'):
            self._active_module.select_method(method_id)

        self.content_stack.setCurrentWidget(self._active_module)

        # 사이드바 표시 및 활성 상태 업데이트
        self.sidebar.setVisible(True)
        self.sidebar.set_active(module_id, method_id)

        info = ModuleRegistry.get(module_id)
        # 메소드 이름 찾기
        method_name = method_id
        for m in info.methods:
            if m.method_id == method_id:
                method_name = m.name
                break

        self.statusbar.showMessage(f"{info.name} - {method_name}")
        self.log_viewer.append(f"{info.name} - {method_name} 선택", "info")

    @Slot()
    def _show_home(self):
        """홈 화면으로 이동"""
        if self._active_module:
            self._active_module.on_deactivate()
            self._active_module = None

        self.sidebar.setVisible(False)
        self.content_stack.setCurrentWidget(self.home_screen)
        self.statusbar.showMessage("홈")
        self.log_viewer.append("홈 화면으로 이동", "info")

    def _show_about(self):
        """정보 다이얼로그"""
        QMessageBox.about(
            self,
            "KooMesh Modeller 정보",
            "<h3>KooMesh Modeller</h3>"
            "<p>Version 1.0.0</p>"
            "<p>LS-DYNA 모델 자동화 도구</p>"
            "<p>PySide6 기반 (LGPL v3)</p>"
        )
