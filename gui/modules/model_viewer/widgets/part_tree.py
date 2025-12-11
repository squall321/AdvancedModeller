"""Part 목록 트리 위젯

Part별 표시/숨기기 컨트롤
"""
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from typing import Dict, Set

try:
    import qtawesome as qta
except ImportError:
    qta = None


class PartTreeWidget(QWidget):
    """Part 목록 및 가시성 제어 위젯"""

    # 시그널
    visibilityChanged = Signal(set)  # visible_part_ids

    def __init__(self, parent=None):
        super().__init__(parent)
        self._part_items: Dict[int, QTreeWidgetItem] = {}
        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self._all_btn = QPushButton("전체 선택")
        self._all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(self._all_btn)

        self._none_btn = QPushButton("전체 해제")
        self._none_btn.clicked.connect(self._select_none)
        btn_layout.addWidget(self._none_btn)

        layout.addLayout(btn_layout)

        # 트리
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Part", "Elements"])
        self._tree.setColumnWidth(0, 200)
        self._tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._tree)

    def set_parts(self, part_names: Dict[int, str], part_element_counts: Dict[int, int]):
        """Part 목록 설정

        Args:
            part_names: {part_id: part_name}
            part_element_counts: {part_id: element_count}
        """
        self._tree.blockSignals(True)  # 시그널 일시 차단
        self._tree.clear()
        self._part_items.clear()

        for part_id in sorted(part_names.keys()):
            name = part_names[part_id]
            count = part_element_counts.get(part_id, 0)

            item = QTreeWidgetItem([name, str(count)])
            item.setData(0, Qt.UserRole, part_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)  # 기본적으로 모두 선택

            if qta:
                item.setIcon(0, qta.icon('fa5s.cube'))

            self._tree.addTopLevelItem(item)
            self._part_items[part_id] = item

        self._tree.blockSignals(False)
        self._emit_visibility_changed()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """아이템 체크 상태 변경"""
        if column == 0:
            self._emit_visibility_changed()

    def _emit_visibility_changed(self):
        """가시성 변경 시그널 발생"""
        visible_parts = set()
        for part_id, item in self._part_items.items():
            if item.checkState(0) == Qt.Checked:
                visible_parts.add(part_id)

        self.visibilityChanged.emit(visible_parts)

    def _select_all(self):
        """모두 선택"""
        self._tree.blockSignals(True)
        for item in self._part_items.values():
            item.setCheckState(0, Qt.Checked)
        self._tree.blockSignals(False)
        self._emit_visibility_changed()

    def _select_none(self):
        """모두 해제"""
        self._tree.blockSignals(True)
        for item in self._part_items.values():
            item.setCheckState(0, Qt.Unchecked)
        self._tree.blockSignals(False)
        self._emit_visibility_changed()

    def get_visible_parts(self) -> Set[int]:
        """현재 표시 중인 Part ID 반환"""
        visible = set()
        for part_id, item in self._part_items.items():
            if item.checkState(0) == Qt.Checked:
                visible.add(part_id)
        return visible
