"""Advanced Laminate Module - Main module class"""
import json
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QGroupBox, QPushButton, QLineEdit, QLabel,
                                QFileDialog, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, Slot
import qtawesome as qta

from gui.modules.base import BaseModule
from gui.widgets import (FileInputWidget, PartListWidget, LayerTableWidget,
                         LayerPreviewWidget)
from core import (KFileParser, ScriptGenerator, ProcessExecutor,
                  DisplayParser, PartConfigLoader)
from models import LayerConfig


class AdvancedLaminateModule(BaseModule):
    """적층 고도화 모듈"""

    @property
    def module_id(self) -> str:
        return "advanced_laminate"

    def _setup_ui(self):
        """UI 초기화"""
        # Module-specific components
        self.k_parser = KFileParser()
        self.display_parser = DisplayParser()
        self.part_config_loader = PartConfigLoader()
        self.script_gen = None
        self.executor = ProcessExecutor(self)

        # State
        self.current_project_path = ""

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 8, 12, 8)

        # === File Input Section ===
        file_group = QGroupBox("파일 설정")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(8)

        # K file input
        self.k_file_input = FileInputWidget("K파일", "LS-DYNA Files (*.k *.key *.dyn);;All Files (*)")
        file_layout.addWidget(self.k_file_input)

        # Material source input
        self.material_input = FileInputWidget("Material", "Text Files (*.txt *.csv);;All Files (*)")
        file_layout.addWidget(self.material_input)

        # Output name + Load button
        output_layout = QHBoxLayout()
        output_icon = QLabel()
        output_icon.setPixmap(qta.icon('fa5s.save', color='#9ca3af').pixmap(20, 20))
        output_layout.addWidget(output_icon)
        output_lbl = QLabel("출력명")
        output_lbl.setFixedWidth(80)
        output_layout.addWidget(output_lbl)
        self.output_name_edit = QLineEdit()
        self.output_name_edit.setPlaceholderText("출력 파일 이름 (예: B5)")
        output_layout.addWidget(self.output_name_edit, 1)

        self.load_btn = QPushButton(qta.icon('fa5s.file-import', color='#f3f4f6'), " K파일 로드")
        self.load_btn.setObjectName("primary")
        self.load_btn.setFixedWidth(120)
        output_layout.addWidget(self.load_btn)
        file_layout.addLayout(output_layout)

        layout.addWidget(file_group)

        # === Middle Section (Parts + Editor + Preview) ===
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Parts list
        parts_group = QGroupBox("Parts")
        parts_layout = QVBoxLayout(parts_group)
        parts_layout.setContentsMargins(4, 8, 4, 4)
        self.part_list = PartListWidget()
        parts_layout.addWidget(self.part_list)
        parts_group.setMinimumWidth(320)
        parts_group.setMaximumWidth(450)
        middle_splitter.addWidget(parts_group)

        # Right side (Editor + Preview)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # Editor and Preview side by side
        editor_preview_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Layer Editor
        editor_group = QGroupBox("Layer Editor")
        editor_layout = QVBoxLayout(editor_group)
        editor_layout.setContentsMargins(4, 8, 4, 4)
        self.layer_table = LayerTableWidget()
        editor_layout.addWidget(self.layer_table)
        editor_group.setMinimumWidth(420)
        editor_preview_splitter.addWidget(editor_group)

        # Layer Preview
        preview_group = QGroupBox("Layer Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(4, 8, 4, 4)
        self.layer_preview = LayerPreviewWidget()
        preview_layout.addWidget(self.layer_preview)
        preview_group.setMinimumWidth(250)
        editor_preview_splitter.addWidget(preview_group)

        editor_preview_splitter.setSizes([600, 350])
        right_layout.addWidget(editor_preview_splitter, 1)

        middle_splitter.addWidget(right_widget)
        middle_splitter.setSizes([300, 750])

        layout.addWidget(middle_splitter, 1)

        # === Actions Section ===
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)

        self.generate_btn = QPushButton(qta.icon('fa5s.file-code', color='#f3f4f6'), " 스크립트 생성")
        self.generate_btn.setFixedHeight(40)
        actions_layout.addWidget(self.generate_btn)

        self.preview_btn = QPushButton(qta.icon('fa5s.eye', color='#f3f4f6'), " 미리보기")
        self.preview_btn.setFixedHeight(40)
        actions_layout.addWidget(self.preview_btn)

        self.run_btn = QPushButton(qta.icon('fa5s.play', color='#f3f4f6'), " KooMeshModifier 실행")
        self.run_btn.setObjectName("success")
        self.run_btn.setFixedHeight(40)
        actions_layout.addWidget(self.run_btn)

        layout.addWidget(actions_group)

        self._connect_signals()
        self._load_last_session()

    def _connect_signals(self):
        """시그널 연결"""
        self.load_btn.clicked.connect(self._load_k_file)
        self.k_file_input.fileSelected.connect(self._on_k_file_selected)
        self.material_input.fileSelected.connect(self._on_material_selected)

        self.part_list.partSelected.connect(self._on_part_selected)
        self.part_list.partToggled.connect(self._on_part_toggled)

        self.layer_table.layersChanged.connect(self._on_layers_changed)
        self.layer_table.stackSettingsChanged.connect(self._on_stack_settings_changed)
        self.layer_table.layerAdded.connect(self._on_layer_added)
        self.layer_table.layerRemoved.connect(self._on_layer_removed)
        self.layer_table.layersCopied.connect(self._on_layers_copied)
        self.layer_table.layersPasted.connect(self._on_layers_pasted)
        self.layer_table.materialChanged.connect(self._on_material_changed)
        self.layer_table.thicknessChanged.connect(self._on_thickness_changed)
        self.layer_table.layerSetChanged.connect(self._on_layer_set_changed)

        self.generate_btn.clicked.connect(self._generate_script)
        self.preview_btn.clicked.connect(self._preview_script)
        self.run_btn.clicked.connect(self._run_koomesh)

        self.executor.output.connect(lambda s: self.log(s.strip(), "info") if s.strip() else None)
        self.executor.error.connect(lambda s: self.log(s, "error"))
        self.executor.finished.connect(self._on_process_finished)

    def _load_last_session(self):
        """마지막 세션 로드"""
        last_k = self.ctx.config.get("last_k_file", "")
        last_mat = self.ctx.config.get("last_material_source", "")

        if last_k and Path(last_k).exists():
            self.k_file_input.set_path(last_k)

        if last_mat and Path(last_mat).exists():
            self.material_input.set_path(last_mat)
            self._load_materials(last_mat)

    def on_activate(self):
        """모듈 활성화"""
        self.log("적층 고도화 모듈 활성화", "info")

    def get_actions(self):
        """액션 버튼 정의"""
        return [
            {'id': 'generate', 'name': '스크립트 생성', 'icon': 'fa5s.file-code', 'primary': True},
            {'id': 'preview', 'name': '미리보기', 'icon': 'fa5s.eye'},
            {'id': 'run', 'name': 'KooMesh 실행', 'icon': 'fa5s.play', 'style': 'success'},
        ]

    # === File handling ===

    @Slot(str)
    def _on_k_file_selected(self, path: str):
        self.ctx.current_k_file = path
        name = Path(path).stem
        self.output_name_edit.setText(name)

    @Slot(str)
    def _on_material_selected(self, path: str):
        self._load_materials(path)

    def _load_materials(self, path: str):
        if self.ctx.material_db.load(path):
            self.ctx.current_material_file = path
            self.ctx.config.set("last_material_source", path)

            materials = self.ctx.material_db.get_names()
            self.layer_table.set_materials(materials)
            self.layer_preview.set_material_types(self.ctx.material_db.get_type_mapping())
            self.layer_preview.set_material_db(self.ctx.material_db)

            self.log(f"Material 로드 완료: {len(materials)}개", "success")
        else:
            self.log(f"Material 로드 실패: {path}", "error")

    @Slot()
    def _load_k_file(self):
        path = self.k_file_input.get_path()
        if not path:
            QMessageBox.warning(self, "경고", "K파일을 선택하세요.")
            return

        if not Path(path).exists():
            QMessageBox.warning(self, "경고", "K파일이 존재하지 않습니다.")
            return

        mat_path = self.material_input.get_path()
        if mat_path and not self.ctx.material_db.materials:
            self._load_materials(mat_path)

        try:
            parts_dict = self.k_parser.parse_with_names(path)

            if not parts_dict:
                part_ids = self.k_parser.parse(path)
                if not part_ids:
                    part_ids = self.k_parser.parse_quick(path)
                parts_dict = {pid: "" for pid in part_ids}

            if parts_dict:
                self.part_list.set_parts_with_names(parts_dict)
                self.ctx.config.set("last_k_file", path)
                named_count = sum(1 for name in parts_dict.values() if name)
                self.log(f"K파일 로드 완료: {len(parts_dict)} parts ({named_count} with names)", "success")
            else:
                self.log("K파일에서 Part를 찾을 수 없습니다.", "warning")
        except Exception as e:
            self.log(f"K파일 로드 실패: {e}", "error")

    # === Part/Layer handling ===

    @Slot(int)
    def _on_part_selected(self, part_id: int):
        part = self.part_list.get_part(part_id)
        if part:
            self.layer_table.set_part(
                part_id, part.layers,
                direction=part.stack_direction,
                angle=part.stack_angle
            )
            self.layer_preview.set_layers(part.layers)
            self.layer_preview.set_stack_settings(part.stack_direction, part.stack_angle)
            self.log(f"Part {part_id} 선택 (레이어: {len(part.layers)}개)", "info")

    @Slot(int, bool)
    def _on_part_toggled(self, part_id: int, enabled: bool):
        status = "활성화" if enabled else "비활성화"
        self.log(f"Part {part_id} {status}", "info")

    @Slot()
    def _on_layers_changed(self):
        part_id = self.layer_table.current_part_id
        if part_id < 0:
            return

        layers = self.layer_table.get_layers()
        part = self.part_list.get_part(part_id)
        if part:
            part.layers = layers
            part.enabled = True
            self.part_list.update_part_card(part_id)

        self.layer_preview.set_layers(layers)

    @Slot(tuple, float)
    def _on_stack_settings_changed(self, direction: tuple, angle: float):
        part_id = self.layer_table.current_part_id
        if part_id < 0:
            return

        part = self.part_list.get_part(part_id)
        if part:
            part.stack_direction = direction
            part.stack_angle = angle
            self.layer_preview.set_stack_settings(direction, angle)
            self.log(f"Part {part_id} 적층 설정: ({direction[0]},{direction[1]},{direction[2]}) {angle}°", "info")

    @Slot(str, float)
    def _on_layer_added(self, material: str, thickness: float):
        part_id = self.layer_table.current_part_id
        self.log(f"Part {part_id}: 레이어 추가 ({material}, {thickness:.3f}mm)", "info")

    @Slot(int)
    def _on_layer_removed(self, count: int):
        part_id = self.layer_table.current_part_id
        self.log(f"Part {part_id}: 레이어 {count}개 삭제", "info")

    @Slot(int)
    def _on_layers_copied(self, count: int):
        self.log(f"레이어 {count}개 복사됨", "info")

    @Slot(int)
    def _on_layers_pasted(self, count: int):
        part_id = self.layer_table.current_part_id
        self.log(f"Part {part_id}: 레이어 {count}개 붙여넣기", "info")

    @Slot(int, str)
    def _on_material_changed(self, row: int, material: str):
        part_id = self.layer_table.current_part_id
        self.log(f"Part {part_id}: 레이어 {row+1} 물성 → {material}", "info")

    @Slot(int, float)
    def _on_thickness_changed(self, row: int, thickness: float):
        part_id = self.layer_table.current_part_id
        self.log(f"Part {part_id}: 레이어 {row+1} 두께 → {thickness:.3f}mm", "info")

    @Slot(int, int)
    def _on_layer_set_changed(self, row: int, layer_set: int):
        part_id = self.layer_table.current_part_id
        self.log(f"Part {part_id}: 레이어 {row+1} 층구분 → {layer_set}", "info")

    # === Script generation ===

    @Slot()
    def _generate_script(self):
        output_name = self.output_name_edit.text().strip()
        if not output_name:
            QMessageBox.warning(self, "경고", "출력 파일명을 입력하세요.")
            return

        enabled_parts = self.part_list.get_enabled_parts()
        if not enabled_parts:
            QMessageBox.warning(self, "경고", "활성화된 Part가 없습니다.")
            return

        if not self.ctx.material_db.materials:
            QMessageBox.warning(self, "경고", "Material Source를 먼저 로드하세요.")
            return

        self.script_gen = ScriptGenerator(self.ctx.material_db)
        k_filename = Path(self.k_file_input.get_path()).name if self.k_file_input.get_path() else f"{output_name}.k"

        try:
            script = self.script_gen.generate(enabled_parts, output_name, k_filename)

            output_dir = Path(self.k_file_input.get_path()).parent if self.k_file_input.get_path() else Path.cwd()
            output_path = output_dir / f"{output_name}_display.txt"

            self.script_gen.save(script, str(output_path))
            self.log(f"스크립트 생성 완료: {output_path}", "success")
            self._last_script_path = str(output_path)
            self._last_script = script

        except Exception as e:
            self.log(f"스크립트 생성 실패: {e}", "error")

    @Slot()
    def _preview_script(self):
        if not hasattr(self, '_last_script'):
            self._generate_script()

        if hasattr(self, '_last_script'):
            from gui.dialogs.preview_dialog import PreviewDialog
            dlg = PreviewDialog(self._last_script, self)
            self.log("스크립트 미리보기 열림", "info")
            dlg.exec()

    @Slot()
    def _run_koomesh(self):
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
        self.run_btn.setEnabled(True)
        if exit_code == 0:
            self.log("실행 완료", "success")
        else:
            self.log(f"실행 완료 (exit code: {exit_code})", "warning")

    # === Project management ===

    def new_project(self):
        """새 프로젝트"""
        self.part_list.set_parts([])
        self.layer_table.set_part(-1, [])
        self.layer_preview.set_layers([])
        self.k_file_input.set_path("")
        self.output_name_edit.setText("")
        self.current_project_path = ""
        self.log("새 프로젝트 생성", "info")

    def open_project(self):
        """프로젝트 열기"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "프로젝트 열기", "",
            "Laminate Project (*.laminate);;JSON Files (*.json);;All Files (*)"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get("k_file"):
                self.k_file_input.set_path(data["k_file"])
            if data.get("material_source"):
                self.material_input.set_path(data["material_source"])
                self._load_materials(data["material_source"])
            if data.get("output_name"):
                self.output_name_edit.setText(data["output_name"])

            if data.get("parts"):
                part_ids = [p["part_id"] for p in data["parts"]]
                self.part_list.set_parts(part_ids)

                for part_data in data["parts"]:
                    part = self.part_list.get_part(part_data["part_id"])
                    if part:
                        part.enabled = part_data.get("enabled", False)
                        part.layers = [LayerConfig.from_dict(l) for l in part_data.get("layers", [])]
                        self.part_list.update_part_card(part_data["part_id"])

            self.current_project_path = filepath
            self.log(f"프로젝트 로드: {filepath}", "success")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"프로젝트를 열 수 없습니다:\n{e}")

    def save_project(self):
        """프로젝트 저장"""
        if self.current_project_path:
            self._save_project_to(self.current_project_path)
        else:
            self.save_project_as()

    def save_project_as(self):
        """다른 이름으로 저장"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "프로젝트 저장", "",
            "Laminate Project (*.laminate);;JSON Files (*.json)"
        )
        if filepath:
            if not filepath.endswith('.laminate') and not filepath.endswith('.json'):
                filepath += '.laminate'
            self._save_project_to(filepath)

    def _save_project_to(self, filepath: str):
        """파일로 저장"""
        try:
            data = {
                "version": "1.0",
                "k_file": self.k_file_input.get_path(),
                "material_source": self.material_input.get_path(),
                "output_name": self.output_name_edit.text(),
                "parts": [p.to_dict() for p in self.part_list.parts.values()]
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.current_project_path = filepath
            self.log(f"프로젝트 저장: {filepath}", "success")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")

    def import_display_file(self):
        """Display.txt 불러오기"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Display.txt 불러오기", "",
            "Display Files (*.txt);;All Files (*)"
        )
        if not filepath:
            return

        try:
            k_filename, parsed_parts = self.display_parser.parse(filepath)

            if not parsed_parts:
                QMessageBox.warning(self, "경고", "파일에서 Part 정보를 찾을 수 없습니다.")
                return

            if k_filename:
                display_dir = Path(filepath).parent
                k_path = display_dir / k_filename
                if k_path.exists():
                    self.k_file_input.set_path(str(k_path))
                    self.output_name_edit.setText(Path(k_filename).stem)

            parts_dict = {p.part_id: "" for p in parsed_parts}
            self.part_list.set_parts_with_names(parts_dict)

            for parsed_part in parsed_parts:
                part = self.part_list.get_part(parsed_part.part_id)
                if part:
                    part.enabled = True
                    part.layers = [
                        LayerConfig(
                            material_name=layer.material_name,
                            thickness=layer.thickness,
                            layer_set=layer.layer_set
                        )
                        for layer in parsed_part.layers
                    ]
                    self.part_list.update_part_card(parsed_part.part_id)

            if parsed_parts:
                first_part = self.part_list.get_part(parsed_parts[0].part_id)
                if first_part:
                    self.layer_table.set_part(parsed_parts[0].part_id, first_part.layers)
                    self.layer_preview.set_layers(first_part.layers)

            self.log(f"Display.txt 로드 완료: {len(parsed_parts)} parts", "success")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일을 불러올 수 없습니다:\n{e}")

    def import_part_config_csv(self):
        """Part 설정 CSV 불러오기"""
        if not self.part_list.parts:
            QMessageBox.warning(self, "경고", "먼저 K파일을 로드하세요.")
            return

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Part 설정 CSV 불러오기", "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not filepath:
            return

        try:
            configs = self.part_config_loader.load(filepath)

            if not configs:
                QMessageBox.warning(self, "경고", "CSV에서 설정을 찾을 수 없습니다.")
                return

            applied = 0
            skipped = 0

            for part_id, layers in configs.items():
                part = self.part_list.get_part(part_id)
                if part:
                    part.layers = layers
                    part.enabled = True
                    self.part_list.update_part_card(part_id)
                    applied += 1
                else:
                    skipped += 1

            for part_id in configs.keys():
                part = self.part_list.get_part(part_id)
                if part:
                    self.layer_table.set_part(part_id, part.layers)
                    self.layer_preview.set_layers(part.layers)
                    break

            self.log(f"CSV 로드 완료: {applied} parts 적용, {skipped} parts 스킵", "success")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"CSV 파일을 불러올 수 없습니다:\n{e}")
