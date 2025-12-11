"""Keyword preview widget for showing K-file format"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from typing import Any, Optional


class KeywordPreviewWidget(QWidget):
    """K-file 형식 미리보기 위젯

    선택된 키워드를 K-file 형식으로 표시합니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_category: str = ""
        self._current_item: Any = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 헤더
        header = QLabel("K-file 미리보기")
        header.setStyleSheet("padding: 4px; background: palette(alternate-base);")
        layout.addWidget(header)

        # 텍스트 에디터
        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)

        # 고정폭 폰트 사용
        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixed_font.setPointSize(10)
        self._editor.setFont(fixed_font)

        self._editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
        """)

        layout.addWidget(self._editor)

    def set_keyword(self, category: str, item: Any):
        """키워드 설정 및 미리보기 생성"""
        self._current_category = category
        self._current_item = item
        self._update_preview()

    def _update_preview(self):
        """미리보기 텍스트 생성"""
        if self._current_item is None:
            self._editor.setPlainText("$ 키워드를 선택하면 K-file 형식으로 표시됩니다")
            return

        text = self._generate_kfile_text()
        self._editor.setPlainText(text)

    def _generate_kfile_text(self) -> str:
        """K-file 형식 텍스트 생성"""
        item = self._current_item
        category = self._current_category
        lines = []

        if category == 'nodes':
            lines.append("*NODE")
            lines.append(self._format_node(item))

        elif category == 'parts':
            lines.append("*PART")
            lines.append(getattr(item, 'name', 'Part'))
            lines.append(self._format_part(item))

        elif category == 'shell':
            lines.append("*ELEMENT_SHELL")
            lines.append(self._format_shell(item))

        elif category == 'solid':
            lines.append("*ELEMENT_SOLID")
            lines.append(self._format_solid(item))

        elif category == 'materials':
            keyword = getattr(item, 'keyword_type', 'MAT_ELASTIC')
            lines.append(f"*{keyword}")
            lines.append(self._format_material(item))

        elif category == 'sections':
            keyword = getattr(item, 'keyword_type', 'SECTION_SHELL')
            lines.append(f"*{keyword}")
            lines.append(self._format_section(item))

        elif category == 'contacts':
            keyword = getattr(item, 'keyword_type', 'CONTACT_AUTOMATIC_SURFACE_TO_SURFACE')
            lines.append(f"*{keyword}")
            lines.append(self._format_contact(item))

        elif category == 'sets':
            keyword = getattr(item, 'keyword_type', 'SET_PART')
            lines.append(f"*{keyword}")
            lines.append(self._format_set(item))

        else:
            # 일반적인 키워드
            keyword = getattr(item, 'keyword_type', category.upper())
            lines.append(f"*{keyword}")
            lines.append(self._format_generic(item))

        return '\n'.join(lines)

    def _format_node(self, node) -> str:
        """노드 포맷"""
        nid = getattr(node, 'nid', 0)
        x = getattr(node, 'x', 0.0)
        y = getattr(node, 'y', 0.0)
        z = getattr(node, 'z', 0.0)
        return f"{nid:8d}{x:16.8f}{y:16.8f}{z:16.8f}"

    def _format_part(self, part) -> str:
        """파트 포맷"""
        pid = getattr(part, 'pid', 0)
        secid = getattr(part, 'secid', 0)
        mid = getattr(part, 'mid', 0)
        eosid = getattr(part, 'eosid', 0)
        hgid = getattr(part, 'hgid', 0)
        grav = getattr(part, 'grav', 0)
        adpopt = getattr(part, 'adpopt', 0)
        tmid = getattr(part, 'tmid', 0)
        return f"{pid:10d}{secid:10d}{mid:10d}{eosid:10d}{hgid:10d}{grav:10d}{adpopt:10d}{tmid:10d}"

    def _format_shell(self, elem) -> str:
        """쉘 요소 포맷"""
        eid = getattr(elem, 'eid', 0)
        pid = getattr(elem, 'pid', 0)
        # nodes 리스트에서 가져오기
        nodes = getattr(elem, 'nodes', [0, 0, 0, 0])
        n1 = nodes[0] if len(nodes) > 0 else 0
        n2 = nodes[1] if len(nodes) > 1 else 0
        n3 = nodes[2] if len(nodes) > 2 else 0
        n4 = nodes[3] if len(nodes) > 3 else 0
        return f"{eid:8d}{pid:8d}{n1:8d}{n2:8d}{n3:8d}{n4:8d}"

    def _format_solid(self, elem) -> str:
        """솔리드 요소 포맷"""
        eid = getattr(elem, 'eid', 0)
        pid = getattr(elem, 'pid', 0)
        # nodes 리스트에서 가져오기
        nodes_list = getattr(elem, 'nodes', [])
        # 8개 노드로 패딩
        nodes = list(nodes_list) + [0] * (8 - len(nodes_list))
        node_str = ''.join(f"{n:8d}" for n in nodes[:8])
        return f"{eid:8d}{pid:8d}{node_str}"

    def _format_material(self, mat) -> str:
        """재료 포맷"""
        mid = getattr(mat, 'mid', 0)
        ro = getattr(mat, 'ro', 0.0)
        e = getattr(mat, 'e', 0.0)
        pr = getattr(mat, 'pr', 0.0)
        return f"{mid:10d}{ro:10.4e}{e:10.4e}{pr:10.4f}"

    def _format_section(self, sec) -> str:
        """섹션 포맷"""
        secid = getattr(sec, 'secid', 0)
        elform = getattr(sec, 'elform', 2)
        shrf = getattr(sec, 'shrf', 1.0)
        nip = getattr(sec, 'nip', 2)
        t1 = getattr(sec, 't1', getattr(sec, 'thickness', 1.0))
        return f"{secid:10d}{elform:10d}{shrf:10.4f}{nip:10d}\n{t1:10.4f}"

    def _format_contact(self, contact) -> str:
        """접촉 포맷"""
        ssid = getattr(contact, 'ssid', 0)
        msid = getattr(contact, 'msid', 0)
        sstyp = getattr(contact, 'sstyp', 2)
        mstyp = getattr(contact, 'mstyp', 2)
        return f"{ssid:10d}{msid:10d}{sstyp:10d}{mstyp:10d}"

    def _format_set(self, s) -> str:
        """세트 포맷"""
        sid = getattr(s, 'sid', 0)
        ids = getattr(s, 'ids', [])
        lines = [f"{sid:10d}"]

        # 한 줄에 8개씩
        for i in range(0, len(ids), 8):
            chunk = ids[i:i+8]
            lines.append(''.join(f"{id_:10d}" for id_ in chunk))

        return '\n'.join(lines)

    def _format_generic(self, item) -> str:
        """일반 키워드 포맷"""
        # raw_data가 있으면 사용
        if hasattr(item, 'raw_data'):
            return str(item.raw_data)

        # 주요 속성 추출
        fields = []
        for attr in dir(item):
            if attr.startswith('_'):
                continue
            try:
                value = getattr(item, attr)
                if not callable(value) and not isinstance(value, (list, dict)):
                    fields.append(f"{attr}={value}")
            except:
                pass

        return "$ " + ", ".join(fields[:10])

    def set_range(self, category: str, items: list):
        """범위 항목들의 K-file 미리보기 생성"""
        self._current_category = category
        self._current_item = None

        if not items:
            self._editor.setPlainText("$ 항목이 없습니다")
            return

        lines = []
        max_items = 100  # 미리보기에 표시할 최대 항목 수

        if category == 'nodes':
            lines.append("*NODE")
            for item in items[:max_items]:
                lines.append(self._format_node(item))
        elif category == 'shell':
            lines.append("*ELEMENT_SHELL")
            for item in items[:max_items]:
                lines.append(self._format_shell(item))
        elif category == 'solid':
            lines.append("*ELEMENT_SOLID")
            for item in items[:max_items]:
                lines.append(self._format_solid(item))
        elif category == 'beam':
            lines.append("*ELEMENT_BEAM")
            for item in items[:max_items]:
                eid = getattr(item, 'eid', 0)
                pid = getattr(item, 'pid', 0)
                nodes_list = getattr(item, 'nodes', [])
                n1 = nodes_list[0] if len(nodes_list) > 0 else 0
                n2 = nodes_list[1] if len(nodes_list) > 1 else 0
                lines.append(f"{eid:8d}{pid:8d}{n1:8d}{n2:8d}")

        if len(items) > max_items:
            lines.append(f"$ ... 외 {len(items) - max_items:,}개 더")

        self._editor.setPlainText('\n'.join(lines))

    def clear(self):
        """미리보기 초기화"""
        self._current_category = ""
        self._current_item = None
        self._editor.setPlainText("")
