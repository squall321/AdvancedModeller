"""Element Info Widget - 선택된 요소 정보 표시"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
from typing import Optional

from ..core.mesh_data import MeshData


class ElementInfoWidget(QWidget):
    """선택된 요소의 상세 정보 표시 위젯

    - 요소 ID
    - Part ID & 이름
    - 요소 타입
    - 노드 목록
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mesh: Optional[MeshData] = None
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 그룹 박스
        group = QGroupBox("선택된 요소")
        group_layout = QVBoxLayout(group)

        # 정보 텍스트
        self._info_text = QTextEdit()
        self._info_text.setReadOnly(True)
        self._info_text.setMaximumHeight(150)
        self._info_text.setPlainText("요소를 클릭하여 선택하세요")
        group_layout.addWidget(self._info_text)

        layout.addWidget(group)

    def set_mesh(self, mesh: MeshData):
        """메쉬 데이터 설정"""
        self._mesh = mesh

    def show_element(self, elem_idx: int):
        """요소 정보 표시"""
        if not self._mesh or elem_idx < 0 or elem_idx >= len(self._mesh.elements):
            self._info_text.setPlainText("유효하지 않은 요소")
            return

        # 요소 정보 수집
        node_indices = self._mesh.elements[elem_idx]
        elem_type = self._mesh.element_type

        # Part 찾기
        part_id = None
        for pid, elem_list in self._mesh.part_elements.items():
            if elem_idx in elem_list:
                part_id = pid
                break

        part_name = self._mesh.part_names.get(part_id, "Unknown") if part_id else "Unknown"

        # 노드 좌표
        node_coords = []
        for nid in node_indices:
            coords = self._mesh.nodes[nid]
            node_coords.append(f"  Node {nid}: ({coords[0]:.3f}, {coords[1]:.3f}, {coords[2]:.3f})")

        # 정보 텍스트 생성
        info_lines = [
            "=" * 50,
            "  선택된 요소 정보",
            "=" * 50,
            "",
            f"요소 ID:     {elem_idx}",
            f"Part ID:     {part_id}",
            f"Part 이름:   {part_name}",
            f"요소 타입:   {elem_type.upper()}",
            f"노드 개수:   {len(node_indices)}",
            "",
            "노드 좌표:",
            *node_coords,
        ]

        self._info_text.setPlainText("\n".join(info_lines))

    def clear(self):
        """정보 초기화"""
        self._info_text.setPlainText("요소를 클릭하여 선택하세요")
