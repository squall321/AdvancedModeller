"""Home screen with module cards"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QPushButton, QGridLayout, QFrame,
                                QSizePolicy)
from PySide6.QtCore import Signal, Qt
import qtawesome as qta
from gui.modules import ModuleRegistry


class ModuleCard(QFrame):
    """모듈 선택 카드"""
    clicked = Signal(str)  # module_id

    def __init__(self, module_id: str, name: str, description: str, icon: str, parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self._setup_ui(name, description, icon)

    def _setup_ui(self, name: str, description: str, icon: str):
        self.setObjectName("moduleCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(280, 160)
        self.setStyleSheet("""
            #moduleCard {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 12px;
            }
            #moduleCard:hover {
                border-color: #60a5fa;
                background-color: #1e3a5f;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 아이콘
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon, color='#60a5fa').pixmap(40, 40))
        layout.addWidget(icon_label)

        # 제목
        title = QLabel(name)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f3f4f6;")
        layout.addWidget(title)

        # 설명
        desc = QLabel(description)
        desc.setStyleSheet("font-size: 12px; color: #9ca3af;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self.module_id)


class HomeScreen(QWidget):
    """홈 화면 - 모듈 선택"""
    moduleSelected = Signal(str)  # module_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # 헤더
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("KooMesh Modeller")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #f3f4f6;")
        header_layout.addWidget(title)

        subtitle = QLabel("자동화 모듈을 선택하세요")
        subtitle.setStyleSheet("font-size: 14px; color: #9ca3af;")
        header_layout.addWidget(subtitle)

        layout.addLayout(header_layout)

        # 카드 그리드
        self.card_grid = QHBoxLayout()
        self.card_grid.setSpacing(20)
        self.card_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(self.card_grid)

        layout.addStretch()

        # 하단 정보
        footer = QLabel("LS-DYNA 모델 자동화 도구")
        footer.setStyleSheet("font-size: 12px; color: #6b7280;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

    def populate_modules(self):
        """등록된 모듈로 카드 생성"""
        # 기존 카드 제거
        while self.card_grid.count():
            item = self.card_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 모듈 카드 추가
        for info in ModuleRegistry.get_all():
            card = ModuleCard(
                info.module_id,
                info.name,
                info.description,
                info.icon
            )
            card.clicked.connect(self.moduleSelected.emit)
            self.card_grid.addWidget(card)
