#!/usr/bin/env python3
"""Debug DropSet.k Adjacent Parts Detection

PKG 파트들끼리 제대로 인접 파트로 검출되는지 테스트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from gui.app_context import AppContext
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector


def test_dropset():
    """Test with DropSet.k"""
    print("=" * 80)
    print("DropSet.k Adjacent Parts Detection Debug")
    print("=" * 80)

    # Load DropSet.k
    ctx = AppContext()
    kfile = "examples/DropSet.k"

    print(f"\n1. Loading: {kfile}")
    if not ctx.load_k_file(kfile):
        print("ERROR: Failed to load")
        return

    print(f"   ✓ Parts: {ctx.model.part_count}")
    print(f"   ✓ Nodes: {ctx.model.node_count}")
    print(f"   ✓ Elements: {ctx.model.element_count}")

    # Create MeshData
    print("\n2. Creating MeshData...")
    mesh_data = MeshData.from_parsed_model(ctx.model)
    if mesh_data is None:
        print("ERROR: MeshData creation failed")
        return

    print(f"   ✓ MeshData parts: {len(mesh_data.part_elements)}")

    # List all parts
    print("\n3. Part List:")
    for pid in sorted(mesh_data.part_ids):
        name = mesh_data.part_names.get(pid, f"Part {pid}")
        elem_count = len(mesh_data.part_elements[pid])
        print(f"   Part {pid:3d}: {name:30s} ({elem_count:6d} elements)")

    # Find PKG parts
    pkg_parts = []
    for pid in mesh_data.part_ids:
        name = mesh_data.part_names.get(pid, "").upper()
        if "PKG" in name:
            pkg_parts.append((pid, mesh_data.part_names.get(pid, "")))

    print(f"\n4. Found {len(pkg_parts)} PKG parts:")
    for pid, name in pkg_parts:
        print(f"   Part {pid}: {name}")

    if not pkg_parts:
        print("   No PKG parts found!")
        return

    # Initialize detector
    print("\n5. Initializing detector...")
    detector = AdjacentPartsDetector(mesh_data)
    print("   ✓ Detector ready")

    # Test with first PKG
    source_pid, source_name = pkg_parts[0]
    print(f"\n6. Testing with source: Part {source_pid} ({source_name})")

    # Get bbox
    bbox = detector._spatial_index.get_part_bbox(source_pid)
    print(f"   BBox min: {bbox.min_point}")
    print(f"   BBox max: {bbox.max_point}")
    print(f"   BBox size: {bbox.size}")
    print(f"   BBox center: {bbox.center}")

    # Suggest plane
    plane = detector.suggest_best_plane(source_pid)
    print(f"\n7. Suggested plane: {plane}")

    # Auto thickness
    thickness_min, thickness_max = detector.get_auto_thickness_range(
        source_pid, plane, search_multiplier=10.0  # Larger search
    )
    print(f"   Thickness range: {thickness_min:.2f} ~ {thickness_max:.2f}")

    # Spatial query
    print(f"\n8. Spatial query for candidates...")
    candidates = detector._spatial_index.query_thickness_range(
        source_pid, plane, thickness_min, thickness_max
    )
    print(f"   Found {len(candidates)} candidates: {sorted(list(candidates))}")

    # Check if other PKGs are in candidates
    other_pkg_ids = [pid for pid, _ in pkg_parts if pid != source_pid]
    print(f"\n9. Checking other PKG parts in candidates:")
    for other_pid in other_pkg_ids:
        other_name = mesh_data.part_names.get(other_pid, "")
        if other_pid in candidates:
            print(f"   ✓ Part {other_pid} ({other_name}) IS in candidates")
            # Check bbox distance
            other_bbox = detector._spatial_index.get_part_bbox(other_pid)
            print(f"     - Other bbox: {other_bbox.min_point} ~ {other_bbox.max_point}")

            # Distance along plane axis
            if plane == 'XY':
                axis_idx = 2
            elif plane == 'YZ':
                axis_idx = 0
            else:
                axis_idx = 1

            # Check overlap on plane axes and distance on normal axis
            dist_min = abs(bbox.min_point[axis_idx] - other_bbox.max_point[axis_idx])
            dist_max = abs(bbox.max_point[axis_idx] - other_bbox.min_point[axis_idx])
            dist = min(dist_min, dist_max)
            print(f"     - Distance along {['X','Y','Z'][axis_idx]}: {dist:.2f}")
        else:
            print(f"   ✗ Part {other_pid} ({other_name}) NOT in candidates")
            other_bbox = detector._spatial_index.get_part_bbox(other_pid)
            print(f"     - Other bbox: {other_bbox.min_point} ~ {other_bbox.max_point}")

    # Exterior faces check
    print(f"\n10. Checking exterior faces...")
    detector._fast_detector._ensure_exterior_faces()
    ext_faces = detector._fast_detector._exterior_faces

    if source_pid in ext_faces:
        print(f"   Source part {source_pid}: {len(ext_faces[source_pid])} exterior faces")
    else:
        print(f"   Source part {source_pid}: NO exterior faces!")

    for other_pid in other_pkg_ids[:3]:  # Check first 3
        if other_pid in ext_faces:
            print(f"   Part {other_pid}: {len(ext_faces[other_pid])} exterior faces")

    # Run detection
    print(f"\n11. Running detection...")
    result = detector.find_adjacent(
        source_part_id=source_pid,
        plane=plane,
        thickness_min=thickness_min,
        thickness_max=thickness_max,
        check_facing=False,  # Disable facing check for now
        ray_density=0.1,
        coverage_threshold=0.05,
        visualize=False,
        layer_mode=True  # Enable layer mode for PCB packages
    )

    print(f"\n{'=' * 80}")
    print("DETECTION RESULTS:")
    print(f"{'=' * 80}")
    print(f"Adjacent parts found: {len(result.adjacent_parts)}")
    print(f"Part IDs: {sorted(list(result.adjacent_parts))}")

    # Check which PKGs were found
    found_pkgs = []
    missed_pkgs = []
    for other_pid, other_name in pkg_parts:
        if other_pid == source_pid:
            continue
        if other_pid in result.adjacent_parts:
            found_pkgs.append((other_pid, other_name))
        else:
            missed_pkgs.append((other_pid, other_name))

    print(f"\nPKG Detection Results:")
    print(f"  ✓ Found PKGs ({len(found_pkgs)}):")
    for pid, name in found_pkgs:
        cov = result.coverage.get(pid, 0)
        print(f"    Part {pid}: {name} (coverage: {cov*100:.1f}%)")

    print(f"  ✗ Missed PKGs ({len(missed_pkgs)}):")
    for pid, name in missed_pkgs:
        print(f"    Part {pid}: {name}")
        if pid in candidates:
            print(f"      (was in candidates but not detected)")
        else:
            print(f"      (not in candidates - spatial query issue)")

    print(f"\n{'=' * 80}")
    print("Timing:")
    for key, val in result.timing.items():
        print(f"  {key}: {val:.2f} ms")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    test_dropset()
