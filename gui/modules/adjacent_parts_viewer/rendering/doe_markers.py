"""
DOE marker renderer for position visualization.

Renders position markers (spheres) for original and DOE placement positions.
"""

from typing import List
import numpy as np
from OpenGL.GL import *

from gui.modules.model_viewer.core.camera import Camera


class DOEMarkerRenderer:
    """Renders position markers for original and DOE placements."""

    def __init__(self):
        """Initialize marker renderer."""
        self._vbo = None
        self._positions = np.array([])
        self._colors = np.array([])
        self._count = 0
        self._marker_size = 1.0

    def set_markers(
        self,
        original_pos: np.ndarray,
        doe_positions: List[np.ndarray],
        marker_size: float = 1.0
    ):
        """
        Set marker positions and colors.

        Args:
            original_pos: [x, y, z] center of source part at original location
            doe_positions: List of [x, y, z] centers at each DOE displaced location
            marker_size: Size multiplier for markers
        """
        if original_pos is None or len(doe_positions) == 0:
            self._positions = np.array([])
            self._colors = np.array([])
            self._count = 0
            self._cleanup_vbo()
            return

        self._marker_size = marker_size

        # Build position and color arrays
        positions = []
        colors = []

        # Original position marker - BLACK
        positions.append(original_pos)
        colors.append([0.0, 0.0, 0.0, 1.0])  # Black, opaque

        # DOE placement markers - DARK RED
        for doe_pos in doe_positions:
            positions.append(doe_pos)
            colors.append([0.6, 0.0, 0.0, 1.0])  # Dark red, opaque

        self._positions = np.array(positions, dtype=np.float32)
        self._colors = np.array(colors, dtype=np.float32)
        self._count = len(positions)

        self._build_vbo()

    def _build_vbo(self):
        """Build VBO for marker rendering using sphere geometry."""
        if self._count == 0:
            return

        # Generate sphere geometry for instancing
        # Simple icosphere or UV sphere
        sphere_verts, sphere_colors = self._generate_sphere_geometry()

        # Store for rendering
        self._sphere_verts = sphere_verts
        self._sphere_vert_count = len(sphere_verts)

    def _generate_sphere_geometry(self) -> tuple:
        """
        Generate simple sphere geometry.

        Returns:
            Tuple of (vertices, colors) for a unit sphere
        """
        # Simple UV sphere with 16 segments
        segments = 16
        rings = 12

        vertices = []

        for i in range(rings + 1):
            theta = i * np.pi / rings
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)

            for j in range(segments + 1):
                phi = j * 2 * np.pi / segments
                sin_phi = np.sin(phi)
                cos_phi = np.cos(phi)

                x = sin_theta * cos_phi
                y = sin_theta * sin_phi
                z = cos_theta

                vertices.append([x, y, z])

        vertices = np.array(vertices, dtype=np.float32)

        # Generate triangle indices
        indices = []
        for i in range(rings):
            for j in range(segments):
                first = i * (segments + 1) + j
                second = first + segments + 1

                indices.extend([first, second, first + 1])
                indices.extend([second, second + 1, first + 1])

        self._sphere_indices = np.array(indices, dtype=np.uint32)

        return vertices, None

    def render(self, camera: Camera):
        """
        Render all markers.

        Args:
            camera: Camera for view/projection matrices
        """
        if self._count == 0 or not hasattr(self, '_sphere_verts'):
            return

        # Save current state
        glPushAttrib(GL_ALL_ATTRIB_BITS)

        # Enable depth test
        glEnable(GL_DEPTH_TEST)

        # For each marker, render a sphere at that position with that color
        for idx in range(self._count):
            pos = self._positions[idx]
            color = self._colors[idx]

            # Set color
            glColor4fv(color)

            # Calculate marker size based on whether it's original (larger) or DOE (smaller)
            if idx == 0:
                # Original position - larger (5% of view size)
                scale = self._marker_size * 2.0
            else:
                # DOE positions - smaller (3% of view size)
                scale = self._marker_size * 1.2

            glPushMatrix()

            # Translate to marker position
            glTranslatef(pos[0], pos[1], pos[2])

            # Scale sphere
            glScalef(scale, scale, scale)

            # Render sphere using immediate mode (simple but works)
            self._render_sphere_immediate()

            glPopMatrix()

        # Restore state
        glPopAttrib()

    def _render_sphere_immediate(self):
        """Render sphere using immediate mode for simplicity."""
        if not hasattr(self, '_sphere_verts') or not hasattr(self, '_sphere_indices'):
            return

        # Use vertex arrays for better performance than pure immediate mode
        glEnableClientState(GL_VERTEX_ARRAY)

        glVertexPointer(3, GL_FLOAT, 0, self._sphere_verts)
        glDrawElements(GL_TRIANGLES, len(self._sphere_indices), GL_UNSIGNED_INT, self._sphere_indices)

        glDisableClientState(GL_VERTEX_ARRAY)

    def _cleanup_vbo(self):
        """Clean up VBO resources."""
        if self._vbo is not None:
            # VBO cleanup if we were using VBOs
            pass
        self._vbo = None

    def clear(self):
        """Clear all markers."""
        self._positions = np.array([])
        self._colors = np.array([])
        self._count = 0
        self._cleanup_vbo()
