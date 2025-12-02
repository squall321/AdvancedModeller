"""Preview dialog for generated script"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit,
                                QPushButton, QHBoxLayout)
from PySide6.QtGui import QFont
from gui.styles import DARK_STYLE

class PreviewDialog(QDialog):
    def __init__(self, script: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("스크립트 미리보기")
        self.setMinimumSize(600, 500)
        self.setStyleSheet(DARK_STYLE)

        layout = QVBoxLayout(self)

        # Text area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 11))
        self.text_edit.setPlainText(script)
        layout.addWidget(self.text_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
