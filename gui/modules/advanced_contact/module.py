"""Advanced Contact Module - Main module class"""
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QGroupBox, QPushButton, QLabel,
                                QStackedWidget, QFileDialog,
                                QMessageBox)
from PySide6.QtCore import Qt, Slot
import qtawesome as qta

from gui.modules.base import BaseModule
from gui.widgets import FileInputWidget
from .methods import CONTACT_METHODS
from core import ProcessExecutor


class AdvancedContactModule(BaseModule):
    """접촉 고도화 모듈"""

    @property
    def module_id(self) -> str:
        return "advanced_contact"

    def _setup_ui(self):
        """UI 초기화"""
        self.executor = ProcessExecutor(self)
        self._method_widgets = {}
        self._current_method_id = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 8, 12, 8)

        # === 파일 설정 ===
        file_group = QGroupBox("파일 설정")
        file_layout = QVBoxLayout(file_group)

        self.k_file_input = FileInputWidget("K파일", "LS-DYNA Files (*.k *.key *.dyn);;All Files (*)")
        file_layout.addWidget(self.k_file_input)

        layout.addWidget(file_group)

        # === 메소드 옵션 영역 ===
        self.options_group = QGroupBox("옵션")
        options_layout = QVBoxLayout(self.options_group)

        # 메소드별 옵션 스택
        self.method_stack = QStackedWidget()
        for method_id, method_cls in CONTACT_METHODS.items():
            widget = method_cls(self.ctx)
            widget.logMessage.connect(self.log)
            self._method_widgets[method_id] = widget
            self.method_stack.addWidget(widget)
        options_layout.addWidget(self.method_stack, 1)

        layout.addWidget(self.options_group, 1)

        # === 액션 버튼 ===
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)

        self.generate_btn = QPushButton(qta.icon('fa5s.file-code', color='#f3f4f6'), " 스크립트 생성")
        self.generate_btn.setFixedHeight(40)
        self.generate_btn.clicked.connect(self._generate_script)
        actions_layout.addWidget(self.generate_btn)

        self.preview_btn = QPushButton(qta.icon('fa5s.eye', color='#f3f4f6'), " 미리보기")
        self.preview_btn.setFixedHeight(40)
        self.preview_btn.clicked.connect(self._preview_script)
        actions_layout.addWidget(self.preview_btn)

        self.run_btn = QPushButton(qta.icon('fa5s.play', color='#f3f4f6'), " KooMeshModifier 실행")
        self.run_btn.setObjectName("success")
        self.run_btn.setFixedHeight(40)
        self.run_btn.clicked.connect(self._run_koomesh)
        actions_layout.addWidget(self.run_btn)

        layout.addWidget(actions_group)

        # Executor 시그널 연결
        self.executor.output.connect(lambda s: self.log(s.strip(), "info") if s.strip() else None)
        self.executor.error.connect(lambda s: self.log(s, "error"))
        self.executor.finished.connect(self._on_process_finished)

        # 첫 번째 메소드 선택 (기본값)
        if CONTACT_METHODS:
            first_method = next(iter(CONTACT_METHODS.keys()))
            self.select_method(first_method)

    def on_activate(self):
        """모듈 활성화"""
        self.log("접촉 고도화 모듈 활성화", "info")

    def select_method(self, method_id: str):
        """메소드 선택 (사이드바에서 호출)"""
        if method_id not in self._method_widgets:
            self.log(f"알 수 없는 메소드: {method_id}", "error")
            return

        self._current_method_id = method_id
        widget = self._method_widgets[method_id]
        self.method_stack.setCurrentWidget(widget)

        # 옵션 그룹 제목 업데이트
        method_name = widget.method_name
        self.options_group.setTitle(f"옵션 - {method_name}")
        self.log(f"메소드 선택: {method_name}", "info")

    def get_actions(self):
        """액션 버튼 정의"""
        return [
            {'id': 'generate', 'name': '스크립트 생성', 'icon': 'fa5s.file-code', 'primary': True},
            {'id': 'preview', 'name': '미리보기', 'icon': 'fa5s.eye'},
            {'id': 'run', 'name': 'KooMesh 실행', 'icon': 'fa5s.play', 'style': 'success'},
        ]

    def _get_current_method(self):
        """현재 선택된 메소드 위젯 반환"""
        if self._current_method_id:
            return self._method_widgets.get(self._current_method_id)
        return None

    @Slot()
    def _generate_script(self):
        """스크립트 생성"""
        k_path = self.k_file_input.get_path()
        if not k_path:
            QMessageBox.warning(self, "경고", "K파일을 선택하세요.")
            return

        if not Path(k_path).exists():
            QMessageBox.warning(self, "경고", "K파일이 존재하지 않습니다.")
            return

        method = self._get_current_method()
        if not method:
            QMessageBox.warning(self, "경고", "메소드가 선택되지 않았습니다.")
            return

        # 검증
        is_valid, error = method.validate()
        if not is_valid:
            QMessageBox.warning(self, "경고", error)
            return

        try:
            k_filename = Path(k_path).name
            script = method.generate_script(k_filename)

            # 저장
            output_dir = Path(k_path).parent
            output_name = f"{Path(k_path).stem}_{method.method_id}_display.txt"
            output_path = output_dir / output_name

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(script)

            self._last_script = script
            self._last_script_path = str(output_path)

            self.log(f"스크립트 생성 완료: {output_path}", "success")

        except Exception as e:
            self.log(f"스크립트 생성 실패: {e}", "error")

    @Slot()
    def _preview_script(self):
        """스크립트 미리보기"""
        if not hasattr(self, '_last_script'):
            self._generate_script()

        if hasattr(self, '_last_script'):
            from gui.dialogs.preview_dialog import PreviewDialog
            dlg = PreviewDialog(self._last_script, self)
            self.log("스크립트 미리보기 열림", "info")
            dlg.exec()

    @Slot()
    def _run_koomesh(self):
        """KooMeshModifier 실행"""
        if not hasattr(self, '_last_script_path'):
            self._generate_script()

        if not hasattr(self, '_last_script_path'):
            return

        koomesh_path = self.ctx.config.get("koomesh_path", "")
        self.log("KooMeshModifier 실행 중...", "process")

        self.run_btn.setEnabled(False)
        self.executor.run(self._last_script_path, koomesh_path if koomesh_path else None)

    @Slot(int)
    def _on_process_finished(self, exit_code: int):
        """프로세스 완료"""
        self.run_btn.setEnabled(True)
        if exit_code == 0:
            self.log("실행 완료", "success")
        else:
            self.log(f"실행 완료 (exit code: {exit_code})", "warning")
