#!/usr/bin/env python3
"""
Test DOE with real DropSet.k file.
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
    print("DOE Real File Test (DropSet.k)")
    print("=" * 60)

    # Load DropSet.k
    print("\n1. Loading DropSet.k...")
    try:
        reader = KFileReader(
            "examples/DropSet.k",
            parse_nodes=True,
            parse_parts=True,
            parse_elements=True
        )
    except Exception as e:
        print(f"Error loading file: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Access parsed data
    parsed = reader._parsed

    # Convert iterables to lists and create dictionaries
    nodes_list = list(parsed.nodes)
    elements_list = list(parsed.elements)
    parts_list = list(parsed.parts)

    # Build data structures similar to what MeshData expects
    nodes = np.array([[n.x, n.y, n.z] for n in nodes_list], dtype=np.float32)

    # Build elements array (node indices for each element)
    elements = []
    part_elements = {}  # part_id -> [element_indices]
    part_names = {}  # part_id -> name

    # Map node IDs to indices
    node_id_to_idx = {n.nid: i for i, n in enumerate(nodes_list)}

    # Build part info
    for part in parts_list:
        part_id = part.pid
        part_name = getattr(part, 'name', f'Part {part_id}')
        part_names[part_id] = part_name
        part_elements[part_id] = []

    # Build elements
    for elem_idx, elem in enumerate(elements_list):
        # Convert node IDs to indices
        node_indices = [node_id_to_idx.get(nid, 0) for nid in elem.nodes if nid != 0]
        elements.append(node_indices)

        # Associate with part
        if elem.pid in part_elements:
            part_elements[elem.pid].append(elem_idx)

    elements = np.array(elements, dtype=np.int32)

    print(f"   Loaded: {len(nodes):,} nodes, {len(elements):,} elements")
    print(f"   Parts: {len(part_elements)}")

    # Calculate bounds
    bounds = (nodes.min(axis=0), nodes.max(axis=0))

    # Create MeshData
    mesh_data = MeshData(
        nodes=nodes,
        elements=elements,
        part_elements=part_elements,
        part_names=part_names,
        element_type="solid",
        bounds=bounds
    )

    # Select a source part (PKG)
    pkg_parts = [pid for pid, name in part_names.items() if 'PKG' in name.upper()]
    if not pkg_parts:
        print("No PKG parts found!")
        return 1

    source_part = pkg_parts[0]
    print(f"\n2. Source part: {source_part} - {part_names.get(source_part, 'Unknown')}")

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

    print(f"   Found {len(result.adjacent_parts)} adjacent parts")
    if len(result.adjacent_parts) == 0:
        print("   No adjacent parts found - trying another source part...")
        if len(pkg_parts) > 1:
            source_part = pkg_parts[1]
            print(f"   Trying part {source_part}")
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
            print(f"   Found {len(result.adjacent_parts)} adjacent parts")

    if len(result.adjacent_parts) == 0:
        print("   Still no adjacent parts - cannot test DOE")
        return 1

    adjacent_ids = list(result.adjacent_parts)
    print(f"   Adjacent part IDs: {adjacent_ids[:5]}{'...' if len(adjacent_ids) > 5 else ''}")

    # Generate DOE placements
    print("\n4. Generating DOE placements...")
    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    # Auto-suggest max displacement
    suggested_disp = generator.suggest_max_displacement(source_part, adjacent_ids)
    print(f"   Auto-suggested max_displacement: {suggested_disp:.1f} mm")

    # Generate with suggested displacement
    doe_count = 20
    print(f"   Generating {doe_count} placements with max_disp={suggested_disp:.1f} mm...")

    doe_result = generator.generate_placements(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        num_samples=doe_count,
        max_displacement=suggested_disp,
        enable_resampling=True
    )

    print(f"\n5. Results:")
    print(f"   Valid placements: {doe_result.num_valid}/{doe_result.num_total}")
    print(f"   Success rate: {doe_result.num_valid/doe_count*100:.1f}%")

    if doe_result.num_valid > 0:
        print(f"\n   Sample placements:")
        for i, p in enumerate(doe_result.placements[:5]):
            dist = (p.dx**2 + p.dy**2)**0.5
            print(f"   #{i+1}: dx={p.dx:+7.1f}, dy={p.dy:+7.1f}, dist={dist:6.1f} mm, score={p.score:.1f}")

        # Export to CSV
        from gui.modules.adjacent_parts_viewer.export.doe_exporter import DOEExporter
        output_path = "doe_results_real.csv"
        success = DOEExporter.export_to_csv(doe_result, output_path, include_invalid=False)
        if success:
            print(f"\n   Exported to: {output_path}")

    print("\n" + "=" * 60)
    if doe_result.num_valid >= doe_count * 0.9:
        print("✓ DOE generation SUCCESSFUL (≥90% valid)")
    elif doe_result.num_valid >= doe_count * 0.7:
        print("⚠ DOE generation PARTIAL (70-90% valid)")
    else:
        print("✗ DOE generation FAILED (<70% valid)")
    print("=" * 60)

    return 0 if doe_result.num_valid >= doe_count * 0.7 else 1


if __name__ == "__main__":
    sys.exit(main())
