"""Ray Tracing for Adjacent Part Detection

Casts rays from source part outline to detect intersections with candidate parts.
"""
import numpy as np
from typing import Set, List, Tuple, Optional, Dict
from dataclasses import dataclass
from .spatial_index import BoundingBox


@dataclass
class RayHit:
    """Ray intersection result"""
    part_id: int
    distance: float  # Distance from ray origin
    hit_point: np.ndarray  # 3D intersection point


class RayTracer:
    """Ray-based intersection testing for adjacent parts"""

    def __init__(self, mesh_data, spatial_index):
        """Initialize ray tracer

        Args:
            mesh_data: MeshData object
            spatial_index: SpatialIndex for fast queries
        """
        self._mesh = mesh_data
        self._spatial_index = spatial_index

    def cast_rays(
        self,
        ray_origins: np.ndarray,
        ray_direction: np.ndarray,
        candidate_parts: Set[int],
        max_distance: float = 1000.0
    ) -> Dict[int, List[RayHit]]:
        """Cast multiple rays and find intersections

        Args:
            ray_origins: Nx3 array of ray start points
            ray_direction: [dx, dy, dz] unit vector
            candidate_parts: Set of part IDs to test
            max_distance: Maximum ray distance

        Returns:
            Dict mapping part_id -> list of RayHit
        """
        hits_by_part = {}

        for part_id in candidate_parts:
            hits = self._test_part(
                ray_origins,
                ray_direction,
                part_id,
                max_distance
            )

            if hits:
                hits_by_part[part_id] = hits

        return hits_by_part

    def cast_rays_with_occlusion(
        self,
        ray_origins: np.ndarray,
        ray_direction: np.ndarray,
        candidate_parts: Set[int],
        max_distance: float = 1000.0
    ) -> Dict[int, List[RayHit]]:
        """Cast rays with occlusion handling

        For each ray, only the CLOSEST hit is recorded. Parts behind
        closer parts are excluded (occluded).

        Args:
            ray_origins: Nx3 array of ray start points
            ray_direction: [dx, dy, dz] unit vector
            candidate_parts: Set of part IDs to test
            max_distance: Maximum ray distance

        Returns:
            Dict mapping part_id -> list of RayHit (only closest hits)
        """
        hits_by_part = {}

        # For each ray, find all intersections and keep only closest
        for ray_idx, origin in enumerate(ray_origins):
            closest_hit = None
            closest_distance = max_distance

            # Test all candidate parts
            for part_id in candidate_parts:
                bbox = self._spatial_index.get_part_bbox(part_id)
                if bbox is None:
                    continue

                # Test intersection
                t = self._ray_aabb_intersection(
                    origin, ray_direction, bbox, max_distance
                )

                if t is not None and t < closest_distance:
                    closest_distance = t
                    hit_point = origin + t * ray_direction
                    closest_hit = (part_id, RayHit(part_id, t, hit_point))

            # Record only the closest hit for this ray
            if closest_hit is not None:
                part_id, hit = closest_hit
                if part_id not in hits_by_part:
                    hits_by_part[part_id] = []
                hits_by_part[part_id].append(hit)

        return hits_by_part

    def _test_part(
        self,
        ray_origins: np.ndarray,
        ray_direction: np.ndarray,
        part_id: int,
        max_distance: float
    ) -> List[RayHit]:
        """Test rays against a single part

        Args:
            ray_origins: Nx3 array
            ray_direction: [dx, dy, dz] unit vector
            part_id: Part ID to test
            max_distance: Max ray distance

        Returns:
            List of RayHit
        """
        # Get part bounding box
        bbox = self._spatial_index.get_part_bbox(part_id)
        if bbox is None:
            return []

        hits = []

        # Test each ray against bounding box
        for origin in ray_origins:
            t = self._ray_aabb_intersection(
                origin, ray_direction, bbox, max_distance
            )

            if t is not None:
                # Hit!
                hit_point = origin + t * ray_direction
                hits.append(RayHit(part_id, t, hit_point))

        return hits

    def _ray_aabb_intersection(
        self,
        ray_origin: np.ndarray,
        ray_direction: np.ndarray,
        bbox: BoundingBox,
        max_distance: float
    ) -> Optional[float]:
        """Ray-AABB intersection test

        Uses slab method for efficiency.

        Args:
            ray_origin: [x, y, z]
            ray_direction: [dx, dy, dz] (unit vector)
            bbox: BoundingBox
            max_distance: Maximum t value

        Returns:
            t value if hit, None otherwise
        """
        # Slab method
        t_min = 0.0
        t_max = max_distance

        for i in range(3):
            if abs(ray_direction[i]) < 1e-10:
                # Ray parallel to slab
                if ray_origin[i] < bbox.min_point[i] or \
                   ray_origin[i] > bbox.max_point[i]:
                    return None  # Outside slab
            else:
                # Compute intersection distances
                t1 = (bbox.min_point[i] - ray_origin[i]) / ray_direction[i]
                t2 = (bbox.max_point[i] - ray_origin[i]) / ray_direction[i]

                # Ensure t1 < t2
                if t1 > t2:
                    t1, t2 = t2, t1

                # Update intersection interval
                t_min = max(t_min, t1)
                t_max = min(t_max, t2)

                if t_min > t_max:
                    return None  # No intersection

        # Return closest intersection
        if t_min > 0:
            return t_min
        elif t_max > 0:
            return t_max
        else:
            return None

    def filter_by_facing(
        self,
        hits_by_part: Dict[int, List[RayHit]],
        source_part_id: int,
        surface_analyzer,
        plane: Optional[str] = None,
        threshold: float = -0.5
    ) -> Set[int]:
        """Filter hits to only include parts that face the source

        Args:
            hits_by_part: Results from cast_rays
            source_part_id: Source part ID
            surface_analyzer: SurfaceAnalyzer instance
            plane: Optional plane constraint
            threshold: Facing threshold

        Returns:
            Set of part IDs that actually face the source
        """
        facing_parts = set()

        for part_id in hits_by_part.keys():
            if surface_analyzer.check_facing(
                source_part_id,
                part_id,
                plane,
                threshold
            ):
                facing_parts.add(part_id)

        return facing_parts

    def compute_coverage(
        self,
        hits_by_part: Dict[int, List[RayHit]],
        total_rays: int
    ) -> Dict[int, float]:
        """Compute coverage percentage for each part

        Coverage = (number of rays hit) / (total rays)

        Args:
            hits_by_part: Results from cast_rays
            total_rays: Total number of rays cast

        Returns:
            Dict mapping part_id -> coverage (0.0 to 1.0)
        """
        coverage = {}

        for part_id, hits in hits_by_part.items():
            coverage[part_id] = len(hits) / max(1, total_rays)

        return coverage
