"""
Spatial utilities for 2D bounding box operations.

This module provides data structures and utilities for working with
2D bounding boxes in the XY plane, used for DOE placement collision detection.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class BBox2D:
    """2D bounding box in XY plane."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    def overlaps(self, other: 'BBox2D') -> bool:
        """
        Check if this bbox overlaps with another in 2D.

        Args:
            other: Another BBox2D to check against

        Returns:
            True if bboxes overlap, False otherwise
        """
        x_overlap = not (self.max_x < other.min_x or self.min_x > other.max_x)
        y_overlap = not (self.max_y < other.min_y or self.min_y > other.max_y)
        return x_overlap and y_overlap

    def width(self) -> float:
        """Get width of bbox in X direction."""
        return self.max_x - self.min_x

    def height(self) -> float:
        """Get height of bbox in Y direction."""
        return self.max_y - self.min_y

    def center(self) -> Tuple[float, float]:
        """Get center point of bbox."""
        return (
            (self.min_x + self.max_x) / 2.0,
            (self.min_y + self.max_y) / 2.0
        )

    def expand(self, dx: float, dy: float) -> 'BBox2D':
        """
        Expand bbox by specified amounts in each direction.

        Args:
            dx: Amount to expand in X direction (added to both sides)
            dy: Amount to expand in Y direction (added to both sides)

        Returns:
            New expanded BBox2D
        """
        return BBox2D(
            min_x=self.min_x - dx,
            max_x=self.max_x + dx,
            min_y=self.min_y - dy,
            max_y=self.max_y + dy
        )

    def translate(self, dx: float, dy: float) -> 'BBox2D':
        """
        Translate bbox by displacement.

        Args:
            dx: Displacement in X direction
            dy: Displacement in Y direction

        Returns:
            New translated BBox2D
        """
        return BBox2D(
            min_x=self.min_x + dx,
            max_x=self.max_x + dx,
            min_y=self.min_y + dy,
            max_y=self.max_y + dy
        )

    @staticmethod
    def from_points(points: np.ndarray) -> 'BBox2D':
        """
        Create BBox2D from array of XY points.

        Args:
            points: Nx2 or Nx3 numpy array of coordinates

        Returns:
            BBox2D enclosing all points
        """
        if points.shape[1] >= 2:
            return BBox2D(
                min_x=float(np.min(points[:, 0])),
                max_x=float(np.max(points[:, 0])),
                min_y=float(np.min(points[:, 1])),
                max_y=float(np.max(points[:, 1]))
            )
        else:
            raise ValueError("Points array must have at least 2 columns (X, Y)")


@dataclass
class Placement:
    """Represents a single DOE placement option."""
    index: int              # Placement option number (0, 1, 2, ...)
    dx: float               # X displacement
    dy: float               # Y displacement
    is_valid: bool          # True if no collision
    collision_parts: List[int]  # Part IDs that collide (empty if valid)
    center: np.ndarray      # [x+dx, y+dy, z] displaced center
    score: float = 0.0      # Quality metric (distance to nearest obstacle)

    def __repr__(self) -> str:
        status = "VALID" if self.is_valid else "COLLISION"
        return f"Placement({self.index}: dx={self.dx:.2f}, dy={self.dy:.2f}, {status})"


@dataclass
class DOEResult:
    """Result of DOE placement generation."""
    source_part_id: int
    source_center: np.ndarray     # Original [x, y, z]
    placements: List[Placement]   # All DOE placement options
    num_valid: int                # Count of collision-free placements
    num_total: int                # Total samples attempted
    max_displacement: float       # Max displacement used
    feasible_bounds: Tuple[float, float, float, float]  # (dx_min, dx_max, dy_min, dy_max)

    def get_valid_placements(self) -> List[Placement]:
        """Get only valid (collision-free) placements."""
        return [p for p in self.placements if p.is_valid]

    def __repr__(self) -> str:
        return f"DOEResult(source={self.source_part_id}, valid={self.num_valid}/{self.num_total})"
