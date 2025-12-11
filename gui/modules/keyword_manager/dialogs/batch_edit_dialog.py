"""Batch Edit Dialog

여러 키워드 항목을 일괄 수정하기 위한 다이얼로그입니다.
선택된 항목들의 특정 필드를 동일한 값으로 변경하거나
수식을 적용하여 값을 변경할 수 있습니다.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QDialogButtonBox, QCheckBox,
    QWidget, QMessageBox, QRadioButton, QButtonGroup, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from typing import Any, Optional, Dict, List

try:
    import qtawesome as qta
except ImportError:
    qta = None


# 카테고리별 수정 가능한 필드 정의
EDITABLE_FIELDS = {
    'nodes': [
        {'name': 'x', 'label': 'X 좌표', 'type': 'float'},
        {'name': 'y', 'label': 'Y 좌표', 'type': 'float'},
        {'name': 'z', 'label': 'Z 좌표', 'type': 'float'},
        {'name': 'tc', 'label': 'TC', 'type': 'int'},
        {'name': 'rc', 'label': 'RC', 'type': 'int'},
    ],
    'shell': [
        {'name': 'pid', 'label': 'Part ID', 'type': 'int'},
    ],
    'solid': [
        {'name': 'pid', 'label': 'Part ID', 'type': 'int'},
    ],
    'beam': [
        {'name': 'pid', 'label': 'Part ID', 'type': 'int'},
    ],
    'parts': [
        {'name': 'secid', 'label': 'Section ID', 'type': 'int'},
        {'name': 'mid', 'label': 'Material ID', 'type': 'int'},
        {'name': 'eosid', 'label': 'EOS ID', 'type': 'int'},
        {'name': 'hgid', 'label': 'Hourglass ID', 'type': 'int'},
    ],
}


class BatchEditDialog(QDialog):
    """다중 항목 일괄 수정 다이얼로그"""

    # 시그널: 일괄 수정 완료 (field_name, edit_mode, value/expression)
    batchEditApplied = Signal(str, str, object)

    def __init__(self, parent=None, category: str = 'nodes', items: List[Any] = None):
        """
        Args:
            parent: 부모 위젯
            category: 카테고리 ID
            items: 수정할 항목 리스트
        """
        super().__init__(parent)
        self._category = category
        self._items = items or []
        self._result_data = None

        self.setWindowTitle(f"일괄 수정 - {category}")
        self.setMinimumWidth(450)
        self.setMinimumHeight(350)

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)

        # 선택된 항목 정보
        info_group = QGroupBox("선택된 항목")
        info_layout = QVBoxLayout(info_group)

        self._info_label = QLabel(f"{len(self._items)}개 항목 선택됨")
        self._info_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self._info_label)

        layout.addWidget(info_group)

        # 필드 선택
        field_group = QGroupBox("수정할 필드")
        field_layout = QFormLayout(field_group)

        self._field_combo = QComboBox()
        fields = EDITABLE_FIELDS.get(self._category, [])
        for field in fields:
            self._field_combo.addItem(field['label'], field['name'])
        self._field_combo.currentIndexChanged.connect(self._on_field_changed)
        field_layout.addRow("필드:", self._field_combo)

        layout.addWidget(field_group)

        # 수정 모드 선택
        mode_group = QGroupBox("수정 방법")
        mode_layout = QVBoxLayout(mode_group)

        self._mode_group = QButtonGroup(self)

        # 모드 1: 고정값으로 설정
        self._mode_set = QRadioButton("고정값으로 설정")
        self._mode_set.setChecked(True)
        self._mode_group.addButton(self._mode_set, 0)
        mode_layout.addWidget(self._mode_set)

        set_layout = QHBoxLayout()
        set_layout.addSpacing(20)
        self._value_spin = QDoubleSpinBox()
        self._value_spin.setRange(-1e20, 1e20)
        self._value_spin.setDecimals(8)
        set_layout.addWidget(QLabel("값:"))
        set_layout.addWidget(self._value_spin, 1)
        mode_layout.addLayout(set_layout)

        # 모드 2: 값 더하기
        self._mode_add = QRadioButton("현재값에 더하기")
        self._mode_group.addButton(self._mode_add, 1)
        mode_layout.addWidget(self._mode_add)

        add_layout = QHBoxLayout()
        add_layout.addSpacing(20)
        self._add_spin = QDoubleSpinBox()
        self._add_spin.setRange(-1e20, 1e20)
        self._add_spin.setDecimals(8)
        add_layout.addWidget(QLabel("더할 값:"))
        add_layout.addWidget(self._add_spin, 1)
        mode_layout.addLayout(add_layout)

        # 모드 3: 값 곱하기
        self._mode_multiply = QRadioButton("현재값에 곱하기")
        self._mode_group.addButton(self._mode_multiply, 2)
        mode_layout.addWidget(self._mode_multiply)

        mul_layout = QHBoxLayout()
        mul_layout.addSpacing(20)
        self._mul_spin = QDoubleSpinBox()
        self._mul_spin.setRange(-1e20, 1e20)
        self._mul_spin.setDecimals(8)
        self._mul_spin.setValue(1.0)
        mul_layout.addWidget(QLabel("곱할 값:"))
        mul_layout.addWidget(self._mul_spin, 1)
        mode_layout.addLayout(mul_layout)

        # 모드 4: 수식 적용
        self._mode_expression = QRadioButton("수식 적용")
        self._mode_group.addButton(self._mode_expression, 3)
        mode_layout.addWidget(self._mode_expression)

        expr_layout = QVBoxLayout()
        expr_layout.addSpacing(5)

        expr_help = QLabel("사용 가능한 변수: v (현재값), i (인덱스), id (항목 ID)")
        expr_help.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        expr_layout.addWidget(expr_help)

        expr_input_layout = QHBoxLayout()
        expr_input_layout.addSpacing(20)
        self._expr_edit = QLineEdit()
        self._expr_edit.setPlaceholderText("예: v * 1.5 + 10")
        expr_input_layout.addWidget(QLabel("수식:"))
        expr_input_layout.addWidget(self._expr_edit, 1)
        expr_layout.addLayout(expr_input_layout)

        mode_layout.addLayout(expr_layout)

        layout.addWidget(mode_group)

        # 미리보기
        preview_group = QGroupBox("미리보기 (처음 5개)")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setMaximumHeight(100)
        self._preview_text.setStyleSheet("font-family: monospace;")
        preview_layout.addWidget(self._preview_text)

        preview_btn = QPushButton("미리보기 업데이트")
        preview_btn.clicked.connect(self._update_preview)
        preview_layout.addWidget(preview_btn)

        layout.addWidget(preview_group)

        # 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # 초기 필드 타입 설정
        self._on_field_changed(0)

    def _on_field_changed(self, index: int):
        """필드 변경 시 입력 위젯 타입 업데이트"""
        fields = EDITABLE_FIELDS.get(self._category, [])
        if index < 0 or index >= len(fields):
            return

        field = fields[index]
        ftype = field['type']

        # int 타입인 경우 소수점 비활성화
        if ftype == 'int':
            self._value_spin.setDecimals(0)
            self._add_spin.setDecimals(0)
            self._mul_spin.setDecimals(0)
        else:
            self._value_spin.setDecimals(8)
            self._add_spin.setDecimals(8)
            self._mul_spin.setDecimals(8)

        self._update_preview()

    def _get_item_id(self, item: Any) -> int:
        """항목의 ID 반환"""
        if self._category == 'nodes':
            return getattr(item, 'nid', 0)
        elif self._category in ('shell', 'solid', 'beam'):
            return getattr(item, 'eid', 0)
        elif self._category == 'parts':
            return getattr(item, 'pid', 0)
        elif self._category == 'materials':
            return getattr(item, 'mid', 0)
        elif self._category == 'sections':
            return getattr(item, 'secid', 0)
        elif self._category == 'sets':
            return getattr(item, 'sid', 0)
        return 0

    def _calculate_new_value(self, item: Any, index: int) -> Optional[float]:
        """새 값 계산"""
        field_name = self._field_combo.currentData()
        if not field_name:
            return None

        current_value = getattr(item, field_name, 0)
        item_id = self._get_item_id(item)
        mode = self._mode_group.checkedId()

        try:
            if mode == 0:  # 고정값
                return self._value_spin.value()
            elif mode == 1:  # 더하기
                return current_value + self._add_spin.value()
            elif mode == 2:  # 곱하기
                return current_value * self._mul_spin.value()
            elif mode == 3:  # 수식
                expr = self._expr_edit.text().strip()
                if not expr:
                    return current_value
                # 안전한 수식 평가
                allowed_names = {
                    'v': current_value,
                    'i': index,
                    'id': item_id,
                    'abs': abs,
                    'min': min,
                    'max': max,
                    'round': round,
                    'int': int,
                    'float': float,
                }
                return eval(expr, {"__builtins__": {}}, allowed_names)
        except Exception as e:
            return None

        return current_value

    def _update_preview(self):
        """미리보기 업데이트"""
        field_name = self._field_combo.currentData()
        if not field_name or not self._items:
            self._preview_text.clear()
            return

        lines = []
        preview_items = self._items[:5]  # 처음 5개만

        for i, item in enumerate(preview_items):
            item_id = self._get_item_id(item)
            old_value = getattr(item, field_name, 0)
            new_value = self._calculate_new_value(item, i)

            if new_value is not None:
                if isinstance(old_value, float):
                    lines.append(f"ID {item_id}: {old_value:.6f} -> {new_value:.6f}")
                else:
                    lines.append(f"ID {item_id}: {old_value} -> {int(new_value)}")
            else:
                lines.append(f"ID {item_id}: 오류")

        if len(self._items) > 5:
            lines.append(f"... 외 {len(self._items) - 5}개 항목")

        self._preview_text.setText('\n'.join(lines))

    def _on_accept(self):
        """확인 버튼 클릭"""
        field_name = self._field_combo.currentData()
        if not field_name:
            return

        mode = self._mode_group.checkedId()
        mode_names = ['set', 'add', 'multiply', 'expression']

        # 수식 모드 검증
        if mode == 3:
            expr = self._expr_edit.text().strip()
            if not expr:
                QMessageBox.warning(self, "입력 오류", "수식을 입력해주세요.")
                self._expr_edit.setFocus()
                return

            # 테스트 평가
            try:
                test_item = self._items[0] if self._items else None
                if test_item:
                    result = self._calculate_new_value(test_item, 0)
                    if result is None:
                        raise ValueError("계산 오류")
            except Exception as e:
                QMessageBox.warning(self, "수식 오류", f"수식 평가 중 오류: {e}")
                return

        # 결과 데이터 저장
        if mode == 0:
            value = self._value_spin.value()
        elif mode == 1:
            value = self._add_spin.value()
        elif mode == 2:
            value = self._mul_spin.value()
        else:
            value = self._expr_edit.text().strip()

        self._result_data = {
            'field_name': field_name,
            'mode': mode_names[mode],
            'value': value,
        }

        self.batchEditApplied.emit(field_name, mode_names[mode], value)
        self.accept()

    def get_result(self) -> Optional[Dict]:
        """결과 반환"""
        if self.result() == QDialog.Accepted:
            return self._result_data
        return None

    def apply_to_items(self, items: List[Any]) -> List[tuple]:
        """항목들에 수정 적용하고 (item, field, old_value, new_value) 리스트 반환"""
        if not self._result_data:
            return []

        field_name = self._result_data['field_name']
        mode = self._result_data['mode']
        value = self._result_data['value']

        changes = []

        for i, item in enumerate(items):
            old_value = getattr(item, field_name, 0)
            item_id = self._get_item_id(item)

            if mode == 'set':
                new_value = value
            elif mode == 'add':
                new_value = old_value + value
            elif mode == 'multiply':
                new_value = old_value * value
            elif mode == 'expression':
                try:
                    allowed_names = {
                        'v': old_value,
                        'i': i,
                        'id': item_id,
                        'abs': abs,
                        'min': min,
                        'max': max,
                        'round': round,
                        'int': int,
                        'float': float,
                    }
                    new_value = eval(value, {"__builtins__": {}}, allowed_names)
                except Exception:
                    continue
            else:
                continue

            # 필드 타입에 맞게 변환
            fields = EDITABLE_FIELDS.get(self._category, [])
            field_info = next((f for f in fields if f['name'] == field_name), None)
            if field_info and field_info['type'] == 'int':
                new_value = int(new_value)

            changes.append((item, field_name, old_value, new_value))

        return changes
