"""Simple and Robust Adjacent Parts Detector

핵심 아이디어:
1. Source part의 모든 exterior face 노드들 수집
2. 각 노드에서 평면의 수직 방향으로 ray 발사 (양방향)
3. Candidate parts의 모든 exterior face와 충돌 검사
4. 충돌하면 → adjacent part
"""
import numpy as np
from typing import Set, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class SimpleHit:
    """Simple hit result"""
    part_id: int
    distance: float


class SimpleAdjacentDetector:
    """Simple, robust detector using node-based ray casting"""

    def __init__(self, mesh_data):
        self._mesh = mesh_data
        self._exterior_faces = None

    def _ensure_exterior_faces(self):
        """Extract exterior faces if needed"""
        if self._exterior_faces is None:
            print("[SimpleDetector] Extracting exterior faces...")
            self._exterior_faces = self._mesh.extract_exterior_faces()
            total = sum(len(f) for f in self._exterior_faces.values())
            print(f"[SimpleDetector] Extracted {total} exterior faces")

    def find_adjacent(
        self,
        source_part_id: int,
        plane: str,
        candidate_parts: Set[int],
        max_distance: float
    ) -> Dict[int, int]:
        """Find adjacent parts

        Args:
            source_part_id: Source part
            plane: 'XY', 'YZ', or 'ZX'
            candidate_parts: Candidates to test
            max_distance: Max search distance

        Returns:
            {part_id: hit_count}
        """
        self._ensure_exterior_faces()

        if source_part_id not in self._exterior_faces:
            print(f"[SimpleDetector] Source part {source_part_id} has no exterior faces")
            return {}

        # Get ray direction
        if plane == 'XY':
            ray_dir = np.array([0.0, 0.0, 1.0])
        elif plane == 'YZ':
            ray_dir = np.array([1.0, 0.0, 0.0])
        elif plane == 'ZX':
            ray_dir = np.array([0.0, 1.0, 0.0])
        else:
            return {}

        print(f"[SimpleDetector] Ray direction: {ray_dir}")

        # Collect all unique nodes from source part's exterior faces
        source_nodes = self._get_part_face_nodes(source_part_id)
        print(f"[SimpleDetector] Source part has {len(source_nodes)} unique face nodes")

        # Sample nodes (if too many)
        if len(source_nodes) > 500:
            import random
            source_nodes = random.sample(list(source_nodes), 500)
            print(f"[SimpleDetector] Sampled to {len(source_nodes)} nodes")

        # Get node coordinates
        ray_origins = self._mesh.nodes[list(source_nodes)]

        # Cast rays and count hits
        hits_by_part = {}

        for i, origin in enumerate(ray_origins):
            if i % 100 == 0:
                print(f"[SimpleDetector] Processing ray {i}/{len(ray_origins)}")

            # Cast in both directions
            for direction in [ray_dir, -ray_dir]:
                hit = self._cast_ray_simple(
                    origin, direction, candidate_parts, max_distance
                )
                if hit:
                    hits_by_part[hit.part_id] = hits_by_part.get(hit.part_id, 0) + 1

        print(f"[SimpleDetector] Hits: {hits_by_part}")
        return hits_by_part

    def _get_part_face_nodes(self, part_id: int) -> Set[int]:
        """Get all unique node indices from exterior faces

        Args:
            part_id: Part ID

        Returns:
            Set of node indices
        """
        if part_id not in self._exterior_faces:
            return set()

        node_indices = set()
        for elem_idx, face_indices in self._exterior_faces[part_id]:
            element_nodes = self._mesh.elements[elem_idx]
            for fi in face_indices:
                node_indices.add(element_nodes[fi])

        return node_indices

    def _cast_ray_simple(
        self,
        origin: np.ndarray,
        direction: np.ndarray,
        candidate_parts: Set[int],
        max_distance: float
    ) -> SimpleHit:
        """Cast a ray and find closest hit

        Args:
            origin: Ray origin
            direction: Ray direction
            candidate_parts: Parts to test
            max_distance: Max distance

        Returns:
            SimpleHit if hit, None otherwise
        """
        closest_hit = None
        closest_dist = max_distance

        for part_id in candidate_parts:
            if part_id not in self._exterior_faces:
                continue

            # Test each face
            for elem_idx, face_indices in self._exterior_faces[part_id]:
                # Get face vertices
                element_nodes = self._mesh.elements[elem_idx]
                face_node_indices = [element_nodes[i] for i in face_indices]
                face_coords = self._mesh.nodes[face_node_indices]

                # Test ray-face intersection
                dist = self._ray_polygon_intersection(
                    origin, direction, face_coords, max_distance
                )

                if dist is not None and dist < closest_dist:
                    closest_dist = dist
                    closest_hit = SimpleHit(part_id, dist)

        return closest_hit

    def _ray_polygon_intersection(
        self,
        origin: np.ndarray,
        direction: np.ndarray,
        vertices: np.ndarray,
        max_distance: float
    ) -> float:
        """Test ray-polygon intersection

        Args:
            origin: Ray origin
            direction: Ray direction (unit)
            vertices: Polygon vertices (N x 3)
            max_distance: Max distance

        Returns:
            Distance if hit, None otherwise
        """
        if len(vertices) < 3:
            return None

        # For quad, split into 2 triangles
        if len(vertices) == 4:
            # Triangle 1
            dist = self._ray_triangle_intersection_simple(
                origin, direction,
                vertices[0], vertices[1], vertices[2],
                max_distance
            )
            if dist is not None:
                return dist

            # Triangle 2
            dist = self._ray_triangle_intersection_simple(
                origin, direction,
                vertices[0], vertices[2], vertices[3],
                max_distance
            )
            return dist

        # Triangle
        return self._ray_triangle_intersection_simple(
            origin, direction,
            vertices[0], vertices[1], vertices[2],
            max_distance
        )

    def _ray_triangle_intersection_simple(
        self,
        origin: np.ndarray,
        direction: np.ndarray,
        v0: np.ndarray,
        v1: np.ndarray,
        v2: np.ndarray,
        max_distance: float
    ) -> float:
        """Möller-Trumbore ray-triangle intersection

        Returns distance if hit, None otherwise
        """
        epsilon = 1e-8

        edge1 = v1 - v0
        edge2 = v2 - v0

        h = np.cross(direction, edge2)
        a = np.dot(edge1, h)

        # Ray parallel to triangle
        if abs(a) < epsilon:
            return None

        f = 1.0 / a
        s = origin - v0
        u = f * np.dot(s, h)

        if u < -epsilon or u > 1.0 + epsilon:
            return None

        q = np.cross(s, edge1)
        v = f * np.dot(direction, q)

        if v < -epsilon or u + v > 1.0 + epsilon:
            return None

        # Distance
        t = f * np.dot(edge2, q)

        # Check range (allow small negative for surface hits)
        if t > -epsilon and t < max_distance:
            return abs(t)

        return None
