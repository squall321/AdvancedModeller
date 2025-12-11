#!/usr/bin/env python3
"""
Basic DOE feature test script.

Tests core functionality without requiring GUI.
"""

import numpy as np
from gui.modules.adjacent_parts_viewer.core.spatial_utils import BBox2D, Placement, DOEResult
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.adjacent_parts_viewer.export.doe_exporter import DOEExporter
from gui.modules.model_viewer.core.mesh_data import MeshData


def test_bbox_operations():
    """Test 2D bounding box operations"""
    print("Testing BBox2D operations...")

    # Create test bboxes
    bbox1 = BBox2D(0, 10, 0, 10)
    bbox2 = BBox2D(5, 15, 5, 15)
    bbox3 = BBox2D(20, 30, 20, 30)

    # Test overlap
    assert bbox1.overlaps(bbox2), "bbox1 should overlap bbox2"
    assert not bbox1.overlaps(bbox3), "bbox1 should not overlap bbox3"

    # Test dimensions
    assert bbox1.width() == 10
    assert bbox1.height() == 10

    # Test center
    cx, cy = bbox1.center()
    assert cx == 5.0 and cy == 5.0

    # Test translate
    translated = bbox1.translate(10, 5)
    assert translated.min_x == 10 and translated.min_y == 5

    # Test expand
    expanded = bbox1.expand(2, 3)
    assert expanded.width() == 14 and expanded.height() == 16

    # Test from_points
    points = np.array([
        [0, 0, 0],
        [10, 10, 5],
        [5, 5, 2.5]
    ])
    bbox_from_pts = BBox2D.from_points(points)
    assert bbox_from_pts.min_x == 0 and bbox_from_pts.max_x == 10
    assert bbox_from_pts.min_y == 0 and bbox_from_pts.max_y == 10

    print("✓ BBox2D operations passed")


def test_lhs_sampling():
    """Test Latin Hypercube Sampling"""
    print("Testing LHS sampling...")

    from scipy.stats import qmc

    # Create sampler
    sampler = qmc.LatinHypercube(d=2, seed=42)
    samples = sampler.random(n=20)

    # Check shape
    assert samples.shape == (20, 2), f"Expected (20, 2), got {samples.shape}"

    # Check range [0, 1]
    assert np.all(samples >= 0) and np.all(samples <= 1), "Samples out of range"

    # Scale to [-50, 50] in both dimensions
    dx_min, dx_max = -50, 50
    dy_min, dy_max = -50, 50

    scaled = samples.copy()
    scaled[:, 0] = dx_min + scaled[:, 0] * (dx_max - dx_min)
    scaled[:, 1] = dy_min + scaled[:, 1] * (dy_max - dy_min)

    assert np.all(scaled[:, 0] >= dx_min) and np.all(scaled[:, 0] <= dx_max)
    assert np.all(scaled[:, 1] >= dy_min) and np.all(scaled[:, 1] <= dy_max)

    print(f"✓ LHS sampling passed (generated {len(samples)} samples)")


def test_collision_detection():
    """Test collision detection logic"""
    print("Testing collision detection...")

    # Create mock mesh data
    mock_nodes = np.array([
        [0, 0, 0],    # 0
        [10, 0, 0],   # 1
        [10, 10, 0],  # 2
        [0, 10, 0],   # 3
        [0, 0, 10],   # 4
        [10, 0, 10],  # 5
        [10, 10, 10], # 6
        [0, 10, 10],  # 7
        # Part 2
        [20, 0, 0],   # 8
        [30, 0, 0],   # 9
        [30, 10, 0],  # 10
        [20, 10, 0],  # 11
        [20, 0, 10],  # 12
        [30, 0, 10],  # 13
        [30, 10, 10], # 14
        [20, 10, 10], # 15
    ], dtype=np.float32)

    mock_elements = np.array([
        [0, 1, 2, 3, 4, 5, 6, 7],  # Part 1
        [8, 9, 10, 11, 12, 13, 14, 15],  # Part 2
    ], dtype=np.int32)

    mock_part_elements = {
        1: [0],
        2: [1]
    }

    # Create mock MeshData
    mesh_data = MeshData(
        nodes=mock_nodes,
        elements=mock_elements,
        part_elements=mock_part_elements,
        part_names={1: "Part 1", 2: "Part 2"},
        element_type="solid",
        bounds=(mock_nodes.min(axis=0), mock_nodes.max(axis=0))
    )

    # Create generator
    generator = DOEPlacementGenerator(mesh_data)

    # Test get_2d_bbox
    bbox1 = generator.get_2d_bbox(1)
    assert bbox1.min_x == 0 and bbox1.max_x == 10
    assert bbox1.min_y == 0 and bbox1.max_y == 10

    bbox2 = generator.get_2d_bbox(2)
    assert bbox2.min_x == 20 and bbox2.max_x == 30

    # Test collision detection
    # No collision: part1 at original position
    assert not generator.check_collision(bbox1, 0, 0, [bbox2])

    # Collision: move part1 to overlap with part2
    assert generator.check_collision(bbox1, 15, 0, [bbox2])

    # No collision: move part1 far away
    assert not generator.check_collision(bbox1, 50, 50, [bbox2])

    print("✓ Collision detection passed")


def test_doe_generation():
    """Test DOE placement generation"""
    print("Testing DOE generation...")

    # Create simple test mesh
    mock_nodes = np.array([
        # Part 1 (source): centered at origin
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        # Part 2 (adjacent): offset
        [20, 0, 0], [30, 0, 0], [30, 10, 0], [20, 10, 0],
        [20, 0, 10], [30, 0, 10], [30, 10, 10], [20, 10, 10],
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

    # Generate placements
    result = generator.generate_placements(
        source_part_id=1,
        adjacent_part_ids=[2],
        num_samples=10,
        max_displacement=50.0
    )

    # Verify result
    assert result.source_part_id == 1
    assert result.num_total == 10
    assert len(result.placements) == 10
    assert result.num_valid >= 0 and result.num_valid <= 10

    print(f"✓ DOE generation passed ({result.num_valid}/{result.num_total} valid)")

    # Check placement structure
    for p in result.placements:
        assert hasattr(p, 'dx') and hasattr(p, 'dy')
        assert hasattr(p, 'is_valid')
        assert hasattr(p, 'center')
        assert len(p.center) == 3

    print("✓ Placement structure validated")

    return result


def test_csv_export(doe_result):
    """Test CSV export"""
    print("Testing CSV export...")

    import tempfile
    import os

    # Export to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name

    try:
        success = DOEExporter.export_to_csv(
            doe_result=doe_result,
            output_path=temp_path,
            include_invalid=True
        )

        assert success, "Export should succeed"

        # Verify file exists and has content
        assert os.path.exists(temp_path), "Export file should exist"
        file_size = os.path.getsize(temp_path)
        assert file_size > 0, "Export file should have content"

        # Read and verify basic structure
        with open(temp_path, 'r') as f:
            content = f.read()
            assert 'dx (mm)' in content, "CSV should have dx column"
            assert 'dy (mm)' in content, "CSV should have dy column"
            assert 'Valid' in content, "CSV should have Valid column"

        print(f"✓ CSV export passed ({file_size} bytes)")

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def main():
    """Run all tests"""
    print("=" * 60)
    print("DOE Feature Basic Tests")
    print("=" * 60)

    try:
        test_bbox_operations()
        test_lhs_sampling()
        test_collision_detection()
        doe_result = test_doe_generation()
        test_csv_export(doe_result)

        print("=" * 60)
        print("✓ All tests passed!")
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
