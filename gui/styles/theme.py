"""Dark theme for Laminate Modeller"""

class Theme:
    # Colors
    BG_DARK = "#1a1a2e"
    BG_MEDIUM = "#16213e"
    CARD_BG = "#1f2937"
    CARD_BORDER = "#374151"
    ACCENT = "#3b82f6"
    ACCENT_HOVER = "#2563eb"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    TEXT = "#f3f4f6"
    TEXT_DIM = "#9ca3af"

    # Material colors for layer preview
    MAT_ELASTIC = "#3b82f6"
    MAT_VISCOELASTIC = "#10b981"
    MAT_ELASTOPLASTIC = "#f59e0b"
    MAT_PSA = "#6b7280"

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #f3f4f6;
    font-family: 'Segoe UI', 'Noto Sans', sans-serif;
    font-size: 13px;
}

QGroupBox {
    background-color: #1f2937;
    border: 1px solid #374151;
    border-radius: 6px;
    margin-top: 8px;
    padding: 8px;
    padding-top: 16px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #9ca3af;
}

QPushButton {
    background-color: #374151;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    color: #f3f4f6;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #4b5563;
}

QPushButton:pressed {
    background-color: #3b82f6;
}

QPushButton:disabled {
    background-color: #1f2937;
    color: #6b7280;
}

QPushButton#primary {
    background-color: #3b82f6;
}

QPushButton#primary:hover {
    background-color: #2563eb;
}

QPushButton#success {
    background-color: #10b981;
}

QPushButton#success:hover {
    background-color: #059669;
}

QLineEdit {
    background-color: #374151;
    border: 1px solid #4b5563;
    border-radius: 6px;
    padding: 8px;
    color: #f3f4f6;
}

QLineEdit:focus {
    border-color: #3b82f6;
}

QSpinBox, QDoubleSpinBox {
    background-color: #374151;
    border: 1px solid #4b5563;
    border-radius: 4px;
    padding: 4px 8px;
    color: #f3f4f6;
    min-height: 24px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3b82f6;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #4b5563;
    background-color: #4b5563;
    border-top-right-radius: 4px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
    background-color: #6b7280;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid #4b5563;
    background-color: #4b5563;
    border-bottom-right-radius: 4px;
}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #6b7280;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 10px;
    height: 10px;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 10px;
    height: 10px;
}

QComboBox {
    background-color: #374151;
    border: 1px solid #4b5563;
    border-radius: 6px;
    padding: 8px;
    color: #f3f4f6;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #3b82f6;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #374151;
    border: 1px solid #4b5563;
    selection-background-color: #3b82f6;
}

QTableWidget {
    background-color: #1f2937;
    border: 1px solid #374151;
    border-radius: 6px;
    gridline-color: #374151;
    color: #f3f4f6;
    alternate-background-color: #283548;
}

QTableWidget::item {
    padding: 8px;
    color: #f3f4f6;
}

QTableWidget::item:selected {
    background-color: #3b82f6;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #374151;
    color: #f3f4f6;
    border: none;
    border-right: 1px solid #4b5563;
    padding: 8px 4px;
    font-weight: bold;
    font-size: 12px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #1f2937;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #4b5563;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6b7280;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #4b5563;
    background-color: #374151;
}

QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border-color: #3b82f6;
}

QTextEdit {
    background-color: #0f172a;
    border: 1px solid #374151;
    border-radius: 6px;
    color: #f3f4f6;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
}

QStatusBar {
    background-color: #16213e;
    color: #9ca3af;
}

QLabel#title {
    font-size: 16px;
    font-weight: bold;
    color: #f3f4f6;
}

QLabel#subtitle {
    color: #9ca3af;
    font-size: 12px;
}

QFrame#card {
    background-color: #1f2937;
    border: 1px solid #374151;
    border-radius: 8px;
}

QFrame#partCard {
    background-color: #1f2937;
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 8px;
}

QFrame#partCard:hover {
    border-color: #3b82f6;
}
"""
