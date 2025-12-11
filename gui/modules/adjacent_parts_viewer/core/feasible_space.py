"""
Feasible space analyzer for DOE placement.

Uses voxel-based occupancy grid to find valid placement regions.
"""

import numpy as np
from typing import List, Tuple, Set
from .spatial_utils import BBox2D


class FeasibleSpaceAnalyzer:
    """Analyzes feasible space for part placement using voxel grid."""

    def __init__(self, voxel_size: float = 1.0):
        """
        Initialize analyzer.

        Args:
            voxel_size: Size of each voxel in mm
        """
        self.voxel_size = voxel_size

    def find_feasible_regions(
        self,
        source_bbox: BBox2D,
        adjacent_bboxes: List[BBox2D],
        max_displacement: float,
        margin: float = 2.0
    ) -> List[Tuple[float, float, float, float]]:
        """
        Find feasible rectangular regions for placement.

        Strategy:
        1. Create voxel grid covering search area
        2. Mark occupied voxels (adjacent parts + margin)
        3. Find connected free regions
        4. Return bounding boxes of free regions

        Args:
            source_bbox: Source part bounding box
            adjacent_bboxes: List of adjacent part bboxes
            max_displacement: Maximum search distance
            margin: Safety margin around obstacles (mm)

        Returns:
            List of (x_min, x_max, y_min, y_max) feasible regions
        """
        if not adjacent_bboxes:
            # No obstacles - entire area is feasible
            cx, cy = source_bbox.center()
            return [(
                cx - max_displacement,
                cx + max_displacement,
                cy - max_displacement,
                cy + max_displacement
            )]

        # Determine grid bounds
        source_cx, source_cy = source_bbox.center()
        grid_min_x = source_cx - max_displacement
        grid_max_x = source_cx + max_displacement
        grid_min_y = source_cy - max_displacement
        grid_max_y = source_cy + max_displacement

        # Create voxel grid
        nx = int(np.ceil((grid_max_x - grid_min_x) / self.voxel_size))
        ny = int(np.ceil((grid_max_y - grid_min_y) / self.voxel_size))

        # Occupancy grid: 0 = free, 1 = occupied
        grid = np.zeros((nx, ny), dtype=np.uint8)

        # Mark occupied regions (adjacent parts + margin)
        for adj_bbox in adjacent_bboxes:
            # Expand by margin
            expanded = BBox2D(
                min_x=adj_bbox.min_x - margin,
                max_x=adj_bbox.max_x + margin,
                min_y=adj_bbox.min_y - margin,
                max_y=adj_bbox.max_y + margin
            )

            # Convert to grid indices
            ix_min = max(0, int((expanded.min_x - grid_min_x) / self.voxel_size))
            ix_max = min(nx, int((expanded.max_x - grid_min_x) / self.voxel_size) + 1)
            iy_min = max(0, int((expanded.min_y - grid_min_y) / self.voxel_size))
            iy_max = min(ny, int((expanded.max_y - grid_min_y) / self.voxel_size) + 1)

            grid[ix_min:ix_max, iy_min:iy_max] = 1

        # For each displacement, check if source would collide
        source_width = source_bbox.width()
        source_height = source_bbox.height()

        # Refine grid: mark cells where placing source would cause collision
        collision_grid = np.zeros((nx, ny), dtype=np.uint8)

        for ix in range(nx):
            for iy in range(ny):
                # World position of this voxel center
                voxel_x = grid_min_x + (ix + 0.5) * self.voxel_size
                voxel_y = grid_min_y + (iy + 0.5) * self.voxel_size

                # Displacement to center source at this voxel
                dx = voxel_x - source_cx
                dy = voxel_y - source_cy

                # Check if displaced source would overlap any adjacent part
                displaced_bbox = source_bbox.translate(dx, dy)

                # Expand slightly for safety
                displaced_bbox = BBox2D(
                    min_x=displaced_bbox.min_x - margin,
                    max_x=displaced_bbox.max_x + margin,
                    min_y=displaced_bbox.min_y - margin,
                    max_y=displaced_bbox.max_y + margin
                )

                # Check collision
                collides = False
                for adj_bbox in adjacent_bboxes:
                    if displaced_bbox.overlaps(adj_bbox):
                        collides = True
                        break

                if collides:
                    collision_grid[ix, iy] = 1

        # Find connected free regions using flood fill
        free_grid = (collision_grid == 0).astype(np.uint8)
        visited = np.zeros((nx, ny), dtype=bool)
        regions = []

        def flood_fill(start_x: int, start_y: int) -> Set[Tuple[int, int]]:
            """Flood fill to find connected free region."""
            region = set()
            stack = [(start_x, start_y)]

            while stack:
                x, y = stack.pop()

                if x < 0 or x >= nx or y < 0 or y >= ny:
                    continue
                if visited[x, y] or free_grid[x, y] == 0:
                    continue

                visited[x, y] = True
                region.add((x, y))

                # 4-connected neighbors
                stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])

            return region

        # Find all connected regions
        for ix in range(nx):
            for iy in range(ny):
                if free_grid[ix, iy] == 1 and not visited[ix, iy]:
                    region = flood_fill(ix, iy)
                    if len(region) > 0:
                        regions.append(region)

        # Convert regions to bounding boxes
        feasible_bboxes = []
        for region in regions:
            if not region:
                continue

            xs = [ix for ix, iy in region]
            ys = [iy for ix, iy in region]

            # Grid indices to world coordinates
            x_min = grid_min_x + min(xs) * self.voxel_size
            x_max = grid_min_x + (max(xs) + 1) * self.voxel_size
            y_min = grid_min_y + min(ys) * self.voxel_size
            y_max = grid_min_y + (max(ys) + 1) * self.voxel_size

            # Only include regions with sufficient area
            area = (x_max - x_min) * (y_max - y_min)
            min_area = (source_width * source_height) * 0.1  # At least 10% of source size

            if area >= min_area:
                feasible_bboxes.append((x_min, x_max, y_min, y_max))

        # Sort by area (largest first)
        feasible_bboxes.sort(key=lambda bbox: (bbox[1] - bbox[0]) * (bbox[3] - bbox[2]), reverse=True)

        return feasible_bboxes

    def sample_from_regions(
        self,
        regions: List[Tuple[float, float, float, float]],
        num_samples: int,
        strategy: str = 'weighted'
    ) -> np.ndarray:
        """
        Sample points from feasible regions using LHS.

        Args:
            regions: List of (x_min, x_max, y_min, y_max) regions
            num_samples: Number of samples to generate
            strategy: 'weighted' (by area) or 'uniform' (equal per region)

        Returns:
            Nx2 array of (dx, dy) samples
        """
        if not regions:
            return np.array([])

        if strategy == 'weighted':
            # Weight by area
            areas = [(bbox[1] - bbox[0]) * (bbox[3] - bbox[2]) for bbox in regions]
            total_area = sum(areas)
            weights = [a / total_area for a in areas]

            # Distribute samples proportionally
            samples_per_region = []
            remaining = num_samples
            for i, weight in enumerate(weights[:-1]):
                count = int(num_samples * weight)
                samples_per_region.append(count)
                remaining -= count
            samples_per_region.append(remaining)  # Last region gets remainder

        else:  # uniform
            base_count = num_samples // len(regions)
            remainder = num_samples % len(regions)
            samples_per_region = [base_count] * len(regions)
            for i in range(remainder):
                samples_per_region[i] += 1

        # Generate samples for each region using LHS
        from scipy.stats import qmc
        all_samples = []

        for region_bbox, count in zip(regions, samples_per_region):
            if count == 0:
                continue

            x_min, x_max, y_min, y_max = region_bbox

            # LHS in [0, 1]^2
            sampler = qmc.LatinHypercube(d=2, seed=None)
            unit_samples = sampler.random(n=count)

            # Scale to region bounds
            scaled_samples = unit_samples.copy()
            scaled_samples[:, 0] = x_min + unit_samples[:, 0] * (x_max - x_min)
            scaled_samples[:, 1] = y_min + unit_samples[:, 1] * (y_max - y_min)

            all_samples.append(scaled_samples)

        if not all_samples:
            return np.array([])

        return np.vstack(all_samples)

    def visualize_grid(
        self,
        source_bbox: BBox2D,
        adjacent_bboxes: List[BBox2D],
        max_displacement: float,
        output_path: str = None
    ):
        """
        Visualize occupancy grid (for debugging).

        Args:
            source_bbox: Source part bbox
            adjacent_bboxes: Adjacent part bboxes
            max_displacement: Max displacement
            output_path: Optional path to save visualization
        """
        try:
            import matplotlib.pyplot as plt

            regions = self.find_feasible_regions(
                source_bbox, adjacent_bboxes, max_displacement
            )

            fig, ax = plt.subplots(figsize=(10, 10))

            # Draw adjacent parts
            for adj_bbox in adjacent_bboxes:
                rect = plt.Rectangle(
                    (adj_bbox.min_x, adj_bbox.min_y),
                    adj_bbox.width(), adj_bbox.height(),
                    color='red', alpha=0.3, label='Adjacent Parts'
                )
                ax.add_patch(rect)

            # Draw source part
            src_rect = plt.Rectangle(
                (source_bbox.min_x, source_bbox.min_y),
                source_bbox.width(), source_bbox.height(),
                color='blue', alpha=0.5, label='Source Part'
            )
            ax.add_patch(src_rect)

            # Draw feasible regions
            for i, (x_min, x_max, y_min, y_max) in enumerate(regions):
                rect = plt.Rectangle(
                    (x_min, y_min),
                    x_max - x_min, y_max - y_min,
                    color='green', alpha=0.2,
                    edgecolor='green', linewidth=2,
                    label='Feasible Region' if i == 0 else None
                )
                ax.add_patch(rect)

            ax.set_xlim(source_bbox.center()[0] - max_displacement * 1.2,
                       source_bbox.center()[0] + max_displacement * 1.2)
            ax.set_ylim(source_bbox.center()[1] - max_displacement * 1.2,
                       source_bbox.center()[1] + max_displacement * 1.2)
            ax.set_aspect('equal')
            ax.legend()
            ax.set_title('Feasible Space Analysis')
            ax.grid(True, alpha=0.3)

            if output_path:
                plt.savefig(output_path)
            else:
                plt.show()

            plt.close()

        except ImportError:
            print("matplotlib not available for visualization")
