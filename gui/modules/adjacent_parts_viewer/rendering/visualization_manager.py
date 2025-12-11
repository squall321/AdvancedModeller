"""
DOE visualization manager.

Coordinates all DOE visualization layers: markers and preview geometry.
"""

from typing import List, Tuple, Optional
import numpy as np

from gui.modules.model_viewer.core.camera import Camera
from .doe_markers import DOEMarkerRenderer
from .doe_preview import DOEPreviewRenderer


class DOEVisualizationManager:
    """Manages all DOE visualization layers."""

    def __init__(self, gl_widget):
        """
        Initialize visualization manager.

        Args:
            gl_widget: OpenGL widget for rendering
        """
        self._gl_widget = gl_widget
        self._marker_renderer = DOEMarkerRenderer()

        # Get mesh data from renderer
        mesh_data = None
        if gl_widget._renderer and hasattr(gl_widget._renderer, '_mesh'):
            mesh_data = gl_widget._renderer._mesh

        self._preview_renderer = DOEPreviewRenderer(mesh_data) if mesh_data else None

        self._source_part_id = None
        self._doe_placements = []  # List of (dx, dy) tuples
        self._selected_placement_idx = None
        self._source_center = None

    def set_doe_results(
        self,
        source_part_id: int,
        placements: List[Tuple[float, float]],
        source_center: np.ndarray
    ):
        """
        Set DOE results and prepare visualization.

        Args:
            source_part_id: Source part ID
            placements: List of (dx, dy) displacement pairs
            source_center: [x, y, z] center of source part
        """
        self._source_part_id = source_part_id
        self._doe_placements = placements
        self._source_center = source_center.copy()
        self._selected_placement_idx = None

        # Calculate displaced centers for markers
        doe_centers = []
        for dx, dy in placements:
            displaced_center = source_center.copy()
            displaced_center[0] += dx
            displaced_center[1] += dy
            doe_centers.append(displaced_center)

        # Calculate marker size based on scene scale
        # Use 2% of the maximum dimension of source part bbox
        marker_size = self._calculate_marker_size(source_part_id)

        # Update marker renderer
        self._marker_renderer.set_markers(
            original_pos=source_center,
            doe_positions=doe_centers,
            marker_size=marker_size
        )

        # Hide preview initially
        self._preview_renderer.set_preview(
            source_part_id, 0.0, 0.0, visible=False
        )

        # Request redraw
        self._gl_widget.update()

    def select_placement(self, placement_idx: Optional[int]):
        """
        Select a placement option to preview.

        Args:
            placement_idx: Index into placements list, or None to clear
        """
        if not self._preview_renderer:
            return

        if placement_idx is None or placement_idx < 0 or placement_idx >= len(self._doe_placements):
            # Hide preview if invalid index
            self._preview_renderer.set_preview(
                self._source_part_id, 0.0, 0.0, visible=False
            )
            self._selected_placement_idx = None
        else:
            dx, dy = self._doe_placements[placement_idx]
            self._preview_renderer.set_preview(
                self._source_part_id, dx, dy, visible=True
            )
            self._selected_placement_idx = placement_idx

        # Request redraw
        self._gl_widget.update()

    def render(self, camera: Camera):
        """
        Render all DOE visualization layers.

        Args:
            camera: Camera for view/projection matrices
        """
        # Layer 1: Adjacent parts (rendered by main VBO renderer - not handled here)

        # Layer 2: Position markers (always visible when DOE is active)
        self._marker_renderer.render(camera)

        # Layer 3: Selected placement preview (only when selected)
        if self._preview_renderer:
            self._preview_renderer.render(camera)

    def clear(self):
        """Clear all DOE visualization."""
        self._marker_renderer.clear()
        if self._preview_renderer:
            self._preview_renderer.clear()
        self._source_part_id = None
        self._doe_placements = []
        self._selected_placement_idx = None
        self._source_center = None
        self._gl_widget.update()

    def _calculate_marker_size(self, part_id: int) -> float:
        """
        Calculate appropriate marker size based on part dimensions.

        Args:
            part_id: Part ID to base size on

        Returns:
            Marker size in world units
        """
        try:
            # Get mesh data from renderer
            if not self._gl_widget._renderer or not hasattr(self._gl_widget._renderer, '_mesh'):
                return 1.0

            mesh_data = self._gl_widget._renderer._mesh
            if not mesh_data or part_id not in mesh_data.part_elements:
                return 1.0

            elem_indices = mesh_data.part_elements[part_id]

            # Get bounding box of source part
            coords = []
            for elem_idx in elem_indices:
                node_list = mesh_data.elements[elem_idx]
                elem_coords = mesh_data.nodes[node_list]
                coords.append(elem_coords)

            coords = np.vstack(coords)

            # Calculate bbox dimensions
            bbox_min = coords.min(axis=0)
            bbox_max = coords.max(axis=0)
            bbox_size = bbox_max - bbox_min

            # Use 2% of maximum dimension as marker size
            max_dim = np.max(bbox_size)
            marker_size = max_dim * 0.02

            return max(marker_size, 0.1)  # Minimum size

        except Exception:
            return 1.0  # Default fallback

    def is_active(self) -> bool:
        """
        Check if DOE visualization is active.

        Returns:
            True if DOE results are loaded
        """
        return len(self._doe_placements) > 0

    def get_selected_placement(self) -> Optional[Tuple[float, float]]:
        """
        Get currently selected placement.

        Returns:
            (dx, dy) tuple or None if no selection
        """
        if self._selected_placement_idx is None:
            return None
        if self._selected_placement_idx >= len(self._doe_placements):
            return None
        return self._doe_placements[self._selected_placement_idx]
