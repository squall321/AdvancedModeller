#!/usr/bin/env python3
"""
Test co-planar filtering with real DropSet.k file.
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
    print("DropSet.k Co-planar Filtering Test")
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

    print(f"   Loaded: {len(nodes):,} nodes, {len(elements):,} elements")

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
    print(f"   Adjacent parts: {len(adjacent_ids)}")

    # Create DOE generator and filter
    print("\n4. Filtering co-planar parts...")
    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    collision_parts, coplanar_parts = generator.filter_coplanar_parts(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        z_tolerance=1.0
    )

    print(f"   Total adjacent: {len(adjacent_ids)}")
    print(f"   Collision check: {len(collision_parts)} parts")
    print(f"   Co-planar (excluded): {len(coplanar_parts)} parts")

    if coplanar_parts:
        print(f"\n   Co-planar parts (likely PCB/mounting surface):")
        for pid in coplanar_parts[:5]:
            name = part_names.get(pid, f'Part {pid}')
            print(f"     Part {pid}: {name}")

    # Generate DOE with filtering
    print("\n5. Generating DOE with co-planar filtering...")
    doe_result = generator.generate_placements(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        num_samples=20,
        max_displacement=20.0,
        enable_resampling=True
    )

    print(f"\n6. Results:")
    print(f"   Valid placements: {doe_result.num_valid}/20")
    print(f"   Success rate: {doe_result.num_valid/20*100:.1f}%")

    if doe_result.num_valid > 0:
        print(f"\n   Sample placements:")
        for i, p in enumerate(doe_result.placements[:5]):
            dist = np.sqrt(p.dx**2 + p.dy**2)
            print(f"   #{i+1}: dx={p.dx:+7.1f}, dy={p.dy:+7.1f}, dist={dist:6.1f} mm")

    print("\n" + "=" * 60)
    if doe_result.num_valid >= 18:  # 90% success
        print("✓ Co-planar filtering SUCCESS")
        print("  - PCB/mounting surface correctly excluded")
        print("  - XY movement now possible")
    else:
        print("⚠ Partial success")
        print(f"  - Got {doe_result.num_valid}/20 valid placements")

    print("=" * 60)

    return 0 if doe_result.num_valid >= 18 else 1


if __name__ == "__main__":
    sys.exit(main())
