"""Sidebar navigation widget with hierarchical structure"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                                QLabel, QFrame, QSizePolicy)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
import qtawesome as qta
from gui.modules import ModuleRegistry


class MethodButton(QPushButton):
    """하위 메소드 버튼"""

    def __init__(self, module_id: str, method_id: str, name: str, icon: str, parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self.method_id = method_id
        self._icon_name = icon

        self.setIcon(qta.icon(icon, color='#6b7280'))
        self.setText(f"  {name}")
        self.setFixedHeight(36)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                text-align: left;
                padding-left: 32px;
                font-size: 12px;
                color: #9ca3af;
            }
            QPushButton:hover {
                background-color: #1f2937;
                color: #d1d5db;
            }
            QPushButton:checked {
                background-color: #1e3a5f;
                color: #60a5fa;
            }
        """)

    def set_active(self, active: bool):
        """활성 상태 설정"""
        self.setChecked(active)
        color = '#60a5fa' if active else '#6b7280'
        self.setIcon(qta.icon(self._icon_name, color=color))


class SidebarButton(QPushButton):
    """사이드바 모듈 버튼 (확장/축소 지원)"""

    def __init__(self, module_id: str, name: str, icon: str, has_children: bool = False, parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self._icon_name = icon
        self._has_children = has_children
        self._expanded = False

        self.setIcon(qta.icon(icon, color='#9ca3af'))
        self._update_text()
        self.setFixedHeight(44)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 12px;
                font-size: 13px;
                color: #d1d5db;
            }
            QPushButton:hover {
                background-color: #374151;
            }
            QPushButton:checked {
                background-color: #1f2937;
                color: #60a5fa;
            }
        """)

    def _update_text(self):
        """텍스트 업데이트 (확장 아이콘 포함)"""
        if self._has_children:
            arrow = "▼" if self._expanded else "▶"
            self.setText(f"  {self.property('display_name') or ''} {arrow}")
        else:
            self.setText(f"  {self.property('display_name') or ''}")

    def set_expanded(self, expanded: bool):
        """확장 상태 설정"""
        self._expanded = expanded
        self._update_text()

    def is_expanded(self) -> bool:
        return self._expanded

    def has_children(self) -> bool:
        return self._has_children

    def set_active(self, active: bool, keep_expanded: bool = False):
        """활성 상태 설정"""
        self.setChecked(active)
        color = '#60a5fa' if active else '#9ca3af'
        self.setIcon(qta.icon(self._icon_name, color=color))


class MethodContainer(QWidget):
    """메소드 버튼들을 담는 컨테이너 (애니메이션 지원)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)
        self._buttons = []

    def add_button(self, btn: MethodButton):
        self._buttons.append(btn)
        self._layout.addWidget(btn)

    def get_buttons(self):
        return self._buttons

    def clear(self):
        for btn in self._buttons:
            btn.deleteLater()
        self._buttons.clear()


class Sidebar(QWidget):
    """사이드바 네비게이션 (계층 구조 지원)"""
    moduleSelected = Signal(str)  # module_id
    methodSelected = Signal(str, str)  # module_id, method_id
    homeRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._module_buttons = {}  # module_id -> SidebarButton
        self._method_containers = {}  # module_id -> MethodContainer
        self._method_buttons = {}  # (module_id, method_id) -> MethodButton
        self._active_module = None
        self._active_method = None
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("sidebar")
        self.setStyleSheet("""
            #sidebar {
                background-color: #111827;
                border-right: 1px solid #374151;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        # 홈 버튼
        home_btn = QPushButton(qta.icon('fa5s.home', color='#9ca3af'), "  홈")
        home_btn.setFixedHeight(44)
        home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 12px;
                font-size: 13px;
                color: #d1d5db;
            }
            QPushButton:hover {
                background-color: #374151;
            }
        """)
        home_btn.clicked.connect(self.homeRequested.emit)
        layout.addWidget(home_btn)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #374151;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # 모듈 버튼들 컨테이너
        self._module_container = QVBoxLayout()
        self._module_container.setSpacing(2)
        layout.addLayout(self._module_container)

        layout.addStretch()

        # 하단 버전 정보
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #4b5563; font-size: 11px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

    def populate_modules(self):
        """등록된 모듈로 버튼 생성"""
        # 기존 버튼 제거
        for btn in self._module_buttons.values():
            btn.deleteLater()
        for container in self._method_containers.values():
            container.deleteLater()
        self._module_buttons.clear()
        self._method_containers.clear()
        self._method_buttons.clear()

        # 모듈 버튼 추가
        for info in ModuleRegistry.get_all():
            has_methods = info.has_methods

            # 모듈 버튼 생성
            btn = SidebarButton(info.module_id, info.name, info.icon, has_methods)
            btn.setProperty('icon_name', info.icon)
            btn.setProperty('display_name', info.name)
            btn._update_text()
            btn.clicked.connect(lambda checked, mid=info.module_id: self._on_module_clicked(mid))
            self._module_container.addWidget(btn)
            self._module_buttons[info.module_id] = btn

            # 메소드가 있으면 컨테이너 생성
            if has_methods:
                container = MethodContainer()
                container.setVisible(False)

                for method_info in info.methods:
                    method_btn = MethodButton(
                        info.module_id,
                        method_info.method_id,
                        method_info.name,
                        method_info.icon
                    )
                    method_btn.clicked.connect(
                        lambda checked, mid=info.module_id, meth=method_info.method_id:
                        self._on_method_clicked(mid, meth)
                    )
                    container.add_button(method_btn)
                    self._method_buttons[(info.module_id, method_info.method_id)] = method_btn

                self._module_container.addWidget(container)
                self._method_containers[info.module_id] = container

    def _on_module_clicked(self, module_id: str):
        """모듈 버튼 클릭 처리"""
        btn = self._module_buttons.get(module_id)
        if not btn:
            return

        if btn.has_children():
            # 하위 항목이 있으면 확장/축소 토글
            new_expanded = not btn.is_expanded()
            btn.set_expanded(new_expanded)

            container = self._method_containers.get(module_id)
            if container:
                container.setVisible(new_expanded)

            # 확장만 하고 모듈 자체는 선택하지 않음
            # 모듈을 활성화하려면 메소드를 선택해야 함
            btn.setChecked(self._active_module == module_id)
        else:
            # 하위 항목이 없으면 바로 모듈 선택
            self.moduleSelected.emit(module_id)

    def _on_method_clicked(self, module_id: str, method_id: str):
        """메소드 버튼 클릭 처리"""
        self.methodSelected.emit(module_id, method_id)

    def set_active(self, module_id: str, method_id: str = None):
        """활성 모듈/메소드 설정"""
        self._active_module = module_id
        self._active_method = method_id

        # 모든 버튼 비활성화
        for mid, btn in self._module_buttons.items():
            is_active = mid == module_id
            btn.set_active(is_active)

            # 활성 모듈이면 자동 확장
            if is_active and btn.has_children():
                btn.set_expanded(True)
                container = self._method_containers.get(mid)
                if container:
                    container.setVisible(True)

        # 메소드 버튼 활성화
        for (mid, meth), btn in self._method_buttons.items():
            is_active = mid == module_id and meth == method_id
            btn.set_active(is_active)

    def collapse_all(self):
        """모든 모듈 축소"""
        for module_id, btn in self._module_buttons.items():
            if btn.has_children():
                btn.set_expanded(False)
                container = self._method_containers.get(module_id)
                if container:
                    container.setVisible(False)
