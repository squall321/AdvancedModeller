# Model Viewer - 사용 가이드

## 🚀 빠른 시작

### 1. 테스트 (메쉬 데이터 생성만)
```bash
./test_viewer_quick.py --mesh-only
```

### 2. GUI 실행
```bash
# 통합 GUI에서
./rungui.sh
# → "모델 뷰어" 모듈 선택

# 또는 독립 실행
./test_viewer_quick.py
```

### 3. K-file 로드
- **파일 선택** 버튼 클릭
- `examples/DropSet.k` 선택 (또는 다른 K-file)
- 자동으로 3D 렌더링됨

---

## 🎮 조작법

### 마우스
| 조작 | 동작 |
|------|------|
| **좌클릭 드래그** | 회전 |
| **중클릭 드래그** | 팬 (이동) |
| **Shift + 좌클릭 드래그** | 팬 (이동) |
| **휠** | 줌 (확대/축소) |

### 버튼
| 버튼 | 기능 |
|------|------|
| **파일 선택** | K-file 열기 |
| **뷰 리셋** | 모델이 화면에 꽉 차도록 자동 조정 |
| **F/B/L/R/T/Bo/Iso** | 6-View 프리셋 (Front/Back/Left/Right/Top/Bottom/Isometric) ✨ NEW |
| **전체 선택** | 모든 Part 표시 |
| **전체 해제** | 모든 Part 숨기기 |

### 체크박스
- Part별로 개별 표시/숨기기 가능
- 좌측 트리에서 Part를 체크/해제

### 옵션 (VBO 고속화 버전!)
- **Solid**: 면 채우기 (Part별 랜덤 색상) ✨ NEW
- **와이어프레임**: 모서리 표시 (Part별 색상) ✨ 색상 추가
- **노드**: 노드 점 표시
- **FPS 표시**: 실시간 성능 모니터링 ✨ NEW

---

## 📊 테스트 결과

### DropSet.k (예제 파일)
```
Nodes:    29,624
Elements: 44,657 (solid)
Parts:    23

Bounding Box:
  Min: [-245.2, -73.5, -110.7]
  Max: [60.6, 319.9, 113.5]
  Size: 546.4

Parts:
  - Part 1: 33,241 elements - Front\Metal
  - Part 2: 68 elements - Front\Wall
  - Part 3: 544 elements - PCB\PCB
  ... (외 20개)
```

---

## 🔧 프로그래밍 방식 사용

### MeshData 직접 생성
```python
from gui.app_context import AppContext
from gui.modules.model_viewer.core.mesh_data import MeshData

# K-file 로드
ctx = AppContext()
ctx.load_k_file("examples/DropSet.k")

# MeshData 생성
mesh = MeshData.from_parsed_model(ctx.model)

print(f"Nodes: {len(mesh.nodes)}")
print(f"Elements: {len(mesh.elements)}")
print(f"Parts: {len(mesh.part_elements)}")
```

### GLWidget 직접 사용
```python
from PySide6.QtWidgets import QApplication
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget
from gui.modules.model_viewer.core.mesh_data import MeshData

app = QApplication([])

# GL Widget 생성
gl_widget = ModelGLWidget()
gl_widget.resize(800, 600)

# 메쉬 설정
mesh = MeshData.from_parsed_model(model)
gl_widget.set_mesh(mesh)

# 표시할 Part 설정
gl_widget.set_visible_parts({1, 2, 3})

gl_widget.show()
app.exec()
```

### Camera 직접 사용
```python
from gui.modules.model_viewer.core.camera import Camera
import numpy as np

camera = Camera()

# 모델에 맞춤
camera.fit_to_bounds(
    min_bounds=np.array([-100, -100, -100]),
    max_bounds=np.array([100, 100, 100])
)

# 회전
camera.rotate(delta_azim=10, delta_elev=5)

# 줌
camera.zoom(1.2)

# 행렬 얻기
view_matrix = camera.get_view_matrix()
proj_matrix = camera.get_projection_matrix(aspect=16/9)
```

---

## 🎯 DOE 시각화 예제

```python
# DOE 결과에 따라 Part 색상 변경 (향후 구현)
from gui.modules.model_viewer.module import ModelViewerModule

viewer = ModelViewerModule(ctx)

# DOE 파라미터에 따라 특정 Part만 표시
viewer.set_visible_parts({1, 3, 5})  # 선택된 Part만
viewer.reset_view()
```

---

## 📸 스크린샷 (테스트 결과)

```
================================================================================
  Model Viewer - Mesh Data 테스트
================================================================================

1. K-file 로드: /path/to/DropSet.k
   ✓ 로드 성공!

2. 메쉬 데이터 생성
   ✓ 메쉬 생성 성공!

3. 메쉬 통계:
   - Nodes:    29,624
   - Elements: 44,657 (solid)
   - Parts:    23

4. Bounding Box:
   - Min: [-245.24971   -73.5      -110.750244]
   - Max: [ 60.562656 319.90384  113.5538  ]
   - Center: [-92.34353   123.20192     1.4017792]
   - Size: 546.44

5. Part 정보:
   - Part   1: 33,241 elements - Front\Metal
   - Part   2:     68 elements - Front\Wall
   - Part   3:    544 elements - PCB\PCB
   - Part   4:      6 elements - PKG\PKG 1
   - Part   5:     15 elements - PKG\PKG 3
   ... 외 18개 Part

================================================================================
  ✓ 메쉬 데이터 생성 성공!
================================================================================
```

---

## ⚠️ 알려진 이슈

1. **헤드리스 환경** (서버 등)
   - OpenGL이 없으면 실행 불가
   - 해결: `xvfb`나 가상 디스플레이 사용

2. **대용량 모델**
   - 100만 노드 이상: 느려질 수 있음
   - 해결: Part별로 나눠서 보기

---

## 📝 다음 단계

- [ ] Solid 면 렌더링 (채우기)
- [ ] Part별 랜덤 색상
- [ ] 요소 선택 (picking)
- [ ] 스크린샷 저장
- [ ] 등고선 표시 (결과 가시화)

---

**Model Viewer로 K-file을 3D로 시각화하세요!** 🎨
