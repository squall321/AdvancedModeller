#!/usr/bin/env python3
"""Model Viewer 빠른 테스트 - DropSet.k"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core" / "kfile_parser"))

# Qt 환경 변수
os.environ.setdefault('QT_API', 'pyside6')
os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')  # Linux GUI

from PySide6.QtWidgets import QApplication
from gui.app_context import AppContext
from gui.modules.model_viewer.core.mesh_data import MeshData

def test_mesh_creation():
    """메쉬 데이터 생성 테스트 (GUI 없이)"""
    print("=" * 80)
    print("  Model Viewer - Mesh Data 테스트")
    print("=" * 80)

    # AppContext 생성
    ctx = AppContext()

    # K-file 로드
    kfile_path = project_root / "examples" / "DropSet.k"
    print(f"\n1. K-file 로드: {kfile_path}")

    if not kfile_path.exists():
        print(f"   ERROR: 파일이 없습니다!")
        return False

    result = ctx.load_k_file(str(kfile_path))
    if not result:
        print(f"   ERROR: 로드 실패!")
        return False

    print(f"   ✓ 로드 성공!")

    # 메쉬 데이터 생성
    print(f"\n2. 메쉬 데이터 생성")
    try:
        mesh = MeshData.from_parsed_model(ctx.model)
        print(f"   ✓ 메쉬 생성 성공!")

        # 통계 출력
        print(f"\n3. 메쉬 통계:")
        print(f"   - Nodes:    {len(mesh.nodes):,}")
        print(f"   - Elements: {len(mesh.elements):,} ({mesh.element_type})")
        print(f"   - Parts:    {len(mesh.part_elements)}")
        print(f"\n4. Bounding Box:")
        print(f"   - Min: {mesh.bounds[0]}")
        print(f"   - Max: {mesh.bounds[1]}")
        print(f"   - Center: {mesh.get_center()}")
        print(f"   - Size: {mesh.get_size():.2f}")

        print(f"\n5. Part 정보:")
        for pid in sorted(list(mesh.part_elements.keys())[:5]):  # 처음 5개만
            name = mesh.part_names.get(pid, f"Part {pid}")
            count = len(mesh.part_elements[pid])
            print(f"   - Part {pid:3d}: {count:6,} elements - {name}")

        if len(mesh.part_elements) > 5:
            print(f"   ... 외 {len(mesh.part_elements) - 5}개 Part")

        print("\n" + "=" * 80)
        print("  ✓ 메쉬 데이터 생성 성공!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui():
    """GUI 테스트"""
    print("\n" + "=" * 80)
    print("  GUI 실행 중...")
    print("=" * 80)

    app = QApplication(sys.argv)

    # AppContext 생성
    ctx = AppContext()

    # K-file 자동 로드
    kfile_path = project_root / "examples" / "DropSet.k"
    ctx.load_k_file(str(kfile_path))

    # Model Viewer 생성
    from gui.modules.model_viewer.module import ModelViewerModule
    viewer = ModelViewerModule(ctx)
    viewer.setWindowTitle("Model Viewer - DropSet.k")
    viewer.resize(1200, 800)

    # 자동으로 모델 로드
    viewer._load_from_context_model()

    viewer.show()

    print("\n조작법:")
    print("  - 좌클릭 드래그: 회전")
    print("  - 중클릭 or Shift+드래그: 팬")
    print("  - 휠: 줌")
    print("  - Part 체크박스: 표시/숨기기")
    print("  - 뷰 리셋: 자동 fit")
    print("")

    sys.exit(app.exec())


if __name__ == '__main__':
    # 인자에 따라 테스트 모드 선택
    if len(sys.argv) > 1 and sys.argv[1] == '--mesh-only':
        # 메쉬 생성만 테스트 (GUI 없이)
        success = test_mesh_creation()
        sys.exit(0 if success else 1)
    else:
        # GUI 테스트
        test_gui()
