"""Model Viewer Module - 3D K-file visualization

초고속 3D 시각화 모듈
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QGroupBox, QCheckBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

try:
    import qtawesome as qta
except ImportError:
    qta = None

from gui.modules.base import BaseModule
from gui.modules import ModuleRegistry
from .widgets.gl_widget import ModelGLWidget
from .widgets.part_tree import PartTreeWidget
from .widgets.element_info import ElementInfoWidget
from .core.mesh_data import MeshData

if TYPE_CHECKING:
    from gui.app_context import AppContext


@ModuleRegistry.register(
    module_id="model_viewer",
    name="모델 뷰어",
    description="K-file 3D 시각화",
    icon="fa5s.cube",
    order=10,
    methods=[
        {'id': 'load', 'name': '모델 로드', 'icon': 'fa5s.folder-open'},
        {'id': 'reset_view', 'name': '뷰 리셋', 'icon': 'fa5s.eye'},
    ]
)
class ModelViewerModule(BaseModule):
    """3D 모델 뷰어 모듈

    빠른 와이어프레임 렌더링과 Part 제어
    """

    @property
    def module_id(self) -> str:
        return "model_viewer"

    def __init__(self, ctx: 'AppContext', parent=None):
        self._mesh_data: MeshData = None
        super().__init__(ctx, parent)

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 파일 정보 (읽기 전용)
        self._file_label = QLabel("K-file: (파일 로더에서 로드하세요)")
        self._file_label.setStyleSheet("padding: 4px; color: gray;")
        layout.addWidget(self._file_label)

        # 메인 스플리터
        splitter = QSplitter(Qt.Horizontal)

        # 좌측: Part 트리 + 요소 정보
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Part 트리
        self._part_tree = PartTreeWidget()
        self._part_tree.setMinimumWidth(250)
        self._part_tree.visibilityChanged.connect(self._on_part_visibility_changed)
        left_layout.addWidget(self._part_tree, 2)  # 2/3 높이

        # 요소 정보
        self._element_info = ElementInfoWidget()
        left_layout.addWidget(self._element_info, 1)  # 1/3 높이

        splitter.addWidget(left_widget)

        # 우측: 3D 뷰
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        self._gl_widget = ModelGLWidget()
        self._gl_widget.setMinimumSize(400, 300)
        self._gl_widget.statusMessage.connect(self._on_gl_status)
        self._gl_widget.fpsUpdate.connect(self._on_fps_update)
        self._gl_widget.elementSelected.connect(self._on_element_selected)
        right_layout.addWidget(self._gl_widget, 1)

        # 뷰 옵션
        options_layout = QHBoxLayout()

        # Backend selector
        backend_label = QLabel("Backend:")
        options_layout.addWidget(backend_label)

        self._backend_combo = QComboBox()
        self._backend_combo.addItems(["Legacy OpenGL", "VBO (GPU 가속)", "PyVista (향후)"])
        self._backend_combo.setCurrentIndex(0)
        self._backend_combo.setToolTip("렌더링 백엔드 선택\n- Legacy: 최대 호환성\n- VBO: GPU 가속 (10-100배 빠름)")
        self._backend_combo.currentIndexChanged.connect(self._on_backend_changed)
        options_layout.addWidget(self._backend_combo)

        options_layout.addSpacing(15)

        self._show_solid_cb = QCheckBox("Solid")
        self._show_solid_cb.setChecked(True)  # CAE에서는 기본적으로 Solid 뷰
        self._show_solid_cb.toggled.connect(self._gl_widget.set_show_solid)
        options_layout.addWidget(self._show_solid_cb)

        self._show_edges_cb = QCheckBox("Edges")
        self._show_edges_cb.setChecked(True)  # 외곽 윤곽선 (CAE 기본)
        self._show_edges_cb.setToolTip("외곽 엣지 표시 (검은색 윤곽선)")
        self._show_edges_cb.toggled.connect(self._gl_widget.set_show_edges)
        options_layout.addWidget(self._show_edges_cb)

        self._show_wireframe_cb = QCheckBox("와이어프레임")
        self._show_wireframe_cb.setChecked(False)  # 내부 엣지까지 (비효율적)
        self._show_wireframe_cb.setToolTip("모든 엣지 표시 (내부까지)")
        self._show_wireframe_cb.toggled.connect(self._gl_widget.set_show_wireframe)
        options_layout.addWidget(self._show_wireframe_cb)

        self._show_nodes_cb = QCheckBox("노드")
        self._show_nodes_cb.setChecked(False)
        self._show_nodes_cb.toggled.connect(self._gl_widget.set_show_nodes)
        options_layout.addWidget(self._show_nodes_cb)

        if qta:
            reset_btn = QPushButton(qta.icon('fa5s.eye'), " 뷰 리셋")
        else:
            reset_btn = QPushButton("뷰 리셋")
        reset_btn.clicked.connect(self._gl_widget.reset_view)
        options_layout.addWidget(reset_btn)

        # 6-View buttons
        options_layout.addSpacing(10)
        view_label = QLabel("뷰:")
        options_layout.addWidget(view_label)

        # Create compact view buttons
        view_buttons = [
            ("F", "Front", self._gl_widget.view_front),
            ("B", "Back", self._gl_widget.view_back),
            ("L", "Left", self._gl_widget.view_left),
            ("R", "Right", self._gl_widget.view_right),
            ("T", "Top", self._gl_widget.view_top),
            ("Bo", "Bottom", self._gl_widget.view_bottom),
            ("Iso", "Isometric", self._gl_widget.view_isometric),
        ]

        for text, tooltip, callback in view_buttons:
            btn = QPushButton(text)
            btn.setToolTip(f"{tooltip} view")
            btn.setFixedWidth(32 if len(text) <= 1 else 40)
            btn.clicked.connect(callback)
            options_layout.addWidget(btn)

        # FPS 표시
        self._fps_label = QLabel("FPS: --")
        self._fps_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        options_layout.addWidget(self._fps_label)

        options_layout.addStretch()
        right_layout.addLayout(options_layout)

        splitter.addWidget(right_widget)

        # 스플리터 비율
        splitter.setSizes([250, 550])

        layout.addWidget(splitter, 1)

        # 상태바
        self._status = QLabel("준비됨")
        self._status.setStyleSheet("padding: 4px; background: palette(alternate-base);")
        layout.addWidget(self._status)

    def on_activate(self):
        """모듈 활성화 시"""
        # AppContext에서 모델이 로드되어 있으면 사용
        if self.ctx.model.is_loaded:
            import os
            self._file_label.setText(f"K-file: {os.path.basename(self.ctx.model.filepath)}")
            self._file_label.setStyleSheet("padding: 4px;")
            self._load_from_context_model()
        else:
            self._file_label.setText("K-file: (파일 로더에서 로드하세요)")
            self._file_label.setStyleSheet("padding: 4px; color: gray;")
            self.log("파일 로더에서 K-file을 먼저 로드해주세요", "info")

    def on_action(self, action_id: str):
        """액션 처리"""
        if action_id == 'load':
            self.log("파일 로더 모듈을 사용하여 K-file을 로드하세요", "info")
        elif action_id == 'reset_view':
            self._gl_widget.reset_view()

    def _browse_file(self):
        """파일 선택 다이얼로그"""
        import os
        start_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "examples")
        if not os.path.exists(start_dir):
            start_dir = ""

        path, _ = QFileDialog.getOpenFileName(
            self,
            "K-file 열기",
            start_dir,
            "K-files (*.k *.key *.dyn);;All files (*.*)"
        )
        if path:
            self._file_path.setText(path)
            self.log(f"파일 선택됨: {path}", "info")
            self._load_model()

    def _load_model(self):
        """모델 로드"""
        path = self._file_path.text()
        if not path:
            self.log("파일 경로를 입력해주세요", "warning")
            return

        self.status("모델 로딩 중...")

        # AppContext를 통해 로드
        load_result = self.ctx.load_k_file(path)

        if load_result:
            self._load_from_context_model()
        else:
            self.log(f"모델 로드 실패: {path}", "error")
            self._status.setText("로드 실패")

    def _load_from_context_model(self):
        """AppContext의 모델에서 메쉬 데이터 생성"""
        self.status("메쉬 데이터 생성 중...")

        try:
            # MeshData 생성
            self._mesh_data = MeshData.from_parsed_model(self.ctx.model)

            # GL 위젯에 설정
            self._gl_widget.set_mesh(self._mesh_data)

            # Part 트리 설정
            part_element_counts = {
                pid: len(indices)
                for pid, indices in self._mesh_data.part_elements.items()
            }
            self._part_tree.set_parts(self._mesh_data.part_names, part_element_counts)

            # 요소 정보 위젯에 메쉬 설정
            self._element_info.set_mesh(self._mesh_data)

            # 상태 업데이트
            self._update_status()
            self.log(f"모델 로드 완료: {self.ctx.model.filename}", "info")

        except Exception as e:
            self.log(f"메쉬 데이터 생성 실패: {e}", "error")
            self._status.setText("로드 실패")
            import traceback
            traceback.print_exc()

    def _update_status(self):
        """상태바 업데이트"""
        if not self._mesh_data:
            self._status.setText("모델 없음")
            return

        node_count = len(self._mesh_data.nodes)
        elem_count = len(self._mesh_data.elements)
        part_count = len(self._mesh_data.part_elements)

        self._status.setText(
            f"Nodes: {node_count:,} | "
            f"Elements: {elem_count:,} ({self._mesh_data.element_type}) | "
            f"Parts: {part_count}"
        )

    def _on_part_visibility_changed(self, visible_parts: set):
        """Part 가시성 변경"""
        if self._gl_widget:
            self._gl_widget.set_visible_parts(visible_parts)

    def _on_gl_status(self, message: str):
        """GL 위젯 상태 메시지"""
        self.log(message, "info")

    def _on_fps_update(self, fps: float):
        """FPS 업데이트"""
        self._fps_label.setText(f"FPS: {fps:.1f}")

    def _on_element_selected(self, elem_idx: int):
        """요소 선택 이벤트"""
        self._element_info.show_element(elem_idx)
        self.log(f"요소 {elem_idx} 선택됨", "info")

    def _on_backend_changed(self, index: int):
        """Backend 변경"""
        backends = ['legacy', 'vbo', 'pyvista']
        if index < len(backends):
            backend = backends[index]
            self._gl_widget.set_backend(backend)
            self.log(f"Backend changed to: {self._gl_widget.get_backend_name()}", "info")

    def get_actions(self):
        """모듈 액션 버튼"""
        return [
            {'id': 'load', 'name': 'K-file 열기', 'icon': 'fa5s.folder-open'},
            {'id': 'reset_view', 'name': '뷰 리셋', 'icon': 'fa5s.eye'},
        ]
