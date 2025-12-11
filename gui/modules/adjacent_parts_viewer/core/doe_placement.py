"""
DOE-based placement generator using Latin Hypercube Sampling.

This module generates multiple placement options for a source part by:
1. Sampling the XY space uniformly using LHS
2. Checking collision with adjacent parts
3. Filtering valid placements
"""

from typing import List, Tuple
import numpy as np
from scipy.stats import qmc

from gui.modules.model_viewer.core.mesh_data import MeshData
from .spatial_utils import BBox2D, Placement, DOEResult
from .feasible_space import FeasibleSpaceAnalyzer


class DOEPlacementGenerator:
    """Generates DOE-based placement options for package positioning."""

    def __init__(self, mesh_data: MeshData, voxel_size: float = 2.0):
        """
        Initialize generator with mesh data.

        Args:
            mesh_data: MeshData containing part geometry
            voxel_size: Voxel size for feasible space analysis (mm)
        """
        self.mesh_data = mesh_data
        self.feasible_analyzer = FeasibleSpaceAnalyzer(voxel_size=voxel_size)

    def suggest_max_displacement(
        self,
        source_part_id: int,
        adjacent_part_ids: List[int]
    ) -> float:
        """
        Suggest appropriate max_displacement based on adjacent package distances.

        Strategy:
        - Find distance to nearest adjacent package
        - Return 1.5x to 2.0x that distance as max displacement
        - Ensures samples explore meaningful space without going too far

        Args:
            source_part_id: Source part ID
            adjacent_part_ids: List of adjacent part IDs

        Returns:
            Suggested max_displacement in mm
        """
        if not adjacent_part_ids:
            return 100.0  # Default if no adjacent parts

        # Get source part bbox
        source_bbox = self.get_2d_bbox(source_part_id)
        source_cx, source_cy = source_bbox.center()

        # Get adjacent part bboxes
        adjacent_bboxes = [self.get_2d_bbox(pid) for pid in adjacent_part_ids]

        # Find minimum distance to any adjacent package center
        min_distance = float('inf')

        for adj_bbox in adjacent_bboxes:
            adj_cx, adj_cy = adj_bbox.center()
            distance = np.sqrt((source_cx - adj_cx)**2 + (source_cy - adj_cy)**2)
            min_distance = min(min_distance, distance)

        # Use 1.5x to 2.0x nearest neighbor distance
        # But subtract half the source size to get clearance-based distance
        source_size = max(source_bbox.width(), source_bbox.height())
        clearance = min_distance - source_size / 2

        # Suggested displacement: 1.5x clearance
        suggested = clearance * 1.5

        # Clamp to reasonable range
        return max(min(suggested, 500.0), 20.0)  # Between 20mm and 500mm

    def generate_placements(
        self,
        source_part_id: int,
        adjacent_part_ids: List[int],
        num_samples: int,
        max_displacement: float,
        enable_resampling: bool = True
    ) -> DOEResult:
        """
        Generate DOE-based placement options.

        Args:
            source_part_id: Part ID to generate placements for
            adjacent_part_ids: List of adjacent part IDs to avoid
            num_samples: Number of placement samples to generate
            max_displacement: Maximum XY displacement in mm
            enable_resampling: If True, resample to meet desired count

        Returns:
            DOEResult with placements and metadata
        """
        # Get source part geometry
        source_bbox = self.get_2d_bbox(source_part_id)
        source_center_3d = self.get_part_center(source_part_id)

        # Get adjacent part bboxes
        adjacent_bboxes = [
            self.get_2d_bbox(pid) for pid in adjacent_part_ids
        ]

        # Find feasible regions using voxel-based analysis
        feasible_regions = self.feasible_analyzer.find_feasible_regions(
            source_bbox=source_bbox,
            adjacent_bboxes=adjacent_bboxes,
            max_displacement=max_displacement,
            margin=2.0  # 2mm safety margin
        )

        # Calculate overall feasible bounds for metadata
        if feasible_regions:
            all_x_mins = [r[0] for r in feasible_regions]
            all_x_maxs = [r[1] for r in feasible_regions]
            all_y_mins = [r[2] for r in feasible_regions]
            all_y_maxs = [r[3] for r in feasible_regions]
            feasible_bounds = (
                min(all_x_mins), max(all_x_maxs),
                min(all_y_mins), max(all_y_maxs)
            )
        else:
            # Fallback to old method
            feasible_bounds = self.calculate_feasible_range(
                source_bbox, adjacent_bboxes, max_displacement
            )
            feasible_regions = [(
                feasible_bounds[0], feasible_bounds[1],
                feasible_bounds[2], feasible_bounds[3]
            )]

        # Keep sampling until we get num_samples valid placements
        source_cx, source_cy = source_bbox.center()
        placements = []
        num_valid = 0
        placement_idx = 0
        max_attempts = 20 if enable_resampling else 1
        attempt = 0

        # Batch size: start with requested amount, increase if needed
        batch_size = num_samples

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

        while num_valid < num_samples and attempt < max_attempts:
            # Sample from feasible regions
            samples_world = self.feasible_analyzer.sample_from_regions(
                regions=feasible_regions,
                num_samples=batch_size,
                strategy='weighted'
            )

            if len(samples_world) == 0:
                # No samples possible, try fallback
                if attempt == 0:
                    samples_world = self.sample_lhs(batch_size, feasible_bounds)
                    samples_world = np.column_stack([
                        samples_world[:, 0] + source_cx,
                        samples_world[:, 1] + source_cy
                    ])
                else:
                    break  # Give up

            # Convert world coordinates to displacements
            samples = np.column_stack([
                samples_world[:, 0] - source_cx,  # dx
                samples_world[:, 1] - source_cy   # dy
            ])

            # Process each sample
            for dx, dy in samples:
                if num_valid >= num_samples:
                    break  # Got enough valid placements

                # Check max_displacement constraint first
                displacement = np.sqrt(dx**2 + dy**2)
                if displacement > max_displacement:
                    continue

                # Check collision
                collision_parts = self.find_collisions(
                    source_bbox, dx, dy, adjacent_part_ids, adjacent_bboxes
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

            # If we still need more, increase batch size for next attempt
            if num_valid < num_samples:
                needed = num_samples - num_valid
                batch_size = needed * 3  # Generate 3x what we need
                attempt += 1

        # Log if we couldn't meet the target
        if num_valid < num_samples:
            print(f"⚠ WARNING: Could only generate {num_valid}/{num_samples} valid placements")
            print(f"  Attempts made: {attempt}")
            print(f"  Max displacement: {max_displacement:.1f} mm")
            print(f"  Feasible regions: {len(feasible_regions)}")
            if feasible_regions:
                total_area = sum((r[1]-r[0])*(r[3]-r[2]) for r in feasible_regions)
                print(f"  Total feasible area: {total_area:.1f} mm²")

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
