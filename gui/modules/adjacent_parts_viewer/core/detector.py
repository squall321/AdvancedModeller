"""Adjacent Parts Detector - Main Integration

Combines spatial indexing, projection, ray tracing, and surface analysis
to detect parts that face each other.
"""
import numpy as np
import time
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass

from .spatial_index import SpatialIndex, BoundingBox
from .surface_analyzer import SurfaceAnalyzer
from .projection import ProjectionEngine, ProjectedOutline
from .ray_tracer import RayTracer, RayHit
from .element_ray_tracer import ElementRayTracer
from .simple_detector import SimpleAdjacentDetector
from .fast_detector import FastAdjacentDetector


@dataclass
class DetectionResult:
    """Result of adjacent parts detection"""
    source_part_id: int
    adjacent_parts: Set[int]
    plane: str
    thickness_min: float
    thickness_max: float

    # Additional info
    ray_count: int
    hit_count: int
    coverage: Dict[int, float]  # part_id -> coverage percentage

    # Performance
    timing: Dict[str, float]  # stage -> time (ms)

    # Visualization data (optional)
    ray_origins: Optional[np.ndarray] = None
    ray_direction: Optional[np.ndarray] = None


class AdjacentPartsDetector:
    """High-level detector for finding adjacent parts

    Algorithm:
    1. Spatial Query: Use Octree to find candidate parts in thickness range
    2. Projection: Project source part to 2D plane, extract outline
    3. Ray Casting: Cast rays from outline along plane normal
    4. Facing Check: Validate parts actually face each other using normals
    5. Filtering: Apply coverage threshold
    """

    def __init__(self, mesh_data):
        """Initialize detector

        Args:
            mesh_data: MeshData object
        """
        self._mesh = mesh_data

        # Initialize subsystems
        self._spatial_index = SpatialIndex(mesh_data)
        self._surface_analyzer = SurfaceAnalyzer(mesh_data)
        self._projection_engine = ProjectionEngine(mesh_data)
        self._ray_tracer = RayTracer(mesh_data, self._spatial_index)
        self._element_ray_tracer = ElementRayTracer(mesh_data)
        self._simple_detector = SimpleAdjacentDetector(mesh_data)
        self._fast_detector = FastAdjacentDetector(mesh_data, self._spatial_index)

    def get_auto_thickness_range(
        self,
        source_part_id: int,
        plane: str,
        search_multiplier: float = 5.0
    ) -> Tuple[float, float]:
        """자동으로 thickness 범위를 계산

        선택한 평면의 수직 축에서 source part의 bounding box를 기준으로
        검색 범위를 자동 설정합니다.

        Args:
            source_part_id: Source part ID
            plane: 'XY', 'YZ', or 'ZX'
            search_multiplier: BBox 크기의 몇 배까지 검색할지

        Returns:
            (thickness_min, thickness_max) tuple
        """
        bbox = self._spatial_index.get_part_bbox(source_part_id)
        if bbox is None:
            # Default fallback
            return (0.1, 100.0)

        # 평면에 따라 수직 축 결정
        if plane == 'XY':
            axis_idx = 2  # Z축
        elif plane == 'YZ':
            axis_idx = 0  # X축
        elif plane == 'ZX':
            axis_idx = 1  # Y축
        else:
            return (0.1, 100.0)

        # Source part의 해당 축 범위
        part_min = bbox.min_point[axis_idx]
        part_max = bbox.max_point[axis_idx]
        part_size = part_max - part_min

        # 검색 범위: part 두께 + (part 크기의 N배)
        thickness_min = max(0.1, part_size * 0.1)  # 최소 10% 두께
        thickness_max = part_size * search_multiplier

        return (thickness_min, thickness_max)

    def find_adjacent(
        self,
        source_part_id: int,
        plane: str,
        thickness_min: float,
        thickness_max: float,
        check_facing: bool = True,
        ray_density: float = 0.1,
        coverage_threshold: float = 0.1,
        visualize: bool = False,
        layer_mode: bool = False
    ) -> DetectionResult:
        """Find parts adjacent to source part using ELEMENT-BASED ray tracing

        Args:
            source_part_id: Source part ID
            plane: 'XY', 'YZ', or 'ZX'
            thickness_min: Minimum distance along normal
            thickness_max: Maximum distance along normal
            check_facing: Validate parts actually face each other (ignored for element-based)
            ray_density: Ray density (ignored for element-based)
            coverage_threshold: Minimum hit count ratio to include part
            visualize: Include visualization data in result
            layer_mode: If True, accept all parts within Z-range without ray testing
                       (useful for PCB packages at same layer but different XY positions)

        Returns:
            DetectionResult with adjacent parts and metadata
        """
        timing = {}

        print(f"[Detector] ===== FAST BBOX-BASED DETECTION =====")
        print(f"[Detector] Source part: {source_part_id}, Plane: {plane}")
        print(f"[Detector] Thickness range: {thickness_min:.2f} ~ {thickness_max:.2f}")

        # Stage 1: Spatial query for candidates
        t0 = time.time()
        candidates = self._spatial_index.query_thickness_range(
            source_part_id, plane, thickness_min, thickness_max
        )
        timing['spatial_query'] = (time.time() - t0) * 1000

        print(f"[Detector] Spatial query found {len(candidates)} candidates: {sorted(list(candidates))}")

        if not candidates:
            print(f"[Detector] No candidates found in thickness range!")
            return self._empty_result(
                source_part_id, plane, thickness_min, thickness_max, timing
            )

        # Stage 2: Fast bbox + sampling detection (or skip in layer mode)
        t0 = time.time()
        if layer_mode:
            # Layer mode: accept all candidates without ray testing
            print(f"[Detector] Layer mode: accepting all {len(candidates)} candidates")
            hits_by_part = {pid: 1 for pid in candidates}  # Dummy hits
        else:
            hits_by_part = self._fast_detector.find_adjacent(
                source_part_id=source_part_id,
                plane=plane,
                candidate_parts=candidates,
                max_distance=thickness_max,
                sample_rays=100  # More samples for better accuracy
            )
        timing['fast_detection'] = (time.time() - t0) * 1000

        print(f"[Detector] Fast detector found {len(hits_by_part)} parts with hits")
        for pid in sorted(hits_by_part.keys())[:10]:  # Show first 10
            print(f"[Detector]   Part {pid}: {hits_by_part[pid]} hits")

        # Stage 3: Filter by minimum hit count
        t0 = time.time()

        if not hits_by_part:
            print(f"[Detector] No hits found!")
            timing['filtering'] = (time.time() - t0) * 1000
            timing['total'] = sum(timing.values())
            return DetectionResult(
                source_part_id=source_part_id,
                adjacent_parts=set(),
                plane=plane,
                thickness_min=thickness_min,
                thickness_max=thickness_max,
                ray_count=0,
                hit_count=0,
                coverage={},
                timing=timing
            )

        # Find maximum hit count to normalize
        max_hits = max(hits_by_part.values())
        min_required_hits = max(1, int(max_hits * coverage_threshold))

        print(f"[Detector] Filtering: max_hits={max_hits}, min_required={min_required_hits}")

        # Compute coverage and filter
        coverage = {}
        adjacent_parts = set()

        for pid, hit_count in hits_by_part.items():
            cov = hit_count / max(1, max_hits)
            coverage[pid] = cov

            if hit_count >= min_required_hits:
                adjacent_parts.add(pid)
                print(f"[Detector]   Part {pid}: {hit_count} hits ({cov*100:.1f}%) -> INCLUDED")
            else:
                print(f"[Detector]   Part {pid}: {hit_count} hits ({cov*100:.1f}%) -> filtered out")

        timing['filtering'] = (time.time() - t0) * 1000
        timing['total'] = sum(timing.values())

        print(f"[Detector] Final result: {len(adjacent_parts)} adjacent parts")

        # Build result
        total_hits = sum(hits_by_part.values())
        result = DetectionResult(
            source_part_id=source_part_id,
            adjacent_parts=adjacent_parts,
            plane=plane,
            thickness_min=thickness_min,
            thickness_max=thickness_max,
            ray_count=0,  # Not applicable for element-based
            hit_count=total_hits,
            coverage=coverage,
            timing=timing
        )

        return result

    def _generate_bbox_rays(
        self,
        source_part_id: int,
        plane: str,
        density: float = 0.1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate rays from source part's bounding box face

        Args:
            source_part_id: Source part ID
            plane: 'XY', 'YZ', or 'ZX'
            density: Ray grid density (rays per unit length)

        Returns:
            (ray_origins_3d, ray_direction)
        """
        bbox = self._spatial_index.get_part_bbox(source_part_id)
        if bbox is None:
            return np.array([]), np.array([0, 0, 1])

        min_pt = bbox.min_point
        max_pt = bbox.max_point

        # Determine plane axes and perpendicular direction
        if plane == 'XY':
            # Ray direction: +Z
            ray_direction = np.array([0.0, 0.0, 1.0])
            # Grid on XY plane at source bbox center Z
            z_value = (min_pt[2] + max_pt[2]) / 2
            x_range = (min_pt[0], max_pt[0])
            y_range = (min_pt[1], max_pt[1])

            # Create grid
            x_size = x_range[1] - x_range[0]
            y_size = y_range[1] - y_range[0]
            nx = max(3, int(x_size * density))
            ny = max(3, int(y_size * density))

            x_vals = np.linspace(x_range[0], x_range[1], nx)
            y_vals = np.linspace(y_range[0], y_range[1], ny)

            ray_origins_3d = []
            for x in x_vals:
                for y in y_vals:
                    ray_origins_3d.append([x, y, z_value])

        elif plane == 'YZ':
            # Ray direction: +X
            ray_direction = np.array([1.0, 0.0, 0.0])
            x_value = (min_pt[0] + max_pt[0]) / 2
            y_range = (min_pt[1], max_pt[1])
            z_range = (min_pt[2], max_pt[2])

            y_size = y_range[1] - y_range[0]
            z_size = z_range[1] - z_range[0]
            ny = max(3, int(y_size * density))
            nz = max(3, int(z_size * density))

            y_vals = np.linspace(y_range[0], y_range[1], ny)
            z_vals = np.linspace(z_range[0], z_range[1], nz)

            ray_origins_3d = []
            for y in y_vals:
                for z in z_vals:
                    ray_origins_3d.append([x_value, y, z])

        elif plane == 'ZX':
            # Ray direction: +Y
            ray_direction = np.array([0.0, 1.0, 0.0])
            y_value = (min_pt[1] + max_pt[1]) / 2
            z_range = (min_pt[2], max_pt[2])
            x_range = (min_pt[0], max_pt[0])

            z_size = z_range[1] - z_range[0]
            x_size = x_range[1] - x_range[0]
            nz = max(3, int(z_size * density))
            nx = max(3, int(x_size * density))

            z_vals = np.linspace(z_range[0], z_range[1], nz)
            x_vals = np.linspace(x_range[0], x_range[1], nx)

            ray_origins_3d = []
            for z in z_vals:
                for x in x_vals:
                    ray_origins_3d.append([x, y_value, z])

        else:
            return np.array([]), np.array([0, 0, 1])

        return np.array(ray_origins_3d), ray_direction

    def _setup_rays(
        self,
        ray_origins_2d: np.ndarray,
        plane: str,
        source_part_id: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Setup 3D ray origins and direction

        Args:
            ray_origins_2d: Nx2 array
            plane: 'XY', 'YZ', or 'ZX'
            source_part_id: Source part ID

        Returns:
            (ray_origins_3d, ray_direction)
        """
        # Get source part bounding box for Z value
        bbox = self._spatial_index.get_part_bbox(source_part_id)
        if bbox is None:
            return np.array([]), np.array([0, 0, 1])

        # Use center of bbox along perpendicular axis
        center = bbox.center

        # Determine perpendicular axis and ray direction
        if plane == 'XY':
            z_value = center[2]
            ray_direction = np.array([0, 0, 1])  # +Z
            axis_idx = 2
        elif plane == 'YZ':
            z_value = center[0]
            ray_direction = np.array([1, 0, 0])  # +X
            axis_idx = 0
        elif plane == 'ZX':
            z_value = center[1]
            ray_direction = np.array([0, 1, 0])  # +Y
            axis_idx = 1
        else:
            return np.array([]), np.array([0, 0, 1])

        # Convert 2D origins to 3D
        ray_origins_3d = []
        for p2d in ray_origins_2d:
            p3d = self._projection_engine.restore_3d_point(p2d, plane, z_value)
            ray_origins_3d.append(p3d)

        ray_origins_3d = np.array(ray_origins_3d)

        # Optionally cast in both directions (for thin parts)
        # For now, just use positive direction

        return ray_origins_3d, ray_direction

    def _empty_result(
        self,
        source_part_id: int,
        plane: str,
        thickness_min: float,
        thickness_max: float,
        timing: Dict[str, float]
    ) -> DetectionResult:
        """Create empty result"""
        return DetectionResult(
            source_part_id=source_part_id,
            adjacent_parts=set(),
            plane=plane,
            thickness_min=thickness_min,
            thickness_max=thickness_max,
            ray_count=0,
            hit_count=0,
            coverage={},
            timing=timing
        )

    def suggest_best_plane(self, part_id: int) -> Optional[str]:
        """Suggest best plane for detecting adjacent parts

        Args:
            part_id: Part ID

        Returns:
            'XY', 'YZ', or 'ZX'
        """
        return self._surface_analyzer.get_dominant_plane_normal(part_id)

    def explain_no_hits(
        self,
        result: DetectionResult
    ) -> List[str]:
        """Explain why no adjacent parts were found

        Args:
            result: DetectionResult with empty adjacent_parts

        Returns:
            List of possible reasons
        """
        reasons = []

        if result.ray_count == 0:
            reasons.append("Source part could not be projected to 2D plane")
            return reasons

        # Check if any candidates were found
        if 'spatial_query' in result.timing:
            # If spatial query was fast, probably no candidates
            reasons.append(
                f"No parts found within thickness range "
                f"[{result.thickness_min}, {result.thickness_max}]. "
                f"Try increasing max thickness."
            )

        # Check if coverage was too low
        if result.coverage:
            max_coverage = max(result.coverage.values())
            reasons.append(
                f"Parts detected but coverage too low "
                f"(max: {max_coverage:.1%}). "
                f"Try adjusting coverage threshold or ray density."
            )

        # Check if facing check eliminated all parts
        if 'facing_check' in result.timing and not result.adjacent_parts:
            reasons.append(
                f"Parts found but not facing the source part. "
                f"Try different plane or disable facing check."
            )

        return reasons

    def get_performance_stats(self, result: DetectionResult) -> str:
        """Format performance statistics

        Args:
            result: DetectionResult

        Returns:
            Human-readable performance summary
        """
        lines = [
            f"Total time: {result.timing.get('total', 0):.1f} ms",
            f"  - Spatial query: {result.timing.get('spatial_query', 0):.1f} ms",
            f"  - Projection: {result.timing.get('projection', 0):.1f} ms",
            f"  - Ray setup: {result.timing.get('ray_setup', 0):.1f} ms",
            f"  - Ray casting: {result.timing.get('ray_casting', 0):.1f} ms",
        ]

        if 'facing_check' in result.timing:
            lines.append(
                f"  - Facing check: {result.timing.get('facing_check', 0):.1f} ms"
            )

        lines.append(
            f"  - Filtering: {result.timing.get('filtering', 0):.1f} ms"
        )

        lines.extend([
            f"Rays cast: {result.ray_count}",
            f"Hits: {result.hit_count}",
            f"Adjacent parts: {len(result.adjacent_parts)}"
        ])

        return "\n".join(lines)

    def clear_caches(self):
        """Clear all caches (call when mesh changes)"""
        self._surface_analyzer.clear_cache()
        self._projection_engine.clear_cache()
