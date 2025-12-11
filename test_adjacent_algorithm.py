#!/usr/bin/env python3
"""Test Adjacent Parts Detection Algorithm"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from gui.app_context import AppContext
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.modules.adjacent_parts_viewer.core import AdjacentPartsDetector


def test_algorithm():
    """Test the detection algorithm step by step"""

    print("=" * 80)
    print("Adjacent Parts Detection Algorithm Test")
    print("=" * 80)

    # Load model
    ctx = AppContext()
    kfile_path = "/home/koopark/cursor/pyKooCAE/occProject/Generators/dist/DisplayImpact/PackageInfoBoxMeshCompositeMaterial_3ptbending_1.0_0.0_0.02_0.0019_0.1_0.0019_0.1_0.000419_0.0006.k"

    print(f"\n1. Loading K-file: {kfile_path}")
    if not ctx.load_k_file(kfile_path):
        print("ERROR: Failed to load K-file")
        return

    print(f"   ✓ Loaded: {ctx.model.part_count} parts, "
          f"{ctx.model.node_count} nodes, {ctx.model.element_count} elements")

    # Create MeshData
    print("\n2. Creating MeshData...")
    mesh_data = MeshData.from_parsed_model(ctx.model)
    if mesh_data is None:
        print("ERROR: Failed to create MeshData")
        return

    print(f"   ✓ MeshData created: {len(mesh_data.part_elements)} parts")

    # Initialize detector
    print("\n3. Initializing Detector...")
    detector = AdjacentPartsDetector(mesh_data)
    print("   ✓ Detector initialized")

    # Select first part as source
    source_part_id = sorted(mesh_data.part_elements.keys())[0]
    print(f"\n4. Testing with source part: {source_part_id}")

    # Get bounding box
    bbox = detector._spatial_index.get_part_bbox(source_part_id)
    print(f"   BBox: min={bbox.min_point}, max={bbox.max_point}")
    print(f"   Size: {bbox.size}")
    print(f"   Center: {bbox.center}")

    # Suggest plane
    plane = detector.suggest_best_plane(source_part_id)
    print(f"\n5. Suggested plane: {plane}")

    # Auto thickness range
    thickness_min, thickness_max = detector.get_auto_thickness_range(
        source_part_id, plane, search_multiplier=5.0
    )
    print(f"   Thickness range: {thickness_min:.2f} ~ {thickness_max:.2f}")

    # Test spatial query
    print(f"\n6. Testing spatial query...")
    candidates = detector._spatial_index.query_thickness_range(
        source_part_id, plane, thickness_min, thickness_max
    )
    print(f"   ✓ Found {len(candidates)} candidate parts")
    print(f"   Candidates: {sorted(list(candidates))[:10]}..." if len(candidates) > 10
          else f"   Candidates: {sorted(list(candidates))}")

    # Test ray generation
    print(f"\n7. Testing ray generation...")
    ray_origins, ray_direction = detector._generate_bbox_rays(
        source_part_id, plane, density=0.1
    )
    print(f"   ✓ Generated {len(ray_origins)} rays")
    print(f"   Ray direction: {ray_direction}")
    print(f"   First 3 ray origins:")
    for i in range(min(3, len(ray_origins))):
        print(f"     {i}: {ray_origins[i]}")

    # Test ray casting with occlusion
    print(f"\n8. Testing ray casting with occlusion...")
    hits_by_part_pos = detector._ray_tracer.cast_rays_with_occlusion(
        ray_origins, ray_direction, candidates, thickness_max
    )
    print(f"   ✓ Positive direction: {len(hits_by_part_pos)} parts hit")

    hits_by_part_neg = detector._ray_tracer.cast_rays_with_occlusion(
        ray_origins, -ray_direction, candidates, thickness_max
    )
    print(f"   ✓ Negative direction: {len(hits_by_part_neg)} parts hit")

    # Merge
    all_hit_parts = set(hits_by_part_pos.keys()) | set(hits_by_part_neg.keys())
    print(f"   ✓ Total unique parts hit: {len(all_hit_parts)}")

    # Show hit details
    print(f"\n9. Hit details:")
    for pid in sorted(list(all_hit_parts)[:5]):
        hits_pos = len(hits_by_part_pos.get(pid, []))
        hits_neg = len(hits_by_part_neg.get(pid, []))
        total_hits = hits_pos + hits_neg
        coverage = total_hits / len(ray_origins) * 100
        print(f"   Part {pid}: {total_hits} hits ({hits_pos}+, {hits_neg}-), "
              f"coverage={coverage:.1f}%")

    # Full detection
    print(f"\n10. Running full detection...")
    result = detector.find_adjacent(
        source_part_id=source_part_id,
        plane=plane,
        thickness_min=thickness_min,
        thickness_max=thickness_max,
        check_facing=True,
        ray_density=0.1,
        coverage_threshold=0.05,
        visualize=False
    )

    print(f"\n{'=' * 80}")
    print("FINAL RESULTS:")
    print(f"{'=' * 80}")
    print(f"Adjacent parts found: {len(result.adjacent_parts)}")
    print(f"Part IDs: {sorted(list(result.adjacent_parts))}")
    print(f"\nTiming:")
    for key, value in result.timing.items():
        print(f"  {key}: {value:.2f} ms")
    print(f"\nCoverage:")
    for pid in sorted(result.adjacent_parts):
        cov = result.coverage.get(pid, 0)
        print(f"  Part {pid}: {cov*100:.1f}%")

    print(f"\n{'=' * 80}")
    if len(result.adjacent_parts) > 0:
        print("✓ SUCCESS: Algorithm detected adjacent parts!")
    else:
        print("✗ WARNING: No adjacent parts detected")
        print("\nDiagnostics:")
        print(f"  - Candidates found: {len(candidates)}")
        print(f"  - Rays generated: {len(ray_origins)}")
        print(f"  - Parts hit (before filtering): {len(all_hit_parts)}")
        print(f"  - After facing check: {len(result.adjacent_parts)}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    test_algorithm()
