"""Surface Normal Analysis for Facing Validation

Computes part surface normals to verify parts actually face each other.
"""
import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class SurfaceNormal:
    """Surface normal information"""
    direction: np.ndarray  # Unit vector
    confidence: float  # 0-1, based on variance


class SurfaceAnalyzer:
    """Analyzes surface normals to determine if parts face each other"""

    def __init__(self, mesh_data):
        """Initialize surface analyzer

        Args:
            mesh_data: MeshData object
        """
        self._mesh = mesh_data
        self._normal_cache: Dict[tuple, SurfaceNormal] = {}

    def compute_part_normal(
        self,
        part_id: int,
        plane: Optional[str] = None
    ) -> Optional[SurfaceNormal]:
        """Compute average surface normal for a part

        Args:
            part_id: Part ID
            plane: If specified, compute normal for projection to this plane

        Returns:
            SurfaceNormal with direction and confidence
        """
        cache_key = (part_id, plane)
        if cache_key in self._normal_cache:
            return self._normal_cache[cache_key]

        # Get all elements in this part
        element_normals = []

        # Get element indices for this part
        if part_id not in self._mesh.part_elements:
            return None

        elem_indices = self._mesh.part_elements[part_id]

        for elem_idx in elem_indices:
            # Compute element normal
            normal = self._compute_element_normal(elem_idx)
            if normal is not None:
                element_normals.append(normal)

        if not element_normals:
            return None

        element_normals = np.array(element_normals)

        # Compute average normal
        avg_normal = np.mean(element_normals, axis=0)

        # Normalize
        norm = np.linalg.norm(avg_normal)
        if norm < 1e-10:
            return None

        avg_normal = avg_normal / norm

        # Compute confidence based on variance
        # Low variance = high confidence (consistent normal direction)
        variances = np.var(element_normals, axis=0)
        confidence = 1.0 / (1.0 + np.sum(variances))

        result = SurfaceNormal(avg_normal, confidence)
        self._normal_cache[cache_key] = result

        return result

    def _compute_element_normal(
        self,
        elem_idx: int
    ) -> Optional[np.ndarray]:
        """Compute normal for a single element"""
        # Get node indices for this element
        node_indices = self._mesh.elements[elem_idx]

        if len(node_indices) < 3:
            return None

        # Get first 3 nodes to form triangle
        # nodes is (N, 3) numpy array
        p0 = self._mesh.nodes[node_indices[0]]
        p1 = self._mesh.nodes[node_indices[1]]
        p2 = self._mesh.nodes[node_indices[2]]

        # Cross product to get normal
        v1 = p1 - p0
        v2 = p2 - p0

        normal = np.cross(v1, v2)

        # Normalize
        norm = np.linalg.norm(normal)
        if norm < 1e-10:
            return None

        return normal / norm

    def check_facing(
        self,
        source_part_id: int,
        target_part_id: int,
        plane: Optional[str] = None,
        threshold: float = -0.5
    ) -> bool:
        """Check if two parts face each other

        Args:
            source_part_id: Source part
            target_part_id: Target part
            plane: Optional plane constraint
            threshold: Dot product threshold (<0 means opposite directions)

        Returns:
            True if parts face each other
        """
        source_normal = self.compute_part_normal(source_part_id, plane)
        target_normal = self.compute_part_normal(target_part_id, plane)

        if source_normal is None or target_normal is None:
            # Can't determine - assume facing
            return True

        # Dot product of normals
        # < 0 means opposite directions (facing)
        # > 0 means same direction (not facing)
        dot = np.dot(source_normal.direction, target_normal.direction)

        return dot < threshold

    def get_dominant_plane_normal(
        self,
        part_id: int
    ) -> Optional[str]:
        """Determine which plane (XY/YZ/ZX) the part is most aligned with

        Useful for suggesting best plane for adjacent part detection.

        Args:
            part_id: Part ID

        Returns:
            'XY', 'YZ', or 'ZX'
        """
        normal = self.compute_part_normal(part_id)
        if normal is None:
            return None

        # Check alignment with plane normals
        # XY plane: normal = [0, 0, 1]
        # YZ plane: normal = [1, 0, 0]
        # ZX plane: normal = [0, 1, 0]

        abs_normal = np.abs(normal.direction)
        dominant_axis = np.argmax(abs_normal)

        if dominant_axis == 0:
            return 'YZ'
        elif dominant_axis == 1:
            return 'ZX'
        else:
            return 'XY'

    def compute_angle_between_parts(
        self,
        part_id_1: int,
        part_id_2: int
    ) -> Optional[float]:
        """Compute angle between part normals in degrees

        Args:
            part_id_1: First part
            part_id_2: Second part

        Returns:
            Angle in degrees (0-180)
        """
        normal1 = self.compute_part_normal(part_id_1)
        normal2 = self.compute_part_normal(part_id_2)

        if normal1 is None or normal2 is None:
            return None

        # Dot product = cos(angle)
        dot = np.dot(normal1.direction, normal2.direction)

        # Clamp to [-1, 1] to avoid numerical issues
        dot = np.clip(dot, -1.0, 1.0)

        angle_rad = np.arccos(dot)
        angle_deg = np.degrees(angle_rad)

        return angle_deg

    def clear_cache(self):
        """Clear normal cache (call when mesh changes)"""
        self._normal_cache.clear()
