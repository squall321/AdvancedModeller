#!/usr/bin/env python3
"""Model Viewer 성능 프로파일링

현재 렌더링 성능을 측정하고 병목 지점을 찾습니다.
"""
import sys
import os
import time
import numpy as np

# Add to path
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('PYTHONPATH', 'core/kfile_parser')

from kfile_parser.wrapper import KFileParser
from gui.modules.model_viewer.core.mesh_data import MeshData


def profile_mesh_creation(kfile_path: str):
    """메쉬 데이터 생성 성능 측정"""
    print("=" * 80)
    print("  메쉬 데이터 생성 프로파일링")
    print("=" * 80)

    # K-file 로드
    t0 = time.time()
    parser = KFileParser()
    result = parser.parse(kfile_path)
    t1 = time.time()
    print(f"\n1. K-file 파싱: {(t1-t0)*1000:.1f} ms")

    # 데이터 카운트
    node_count = len(result.nodes)
    shell_count = len([e for e in result.elements if e.element_type.name == 'SHELL'])
    solid_count = len([e for e in result.elements if e.element_type.name == 'SOLID'])

    print(f"   - Nodes: {node_count:,}")
    print(f"   - Shell elements: {shell_count:,}")
    print(f"   - Solid elements: {solid_count:,}")

    # MeshData 생성
    t0 = time.time()

    # ParsedModelData 모킹
    class MockModel:
        def __init__(self, parsed_result):
            self._result = parsed_result

        @property
        def nodes(self):
            class NodeWrapper:
                def __init__(self, nodes):
                    self._nodes = nodes
                def getNodeList(self):
                    return np.array([[n.nid, n.x, n.y, n.z] for n in self._nodes])
            return NodeWrapper(self._result.nodes)

        @property
        def element_shell(self):
            class ShellWrapper:
                def __init__(self, elements):
                    self._elements = [e for e in elements if e.element_type.name == 'SHELL']
                def getShellElementList(self):
                    return np.array([[e.eid, e.pid] + e.node_ids for e in self._elements])
            return ShellWrapper(self._result.elements)

        @property
        def element_solid(self):
            class SolidWrapper:
                def __init__(self, elements):
                    self._elements = [e for e in elements if e.element_type.name == 'SOLID']
                def getSolidElementList(self):
                    return np.array([[e.eid, e.pid] + e.node_ids for e in self._elements])
            return SolidWrapper(self._result.elements)

        @property
        def parts(self):
            class PartWrapper:
                def __init__(self, parts):
                    self._parts = parts
                def getPartList(self):
                    return np.array([[p.pid, p.secid if hasattr(p, 'secid') else 0, p.mid if hasattr(p, 'mid') else 0] for p in self._parts])
            return PartWrapper(self._result.parts)

    model = MockModel(result)
    mesh = MeshData.from_parsed_model(model)

    t1 = time.time()
    print(f"\n2. MeshData 생성: {(t1-t0)*1000:.1f} ms")
    print(f"   - Nodes: {len(mesh.nodes):,}")
    print(f"   - Elements: {len(mesh.elements):,} ({mesh.element_type})")
    print(f"   - Parts: {len(mesh.part_elements)}")

    return mesh


