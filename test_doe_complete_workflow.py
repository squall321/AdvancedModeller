#!/usr/bin/env python3
"""
Complete DOE workflow demonstration with all features integrated.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from core.KooDynaKeyword import KFileReader
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def print_section(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def main():
    print_section("DOE Complete Workflow Demonstration")

    # =========================================================================
    # Step 1: Load Model
    # =========================================================================
    print_section("Step 1: Loading DropSet.k Model")

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

    print(f"✓ Loaded: {len(nodes):,} nodes, {len(elements):,} elements")
    print(f"✓ Parts: {len(part_names)}")

    # =========================================================================
    # Step 2: Select Source Part
    # =========================================================================
    print_section("Step 2: Selecting Source Part")

    pkg_parts = [pid for pid, name in part_names.items() if 'PKG' in name.upper()]
    source_part = pkg_parts[0]

    print(f"Source Part ID: {source_part}")
    print(f"Source Part Name: {part_names[source_part]}")

    source_nodes = mesh_data.nodes[mesh_data.elements[mesh_data.part_elements[source_part]].flatten()]
    source_bbox = (source_nodes.min(axis=0), source_nodes.max(axis=0))
    source_size = source_bbox[1] - source_bbox[0]

    print(f"Source Size: {source_size[0]:.1f} × {source_size[1]:.1f} × {source_size[2]:.1f} mm")
    print(f"Source Center: ({(source_bbox[0][0]+source_bbox[1][0])/2:.1f}, "
          f"{(source_bbox[0][1]+source_bbox[1][1])/2:.1f}, "
          f"{(source_bbox[0][2]+source_bbox[1][2])/2:.1f}) mm")

    # =========================================================================
    # Step 3: Detect Adjacent Parts
    # =========================================================================
    print_section("Step 3: Detecting Adjacent Parts")

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
    print(f"✓ Found {len(adjacent_ids)} adjacent parts")

    # =========================================================================
    # Step 4: Filter Co-Planar Parts
    # =========================================================================
    print_section("Step 4: Filtering Co-Planar Parts (PCB, etc.)")

    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    collision_parts, coplanar_parts = generator.filter_coplanar_parts(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        z_tolerance=1.0
    )

    print(f"Adjacent Parts: {len(adjacent_ids)}")
    print(f"  ├─ Collision Check: {len(collision_parts)} parts")
    print(f"  └─ Co-Planar (excluded): {len(coplanar_parts)} parts")

    if coplanar_parts:
        print(f"\nCo-planar parts (face-to-face contact in Z):")
        for pid in coplanar_parts[:8]:
            name = part_names.get(pid, f'Part {pid}')
            print(f"  • Part {pid}: {name}")
        if len(coplanar_parts) > 8:
            print(f"  ... and {len(coplanar_parts)-8} more")

    # =========================================================================
    # Step 5: Auto-Suggest Max Displacement
    # =========================================================================
    print_section("Step 5: Auto-Suggesting Max Displacement")

    suggested_displacement = generator.suggest_max_displacement(
        source_part_id=source_part,
        adjacent_part_ids=collision_parts,
        grid_step=0.1
    )

    print(f"\n✓ Suggested max_displacement: {suggested_displacement:.1f} mm")
    print(f"  (Based on grid-based feasible space analysis)")

    # =========================================================================
    # Step 6: Generate DOE Placements
    # =========================================================================
    print_section("Step 6: Generating DOE Placements")

    num_samples = 20
    print(f"Target: {num_samples} valid placements")
    print(f"Max Displacement: {suggested_displacement:.1f} mm")
    print(f"Resampling: Enabled (adaptive)")

    doe_result = generator.generate_placements(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,  # Original list (filtering done internally)
        num_samples=num_samples,
        max_displacement=suggested_displacement,
        enable_resampling=True
    )

    # =========================================================================
    # Step 7: Analyze Results
    # =========================================================================
    print_section("Step 7: Results Analysis")

    success_rate = doe_result.num_valid / num_samples * 100

    print(f"Valid Placements: {doe_result.num_valid}/{doe_result.num_total}")
    print(f"Success Rate: {success_rate:.1f}%")

    if doe_result.num_valid > 0:
        displacements = [np.sqrt(p.dx**2 + p.dy**2) for p in doe_result.placements]
        avg_disp = np.mean(displacements)
        max_disp = max(displacements)
        min_disp = min(displacements)

        print(f"\nDisplacement Statistics:")
        print(f"  Average: {avg_disp:.1f} mm")
        print(f"  Min: {min_disp:.1f} mm")
        print(f"  Max: {max_disp:.1f} mm")
        print(f"  Limit: {suggested_displacement:.1f} mm")

        # Directional analysis
        dx_values = [p.dx for p in doe_result.placements]
        dy_values = [p.dy for p in doe_result.placements]

        print(f"\nDirectional Distribution:")
        print(f"  X: {np.mean(dx_values):+.1f} mm (avg), "
              f"range [{min(dx_values):+.1f}, {max(dx_values):+.1f}]")
        print(f"  Y: {np.mean(dy_values):+.1f} mm (avg), "
              f"range [{min(dy_values):+.1f}, {max(dy_values):+.1f}]")

        print(f"\nSample Placements (first 10):")
        print(f"{'#':<4} {'dx (mm)':<10} {'dy (mm)':<10} {'dist (mm)':<12} {'valid'}")
        print("-" * 50)
        for i, p in enumerate(doe_result.placements[:10]):
            dist = np.sqrt(p.dx**2 + p.dy**2)
            status = "✓" if p.index < doe_result.num_valid else "✗"
            print(f"{i+1:<4} {p.dx:+9.2f} {p.dy:+9.2f} {dist:11.2f}  {status}")

    # =========================================================================
    # Summary
    # =========================================================================
    print_section("Summary")

    print("Workflow Steps:")
    print("  1. ✓ Loaded model (DropSet.k)")
    print(f"  2. ✓ Selected source part ({source_part})")
    print(f"  3. ✓ Detected {len(adjacent_ids)} adjacent parts")
    print(f"  4. ✓ Filtered out {len(coplanar_parts)} co-planar parts (PCB, etc.)")
    print(f"  5. ✓ Auto-suggested {suggested_displacement:.1f} mm max displacement")
    print(f"  6. ✓ Generated {doe_result.num_valid}/{num_samples} valid placements")

    print(f"\nKey Features Demonstrated:")
    print("  • Co-planar part filtering (PCB exclusion)")
    print("  • Grid-based auto max_displacement calculation")
    print("  • Latin Hypercube Sampling (LHS)")
    print("  • Adaptive resampling for target count")
    print("  • Feasible space analysis")

    if success_rate >= 90:
        print(f"\n{'='*70}")
        print(f"  ✓ SUCCESS: {success_rate:.1f}% success rate achieved!")
        print(f"{'='*70}")
        return 0
    else:
        print(f"\n{'='*70}")
        print(f"  ⚠ Partial success: {success_rate:.1f}%")
        print(f"{'='*70}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
