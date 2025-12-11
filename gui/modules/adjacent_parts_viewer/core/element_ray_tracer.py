"""Element-based Ray Tracing for Adjacent Parts Detection

Uses actual element faces (exterior faces) instead of bounding boxes.
"""
import numpy as np
from typing import Set, List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FaceHit:
    """Ray-face intersection result"""
    part_id: int
    elem_idx: int
    distance: float
    hit_point: np.ndarray


class ElementRayTracer:
    """Ray tracing using actual element faces"""

    def __init__(self, mesh_data):
        """Initialize element ray tracer

        Args:
            mesh_data: MeshData object
        """
        self._mesh = mesh_data
        self._exterior_faces = None  # Lazy load

    def _ensure_exterior_faces(self):
        """Extract exterior faces if not already done"""
        if self._exterior_faces is None:
            print("[ElementRayTracer] Extracting exterior faces...")
            self._exterior_faces = self._mesh.extract_exterior_faces()
            total_faces = sum(len(faces) for faces in self._exterior_faces.values())
            print(f"[ElementRayTracer] Extracted {total_faces} exterior faces from {len(self._exterior_faces)} parts")

    def find_adjacent_parts(
        self,
        source_part_id: int,
        plane: str,
        thickness_max: float,
        candidate_parts: Set[int],
        ray_density: float = 0.5
    ) -> Dict[int, int]:
        """Find adjacent parts using element faces

        Args:
            source_part_id: Source part ID
            plane: 'XY', 'YZ', or 'ZX'
            thickness_max: Maximum search distance
            candidate_parts: Set of candidate part IDs
            ray_density: Rays per face (average)

        Returns:
            Dict mapping part_id -> hit_count
        """
        self._ensure_exterior_faces()

        if source_part_id not in self._exterior_faces:
            print(f"[ElementRayTracer] Source part {source_part_id} has no exterior faces!")
            return {}

        source_faces = self._exterior_faces[source_part_id]
        print(f"[ElementRayTracer] Source part has {len(source_faces)} exterior faces")

        # Get plane normal direction
        if plane == 'XY':
            ray_direction = np.array([0.0, 0.0, 1.0])
        elif plane == 'YZ':
            ray_direction = np.array([1.0, 0.0, 0.0])
        elif plane == 'ZX':
            ray_direction = np.array([0.0, 1.0, 0.0])
        else:
            return {}

        # Cast rays from source faces
        hits_by_part = {}

        # Sample rays from source faces
        for elem_idx, face_indices in source_faces:
            # Get face center as ray origin
            ray_origin = self._get_face_center(elem_idx, face_indices)
            face_normal = self._get_face_normal(elem_idx, face_indices)

            # Check if face is oriented towards the plane direction
            # (we want faces that point in +direction or -direction)
            dot_pos = np.dot(face_normal, ray_direction)
            dot_neg = np.dot(face_normal, -ray_direction)

            # Cast ray in positive direction if face points that way
            if abs(dot_pos) > 0.3:  # Face is somewhat aligned
                hit = self._cast_ray_to_candidates(
                    ray_origin, ray_direction, candidate_parts, thickness_max
                )
                if hit:
                    hits_by_part[hit.part_id] = hits_by_part.get(hit.part_id, 0) + 1

            # Cast ray in negative direction if face points that way
            if abs(dot_neg) > 0.3:
                hit = self._cast_ray_to_candidates(
                    ray_origin, -ray_direction, candidate_parts, thickness_max
                )
                if hit:
                    hits_by_part[hit.part_id] = hits_by_part.get(hit.part_id, 0) + 1

        print(f"[ElementRayTracer] Hit results: {hits_by_part}")
        return hits_by_part

    def _get_face_center(self, elem_idx: int, face_indices: List[int]) -> np.ndarray:
        """Get center point of a face

        Args:
            elem_idx: Element index
            face_indices: Face node indices (e.g., [0,1,2,3])

        Returns:
            Center point [x, y, z]
        """
        element_nodes = self._mesh.elements[elem_idx]
        face_node_indices = [element_nodes[i] for i in face_indices]

        # Get coordinates
        coords = self._mesh.nodes[face_node_indices]

        # Average = center
        return np.mean(coords, axis=0)

    def _get_face_normal(self, elem_idx: int, face_indices: List[int]) -> np.ndarray:
        """Get normal vector of a face

        Args:
            elem_idx: Element index
            face_indices: Face node indices

        Returns:
            Normal vector (unit)
        """
        element_nodes = self._mesh.elements[elem_idx]
        face_node_indices = [element_nodes[i] for i in face_indices]

        # Get coordinates of first 3 nodes
        coords = self._mesh.nodes[face_node_indices[:3]]

        # Compute normal using cross product
        v1 = coords[1] - coords[0]
        v2 = coords[2] - coords[0]
        normal = np.cross(v1, v2)

        # Normalize
        norm = np.linalg.norm(normal)
        if norm > 1e-10:
            return normal / norm
        else:
            return np.array([0.0, 0.0, 1.0])

    def _cast_ray_to_candidates(
        self,
        ray_origin: np.ndarray,
        ray_direction: np.ndarray,
        candidate_parts: Set[int],
        max_distance: float
    ) -> Optional[FaceHit]:
        """Cast a ray and find closest intersection with candidate parts

        Args:
            ray_origin: Ray start point
            ray_direction: Ray direction (unit vector)
            candidate_parts: Part IDs to test
            max_distance: Maximum distance

        Returns:
            FaceHit if intersection found, None otherwise
        """
        closest_hit = None
        closest_distance = max_distance

        # Test each candidate part
        for part_id in candidate_parts:
            if part_id not in self._exterior_faces:
                continue

            # Test each face of this part
            for elem_idx, face_indices in self._exterior_faces[part_id]:
                hit = self._ray_face_intersection(
                    ray_origin, ray_direction, elem_idx, face_indices, max_distance, part_id
                )

                if hit and hit.distance < closest_distance:
                    closest_distance = hit.distance
                    closest_hit = hit

        return closest_hit

    def _ray_face_intersection(
        self,
        ray_origin: np.ndarray,
        ray_direction: np.ndarray,
        elem_idx: int,
        face_indices: List[int],
        max_distance: float,
        part_id: int
    ) -> Optional[FaceHit]:
        """Test ray-face intersection using Möller-Trumbore algorithm

        Args:
            ray_origin: Ray origin
            ray_direction: Ray direction
            elem_idx: Element index
            face_indices: Face node indices
            max_distance: Max distance
            part_id: Part ID (for FaceHit)

        Returns:
            FaceHit if hit, None otherwise
        """
        element_nodes = self._mesh.elements[elem_idx]
        face_node_indices = [element_nodes[i] for i in face_indices]

        # Get face coordinates
        coords = self._mesh.nodes[face_node_indices]

        # For quad faces, split into two triangles
        if len(coords) == 4:
            # Triangle 1: [0, 1, 2]
            hit = self._ray_triangle_intersection(
                ray_origin, ray_direction, coords[0], coords[1], coords[2], max_distance, part_id, elem_idx
            )
            if hit is not None:
                return hit

            # Triangle 2: [0, 2, 3]
            hit = self._ray_triangle_intersection(
                ray_origin, ray_direction, coords[0], coords[2], coords[3], max_distance, part_id, elem_idx
            )
            if hit is not None:
                return hit

        elif len(coords) == 3:
            # Already a triangle
            hit = self._ray_triangle_intersection(
                ray_origin, ray_direction, coords[0], coords[1], coords[2], max_distance, part_id, elem_idx
            )
            if hit is not None:
                return hit

        return None

    def _ray_triangle_intersection(
        self,
        ray_origin: np.ndarray,
        ray_direction: np.ndarray,
        v0: np.ndarray,
        v1: np.ndarray,
        v2: np.ndarray,
        max_distance: float,
        part_id: int,
        elem_idx: int
    ) -> Optional[FaceHit]:
        """Möller-Trumbore ray-triangle intersection

        Args:
            ray_origin: Ray origin
            ray_direction: Ray direction
            v0, v1, v2: Triangle vertices
            max_distance: Max distance
            part_id: Part ID
            elem_idx: Element index

        Returns:
            FaceHit if hit, None otherwise
        """
        epsilon = 1e-6

        # Edges
        edge1 = v1 - v0
        edge2 = v2 - v0

        # Begin calculating determinant
        h = np.cross(ray_direction, edge2)
        a = np.dot(edge1, h)

        # Ray parallel to triangle?
        if abs(a) < epsilon:
            return None

        f = 1.0 / a
        s = ray_origin - v0
        u = f * np.dot(s, h)

        # Check barycentric coordinate u
        if u < 0.0 or u > 1.0:
            return None

        q = np.cross(s, edge1)
        v = f * np.dot(ray_direction, q)

        # Check barycentric coordinate v
        if v < 0.0 or u + v > 1.0:
            return None

        # Calculate t (distance along ray)
        t = f * np.dot(edge2, q)

        # Check if intersection is in valid range
        if t > epsilon and t < max_distance:
            hit_point = ray_origin + t * ray_direction
            return FaceHit(
                part_id=part_id,
                elem_idx=elem_idx,
                distance=t,
                hit_point=hit_point
            )

        return None
