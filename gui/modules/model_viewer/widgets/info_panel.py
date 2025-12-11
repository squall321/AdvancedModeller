"""Element Info Panel Widget

선택된 요소의 상세 정보 표시
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, List, Dict, Any


class ElementInfoPanel(QWidget):
    """Element 상세 정보 패널

    선택된 Element의:
    - Element ID
    - Part ID
    - Node IDs
    - 좌표 정보
    - 기타 속성
    """

    # 시그널
    clearSelection = Signal()  # 선택 해제 요청
    zoomToElement = Signal(int)  # Element로 줌

    def __init__(self, parent=None):
        super().__init__(parent)

        self._element_id: Optional[int] = None
        self._part_id: Optional[int] = None
        self._node_ids: List[int] = []
        self._element_info: Dict[str, Any] = {}

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 타이틀
        title = QLabel("Selection Info")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(4, 4, 4, 4)
        self._content_layout.setSpacing(8)

        # Element 기본 정보
        self._element_group = self._create_element_group()
        self._content_layout.addWidget(self._element_group)

        # Node 정보
        self._nodes_group = self._create_nodes_group()
        self._content_layout.addWidget(self._nodes_group)

        # 액션 버튼
        self._actions_group = self._create_actions_group()
        self._content_layout.addWidget(self._actions_group)

        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # 초기 상태: 선택 없음
        self._show_no_selection()

    def _create_element_group(self) -> QGroupBox:
        """Element 정보 그룹"""
        group = QGroupBox("Element")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        self._element_id_label = QLabel("ID: -")
        self._part_id_label = QLabel("Part: -")
        self._element_type_label = QLabel("Type: -")

        layout.addWidget(self._element_id_label)
        layout.addWidget(self._part_id_label)
        layout.addWidget(self._element_type_label)

        return group

    def _create_nodes_group(self) -> QGroupBox:
        """Node 정보 그룹"""
        group = QGroupBox("Nodes")
        layout = QVBoxLayout(group)
        layout.setSpacing(2)

        self._nodes_label = QLabel("Count: -")
        layout.addWidget(self._nodes_label)

        # Node ID 리스트
        self._nodes_list_widget = QWidget()
        self._nodes_list_layout = QVBoxLayout(self._nodes_list_widget)
        self._nodes_list_layout.setContentsMargins(0, 0, 0, 0)
        self._nodes_list_layout.setSpacing(1)
        layout.addWidget(self._nodes_list_widget)

        return group

    def _create_actions_group(self) -> QGroupBox:
        """액션 버튼 그룹"""
        group = QGroupBox("Actions")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # Zoom 버튼
        self._zoom_btn = QPushButton("Zoom to Element")
        self._zoom_btn.clicked.connect(self._on_zoom_clicked)
        layout.addWidget(self._zoom_btn)

        # 선택 해제 버튼
        self._clear_btn = QPushButton("Clear Selection")
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self._clear_btn)

        return group

    def set_element(self, element_id: int, part_id: int, node_ids: List[int],
                   element_type: str = "solid", additional_info: Dict[str, Any] = None):
        """Element 정보 설정

        Args:
            element_id: Element ID
            part_id: Part ID
            node_ids: Node ID 리스트
            element_type: 'shell' or 'solid'
            additional_info: 추가 정보 (좌표 등)
        """
        self._element_id = element_id
        self._part_id = part_id
        self._node_ids = node_ids
        self._element_info = additional_info or {}

        # UI 업데이트
        self._element_id_label.setText(f"ID: {element_id}")
        self._part_id_label.setText(f"Part: {part_id}")
        self._element_type_label.setText(f"Type: {element_type.upper()}")

        # Nodes
        self._nodes_label.setText(f"Count: {len(node_ids)}")

        # Node 리스트 재생성
        self._clear_nodes_list()
        for i, nid in enumerate(node_ids, 1):
            node_label = QLabel(f"  {i}. Node {nid}")
            node_label.setStyleSheet("font-family: monospace; font-size: 9pt;")
            self._nodes_list_layout.addWidget(node_label)

        # 버튼 활성화
        self._zoom_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)

        # 그룹 보이기
        self._element_group.setVisible(True)
        self._nodes_group.setVisible(True)
        self._actions_group.setVisible(True)

    def set_multiple_elements(self, count: int):
        """다중 선택 표시

        Args:
            count: 선택된 Element 개수
        """
        self._element_id_label.setText(f"Selected: {count} elements")
        self._part_id_label.setText("Multiple parts")
        self._element_type_label.setText("-")

        self._nodes_label.setText("-")
        self._clear_nodes_list()

        self._zoom_btn.setEnabled(False)
        self._clear_btn.setEnabled(True)

        self._element_group.setVisible(True)
        self._nodes_group.setVisible(False)
        self._actions_group.setVisible(True)

    def clear(self):
        """정보 클리어"""
        self._element_id = None
        self._part_id = None
        self._node_ids = []
        self._element_info = {}

        self._show_no_selection()

    def _show_no_selection(self):
        """선택 없음 표시"""
        self._element_id_label.setText("No selection")
        self._part_id_label.setText("-")
        self._element_type_label.setText("-")

        self._nodes_label.setText("-")
        self._clear_nodes_list()

        self._zoom_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)

        self._element_group.setVisible(True)
        self._nodes_group.setVisible(False)
        self._actions_group.setVisible(False)

    def _clear_nodes_list(self):
        """Node 리스트 위젯 클리어"""
        while self._nodes_list_layout.count():
            item = self._nodes_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_zoom_clicked(self):
        """Zoom 버튼 클릭"""
        if self._element_id is not None:
            self.zoomToElement.emit(self._element_id)

    def _on_clear_clicked(self):
        """Clear 버튼 클릭"""
        self.clearSelection.emit()

    def get_element_id(self) -> Optional[int]:
        """현재 표시 중인 Element ID"""
        return self._element_id
