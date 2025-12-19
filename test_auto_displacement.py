#!/usr/bin/env python3
"""
Test auto max_displacement calculation with new algorithm.
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
    print("Auto Max Displacement Calculation Test")
    print("=" * 60)

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

    # Find PKG parts
    pkg_parts = [pid for pid, name in part_names.items() if 'PKG' in name.upper()]
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

    adjacent_ids = list(result.adjacent_parts)
    print(f"   Adjacent parts detected: {len(adjacent_ids)}")

    # Create DOE generator
    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    # Filter co-planar parts
    print("\n4. Filtering co-planar parts...")
    collision_parts, coplanar_parts = generator.filter_coplanar_parts(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        z_tolerance=1.0
    )

    print(f"   Total: {len(adjacent_ids)} adjacent")
    print(f"   Collision check: {len(collision_parts)} parts")
    print(f"   Co-planar (excluded): {len(coplanar_parts)} parts")

    # Calculate clearances manually for verification
    print("\n5. Manual clearance calculation:")
    source_bbox = generator.get_2d_bbox(source_part)
    source_cx, source_cy = source_bbox.center()
    source_size = max(source_bbox.width(), source_bbox.height())

    print(f"   Source size: {source_size:.1f} mm")

    clearances = []
    for coll_id in collision_parts[:5]:  # Check first 5
        coll_bbox = generator.get_2d_bbox(coll_id)
        coll_cx, coll_cy = coll_bbox.center()
        coll_size = max(coll_bbox.width(), coll_bbox.height())

        center_dist = np.sqrt((source_cx - coll_cx)**2 + (source_cy - coll_cy)**2)
        clearance = center_dist - (source_size / 2) - (coll_size / 2)
        clearances.append(clearance)

        print(f"   Part {coll_id}: center_dist={center_dist:.1f}, clearance={clearance:.1f} mm")

    min_clearance = min(clearances) if clearances else 0
    print(f"\n   Minimum clearance: {min_clearance:.1f} mm")

    # Test auto-suggest
    print("\n6. Auto-suggested max_displacement:")

    if len(collision_parts) > 0:
        suggested = generator.suggest_max_displacement(
            source_part_id=source_part,
            adjacent_part_ids=collision_parts
        )
    else:
        suggested = 50.0

    print(f"   Suggested: {suggested:.1f} mm")
    print(f"   Expected: ~{min_clearance * 0.45:.1f} mm (45% of clearance)")
    print(f"   Ratio: {suggested / min_clearance * 100:.1f}% of min clearance")

    # Generate DOE with auto-suggested value
    print("\n7. Generating DOE with auto-suggested max_displacement...")
    doe_result = generator.generate_placements(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        num_samples=20,
        max_displacement=suggested,
        enable_resampling=True
    )

    print(f"\n8. Results:")
    print(f"   Valid placements: {doe_result.num_valid}/20")
    print(f"   Success rate: {doe_result.num_valid/20*100:.1f}%")

    if doe_result.num_valid > 0:
        # Check displacement distribution
        displacements = [np.sqrt(p.dx**2 + p.dy**2) for p in doe_result.placements]
        avg_disp = np.mean(displacements)
        max_disp = max(displacements)

        print(f"\n   Displacement stats:")
        print(f"     Average: {avg_disp:.1f} mm")
        print(f"     Maximum: {max_disp:.1f} mm")
        print(f"     Suggested limit: {suggested:.1f} mm")

        print(f"\n   Sample placements (first 5):")
        for i, p in enumerate(doe_result.placements[:5]):
            dist = np.sqrt(p.dx**2 + p.dy**2)
            print(f"     #{i+1}: dx={p.dx:+6.1f}, dy={p.dy:+6.1f}, dist={dist:5.1f} mm")

    print("\n" + "=" * 60)
    if doe_result.num_valid >= 18:
        print("✓ AUTO-SUGGEST SUCCESS")
        print(f"  - Suggested {suggested:.1f} mm based on {min_clearance:.1f} mm clearance")
        print(f"  - Achieved {doe_result.num_valid}/20 valid placements")
        print(f"  - Appropriate for repositioning (small movements)")
    else:
        print(f"⚠ Partial success: {doe_result.num_valid}/20")

    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
