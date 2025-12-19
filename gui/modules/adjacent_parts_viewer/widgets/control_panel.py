"""Control Panel for Adjacent Parts Viewer

Provides UI controls for plane selection, thickness range, and detection parameters.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QDoubleSpinBox,
    QCheckBox, QSlider, QSpinBox
)
from PySide6.QtCore import Qt, Signal


class ControlPanel(QWidget):
    """Control panel for adjacent parts detection"""

    # Signals
    detectRequested = Signal()  # User clicked "Detect" button
    settingsChanged = Signal()  # Any setting changed
    generatePlacementsRequested = Signal()  # User clicked "Generate Placements"
    clearPreviewRequested = Signal()  # User clicked "Clear Preview"
    exportCSVRequested = Signal()  # User clicked "Export to CSV"

    def __init__(self, parent=None):
        super().__init__(parent)

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Title
        title = QLabel("Adjacent Parts Detection")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        # Plane Selection
        plane_group = self._create_plane_group()
        layout.addWidget(plane_group)

        # Thickness Range
        thickness_group = self._create_thickness_group()
        layout.addWidget(thickness_group)

        # Detection Options
        options_group = self._create_options_group()
        layout.addWidget(options_group)

        # Detect Button
        self._detect_btn = QPushButton("Detect Adjacent Parts")
        self._detect_btn.setStyleSheet("font-weight: bold;")
        self._detect_btn.clicked.connect(self.detectRequested.emit)
        layout.addWidget(self._detect_btn)

        # DOE Placement Section
        doe_group = self._create_doe_group()
        layout.addWidget(doe_group)

        # Status Label
        self._status_label = QLabel("Ready")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        layout.addStretch()

    def _create_plane_group(self) -> QGroupBox:
        """Plane selection group"""
        group = QGroupBox("Projection Plane")
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)

        # Plane selector + Auto button in one row
        plane_layout = QHBoxLayout()
        plane_layout.addWidget(QLabel("Plane:"))

        self._plane_combo = QComboBox()
        self._plane_combo.addItems(['XY', 'YZ', 'ZX'])
        self._plane_combo.setCurrentText('XY')
        self._plane_combo.currentTextChanged.connect(self.settingsChanged.emit)
        plane_layout.addWidget(self._plane_combo)

        self._auto_plane_btn = QPushButton("Auto")
        self._auto_plane_btn.setMaximumWidth(50)
        self._auto_plane_btn.setToolTip("Automatically suggest best plane")
        plane_layout.addWidget(self._auto_plane_btn)

        layout.addLayout(plane_layout)

        # View + Bbox offset in one row
        view_offset_layout = QHBoxLayout()
        view_offset_layout.addWidget(QLabel("View:"))

        self._view_direction_combo = QComboBox()
        self._view_direction_combo.addItems(['Top', 'Bottom'])
        self._view_direction_combo.setCurrentText('Top')
        self._view_direction_combo.setToolTip("View direction")
        self._view_direction_combo.currentTextChanged.connect(self.settingsChanged.emit)
        view_offset_layout.addWidget(self._view_direction_combo)

        view_offset_layout.addWidget(QLabel("Offset:"))

        self._bbox_offset_spin = QDoubleSpinBox()
        self._bbox_offset_spin.setRange(0.0, 20.0)
        self._bbox_offset_spin.setValue(5.0)
        self._bbox_offset_spin.setSingleStep(1.0)
        self._bbox_offset_spin.setDecimals(1)
        self._bbox_offset_spin.setMinimumWidth(50)
        self._bbox_offset_spin.setToolTip("Bbox offset multiplier")
        self._bbox_offset_spin.valueChanged.connect(self.settingsChanged.emit)
        view_offset_layout.addWidget(self._bbox_offset_spin)

        layout.addLayout(view_offset_layout)

        return group

    def _create_thickness_group(self) -> QGroupBox:
        """Thickness range group"""
        group = QGroupBox("Thickness Range")
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)

        # Min and Max in one row
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Min:"))

        self._thickness_min_spin = QDoubleSpinBox()
        self._thickness_min_spin.setRange(0.0, 10000.0)
        self._thickness_min_spin.setValue(0.0)
        self._thickness_min_spin.setSingleStep(1.0)
        self._thickness_min_spin.setDecimals(1)
        self._thickness_min_spin.setMinimumWidth(60)
        self._thickness_min_spin.valueChanged.connect(self.settingsChanged.emit)
        range_layout.addWidget(self._thickness_min_spin)

        range_layout.addWidget(QLabel("Max:"))

        self._thickness_max_spin = QDoubleSpinBox()
        self._thickness_max_spin.setRange(0.1, 10000.0)
        self._thickness_max_spin.setValue(100.0)
        self._thickness_max_spin.setSingleStep(10.0)
        self._thickness_max_spin.setDecimals(1)
        self._thickness_max_spin.setMinimumWidth(60)
        self._thickness_max_spin.valueChanged.connect(self.settingsChanged.emit)
        range_layout.addWidget(self._thickness_max_spin)

        layout.addLayout(range_layout)

        return group

    def _create_options_group(self) -> QGroupBox:
        """Detection options group"""
        group = QGroupBox("Options")
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)

        # Check facing + Ray density + Coverage in compact layout
        self._check_facing_cb = QCheckBox("Check Facing")
        self._check_facing_cb.setChecked(True)
        self._check_facing_cb.setToolTip("Only include parts that face the source part")
        self._check_facing_cb.toggled.connect(self.settingsChanged.emit)
        layout.addWidget(self._check_facing_cb)

        # Ray density and Coverage in one row
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Ray:"))

        self._ray_density_spin = QDoubleSpinBox()
        self._ray_density_spin.setRange(0.01, 1.0)
        self._ray_density_spin.setValue(0.1)
        self._ray_density_spin.setSingleStep(0.05)
        self._ray_density_spin.setDecimals(2)
        self._ray_density_spin.setMinimumWidth(55)
        self._ray_density_spin.setToolTip("Ray density")
        self._ray_density_spin.valueChanged.connect(self.settingsChanged.emit)
        params_layout.addWidget(self._ray_density_spin)

        params_layout.addWidget(QLabel("Cov:"))

        self._coverage_spin = QDoubleSpinBox()
        self._coverage_spin.setRange(0.0, 1.0)
        self._coverage_spin.setValue(0.1)
        self._coverage_spin.setSingleStep(0.05)
        self._coverage_spin.setDecimals(2)
        self._coverage_spin.setMinimumWidth(55)
        self._coverage_spin.setToolTip("Coverage threshold")
        self._coverage_spin.valueChanged.connect(self.settingsChanged.emit)
        params_layout.addWidget(self._coverage_spin)

        layout.addLayout(params_layout)

        return group

    def _create_doe_group(self) -> QGroupBox:
        """DOE placement options group"""
        group = QGroupBox("DOE Placement")
        layout = QVBoxLayout(group)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)

        # DOE count + Max displacement in one row
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Count:"))

        self._doe_count_spin = QSpinBox()
        self._doe_count_spin.setRange(5, 200)
        self._doe_count_spin.setValue(20)
        self._doe_count_spin.setSingleStep(5)
        self._doe_count_spin.setMinimumWidth(50)
        self._doe_count_spin.setToolTip("Number of placements")
        params_layout.addWidget(self._doe_count_spin)

        params_layout.addWidget(QLabel("Max:"))

        self._max_displacement_spin = QDoubleSpinBox()
        self._max_displacement_spin.setRange(0.1, 1000.0)
        self._max_displacement_spin.setValue(100.0)
        self._max_displacement_spin.setSingleStep(1.0)
        self._max_displacement_spin.setDecimals(1)
        self._max_displacement_spin.setSuffix("mm")
        self._max_displacement_spin.setMinimumWidth(70)
        self._max_displacement_spin.setToolTip("Max XY displacement")
        params_layout.addWidget(self._max_displacement_spin)

        layout.addLayout(params_layout)

        # Grid step
        grid_layout = QHBoxLayout()
        grid_layout.addWidget(QLabel("Grid:"))

        self._grid_step_spin = QDoubleSpinBox()
        self._grid_step_spin.setRange(0.01, 10.0)
        self._grid_step_spin.setValue(0.1)
        self._grid_step_spin.setSingleStep(0.05)
        self._grid_step_spin.setDecimals(2)
        self._grid_step_spin.setSuffix("mm")
        self._grid_step_spin.setMinimumWidth(65)
        self._grid_step_spin.setToolTip("Grid step for auto-suggest")
        grid_layout.addWidget(self._grid_step_spin)

        # Generate button inline
        self._generate_placements_btn = QPushButton("Generate")
        self._generate_placements_btn.setEnabled(False)
        self._generate_placements_btn.setToolTip("Generate DOE placements")
        self._generate_placements_btn.clicked.connect(self.generatePlacementsRequested.emit)
        grid_layout.addWidget(self._generate_placements_btn)

        layout.addLayout(grid_layout)

        # Action buttons
        btn_layout = QHBoxLayout()

        self._clear_preview_btn = QPushButton("Clear")
        self._clear_preview_btn.setEnabled(False)
        self._clear_preview_btn.setToolTip("Clear preview")
        self._clear_preview_btn.clicked.connect(self.clearPreviewRequested.emit)
        btn_layout.addWidget(self._clear_preview_btn)

        self._export_csv_btn = QPushButton("Export")
        self._export_csv_btn.setEnabled(False)
        self._export_csv_btn.setToolTip("Export to CSV")
        self._export_csv_btn.clicked.connect(self.exportCSVRequested.emit)
        btn_layout.addWidget(self._export_csv_btn)

        layout.addLayout(btn_layout)

        return group

    # Getters
    def get_plane(self) -> str:
        """Get selected plane"""
        return self._plane_combo.currentText()

    def set_plane(self, plane: str):
        """Set plane"""
        self._plane_combo.setCurrentText(plane)

    def get_view_direction(self) -> str:
        """Get view direction ('top' or 'bottom')"""
        text = self._view_direction_combo.currentText()
        return 'top' if text == 'Top' else 'bottom'

    def get_bbox_offset(self) -> float:
        """Get bbox offset multiplier"""
        return self._bbox_offset_spin.value()

    def get_thickness_range(self) -> tuple:
        """Get (min, max) thickness"""
        return (
            self._thickness_min_spin.value(),
            self._thickness_max_spin.value()
        )

    def set_thickness_range(self, min_val: float, max_val: float):
        """Set thickness range"""
        self._thickness_min_spin.setValue(min_val)
        self._thickness_max_spin.setValue(max_val)

    def get_check_facing(self) -> bool:
        """Get facing check enabled"""
        return self._check_facing_cb.isChecked()

    def get_ray_density(self) -> float:
        """Get ray density"""
        return self._ray_density_spin.value()

    def get_coverage_threshold(self) -> float:
        """Get coverage threshold"""
        return self._coverage_spin.value()

    def set_status(self, text: str):
        """Set status label text"""
        self._status_label.setText(text)

    def set_enabled(self, enabled: bool):
        """Enable/disable all controls"""
        self._plane_combo.setEnabled(enabled)
        self._auto_plane_btn.setEnabled(enabled)
        self._thickness_min_spin.setEnabled(enabled)
        self._thickness_max_spin.setEnabled(enabled)
        self._check_facing_cb.setEnabled(enabled)
        self._ray_density_spin.setEnabled(enabled)
        self._coverage_spin.setEnabled(enabled)
        self._detect_btn.setEnabled(enabled)

    def get_auto_plane_button(self) -> QPushButton:
        """Get auto plane button for signal connection"""
        return self._auto_plane_btn

    def get_doe_count(self) -> int:
        """Get DOE sample count"""
        return self._doe_count_spin.value()

    def get_max_displacement(self) -> float:
        """Get maximum displacement in mm"""
        return self._max_displacement_spin.value()

    def get_grid_step(self) -> float:
        """Get grid step size in mm for auto-suggest"""
        return self._grid_step_spin.value()

    def enable_doe_controls(self, enabled: bool):
        """Enable/disable DOE controls"""
        self._generate_placements_btn.setEnabled(enabled)

    def enable_doe_actions(self, enabled: bool):
        """Enable/disable DOE action buttons (clear, export)"""
        self._clear_preview_btn.setEnabled(enabled)
        self._export_csv_btn.setEnabled(enabled)
