"""Layer table widget for editing laminate layers"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                                QTableWidgetItem, QComboBox, QDoubleSpinBox,
                                QSpinBox, QPushButton, QHeaderView, QLabel,
                                QAbstractItemView, QMessageBox, QFrame)
from PySide6.QtCore import Signal, Qt
import qtawesome as qta
from typing import List, Optional, Tuple
from models import LayerConfig

# Direction presets: name -> (x, y, z)
DIRECTION_PRESETS = {
    "Bottom-Up (0,1,0)": (0, 1, 0),
    "Top-Down (0,-1,0)": (0, -1, 0),
    "Left-Right (1,0,0)": (1, 0, 0),
    "Right-Left (-1,0,0)": (-1, 0, 0),
    "Front-Back (0,0,1)": (0, 0, 1),
    "Back-Front (0,0,-1)": (0, 0, -1),
    "Custom": None
}

class LayerTableWidget(QWidget):
    """Table widget for editing laminate layers"""
    layersChanged = Signal()
    stackSettingsChanged = Signal(tuple, float)  # (direction, angle)
    # Action logging signals
    layerAdded = Signal(str, float)  # (material_name, thickness)
    layerRemoved = Signal(int)  # count of removed layers
    layersCopied = Signal(int)  # count of copied layers
    layersPasted = Signal(int)  # count of pasted layers
    materialChanged = Signal(int, str)  # (row, new_material)
    thicknessChanged = Signal(int, float)  # (row, new_thickness)
    layerSetChanged = Signal(int, int)  # (row, new_layer_set)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.materials: List[str] = []
        self.current_part_id: int = -1
        self._clipboard: List[LayerConfig] = []
        self._current_direction: Tuple[float, float, float] = (0, 1, 0)
        self._current_angle: float = 5.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header - compact
        self.header_label = QLabel("Part - 선택 안됨")
        layout.addWidget(self.header_label)

        # Stack direction settings
        stack_layout = QHBoxLayout()
        stack_layout.setSpacing(8)

        dir_label = QLabel("적층 방향:")
        dir_label.setFixedWidth(60)
        stack_layout.addWidget(dir_label)

        self.direction_combo = QComboBox()
        self.direction_combo.addItems(list(DIRECTION_PRESETS.keys()))
        self.direction_combo.setFixedWidth(150)
        self.direction_combo.currentTextChanged.connect(self._on_direction_preset_changed)
        stack_layout.addWidget(self.direction_combo)

        # Custom direction inputs (hidden by default)
        self.custom_frame = QFrame()
        custom_layout = QHBoxLayout(self.custom_frame)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(2)

        self.dir_x = QDoubleSpinBox()
        self.dir_x.setRange(-1, 1)
        self.dir_x.setDecimals(1)
        self.dir_x.setSingleStep(0.1)
        self.dir_x.setFixedWidth(50)
        self.dir_x.valueChanged.connect(self._on_custom_direction_changed)
        custom_layout.addWidget(self.dir_x)

        self.dir_y = QDoubleSpinBox()
        self.dir_y.setRange(-1, 1)
        self.dir_y.setDecimals(1)
        self.dir_y.setSingleStep(0.1)
        self.dir_y.setFixedWidth(50)
        self.dir_y.setValue(1)
        self.dir_y.valueChanged.connect(self._on_custom_direction_changed)
        custom_layout.addWidget(self.dir_y)

        self.dir_z = QDoubleSpinBox()
        self.dir_z.setRange(-1, 1)
        self.dir_z.setDecimals(1)
        self.dir_z.setSingleStep(0.1)
        self.dir_z.setFixedWidth(50)
        self.dir_z.valueChanged.connect(self._on_custom_direction_changed)
        custom_layout.addWidget(self.dir_z)

        self.custom_frame.setVisible(False)
        stack_layout.addWidget(self.custom_frame)

        stack_layout.addStretch()

        angle_label = QLabel("각도:")
        stack_layout.addWidget(angle_label)

        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(0, 90)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setSingleStep(1)
        self.angle_spin.setSuffix("°")
        self.angle_spin.setValue(5.0)
        self.angle_spin.setFixedWidth(70)
        self.angle_spin.valueChanged.connect(self._on_angle_changed)
        stack_layout.addWidget(self.angle_spin)

        layout.addLayout(stack_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Material", "두께 (mm)", "층구분"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 70)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        layout.addWidget(self.table, 1)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton(qta.icon('fa5s.plus', color='#10b981'), " 추가")
        add_btn.clicked.connect(self._add_layer)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton(qta.icon('fa5s.minus', color='#ef4444'), " 삭제")
        remove_btn.clicked.connect(self._remove_layer)
        btn_layout.addWidget(remove_btn)

        btn_layout.addStretch()

        copy_btn = QPushButton(qta.icon('fa5s.copy', color='#9ca3af'), " 복사")
        copy_btn.clicked.connect(self._copy_layers)
        btn_layout.addWidget(copy_btn)

        paste_btn = QPushButton(qta.icon('fa5s.paste', color='#9ca3af'), " 붙여넣기")
        paste_btn.clicked.connect(self._paste_layers)
        btn_layout.addWidget(paste_btn)

        layout.addLayout(btn_layout)

    def set_materials(self, materials: List[str]):
        """Set available materials for combo boxes"""
        self.materials = materials
        # Update existing combo boxes
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            if combo:
                current = combo.currentText()
                combo.blockSignals(True)
                combo.clear()
                combo.addItems(materials)
                if current in materials:
                    combo.setCurrentText(current)
                elif materials:
                    combo.setCurrentIndex(0)
                combo.blockSignals(False)

    def set_part(self, part_id: int, layers: List[LayerConfig],
                 direction: Tuple[float, float, float] = None,
                 angle: float = None):
        """Load layers for a part"""
        self.current_part_id = part_id
        if part_id >= 0:
            self.header_label.setText(f"Part {part_id}")
        else:
            self.header_label.setText("Part - 선택 안됨")

        # Set stack direction and angle
        if direction is not None:
            self._set_direction(direction)
        if angle is not None:
            self.angle_spin.blockSignals(True)
            self.angle_spin.setValue(angle)
            self._current_angle = angle
            self.angle_spin.blockSignals(False)

        self._populate_table(layers)

    def _set_direction(self, direction: Tuple[float, float, float]):
        """Set direction in UI"""
        self._current_direction = direction

        # Check if it matches a preset
        preset_found = False
        for name, preset_dir in DIRECTION_PRESETS.items():
            if preset_dir == direction:
                self.direction_combo.blockSignals(True)
                self.direction_combo.setCurrentText(name)
                self.direction_combo.blockSignals(False)
                self.custom_frame.setVisible(False)
                preset_found = True
                break

        if not preset_found:
            # Set to Custom
            self.direction_combo.blockSignals(True)
            self.direction_combo.setCurrentText("Custom")
            self.direction_combo.blockSignals(False)
            self.custom_frame.setVisible(True)
            self.dir_x.blockSignals(True)
            self.dir_y.blockSignals(True)
            self.dir_z.blockSignals(True)
            self.dir_x.setValue(direction[0])
            self.dir_y.setValue(direction[1])
            self.dir_z.setValue(direction[2])
            self.dir_x.blockSignals(False)
            self.dir_y.blockSignals(False)
            self.dir_z.blockSignals(False)

    def _populate_table(self, layers: List[LayerConfig]):
        self.table.setRowCount(0)
        for i, layer in enumerate(layers):
            self._add_row(i, layer)

    def _add_row(self, row: int, layer: Optional[LayerConfig] = None, emit_signals: bool = True):
        self.table.insertRow(row)
        self.table.setRowHeight(row, 38)

        # Row number
        num_item = QTableWidgetItem(str(row + 1))
        num_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, num_item)

        # Material combo
        combo = QComboBox()
        combo.setFixedHeight(30)
        combo.addItems(self.materials)
        if layer and layer.material_name in self.materials:
            combo.setCurrentText(layer.material_name)
        elif self.materials:
            combo.setCurrentIndex(0)
        combo.setProperty("row", row)
        combo.currentTextChanged.connect(self._on_material_changed)
        self.table.setCellWidget(row, 1, combo)

        # Thickness spin
        thickness_spin = QDoubleSpinBox()
        thickness_spin.setFixedHeight(30)
        thickness_spin.setMinimumWidth(85)
        thickness_spin.setRange(0.001, 10.0)
        thickness_spin.setDecimals(3)
        thickness_spin.setSingleStep(0.01)
        thickness_spin.setSuffix(" mm")
        thickness_spin.setValue(layer.thickness if layer else 0.05)
        thickness_spin.setProperty("row", row)
        thickness_spin.valueChanged.connect(self._on_thickness_changed)
        self.table.setCellWidget(row, 2, thickness_spin)

        # Layer set spin
        set_spin = QSpinBox()
        set_spin.setFixedHeight(30)
        set_spin.setMinimumWidth(45)
        set_spin.setRange(1, 99)
        set_spin.setValue(layer.layer_set if layer else row + 1)
        set_spin.setProperty("row", row)
        set_spin.valueChanged.connect(self._on_layer_set_changed)
        self.table.setCellWidget(row, 3, set_spin)

    def _add_layer(self):
        if not self.materials:
            QMessageBox.warning(self, "경고", "Material Source를 먼저 로드하세요.")
            return
        if self.current_part_id < 0:
            QMessageBox.warning(self, "경고", "Part를 먼저 선택하세요.")
            return

        row = self.table.rowCount()
        new_layer = LayerConfig(
            material_name=self.materials[0],
            thickness=0.05,
            layer_set=row + 1
        )
        self._add_row(row, new_layer)
        self._update_row_numbers()
        self._on_change()
        self.layerAdded.emit(new_layer.material_name, new_layer.thickness)

    def _remove_layer(self):
        if self.table.rowCount() == 0:
            return

        selected_rows = self.table.selectionModel().selectedRows()
        removed_count = 0
        if not selected_rows:
            # If no row selected, remove last row
            self.table.removeRow(self.table.rowCount() - 1)
            removed_count = 1
        else:
            removed_count = len(selected_rows)
            for index in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
                self.table.removeRow(index.row())
        self._update_row_numbers()
        self._on_change()
        self.layerRemoved.emit(removed_count)

    def _update_row_numbers(self):
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item:
                item.setText(str(i + 1))

    def _copy_layers(self):
        self._clipboard = self.get_layers()
        if self._clipboard:
            self.layersCopied.emit(len(self._clipboard))

    def _paste_layers(self):
        if self._clipboard:
            self._populate_table(self._clipboard)
            self._on_change()
            self.layersPasted.emit(len(self._clipboard))

    def _on_change(self):
        self.layersChanged.emit()

    def _on_material_changed(self, value: str):
        """Handle material combo change"""
        sender = self.sender()
        if sender:
            row = self._find_widget_row(sender, 1)
            if row >= 0:
                self.materialChanged.emit(row, value)
        self.layersChanged.emit()

    def _on_thickness_changed(self, value: float):
        """Handle thickness spin change"""
        sender = self.sender()
        if sender:
            row = self._find_widget_row(sender, 2)
            if row >= 0:
                self.thicknessChanged.emit(row, value)
        self.layersChanged.emit()

    def _on_layer_set_changed(self, value: int):
        """Handle layer set spin change"""
        sender = self.sender()
        if sender:
            row = self._find_widget_row(sender, 3)
            if row >= 0:
                self.layerSetChanged.emit(row, value)
        self.layersChanged.emit()

    def _find_widget_row(self, widget, column: int) -> int:
        """Find the row of a widget in the table"""
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, column) == widget:
                return row
        return -1

    def get_layers(self) -> List[LayerConfig]:
        """Get current layers from table"""
        layers = []
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            thickness_spin = self.table.cellWidget(row, 2)
            set_spin = self.table.cellWidget(row, 3)

            if combo and thickness_spin and set_spin:
                layers.append(LayerConfig(
                    material_name=combo.currentText(),
                    thickness=thickness_spin.value(),
                    layer_set=set_spin.value()
                ))
        return layers

    def _on_direction_preset_changed(self, text: str):
        """Handle direction preset selection"""
        if text == "Custom":
            self.custom_frame.setVisible(True)
            self._current_direction = (
                self.dir_x.value(),
                self.dir_y.value(),
                self.dir_z.value()
            )
        else:
            self.custom_frame.setVisible(False)
            preset_dir = DIRECTION_PRESETS.get(text)
            if preset_dir:
                self._current_direction = preset_dir
        self._emit_stack_settings()

    def _on_custom_direction_changed(self):
        """Handle custom direction value change"""
        self._current_direction = (
            self.dir_x.value(),
            self.dir_y.value(),
            self.dir_z.value()
        )
        self._emit_stack_settings()

    def _on_angle_changed(self, value: float):
        """Handle angle value change"""
        self._current_angle = value
        self._emit_stack_settings()

    def _emit_stack_settings(self):
        """Emit stack settings changed signal"""
        self.stackSettingsChanged.emit(self._current_direction, self._current_angle)

    def get_stack_direction(self) -> Tuple[float, float, float]:
        """Get current stack direction"""
        return self._current_direction

    def get_stack_angle(self) -> float:
        """Get current stack angle"""
        return self._current_angle
