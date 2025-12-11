"""Results Panel for Adjacent Parts Viewer

Displays detection results including adjacent parts list and 3D viewer.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QListWidget, QListWidgetItem, QPushButton,
    QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Optional, Set, Dict
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget
from gui.modules.model_viewer.core.mesh_data import MeshData
import numpy as np


class ResultsPanel(QWidget):
    """Results panel showing adjacent parts"""

    # Signals
    partSelected = Signal(int)  # User selected a part from list
    partDoubleClicked = Signal(int)  # User double-clicked part

    def __init__(self, parent=None):
        super().__init__(parent)

        self._mesh_data = None
        self._viewer = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Title
        title = QLabel("Detection Results")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        # Vertical splitter: Parts List (top) | 3D Viewer (bottom)
        splitter = QSplitter(Qt.Vertical)

        # Top: Adjacent Parts List
        parts_group = self._create_parts_group()
        splitter.addWidget(parts_group)

        # Bottom: 3D Viewer
        viewer_group = self._create_viewer_group()
        splitter.addWidget(viewer_group)

        # Set splitter ratios: Parts (1) : Viewer (12) - 3D viewer gets much more space
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 12)

        layout.addWidget(splitter)

        # Action Buttons
        actions = self._create_actions()
        layout.addLayout(actions)

    def _create_parts_group(self) -> QGroupBox:
        """Adjacent parts list group"""
        group = QGroupBox("Adjacent Parts")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # Count label
        self._count_label = QLabel("Found: 0 parts")
        self._count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._count_label)

        # Parts list
        self._parts_list = QListWidget()
        self._parts_list.setSelectionMode(QListWidget.SingleSelection)
        self._parts_list.itemClicked.connect(self._on_part_clicked)
        self._parts_list.itemDoubleClicked.connect(self._on_part_double_clicked)
        layout.addWidget(self._parts_list)

        return group

    def _create_viewer_group(self) -> QGroupBox:
        """3D Viewer group"""
        group = QGroupBox("3D View")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Create 3D viewer using VBO backend for better performance
        self._viewer = ModelGLWidget(backend='vbo')

        # Configure viewer: no edges/wireframe, only solid surfaces with lighting
        if self._viewer._renderer:
            self._viewer._renderer.set_show_edges(False)
            self._viewer._renderer.set_show_wireframe(False)
            self._viewer._renderer.set_show_solid(True)

        layout.addWidget(self._viewer)

        return group

    def _create_actions(self) -> QHBoxLayout:
        """Action buttons"""
        layout = QHBoxLayout()

        self._clear_btn = QPushButton("Clear Results")
        self._clear_btn.clicked.connect(self.clear)
        layout.addWidget(self._clear_btn)

        self._export_btn = QPushButton("Export...")
        self._export_btn.setEnabled(False)
        layout.addWidget(self._export_btn)

        return layout

    def set_results(
        self,
        source_part_id: int,
        adjacent_parts: Set[int],
        coverage: Dict[int, float],
        plane: str = "XY",
        view_direction: str = "top",
        bbox_offset: float = 5.0
    ):
        """Set detection results

        Args:
            source_part_id: Source part ID
            adjacent_parts: Set of adjacent part IDs
            coverage: Dict mapping part_id -> coverage percentage
            plane: Projection plane for camera view
            view_direction: View direction ('top' or 'bottom')
            bbox_offset: Bbox offset multiplier for in-plane filtering
        """
        # Clear previous
        self._parts_list.clear()

        # Add source part at the top with clear marker
        source_item = QListWidgetItem(f"🔴 Part {source_part_id} [SOURCE]")
        source_item.setData(Qt.UserRole, source_part_id)
        # Make it bold and red
        font = source_item.font()
        font.setBold(True)
        source_item.setFont(font)
        source_item.setForeground(QColor(255, 50, 50))  # Red text
        self._parts_list.addItem(source_item)

        # Add separator
        separator = QListWidgetItem("─" * 30)
        separator.setFlags(Qt.NoItemFlags)  # Not selectable
        separator.setForeground(QColor(128, 128, 128))  # Gray
        self._parts_list.addItem(separator)

        # Update count
        self._count_label.setText(f"Found: {len(adjacent_parts)} adjacent parts")

        # Add adjacent parts to list (sorted by coverage, descending)
        sorted_parts = sorted(
            adjacent_parts,
            key=lambda pid: coverage.get(pid, 0.0),
            reverse=True
        )

        for part_id in sorted_parts:
            cov = coverage.get(part_id, 0.0)
            item = QListWidgetItem(f"Part {part_id} ({cov:.1%} coverage)")
            item.setData(Qt.UserRole, part_id)
            self._parts_list.addItem(item)

        # Update 3D viewer
        self._update_viewer(source_part_id, adjacent_parts, plane, view_direction, bbox_offset)

        # Enable export
        self._export_btn.setEnabled(len(adjacent_parts) > 0)

    def set_mesh_data(self, mesh_data: MeshData):
        """Set mesh data for 3D viewer"""
        self._mesh_data = mesh_data
        if self._viewer and mesh_data:
            self._viewer.set_mesh(mesh_data)

    def _update_viewer(self, source_part_id: int, adjacent_parts: Set[int], plane: str, view_direction: str = "top", bbox_offset: float = 5.0):
        """Update 3D viewer to show selected parts from plane direction

        Args:
            source_part_id: Selected source part ID
            adjacent_parts: Set of adjacent part IDs
            plane: Viewing plane ('XY', 'YZ', 'ZX')
            view_direction: View direction ('top' or 'bottom')
            bbox_offset: Bbox offset multiplier
        """
        if not self._viewer or not self._mesh_data:
            return

        # Filter out occluded parts using new rules
        all_parts = {source_part_id} | adjacent_parts
        visible_parts = self._filter_occluded_parts(all_parts, plane, source_part_id, view_direction, bbox_offset)

        # ALWAYS ensure source part is visible (safety check)
        if source_part_id not in visible_parts:
            visible_parts.add(source_part_id)

        # Set colors with depth-based shading BEFORE setting visible parts
        # This ensures colors are ready when VBO is built
        self._apply_colors_with_depth(visible_parts, source_part_id, plane)

        # Set visible parts - this triggers VBO rebuild with new colors
        self._viewer.set_visible_parts(visible_parts)

        # Set camera view based on plane and direction, centered on source part
        self._set_camera_for_plane(plane, visible_parts, view_direction, source_part_id)

        self._viewer.update()

    def _apply_colors_with_depth(self, visible_parts: Set[int], source_part_id: int, plane: str):
        """Apply colors to parts with depth-based brightness modulation

        Strategy:
        - Preserve original part colors from renderer
        - Apply subtle depth-based brightness (0.7 - 1.0)
        - Source part: bright red (1.0, 0.1, 0.1) for clear visibility
        - Adjacent parts: use original color with depth shading

        Args:
            visible_parts: Set of visible part IDs
            source_part_id: The selected source part ID
            plane: Viewing plane ('XY', 'YZ', 'ZX')
        """
        if not self._viewer or not self._mesh_data:
            return

        renderer = self._viewer._renderer
        if not renderer:
            return

        # Store original colors if not already stored
        if not hasattr(self, '_original_part_colors'):
            self._original_part_colors = {}

        # Save original colors for all visible parts
        for part_id in visible_parts:
            if part_id not in self._original_part_colors:
                if part_id in renderer._part_colors:
                    self._original_part_colors[part_id] = renderer._part_colors[part_id]

        # Determine view axis (plane normal direction)
        plane_axis_map = {'XY': 2, 'YZ': 0, 'ZX': 1}  # Z, X, Y
        view_axis = plane_axis_map.get(plane, 2)

        # Calculate depth (view axis position) for each visible part
        part_depths = {}
        for part_id in visible_parts:
            if part_id not in self._mesh_data.part_elements:
                continue

            elem_indices = self._mesh_data.part_elements[part_id]
            if len(elem_indices) == 0:
                continue

            # Get center position along view axis
            all_coords = []
            for elem_idx in elem_indices:
                node_list = self._mesh_data.elements[elem_idx]
                coords = self._mesh_data.nodes[node_list]
                all_coords.append(coords)

            if all_coords:
                all_coords = np.vstack(all_coords)
                center = all_coords.mean(axis=0)
                part_depths[part_id] = center[view_axis]

        if not part_depths:
            return

        # Normalize depths to [0.7, 1.0] range for subtle brightness scaling
        min_depth = min(part_depths.values())
        max_depth = max(part_depths.values())
        depth_range = max_depth - min_depth

        if depth_range < 1e-6:
            # All parts at same depth - use full brightness
            normalized_depths = {pid: 1.0 for pid in part_depths}
        else:
            # Normalize: closer to camera (higher value) = 1.0, farther = 0.7
            normalized_depths = {
                pid: 0.7 + 0.3 * (depth - min_depth) / depth_range
                for pid, depth in part_depths.items()
            }

        # Apply colors
        for part_id in visible_parts:
            if part_id not in normalized_depths:
                continue

            # Get original color
            if part_id not in self._original_part_colors:
                continue

            orig_color = self._original_part_colors[part_id]
            depth_brightness = normalized_depths[part_id]

            if part_id == source_part_id:
                # Source part: Very bright red (almost white-red for high visibility)
                color = (1.0, 0.8, 0.8)
            else:
                # Adjacent parts: Original color with depth-based brightness
                color = tuple(c * depth_brightness for c in orig_color)

            # Set color in renderer
            renderer._part_colors[part_id] = color

    def _filter_occluded_parts(self, parts: Set[int], plane: str, source_part_id: int, view_direction: str = "top", bbox_offset: float = 5.0) -> Set[int]:
        """Filter parts based on in-plane bbox and view direction occlusion

        New Rules:
        1. In-plane filtering: Show parts if their bbox overlaps with expanded source bbox
           - Expanded bbox = source bbox extended by (source_size * bbox_offset) in each direction
           - Parts completely outside this bbox are hidden

        2. View direction occlusion: Among visible parts, hide those blocking the view
           - Top view: Hide parts ABOVE source AND overlapping source XY bbox
           - Bottom view: Hide parts BELOW source AND overlapping source XY bbox

        Args:
            parts: Set of part IDs to filter
            plane: Viewing plane ('XY', 'YZ', 'ZX')
            source_part_id: Selected source part ID
            view_direction: 'top' or 'bottom'
            bbox_offset: Bbox expansion multiplier (default 5.0)

        Returns:
            Set of visible part IDs
        """
        if not parts or not self._mesh_data:
            return parts

        # Get source part position
        if source_part_id not in self._mesh_data.part_elements:
            return parts

        source_elem_indices = self._mesh_data.part_elements[source_part_id]
        if len(source_elem_indices) == 0:
            return parts

        # Get source part center and bounds
        source_coords = []
        for elem_idx in source_elem_indices:
            node_list = self._mesh_data.elements[elem_idx]
            coords = self._mesh_data.nodes[node_list]
            source_coords.append(coords)

        if not source_coords:
            return parts

        source_coords = np.vstack(source_coords)
        source_center = source_coords.mean(axis=0)

        # Determine which axis is the viewing direction (plane normal)
        plane_axis_map = {'XY': 2, 'YZ': 0, 'ZX': 1}  # Z, X, Y
        view_axis = plane_axis_map.get(plane, 2)

        # Get in-plane axes (for bounding box calculation)
        if plane == 'XY':
            in_plane_axes = [0, 1]  # X, Y
        elif plane == 'YZ':
            in_plane_axes = [1, 2]  # Y, Z
        else:  # ZX
            in_plane_axes = [2, 0]  # Z, X

        # Calculate source part's in-plane bounding box
        source_bbox_min = np.array([source_coords[:, ax].min() for ax in in_plane_axes])
        source_bbox_max = np.array([source_coords[:, ax].max() for ax in in_plane_axes])

        source_view_pos = source_center[view_axis]

        # Get source part size in each in-plane direction
        source_size_0 = source_coords[:, in_plane_axes[0]].max() - source_coords[:, in_plane_axes[0]].min()
        source_size_1 = source_coords[:, in_plane_axes[1]].max() - source_coords[:, in_plane_axes[1]].min()

        # Calculate expanded bbox for in-plane filtering
        # Expand by (size * bbox_offset) in each direction
        expanded_bbox_min = source_bbox_min - np.array([source_size_0, source_size_1]) * bbox_offset
        expanded_bbox_max = source_bbox_max + np.array([source_size_0, source_size_1]) * bbox_offset

        print(f"\n[Occlusion Filter] ==================")
        print(f"Source part: {source_part_id}")
        print(f"Plane: {plane}, View: {view_direction}, View axis: {view_axis}")
        print(f"Source view pos (axis {view_axis}): {source_view_pos:.2f}")
        print(f"Source in-plane bbox: {source_bbox_min} ~ {source_bbox_max}")
        print(f"Expanded bbox (offset={bbox_offset}): {expanded_bbox_min} ~ {expanded_bbox_max}")
        print(f"Total parts to check: {len(parts)}")

        visible = {source_part_id}  # Source is always visible

        for part_id in parts:
            if part_id == source_part_id:
                continue

            if part_id not in self._mesh_data.part_elements:
                continue

            elem_indices = self._mesh_data.part_elements[part_id]
            if len(elem_indices) == 0:
                continue

            # Get all coordinates for this part
            all_coords = []
            for elem_idx in elem_indices:
                node_list = self._mesh_data.elements[elem_idx]
                coords = self._mesh_data.nodes[node_list]
                all_coords.append(coords)

            if not all_coords:
                continue

            all_coords = np.vstack(all_coords)

            # Get part bbox in in-plane axes
            part_bbox_min = np.array([all_coords[:, ax].min() for ax in in_plane_axes])
            part_bbox_max = np.array([all_coords[:, ax].max() for ax in in_plane_axes])
            part_view_pos = all_coords.mean(axis=0)[view_axis]

            print(f"\nPart {part_id}:")
            print(f"  Part bbox: {part_bbox_min} ~ {part_bbox_max}")
            print(f"  View pos: {part_view_pos:.2f} (source: {source_view_pos:.2f})")

            hidden = False
            reason = ""

            # Rule 1: Check if part bbox overlaps with expanded source bbox
            # A bbox overlaps if it's NOT completely outside
            # Completely outside means: part_max < expanded_min OR part_min > expanded_max
            completely_outside = np.any(part_bbox_max < expanded_bbox_min) or \
                                 np.any(part_bbox_min > expanded_bbox_max)

            if completely_outside:
                hidden = True
                reason = "Outside expanded bbox (no overlap)"
            else:
                # Rule 2: Check view direction occlusion
                # Only hide if part blocks the view AND overlaps source XY bbox
                part_overlaps_source = not (np.any(part_bbox_max < source_bbox_min) or \
                                           np.any(part_bbox_min > source_bbox_max))

                if part_overlaps_source:
                    if view_direction == 'top':
                        # Top view: Hide parts ABOVE source that overlap in XY
                        if part_view_pos > source_view_pos:
                            hidden = True
                            reason = f"ABOVE source ({part_view_pos:.2f} > {source_view_pos:.2f}) & overlaps source bbox"
                    else:  # bottom
                        # Bottom view: Hide parts BELOW source that overlap in XY
                        if part_view_pos < source_view_pos:
                            hidden = True
                            reason = f"BELOW source ({part_view_pos:.2f} < {source_view_pos:.2f}) & overlaps source bbox"

            if hidden:
                print(f"  ❌ HIDDEN: {reason}")
            else:
                print(f"  ✅ VISIBLE")
                visible.add(part_id)

        print(f"\n[Occlusion Filter] Result: {len(visible)-1} visible adjacent parts (+ 1 source)")
        print(f"[Occlusion Filter] ==================\n")
        return visible

    def _set_camera_for_plane(self, plane: str, visible_parts: Set[int], view_direction: str = "top", source_part_id: int = None):
        """Set camera to view from plane normal direction, centered on source part

        Args:
            plane: Viewing plane ('XY', 'YZ', 'ZX')
            visible_parts: Set of visible part IDs
            view_direction: View direction ('top' or 'bottom')
            source_part_id: Source part ID to center camera on
        """
        if not self._mesh_data or not visible_parts:
            return

        # Access camera directly
        camera = self._viewer._camera
        if not camera:
            return

        # Get source part center for camera target
        if source_part_id and source_part_id in self._mesh_data.part_elements:
            source_coords = []
            elem_indices = self._mesh_data.part_elements[source_part_id]
            for elem_idx in elem_indices:
                node_list = self._mesh_data.elements[elem_idx]
                coords = self._mesh_data.nodes[node_list]
                source_coords.append(coords)

            if source_coords:
                source_coords = np.vstack(source_coords)
                source_center = source_coords.mean(axis=0)
                # Set camera target to source part center
                camera.target = source_center.astype(np.float32)

        # Compute bounding box of visible parts for distance calculation
        all_coords = []
        for part_id in visible_parts:
            if part_id not in self._mesh_data.part_elements:
                continue
            elem_indices = self._mesh_data.part_elements[part_id]
            if len(elem_indices) == 0:
                continue
            for elem_idx in elem_indices:
                node_list = self._mesh_data.elements[elem_idx]
                coords = self._mesh_data.nodes[node_list]
                all_coords.append(coords)

        if not all_coords:
            return

        all_coords = np.vstack(all_coords)
        bbox_min = all_coords.min(axis=0)
        bbox_max = all_coords.max(axis=0)
        size = bbox_max - bbox_min

        # Set camera angles based on plane and view direction
        if plane == "XY":
            if view_direction == 'top':
                # View from +Z direction (top view)
                camera.elevation = 89.0  # Almost straight down
                camera.azimuth = 0.0
            else:  # bottom
                # View from -Z direction (bottom view)
                camera.elevation = -89.0  # Almost straight up
                camera.azimuth = 0.0
        elif plane == "YZ":
            if view_direction == 'top':
                # View from +X direction
                camera.elevation = 0.0
                camera.azimuth = 0.0
            else:  # bottom
                # View from -X direction
                camera.elevation = 0.0
                camera.azimuth = 180.0
        else:  # ZX
            if view_direction == 'top':
                # View from +Y direction
                camera.elevation = 0.0
                camera.azimuth = 90.0
            else:  # bottom
                # View from -Y direction
                camera.elevation = 0.0
                camera.azimuth = -90.0

        # Calculate proper distance to fit all parts in view
        # Account for FOV (45 degrees default) to ensure all parts are visible
        max_dimension = np.max(size)
        camera.distance = max_dimension * 1.5  # Tighter fit, all parts visible

    def clear(self):
        """Clear results"""
        self._parts_list.clear()
        self._count_label.setText("Found: 0 parts")
        self._export_btn.setEnabled(False)

        # Clear viewer - show all parts with default colors
        if self._viewer and self._mesh_data:
            all_parts = set(self._mesh_data.part_elements.keys())
            self._viewer.set_visible_parts(all_parts)

            # Restore original colors
            renderer = self._viewer._renderer
            if renderer and hasattr(self, '_original_part_colors'):
                # Restore all original colors
                for part_id, orig_color in self._original_part_colors.items():
                    renderer._part_colors[part_id] = orig_color

            self._viewer.update()

    def _on_part_clicked(self, item: QListWidgetItem):
        """Part item clicked"""
        part_id = item.data(Qt.UserRole)
        if part_id is not None:
            self.partSelected.emit(part_id)

    def _on_part_double_clicked(self, item: QListWidgetItem):
        """Part item double-clicked"""
        part_id = item.data(Qt.UserRole)
        if part_id is not None:
            self.partDoubleClicked.emit(part_id)

    def get_selected_part_id(self) -> Optional[int]:
        """Get currently selected part ID"""
        items = self._parts_list.selectedItems()
        if items:
            return items[0].data(Qt.UserRole)
        return None

    def get_export_button(self) -> QPushButton:
        """Get export button for signal connection"""
        return self._export_btn