def profile_rendering_data(mesh: MeshData):
    """렌더링 데이터 준비 성능 측정"""
    print("\n" + "=" * 80)
    print("  렌더링 데이터 프로파일링")
    print("=" * 80)

    # 모든 Part 표시
    visible_parts = set(mesh.part_elements.keys())

    t0 = time.time()
    visible_elem_indices = mesh.get_visible_elements(visible_parts)
    t1 = time.time()
    print(f"\n1. Visible elements 필터링: {(t1-t0)*1000:.3f} ms")
    print(f"   - 표시 요소: {len(visible_elem_indices):,}")

    # 라인 데이터 생성 (현재 방식)
    t0 = time.time()

    nodes = mesh.nodes
    elements = mesh.elements[visible_elem_indices]
    line_count = 0

    if mesh.element_type == 'shell':
        # Shell: 4 lines per element
        line_count = len(elements) * 4
    else:  # solid
        # Solid: 12 lines per element
        line_count = len(elements) * 12

    t1 = time.time()
    print(f"\n2. 라인 카운트 계산: {(t1-t0)*1000:.3f} ms")
    print(f"   - 총 라인 수: {line_count:,}")
    print(f"   - 총 vertex 호출: {line_count * 2:,}")

    # VBO 데이터 생성 시뮬레이션
    t0 = time.time()

    if mesh.element_type == 'shell':
        # Shell wireframe: 4 edges per element, 2 vertices per edge
        vbo_data = np.empty((len(elements) * 4 * 2, 3), dtype=np.float32)
        idx = 0
        for elem in elements:
            n1, n2, n3, n4 = elem
            edges = [(n1, n2), (n2, n3), (n3, n4), (n4, n1)]
            for i, j in edges:
                vbo_data[idx] = nodes[i]
                vbo_data[idx + 1] = nodes[j]
                idx += 2
    else:  # solid
        # Solid wireframe: 12 edges per element
        vbo_data = np.empty((len(elements) * 12 * 2, 3), dtype=np.float32)
        idx = 0
        for elem in elements:
            n1, n2, n3, n4, n5, n6, n7, n8 = elem
            edges = [
                (n1, n2), (n2, n3), (n3, n4), (n4, n1),  # 아래
                (n5, n6), (n6, n7), (n7, n8), (n8, n5),  # 위
                (n1, n5), (n2, n6), (n3, n7), (n4, n8),  # 수직
            ]
            for i, j in edges:
                vbo_data[idx] = nodes[i]
                vbo_data[idx + 1] = nodes[j]
                idx += 2

    t1 = time.time()
    print(f"\n3. VBO 데이터 생성 (numpy): {(t1-t0)*1000:.1f} ms")
    print(f"   - VBO 크기: {vbo_data.nbytes / 1024 / 1024:.2f} MB")
    print(f"   - Vertex 수: {len(vbo_data):,}")

    # 예상 성능
    print(f"\n예상 성능 개선:")
    print(f"   - 현재 방식: glVertex3fv() {line_count * 2:,}번 호출/프레임")
    print(f"   - VBO 방식: glDrawArrays() 1번 호출/프레임")
    print(f"   - 예상 속도 향상: 10-100배")

    return vbo_data


def estimate_fps(mesh: MeshData):
    """FPS 추정"""
    print("\n" + "=" * 80)
    print("  FPS 추정")
    print("=" * 80)

    vertex_count = len(mesh.elements) * (4 if mesh.element_type == 'shell' else 12) * 2

    # 경험적 추정 (GPU 성능에 따라 다름)
    # Legacy glBegin/glEnd: ~100K vertices @ 60 FPS
    # VBO: ~10M vertices @ 60 FPS

    legacy_fps = 60 * (100_000 / max(vertex_count, 1))
    vbo_fps = 60 * (10_000_000 / max(vertex_count, 1))

    print(f"\n현재 방식 (glBegin/glEnd) 예상 FPS: {legacy_fps:.1f}")
    print(f"VBO 방식 예상 FPS: {min(vbo_fps, 300):.1f}")  # Cap at 300
    print(f"개선 비율: {min(vbo_fps / max(legacy_fps, 0.1), 100):.1f}x")


def main():
    kfile_path = os.path.join(os.path.dirname(__file__), 'examples/DropSet.k')

    if not os.path.exists(kfile_path):
        print(f"Error: K-file not found: {kfile_path}")
        return

    print(f"\nK-file: {kfile_path}\n")

    # 프로파일링
    mesh = profile_mesh_creation(kfile_path)
    vbo_data = profile_rendering_data(mesh)
    estimate_fps(mesh)

    print("\n" + "=" * 80)
    print("  프로파일링 완료!")
    print("=" * 80)
    print("\n다음 단계: VBO 렌더링 구현으로 10-100배 속도 향상\n")


if __name__ == "__main__":
    main()