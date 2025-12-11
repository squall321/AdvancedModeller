"""Package Movement DOE Module

Main module integrating detector, UI, and Model Viewer visualization.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSplitter, QMessageBox, QGroupBox,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt

from gui.modules import ModuleRegistry
from gui.modules.base import BaseModule
from .core import AdjacentPartsDetector, DetectionResult
from .widgets.control_panel import ControlPanel
from .widgets.results_panel import ResultsPanel


@ModuleRegistry.register(
    module_id="package_movement_doe",
    name="패키지 이동 DOE",
    description="Ray tracing 기반 인접 파트 검출 및 DOE",
    icon="fa5s.arrows-alt",
    order=4
)
class AdjacentPartsViewerModule(BaseModule):
    """Package Movement DOE Module

    Features:
    - Select source part
    - Choose projection plane (XY/YZ/ZX)
    - Set thickness range
    - Detect adjacent parts using ray tracing
    - Visualize results in 3D viewer
    """

    @property
    def module_id(self) -> str:
        return "package_movement_doe"

    def __init__(self, ctx):
        super().__init__(ctx)

        self._detector = None
        self._mesh_data = None
        self._current_source_part = None

        self._setup_connections()

    def _setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Title
        header = QHBoxLayout()
        title = QLabel("패키지 이동 DOE")
        title.setStyleSheet("font-weight: bold; font-size: 14pt;")
        header.addWidget(title)
        header.addStretch()

        # Source part selection label
        self._source_label = QLabel("Source Part: None")
        self._source_label.setStyleSheet("font-weight: bold; color: #2563eb;")
        header.addWidget(self._source_label)

        layout.addLayout(header)

        # Main splitter: Part List | Control Panel | Results
        splitter = QSplitter(Qt.Horizontal)

        # Left: Part List
        part_list_widget = QWidget()
        part_list_layout = QVBoxLayout(part_list_widget)
        part_list_layout.setContentsMargins(0, 0, 0, 0)

        part_list_group = QGroupBox("Part 목록")
        part_list_group_layout = QVBoxLayout(part_list_group)

        # Part list
        self._part_list = QListWidget()
        self._part_list.setToolTip("기준 Part를 선택하세요")
        part_list_group_layout.addWidget(self._part_list)

        part_list_layout.addWidget(part_list_group)
        splitter.addWidget(part_list_widget)

        # Middle: Control Panel
        self._control_panel = ControlPanel()
        splitter.addWidget(self._control_panel)

        # Right: Results Panel
        self._results_panel = ResultsPanel()
        splitter.addWidget(self._results_panel)

        # Set splitter ratios: Part List (2) : Controls (1) : Results (3)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 3)

        layout.addWidget(splitter)

    def _setup_connections(self):
        """Setup signal connections"""
        # Part list
        self._part_list.currentItemChanged.connect(self._on_part_list_selection_changed)

        # Control panel
        self._control_panel.detectRequested.connect(self._on_detect_requested)
        self._control_panel.get_auto_plane_button().clicked.connect(
            self._on_auto_plane
        )

        # Results panel
        self._results_panel.partSelected.connect(self._on_part_selected)
        self._results_panel.partDoubleClicked.connect(self._on_part_zoom)

    def on_activate(self):
        """모듈 활성화 시 호출"""
        self.log("패키지 이동 DOE 모듈 활성화", "info")

        # 이미 로드된 경우 스킵
        if self._detector is not None:
            self.log("이미 로드됨 - 스킵", "info")
            return

        # AppContext에서 모델 로드
        if self.ctx.model.is_loaded:
            self.log("AppContext에서 모델 로드 시작", "info")
            self._load_from_context()
        else:
            self.log("K-file을 먼저 로드하세요", "warning")

    def _load_from_context(self):
        """Load mesh data from AppContext"""
        try:
            self.log("MeshData 생성 중...", "info")
            # MeshData 생성
            from gui.modules.model_viewer.core.mesh_data import MeshData
            self._mesh_data = MeshData.from_parsed_model(self.ctx.model)

            if self._mesh_data is None:
                raise ValueError("Failed to create mesh data")

            self.log(f"MeshData 생성 완료: {len(self._mesh_data.part_elements)} Parts", "info")

            # Initialize detector
            self.log("Detector 초기화 중...", "info")
            self._detector = AdjacentPartsDetector(self._mesh_data)
            self.log("Detector 초기화 완료", "success")

            # Populate Part list
            self.log("Part 목록 채우는 중...", "info")
            self._populate_part_list()

            # Log completion
            num_parts = len(self._mesh_data.part_elements)
            num_nodes = len(self._mesh_data.nodes)
            num_elements = len(self._mesh_data.elements)

            self.log(f"로드됨: {num_parts} Parts, {num_nodes:,} Nodes, {num_elements:,} Elements", "success")
            self.log(f"모든 초기화 완료: {num_parts} Parts", "success")

            # Set mesh data to results panel for 3D viewer
            self._results_panel.set_mesh_data(self._mesh_data)

            self._control_panel.set_status("Part를 선택하세요")

        except Exception as e:
            import traceback
            self.log(f"모델 로드 실패: {str(e)}", "error")
            self.log(f"상세 에러:\n{traceback.format_exc()}", "error")

    def _populate_part_list(self):
        """Populate part list from mesh data"""
        self.log("Part 목록 초기화 시작", "info")
        self._part_list.clear()

        if self._mesh_data is None:
            self.log("_mesh_data가 None입니다", "error")
            return

        # Get all part IDs
        part_ids = sorted(self._mesh_data.part_elements.keys())
        self.log(f"Part ID 개수: {len(part_ids)}", "info")

        for pid in part_ids:
            # Get part info
            elem_count = len(self._mesh_data.part_elements[pid])

            # Get part name if available
            part_name = f"Part {pid}"
            if hasattr(self._mesh_data, 'part_names') and pid in self._mesh_data.part_names:
                part_name = f"Part {pid}: {self._mesh_data.part_names[pid]}"

            # Create list item
            item = QListWidgetItem(f"{part_name} ({elem_count:,} elems)")
            item.setData(Qt.UserRole, pid)  # Store part ID
            self._part_list.addItem(item)

            if pid == part_ids[0]:  # 첫 번째 Part만 로그
                self.log(f"첫 Part 추가: {part_name} ({elem_count} elems)", "info")

        self.log(f"✓ {len(part_ids)} Parts를 목록에 추가 완료", "success")

    def set_source_part(self, part_id: int):
        """Set source part for detection

        Args:
            part_id: Source part ID
        """
        if self._detector is None:
            return

        self._current_source_part = part_id
        self._source_label.setText(f"Source Part: {part_id}")
        self.log(f"Source Part 설정: {part_id}", "info")

        # Auto-suggest best plane
        suggested_plane = self._detector.suggest_best_plane(part_id)
        if suggested_plane:
            self._control_panel.set_plane(suggested_plane)
            self.log(f"자동 평면 선택: {suggested_plane}", "info")

            # Auto-set thickness range based on bounding box
            thickness_min, thickness_max = self._detector.get_auto_thickness_range(
                part_id, suggested_plane, search_multiplier=5.0
            )
            self._control_panel.set_thickness_range(thickness_min, thickness_max)
            self.log(
                f"자동 Thickness 설정: {thickness_min:.2f} ~ {thickness_max:.2f}",
                "info"
            )

            self._control_panel.set_status(
                f"평면: {suggested_plane}, Thickness: {thickness_min:.1f}~{thickness_max:.1f}"
            )

        # Enable detection
        self._control_panel.set_enabled(True)

    def _on_detect_requested(self):
        """Handle detect button clicked"""
        if self._detector is None or self._current_source_part is None:
            QMessageBox.warning(
                self,
                "No Source Part",
                "Please select a source part first"
            )
            return

        # Get parameters
        plane = self._control_panel.get_plane()
        thickness_min, thickness_max = self._control_panel.get_thickness_range()
        check_facing = self._control_panel.get_check_facing()
        ray_density = self._control_panel.get_ray_density()
        coverage_threshold = self._control_panel.get_coverage_threshold()

        self.log(f"=== Detection Parameters ===", "info")
        self.log(f"Source Part: {self._current_source_part}", "info")
        self.log(f"Plane: {plane}", "info")
        self.log(f"Thickness: {thickness_min:.2f} ~ {thickness_max:.2f}", "info")
        self.log(f"Ray Density: {ray_density}", "info")
        self.log(f"Coverage Threshold: {coverage_threshold*100:.1f}%", "info")
        self.log(f"Check Facing: {check_facing}", "info")

        # Validate
        if thickness_min >= thickness_max:
            QMessageBox.warning(
                self,
                "Invalid Range",
                "Min thickness must be less than max thickness"
            )
            return

        # Disable UI during detection
        self._control_panel.set_enabled(False)
        self._control_panel.set_status("Detecting...")

        try:
            # Run detection
            self.log("Starting detection...", "info")
            result = self._detector.find_adjacent(
                source_part_id=self._current_source_part,
                plane=plane,
                thickness_min=thickness_min,
                thickness_max=thickness_max,
                check_facing=check_facing,
                ray_density=ray_density,
                coverage_threshold=coverage_threshold,
                visualize=False,
                layer_mode=True  # Use layer mode to find all parts at same Z-height
            )

            # Log detailed results
            self.log(f"=== Detection Results ===", "success")
            self.log(f"Adjacent parts found: {len(result.adjacent_parts)}", "success")
            self.log(f"Rays cast: {result.ray_count}", "info")
            self.log(f"Total hits: {result.hit_count}", "info")

            if len(result.adjacent_parts) > 0:
                self.log(f"Part IDs: {sorted(list(result.adjacent_parts))}", "info")
                for pid in sorted(result.adjacent_parts):
                    cov = result.coverage.get(pid, 0)
                    self.log(f"  Part {pid}: {cov*100:.1f}% coverage", "info")
            else:
                self.log("No adjacent parts detected!", "warning")
                # Debug info
                self.log(f"Timing breakdown:", "info")
                for key, val in result.timing.items():
                    self.log(f"  {key}: {val:.2f} ms", "info")

            # Display results
            self._display_results(result)

            # Update status
            self._control_panel.set_status(
                f"Complete: {len(result.adjacent_parts)} parts found "
                f"in {result.timing.get('total', 0):.1f} ms"
            )

        except Exception as e:
            import traceback
            self.log(f"Detection failed: {str(e)}", "error")
            self.log(f"Traceback:\n{traceback.format_exc()}", "error")
            QMessageBox.critical(
                self,
                "Detection Error",
                f"Detection failed:\n{str(e)}"
            )
            self._control_panel.set_status("Error - See details")

        finally:
            # Re-enable UI
            self._control_panel.set_enabled(True)

    def _display_results(self, result: DetectionResult):
        """Display detection results

        Args:
            result: DetectionResult
        """
        # Log performance stats
        self.log("=== Performance Stats ===", "info")
        for key, val in result.timing.items():
            self.log(f"  {key}: {val:.2f} ms", "info")

        # Add explanations if no hits
        if not result.adjacent_parts:
            reasons = self._detector.explain_no_hits(result)
            if reasons:
                self.log("Possible reasons for no hits:", "warning")
                for r in reasons:
                    self.log(f"  - {r}", "warning")

        # Get view direction and bbox offset from control panel
        view_direction = self._control_panel.get_view_direction()
        bbox_offset = self._control_panel.get_bbox_offset()

        # Update results panel with plane, view direction, and bbox offset
        self._results_panel.set_results(
            source_part_id=result.source_part_id,
            adjacent_parts=result.adjacent_parts,
            coverage=result.coverage,
            plane=result.plane,
            view_direction=view_direction,
            bbox_offset=bbox_offset
        )

        # Visualize in 3D viewer
        self._visualize_results(result)

    def _visualize_results(self, result: DetectionResult):
        """Visualize results in Model Viewer

        Args:
            result: DetectionResult
        """
        # Check if Model Viewer is available
        if not hasattr(self.ctx, 'model_viewer') or \
           self.ctx.model_viewer is None:
            return

        # Get Model Viewer GL widget
        # (This assumes Model Viewer has been loaded)
        # For now, just log - actual integration pending

        # TODO: Highlight source part (yellow)
        # TODO: Highlight adjacent parts (colored)
        # TODO: Hide other parts or make semi-transparent
        # TODO: Fit camera to visible parts

    def _on_auto_plane(self):
        """Auto-suggest best plane"""
        if self._detector is None or self._current_source_part is None:
            return

        plane = self._detector.suggest_best_plane(self._current_source_part)
        if plane:
            self._control_panel.set_plane(plane)
            self._control_panel.set_status(f"Suggested plane: {plane}")

    def _on_part_selected(self, part_id: int):
        """Handle part selected in results

        Args:
            part_id: Selected part ID
        """
        # TODO: Highlight in 3D viewer
        pass

    def _on_part_zoom(self, part_id: int):
        """Handle part double-clicked - zoom to part

        Args:
            part_id: Part ID to zoom to
        """
        # TODO: Zoom camera to part
        pass

    def _on_part_list_selection_changed(self, current, previous):
        """Handle part list selection changed

        Args:
            current: Current QListWidgetItem
            previous: Previous QListWidgetItem
        """
        if current is None:
            return

        # Get part ID from item data
        part_id = current.data(Qt.UserRole)
        if part_id is not None:
            self.set_source_part(part_id)

    @staticmethod
    def get_module_info():
        """Return module metadata"""
        return {
            'name': '패키지 이동 DOE',
            'description': 'Ray tracing 기반 인접 파트 검출 및 DOE 분석',
            'version': '1.0.0',
            'author': 'LaminateModeller',
            'requires_kfile': True
        }
