#!/usr/bin/env python3
"""
Test manual max_displacement input and continuous sampling.
"""

import numpy as np
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_manual_max_displacement():
    """Test that manual max_displacement input is respected"""
    print("=" * 60)
    print("Testing Manual Max Displacement Input")
    print("=" * 60)

    # Create simple test mesh
    mock_nodes = np.array([
        # Source: 10x10 box at origin
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        # Adjacent: 10x10 box at 50mm distance
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
        part_names={1: "Source", 2: "Adjacent"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    # Test 1: Auto-suggested value
    print("\n1. Testing auto-suggested max_displacement:")
    suggested = generator.suggest_max_displacement(1, [2])
    print(f"   Auto-suggested: {suggested:.1f} mm")

    result_auto = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=20,
        max_displacement=suggested,
        enable_resampling=True
    )
    print(f"   Result: {result_auto.num_valid}/20 valid placements")

    # Verify all within suggested max
    max_dist = 0.0
    for p in result_auto.placements:
        dist = np.sqrt(p.dx**2 + p.dy**2)
        max_dist = max(max_dist, dist)
        if dist > suggested + 0.1:
            print(f"   ✗ VIOLATION: Placement {p.index} has dist={dist:.2f} > {suggested:.1f}")
            return False

    print(f"   ✓ All placements within {suggested:.1f}mm (max observed: {max_dist:.1f}mm)")

    # Test 2: Manual override to smaller value
    print("\n2. Testing manual max_displacement override (30mm):")
    manual_max = 30.0
    print(f"   Manual input: {manual_max:.1f} mm (smaller than auto {suggested:.1f} mm)")

    result_manual = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=20,
        max_displacement=manual_max,  # USER INPUT
        enable_resampling=True
    )
    print(f"   Result: {result_manual.num_valid}/20 valid placements")

    # Verify all within manual max
    max_dist = 0.0
    violations = []
    for p in result_manual.placements:
        dist = np.sqrt(p.dx**2 + p.dy**2)
        max_dist = max(max_dist, dist)
        if dist > manual_max + 0.1:
            violations.append((p.index, dist))

    if violations:
        print(f"   ✗ VIOLATIONS FOUND: {len(violations)} placements exceed {manual_max:.1f}mm")
        for idx, dist in violations[:5]:
            print(f"      Placement {idx}: {dist:.2f}mm")
        return False

    print(f"   ✓ All placements within {manual_max:.1f}mm (max observed: {max_dist:.1f}mm)")

    # Test 3: Manual override to larger value
    print("\n3. Testing manual max_displacement override (100mm):")
    manual_max_large = 100.0
    print(f"   Manual input: {manual_max_large:.1f} mm (larger than auto {suggested:.1f} mm)")

    result_large = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=20,
        max_displacement=manual_max_large,  # USER INPUT
        enable_resampling=True
    )
    print(f"   Result: {result_large.num_valid}/20 valid placements")

    # Verify all within manual max
    max_dist = 0.0
    violations = []
    for p in result_large.placements:
        dist = np.sqrt(p.dx**2 + p.dy**2)
        max_dist = max(max_dist, dist)
        if dist > manual_max_large + 0.1:
            violations.append((p.index, dist))

    if violations:
        print(f"   ✗ VIOLATIONS FOUND: {len(violations)} placements exceed {manual_max_large:.1f}mm")
        for idx, dist in violations[:5]:
            print(f"      Placement {idx}: {dist:.2f}mm")
        return False

    print(f"   ✓ All placements within {manual_max_large:.1f}mm (max observed: {max_dist:.1f}mm)")

    # Test 4: Continuous sampling until target achieved
    print("\n4. Testing continuous sampling to achieve exactly 20 valid:")
    result_exact = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=20,
        max_displacement=30.0,
        enable_resampling=True
    )

    if result_exact.num_valid != 20:
        print(f"   ✗ FAILED: Got {result_exact.num_valid}/20 valid (expected exactly 20)")
        return False

    print(f"   ✓ Achieved exactly 20/20 valid placements")

    print("\n" + "=" * 60)
    print("✓ All tests PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    import sys
    success = test_manual_max_displacement()
    sys.exit(0 if success else 1)
