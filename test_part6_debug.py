#!/usr/bin/env python3
"""
Debug Part 6 micro-repositioning - should find valid positions at 0.1mm scale
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from core.KooDynaKeyword import KFileReader
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_micro_movements(generator, source_part, collision_parts):
    """Test very small movements (0.1mm increments)"""

    print("\n" + "="*70)
    print("Micro-Movement Test (0.1mm increments)")
    print("="*70)

    source_bbox = generator.get_2d_bbox(source_part)
    adjacent_bboxes = [generator.get_2d_bbox(pid) for pid in collision_parts]

    print(f"\nSource Part {source_part} BBox:")
    print(f"  X: [{source_bbox.min_x:.2f}, {source_bbox.max_x:.2f}] (width: {source_bbox.width():.2f}mm)")
    print(f"  Y: [{source_bbox.min_y:.2f}, {source_bbox.max_y:.2f}] (height: {source_bbox.height():.2f}mm)")

    print(f"\nCollision Parts BBoxes:")
    for pid in collision_parts:
        bbox = generator.get_2d_bbox(pid)
        print(f"  Part {pid}: X=[{bbox.min_x:.2f}, {bbox.max_x:.2f}], Y=[{bbox.min_y:.2f}, {bbox.max_y:.2f}]")

    # Test small movements in all directions
    step = 0.1
    test_range = 2.0  # Test up to 2mm

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

    print(f"\nTesting {step}mm increments up to {test_range}mm:")
    print(f"{'Dir':<8} ", end="")
    test_dists = [0.1, 0.2, 0.5, 1.0, 1.5, 2.0]
    for d in test_dists:
        print(f"{d:>6.1f}", end="")
    print(" mm")
    print("-" * 60)

    for dir_name, dx_unit, dy_unit in directions:
        results = []
        for dist in test_dists:
            dx = dx_unit * dist
            dy = dy_unit * dist

            collisions = generator.find_collisions(
                source_bbox, dx, dy, collision_parts, adjacent_bboxes
            )

            is_valid = "✓" if len(collisions) == 0 else "✗"
            results.append(is_valid)

        print(f"{dir_name:<8} ", end="")
        for r in results:
            print(f"{r:>6}", end="")
        print()

    # Count valid positions in 2mm radius with 0.1mm grid
    print(f"\nGrid search (2mm radius, {step}mm step):")
    valid_count = 0
    total_count = 0
    valid_positions = []

    steps = int(test_range / step)
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            dx = i * step
            dy = j * step
            dist = np.sqrt(dx**2 + dy**2)

            if dist > test_range:
                continue

            total_count += 1
            collisions = generator.find_collisions(
                source_bbox, dx, dy, collision_parts, adjacent_bboxes
            )

            if len(collisions) == 0:
                valid_count += 1
                if len(valid_positions) < 10:
                    valid_positions.append((dx, dy, dist))

    print(f"  Valid: {valid_count}/{total_count} positions ({valid_count/max(1,total_count)*100:.1f}%)")

    if valid_positions:
        print(f"\n  First 10 valid positions:")
        for dx, dy, dist in valid_positions[:10]:
            print(f"    dx={dx:+6.2f}, dy={dy:+6.2f}, dist={dist:5.2f}mm")
    else:
        print(f"  ⚠ No valid positions found!")


def main():
    print("="*70)
    print("Part 6 Micro-Repositioning Debug")
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
    source_part = 6
    print(f"\n2. Source part: {source_part} - {part_names[source_part]}")

    # Detect adjacent
    print("\n3. Detecting adjacent parts...")
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
    print(f"   Adjacent parts: {len(adjacent_ids)}")

    # Filter coplanar
    print("\n4. Filtering co-planar parts...")
    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)
    collision_parts, coplanar_parts = generator.filter_coplanar_parts(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        z_tolerance=1.0
    )

    print(f"   Total: {len(adjacent_ids)} adjacent")
    print(f"   Collision check: {len(collision_parts)} parts")
    print(f"   Co-planar (excluded): {len(coplanar_parts)} parts")

    if coplanar_parts:
        print(f"\n   Co-planar parts:")
        for pid in coplanar_parts:
            print(f"     Part {pid}: {part_names.get(pid, '?')}")

    # Test micro movements
    test_micro_movements(generator, source_part, collision_parts)

    # Test auto-suggest
    print("\n" + "="*70)
    print("Auto-Suggest Test")
    print("="*70)

    suggested = generator.suggest_max_displacement(
        source_part_id=source_part,
        adjacent_part_ids=collision_parts,
        grid_step=0.1
    )

    print(f"\nSuggested: {suggested:.2f}mm")
    print(f"Expected: ~0.5-2.0mm (micro-repositioning range)")

    if suggested > 5.0:
        print(f"⚠ WARNING: Suggested value too large!")
        print(f"  Should be in 0.5-2mm range for micro-repositioning")
        return 1
    else:
        print(f"✓ Suggested value in reasonable range")
        return 0


if __name__ == "__main__":
    sys.exit(main())
