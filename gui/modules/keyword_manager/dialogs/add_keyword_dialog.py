"""Add Keyword Dialog

새로운 키워드 항목을 추가하기 위한 다이얼로그입니다.
카테고리 선택 및 필드 값 입력을 지원합니다.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QDialogButtonBox, QScrollArea,
    QWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from typing import Any, Optional, Dict, List

try:
    import qtawesome as qta
except ImportError:
    qta = None


# 카테고리별 필드 정의
CATEGORY_FIELDS = {
    'nodes': {
        'name': 'Node',
        'id_field': 'nid',
        'fields': [
            {'name': 'nid', 'label': 'Node ID', 'type': 'int', 'required': True},
            {'name': 'x', 'label': 'X', 'type': 'float', 'default': 0.0},
            {'name': 'y', 'label': 'Y', 'type': 'float', 'default': 0.0},
            {'name': 'z', 'label': 'Z', 'type': 'float', 'default': 0.0},
            {'name': 'tc', 'label': 'TC', 'type': 'int', 'default': 0},
            {'name': 'rc', 'label': 'RC', 'type': 'int', 'default': 0},
        ]
    },
    'shell': {
        'name': 'Shell Element',
        'id_field': 'eid',
        'fields': [
            {'name': 'eid', 'label': 'Element ID', 'type': 'int', 'required': True},
            {'name': 'pid', 'label': 'Part ID', 'type': 'int', 'default': 0},
            {'name': 'n1', 'label': 'Node 1', 'type': 'int', 'default': 0},
            {'name': 'n2', 'label': 'Node 2', 'type': 'int', 'default': 0},
            {'name': 'n3', 'label': 'Node 3', 'type': 'int', 'default': 0},
            {'name': 'n4', 'label': 'Node 4', 'type': 'int', 'default': 0},
        ]
    },
    'solid': {
        'name': 'Solid Element',
        'id_field': 'eid',
        'fields': [
            {'name': 'eid', 'label': 'Element ID', 'type': 'int', 'required': True},
            {'name': 'pid', 'label': 'Part ID', 'type': 'int', 'default': 0},
            {'name': 'n1', 'label': 'Node 1', 'type': 'int', 'default': 0},
            {'name': 'n2', 'label': 'Node 2', 'type': 'int', 'default': 0},
            {'name': 'n3', 'label': 'Node 3', 'type': 'int', 'default': 0},
            {'name': 'n4', 'label': 'Node 4', 'type': 'int', 'default': 0},
            {'name': 'n5', 'label': 'Node 5', 'type': 'int', 'default': 0},
            {'name': 'n6', 'label': 'Node 6', 'type': 'int', 'default': 0},
            {'name': 'n7', 'label': 'Node 7', 'type': 'int', 'default': 0},
            {'name': 'n8', 'label': 'Node 8', 'type': 'int', 'default': 0},
        ]
    },
    'beam': {
        'name': 'Beam Element',
        'id_field': 'eid',
        'fields': [
            {'name': 'eid', 'label': 'Element ID', 'type': 'int', 'required': True},
            {'name': 'pid', 'label': 'Part ID', 'type': 'int', 'default': 0},
            {'name': 'n1', 'label': 'Node 1', 'type': 'int', 'default': 0},
            {'name': 'n2', 'label': 'Node 2', 'type': 'int', 'default': 0},
            {'name': 'n3', 'label': 'Node 3 (orientation)', 'type': 'int', 'default': 0},
        ]
    },
    'parts': {
        'name': 'Part',
        'id_field': 'pid',
        'fields': [
            {'name': 'pid', 'label': 'Part ID', 'type': 'int', 'required': True},
            {'name': 'name', 'label': 'Name', 'type': 'str', 'default': ''},
            {'name': 'secid', 'label': 'Section ID', 'type': 'int', 'default': 0},
            {'name': 'mid', 'label': 'Material ID', 'type': 'int', 'default': 0},
            {'name': 'eosid', 'label': 'EOS ID', 'type': 'int', 'default': 0},
            {'name': 'hgid', 'label': 'Hourglass ID', 'type': 'int', 'default': 0},
        ]
    },
    'materials': {
        'name': 'Material',
        'id_field': 'mid',
        'fields': [
            {'name': 'mid', 'label': 'Material ID', 'type': 'int', 'required': True},
            {'name': 'name', 'label': 'Name', 'type': 'str', 'default': ''},
            {'name': 'ro', 'label': 'Density (RO)', 'type': 'float', 'default': 0.0},
            {'name': 'e', 'label': "Young's Modulus (E)", 'type': 'float', 'default': 0.0},
            {'name': 'pr', 'label': "Poisson's Ratio (PR)", 'type': 'float', 'default': 0.0},
        ]
    },
    'sections': {
        'name': 'Section',
        'id_field': 'secid',
        'fields': [
            {'name': 'secid', 'label': 'Section ID', 'type': 'int', 'required': True},
            {'name': 'elform', 'label': 'Element Formulation', 'type': 'int', 'default': 0},
            {'name': 't1', 'label': 'Thickness 1', 'type': 'float', 'default': 0.0},
            {'name': 't2', 'label': 'Thickness 2', 'type': 'float', 'default': 0.0},
            {'name': 't3', 'label': 'Thickness 3', 'type': 'float', 'default': 0.0},
            {'name': 't4', 'label': 'Thickness 4', 'type': 'float', 'default': 0.0},
        ]
    },
    'sets': {
        'name': 'Set',
        'id_field': 'sid',
        'fields': [
            {'name': 'sid', 'label': 'Set ID', 'type': 'int', 'required': True},
            {'name': 'name', 'label': 'Name', 'type': 'str', 'default': ''},
        ]
    },
}


class AddKeywordDialog(QDialog):
    """새 키워드 항목 추가 다이얼로그"""

    # 시그널: 항목 추가 완료 (category, item_data)
    itemAdded = Signal(str, dict)

    def __init__(self, parent=None, category: str = None, next_id: int = 1):
        """
        Args:
            parent: 부모 위젯
            category: 초기 카테고리 (None이면 선택 가능)
            next_id: 다음 ID 값 제안
        """
        super().__init__(parent)
        self._category = category
        self._next_id = next_id
        self._field_widgets: Dict[str, QWidget] = {}

        self.setWindowTitle("새 키워드 추가")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        self._setup_ui()

        # 초기 카테고리가 지정되어 있으면 설정
        if category and category in CATEGORY_FIELDS:
            idx = self._category_combo.findData(category)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)
            self._category_combo.setEnabled(False)

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)

        # 카테고리 선택
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("카테고리:"))

        self._category_combo = QComboBox()
        for cat_id, cat_info in CATEGORY_FIELDS.items():
            self._category_combo.addItem(cat_info['name'], cat_id)
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        category_layout.addWidget(self._category_combo, 1)

        layout.addLayout(category_layout)

        # 필드 입력 영역 (스크롤 가능)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        self._fields_widget = QWidget()
        self._fields_layout = QFormLayout(self._fields_widget)
        self._fields_layout.setLabelAlignment(Qt.AlignRight)

        scroll.setWidget(self._fields_widget)
        layout.addWidget(scroll, 1)

        # 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # 초기 필드 구성
        self._on_category_changed(0)

    def _on_category_changed(self, index: int):
        """카테고리 변경 시 필드 업데이트"""
        # 기존 필드 제거
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._field_widgets.clear()

        # 새 카테고리 필드 생성
        category = self._category_combo.currentData()
        if category not in CATEGORY_FIELDS:
            return

        cat_info = CATEGORY_FIELDS[category]
        id_field = cat_info['id_field']

        for field in cat_info['fields']:
            name = field['name']
            label = field['label']
            ftype = field['type']
            required = field.get('required', False)
            default = field.get('default', 0 if ftype == 'int' else (0.0 if ftype == 'float' else ''))

            # 라벨
            label_text = f"{label}:" if not required else f"{label} *:"

            # 입력 위젯 생성
            if ftype == 'int':
                widget = QSpinBox()
                widget.setRange(-999999999, 999999999)
                # ID 필드의 경우 next_id 사용
                if name == id_field:
                    widget.setValue(self._next_id)
                else:
                    widget.setValue(default)
            elif ftype == 'float':
                widget = QDoubleSpinBox()
                widget.setRange(-1e20, 1e20)
                widget.setDecimals(8)
                widget.setValue(default)
            else:  # str
                widget = QLineEdit()
                widget.setText(str(default))

            self._field_widgets[name] = widget
            self._fields_layout.addRow(label_text, widget)

    def _on_accept(self):
        """확인 버튼 클릭"""
        category = self._category_combo.currentData()
        if category not in CATEGORY_FIELDS:
            return

        cat_info = CATEGORY_FIELDS[category]

        # 필수 필드 검증
        for field in cat_info['fields']:
            if field.get('required', False):
                name = field['name']
                widget = self._field_widgets.get(name)
                if widget:
                    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                        if widget.value() <= 0:
                            QMessageBox.warning(
                                self,
                                "입력 오류",
                                f"{field['label']}은(는) 필수 항목입니다."
                            )
                            widget.setFocus()
                            return
                    elif isinstance(widget, QLineEdit):
                        if not widget.text().strip():
                            QMessageBox.warning(
                                self,
                                "입력 오류",
                                f"{field['label']}은(는) 필수 항목입니다."
                            )
                            widget.setFocus()
                            return

        # 데이터 수집
        data = {}
        for field in cat_info['fields']:
            name = field['name']
            widget = self._field_widgets.get(name)
            if widget:
                if isinstance(widget, QSpinBox):
                    data[name] = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    data[name] = widget.value()
                elif isinstance(widget, QLineEdit):
                    data[name] = widget.text()

        # 시그널 발행 및 다이얼로그 종료
        self.itemAdded.emit(category, data)
        self.accept()

    def get_result(self) -> Optional[tuple]:
        """결과 반환 (category, data) 또는 None"""
        if self.result() == QDialog.Accepted:
            category = self._category_combo.currentData()
            data = {}
            for name, widget in self._field_widgets.items():
                if isinstance(widget, QSpinBox):
                    data[name] = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    data[name] = widget.value()
                elif isinstance(widget, QLineEdit):
                    data[name] = widget.text()
            return (category, data)
        return None
