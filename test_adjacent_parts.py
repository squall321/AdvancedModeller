#!/usr/bin/env python3
"""Test script for Adjacent Parts Viewer

Tests the core detection algorithm without GUI.
"""
import sys
import os

# Add core/kfile_parser to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core/kfile_parser'))

from kfile_parser.wrapper import KFileParser
from gui.app_context import ParsedModelData
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.modules.adjacent_parts_viewer.core import AdjacentPartsDetector


def test_adjacent_parts_detection():
    """Test adjacent parts detection on DropSet.k"""

    print("=" * 60)
    print("Adjacent Parts Viewer - Core Algorithm Test")
    print("=" * 60)

    # Load K-file
    kfile_path = "examples/DropSet.k"

    if not os.path.exists(kfile_path):
        print(f"ERROR: {kfile_path} not found")
        return

    print(f"\n1. Loading K-file: {kfile_path}")
    parser = KFileParser()
    reader = parser.parse(kfile_path)

    # Create ParsedModelData wrapper
    model_data = ParsedModelData(filepath=kfile_path, filename="DropSet.k")
    model_data._reader = reader

    # Convert to MeshData
    mesh_data = MeshData.from_parsed_model(model_data)

    if mesh_data is None:
        print("ERROR: Failed to create mesh data")
        return

    print(f"   ✓ Loaded: {len(mesh_data.nodes)} nodes, "
          f"{len(mesh_data.elements)} elements, "
          f"{len(mesh_data.part_ids)} parts")

    # Initialize detector
    print("\n2. Initializing detector...")
    detector = AdjacentPartsDetector(mesh_data)
    print("   ✓ Detector initialized")
    print("   ✓ Octree spatial index built")

    # Get first part as source
    if not mesh_data.part_ids:
        print("ERROR: No parts found")
        return

    source_part_id = min(mesh_data.part_ids)
    print(f"\n3. Testing with source part: {source_part_id}")

    # Auto-suggest best plane
    suggested_plane = detector.suggest_best_plane(source_part_id)
    print(f"   ✓ Suggested plane: {suggested_plane}")

    # Run detection
    plane = suggested_plane or 'XY'
    thickness_min = 0.0
    thickness_max = 100.0

    print(f"\n4. Running detection...")
    print(f"   Plane: {plane}")
    print(f"   Thickness range: [{thickness_min}, {thickness_max}]")
    print(f"   Check facing: True")
    print(f"   Ray density: 0.1")

    result = detector.find_adjacent(
        source_part_id=source_part_id,
        plane=plane,
        thickness_min=thickness_min,
        thickness_max=thickness_max,
        check_facing=True,
        ray_density=0.1,
        coverage_threshold=0.1,
        visualize=False
    )

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(f"\nAdjacent parts found: {len(result.adjacent_parts)}")
    if result.adjacent_parts:
        print(f"Part IDs: {sorted(result.adjacent_parts)}")

        print("\nCoverage:")
        for part_id in sorted(result.adjacent_parts):
            cov = result.coverage.get(part_id, 0.0)
            print(f"  Part {part_id}: {cov:.1%}")

    print(f"\nRays cast: {result.ray_count}")
    print(f"Hits: {result.hit_count}")

    print("\nPerformance:")
    for stage, time_ms in result.timing.items():
        print(f"  {stage}: {time_ms:.2f} ms")

    # Performance stats
    print("\n" + detector.get_performance_stats(result))

    # If no hits, explain why
    if not result.adjacent_parts:
        print("\nNo adjacent parts found. Possible reasons:")
        reasons = detector.explain_no_hits(result)
        for reason in reasons:
            print(f"  - {reason}")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_adjacent_parts_detection()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
