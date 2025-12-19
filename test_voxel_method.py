#!/usr/bin/env python3
"""
Test voxel-based collision detection vs legacy BBox method.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from core.KooDynaKeyword import KFileReader
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_both_methods(mesh_data, source_part, collision_parts, part_names):
    """Test both BBox and Voxel methods"""

    print(f"\n{'='*70}")
    print(f"Comparison: BBox vs Voxel Methods")
    print(f"{'='*70}")
    print(f"Source: Part {source_part} - {part_names[source_part]}")
    print(f"Collision parts: {len(collision_parts)}")

    generator = DOEPlacementGenerator(mesh_data, voxel_size=0.1)

    # Test 1: BBox method (legacy)
    print(f"\n{'='*70}")
    print(f"Method 1: Legacy BBox (2D projection)")
    print(f"{'='*70}")

    bbox_suggested = generator.suggest_max_displacement(
        source_part_id=source_part,
        adjacent_part_ids=collision_parts,
        grid_step=0.1,
        use_voxel=False  # Legacy
    )

    print(f"\n→ BBox suggested: {bbox_suggested:.2f} mm")

    # Test 2: Voxel method (new)
    print(f"\n{'='*70}")
    print(f"Method 2: Voxel-Based (3D accurate)")
    print(f"{'='*70}")

    voxel_suggested = generator.suggest_max_displacement(
        source_part_id=source_part,
        adjacent_part_ids=collision_parts,
        grid_step=0.1,
        use_voxel=True  # New method
    )

    print(f"\n→ Voxel suggested: {voxel_suggested:.2f} mm")

    # Comparison
    print(f"\n{'='*70}")
    print(f"Comparison Results")
    print(f"{'='*70}")
    print(f"BBox method:  {bbox_suggested:.2f} mm")
    print(f"Voxel method: {voxel_suggested:.2f} mm")
    print(f"Difference:   {abs(voxel_suggested - bbox_suggested):.2f} mm")

    if abs(voxel_suggested - bbox_suggested) < 0.1:
        print(f"✓ Methods agree (difference < 0.1mm)")
    else:
        print(f"⚠ Methods differ significantly")
        if voxel_suggested > bbox_suggested:
            print(f"  → Voxel found MORE space (BBox was too conservative)")
        else:
            print(f"  → Voxel found LESS space (BBox missed obstacles)")

    return bbox_suggested, voxel_suggested


def main():
    print("="*70)
    print("Voxel vs BBox Method Comparison")
    print("="*70)

    # Load DropSet.k
    print("\n1. Loading DropSet.k...")
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

    print(f"   Loaded: {len(nodes):,} nodes")

    # Test Part 6
    print("\n" + "="*70)
    print("Test Case: Part 6")
    print("="*70)

    source_part = 6
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

    # Filter
    generator = DOEPlacementGenerator(mesh_data, voxel_size=0.1)
    collision_parts, excluded_parts = generator.filter_coplanar_parts(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        z_tolerance=1.0
    )

    print(f"Adjacent: {len(adjacent_ids)}, Collision check: {len(collision_parts)}, Excluded: {len(excluded_parts)}")

    # Compare methods
    bbox_result, voxel_result = test_both_methods(
        mesh_data, source_part, collision_parts, part_names
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
