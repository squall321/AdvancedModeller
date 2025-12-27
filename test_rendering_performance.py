"""렌더링 성능 테스트 스크립트"""
import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from core.KooDynaKeyword import KFileReader
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.app_context import ParsedModelData


def test_rendering_performance(k_file_path: str):
    """렌더링 성능 테스트"""

    print("=" * 60)
    print("Rendering Performance Test")
    print("=" * 60)
    print()

    # 1. K-file 파싱
    print("[1/4] Parsing K-file...")
    start = time.perf_counter()
    reader = KFileReader(
        k_file_path,
        parse_nodes=True,
        parse_parts=True,
        parse_elements=True
    )
    parse_time = time.perf_counter() - start

    stats = reader.stats
    print(f"  ✓ Parse time: {parse_time:.3f}s")
    print(f"  ✓ Nodes: {stats.get('node_count', 0):,}")
    print(f"  ✓ Elements: {stats.get('element_count', 0):,}")
    print(f"  ✓ Parts: {stats.get('part_count', 0):,}")
    print()

    # 2. Model 데이터 준비
    print("[2/4] Creating model data...")
    start = time.perf_counter()

    model = ParsedModelData(
        filepath=k_file_path,
        filename="DropSet.k",
        parse_time_ms=parse_time * 1000
    )
    model._reader = reader
    model.node_count = stats.get('node_count', 0)
    model.element_count = stats.get('element_count', 0)
    model.part_count = stats.get('part_count', 0)

    model_time = time.perf_counter() - start
    print(f"  ✓ Model creation: {model_time:.3f}s")
    print()

    # 3. MeshData 생성
    print("[3/4] Creating mesh data...")
    start = time.perf_counter()
    mesh = MeshData.from_parsed_model(model)
    mesh_time = time.perf_counter() - start

    print(f"  ✓ Mesh creation: {mesh_time:.3f}s")
    print(f"  ✓ Vertices: {len(mesh.vertices):,}")
    print(f"  ✓ Faces: {len(mesh.faces):,}")
    print()

    # 4. OpenGL 렌더링 테스트
    print("[4/4] Testing OpenGL rendering...")

    app = QApplication(sys.argv)

    # VBO 렌더러로 위젯 생성
    widget = ModelGLWidget(backend='vbo')
    widget.resize(800, 600)
    widget.show()

    # GPU 정보는 initializeGL에서 출력됨

    # 메시 설정
    start = time.perf_counter()
    widget.set_mesh(mesh)
    widget.set_visible_parts(set(mesh.part_elements.keys()))
    widget.reset_view()
    setup_time = time.perf_counter() - start

    print(f"  ✓ Mesh setup: {setup_time:.3f}s")
    print()

    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"Total time (parsing + mesh + setup): {parse_time + mesh_time + setup_time:.3f}s")
    print()
    print("Window opened. Check console for GPU info.")
    print("Close the window to exit.")
    print()

    # 3초 후 종료
    QTimer.singleShot(3000, app.quit)

    sys.exit(app.exec())


if __name__ == '__main__':
    test_rendering_performance(r'd:\AdvancedModeller\examples\DropSet.k')
