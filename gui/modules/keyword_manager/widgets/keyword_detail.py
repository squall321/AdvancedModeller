"""Keyword detail panel for displaying keyword properties"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QScrollArea, QFrame, QGroupBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from typing import Any, Dict, Optional

try:
    import qtawesome as qta
except ImportError:
    qta = None


class KeywordDetailWidget(QWidget):
    """키워드 상세 정보 패널

    선택된 키워드의 모든 속성을 표시합니다.
    """

    keywordModified = Signal(str, object)  # (category, modified_item)

    # 필드 표시 순서 (우선순위 높은 것부터)
    PRIORITY_FIELDS = [
        'nid', 'eid', 'pid', 'mid', 'sid', 'secid',
        'name', 'title', 'keyword_type',
        'x', 'y', 'z',
        'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8',
    ]

    # 숨길 필드
    HIDDEN_FIELDS = ['raw_data', 'raw_lines', '_']

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_category: str = ""
        self._current_item: Any = None
        self._field_widgets: Dict[str, QLineEdit] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 헤더
        self._header = QLabel("키워드를 선택하세요")
        self._header.setFont(QFont("", 12, QFont.Bold))
        self._header.setStyleSheet("""
            padding: 10px;
            background: #2d5a7b;
            color: #ffffff;
            border-bottom: 2px solid #1a3a4f;
        """)
        layout.addWidget(self._header)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: #2b2b2b;")

        # 내용 위젯
        self._content = QWidget()
        self._content.setStyleSheet("background: #2b2b2b;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(12)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        layout.addWidget(scroll)

    def set_keyword(self, category: str, item: Any):
        """키워드 설정 및 표시"""
        self._current_category = category
        self._current_item = item
        self._field_widgets.clear()
        self._update_display()

    def _update_display(self):
        """디스플레이 갱신"""
        # 기존 내용 제거
        while self._content_layout.count() > 1:
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if self._current_item is None:
            self._header.setText("키워드를 선택하세요")
            return

        # 헤더 업데이트
        header_text = self._get_header_text()
        self._header.setText(header_text)

        # 필드 추출
        fields = self._extract_fields(self._current_item)

        # 그룹박스 스타일
        group_style = """
            QGroupBox {
                font-weight: bold;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
                background: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #7fbadc;
            }
        """

        # 입력 필드 스타일
        edit_style = """
            QLineEdit {
                background: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QLineEdit:read-only {
                background: #3c3c3c;
                color: #b0b0b0;
            }
        """

        # 기본 정보 그룹
        basic_group = QGroupBox("기본 정보")
        basic_group.setStyleSheet(group_style)
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(6)
        basic_layout.setContentsMargins(10, 16, 10, 10)

        # 추가 정보 그룹
        extra_group = QGroupBox("상세 정보")
        extra_group.setStyleSheet(group_style)
        extra_layout = QFormLayout(extra_group)
        extra_layout.setSpacing(6)
        extra_layout.setContentsMargins(10, 16, 10, 10)

        # 필드 정렬 (우선순위 순)
        sorted_fields = self._sort_fields(fields)

        basic_count = 0
        for name, value in sorted_fields:
            label_widget = QLabel(f"{self._format_field_name(name)}:")
            label_widget.setStyleSheet("color: #a0a0a0; font-weight: normal;")

            value_str = self._format_value(value)
            edit = QLineEdit(value_str)
            edit.setReadOnly(True)
            edit.setStyleSheet(edit_style)
            self._field_widgets[name] = edit

            # 처음 8개는 기본 정보
            if basic_count < 8:
                basic_layout.addRow(label_widget, edit)
                basic_count += 1
            else:
                extra_layout.addRow(label_widget, edit)

        self._content_layout.insertWidget(0, basic_group)
        if extra_layout.rowCount() > 0:
            self._content_layout.insertWidget(1, extra_group)

    def _get_header_text(self) -> str:
        """헤더 텍스트 생성"""
        if not self._current_item:
            return ""

        category = self._current_category

        if category == 'nodes':
            nid = getattr(self._current_item, 'nid', '?')
            return f"*NODE #{nid}"
        elif category == 'parts':
            pid = getattr(self._current_item, 'pid', '?')
            name = getattr(self._current_item, 'name', '')
            return f"*PART #{pid}: {name}"
        elif category in ('shell', 'solid', 'beam'):
            eid = getattr(self._current_item, 'eid', '?')
            return f"*ELEMENT_{category.upper()} #{eid}"
        elif category == 'materials':
            mid = getattr(self._current_item, 'mid', '?')
            keyword = getattr(self._current_item, 'keyword_type', 'MAT')
            return f"*{keyword} #{mid}"
        elif category == 'sections':
            sid = getattr(self._current_item, 'secid', '?')
            keyword = getattr(self._current_item, 'keyword_type', 'SECTION')
            return f"*{keyword} #{sid}"
        elif category == 'contacts':
            keyword = getattr(self._current_item, 'keyword_type', 'CONTACT')
            return f"*{keyword}"
        elif category == 'sets':
            sid = getattr(self._current_item, 'sid', '?')
            keyword = getattr(self._current_item, 'keyword_type', 'SET')
            return f"*{keyword} #{sid}"
        else:
            keyword = getattr(self._current_item, 'keyword_type', category.upper())
            return f"*{keyword}"

    def _extract_fields(self, item: Any) -> Dict[str, Any]:
        """객체에서 필드 추출"""
        fields = {}
        for attr in dir(item):
            # 숨길 필드 스킵
            if attr.startswith('_'):
                continue
            if any(h in attr for h in self.HIDDEN_FIELDS):
                continue

            try:
                value = getattr(item, attr)
                if callable(value):
                    continue

                # 요소의 nodes 리스트를 n1~n8로 분리
                if attr == 'nodes' and isinstance(value, (list, tuple)):
                    for i, node_id in enumerate(value, 1):
                        fields[f'n{i}'] = node_id
                    continue

                fields[attr] = value
            except:
                pass

        return fields

    def _sort_fields(self, fields: Dict[str, Any]) -> list:
        """필드 정렬 (우선순위 순)"""
        result = []

        # 우선순위 필드 먼저
        for pf in self.PRIORITY_FIELDS:
            if pf in fields:
                result.append((pf, fields[pf]))

        # 나머지 필드 알파벳순
        for name in sorted(fields.keys()):
            if name not in self.PRIORITY_FIELDS:
                result.append((name, fields[name]))

        return result

    def _format_field_name(self, name: str) -> str:
        """필드명 포맷"""
        # 약어 대문자화
        upper_names = {'nid', 'eid', 'pid', 'mid', 'sid', 'secid', 'id', 'ssid', 'msid'}
        if name.lower() in upper_names:
            return name.upper()

        # 언더스코어를 공백으로
        return name.replace('_', ' ').title()

    def _format_value(self, value: Any) -> str:
        """값 포맷"""
        if value is None:
            return "-"
        elif isinstance(value, float):
            if abs(value) < 1e-10:
                return "0"
            elif abs(value) > 1e6 or abs(value) < 1e-4:
                return f"{value:.6e}"
            else:
                return f"{value:.6g}"
        elif isinstance(value, (list, tuple)):
            if len(value) > 10:
                return f"[{len(value)} items]"
            return str(value)
        else:
            return str(value)

    def clear(self):
        """패널 초기화"""
        self._current_category = ""
        self._current_item = None
        self._field_widgets.clear()
        self._update_display()

    def get_current_item(self) -> Optional[Any]:
        """현재 선택된 아이템"""
        return self._current_item
