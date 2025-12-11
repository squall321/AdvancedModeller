#!/usr/bin/env python3
"""커스텀 렌더러 사용 예제

OpenGL 컨텍스트 없이 렌더러와 카메라를 직접 조작
"""
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.modules.model_viewer.core.camera import Camera
from gui.modules.model_viewer.backends import VBORenderer, LegacyRenderer
from gui.app_context import AppContext
import numpy as np


def example_renderer_usage():
    """렌더러를 직접 사용하는 예제"""

    print("=" * 80)
    print("  Custom Renderer Usage Example")
    print("=" * 80)

    # 1. 메쉬 데이터 로드 (렌더러와 독립적)
    ctx = AppContext()
    ctx.load_k_file("examples/DropSet.k")
    mesh = MeshData.from_parsed_model(ctx.model)

    print(f"\n1. Mesh loaded:")
    print(f"   - Nodes: {len(mesh.nodes)}")
    print(f"   - Elements: {len(mesh.elements)}")
    print(f"   - Parts: {len(mesh.part_elements)}")

    # 2. 렌더러 생성 (백엔드 선택 가능)
    renderer = VBORenderer()  # 또는 LegacyRenderer()
    print(f"\n2. Renderer created: {renderer.name}")

    # 3. 카메라 생성 (렌더러와 독립적)
    camera = Camera()
    camera.fit_to_bounds(mesh.bounds[0], mesh.bounds[1])
    print(f"\n3. Camera configured:")
    print(f"   - Distance: {camera.distance:.2f}")
    print(f"   - Target: {camera.target}")
    print(f"   - Elevation: {camera.elevation:.1f}°")
    print(f"   - Azimuth: {camera.azimuth:.1f}°")

    # 4. 렌더러에 데이터 설정
    renderer.set_mesh(mesh)
    renderer.set_camera(camera)
    print(f"\n4. Mesh and camera set to renderer")

    # 5. 특정 Part만 선택
    selected_parts = {1, 2, 3}
    renderer.set_visible_parts(selected_parts)
    print(f"\n5. Visible parts set: {selected_parts}")

    # 6. 렌더링 옵션 설정
    renderer.set_show_solid(True)
    renderer.set_show_edges(True)
    renderer.set_show_wireframe(False)
    renderer.set_show_nodes(False)
    print(f"\n6. Rendering options:")
    print(f"   - Solid: ON")
    print(f"   - Edges: ON (black outlines)")
    print(f"   - Wireframe: OFF")
    print(f"   - Nodes: OFF")

    # 7. 카메라 행렬 얻기 (렌더링에 사용)
    view_matrix = camera.get_view_matrix()
    proj_matrix = camera.get_projection_matrix(aspect=16/9)
    print(f"\n7. Camera matrices generated:")
    print(f"   - View matrix: {view_matrix.shape}")
    print(f"   - Projection matrix: {proj_matrix.shape}")

    # 8. 다양한 뷰로 전환 가능
    print(f"\n8. Testing view presets:")
    views = [
        ("Front", camera.view_front),
        ("Top", camera.view_top),
        ("Isometric", camera.view_isometric),
    ]

    for view_name, view_func in views:
        view_func()
        print(f"   - {view_name:12s}: Elev={camera.elevation:5.1f}°, Azim={camera.azimuth:6.1f}°")

    print("\n" + "=" * 80)
    print("  ✓ Renderer, Camera, Mesh are fully independent!")
    print("=" * 80)


def example_mesh_analysis():
    """메쉬 데이터 분석 (렌더링 없이)"""

    print("\n" + "=" * 80)
    print("  Mesh Data Analysis (without rendering)")
    print("=" * 80)

    # 메쉬 로드
    ctx = AppContext()
    ctx.load_k_file("examples/DropSet.k")
    mesh = MeshData.from_parsed_model(ctx.model)

    # Bounding box
    min_bounds, max_bounds = mesh.bounds
    size = np.linalg.norm(max_bounds - min_bounds)
    center = (min_bounds + max_bounds) / 2.0

    print(f"\nBounding Box:")
    print(f"  Min: [{min_bounds[0]:.2f}, {min_bounds[1]:.2f}, {min_bounds[2]:.2f}]")
    print(f"  Max: [{max_bounds[0]:.2f}, {max_bounds[1]:.2f}, {max_bounds[2]:.2f}]")
    print(f"  Center: [{center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f}]")
    print(f"  Size: {size:.2f}")

    # Part별 통계
    print(f"\nPart Statistics:")
    for pid in sorted(mesh.part_elements.keys())[:5]:  # 첫 5개만
        elem_count = len(mesh.part_elements[pid])
        part_name = mesh.part_names.get(pid, "Unknown")
        print(f"  Part {pid:3d}: {elem_count:5d} elements - {part_name}")

    print("\n  ...")
    print(f"\n  Total: {len(mesh.part_elements)} parts")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    example_renderer_usage()
    example_mesh_analysis()
