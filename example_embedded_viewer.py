#!/usr/bin/env python3
"""다른 애플리케이션에 뷰어를 임베드하는 예제

DOE 결과 비교, 최적화 결과 시각화 등에 사용 가능
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QSplitter, QListWidget, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.app_context import AppContext


class DOEVisualizerApp(QMainWindow):
    """DOE 결과 비교 애플리케이션

    좌측: DOE 케이스 리스트
    우측: 3D 뷰어 (선택된 케이스의 Part 구성 표시)
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DOE Result Visualizer")
        self.resize(1200, 700)

        # 메쉬 데이터 (공통)
        self.mesh = None

        # DOE 케이스별 Part 구성
        self.doe_cases = {
            "Case 1 - Baseline": {1, 2, 3, 4, 5},
            "Case 2 - Optimized A": {1, 2, 6, 7, 8},
            "Case 3 - Optimized B": {1, 3, 9, 10},
            "Case 4 - Lightweight": {2, 3, 5, 11},
        }

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # 좌측: DOE 케이스 리스트
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(300)

        left_layout.addWidget(QLabel("<b>DOE Cases</b>"))

        self.case_list = QListWidget()
        self.case_list.addItems(self.doe_cases.keys())
        self.case_list.currentTextChanged.connect(self._on_case_selected)
        left_layout.addWidget(self.case_list)

        # 케이스 정보
        self.case_info = QLabel("No case selected")
        self.case_info.setWordWrap(True)
        self.case_info.setStyleSheet("padding: 10px; background: #f0f0f0;")
        left_layout.addWidget(self.case_info)

        layout.addWidget(left_panel)

        # 우측: 3D 뷰어 (임베드)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(QLabel("<b>3D Viewer</b>"))

        # 순수 뷰어 위젯 (VBO 고속 렌더링)
        self.viewer = ModelGLWidget(backend='vbo')
        right_layout.addWidget(self.viewer, 1)

        # 간단한 컨트롤
        ctrl_layout = QHBoxLayout()
        for name, callback in [
            ("Front", self.viewer.view_front),
            ("Top", self.viewer.view_top),
            ("Iso", self.viewer.view_isometric),
            ("Reset", self.viewer.reset_view),
        ]:
            btn = QPushButton(name)
            btn.clicked.connect(callback)
            ctrl_layout.addWidget(btn)
        ctrl_layout.addStretch()
        right_layout.addLayout(ctrl_layout)

        layout.addWidget(right_panel, 1)

    def load_model(self, k_file_path: str):
        """K-file 로드 (한 번만)"""
        ctx = AppContext()
        ctx.load_k_file(k_file_path)
        self.mesh = MeshData.from_parsed_model(ctx.model)
        self.viewer.set_mesh(self.mesh)

        # 첫 번째 케이스 선택
        self.case_list.setCurrentRow(0)

    def _on_case_selected(self, case_name: str):
        """DOE 케이스 선택 시"""
        if not case_name or not self.mesh:
            return

        # 해당 케이스의 Part 구성 가져오기
        part_ids = self.doe_cases[case_name]

        # 뷰어에 반영
        self.viewer.set_visible_parts(part_ids)
        self.viewer.reset_view()

        # 정보 표시
        part_list = ", ".join(str(pid) for pid in sorted(part_ids))
        self.case_info.setText(
            f"<b>{case_name}</b><br><br>"
            f"Parts: {part_list}<br>"
            f"Total: {len(part_ids)} parts"
        )


def main():
    """예제 실행"""
    app = QApplication(sys.argv)

    # DOE 비교 애플리케이션
    window = DOEVisualizerApp()
    window.load_model("examples/DropSet.k")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
