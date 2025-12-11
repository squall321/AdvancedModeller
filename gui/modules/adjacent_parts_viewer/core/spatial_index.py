"""Octree Spatial Index for Fast Part Queries

O(log n) bounding box queries for adjacent part detection.
"""
import numpy as np
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """3D Axis-Aligned Bounding Box"""
    min_point: np.ndarray  # [x_min, y_min, z_min]
    max_point: np.ndarray  # [x_max, y_max, z_max]

    @property
    def center(self) -> np.ndarray:
        return (self.min_point + self.max_point) / 2.0

    @property
    def size(self) -> np.ndarray:
        return self.max_point - self.min_point

    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this box intersects another"""
        return np.all(self.min_point <= other.max_point) and \
               np.all(other.min_point <= self.max_point)

    def contains_point(self, point: np.ndarray) -> bool:
        """Check if point is inside box"""
        return np.all(point >= self.min_point) and \
               np.all(point <= self.max_point)

    def expand(self, distance: float) -> 'BoundingBox':
        """Expand box by distance in all directions"""
        return BoundingBox(
            self.min_point - distance,
            self.max_point + distance
        )


class OctreeNode:
    """Single node in Octree spatial index"""

    def __init__(self, bbox: BoundingBox, depth: int = 0, max_depth: int = 8):
        self.bbox = bbox
        self.depth = depth
        self.max_depth = max_depth

        # Part IDs in this node
        self.part_ids: Set[int] = set()

        # Children nodes (8 octants)
        self.children: Optional[List['OctreeNode']] = None

        # Leaf node threshold
        self.max_parts_per_node = 10

    def insert(self, part_id: int, part_bbox: BoundingBox):
        """Insert part into octree"""
        # Check if part intersects this node
        if not self.bbox.intersects(part_bbox):
            return

        # If leaf node or max depth, add to this node
        if self.children is None:
            self.part_ids.add(part_id)

            # Split if too many parts and not at max depth
            if len(self.part_ids) > self.max_parts_per_node and \
               self.depth < self.max_depth:
                self._subdivide()
        else:
            # Insert into children
            for child in self.children:
                child.insert(part_id, part_bbox)

    def _subdivide(self):
        """Split node into 8 octants"""
        center = self.bbox.center
        min_p = self.bbox.min_point
        max_p = self.bbox.max_point

        # Create 8 children
        self.children = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    child_min = np.array([
                        min_p[0] if i == 0 else center[0],
                        min_p[1] if j == 0 else center[1],
                        min_p[2] if k == 0 else center[2]
                    ])
                    child_max = np.array([
                        center[0] if i == 0 else max_p[0],
                        center[1] if j == 0 else max_p[1],
                        center[2] if k == 0 else max_p[2]
                    ])

                    child_bbox = BoundingBox(child_min, child_max)
                    child = OctreeNode(
                        child_bbox,
                        self.depth + 1,
                        self.max_depth
                    )
                    self.children.append(child)

        # Redistribute parts to children
        for part_id in self.part_ids:
            # Note: We need part_bbox, but we don't have it here
            # This will be handled differently in actual usage
            pass

        # Keep parts in this node too (overlap handling)

    def query(self, search_bbox: BoundingBox) -> Set[int]:
        """Find all parts intersecting search box"""
        result = set()

        # Check intersection
        if not self.bbox.intersects(search_bbox):
            return result

        # Add parts from this node
        result.update(self.part_ids)

        # Query children
        if self.children:
            for child in self.children:
                result.update(child.query(search_bbox))

        return result


class SpatialIndex:
    """Octree-based spatial index for part lookup

    Provides O(log n) bounding box queries.
    """

    def __init__(self, mesh_data):
        """Initialize spatial index

        Args:
            mesh_data: MeshData object with nodes and elements
        """
        self._mesh = mesh_data
        self._part_bboxes = {}  # part_id -> BoundingBox
        self._root: Optional[OctreeNode] = None

        self._build_index()

    def _build_index(self):
        """Build octree from mesh data"""
        # Compute bounding box for each part
        for part_id in self._mesh.part_ids:
            bbox = self._compute_part_bbox(part_id)
            self._part_bboxes[part_id] = bbox

        # Compute global bounding box
        if not self._part_bboxes:
            return

        all_mins = np.array([bb.min_point for bb in self._part_bboxes.values()])
        all_maxs = np.array([bb.max_point for bb in self._part_bboxes.values()])

        global_min = np.min(all_mins, axis=0)
        global_max = np.max(all_maxs, axis=0)

        # Expand slightly to ensure all parts fit
        margin = 0.01 * (global_max - global_min)
        global_bbox = BoundingBox(global_min - margin, global_max + margin)

        # Create root node
        self._root = OctreeNode(global_bbox, depth=0, max_depth=8)

        # Insert all parts
        for part_id, bbox in self._part_bboxes.items():
            self._root.insert(part_id, bbox)

    def _compute_part_bbox(self, part_id: int) -> BoundingBox:
        """Compute bounding box for a part"""
        # Get element indices for this part
        if part_id not in self._mesh.part_elements:
            # Empty part
            return BoundingBox(np.zeros(3), np.zeros(3))

        elem_indices = self._mesh.part_elements[part_id]

        # Get node indices for all elements in this part
        node_indices = set()
        for elem_idx in elem_indices:
            # elements is (M, 4 or 8) numpy array
            node_list = self._mesh.elements[elem_idx]
            node_indices.update(node_list)

        if not node_indices:
            # Empty part
            return BoundingBox(np.zeros(3), np.zeros(3))

        # Get node coordinates
        # nodes is (N, 3) numpy array
        node_indices = list(node_indices)
        coords = self._mesh.nodes[node_indices]

        min_point = np.min(coords, axis=0)
        max_point = np.max(coords, axis=0)

        return BoundingBox(min_point, max_point)

    def get_part_bbox(self, part_id: int) -> Optional[BoundingBox]:
        """Get cached bounding box for part"""
        return self._part_bboxes.get(part_id)

    def query_region(self, bbox: BoundingBox) -> Set[int]:
        """Find all parts intersecting bounding box

        Args:
            bbox: Search region

        Returns:
            Set of part IDs
        """
        if self._root is None:
            return set()

        return self._root.query(bbox)

    def query_thickness_range(
        self,
        source_part_id: int,
        plane: str,
        thickness_min: float,
        thickness_max: float
    ) -> Set[int]:
        """Find parts within thickness range along plane normal

        Args:
            source_part_id: Source part ID
            plane: 'XY', 'YZ', or 'ZX'
            thickness_min: Minimum distance
            thickness_max: Maximum distance

        Returns:
            Set of candidate part IDs
        """
        source_bbox = self.get_part_bbox(source_part_id)
        if source_bbox is None:
            return set()

        # Determine plane normal direction
        plane_axis = {'XY': 2, 'YZ': 0, 'ZX': 1}[plane]  # Z, X, Y

        # Expand bounding box along normal direction
        # For in-plane directions, use full model extent to find all parts at same layer
        search_min = source_bbox.min_point.copy()
        search_max = source_bbox.max_point.copy()

        # Expand along normal axis by thickness range
        search_min[plane_axis] -= thickness_max
        search_max[plane_axis] += thickness_max

        # For in-plane axes, use global bounds to find parts at same layer
        # (This allows finding PCB packages at different XY positions but same Z-height)
        for axis in range(3):
            if axis != plane_axis:
                search_min[axis] = -1e10  # Very large negative
                search_max[axis] = 1e10   # Very large positive

        search_bbox = BoundingBox(search_min, search_max)

        # Query octree
        candidates = self.query_region(search_bbox)

        # Remove source part
        candidates.discard(source_part_id)

        # Filter by actual distance (refine)
        result = set()
        for cand_id in candidates:
            cand_bbox = self.get_part_bbox(cand_id)
            if cand_bbox is None:
                continue

            # Check distance along normal axis
            dist = self._bbox_distance_along_axis(
                source_bbox, cand_bbox, plane_axis
            )

            # Accept if within max distance (0 means overlapping/touching, which is perfect!)
            if dist <= thickness_max:
                result.add(cand_id)

        return result

    def _bbox_distance_along_axis(
        self,
        bbox1: BoundingBox,
        bbox2: BoundingBox,
        axis: int
    ) -> float:
        """Compute minimum distance between boxes along axis"""
        # Distance along axis
        dist1 = bbox2.min_point[axis] - bbox1.max_point[axis]
        dist2 = bbox1.min_point[axis] - bbox2.max_point[axis]

        # Minimum positive distance (0 if overlapping)
        return max(0, dist1, dist2)
