#!/usr/bin/env python3
"""
Simulate GUI DOE generation scenarios.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from core.KooDynaKeyword import KFileReader
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def simulate_diagnosis(source_part, adjacent_ids, max_displacement, doe_count, generator):
    """Simulate the diagnosis logic from GUI"""

    doe_result = generator.generate_placements(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        num_samples=doe_count,
        max_displacement=max_displacement,
        enable_resampling=True
    )

    success_rate = doe_result.num_valid / doe_count if doe_count > 0 else 0.0

    print(f"\n{'='*60}")
    print(f"Simulation Result")
    print(f"{'='*60}")
    print(f"Result: {doe_result.num_valid}/{doe_result.num_total} valid")
    print(f"Success rate: {success_rate*100:.1f}%")

    if doe_result.num_valid == 0:
        print("\n진단:")

        # Diagnose issue
        source_bbox = generator.get_2d_bbox(source_part)
        source_cx, source_cy = source_bbox.center()

        # Find nearest adjacent part
        min_dist = float('inf')
        for adj_id in adjacent_ids[:10]:
            adj_bbox = generator.get_2d_bbox(adj_id)
            adj_cx, adj_cy = adj_bbox.center()
            dist = ((source_cx - adj_cx)**2 + (source_cy - adj_cy)**2)**0.5
            min_dist = min(min_dist, dist)

        print(f"  가장 가까운 인접 파트 거리: {min_dist:.1f} mm")
        print(f"  현재 Max Displacement: {max_displacement:.1f} mm")

        if max_displacement < min_dist:
            print(f"  ⚠ Max displacement가 너무 작습니다!")
            print(f"  권장값: {min_dist * 1.2:.1f} mm 이상")
            print(f"\n[GUI 팝업 메시지]")
            print(f"유효한 배치를 생성할 수 없습니다.")
            print(f"")
            print(f"현재 Max Displacement: {max_displacement:.1f} mm")
            print(f"가장 가까운 인접 파트: {min_dist:.1f} mm")
            print(f"")
            print(f"Max Displacement를 {min_dist * 1.2:.1f} mm 이상으로 증가시켜주세요.")
        else:
            print(f"  가능 영역이 매우 좁습니다.")
            print(f"\n[GUI 팝업 메시지]")
            print(f"유효한 배치를 생성할 수 없습니다.")
            print(f"")
            print(f"소스 파트가 인접 파트들에 의해 완전히 둘러싸여 있거나,")
            print(f"가능한 공간이 매우 제한적입니다.")
            print(f"")
            print(f"Max Displacement를 증가시키거나 다른 파트를 선택해주세요.")

    elif success_rate < 0.7:
        print(f"\n[GUI 팝업 메시지]")
        print(f"요청한 {doe_count}개 중 {doe_result.num_valid}개만 생성되었습니다.")
        print(f"")
        print(f"Max Displacement를 증가시키면 더 많은 배치를 생성할 수 있습니다.")
    else:
        print(f"\n✓ 성공!")


def main():
    print("=" * 60)
    print("GUI DOE Generation Simulation")
    print("=" * 60)

    # Load DropSet.k
    print("\nLoading DropSet.k...")
    reader = KFileReader(
        "examples/DropSet.k",
        parse_nodes=True,
        parse_parts=True,
        parse_elements=True
    )

    parsed = reader._parsed
    nodes_list = list(parsed.nodes)
    elements_list = list(parsed.elements)
    parts_list = list(parsed.parts)

    nodes = np.array([[n.x, n.y, n.z] for n in nodes_list], dtype=np.float32)
    node_id_to_idx = {n.nid: i for i, n in enumerate(nodes_list)}

    part_elements = {}
    part_names = {}
    for part in parts_list:
        part_names[part.pid] = getattr(part, 'name', f'Part {part.pid}')
        part_elements[part.pid] = []

    elements = []
    for elem_idx, elem in enumerate(elements_list):
        node_indices = [node_id_to_idx.get(nid, 0) for nid in elem.nodes if nid != 0]
        elements.append(node_indices)
        if elem.pid in part_elements:
            part_elements[elem.pid].append(elem_idx)

    elements = np.array(elements, dtype=np.int32)
    bounds = (nodes.min(axis=0), nodes.max(axis=0))

    mesh_data = MeshData(
        nodes=nodes,
        elements=elements,
        part_elements=part_elements,
        part_names=part_names,
        element_type="solid",
        bounds=bounds
    )

    # Find PKG and detect
    pkg_parts = [pid for pid, name in part_names.items() if 'PKG' in name.upper()]
    source_part = pkg_parts[0]

    detector = AdjacentPartsDetector(mesh_data)
    result = detector.find_adjacent(
        source_part_id=source_part,
        plane='XY',
        thickness_min=0.0,
        thickness_max=50.0,
        check_facing=True,
        ray_density=0.1,
        coverage_threshold=0.1,
        visualize=False,
        layer_mode=True
    )

    adjacent_ids = list(result.adjacent_parts)
    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)

    # Simulate user scenarios
    print("\n\n" + "="*60)
    print("시나리오 1: Max Displacement 너무 작음 (10mm)")
    print("="*60)
    simulate_diagnosis(source_part, adjacent_ids, 10.0, 20, generator)

    print("\n\n" + "="*60)
    print("시나리오 2: 정상 동작 (20mm)")
    print("="*60)
    simulate_diagnosis(source_part, adjacent_ids, 20.0, 20, generator)

    print("\n\n" + "="*60)
    print("시나리오 3: 충분한 공간 (50mm)")
    print("="*60)
    simulate_diagnosis(source_part, adjacent_ids, 50.0, 20, generator)

    return 0


if __name__ == "__main__":
    sys.exit(main())
