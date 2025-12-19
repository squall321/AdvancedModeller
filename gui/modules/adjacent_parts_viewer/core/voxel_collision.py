"""
Voxel-based collision detection for DOE placement generation.

This is a more robust approach compared to 2D BBox projection:
- Handles complex 3D geometries accurately
- No false positives from BBox approximation
- Directly computes feasible movement space
"""

import numpy as np
from typing import List, Tuple, Set
from dataclasses import dataclass


@dataclass
class VoxelGrid:
    """3D voxel grid for collision detection"""
    origin: np.ndarray  # (x, y, z) minimum corner
    voxel_size: float   # voxel spacing in mm
    grid_shape: Tuple[int, int, int]  # (nx, ny, nz)
    occupied: np.ndarray  # 3D boolean array

    def world_to_voxel(self, point: np.ndarray) -> Tuple[int, int, int]:
        """Convert world coordinates to voxel indices"""
        voxel_float = (point - self.origin) / self.voxel_size
        return tuple(np.floor(voxel_float).astype(int))

    def voxel_to_world(self, voxel_idx: Tuple[int, int, int]) -> np.ndarray:
        """Convert voxel indices to world coordinates (center)"""
        return self.origin + (np.array(voxel_idx) + 0.5) * self.voxel_size

    def is_valid_index(self, voxel_idx: Tuple[int, int, int]) -> bool:
        """Check if voxel index is within grid bounds"""
        return (0 <= voxel_idx[0] < self.grid_shape[0] and
                0 <= voxel_idx[1] < self.grid_shape[1] and
                0 <= voxel_idx[2] < self.grid_shape[2])

    def mark_occupied(self, voxel_idx: Tuple[int, int, int]):
        """Mark a voxel as occupied"""
        if self.is_valid_index(voxel_idx):
            self.occupied[voxel_idx] = True

    def is_occupied(self, voxel_idx: Tuple[int, int, int]) -> bool:
        """Check if a voxel is occupied"""
        if not self.is_valid_index(voxel_idx):
            return True  # Out of bounds = occupied
        return self.occupied[voxel_idx]


