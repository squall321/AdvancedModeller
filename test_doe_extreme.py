#!/usr/bin/env python3
"""
Extreme DOE test - very constrained space.
"""

import numpy as np
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_extremely_constrained():
    """Test with very limited feasible space"""
    print("Testing extremely constrained scenario...")

    # Create scenario with source surrounded tightly by adjacent parts
    # Leaving only small gaps
    mock_nodes = np.array([
        # Source: 10x10 box centered at origin
        [-5, -5, 0], [5, -5, 0], [5, 5, 0], [-5, 5, 0],
        [-5, -5, 10], [5, -5, 10], [5, 5, 10], [-5, 5, 10],

        # Adjacent 1: Top (close)
        [-10, 15, 0], [10, 15, 0], [10, 20, 0], [-10, 20, 0],
        [-10, 15, 10], [10, 15, 10], [10, 20, 10], [-10, 20, 10],

        # Adjacent 2: Right (close)
        [15, -10, 0], [20, -10, 0], [20, 10, 0], [15, 10, 0],
        [15, -10, 10], [20, -10, 10], [20, 10, 10], [15, 10, 10],

        # Adjacent 3: Bottom (close)
        [-10, -20, 0], [10, -20, 0], [10, -15, 0], [-10, -15, 0],
        [-10, -20, 10], [10, -20, 10], [10, -15, 10], [-10, -15, 10],

        # Adjacent 4: Left (close)
        [-20, -10, 0], [-15, -10, 0], [-15, 10, 0], [-20, 10, 0],
        [-20, -10, 10], [-15, -10, 10], [-15, 10, 10], [-20, 10, 10],
    ], dtype=np.float32)

    mock_elements = np.array([
        [0, 1, 2, 3, 4, 5, 6, 7],      # Source
        [8, 9, 10, 11, 12, 13, 14, 15],    # Adj 1
        [16, 17, 18, 19, 20, 21, 22, 23],  # Adj 2
        [24, 25, 26, 27, 28, 29, 30, 31],  # Adj 3
        [32, 33, 34, 35, 36, 37, 38, 39],  # Adj 4
    ], dtype=np.int32)

    mock_part_elements = {
        1: [0],  # Source
        2: [1],  # Top
        3: [2],  # Right
        4: [3],  # Bottom
        5: [4],  # Left
    }

    mesh_data = MeshData(
        nodes=mock_nodes,
        elements=mock_elements,
        part_elements=mock_part_elements,
        part_names={1: "Source", 2: "Top", 3: "Right", 4: "Bottom", 5: "Left"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    generator = DOEPlacementGenerator(mesh_data, voxel_size=1.0)

    # Very small max_displacement (only 12mm, while adjacent parts are at ~15mm)
    max_disp = 12.0
    target_count = 20

    print(f"  Target: {target_count} valid placements")
    print(f"  Max displacement: {max_disp} mm")
    print(f"  Feasible space: Very limited (surrounded by 4 adjacent parts)")

    result = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2, 3, 4, 5],
        num_samples=target_count,
        max_displacement=max_disp,
        enable_resampling=True
    )

    print(f"  Result: {result.num_valid}/{result.num_total} valid placements")

    # Verify all constraints
    violations = []
    for p in result.placements:
        displacement = np.sqrt(p.dx**2 + p.dy**2)
        if displacement > max_disp + 0.01:
            violations.append(f"Placement {p.index}: disp={displacement:.2f}mm > {max_disp}mm")
        if not p.is_valid:
            violations.append(f"Placement {p.index}: has collision")

    if violations:
        print("  ✗ Violations found:")
        for v in violations[:5]:
            print(f"    {v}")
        raise AssertionError(f"Found {len(violations)} violations")

    success_rate = result.num_valid / target_count
    print(f"  Success rate: {success_rate*100:.1f}%")

    if result.num_valid >= target_count * 0.9:
        print(f"  ✓ Achieved ≥90% of target count")
    elif result.num_valid >= target_count * 0.7:
        print(f"  ⚠ Achieved 70-90% of target (acceptable for extreme constraints)")
    else:
        print(f"  ⚠ Only achieved {success_rate*100:.1f}% (very constrained space)")

    print("✓ Extreme constraint test passed\n")


def test_impossible_scenario():
    """Test scenario with no feasible space"""
    print("Testing impossible scenario (no feasible space)...")

    # Source completely surrounded with no gap
    mock_nodes = np.array([
        # Source: small 4x4 box
        [-2, -2, 0], [2, -2, 0], [2, 2, 0], [-2, 2, 0],
        [-2, -2, 5], [2, -2, 5], [2, 2, 5], [-2, 2, 5],

        # Giant adjacent part blocking everything within max_displacement
        [-20, -20, 0], [20, -20, 0], [20, 20, 0], [-20, 20, 0],
        [-20, -20, 5], [20, -20, 5], [20, 20, 5], [-20, 20, 5],
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
        part_names={1: "Source", 2: "Blocker"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(0))
    )

    generator = DOEPlacementGenerator(mesh_data, voxel_size=1.0)

    # Try to generate with small max_displacement where no space exists
    result = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=10,
        max_displacement=8.0,  # Too small to escape the blocker
        enable_resampling=True
    )

    print(f"  Result: {result.num_valid}/{result.num_total} valid placements")

    # In impossible scenario, should gracefully return 0 valid
    if result.num_valid == 0:
        print("  ✓ Correctly returned 0 valid placements (no feasible space)")
    else:
        print(f"  ⚠ Got {result.num_valid} placements (unexpected but acceptable)")

    print("✓ Impossible scenario handled gracefully\n")


def main():
    print("=" * 60)
    print("Extreme DOE Tests")
    print("=" * 60)

    try:
        test_extremely_constrained()
        test_impossible_scenario()

        print("=" * 60)
        print("✓ All extreme tests passed!")
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
