"""File Loader Module - K-file 로드 및 3D 미리보기

프로그램의 첫 번째 단계로 K-file을 로드하고 기본 정보를 확인
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QGroupBox, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal

from gui.modules.base import BaseModule
from gui.modules import ModuleRegistry
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget
from gui.modules.model_viewer.core.mesh_data import MeshData

try:
    import qtawesome as qta
except ImportError:
    qta = None


@ModuleRegistry.register(
    module_id="file_loader",
    name="파일 로더",
    description="K-file을 로드하고 3D 미리보기",
    icon="fa5s.folder-open",
    order=0  # 첫 번째 모듈
)
class FileLoaderModule(BaseModule):
    """K-file 로더 및 미리보기 모듈

    프로그램 시작 시 첫 번째 모듈로 사용
    K-file을 로드하고 3D 미리보기 제공
    """

    # 파일 로드 완료 시그널
    fileLoaded = Signal()

    @property
    def module_id(self) -> str:
        return "file_loader"

    def __init__(self, ctx):
        super().__init__(ctx)
        self.setWindowTitle("K-File Loader")

    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 타이틀
        title = QLabel("<h1>LaminateModeller</h1>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("K-file을 로드하여 시작하세요")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # 파일 선택 영역
        file_group = QGroupBox("K-File 선택")
        file_layout = QVBoxLayout(file_group)

        # 파일 경로 표시
        path_layout = QHBoxLayout()
        self._file_label = QLabel("파일이 선택되지 않았습니다")
        self._file_label.setStyleSheet("padding: 8px; background: #f0f0f0; border-radius: 4px;")
        path_layout.addWidget(self._file_label, 1)

        # 파일 선택 버튼
        if qta:
            browse_btn = QPushButton(qta.icon('fa5s.folder-open'), " 파일 선택")
        else:
            browse_btn = QPushButton("파일 선택")
        browse_btn.setFixedWidth(120)
        browse_btn.clicked.connect(self._browse_file)
        path_layout.addWidget(browse_btn)

        file_layout.addLayout(path_layout)
        layout.addWidget(file_group)

        # 메인 컨텐츠 - 스플리터
        splitter = QSplitter(Qt.Horizontal)

        # 좌측: 모델 정보
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(350)

        info_group = QGroupBox("모델 정보")
        info_layout = QVBoxLayout(info_group)

        self._info_text = QTextEdit()
        self._info_text.setReadOnly(True)
        self._info_text.setPlainText("K-file을 로드하면 모델 정보가 여기에 표시됩니다.")
        info_layout.addWidget(self._info_text)

        left_layout.addWidget(info_group)

        # 다음 버튼
        if qta:
            self._next_btn = QPushButton(qta.icon('fa5s.arrow-right'), " 다음: 기능 선택")
        else:
            self._next_btn = QPushButton("다음: 기능 선택")
        self._next_btn.setEnabled(False)
        self._next_btn.setStyleSheet("""
            QPushButton:enabled {
                background: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:enabled:hover {
                background: #45a049;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self._next_btn.clicked.connect(self._on_next_clicked)
        left_layout.addWidget(self._next_btn)

        splitter.addWidget(left_panel)

        # 우측: 3D 미리보기
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        preview_label = QLabel("<b>3D 미리보기</b>")
        right_layout.addWidget(preview_label)

        # 3D 뷰어 (VBO 백엔드)
        self._viewer = ModelGLWidget(backend='vbo')
        right_layout.addWidget(self._viewer, 1)

        # 뷰 컨트롤
        view_layout = QHBoxLayout()

        view_btns = [
            ("Front", self._viewer.view_front),
            ("Top", self._viewer.view_top),
            ("Right", self._viewer.view_right),
            ("Iso", self._viewer.view_isometric),
            ("Reset", self._viewer.reset_view),
        ]

        for text, callback in view_btns:
            btn = QPushButton(text)
            btn.setFixedWidth(60)
            btn.clicked.connect(callback)
            view_layout.addWidget(btn)

        view_layout.addStretch()
        right_layout.addLayout(view_layout)

        splitter.addWidget(right_panel)

        # 스플리터 비율
        splitter.setSizes([350, 650])

        layout.addWidget(splitter, 1)

        # 상태바
        self._status = QLabel("준비됨")
        self._status.setStyleSheet("padding: 4px; background: palette(alternate-base);")
        layout.addWidget(self._status)

    def _browse_file(self):
        """파일 선택 다이얼로그"""
        # 기본 디렉토리: examples
        start_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "examples"
        )
        if not os.path.exists(start_dir):
            start_dir = ""

        path, _ = QFileDialog.getOpenFileName(
            self,
            "K-file 선택",
            start_dir,
            "K-files (*.k *.key *.dyn);;All files (*.*)"
        )

        if path:
            self._load_file(path)

    def _load_file(self, filepath: str):
        """K-file 로드"""
        try:
            self._status.setText(f"로드 중: {os.path.basename(filepath)}...")

            # AppContext에 로드
            self.ctx.load_k_file(filepath)

            # 파일 경로 표시
            self._file_label.setText(filepath)
            self._file_label.setStyleSheet("padding: 8px; background: #e8f5e9; border-radius: 4px;")

            # 모델 정보 표시
            self._update_model_info()

            # 3D 미리보기
            self._update_3d_preview()

            # 다음 버튼 활성화
            self._next_btn.setEnabled(True)

            self._status.setText(f"로드 완료: {os.path.basename(filepath)}")
            self.log(f"K-file loaded: {filepath}", "success")

            # 시그널 발생
            self.fileLoaded.emit()

        except Exception as e:
            self._status.setText(f"로드 실패: {str(e)}")
            self.log(f"Failed to load K-file: {str(e)}", "error")
            self._file_label.setText("파일 로드 실패!")
            self._file_label.setStyleSheet("padding: 8px; background: #ffebee; border-radius: 4px;")

    def _update_model_info(self):
        """모델 정보 업데이트"""
        model = self.ctx.model

        info_lines = [
            "=" * 50,
            "  모델 정보",
            "=" * 50,
            "",
            f"파일: {os.path.basename(model.filepath)}",
            f"경로: {model.filepath}",
            "",
            "=" * 50,
            "  통계",
            "=" * 50,
            "",
            f"노드:    {model.node_count:,}",
            f"Shell:   {len(model.shells):,}",
            f"Solid:   {len(model.solids):,}",
            f"Beam:    {len(model.beams):,}",
            f"Part:    {model.part_count}",
            f"재료:    {len(model.materials)}",
            "",
        ]

        # Part 정보
        if model.part_count > 0:
            info_lines.extend([
                "=" * 50,
                "  Part 목록",
                "=" * 50,
                "",
            ])

            # Part별 요소 수 계산
            part_elem_count = {}
            for elem in model.shells:
                pid = elem.pid if hasattr(elem, 'pid') else None
                if pid:
                    part_elem_count[pid] = part_elem_count.get(pid, 0) + 1

            for elem in model.solids:
                pid = elem.pid if hasattr(elem, 'pid') else None
                if pid:
                    part_elem_count[pid] = part_elem_count.get(pid, 0) + 1

            # Part별 출력 (처음 10개만)
            for i, (pid, count) in enumerate(sorted(part_elem_count.items())[:10]):
                part = model.get_part_by_id(pid)
                part_name = part.title if part and hasattr(part, 'title') else "Unknown"
                info_lines.append(f"  Part {pid:3d}: {count:6,} 요소 - {part_name}")

            if len(part_elem_count) > 10:
                info_lines.append(f"  ... 외 {len(part_elem_count) - 10}개 Part")

        self._info_text.setPlainText("\n".join(info_lines))

    def _update_3d_preview(self):
        """3D 미리보기 업데이트"""
        try:
            # MeshData 생성
            mesh = MeshData.from_parsed_model(self.ctx.model)

            # 뷰어에 설정
            self._viewer.set_mesh(mesh)

            # 모든 Part 표시
            self._viewer.set_visible_parts(set(mesh.part_elements.keys()))

            # 뷰 리셋
            self._viewer.reset_view()

        except Exception as e:
            self.log(f"Failed to create 3D preview: {str(e)}", "error")

    def _on_next_clicked(self):
        """다음 버튼 클릭"""
        # 메인 윈도우에 다음 단계 알림 (아무 모듈이나 선택 가능)
        self.log("K-file 로드 완료. 왼쪽 메뉴에서 기능을 선택하세요.", "info")

    def on_activate(self):
        """모듈 활성화 시"""
        # 이미 로드된 K-file이 있으면 표시
        if self.ctx.model.is_loaded:
            self._file_label.setText(self.ctx.model.filepath)
            self._file_label.setStyleSheet("padding: 8px; background: #e8f5e9; border-radius: 4px;")
            self._update_model_info()
            self._update_3d_preview()
            self._next_btn.setEnabled(True)
            self._status.setText("모델 로드됨")
