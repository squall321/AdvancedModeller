"""Log viewer widget for displaying execution output"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QTextEdit, QPushButton, QLabel)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor
from datetime import datetime
import qtawesome as qta

class LogViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header
        header = QHBoxLayout()
        title = QLabel("Log")
        title.setObjectName("subtitle")
        header.addWidget(title)
        header.addStretch()

        clear_btn = QPushButton(qta.icon('fa5s.trash-alt', color='#9ca3af'), "지우기")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self.clear)
        header.addWidget(clear_btn)
        layout.addLayout(header)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        # Ensure vertical scroll bar is always shown
        from PySide6.QtCore import Qt
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        layout.addWidget(self.log_text)

    @Slot(str)
    def append(self, message: str, level: str = "info"):
        """Append message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#9ca3af",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "process": "#3b82f6"
        }
        icons = {
            "info": "",
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "process": "▶"
        }

        color = colors.get(level, colors["info"])
        icon = icons.get(level, "")

        html = f'<span style="color:#6b7280">{timestamp}</span> '
        html += f'<span style="color:{color}">{icon} {message}</span><br>'

        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        self.log_text.insertHtml(html)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def append_raw(self, text: str):
        """Append raw text (for process output)"""
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        self.log_text.insertPlainText(text)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def clear(self):
        self.log_text.clear()
