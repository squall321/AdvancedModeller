"""
DOE preview renderer for semi-transparent geometry.

Renders the source part at displaced position with transparency.
"""

import numpy as np
from OpenGL.GL import *

from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.modules.model_viewer.core.camera import Camera


class DOEPreviewRenderer:
    """Renders semi-transparent source part at selected DOE position."""

    def __init__(self, mesh_data: MeshData):
        """
        Initialize preview renderer.

        Args:
            mesh_data: MeshData containing part geometry
        """
        self._mesh_data = mesh_data
        self._vertices = None
        self._colors = None
        self._displacement = (0.0, 0.0)
        self._visible = False
        self._source_part_id = None

    def set_preview(
        self,
        source_part_id: int,
        dx: float,
        dy: float,
        visible: bool = True
    ):
        """
        Set which placement to preview.

        Args:
            source_part_id: Part ID to render
            dx, dy: Displacement from original position
            visible: Whether to show preview
        """
        self._source_part_id = source_part_id
        self._displacement = (dx, dy)
        self._visible = visible

        if visible and source_part_id is not None:
            self._build_preview_geometry()
        else:
            self._vertices = None
            self._colors = None

    def _build_preview_geometry(self):
        """
        Build geometry for displaced source part.

        Steps:
        1. Extract source part vertices from mesh_data
        2. Apply displacement: vertices[:, 0] += dx, vertices[:, 1] += dy
        3. Set color to semi-transparent red: (1.0, 0.2, 0.2, 0.5)
        """
        if self._source_part_id is None:
            return

        if self._source_part_id not in self._mesh_data.part_elements:
            return

        part_id = self._source_part_id
        dx, dy = self._displacement

        elem_indices = self._mesh_data.part_elements[part_id]

        # Collect all vertices for this part
        vertices = []

        for elem_idx in elem_indices:
            node_list = self._mesh_data.elements[elem_idx]
            coords = self._mesh_data.nodes[node_list].copy()

            # Apply displacement in XY plane
            coords[:, 0] += dx
            coords[:, 1] += dy

            # For solid elements (hex8), extract exterior faces
            if len(node_list) == 8:
                # Hex faces (each face has 4 vertices)
                hex_faces = [
                    [0, 1, 2, 3],  # Bottom
                    [4, 5, 6, 7],  # Top
                    [0, 1, 5, 4],  # Front
                    [2, 3, 7, 6],  # Back
                    [0, 3, 7, 4],  # Left
                    [1, 2, 6, 5],  # Right
                ]

                # For preview, show all faces (simplified)
                for face_indices in hex_faces:
                    face_coords = coords[face_indices]
                    # Split quad into two triangles
                    vertices.append(face_coords[[0, 1, 2]])
                    vertices.append(face_coords[[0, 2, 3]])

            elif len(node_list) == 4:
                # Shell/quad element - single face
                # Two triangles
                vertices.append(coords[[0, 1, 2]])
                vertices.append(coords[[0, 2, 3]])

        if not vertices:
            self._vertices = None
            self._colors = None
            return

        # Stack all vertices
        self._vertices = np.vstack(vertices).astype(np.float32)

        # Create color array: semi-transparent red (RGBA: 1.0, 0.2, 0.2, 0.5)
        num_verts = len(self._vertices)
        self._colors = np.full((num_verts, 4), [1.0, 0.2, 0.2, 0.5], dtype=np.float32)

    def render(self, camera: Camera):
        """
        Render preview if visible.

        Args:
            camera: Camera for view/projection matrices
        """
        if not self._visible or self._vertices is None:
            return

        # Save current state
        glPushAttrib(GL_ALL_ATTRIB_BITS)

        # Enable alpha blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Disable depth write to prevent occlusion artifacts with transparency
        glDepthMask(GL_FALSE)

        # Enable depth test (read but don't write)
        glEnable(GL_DEPTH_TEST)

        # Enable smooth shading
        glShadeModel(GL_SMOOTH)

        # Enable lighting for depth perception
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        # Set material properties for semi-transparent red
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.3, 0.06, 0.06, 0.5])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [1.0, 0.2, 0.2, 0.5])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5, 0.5, 0.5, 0.5])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)

        # Render using vertex arrays
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        glVertexPointer(3, GL_FLOAT, 0, self._vertices)
        glColorPointer(4, GL_FLOAT, 0, self._colors)

        # Calculate normals for lighting (per-triangle)
        num_triangles = len(self._vertices) // 3

        for i in range(num_triangles):
            v0 = self._vertices[i * 3]
            v1 = self._vertices[i * 3 + 1]
            v2 = self._vertices[i * 3 + 2]

            # Calculate normal
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            if norm > 1e-6:
                normal = normal / norm
            else:
                normal = np.array([0, 0, 1], dtype=np.float32)

            glBegin(GL_TRIANGLES)
            glNormal3fv(normal)
            glColor4fv(self._colors[i * 3])
            glVertex3fv(self._vertices[i * 3])
            glColor4fv(self._colors[i * 3 + 1])
            glVertex3fv(self._vertices[i * 3 + 1])
            glColor4fv(self._colors[i * 3 + 2])
            glVertex3fv(self._vertices[i * 3 + 2])
            glEnd()

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        # Restore state
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)

        glPopAttrib()

    def clear(self):
        """Clear preview geometry."""
        self._vertices = None
        self._colors = None
        self._visible = False
