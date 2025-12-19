#!/usr/bin/env python3
"""
Test grid-based search in specific directions to understand geometry.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from core.KooDynaKeyword import KFileReader
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_directions(generator, source_bbox, collision_parts, adjacent_bboxes):
    """Test specific directions to find where valid space is"""

    print("\n" + "="*60)
    print("Directional Analysis")
    print("="*60)

    # Test cardinal directions at various distances
    directions = [
        ("+X", 1, 0),
        ("-X", -1, 0),
        ("+Y", 0, 1),
        ("-Y", 0, -1),
        ("+X+Y", 0.707, 0.707),
        ("-X+Y", -0.707, 0.707),
        ("+X-Y", 0.707, -0.707),
        ("-X-Y", -0.707, -0.707),
    ]

    test_distances = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0]

    print("\nTesting directions at various distances:")
    print(f"{'Direction':<8} " + " ".join(f"{d:>5.1f}" for d in test_distances))
    print("-" * 60)

    for dir_name, dx_unit, dy_unit in directions:
        results = []
        for dist in test_distances:
            dx = dx_unit * dist
            dy = dy_unit * dist

            collisions = generator.find_collisions(
                source_bbox, dx, dy, collision_parts, adjacent_bboxes
            )

            is_valid = "✓" if len(collisions) == 0 else "✗"
            results.append(is_valid)

        print(f"{dir_name:<8} " + " ".join(f"{r:>5}" for r in results))

    print("\n✓ = valid position (no collision)")
    print("✗ = collision detected")


def main():
    print("="*60)
    print("Grid Direction Analysis")
    print("="*60)

    # Load DropSet.k
    print("\nLoading DropSet.k...")
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

    # Find PKG and detect
    pkg_parts = [pid for pid, name in part_names.items() if 'PKG' in name.upper()]
    source_part = pkg_parts[0]

    print(f"Source part: {source_part} - {part_names[source_part]}")

    detector = AdjacentPartsDetector(mesh_data)
    result = detector.find_adjacent(
        source_part_id=source_part,
        plane='XY',
        thickness_min=0.0,
        thickness_max=50.0,
        check_facing=True,
        ray_density=0.1,
        coverage_threshold=0.1,
        visualize=False,
        layer_mode=True
    )

    adjacent_ids = list(result.adjacent_parts)

    # Create generator and filter
    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)
    collision_parts, coplanar_parts = generator.filter_coplanar_parts(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        z_tolerance=1.0
    )

    print(f"\nAdjacent parts: {len(adjacent_ids)}")
    print(f"Collision check: {len(collision_parts)} parts")
    print(f"Co-planar (excluded): {len(coplanar_parts)} parts")

    # Get bboxes
    source_bbox = generator.get_2d_bbox(source_part)
    adjacent_bboxes = [generator.get_2d_bbox(pid) for pid in collision_parts]

    # Run directional test
    test_directions(generator, source_bbox, collision_parts, adjacent_bboxes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
