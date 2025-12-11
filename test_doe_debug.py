#!/usr/bin/env python3
"""
Debug DOE generation to see what's happening.
"""

import numpy as np
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_debug():
    """Debug test with verbose output"""
    print("Debug DOE generation...")

    # Simple scenario
    mock_nodes = np.array([
        # Part 1 (source): 10x10 box at origin
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        # Part 2 (adjacent): 10x10 box offset by 50mm
        [50, 0, 0], [60, 0, 0], [60, 10, 0], [50, 10, 0],
        [50, 0, 10], [60, 0, 10], [60, 10, 10], [50, 10, 10],
    ], dtype=np.float32)

    mock_elements = np.array([
        [0, 1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14, 15],
    ], dtype=np.int32)

    mock_part_elements = {1: [0], 2: [1]}

    mesh_data = MeshData(
        nodes=mock_nodes,
        elements=mock_elements,
        part_elements=mock_part_elements,
        part_names={1: "Part 1", 2: "Part 2"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    # Get bboxes
    source_bbox = generator.get_2d_bbox(1)
    adj_bbox = generator.get_2d_bbox(2)

    print(f"Source bbox: ({source_bbox.min_x}, {source_bbox.max_x}), ({source_bbox.min_y}, {source_bbox.max_y})")
    print(f"Adjacent bbox: ({adj_bbox.min_x}, {adj_bbox.max_x}), ({adj_bbox.min_y}, {adj_bbox.max_y})")

    source_center = source_bbox.center()
    adj_center = adj_bbox.center()
    distance = np.sqrt((source_center[0] - adj_center[0])**2 + (source_center[1] - adj_center[1])**2)
    print(f"Distance between centers: {distance:.1f} mm")

    # Test with reasonable max_displacement
    max_disp = 30.0
    print(f"\nGenerating with max_displacement={max_disp} mm")

    result = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=10,
        max_displacement=max_disp,
        enable_resampling=True
    )

    print(f"\nResult: {result.num_valid}/{result.num_total} valid placements")
    print(f"Feasible bounds: {result.feasible_bounds}")

    if result.num_valid == 0:
        print("\n⚠ WARNING: 0 valid placements generated!")
        print("Checking feasible space analyzer...")

        # Check feasible regions
        from gui.modules.adjacent_parts_viewer.core.feasible_space import FeasibleSpaceAnalyzer
        analyzer = FeasibleSpaceAnalyzer(voxel_size=2.0)

        feasible_regions = analyzer.find_feasible_regions(
            source_bbox=source_bbox,
            adjacent_bboxes=[adj_bbox],
            max_displacement=max_disp,
            margin=2.0
        )

        print(f"Feasible regions found: {len(feasible_regions)}")
        for i, region in enumerate(feasible_regions):
            x_min, x_max, y_min, y_max = region
            area = (x_max - x_min) * (y_max - y_min)
            print(f"  Region {i}: x=[{x_min:.1f}, {x_max:.1f}], y=[{y_min:.1f}, {y_max:.1f}], area={area:.1f}")

        # Try sampling
        if feasible_regions:
            samples = analyzer.sample_from_regions(
                regions=feasible_regions,
                num_samples=10,
                strategy='weighted'
            )
            print(f"\nSamples generated: {len(samples)}")
            if len(samples) > 0:
                print(f"First 3 samples (world coords): {samples[:3]}")

                # Convert to displacements
                source_cx, source_cy = source_bbox.center()
                displacements = samples.copy()
                displacements[:, 0] -= source_cx
                displacements[:, 1] -= source_cy
                print(f"First 3 displacements: {displacements[:3]}")

                # Check distances
                for i, (dx, dy) in enumerate(displacements[:3]):
                    dist = np.sqrt(dx**2 + dy**2)
                    print(f"  Sample {i}: dx={dx:.1f}, dy={dy:.1f}, distance={dist:.1f} mm")

    else:
        print("✓ Valid placements generated successfully")
        for i, p in enumerate(result.placements[:3]):
            dist = np.sqrt(p.dx**2 + p.dy**2)
            print(f"  Placement {i}: dx={p.dx:.1f}, dy={p.dy:.1f}, distance={dist:.1f} mm")


if __name__ == "__main__":
    test_debug()
