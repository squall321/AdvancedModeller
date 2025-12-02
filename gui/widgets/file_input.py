"""File input widget with browse button"""
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit,
                                QPushButton, QFileDialog, QLabel)
from PySide6.QtCore import Signal
import qtawesome as qta

class FileInputWidget(QWidget):
    fileSelected = Signal(str)

    def __init__(self, label: str, file_filter: str = "", parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        self._setup_ui(label)

    def _setup_ui(self, label: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Icon label
        icon_label = QLabel()
        if "K파일" in label or "k파일" in label.lower():
            icon_label.setPixmap(qta.icon('fa5s.file-code', color='#9ca3af').pixmap(20, 20))
        elif "Material" in label:
            icon_label.setPixmap(qta.icon('fa5s.clipboard-list', color='#9ca3af').pixmap(20, 20))
        else:
            icon_label.setPixmap(qta.icon('fa5s.save', color='#9ca3af').pixmap(20, 20))
        layout.addWidget(icon_label)

        # Label
        lbl = QLabel(label)
        lbl.setFixedWidth(80)
        layout.addWidget(lbl)

        # Path input
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("파일 경로를 선택하세요...")
        layout.addWidget(self.path_edit, 1)

        # Browse button
        browse_btn = QPushButton(qta.icon('fa5s.folder-open', color='#f3f4f6'), "열기")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse)
        layout.addWidget(browse_btn)

    def _browse(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "파일 선택", "", self.file_filter
        )
        if filepath:
            self.path_edit.setText(filepath)
            self.fileSelected.emit(filepath)

    def get_path(self) -> str:
        return self.path_edit.text()

    def set_path(self, path: str):
        self.path_edit.setText(path)
