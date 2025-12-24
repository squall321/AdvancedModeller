"""Script Preview Dialog

Shows generated DOE script with syntax highlighting and save options.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
import qtawesome as qta


class ScriptSyntaxHighlighter(QSyntaxHighlighter):
    """Simple syntax highlighter for DOE scripts"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define formats
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#2563eb"))  # Blue
        self.keyword_format.setFontWeight(QFont.Bold)

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6b7280"))  # Gray
        self.comment_format.setFontItalic(True)

        self.value_format = QTextCharFormat()
        self.value_format.setForeground(QColor("#059669"))  # Green

        # Keywords
        self.keywords = [
            "Inputfile", "Mode", "TranslationX", "TranslationY", "TranslationZ",
            "TRANSLATION_DOE", "EndTranslation_DOE", "End", "PID"
        ]

    def highlightBlock(self, text):
        """Highlight a block of text"""
        # Highlight comments
        if text.strip().startswith("*") or text.strip().startswith("$"):
            self.setFormat(0, len(text), self.comment_format)
            return

        # Highlight keywords
        for keyword in self.keywords:
            index = text.find(keyword)
            while index >= 0:
                self.setFormat(index, len(keyword), self.keyword_format)
                index = text.find(keyword, index + len(keyword))


class ScriptPreviewDialog(QDialog):
    """Dialog for previewing and saving generated scripts"""

    def __init__(self, script_content: str, parent=None):
        super().__init__(parent)
        self.script_content = script_content
        self.saved_path = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("DOE Script Preview")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("Generated DOE Translation Script")
        title.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title)

        # Info label
        line_count = len(self.script_content.split('\n'))
        info = QLabel(f"Total lines: {line_count}")
        info.setStyleSheet("color: #6b7280;")
        layout.addWidget(info)

        # Text editor with syntax highlighting
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.script_content)
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Courier New", 10))
        self.text_edit.setLineWrapMode(QTextEdit.NoWrap)

        # Apply syntax highlighter
        self.highlighter = ScriptSyntaxHighlighter(self.text_edit.document())

        layout.addWidget(self.text_edit, 1)

        # Buttons
        button_layout = QHBoxLayout()

        self.copy_btn = QPushButton(qta.icon('fa5s.copy', color='#374151'), " Copy to Clipboard")
        self.copy_btn.clicked.connect(self._on_copy)
        button_layout.addWidget(self.copy_btn)

        self.save_btn = QPushButton(qta.icon('fa5s.save', color='#374151'), " Save As...")
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _on_copy(self):
        """Copy script to clipboard"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.script_content)

        QMessageBox.information(
            self,
            "Copied",
            "Script copied to clipboard!"
        )

    def _on_save(self):
        """Save script to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save DOE Script",
            "doe_translation.txt",
            "Script Files (*.txt);;All Files (*)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.script_content)

            self.saved_path = filename
            QMessageBox.information(
                self,
                "Saved",
                f"Script saved to:\n{filename}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save script:\n{str(e)}"
            )

    def get_saved_path(self) -> str:
        """Get path where script was saved (if any)"""
        return self.saved_path
