#!/usr/bin/env python3
"""외곽면 추출 테스트

간단한 Hex 요소로 외곽면 추출 알고리즘 검증
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from gui.modules.model_viewer.core.mesh_data import MeshData

def create_test_cube():
    """2x2x2 큐브 (8개 Hex 요소)"""
    # 27개 노드 (3x3x3 그리드)
    nodes = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                nodes.append([x, y, z])
    nodes = np.array(nodes, dtype=np.float32)

    # 8개 Hex 요소
    elements = []
    for z in range(2):
        for y in range(2):
            for x in range(2):
                # 큐브의 8개 코너 노드
                n0 = z * 9 + y * 3 + x
                n1 = n0 + 1
                n2 = n0 + 3 + 1
                n3 = n0 + 3
                n4 = n0 + 9
                n5 = n4 + 1
                n6 = n4 + 3 + 1
                n7 = n4 + 3
                elements.append([n0, n1, n2, n3, n4, n5, n6, n7])
    elements = np.array(elements, dtype=np.int32)

    # 모든 요소를 Part 1에 배치
    part_elements = {1: np.arange(8, dtype=np.int32)}
    part_names = {1: "Test Cube"}

    mesh = MeshData(
        nodes=nodes,
        elements=elements,
        part_elements=part_elements,
        part_names=part_names,
        element_type='solid',
        bounds=(nodes.min(axis=0), nodes.max(axis=0))
    )

    return mesh

def main():
    print("="*60)
    print("외곽면 추출 테스트")
    print("="*60)

    # 테스트 큐브 생성
    print("\n[1] 2x2x2 큐브 생성 (8개 Hex 요소)")
    mesh = create_test_cube()
    print(f"   Nodes: {len(mesh.nodes)}")
    print(f"   Elements: {len(mesh.elements)}")
    print(f"   Total faces (if all rendered): {len(mesh.elements) * 6} = {len(mesh.elements) * 6}")

    # 외곽면 추출
    print("\n[2] 외곽면 추출...")
    exterior = mesh.extract_exterior_faces()

    # 결과 분석
    print("\n[3] 결과 분석")
    for pid, faces in exterior.items():
        print(f"\n   Part {pid} ({mesh.part_names[pid]}):")
        print(f"   - 외곽면 개수: {len(faces)}")
        print(f"   - 요소별 면 분포:")

        # 요소별로 그룹화
        elem_face_count = {}
        for elem_idx, face_indices in faces:
            elem_face_count[elem_idx] = elem_face_count.get(elem_idx, 0) + 1

        for elem_idx in sorted(elem_face_count.keys()):
            count = elem_face_count[elem_idx]
            print(f"     Element {elem_idx}: {count} faces")

    # 통계
    total_exterior_faces = sum(len(faces) for faces in exterior.values())
    total_possible_faces = len(mesh.elements) * 6

    print(f"\n[4] 통계")
    print(f"   전체 가능한 면: {total_possible_faces}")
    print(f"   외곽면: {total_exterior_faces}")
    print(f"   내부면 (제거됨): {total_possible_faces - total_exterior_faces}")
    print(f"   감소율: {100 * (1 - total_exterior_faces / total_possible_faces):.1f}%")

    # 이론적 검증
    print(f"\n[5] 이론적 검증")
    print(f"   2x2x2 큐브는 외부 표면만 있어야 함")
    print(f"   예상 외곽면: 24 (6 faces * 4 surface elements on each face)")
    print(f"   실제 외곽면: {total_exterior_faces}")

    # 코너/엣지/면 요소 분류
    print(f"\n[6] 요소별 분류")
    for pid, faces in exterior.items():
        elem_face_count = {}
        for elem_idx, face_indices in faces:
            elem_face_count[elem_idx] = elem_face_count.get(elem_idx, 0) + 1

        corner_elems = [e for e, c in elem_face_count.items() if c == 3]
        edge_elems = [e for e, c in elem_face_count.items() if c == 2]
        face_elems = [e for e, c in elem_face_count.items() if c == 1]

        print(f"   Part {pid}:")
        print(f"   - 코너 요소 (3면): {len(corner_elems)} 개 → {corner_elems}")
        print(f"   - 엣지 요소 (2면): {len(edge_elems)} 개 → {edge_elems}")
        print(f"   - 면 요소 (1면): {len(face_elems)} 개 → {face_elems}")
        print(f"   - 내부 요소 (0면): {8 - len(elem_face_count)} 개")

    # 검증
    expected = 24  # 2x2x2 큐브의 외곽면
    if total_exterior_faces == expected:
        print(f"\n✅ 테스트 통과! 외곽면 추출이 정확합니다.")
    else:
        print(f"\n❌ 테스트 실패! 예상: {expected}, 실제: {total_exterior_faces}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
