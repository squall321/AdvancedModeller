"""2D Projection and Outline Extraction

Projects 3D parts to 2D planes and extracts outlines using Convex Hull.
"""
import numpy as np
from typing import List, Tuple, Optional
from scipy.spatial import ConvexHull
from dataclasses import dataclass


@dataclass
class ProjectedOutline:
    """2D outline of a projected part"""
    points: np.ndarray  # Nx2 array of 2D points
    area: float  # Projected area
    perimeter: float  # Outline perimeter
    method: str  # 'convex_hull' or 'alpha_shape'


class ProjectionEngine:
    """Projects 3D parts to 2D planes and extracts outlines"""

    def __init__(self, mesh_data):
        """Initialize projection engine

        Args:
            mesh_data: MeshData object
        """
        self._mesh = mesh_data
        self._projection_cache = {}  # (part_id, plane) -> ProjectedOutline

    def project_part(
        self,
        part_id: int,
        plane: str,
        method: str = 'convex_hull'
    ) -> Optional[ProjectedOutline]:
        """Project part to 2D plane and extract outline

        Args:
            part_id: Part ID
            plane: 'XY', 'YZ', or 'ZX'
            method: 'convex_hull' or 'alpha_shape'

        Returns:
            ProjectedOutline with 2D points
        """
        cache_key = (part_id, plane, method)
        if cache_key in self._projection_cache:
            return self._projection_cache[cache_key]

        # Get all nodes in this part
        node_ids = self._get_part_node_ids(part_id)
        if not node_ids:
            return None

        # Get 3D coordinates
        # nodes is (N, 3) numpy array, node_ids are indices
        node_ids_list = list(node_ids)

        if len(node_ids_list) < 3:
            return None

        coords_3d = self._mesh.nodes[node_ids_list]

        # Project to 2D
        coords_2d = self._project_to_plane(coords_3d, plane)

        # Extract outline
        if method == 'convex_hull':
            outline = self._extract_convex_hull(coords_2d)
        elif method == 'alpha_shape':
            # Alpha shape not implemented yet - fall back to convex hull
            outline = self._extract_convex_hull(coords_2d)
        else:
            return None

        if outline is None:
            return None

        # Compute area and perimeter
        area = self._compute_polygon_area(outline)
        perimeter = self._compute_perimeter(outline)

        result = ProjectedOutline(outline, area, perimeter, method)
        self._projection_cache[cache_key] = result

        return result

    def _get_part_node_ids(self, part_id: int) -> set:
        """Get all node IDs used by a part"""
        node_ids = set()

        # Get element indices for this part
        if part_id not in self._mesh.part_elements:
            return node_ids

        elem_indices = self._mesh.part_elements[part_id]

        for elem_idx in elem_indices:
            # elements is (M, 4 or 8) numpy array
            node_list = self._mesh.elements[elem_idx]
            node_ids.update(node_list)

        return node_ids

    def _project_to_plane(
        self,
        coords_3d: np.ndarray,
        plane: str
    ) -> np.ndarray:
        """Project 3D coordinates to 2D plane

        Args:
            coords_3d: Nx3 array
            plane: 'XY', 'YZ', or 'ZX'

        Returns:
            Nx2 array
        """
        if plane == 'XY':
            # Project to XY plane (drop Z)
            return coords_3d[:, :2]  # X, Y
        elif plane == 'YZ':
            # Project to YZ plane (drop X)
            return coords_3d[:, 1:]  # Y, Z
        elif plane == 'ZX':
            # Project to ZX plane (drop Y)
            return coords_3d[:, [2, 0]]  # Z, X
        else:
            raise ValueError(f"Invalid plane: {plane}")

    def _extract_convex_hull(
        self,
        points_2d: np.ndarray
    ) -> Optional[np.ndarray]:
        """Extract convex hull outline from 2D points

        Args:
            points_2d: Nx2 array

        Returns:
            Mx2 array of outline points (ordered)
        """
        if len(points_2d) < 3:
            return None

        # Remove duplicate points
        unique_points = np.unique(points_2d, axis=0)

        if len(unique_points) < 3:
            return None

        try:
            hull = ConvexHull(unique_points)
            # Get vertices in order
            outline_points = unique_points[hull.vertices]
            return outline_points
        except Exception:
            # Degenerate case (collinear points, etc.)
            return None

    def _compute_polygon_area(self, points: np.ndarray) -> float:
        """Compute area of 2D polygon using shoelace formula

        Args:
            points: Nx2 array (ordered vertices)

        Returns:
            Area
        """
        if len(points) < 3:
            return 0.0

        x = points[:, 0]
        y = points[:, 1]

        # Shoelace formula
        area = 0.5 * np.abs(
            np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))
        )

        return area

    def _compute_perimeter(self, points: np.ndarray) -> float:
        """Compute perimeter of 2D polygon

        Args:
            points: Nx2 array (ordered vertices)

        Returns:
            Perimeter length
        """
        if len(points) < 2:
            return 0.0

        # Compute distances between consecutive points
        # Add first point at end to close the loop
        closed_points = np.vstack([points, points[0]])
        diffs = np.diff(closed_points, axis=0)
        distances = np.linalg.norm(diffs, axis=1)

        return np.sum(distances)

    def distribute_rays_on_outline(
        self,
        outline: ProjectedOutline,
        num_rays: int = None,
        density: float = None
    ) -> np.ndarray:
        """Distribute ray origins along outline

        Args:
            outline: ProjectedOutline
            num_rays: Fixed number of rays (overrides density)
            density: Rays per unit length

        Returns:
            Nx2 array of ray origin points
        """
        if outline is None or len(outline.points) < 2:
            return np.array([])

        # Determine number of rays
        if num_rays is None:
            if density is None:
                density = 0.1  # Default: 1 ray per 10 units
            num_rays = max(10, int(outline.perimeter * density))

        # Sample points along outline perimeter
        ray_origins = self._sample_along_perimeter(
            outline.points, num_rays
        )

        return ray_origins

    def _sample_along_perimeter(
        self,
        points: np.ndarray,
        num_samples: int
    ) -> np.ndarray:
        """Sample points uniformly along polygon perimeter

        Args:
            points: Nx2 ordered vertices
            num_samples: Number of samples

        Returns:
            Mx2 sampled points
        """
        if len(points) < 2 or num_samples < 1:
            return points

        # Compute cumulative edge lengths
        closed_points = np.vstack([points, points[0]])
        edges = np.diff(closed_points, axis=0)
        edge_lengths = np.linalg.norm(edges, axis=1)
        cumulative_lengths = np.concatenate([[0], np.cumsum(edge_lengths)])
        total_length = cumulative_lengths[-1]

        # Sample uniformly along perimeter
        sample_positions = np.linspace(0, total_length, num_samples, endpoint=False)

        sampled_points = []
        for pos in sample_positions:
            # Find which edge this position is on
            edge_idx = np.searchsorted(cumulative_lengths, pos, side='right') - 1
            edge_idx = min(edge_idx, len(points) - 1)

            # Interpolate along edge
            t = (pos - cumulative_lengths[edge_idx]) / edge_lengths[edge_idx]
            t = np.clip(t, 0, 1)

            p0 = points[edge_idx]
            p1 = points[(edge_idx + 1) % len(points)]

            sampled_point = p0 + t * (p1 - p0)
            sampled_points.append(sampled_point)

        return np.array(sampled_points)

    def restore_3d_point(
        self,
        point_2d: np.ndarray,
        plane: str,
        z_value: float = 0.0
    ) -> np.ndarray:
        """Convert 2D projected point back to 3D

        Args:
            point_2d: [x, y] in 2D
            plane: 'XY', 'YZ', or 'ZX'
            z_value: Value for the dropped axis

        Returns:
            [x, y, z] in 3D
        """
        if plane == 'XY':
            return np.array([point_2d[0], point_2d[1], z_value])
        elif plane == 'YZ':
            return np.array([z_value, point_2d[0], point_2d[1]])
        elif plane == 'ZX':
            return np.array([point_2d[1], z_value, point_2d[0]])
        else:
            raise ValueError(f"Invalid plane: {plane}")

    def clear_cache(self):
        """Clear projection cache"""
        self._projection_cache.clear()
