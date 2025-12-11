#!/usr/bin/env python3
"""Simplified test for Adjacent Parts Viewer - Direct API test

Tests the core detection algorithm without full GUI integration.
"""
import sys
import os
import numpy as np

# Add core/kfile_parser to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core/kfile_parser'))

from kfile_parser.wrapper import KFileParser
from gui.modules.adjacent_parts_viewer.core import AdjacentPartsDetector


# Simple MeshData class compatible with detector
class SimpleMeshData:
    """Simple mesh data structure for testing"""

    def __init__(self, parsed_kfile):
        self.nodes = {}  # node_id -> [x, y, z]
        self.elements = {}  # element_id -> {'node_ids': [...], 'part_id': ...}
        self.part_ids = set()
        self.element_type = 'shell'  # Assume shell elements

        # Extract nodes
        for node in parsed_kfile.nodes:
            self.nodes[node.nid] = np.array([node.x, node.y, node.z])

        # Extract elements
        for elem in parsed_kfile.elements:
            # Use nodes list from element
            node_ids = [n for n in elem.nodes if n != 0]  # Filter out zero nodes (for hex elements)

            part_id = elem.pid if hasattr(elem, 'pid') else 1

            self.elements[elem.eid] = {
                'node_ids': node_ids,
                'part_id': part_id
            }

            self.part_ids.add(part_id)

            # Set element type from first element
            if self.element_type == 'shell' and elem.element_type == 'solid':
                self.element_type = 'solid'


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
    parsed_kfile = parser.parse(kfile_path)

    # Create simple mesh data
    mesh_data = SimpleMeshData(parsed_kfile)

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
    print(f"   Available parts: {sorted(list(mesh_data.part_ids))[:10]}... (showing first 10)")

    # Count elements in source part
    elem_count = sum(1 for e in mesh_data.elements.values()
                     if e['part_id'] == source_part_id)
    print(f"   Elements in part {source_part_id}: {elem_count}")

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
        check_facing=False,  # Disable for initial test
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