class VoxelCollisionDetector:
    """
    Voxel-based collision detection for DOE placement.

    This method:
    1. Creates a voxel grid around source part
    2. Marks voxels occupied by collision parts
    3. Tests displacements by checking if source+offset overlaps occupied voxels
    """

    def __init__(self, mesh_data, voxel_size: float = 0.1):
        """
        Initialize voxel collision detector.

        Args:
            mesh_data: MeshData object
            voxel_size: Voxel spacing in mm (default 0.1mm for precision)
        """
        self.mesh_data = mesh_data
        self.voxel_size = voxel_size

    def create_voxel_grid(
        self,
        source_part_id: int,
        max_displacement: float,
        z_margin: float = 2.0,
        margin_multiplier: float = 1.5
    ) -> VoxelGrid:
        """
        Create voxel grid around source part with limited extent.

        Grid covers:
        - Source part size
        - + max_displacement in XY directions
        - + margin_multiplier * source_size for safety

        Collision parts outside this grid are ignored (they can't collide anyway).

        Args:
            source_part_id: Source part ID
            max_displacement: Maximum XY displacement
            z_margin: Extra margin in Z direction (mm)
            margin_multiplier: Additional margin as multiple of source size

        Returns:
            VoxelGrid initialized but not yet marked
        """
        # Get source part bounds
        source_nodes = self._get_part_nodes(source_part_id)
        source_min = source_nodes.min(axis=0)
        source_max = source_nodes.max(axis=0)
        source_size = source_max - source_min

        # Calculate XY margin: displacement + small safety buffer
        # For micro-repositioning, we only need source_size + displacement + small margin
        max_source_dim = max(source_size[0], source_size[1])
        xy_margin = max_displacement + max_source_dim * margin_multiplier

        # Grid bounds: source + displacement range + safety margin
        grid_min = source_min.copy()
        grid_max = source_max.copy()

        grid_min[0] -= xy_margin  # X
        grid_max[0] += xy_margin
        grid_min[1] -= xy_margin  # Y
        grid_max[1] += xy_margin
        grid_min[2] -= z_margin   # Z (small, just for Z tolerance)
        grid_max[2] += z_margin

        # Calculate grid shape
        grid_size = grid_max - grid_min
        grid_shape = tuple(np.ceil(grid_size / self.voxel_size).astype(int))

        # Create grid
        occupied = np.zeros(grid_shape, dtype=bool)

        return VoxelGrid(
            origin=grid_min,
            voxel_size=self.voxel_size,
            grid_shape=grid_shape,
            occupied=occupied
        )

    def mark_part_in_grid(self, grid: VoxelGrid, part_id: int):
        """
        Mark all voxels occupied by a part's geometry.

        Args:
            grid: VoxelGrid to mark
            part_id: Part ID to voxelize
        """
        elem_indices = self.mesh_data.part_elements[part_id]
        marked_count = 0

        # For each element, voxelize it
        for elem_idx in elem_indices:
            node_list = self.mesh_data.elements[elem_idx]
            elem_nodes = self.mesh_data.nodes[node_list]

            # Get element bounding box
            elem_min = elem_nodes.min(axis=0)
            elem_max = elem_nodes.max(axis=0)

            # Convert to voxel indices
            voxel_min = grid.world_to_voxel(elem_min)
            voxel_max = grid.world_to_voxel(elem_max)

            # Mark all voxels in this element's bounding box
            # (Conservative: marks entire element bbox)
            i_min = max(0, int(voxel_min[0]))
            i_max = min(grid.grid_shape[0], int(voxel_max[0]) + 1)
            j_min = max(0, int(voxel_min[1]))
            j_max = min(grid.grid_shape[1], int(voxel_max[1]) + 1)
            k_min = max(0, int(voxel_min[2]))
            k_max = min(grid.grid_shape[2], int(voxel_max[2]) + 1)

            for i in range(i_min, i_max):
                for j in range(j_min, j_max):
                    for k in range(k_min, k_max):
                        if not grid.occupied[i, j, k]:
                            grid.occupied[i, j, k] = True
                            marked_count += 1

        return marked_count

    def get_source_voxels(self, grid: VoxelGrid, source_part_id: int) -> Set[Tuple[int, int, int]]:
        """
        Get set of voxel indices occupied by source part.

        Args:
            grid: VoxelGrid
            source_part_id: Source part ID

        Returns:
            Set of (i, j, k) voxel indices
        """
        voxels = set()
        nodes = self._get_part_nodes(source_part_id)
        elem_indices = self.mesh_data.part_elements[source_part_id]

        for elem_idx in elem_indices:
            node_list = self.mesh_data.elements[elem_idx]
            elem_nodes = self.mesh_data.nodes[node_list]

            elem_min = elem_nodes.min(axis=0)
            elem_max = elem_nodes.max(axis=0)

            voxel_min = grid.world_to_voxel(elem_min)
            voxel_max = grid.world_to_voxel(elem_max)

            for i in range(max(0, voxel_min[0]), min(grid.grid_shape[0], voxel_max[0] + 1)):
                for j in range(max(0, voxel_min[1]), min(grid.grid_shape[1], voxel_max[1] + 1)):
                    for k in range(max(0, voxel_min[2]), min(grid.grid_shape[2], voxel_max[2] + 1)):
                        voxels.add((i, j, k))

        return voxels

    def test_displacement(
        self,
        grid: VoxelGrid,
        source_voxels: Set[Tuple[int, int, int]],
        dx: float,
        dy: float
    ) -> bool:
        """
        Test if displacement (dx, dy) causes collision.

        Args:
            grid: VoxelGrid with obstacles marked
            source_voxels: Source part voxel set
            dx, dy: Displacement in mm

        Returns:
            True if valid (no collision), False if collision
        """
        # Convert displacement to voxel units
        dx_voxel = int(round(dx / self.voxel_size))
        dy_voxel = int(round(dy / self.voxel_size))

        # Check each source voxel at new position
        for (i, j, k) in source_voxels:
            new_i = i + dx_voxel
            new_j = j + dy_voxel
            new_k = k  # Z doesn't change

            # Check if new position is occupied
            if not grid.is_valid_index((new_i, new_j, new_k)):
                return False  # Out of bounds

            # Skip if this voxel is part of original source position
            # (source part doesn't collide with itself)
            if (new_i, new_j, new_k) in source_voxels:
                continue

            if grid.occupied[new_i, new_j, new_k]:
                return False  # Collision with obstacle

        return True  # No collision

    def suggest_max_displacement(
        self,
        source_part_id: int,
        collision_part_ids: List[int],
        grid_step: float = 0.1
    ) -> float:
        """
        Suggest max displacement using voxel-based collision detection.

        Args:
            source_part_id: Source part ID
            collision_part_ids: Parts to check collision against
            grid_step: Grid search step size (mm)

        Returns:
            Suggested max displacement (mm)
        """
        print(f"[Voxel Auto] Starting voxel-based auto-suggest")
        print(f"[Voxel Auto] Voxel size: {self.voxel_size:.2f}mm")
        print(f"[Voxel Auto] Grid step: {grid_step:.2f}mm")
        print(f"[Voxel Auto] Collision parts: {len(collision_part_ids)}")

        # Test radii
        test_radii = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0, 15.0, 20.0]

        for radius in test_radii:
            # Create voxel grid (limited to source part + displacement range)
            # margin = radius + 0.5 * source_size (충분한 버퍼)
            grid = self.create_voxel_grid(
                source_part_id, radius, z_margin=1.0,
                margin_multiplier=0.5  # Extra margin = 0.5x source size
            )

            print(f"[Voxel Auto] Radius {radius:.1f}mm: Grid shape {grid.grid_shape}, "
                  f"total voxels: {np.prod(grid.grid_shape):,}")

            # Mark collision parts
            total_marked = 0
            for part_id in collision_part_ids:
                marked = self.mark_part_in_grid(grid, part_id)
                total_marked += marked

            occupied_count = np.sum(grid.occupied)
            print(f"[Voxel Auto]   Marked {total_marked:,} voxels from {len(collision_part_ids)} parts")
            print(f"[Voxel Auto]   Occupied voxels: {occupied_count:,} "
                  f"({occupied_count/np.prod(grid.grid_shape)*100:.1f}%)")

            # Get source voxels
            source_voxels = self.get_source_voxels(grid, source_part_id)
            print(f"[Voxel Auto]   Source voxels: {len(source_voxels)}")

            # Grid search
            valid_count = 0
            steps = int(radius / grid_step)
            total_tests = 0

            for i in range(-steps, steps + 1):
                for j in range(-steps, steps + 1):
                    dx = i * grid_step
                    dy = j * grid_step
                    dist = np.sqrt(dx**2 + dy**2)

                    if dist > radius:
                        continue

                    total_tests += 1

                    if self.test_displacement(grid, source_voxels, dx, dy):
                        valid_count += 1

            success_rate = valid_count / max(1, total_tests) * 100
            print(f"[Voxel Auto]   Valid: {valid_count}/{total_tests} ({success_rate:.1f}%)")

            # If found sufficient valid positions
            if valid_count >= 10:
                print(f"[Voxel Auto] ✓ Found {valid_count} valid positions at {radius:.1f}mm")
                return radius

        print(f"[Voxel Auto] No suitable radius found, using 5.0mm")
        return 5.0

    def find_collisions_voxel(
        self,
        source_part_id: int,
        dx: float,
        dy: float,
        collision_part_ids: List[int],
        grid: VoxelGrid = None
    ) -> List[int]:
        """
        Find which parts collide at given displacement using voxel method.

        Args:
            source_part_id: Source part ID
            dx, dy: Displacement in mm
            collision_part_ids: Parts to check
            grid: Pre-built grid (optional, for efficiency)

        Returns:
            List of part IDs that collide
        """
        # Create grid if not provided
        if grid is None:
            max_disp = max(abs(dx), abs(dy))
            grid = self.create_voxel_grid(source_part_id, max_disp * 1.5, z_margin=2.0)

            # Mark all collision parts
            for part_id in collision_part_ids:
                self.mark_part_in_grid(grid, part_id)

        # Get source voxels
        source_voxels = self.get_source_voxels(grid, source_part_id)

        # Test displacement
        is_valid = self.test_displacement(grid, source_voxels, dx, dy)

        if is_valid:
            return []  # No collision
        else:
            # For now, return all parts if collision detected
            # TODO: Track which specific parts collide
            return collision_part_ids

    def _get_part_nodes(self, part_id: int) -> np.ndarray:
        """Get all node coordinates for a part"""
        elem_indices = self.mesh_data.part_elements[part_id]
        coords = []
        for elem_idx in elem_indices:
            node_list = self.mesh_data.elements[elem_idx]
            elem_coords = self.mesh_data.nodes[node_list]
            coords.append(elem_coords)
        return np.vstack(coords)
