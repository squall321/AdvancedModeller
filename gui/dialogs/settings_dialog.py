"""Settings dialog"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                                QLabel, QLineEdit, QPushButton, QFileDialog,
                                QComboBox)
from PySide6.QtCore import Signal
import qtawesome as qta
from gui.styles import DARK_STYLE

class SettingsDialog(QDialog):
    settingsChanged = Signal(dict)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("설정")
        self.setMinimumWidth(500)
        self.setStyleSheet(DARK_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # KooMeshModifier path
        koomesh_group = QGroupBox("KooMeshModifier 경로")
        koomesh_layout = QHBoxLayout(koomesh_group)

        self.koomesh_edit = QLineEdit()
        self.koomesh_edit.setText(self.config.get("koomesh_path", ""))
        self.koomesh_edit.setPlaceholderText("KooMeshModifier 실행 파일 경로")
        koomesh_layout.addWidget(self.koomesh_edit, 1)

        browse_btn = QPushButton(qta.icon('fa5s.folder-open', color='#f3f4f6'), "찾기")
        browse_btn.clicked.connect(self._browse_koomesh)
        koomesh_layout.addWidget(browse_btn)

        layout.addWidget(koomesh_group)

        # Default directories
        dirs_group = QGroupBox("기본 디렉토리")
        dirs_layout = QVBoxLayout(dirs_group)

        # Default output dir
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("출력 디렉토리:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(self.config.get("last_output_dir", ""))
        output_layout.addWidget(self.output_dir_edit, 1)
        output_browse = QPushButton("찾기")
        output_browse.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(output_browse)
        dirs_layout.addLayout(output_layout)

        layout.addWidget(dirs_group)

        # Theme
        theme_group = QGroupBox("테마")
        theme_layout = QHBoxLayout(theme_group)
        theme_layout.addWidget(QLabel("테마 선택:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.config.get("theme", "Dark").capitalize())
        theme_layout.addWidget(self.theme_combo, 1)
        layout.addWidget(theme_group)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("저장")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _browse_koomesh(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "KooMeshModifier 선택", "",
            "Executable (*.exe *.sh *.bat);;All Files (*)"
        )
        if filepath:
            self.koomesh_edit.setText(filepath)

    def _browse_output_dir(self):
        dirpath = QFileDialog.getExistingDirectory(self, "출력 디렉토리 선택")
        if dirpath:
            self.output_dir_edit.setText(dirpath)

    def _save(self):
        self.config["koomesh_path"] = self.koomesh_edit.text()
        self.config["last_output_dir"] = self.output_dir_edit.text()
        self.config["theme"] = self.theme_combo.currentText().lower()
        self.settingsChanged.emit(self.config)
        self.accept()

    def get_config(self) -> dict:
        return self.config
