#!/usr/bin/env python3
"""
Diagnose 0 valid / 0 total issue.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from core.KooDynaKeyword import KFileReader
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def main():
    print("=" * 60)
    print("Diagnosing 0 valid / 0 total Issue")
    print("=" * 60)

    # Load DropSet.k
    print("\n1. Loading DropSet.k...")
    reader = KFileReader(
        "examples/DropSet.k",
        parse_nodes=True,
        parse_parts=True,
        parse_elements=True
    )

    # Access parsed data
    parsed = reader._parsed
    nodes_list = list(parsed.nodes)
    elements_list = list(parsed.elements)
    parts_list = list(parsed.parts)

    # Build data structures
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

    print(f"   Loaded: {len(nodes):,} nodes, {len(elements):,} elements")

    # Find PKG parts
    pkg_parts = [pid for pid, name in part_names.items() if 'PKG' in name.upper()]
    print(f"   PKG parts found: {pkg_parts}")

    if not pkg_parts:
        print("ERROR: No PKG parts!")
        return 1

    source_part = pkg_parts[0]
    print(f"\n2. Source part: {source_part} - {part_names[source_part]}")

    # Detect adjacent parts
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

    print(f"   Adjacent parts: {len(result.adjacent_parts)}")
    adjacent_ids = list(result.adjacent_parts)
    print(f"   IDs: {adjacent_ids[:5]}..." if len(adjacent_ids) > 5 else f"   IDs: {adjacent_ids}")

    if len(adjacent_ids) == 0:
        print("ERROR: No adjacent parts detected!")
        return 1

    # Create DOE generator
    print("\n4. Creating DOE generator...")
    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    # Test with different max_displacement values
    test_cases = [
        ("User's input", 20.0, 20),  # User's case
        ("Auto-suggested", None, 20),
        ("Small value", 10.0, 20),
        ("Large value", 50.0, 20),
    ]

    for test_name, max_disp, doe_count in test_cases:
        print("\n" + "=" * 60)
        print(f"Test Case: {test_name}")
        print("=" * 60)

        if max_disp is None:
            # Auto-suggest
            max_disp = generator.suggest_max_displacement(source_part, adjacent_ids)
            print(f"Auto-suggested max_displacement: {max_disp:.1f} mm")

        print(f"Parameters: {doe_count} samples, max_disp={max_disp:.1f} mm")

        # Generate
        doe_result = generator.generate_placements(
            source_part_id=source_part,
            adjacent_part_ids=adjacent_ids,
            num_samples=doe_count,
            max_displacement=max_disp,
            enable_resampling=True
        )

        print(f"\nResult: {doe_result.num_valid}/{doe_result.num_total}")
        print(f"Success rate: {doe_result.num_valid/doe_count*100:.1f}%")

        if doe_result.num_valid == 0:
            print("\n⚠ ZERO VALID PLACEMENTS!")
            print(f"Feasible bounds: {doe_result.feasible_bounds}")

            # Additional diagnostics
            source_bbox = generator.get_2d_bbox(source_part)
            print(f"Source bbox: ({source_bbox.min_x:.1f}, {source_bbox.max_x:.1f}), "
                  f"({source_bbox.min_y:.1f}, {source_bbox.max_y:.1f})")
            print(f"Source center: {source_bbox.center()}")
            print(f"Source size: {source_bbox.width():.1f} x {source_bbox.height():.1f}")

            # Check nearest adjacent
            source_cx, source_cy = source_bbox.center()
            min_dist = float('inf')
            nearest_pid = None

            for adj_id in adjacent_ids[:5]:  # Check first 5
                adj_bbox = generator.get_2d_bbox(adj_id)
                adj_cx, adj_cy = adj_bbox.center()
                dist = np.sqrt((source_cx - adj_cx)**2 + (source_cy - adj_cy)**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest_pid = adj_id

            print(f"\nNearest adjacent part: {nearest_pid} at {min_dist:.1f} mm")
            print(f"Max displacement: {max_disp:.1f} mm")
            print(f"Can reach nearest? {'YES' if max_disp >= min_dist else 'NO'}")

        else:
            print(f"✓ Success!")
            # Show first few placements
            for i, p in enumerate(doe_result.placements[:3]):
                dist = np.sqrt(p.dx**2 + p.dy**2)
                print(f"  #{i+1}: dx={p.dx:+7.1f}, dy={p.dy:+7.1f}, dist={dist:6.1f} mm")

    print("\n" + "=" * 60)
    print("Diagnosis Complete")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
