#!/usr/bin/env python3
"""
Advanced DOE feature tests.

Tests auto max displacement and resampling functionality.
"""

import numpy as np
from gui.modules.adjacent_parts_viewer.core.spatial_utils import BBox2D
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_auto_max_displacement():
    """Test automatic max displacement suggestion"""
    print("Testing auto max displacement...")

    # Create test mesh with parts at different distances
    # Part 1 (source) at origin
    # Part 2 at distance 50mm
    # Part 3 at distance 100mm
    mock_nodes = np.array([
        # Part 1 (source): 10x10x10 box at origin
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        # Part 2 (near): 10x10x10 box at distance ~50mm
        [50, 0, 0], [60, 0, 0], [60, 10, 0], [50, 10, 0],
        [50, 0, 10], [60, 0, 10], [60, 10, 10], [50, 10, 10],
        # Part 3 (far): 10x10x10 box at distance ~100mm
        [100, 0, 0], [110, 0, 0], [110, 10, 0], [100, 10, 0],
        [100, 0, 10], [110, 0, 10], [110, 10, 10], [100, 10, 10],
    ], dtype=np.float32)

    mock_elements = np.array([
        [0, 1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14, 15],
        [16, 17, 18, 19, 20, 21, 22, 23],
    ], dtype=np.int32)

    mock_part_elements = {
        1: [0],
        2: [1],
        3: [2]
    }

    mesh_data = MeshData(
        nodes=mock_nodes,
        elements=mock_elements,
        part_elements=mock_part_elements,
        part_names={1: "Part 1", 2: "Part 2", 3: "Part 3"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    generator = DOEPlacementGenerator(mesh_data)

    # Test 1: Adjacent to Part 2 (near) only
    suggested = generator.suggest_max_displacement(
        source_part_id=1,
        adjacent_part_ids=[2]
    )
    print(f"  Near adjacent (50mm): suggested max_displacement = {suggested:.1f} mm")
    assert 20 <= suggested <= 100, f"Expected 20-100mm, got {suggested:.1f}mm"

    # Test 2: Adjacent to Part 3 (far) only
    suggested = generator.suggest_max_displacement(
        source_part_id=1,
        adjacent_part_ids=[3]
    )
    print(f"  Far adjacent (100mm): suggested max_displacement = {suggested:.1f} mm")
    assert 50 <= suggested <= 200, f"Expected 50-200mm, got {suggested:.1f}mm"

    # Test 3: Adjacent to both (should use nearest)
    suggested = generator.suggest_max_displacement(
        source_part_id=1,
        adjacent_part_ids=[2, 3]
    )
    print(f"  Both adjacent: suggested max_displacement = {suggested:.1f} mm")
    assert 20 <= suggested <= 100, f"Expected to use nearest (20-100mm), got {suggested:.1f}mm"

    # Test 4: No adjacent parts (should use default)
    suggested = generator.suggest_max_displacement(
        source_part_id=1,
        adjacent_part_ids=[]
    )
    print(f"  No adjacent: suggested max_displacement = {suggested:.1f} mm")
    assert suggested == 100.0, f"Expected default 100mm, got {suggested:.1f}mm"

    print("✓ Auto max displacement tests passed")


def test_resampling():
    """Test resampling to guarantee DOE count"""
    print("\nTesting resampling...")

    # Create constrained scenario with limited feasible space
    # Source part in center, surrounded by adjacent parts
    # This will force low success rate initially
    mock_nodes = np.array([
        # Source part: small 5x5x5 box at origin
        [-2.5, -2.5, 0], [2.5, -2.5, 0], [2.5, 2.5, 0], [-2.5, 2.5, 0],
        [-2.5, -2.5, 5], [2.5, -2.5, 5], [2.5, 2.5, 5], [-2.5, 2.5, 5],
        # Adjacent 1: blocking top
        [-10, 10, 0], [10, 10, 0], [10, 15, 0], [-10, 15, 0],
        [-10, 10, 5], [10, 10, 5], [10, 15, 5], [-10, 15, 5],
        # Adjacent 2: blocking right
        [10, -10, 0], [15, -10, 0], [15, 10, 0], [10, 10, 0],
        [10, -10, 5], [15, -10, 5], [15, 10, 5], [10, 10, 5],
        # Adjacent 3: blocking bottom
        [-10, -15, 0], [10, -15, 0], [10, -10, 0], [-10, -10, 0],
        [-10, -15, 5], [10, -15, 5], [10, -10, 5], [-10, -10, 5],
        # Adjacent 4: blocking left
        [-15, -10, 0], [-10, -10, 0], [-10, 10, 0], [-15, 10, 0],
        [-15, -10, 5], [-10, -10, 5], [-10, 10, 5], [-15, 10, 5],
    ], dtype=np.float32)

    mock_elements = np.array([
        [0, 1, 2, 3, 4, 5, 6, 7],     # Source
        [8, 9, 10, 11, 12, 13, 14, 15],    # Adj 1
        [16, 17, 18, 19, 20, 21, 22, 23],  # Adj 2
        [24, 25, 26, 27, 28, 29, 30, 31],  # Adj 3
        [32, 33, 34, 35, 36, 37, 38, 39],  # Adj 4
    ], dtype=np.int32)

    mock_part_elements = {
        1: [0],
        2: [1],
        3: [2],
        4: [3],
        5: [4]
    }

    mesh_data = MeshData(
        nodes=mock_nodes,
        elements=mock_elements,
        part_elements=mock_part_elements,
        part_names={1: "Source", 2: "Adj1", 3: "Adj2", 4: "Adj3", 5: "Adj4"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    generator = DOEPlacementGenerator(mesh_data, voxel_size=1.0)

    # Test with resampling enabled (should achieve target count)
    desired_count = 20
    result_with_resampling = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2, 3, 4, 5],
        num_samples=desired_count,
        max_displacement=15.0,
        enable_resampling=True
    )

    print(f"  With resampling: {result_with_resampling.num_valid}/{result_with_resampling.num_total} valid")

    # With smart voxel-based sampling + resampling, we should get close to target
    success_rate = result_with_resampling.num_valid / desired_count
    print(f"  Success rate: {success_rate*100:.1f}%")

    # Should achieve at least 80% of desired count (likely 100%)
    assert result_with_resampling.num_valid >= desired_count * 0.8, \
        f"Expected at least {desired_count*0.8:.0f} valid, got {result_with_resampling.num_valid}"

    # Test without resampling (for comparison)
    result_without_resampling = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2, 3, 4, 5],
        num_samples=desired_count,
        max_displacement=15.0,
        enable_resampling=False
    )

    print(f"  Without resampling: {result_without_resampling.num_valid}/{result_without_resampling.num_total} valid")

    # With voxel-based sampling, even without resampling should be good
    # But resampling should be equal or better
    assert result_with_resampling.num_valid >= result_without_resampling.num_valid, \
        "Resampling should provide equal or better results"

    print("✓ Resampling tests passed")


def main():
    """Run all advanced tests"""
    print("=" * 60)
    print("DOE Advanced Feature Tests")
    print("=" * 60)

    try:
        test_auto_max_displacement()
        test_resampling()

        print("=" * 60)
        print("✓ All advanced tests passed!")
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
