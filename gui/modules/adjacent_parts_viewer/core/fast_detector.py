"""Fast and Simple Adjacent Parts Detector

가장 간단한 접근:
1. Source part bbox 구하기
2. Plane 방향으로 bbox 확장해서 search region 만들기
3. Search region과 겹치는 candidate parts 찾기
4. 그 중에서 실제로 ray가 hit하는지 확인 (샘플링)
"""
import numpy as np
from typing import Set, Dict


class FastAdjacentDetector:
    """Fast bbox + sampling based detector"""

    def __init__(self, mesh_data, spatial_index):
        self._mesh = mesh_data
        self._spatial_index = spatial_index
        self._exterior_faces = None

    def _ensure_exterior_faces(self):
        """Lazy load exterior faces"""
        if self._exterior_faces is None:
            print("[FastDetector] Extracting exterior faces...")
            self._exterior_faces = self._mesh.extract_exterior_faces()
            total = sum(len(f) for f in self._exterior_faces.values())
            print(f"[FastDetector] Total exterior faces: {total}")

    def find_adjacent(
        self,
        source_part_id: int,
        plane: str,
        candidate_parts: Set[int],
        max_distance: float,
        sample_rays: int = 50
    ) -> Dict[int, int]:
        """Find adjacent parts using fast bbox + sampling

        Args:
            source_part_id: Source part
            plane: 'XY', 'YZ', 'ZX'
            candidate_parts: Candidates
            max_distance: Max distance
            sample_rays: Number of sample rays per part

        Returns:
            {part_id: hit_count}
        """
        self._ensure_exterior_faces()

        if source_part_id not in self._exterior_faces:
            print(f"[FastDetector] No exterior faces for source {source_part_id}")
            return {}

        # Get source bbox
        source_bbox = self._spatial_index.get_part_bbox(source_part_id)
        if source_bbox is None:
            print(f"[FastDetector] No bbox for source {source_part_id}")
            return {}

        print(f"[FastDetector] Source bbox: {source_bbox.min_point} ~ {source_bbox.max_point}")

        # Ray direction
        if plane == 'XY':
            ray_dir = np.array([0.0, 0.0, 1.0])
            axis_idx = 2
        elif plane == 'YZ':
            ray_dir = np.array([1.0, 0.0, 0.0])
            axis_idx = 0
        elif plane == 'ZX':
            ray_dir = np.array([0.0, 1.0, 0.0])
            axis_idx = 1
        else:
            return {}

        # Get sample points from source part's exterior faces
        sample_points = self._get_face_sample_points(source_part_id, sample_rays)
        print(f"[FastDetector] Generated {len(sample_points)} sample points")

        if len(sample_points) == 0:
            return {}

        # Test each candidate part
        hits_by_part = {}

        for cand_id in candidate_parts:
            cand_bbox = self._spatial_index.get_part_bbox(cand_id)
            if cand_bbox is None:
                continue

            # Quick bbox overlap test
            hit_count = 0

            # Cast rays from samples
            for point in sample_points:
                # Check positive direction
                if self._ray_bbox_intersect(point, ray_dir, cand_bbox, max_distance):
                    hit_count += 1
                # Check negative direction
                elif self._ray_bbox_intersect(point, -ray_dir, cand_bbox, max_distance):
                    hit_count += 1

            if hit_count > 0:
                hits_by_part[cand_id] = hit_count
                print(f"[FastDetector] Part {cand_id}: {hit_count} hits")

        return hits_by_part

    def _get_face_sample_points(self, part_id: int, num_samples: int) -> np.ndarray:
        """Get sample points from exterior faces

        IMPORTANT: Uses deterministic sampling for consistent results.
        Same part_id always produces same sample points.

        Args:
            part_id: Part ID
            num_samples: Number of samples

        Returns:
            (N, 3) array of points
        """
        if part_id not in self._exterior_faces:
            return np.array([])

        faces = self._exterior_faces[part_id]

        # Get all unique nodes
        node_set = set()
        for elem_idx, face_indices in faces:
            elem_nodes = self._mesh.elements[elem_idx]
            for fi in face_indices:
                node_set.add(elem_nodes[fi])

        # Sort for deterministic ordering
        node_list = sorted(list(node_set))

        # Deterministic uniform sampling if too many
        if len(node_list) > num_samples:
            # Use numpy's evenly spaced indices for consistent sampling
            indices = np.linspace(0, len(node_list) - 1, num_samples, dtype=int)
            node_list = [node_list[i] for i in indices]

        # Get coordinates
        return self._mesh.nodes[node_list]

    def _ray_bbox_intersect(
        self,
        origin: np.ndarray,
        direction: np.ndarray,
        bbox,
        max_distance: float
    ) -> bool:
        """Fast ray-bbox intersection test

        Args:
            origin: Ray origin
            direction: Ray direction (unit)
            bbox: BoundingBox
            max_distance: Max distance

        Returns:
            True if intersect
        """
        t_min = 0.0
        t_max = max_distance

        for i in range(3):
            if abs(direction[i]) < 1e-10:
                # Parallel to slab
                if origin[i] < bbox.min_point[i] or origin[i] > bbox.max_point[i]:
                    return False
            else:
                t1 = (bbox.min_point[i] - origin[i]) / direction[i]
                t2 = (bbox.max_point[i] - origin[i]) / direction[i]

                if t1 > t2:
                    t1, t2 = t2, t1

                t_min = max(t_min, t1)
                t_max = min(t_max, t2)

                if t_min > t_max:
                    return False

        return t_max > 0
