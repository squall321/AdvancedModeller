"""
DOE-based placement generator using Latin Hypercube Sampling.

This module generates multiple placement options for a source part by:
1. Sampling the XY space uniformly using LHS
2. Checking collision with adjacent parts (BBox or Voxel method)
3. Filtering valid placements

Two collision detection methods available:
- Legacy: 2D BBox projection (fast, but approximate)
- Voxel: 3D voxel-based (accurate, handles complex geometry)
"""

from typing import List, Tuple
import numpy as np
from scipy.stats import qmc

from gui.modules.model_viewer.core.mesh_data import MeshData
from .spatial_utils import BBox2D, Placement, DOEResult
from .feasible_space import FeasibleSpaceAnalyzer
from .voxel_collision import VoxelCollisionDetector


class DOEPlacementGenerator:
    """Generates DOE-based placement options for package positioning."""

    def __init__(self, mesh_data: MeshData, voxel_size: float = 2.0):
        """
        Initialize generator with mesh data.

        Args:
            mesh_data: MeshData containing part geometry
            voxel_size: Voxel size for feasible space analysis and voxel collision (mm)
        """
        self.mesh_data = mesh_data
        self.feasible_analyzer = FeasibleSpaceAnalyzer(voxel_size=voxel_size)
        self.voxel_detector = VoxelCollisionDetector(mesh_data, voxel_size=voxel_size)

    def suggest_max_displacement(
        self,
        source_part_id: int,
        adjacent_part_ids: List[int],
        grid_step: float = 0.1,
        use_voxel: bool = False
    ) -> float:
        """
        Suggest appropriate max_displacement for package repositioning.

        Two methods available:
        - Legacy (BBox): Fast 2D BBox projection method
        - Voxel: Accurate 3D voxel-based collision detection

        Args:
            source_part_id: Source part ID
            adjacent_part_ids: List of adjacent part IDs (after coplanar filtering)
            grid_step: Grid spacing in mm (default 0.1mm for fine positioning)
            use_voxel: If True, use voxel method; if False, use legacy BBox method

        Returns:
            Suggested max_displacement in mm (typically 0.5-10mm for repositioning)
        """
        if not adjacent_part_ids:
            return 50.0  # Default if no adjacent parts

        # Voxel method
        if use_voxel:
            return self.voxel_detector.suggest_max_displacement(
                source_part_id, adjacent_part_ids, grid_step
            )

        # Legacy BBox method
        source_bbox = self.get_2d_bbox(source_part_id)
        adjacent_bboxes = [self.get_2d_bbox(pid) for pid in adjacent_part_ids]

        print(f"[Auto Max Disp] BBox-based search (step={grid_step:.2f}mm)")
        print(f"[Auto Max Disp] Source part {source_part_id}, checking against {len(adjacent_part_ids)} collision parts")

        # Try increasing search radii and count valid positions
        # Use finer granularity for small displacements
        test_radii = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0, 15.0, 20.0, 30.0, 50.0]

        first_valid_radius = None
        best_radius = None

        for radius in test_radii:
            # Adaptive sampling: use coarser grid for large radii to save time
            # For small radii (< 5mm), use full resolution (grid_step)
            # For larger radii, use 0.5mm steps
            actual_step = grid_step if radius < 5.0 else max(grid_step, 0.5)

            valid_count = 0
            steps = int(radius / actual_step)

            # Sample grid in circular pattern
            for i in range(-steps, steps + 1):
                for j in range(-steps, steps + 1):
                    dx = i * actual_step
                    dy = j * actual_step
                    dist = np.sqrt(dx**2 + dy**2)

                    # Skip if outside radius
                    if dist > radius:
                        continue

                    # Check if this position collides
                    collisions = self.find_collisions(
                        source_bbox, dx, dy, adjacent_part_ids, adjacent_bboxes
                    )

                    if len(collisions) == 0:
                        valid_count += 1

            total_positions = (2 * steps + 1) ** 2
            success_rate = valid_count / max(1, total_positions) * 100

            print(f"  Radius {radius:5.1f}mm (step={actual_step:.2f}): {valid_count:4d}/{total_positions:4d} valid ({success_rate:5.1f}%)")

            # Track first radius where we find ANY valid positions
            if valid_count > 0 and first_valid_radius is None:
                first_valid_radius = radius

            # If we found at least 10 valid positions, use this radius
            if valid_count >= 10:
                best_radius = radius
                break

        # Decision logic
        if best_radius is not None:
            print(f"[Auto Max Disp] Found {valid_count} valid positions at {best_radius:.1f}mm ✓")
            return best_radius
        elif first_valid_radius is not None:
            # Found some valid positions, but less than 10
            # This indicates very tight packing - use the minimum working value
            print(f"[Auto Max Disp] Tight packing detected: first valid at {first_valid_radius:.1f}mm")
            print(f"[Auto Max Disp] Using {first_valid_radius:.1f}mm (limited space available)")
            return first_valid_radius
        else:
            # No valid positions found at all - use conservative default
            print(f"[Auto Max Disp] No valid positions found, using default 5.0mm")
            return 5.0

    def filter_coplanar_parts(
        self,
        source_part_id: int,
        adjacent_part_ids: List[int],
        z_tolerance: float = 1.0,
        z_separation_threshold: float = 0.5,
        size_ratio_threshold: float = 5.0
    ) -> tuple:
        """
        Filter out parts that should NOT block XY movement.

        Excludes three types of parts:
        1. Face-to-face contact (co-planar): PCB below, lid above
        2. Z-separated parts: Parts that don't overlap in Z direction
        3. Enclosing parts: Very large parts that FULLY enclose source in XY
           (e.g., metal case, display) - these are hollow structures where
           BBox collision would give false positives

        NOTE: Enclosing parts are excluded from normal collision checking,
        but boundary checks are done separately in find_collisions().

        Args:
            source_part_id: Source part ID
            adjacent_part_ids: List of adjacent part IDs
            z_tolerance: Face-to-face detection threshold (mm)
            z_separation_threshold: Minimum Z gap to consider separated (mm)
            size_ratio_threshold: Exclude parts this many times larger in XY area

        Returns:
            (collision_part_ids, excluded_part_ids) tuple
        """
        source_nodes = self._get_part_nodes(source_part_id)
        source_z_min = source_nodes[:, 2].min()
        source_z_max = source_nodes[:, 2].max()

        # Get source 2D bbox for enclosure detection
        source_bbox_2d = self.get_2d_bbox(source_part_id)
        source_area = source_bbox_2d.width() * source_bbox_2d.height()

        collision_parts = []
        excluded_parts = []

        for adj_id in adjacent_part_ids:
            adj_nodes = self._get_part_nodes(adj_id)
            adj_z_min = adj_nodes[:, 2].min()
            adj_z_max = adj_nodes[:, 2].max()

            # Check Z overlap/separation
            # Key insight: We only exclude parts that are ENTIRELY outside source Z range
            # Parts that overlap in Z MUST be checked for XY collision

            # Calculate Z overlap
            z_overlap_min = max(source_z_min, adj_z_min)
            z_overlap_max = min(source_z_max, adj_z_max)
            has_z_overlap = z_overlap_max > z_overlap_min - z_tolerance

            # Case 1: Adjacent part is COMPLETELY BELOW source (no Z overlap)
            # adj_z_max < source_z_min (with some tolerance)
            if adj_z_max + z_separation_threshold < source_z_min and not has_z_overlap:
                excluded_parts.append(adj_id)  # Below with gap → no XY collision
                continue

            # Case 2: Adjacent part is COMPLETELY ABOVE source (no Z overlap)
            # adj_z_min > source_z_max (with some tolerance)
            if adj_z_min - z_separation_threshold > source_z_max and not has_z_overlap:
                excluded_parts.append(adj_id)  # Above with gap → no XY collision
                continue

            # Case 3: Face-to-face contact below (PCB case)
            # Part is directly below source with surface touching, but NO Z overlap
            # This means: adj_z_max ≈ source_z_min AND adj_z_min < source_z_min
            is_below_touching = (abs(adj_z_max - source_z_min) < z_tolerance and
                                 adj_z_min < source_z_min - z_tolerance)
            if is_below_touching and not has_z_overlap:
                excluded_parts.append(adj_id)  # Face contact below → no XY collision
                continue

            # Case 4: Face-to-face contact above (lid case)
            # Part is directly above source with surface touching, but NO Z overlap
            # This means: adj_z_min ≈ source_z_max AND adj_z_max > source_z_max
            is_above_touching = (abs(adj_z_min - source_z_max) < z_tolerance and
                                 adj_z_max > source_z_max + z_tolerance)
            if is_above_touching and not has_z_overlap:
                excluded_parts.append(adj_id)  # Face contact above → no XY collision
                continue

            # Case 5: Enclosing part detection (metal case, frame, etc.)
            # If adjacent part FULLY contains source bbox in XY AND is much larger,
            # it's a hollow enclosing structure - BBox collision would always trigger
            # Boundary check is done separately
            adj_bbox_2d = self.get_2d_bbox(adj_id)
            adj_area = adj_bbox_2d.width() * adj_bbox_2d.height()

            # Check if adjacent fully contains source in XY
            xy_fully_contains = (adj_bbox_2d.min_x <= source_bbox_2d.min_x and
                                 adj_bbox_2d.max_x >= source_bbox_2d.max_x and
                                 adj_bbox_2d.min_y <= source_bbox_2d.min_y and
                                 adj_bbox_2d.max_y >= source_bbox_2d.max_y)

            # Check if adjacent is much larger in XY
            xy_much_larger = (adj_area > source_area * size_ratio_threshold)

            if xy_fully_contains and xy_much_larger:
                # This is likely a hollow enclosing structure (metal case, display)
                # Mark as excluded but store for boundary checking
                excluded_parts.append(adj_id)
                continue

            # Case 6: Z ranges overlap → potential XY collision
            collision_parts.append(adj_id)

        return collision_parts, excluded_parts

    def _get_part_nodes(self, part_id: int) -> np.ndarray:
        """Get all node coordinates for a part"""
        elem_indices = self.mesh_data.part_elements[part_id]
        coords = []
        for elem_idx in elem_indices:
            node_list = self.mesh_data.elements[elem_idx]
            elem_coords = self.mesh_data.nodes[node_list]
            coords.append(elem_coords)
        return np.vstack(coords)

    def find_parts_in_displacement_range(
        self,
        source_part_id: int,
        max_displacement: float,
        margin: float = 5.0
    ) -> List[int]:
        """
        Find ALL parts that could potentially collide within displacement range.

        This is crucial because Adjacent Parts Detection only finds parts that
        overlap with source at current position, but DOE needs to check parts
        that might collide when source moves.

        Args:
            source_part_id: Source part ID
            max_displacement: Maximum XY displacement in mm
            margin: Extra margin for safety (mm)

        Returns:
            List of part IDs that could potentially collide
        """
        source_bbox = self.get_2d_bbox(source_part_id)

        # Expand source bbox by displacement + margin
        expanded_min_x = source_bbox.min_x - max_displacement - margin
        expanded_max_x = source_bbox.max_x + max_displacement + margin
        expanded_min_y = source_bbox.min_y - max_displacement - margin
        expanded_max_y = source_bbox.max_y + max_displacement + margin

        potential_parts = []

        for part_id in self.mesh_data.part_elements.keys():
            if part_id == source_part_id:
                continue

            part_bbox = self.get_2d_bbox(part_id)

            # Check if part's bbox overlaps with expanded search area
            if (part_bbox.max_x >= expanded_min_x and
                part_bbox.min_x <= expanded_max_x and
                part_bbox.max_y >= expanded_min_y and
                part_bbox.min_y <= expanded_max_y):
                potential_parts.append(part_id)

        return potential_parts

    def generate_placements(
        self,
        source_part_id: int,
        adjacent_part_ids: List[int],
        num_samples: int,
        max_displacement: float,
        enable_resampling: bool = True,
        use_voxel: bool = True
    ) -> DOEResult:
        """
        Generate DOE-based placement options.

        Args:
            source_part_id: Part ID to generate placements for
            adjacent_part_ids: List of adjacent part IDs to avoid (from detection)
            num_samples: Number of placement samples to generate
            max_displacement: Maximum XY displacement in mm
            enable_resampling: If True, resample to meet desired count
            use_voxel: If True, use accurate voxel-based collision detection (default)
                       If False, use faster but approximate BBox method

        Returns:
            DOEResult with placements and metadata
        """
        # IMPORTANT: Find ALL parts that could collide within displacement range
        # Adjacent Parts Detection only finds overlapping parts at current position
        # DOE needs to check parts that might collide when source MOVES
        all_potential_parts = self.find_parts_in_displacement_range(
            source_part_id, max_displacement, margin=5.0
        )

        print(f"\n[DOE] 파트 탐색:")
        print(f"  Detection 인접 파트: {len(adjacent_part_ids)}개")
        print(f"  Displacement 범위 내 전체 파트: {len(all_potential_parts)}개")

        # Merge detection results with displacement range parts
        # Use set to avoid duplicates
        all_candidate_parts = list(set(adjacent_part_ids) | set(all_potential_parts))
        print(f"  통합 후보 파트: {len(all_candidate_parts)}개")

        # Filter out co-planar parts (e.g., PCB under package)
        # These should NOT block XY movement
        collision_part_ids, coplanar_part_ids = self.filter_coplanar_parts(
            source_part_id, all_candidate_parts, z_tolerance=1.0
        )

        print(f"\n[DOE] 파트 필터링:")
        print(f"  충돌 체크 대상: {len(collision_part_ids)}개")
        print(f"  면접촉 파트 (제외): {len(coplanar_part_ids)}개")
        if coplanar_part_ids:
            print(f"    제외된 파트 IDs: {coplanar_part_ids[:5]}{'...' if len(coplanar_part_ids) > 5 else ''}")

        # Get source part geometry
        source_bbox = self.get_2d_bbox(source_part_id)
        source_center_3d = self.get_part_center(source_part_id)

        # Get adjacent part bboxes (only for non-coplanar parts)
        adjacent_bboxes = [
            self.get_2d_bbox(pid) for pid in collision_part_ids
        ]

        # Simple approach: sample from entire displacement range, filter by collision
        # This is more reliable than trying to pre-compute feasible regions
        feasible_bounds = (
            -max_displacement, max_displacement,
            -max_displacement, max_displacement
        )
        feasible_regions = [feasible_bounds]  # Single region covering all

        # Keep sampling until we get num_samples valid placements
        source_cx, source_cy = source_bbox.center()
        placements = []
        num_valid = 0
        placement_idx = 0
        max_attempts = 20 if enable_resampling else 1
        attempt = 0

        # Batch size: start with requested amount, increase if needed
        batch_size = num_samples

        # Debug logging
        collision_method = "Voxel (정확)" if use_voxel else "BBox (근사)"
        print(f"\n[DOE] 생성 파라미터:")
        print(f"  요청 샘플: {num_samples}개")
        print(f"  Max displacement: {max_displacement:.1f} mm")
        print(f"  충돌 검사 방식: {collision_method}")
        print(f"  Resampling 활성화: {enable_resampling} (최대 {max_attempts}회 시도)")
        print(f"  소스 중심: ({source_cx:.1f}, {source_cy:.1f})")
        print(f"  인접 파트: {len(adjacent_bboxes)}개")
        print(f"  가능 영역: {len(feasible_regions)}개")

        # Prepare voxel grid if using voxel method
        voxel_grid = None
        source_voxels = None
        if use_voxel and collision_part_ids:
            print(f"\n[DOE] Voxel 그리드 준비 중...")
            voxel_grid = self.voxel_detector.create_voxel_grid(
                source_part_id, max_displacement, z_margin=2.0, margin_multiplier=0.5
            )
            print(f"  그리드 크기: {voxel_grid.grid_shape}")
            print(f"  Voxel 크기: {self.voxel_detector.voxel_size:.2f} mm")

            # Mark collision parts in grid
            total_marked = 0
            for part_id in collision_part_ids:
                marked = self.voxel_detector.mark_part_in_grid(voxel_grid, part_id)
                total_marked += marked
            print(f"  총 마킹된 voxel: {total_marked:,}")

            # Get source voxels
            source_voxels = self.voxel_detector.get_source_voxels(voxel_grid, source_part_id)
            print(f"  소스 파트 voxel: {len(source_voxels):,}")

        # Debug: Check if there are any feasible regions
        if not feasible_regions:
            print(f"⚠ WARNING: No feasible regions found!")
            print(f"  Source center: ({source_cx:.1f}, {source_cy:.1f})")
            print(f"  Max displacement: {max_displacement:.1f} mm")
            print(f"  Adjacent parts: {len(adjacent_bboxes)}")
            return DOEResult(
                source_part_id=source_part_id,
                source_center=source_center_3d,
                placements=[],
                num_valid=0,
                num_total=0,
                max_displacement=max_displacement,
                feasible_bounds=feasible_bounds
            )

        total_area = sum((r[1]-r[0])*(r[3]-r[2]) for r in feasible_regions)
        print(f"  총 가능 영역 면적: {total_area:.1f} mm²")

        while num_valid < num_samples and attempt < max_attempts:
            # Direct LHS sampling in displacement space (simpler and more reliable)
            samples = self.sample_lhs(batch_size, feasible_bounds)

            # Process each sample
            for dx, dy in samples:
                if num_valid >= num_samples:
                    break  # Got enough valid placements

                # Check max_displacement constraint first
                displacement = np.sqrt(dx**2 + dy**2)
                if displacement > max_displacement:
                    continue

                # Check collision (only with non-coplanar parts)
                if use_voxel and voxel_grid is not None and source_voxels is not None:
                    # Voxel-based collision: accurate 3D check
                    is_valid = self.voxel_detector.test_displacement(
                        voxel_grid, source_voxels, dx, dy
                    )
                    collision_parts = [] if is_valid else collision_part_ids
                else:
                    # BBox-based collision: fast but approximate
                    collision_parts = self.find_collisions(
                        source_bbox, dx, dy, collision_part_ids, adjacent_bboxes
                    )
                    is_valid = len(collision_parts) == 0

                if is_valid:
                    # Calculate displaced center
                    displaced_center = source_center_3d.copy()
                    displaced_center[0] += dx
                    displaced_center[1] += dy

                    # Calculate quality score
                    score = self.calculate_placement_score(
                        source_bbox, dx, dy, adjacent_bboxes
                    )

                    placement = Placement(
                        index=placement_idx,
                        dx=dx,
                        dy=dy,
                        is_valid=True,
                        collision_parts=[],
                        center=displaced_center,
                        score=score
                    )
                    placements.append(placement)
                    num_valid += 1
                    placement_idx += 1

            # Progress logging every attempt
            print(f"[DOE] 시도 {attempt + 1}: {num_valid}/{num_samples} valid 달성 ({num_valid/num_samples*100:.1f}%)")

            # If we still need more, increase batch size for next attempt
            if num_valid < num_samples:
                needed = num_samples - num_valid
                batch_size = needed * 3  # Generate 3x what we need
                attempt += 1
                if enable_resampling and attempt < max_attempts:
                    print(f"[DOE] 재샘플링: {needed}개 부족, 배치 크기 {batch_size}로 증가")

        # Final logging
        print(f"\n[DOE] 최종 결과:")
        print(f"  유효 배치: {num_valid}/{num_samples} ({num_valid/num_samples*100:.1f}%)")
        print(f"  총 시도: {attempt + 1}회")

        if num_valid < num_samples:
            print(f"⚠ WARNING: 목표 달성 실패!")
            print(f"  부족: {num_samples - num_valid}개")
            print(f"  Max displacement: {max_displacement:.1f} mm")
            print(f"  Feasible regions: {len(feasible_regions)}")
            if feasible_regions:
                total_area = sum((r[1]-r[0])*(r[3]-r[2]) for r in feasible_regions)
                print(f"  Total feasible area: {total_area:.1f} mm²")
        else:
            print(f"✓ 목표 달성 성공!")

        # Verify all placements respect max_displacement
        violations = 0
        for p in placements:
            dist = np.sqrt(p.dx**2 + p.dy**2)
            if dist > max_displacement + 0.1:
                violations += 1
                if violations <= 3:  # Show first 3
                    print(f"  ⚠ 제약 위반: Placement {p.index}: dist={dist:.2f} > {max_displacement:.1f}")

        if violations > 0:
            print(f"  총 {violations}개 배치가 max_displacement 위반!")

        return DOEResult(
            source_part_id=source_part_id,
            source_center=source_center_3d,
            placements=placements,
            num_valid=num_valid,
            num_total=len(placements),  # Total may be > num_samples after resampling
            max_displacement=max_displacement,
            feasible_bounds=feasible_bounds
        )

    def get_2d_bbox(self, part_id: int) -> BBox2D:
        """
        Extract XY bounding box for a part.

        Args:
            part_id: Part ID

        Returns:
            BBox2D in XY plane
        """
        if part_id not in self.mesh_data.part_elements:
            raise ValueError(f"Part {part_id} not found in mesh data")

        elem_indices = self.mesh_data.part_elements[part_id]

        # Collect all coordinates for this part
        coords = []
        for elem_idx in elem_indices:
            node_list = self.mesh_data.elements[elem_idx]
            elem_coords = self.mesh_data.nodes[node_list]
            coords.append(elem_coords)

        coords = np.vstack(coords)
        return BBox2D.from_points(coords)

    def get_part_center(self, part_id: int) -> np.ndarray:
        """
        Get [x, y, z] center of a part.

        Args:
            part_id: Part ID

        Returns:
            3D center point as numpy array
        """
        if part_id not in self.mesh_data.part_elements:
            raise ValueError(f"Part {part_id} not found in mesh data")

        elem_indices = self.mesh_data.part_elements[part_id]

        # Collect all coordinates
        coords = []
        for elem_idx in elem_indices:
            node_list = self.mesh_data.elements[elem_idx]
            elem_coords = self.mesh_data.nodes[node_list]
            coords.append(elem_coords)

        coords = np.vstack(coords)
        return coords.mean(axis=0).astype(np.float32)

    def check_collision(
        self,
        source_bbox: BBox2D,
        dx: float,
        dy: float,
        adjacent_bboxes: List[BBox2D]
    ) -> bool:
        """
        Check if displacement causes collision with any adjacent part.

        Args:
            source_bbox: Source part bounding box
            dx, dy: Displacement
            adjacent_bboxes: List of adjacent part bboxes

        Returns:
            True if collision detected, False otherwise
        """
        # Create displaced bbox
        displaced_bbox = source_bbox.translate(dx, dy)

        # Check overlap with each adjacent part
        for adj_bbox in adjacent_bboxes:
            if displaced_bbox.overlaps(adj_bbox):
                return True

        return False

    def find_collisions(
        self,
        source_bbox: BBox2D,
        dx: float,
        dy: float,
        adjacent_part_ids: List[int],
        adjacent_bboxes: List[BBox2D]
    ) -> List[int]:
        """
        Find which adjacent parts collide with displaced source.

        Args:
            source_bbox: Source part bounding box
            dx, dy: Displacement
            adjacent_part_ids: List of adjacent part IDs
            adjacent_bboxes: List of adjacent part bboxes

        Returns:
            List of part IDs that collide
        """
        displaced_bbox = source_bbox.translate(dx, dy)
        collision_parts = []

        for part_id, adj_bbox in zip(adjacent_part_ids, adjacent_bboxes):
            if displaced_bbox.overlaps(adj_bbox):
                collision_parts.append(part_id)

        return collision_parts

    def calculate_feasible_range(
        self,
        source_bbox: BBox2D,
        adjacent_bboxes: List[BBox2D],
        max_displacement: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate feasible (dx_min, dx_max, dy_min, dy_max).

        Uses conservative strategy: start with max_displacement bounds,
        then adjust if needed to avoid obvious collisions.

        Args:
            source_bbox: Source part bounding box
            adjacent_bboxes: List of adjacent part bboxes
            max_displacement: Maximum allowed displacement

        Returns:
            Tuple of (dx_min, dx_max, dy_min, dy_max)
        """
        # Start with symmetric bounds
        dx_min = -max_displacement
        dx_max = max_displacement
        dy_min = -max_displacement
        dy_max = max_displacement

        # If no adjacent parts, use full range
        if not adjacent_bboxes:
            return (dx_min, dx_max, dy_min, dy_max)

        # Find the bounding box of all adjacent parts
        all_min_x = min(bbox.min_x for bbox in adjacent_bboxes)
        all_max_x = max(bbox.max_x for bbox in adjacent_bboxes)
        all_min_y = min(bbox.min_y for bbox in adjacent_bboxes)
        all_max_y = max(bbox.max_y for bbox in adjacent_bboxes)

        # Calculate some buffer space around adjacent parts
        # This helps LHS explore useful regions
        buffer = min(source_bbox.width(), source_bbox.height()) * 0.5

        # Extend the feasible range to include space around adjacent parts
        # But don't exceed max_displacement
        source_cx, source_cy = source_bbox.center()

        # Calculate how far we can move before definitely colliding
        # Allow movement beyond adjacent parts with buffer
        suggested_dx_min = max(dx_min, all_min_x - source_bbox.max_x - buffer)
        suggested_dx_max = min(dx_max, all_max_x - source_bbox.min_x + buffer)
        suggested_dy_min = max(dy_min, all_min_y - source_bbox.max_y - buffer)
        suggested_dy_max = min(dy_max, all_max_y - source_bbox.min_y + buffer)

        # Use suggested bounds if they're reasonable
        if suggested_dx_max > suggested_dx_min:
            dx_min = suggested_dx_min
            dx_max = suggested_dx_max
        if suggested_dy_max > suggested_dy_min:
            dy_min = suggested_dy_min
            dy_max = suggested_dy_max

        return (dx_min, dx_max, dy_min, dy_max)

    def sample_lhs(
        self,
        num_samples: int,
        bounds: Tuple[float, float, float, float]
    ) -> np.ndarray:
        """
        Generate LHS samples in feasible region.

        Args:
            num_samples: Number of samples to generate
            bounds: (dx_min, dx_max, dy_min, dy_max)

        Returns:
            Nx2 array of (dx, dy) samples
        """
        dx_min, dx_max, dy_min, dy_max = bounds

        # Create LHS sampler in 2D
        sampler = qmc.LatinHypercube(d=2, seed=42)  # Fixed seed for reproducibility

        # Generate samples in [0, 1]^2
        samples = sampler.random(n=num_samples)

        # Scale to bounds
        samples[:, 0] = dx_min + samples[:, 0] * (dx_max - dx_min)
        samples[:, 1] = dy_min + samples[:, 1] * (dy_max - dy_min)

        return samples

    def calculate_placement_score(
        self,
        source_bbox: BBox2D,
        dx: float,
        dy: float,
        adjacent_bboxes: List[BBox2D]
    ) -> float:
        """
        Calculate quality score for a placement.

        Higher score = better placement (farther from obstacles).

        Args:
            source_bbox: Source part bounding box
            dx, dy: Displacement
            adjacent_bboxes: List of adjacent part bboxes

        Returns:
            Score (0.0 = collision, higher = better)
        """
        displaced_bbox = source_bbox.translate(dx, dy)

        if not adjacent_bboxes:
            return 100.0  # No obstacles, perfect score

        # Calculate minimum distance to any adjacent part
        min_distance = float('inf')

        displaced_cx, displaced_cy = displaced_bbox.center()

        for adj_bbox in adjacent_bboxes:
            adj_cx, adj_cy = adj_bbox.center()

            # Distance between centers
            distance = np.sqrt((displaced_cx - adj_cx)**2 + (displaced_cy - adj_cy)**2)
            min_distance = min(min_distance, distance)

        return min_distance
