#!/usr/bin/env python3
"""
Test co-planar part filtering (PCB case).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_coplanar_filtering():
    """Test that co-planar parts (PCB) are excluded from collision check"""
    print("=" * 60)
    print("Test Co-planar Part Filtering")
    print("=" * 60)

    # Create test scenario:
    # - Package (10x10x5) at z=5~10
    # - PCB (30x30x1) at z=4~5 (touching package bottom)
    # - Side wall (5x30x10) at x=15~20 (actual collision risk)

    mock_nodes = np.array([
        # Package (Part 1): 10x10x5 box at z=5~10
        [0, 0, 5], [10, 0, 5], [10, 10, 5], [0, 10, 5],  # Bottom face
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],  # Top face

        # PCB (Part 2): 30x30x1 at z=4~5 (face-to-face with package)
        [-10, -10, 4], [20, -10, 4], [20, 20, 4], [-10, 20, 4],  # Bottom
        [-10, -10, 5], [20, -10, 5], [20, 20, 5], [-10, 20, 5],  # Top (touches package)

        # Side Wall (Part 3): 5x30x10 at x=15~20
        [15, -10, 0], [20, -10, 0], [20, 20, 0], [15, 20, 0],  # Bottom
        [15, -10, 10], [20, -10, 10], [20, 20, 10], [15, 20, 10],  # Top
    ], dtype=np.float32)

    mock_elements = np.array([
        [0, 1, 2, 3, 4, 5, 6, 7],      # Package
        [8, 9, 10, 11, 12, 13, 14, 15],    # PCB
        [16, 17, 18, 19, 20, 21, 22, 23],  # Side wall
    ], dtype=np.int32)

    mock_part_elements = {
        1: [0],  # Package
        2: [1],  # PCB
        3: [2],  # Side wall
    }

    mesh_data = MeshData(
        nodes=mock_nodes,
        elements=mock_elements,
        part_elements=mock_part_elements,
        part_names={1: "Package", 2: "PCB", 3: "Side Wall"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    # Test 1: Filter co-planar parts
    print("\n1. Testing co-planar part filtering:")
    adjacent_part_ids = [2, 3]  # PCB and Side Wall

    collision_parts, coplanar_parts = generator.filter_coplanar_parts(
        source_part_id=1,
        adjacent_part_ids=adjacent_part_ids,
        z_tolerance=1.0
    )

    print(f"   Adjacent parts: {adjacent_part_ids}")
    print(f"   Collision parts (should exclude PCB): {collision_parts}")
    print(f"   Co-planar parts (should be [2=PCB]): {coplanar_parts}")

    assert 2 in coplanar_parts, "PCB should be detected as co-planar!"
    assert 3 in collision_parts, "Side wall should be in collision check!"
    print("   ✓ Co-planar filtering works correctly")

    # Test 2: Generate DOE with and without filtering
    print("\n2. Testing DOE generation:")

    print("\n   Case A: WITHOUT filtering (old behavior)")
    print("   - Would check collision with both PCB and Side Wall")
    print("   - XY movement blocked by PCB (false positive)")

    # Manually test without filtering (simulate old behavior)
    all_bboxes = [generator.get_2d_bbox(pid) for pid in adjacent_part_ids]
    source_bbox = generator.get_2d_bbox(1)

    # Try to move 5mm in +X direction
    test_dx, test_dy = 5.0, 0.0
    collisions_old = generator.find_collisions(
        source_bbox, test_dx, test_dy, adjacent_part_ids, all_bboxes
    )
    print(f"   - Moving dx=+5mm, dy=0mm")
    print(f"   - Collisions detected: {collisions_old}")

    print("\n   Case B: WITH filtering (new behavior)")
    print("   - Only checks collision with Side Wall")
    print("   - PCB excluded (co-planar in Z)")

    # Generate DOE with filtering (automatic now)
    result = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=adjacent_part_ids,
        num_samples=10,
        max_displacement=12.0,
        enable_resampling=True
    )

    print(f"\n   Result: {result.num_valid}/10 valid placements")

    if result.num_valid > 0:
        print(f"   ✓ Can move in XY plane (PCB doesn't block)")
        print(f"\n   Sample placements:")
        for i, p in enumerate(result.placements[:3]):
            dist = np.sqrt(p.dx**2 + p.dy**2)
            print(f"     #{i+1}: dx={p.dx:+6.1f}, dy={p.dy:+6.1f}, dist={dist:5.1f} mm")
    else:
        print(f"   ✗ FAILED: Still blocked despite filtering!")
        return False

    # Test 3: Verify placements don't collide with side wall
    print("\n3. Verifying collision avoidance with side wall:")
    source_cx = source_bbox.center()[0]  # X center ~5
    side_wall_x_min = 15.0

    violations = []
    for p in result.placements:
        new_x_max = source_cx + 5 + p.dx  # source extends to x+5 from center
        if new_x_max > side_wall_x_min - 1:  # Should stay 1mm away
            violations.append((p.index, new_x_max))

    if violations:
        print(f"   ✗ Found {len(violations)} placements too close to side wall:")
        for idx, x in violations[:3]:
            print(f"     Placement {idx}: x_max={x:.1f} (wall at {side_wall_x_min})")
        return False
    else:
        print(f"   ✓ All {result.num_valid} placements avoid side wall")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nSummary:")
    print("  - Co-planar parts (PCB) correctly identified")
    print("  - DOE generation excludes PCB from collision check")
    print("  - XY movement now possible above/below co-planar parts")
    print("  - Side collision (non-coplanar) still detected correctly")

    return True


if __name__ == "__main__":
    success = test_coplanar_filtering()
    sys.exit(0 if success else 1)
