#!/usr/bin/env python3
"""Debug voxel marking issue"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from core.KooDynaKeyword import KFileReader
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.adjacent_parts_viewer.core.voxel_collision import VoxelCollisionDetector
from gui.modules.model_viewer.core.mesh_data import MeshData


def main():
    # Load
    reader = KFileReader(
        "examples/DropSet.k",
        parse_nodes=True,
        parse_parts=True,
        parse_elements=True
    )

    parsed = reader._parsed
    nodes_list = list(parsed.nodes)
    elements_list = list(parsed.elements)
    parts_list = list(parsed.parts)

    nodes = np.array([[n.x, n.y, n.z] for n in nodes_list], dtype=np.float32)
    node_id_to_idx = {n.nid: i for i, n in enumerate(nodes_list)}

    part_elements = {}
    part_names = {}
    for part in parts_list:
        part_names[part.pid] = getattr(part, 'name', f'Part {part.pid}')
        part_elements[part.pid] = []

    elements = []
    for elem_idx, elem in enumerate(elements_list):
        node_indices = [node_id_to_idx.get(nid, 0) for nid in elem.nodes if nid != 0]
        elements.append(node_indices)
        if elem.pid in part_elements:
            part_elements[elem.pid].append(elem_idx)

    elements = np.array(elements, dtype=np.int32)
    bounds = (nodes.min(axis=0), nodes.max(axis=0))

    mesh_data = MeshData(
        nodes=nodes,
        elements=elements,
        part_elements=part_elements,
        part_names=part_names,
        element_type="solid",
        bounds=bounds
    )

    # Test
    source_part = 6
    collision_parts = [2, 5, 8, 18]  # From previous test

    detector = VoxelCollisionDetector(mesh_data, voxel_size=0.1)

    # Create grid
    grid = detector.create_voxel_grid(source_part, max_displacement=0.5, z_margin=2.0)

    print(f"Grid origin: {grid.origin}")
    print(f"Grid shape: {grid.grid_shape}")
    print(f"Grid extent: {grid.origin + np.array(grid.grid_shape) * grid.voxel_size}")

    # Check source part bounds
    source_nodes = detector._get_part_nodes(source_part)
    print(f"\nSource part {source_part}:")
    print(f"  Min: {source_nodes.min(axis=0)}")
    print(f"  Max: {source_nodes.max(axis=0)}")

    # Check collision parts bounds
    print(f"\nCollision parts:")
    for pid in collision_parts:
        part_nodes = detector._get_part_nodes(pid)
        part_min = part_nodes.min(axis=0)
        part_max = part_nodes.max(axis=0)
        print(f"\n  Part {pid} ({part_names[pid]}):")
        print(f"    Min: {part_min}")
        print(f"    Max: {part_max}")

        # Check if within grid
        in_grid_x = (part_max[0] >= grid.origin[0] and
                     part_min[0] <= grid.origin[0] + grid.grid_shape[0] * grid.voxel_size)
        in_grid_y = (part_max[1] >= grid.origin[1] and
                     part_min[1] <= grid.origin[1] + grid.grid_shape[1] * grid.voxel_size)
        in_grid_z = (part_max[2] >= grid.origin[2] and
                     part_min[2] <= grid.origin[2] + grid.grid_shape[2] * grid.voxel_size)

        print(f"    In grid X: {in_grid_x}")
        print(f"    In grid Y: {in_grid_y}")
        print(f"    In grid Z: {in_grid_z}")

        if in_grid_x and in_grid_y and in_grid_z:
            print(f"    → Part is within grid, should be marked")
        else:
            print(f"    → Part is OUTSIDE grid!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
