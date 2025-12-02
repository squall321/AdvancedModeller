"""Part list widget using QTableWidget for better UX"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                                QTableWidgetItem, QPushButton, QHeaderView,
                                QInputDialog, QMessageBox, QAbstractItemView,
                                QLineEdit)
from PySide6.QtCore import Signal, Qt
import qtawesome as qta
from typing import List, Dict
from models import PartConfig


class PartListWidget(QWidget):
    """Table-based part list for better overview"""
    partSelected = Signal(int)
    partToggled = Signal(int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parts: Dict[int, PartConfig] = {}
        self.selected_part_id: int = -1
        self._all_part_ids: List[int] = []  # For filtering
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색 (ID 또는 이름)...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_parts)
        layout.addWidget(self.search_input)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "ID", "Name", "Layers", "두께"])

        # Column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 28)   # Checkbox
        self.table.setColumnWidth(1, 50)   # ID
        self.table.setColumnWidth(3, 55)   # Layers
        self.table.setColumnWidth(4, 70)   # Thickness

        # Selection behavior
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemChanged.connect(self._on_item_changed)

        # Style
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        add_btn = QPushButton(qta.icon('fa5s.plus', color='#10b981'), "")
        add_btn.setToolTip("Part 추가")
        add_btn.setFixedSize(32, 32)
        add_btn.clicked.connect(self._add_part_manual)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton(qta.icon('fa5s.trash-alt', color='#ef4444'), "")
        remove_btn.setToolTip("선택한 Part 삭제")
        remove_btn.setFixedSize(32, 32)
        remove_btn.clicked.connect(self._remove_selected_part)
        btn_layout.addWidget(remove_btn)

        btn_layout.addStretch()

        select_all_btn = QPushButton("전체")
        select_all_btn.setToolTip("전체 선택")
        select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("해제")
        deselect_all_btn.setToolTip("전체 해제")
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(deselect_all_btn)

        layout.addLayout(btn_layout)

    def set_parts(self, part_ids: List[int]):
        """Set parts from K file or manual input (legacy support)"""
        self.set_parts_with_names({pid: "" for pid in part_ids})

    def set_parts_with_names(self, parts_dict: Dict[int, str]):
        """Set parts with names from K file. parts_dict = {pid: part_name}"""
        self.parts.clear()
        self.table.setRowCount(0)
        self._all_part_ids = sorted(parts_dict.keys())

        for pid in self._all_part_ids:
            part_name = parts_dict.get(pid, "")
            self.parts[pid] = PartConfig(part_id=pid, part_name=part_name)
            self._add_table_row(pid)

        if self._all_part_ids:
            self.table.selectRow(0)

    def _add_table_row(self, pid: int):
        """Add a row to the table"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        part = self.parts[pid]

        # Checkbox (column 0)
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        checkbox_item.setCheckState(Qt.CheckState.Checked if part.enabled else Qt.CheckState.Unchecked)
        checkbox_item.setData(Qt.ItemDataRole.UserRole, pid)  # Store PID
        self.table.setItem(row, 0, checkbox_item)

        # Part ID (column 1)
        id_item = QTableWidgetItem(str(pid))
        id_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, id_item)

        # Part Name (column 2)
        name_item = QTableWidgetItem(part.part_name if part.part_name else "-")
        name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        name_item.setToolTip(part.part_name)  # Show full name on hover
        self.table.setItem(row, 2, name_item)

        # Layer count (column 3)
        layer_item = QTableWidgetItem(str(part.layer_count) if part.layers else "-")
        layer_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        layer_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, layer_item)

        # Thickness (column 4)
        thickness_text = f"{part.total_thickness:.3f}mm" if part.layers else "-"
        thickness_item = QTableWidgetItem(thickness_text)
        thickness_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        thickness_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 4, thickness_item)

    def _on_selection_changed(self):
        """Handle row selection"""
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            item = self.table.item(row, 0)
            if item:
                pid = item.data(Qt.ItemDataRole.UserRole)
                if pid and pid != self.selected_part_id:
                    self.selected_part_id = pid
                    self.partSelected.emit(pid)

    def _on_item_changed(self, item: QTableWidgetItem):
        """Handle checkbox toggle"""
        if item.column() == 0:
            pid = item.data(Qt.ItemDataRole.UserRole)
            if pid and pid in self.parts:
                checked = item.checkState() == Qt.CheckState.Checked
                self.parts[pid].enabled = checked
                self.partToggled.emit(pid, checked)

    def _add_part_manual(self):
        """Manually add a part"""
        pid, ok = QInputDialog.getInt(
            self, "Part 추가", "Part ID:",
            1, 1, 999999, 1
        )
        if ok:
            if pid in self.parts:
                QMessageBox.warning(self, "경고", f"Part {pid}가 이미 존재합니다.")
                return
            self.add_part(pid)

    def add_part(self, pid: int):
        """Add a single part"""
        if pid in self.parts:
            return
        self.parts[pid] = PartConfig(part_id=pid)
        self._add_table_row(pid)

        # Select the new row
        self.table.selectRow(self.table.rowCount() - 1)

    def _remove_selected_part(self):
        """Remove selected part"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()
        item = self.table.item(row, 0)
        if item:
            pid = item.data(Qt.ItemDataRole.UserRole)
            if pid in self.parts:
                del self.parts[pid]
            self.table.removeRow(row)

            # Select next row
            if self.table.rowCount() > 0:
                new_row = min(row, self.table.rowCount() - 1)
                self.table.selectRow(new_row)
            else:
                self.selected_part_id = -1
                self.partSelected.emit(-1)

    def _select_all(self):
        """Enable all parts"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        """Disable all parts"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def get_part(self, part_id: int) -> PartConfig:
        return self.parts.get(part_id)

    def _filter_parts(self, text: str):
        """Filter parts by ID or name"""
        text = text.strip().lower()

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if not item:
                continue

            pid = item.data(Qt.ItemDataRole.UserRole)
            part = self.parts.get(pid)
            if not part:
                continue

            # Check if matches ID or name
            pid_str = str(pid)
            name_str = (part.part_name or "").lower()

            if not text or text in pid_str or text in name_str:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def update_part_card(self, part_id: int):
        """Update display for a specific part"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == part_id:
                part = self.parts.get(part_id)
                if part:
                    # Update checkbox
                    item.setCheckState(Qt.CheckState.Checked if part.enabled else Qt.CheckState.Unchecked)
                    # Update layer count (column 3)
                    self.table.item(row, 3).setText(str(part.layer_count) if part.layers else "-")
                    # Update thickness (column 4)
                    thickness_text = f"{part.total_thickness:.3f}mm" if part.layers else "-"
                    self.table.item(row, 4).setText(thickness_text)
                break

    def get_enabled_parts(self) -> List[PartConfig]:
        return [p for p in self.parts.values() if p.enabled]
