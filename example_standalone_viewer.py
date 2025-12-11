#!/usr/bin/env python3
"""독립적으로 OpenGL 뷰어만 사용하는 예제

파일 로드 UI나 Part 트리 없이 순수 뷰어만 사용
다른 애플리케이션에 임베드 가능
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.app_context import AppContext


class SimpleViewerWindow(QMainWindow):
    """최소한의 뷰어 윈도우 (파일 로드/Part 선택 UI 없음)"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Standalone 3D Viewer")
        self.resize(800, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 순수 OpenGL 뷰어만 (VBO 백엔드 사용)
        self.viewer = ModelGLWidget(backend='vbo')
        layout.addWidget(self.viewer, 1)

        # 간단한 뷰 버튼들만
        btn_layout = QHBoxLayout()

        for name, callback in [
            ("Front", self.viewer.view_front),
            ("Top", self.viewer.view_top),
            ("Right", self.viewer.view_right),
            ("Iso", self.viewer.view_isometric),
            ("Reset", self.viewer.reset_view),
        ]:
            btn = QPushButton(name)
            btn.clicked.connect(callback)
            btn_layout.addWidget(btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def set_mesh_data(self, mesh: MeshData, visible_parts=None):
        """외부에서 메쉬 데이터를 주입

        Args:
            mesh: MeshData 객체
            visible_parts: 표시할 Part ID 집합 (None이면 전체)
        """
        self.viewer.set_mesh(mesh)

        if visible_parts is None:
            visible_parts = set(mesh.part_elements.keys())

        self.viewer.set_visible_parts(visible_parts)


def main():
    """예제: K-file 로드는 별도로 하고 뷰어는 순수하게 사용"""
    app = QApplication(sys.argv)

    # 1. 데이터는 별도로 로드 (뷰어와 독립적)
    ctx = AppContext()
    ctx.load_k_file("examples/DropSet.k")

    # 2. MeshData 생성 (뷰어와 독립적)
    mesh = MeshData.from_parsed_model(ctx.model)

    # 3. 뷰어는 순수하게 렌더링만 담당
    window = SimpleViewerWindow()

    # 4. 특정 Part만 선택해서 표시 (예: Part 1, 3, 5만)
    selected_parts = {1, 3, 5}
    window.set_mesh_data(mesh, visible_parts=selected_parts)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
