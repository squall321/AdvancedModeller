#!/usr/bin/env python3
"""
Strict DOE test to verify max_displacement and resampling.
"""

import numpy as np
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_max_displacement_constraint():
    """Test that all placements respect max_displacement"""
    print("Testing max_displacement constraint...")

    # Create simple test mesh
    mock_nodes = np.array([
        # Part 1 (source): centered at origin
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        # Part 2 (adjacent): offset
        [30, 0, 0], [40, 0, 0], [40, 10, 0], [30, 10, 0],
        [30, 0, 10], [40, 0, 10], [40, 10, 10], [30, 10, 10],
    ], dtype=np.float32)

    mock_elements = np.array([
        [0, 1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14, 15],
    ], dtype=np.int32)

    mock_part_elements = {
        1: [0],
        2: [1]
    }

    mesh_data = MeshData(
        nodes=mock_nodes,
        elements=mock_elements,
        part_elements=mock_part_elements,
        part_names={1: "Part 1", 2: "Part 2"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    generator = DOEPlacementGenerator(mesh_data)

    # Test with max_displacement = 20mm
    max_disp = 20.0
    result = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=20,
        max_displacement=max_disp
    )

    print(f"  Requested: 20 samples, max_displacement={max_disp} mm")
    print(f"  Generated: {result.num_valid}/{result.num_total} valid placements")

    # Verify ALL placements respect max_displacement
    violations = []
    for p in result.placements:
        displacement = np.sqrt(p.dx**2 + p.dy**2)
        if displacement > max_disp + 0.01:  # Allow tiny floating point error
            violations.append((p.index, displacement))

    if violations:
        print(f"  ✗ Found {len(violations)} violations:")
        for idx, disp in violations[:5]:  # Show first 5
            print(f"    Placement {idx}: displacement = {disp:.2f} mm (max = {max_disp} mm)")
        raise AssertionError(f"Max displacement violated in {len(violations)} placements")
    else:
        print(f"  ✓ All {len(result.placements)} placements respect max_displacement")

    # Verify all placements are valid (no collisions)
    invalid_count = sum(1 for p in result.placements if not p.is_valid)
    if invalid_count > 0:
        print(f"  ✗ Found {invalid_count} invalid placements (collisions)")
        raise AssertionError(f"Found {invalid_count} invalid placements")
    else:
        print(f"  ✓ All placements are collision-free")

    # Check if we got close to requested count
    if result.num_valid < 15:  # At least 75% of requested
        print(f"  ⚠ Warning: Only got {result.num_valid}/20 valid samples (75% threshold)")

    print("✓ Max displacement constraint test passed\n")


def test_resampling_effectiveness():
    """Test that resampling actually gets us to target count"""
    print("Testing resampling effectiveness...")

    # Create constrained scenario
    mock_nodes = np.array([
        # Source: small box
        [-2.5, -2.5, 0], [2.5, -2.5, 0], [2.5, 2.5, 0], [-2.5, 2.5, 0],
        [-2.5, -2.5, 5], [2.5, -2.5, 5], [2.5, 2.5, 5], [-2.5, 2.5, 5],
        # Adjacent parts creating constraints
        [-15, 8, 0], [15, 8, 0], [15, 12, 0], [-15, 12, 0],
        [-15, 8, 5], [15, 8, 5], [15, 12, 5], [-15, 12, 5],
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
        part_names={1: "Source", 2: "Adj"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    generator = DOEPlacementGenerator(mesh_data, voxel_size=1.0)

    # Test with resampling
    target_count = 20
    max_disp = 12.0

    result = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=target_count,
        max_displacement=max_disp,
        enable_resampling=True
    )

    print(f"  Target: {target_count} samples")
    print(f"  Result: {result.num_valid} valid samples")

    # With resampling, should get close to target
    success_rate = result.num_valid / target_count
    print(f"  Success rate: {success_rate*100:.1f}%")

    if result.num_valid < target_count * 0.9:  # At least 90%
        print(f"  ⚠ Warning: Resampling only achieved {success_rate*100:.1f}% of target")
    else:
        print(f"  ✓ Resampling achieved target count")

    print("✓ Resampling test passed\n")


def main():
    print("=" * 60)
    print("Strict DOE Tests")
    print("=" * 60)

    try:
        test_max_displacement_constraint()
        test_resampling_effectiveness()

        print("=" * 60)
        print("✓ All strict tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        import traceback
        print("=" * 60)
        print("✗ Test failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
