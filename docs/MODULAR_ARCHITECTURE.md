# Model Viewer - 모듈화 아키텍처

**Date**: 2025-12-08

---

## 🎯 개요

Model Viewer는 **완전히 모듈화**되어 있어 각 컴포넌트를 독립적으로 사용할 수 있습니다.

### 핵심 설계 원칙

1. **관심사의 분리** - 데이터, 렌더링, UI가 독립적
2. **의존성 주입** - 각 모듈이 필요한 것만 받음
3. **플러그인 아키텍처** - 백엔드 교체 가능
4. **재사용성** - 다른 애플리케이션에 쉽게 통합

---

## 🏗️ 아키텍처

### 계층 구조

```
┌─────────────────────────────────────────────┐
│  module.py (Full UI Integration)           │ ← 전체 패키지
│  - File loader                              │
│  - Part tree                                │
│  - Control panel                            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  widgets/gl_widget.py (OpenGL Viewer)       │ ← 순수 뷰어
│  - Camera control                           │
│  - Mouse interaction                        │
│  - Backend management                       │
└──────────────────┬──────────────────────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
┌─────▼─────┐ ┌───▼────┐ ┌─────▼──────┐
│ Backends  │ │ Camera │ │ MeshData   │ ← 독립 모듈
│ - Legacy  │ │        │ │            │
│ - VBO     │ │        │ │            │
└───────────┘ └────────┘ └────────────┘
```

### 디렉토리 구조

```
gui/modules/model_viewer/
├── core/                    # 핵심 로직 (UI 독립적)
│   ├── mesh_data.py        # 메쉬 데이터 구조
│   │   └── MeshData        # K-file → 3D 메쉬 변환
│   └── camera.py           # 카메라 컨트롤
│       └── Camera          # Arcball 카메라, 6-view
│
├── backends/                # 렌더링 백엔드 (교체 가능)
│   ├── base_renderer.py    # 공통 인터페이스
│   ├── legacy_renderer.py  # Legacy OpenGL
│   └── vbo_renderer.py     # VBO GPU 가속
│
├── widgets/                 # 재사용 가능한 위젯
│   ├── gl_widget.py        # OpenGL 뷰어 위젯 ⭐
│   │   └── ModelGLWidget   # 독립적으로 사용 가능!
│   └── part_tree.py        # Part 트리 위젯
│
└── module.py                # 통합 UI 모듈
    └── ModelViewerModule   # 전체 기능 패키지
```

---

## 🔌 사용 시나리오

### 1. 전체 UI 모듈 사용 (기본)

```python
from gui.modules.model_viewer.module import ModelViewerModule
from gui.app_context import AppContext

ctx = AppContext()
viewer_module = ModelViewerModule(ctx)
viewer_module.show()
```

**포함된 기능:**
- ✅ 파일 로드 UI
- ✅ Part 트리 (선택/해제)
- ✅ 렌더링 옵션
- ✅ 6-View 버튼
- ✅ FPS 표시

---

### 2. 순수 OpenGL 뷰어만 사용 ⭐

```python
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget
from gui.modules.model_viewer.core.mesh_data import MeshData

# 뷰어만 생성 (파일 로드/Part 트리 없음)
viewer = ModelGLWidget(backend='vbo')
viewer.resize(800, 600)

# 메쉬 데이터는 외부에서 주입
mesh = MeshData.from_parsed_model(model)
viewer.set_mesh(mesh)

# 특정 Part만 표시
viewer.set_visible_parts({1, 2, 3})

viewer.show()
```

**포함된 기능:**
- ✅ 3D 렌더링 (Solid, Edges, Wireframe, Nodes)
- ✅ 마우스 인터랙션 (회전, 팬, 줌)
- ✅ 6-View 프리셋 메서드
- ✅ 백엔드 전환
- ❌ 파일 로드 UI (외부에서 처리)
- ❌ Part 트리 (외부에서 처리)

---

### 3. 다른 애플리케이션에 임베드

```python
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # 메인 레이아웃
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        # 3D 뷰어 임베드
        self.viewer = ModelGLWidget(backend='vbo')
        layout.addWidget(self.viewer)

        # 나머지 커스텀 UI
        # ...
```

**사용 사례:**
- DOE 결과 비교 툴
- 최적화 결과 시각화
- 실시간 시뮬레이션 모니터
- CAE 후처리 통합

---

### 4. 렌더러만 사용 (OpenGL 컨텍스트 없이)

```python
from gui.modules.model_viewer.backends import VBORenderer
from gui.modules.model_viewer.core.camera import Camera
from gui.modules.model_viewer.core.mesh_data import MeshData

# 메쉬 로드
mesh = MeshData.from_parsed_model(model)

# 렌더러 생성
renderer = VBORenderer()
renderer.set_mesh(mesh)
renderer.set_visible_parts({1, 2, 3})

# 카메라 설정
camera = Camera()
camera.fit_to_bounds(mesh.bounds[0], mesh.bounds[1])
renderer.set_camera(camera)

# 렌더링 옵션
renderer.set_show_solid(True)
renderer.set_show_edges(True)

# 카메라 행렬 얻기 (커스텀 렌더링에 사용)
view_matrix = camera.get_view_matrix()
proj_matrix = camera.get_projection_matrix(aspect=16/9)
```

**사용 사례:**
- 오프스크린 렌더링
- 이미지 생성 (배치 처리)
- 커스텀 OpenGL 파이프라인
- 멀티뷰 렌더링

---

### 5. 메쉬 데이터만 사용 (렌더링 없이)

```python
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.app_context import AppContext

# K-file 로드
ctx = AppContext()
ctx.load_k_file("model.k")

# MeshData 생성
mesh = MeshData.from_parsed_model(ctx.model)

# 데이터 분석
print(f"Nodes: {len(mesh.nodes)}")
print(f"Elements: {len(mesh.elements)}")
print(f"Bounding box: {mesh.bounds}")

# Part별 통계
for pid in mesh.part_elements.keys():
    elem_count = len(mesh.part_elements[pid])
    part_name = mesh.part_names[pid]
    print(f"Part {pid}: {elem_count} elements - {part_name}")
```

**사용 사례:**
- 메쉬 품질 검사
- 통계 분석
- 데이터 변환
- 메쉬 최적화

---

## 📊 의존성 그래프

```
module.py
  ├── widgets/gl_widget.py
  │     ├── backends/vbo_renderer.py
  │     │     ├── backends/base_renderer.py
  │     │     └── core/mesh_data.py
  │     ├── core/camera.py
  │     └── core/mesh_data.py
  └── widgets/part_tree.py
```

### 역방향 의존성 없음!

- `core/` 모듈은 다른 것에 의존하지 않음 ✅
- `backends/`는 `core/`에만 의존 ✅
- `widgets/`는 `core/`, `backends/`에만 의존 ✅
- `module.py`는 전체를 조합 ✅

---

## 🎨 실제 예제

### 예제 1: DOE 결과 비교 툴

```python
# example_embedded_viewer.py 참고

class DOEVisualizerApp(QMainWindow):
    """DOE 케이스별 Part 구성을 3D로 비교"""

    def __init__(self):
        # 좌측: 케이스 리스트
        # 우측: 3D 뷰어 (임베드)
        self.viewer = ModelGLWidget(backend='vbo')

    def on_case_selected(self, case_name):
        # 케이스별 Part 구성 표시
        part_ids = self.doe_cases[case_name]
        self.viewer.set_visible_parts(part_ids)
        self.viewer.reset_view()
```

**실행:**
```bash
python3 example_embedded_viewer.py
```

---

### 예제 2: 최소 뷰어 (파일 로드 제외)

```python
# example_standalone_viewer.py 참고

class SimpleViewerWindow(QMainWindow):
    """최소한의 뷰어 - 파일 로드 UI 없음"""

    def __init__(self):
        # 순수 뷰어만
        self.viewer = ModelGLWidget(backend='vbo')

        # 뷰 버튼만 추가
        for name, callback in [
            ("Front", self.viewer.view_front),
            ("Top", self.viewer.view_top),
            ("Iso", self.viewer.view_isometric),
        ]:
            btn = QPushButton(name)
            btn.clicked.connect(callback)

    def set_mesh_data(self, mesh, visible_parts=None):
        """외부에서 메쉬 주입"""
        self.viewer.set_mesh(mesh)
        self.viewer.set_visible_parts(visible_parts or set(mesh.part_elements.keys()))
```

---

### 예제 3: 렌더러 직접 사용

```python
# example_custom_renderer.py 참고

# 1. 메쉬 로드
mesh = MeshData.from_parsed_model(model)

# 2. 렌더러 생성
renderer = VBORenderer()

# 3. 카메라 생성
camera = Camera()
camera.fit_to_bounds(mesh.bounds[0], mesh.bounds[1])

# 4. 렌더러에 설정
renderer.set_mesh(mesh)
renderer.set_camera(camera)
renderer.set_visible_parts({1, 2, 3})

# 5. 렌더링 옵션
renderer.set_show_solid(True)
renderer.set_show_edges(True)

# 6. 뷰 변경
camera.view_front()
camera.view_top()
```

---

## 🔧 API 레퍼런스

### ModelGLWidget (독립 뷰어)

```python
class ModelGLWidget(QOpenGLWidget):
    """순수 OpenGL 뷰어 위젯 (독립적으로 사용 가능)"""

    def __init__(self, backend='legacy'):
        """
        Args:
            backend: 'legacy', 'vbo', 'pyvista'
        """

    # 데이터 설정
    def set_mesh(self, mesh: MeshData):
        """메쉬 설정"""

    def set_visible_parts(self, part_ids: Set[int]):
        """표시할 Part 설정"""

    # 렌더링 옵션
    def set_show_solid(self, show: bool):
        """Solid 표시 ON/OFF"""

    def set_show_edges(self, show: bool):
        """외곽 엣지 표시 ON/OFF"""

    def set_show_wireframe(self, show: bool):
        """와이어프레임 표시 ON/OFF"""

    def set_show_nodes(self, show: bool):
        """노드 표시 ON/OFF"""

    # 뷰 컨트롤
    def reset_view(self):
        """뷰 리셋 (모델에 맞춤)"""

    def view_front(self):
        """Front view"""

    def view_back(self):
        """Back view"""

    def view_left(self):
        """Left view"""

    def view_right(self):
        """Right view"""

    def view_top(self):
        """Top view"""

    def view_bottom(self):
        """Bottom view"""

    def view_isometric(self):
        """Isometric view"""

    # 백엔드 관리
    def set_backend(self, backend: str):
        """백엔드 전환 ('legacy' or 'vbo')"""

    def get_backend_name(self) -> str:
        """현재 백엔드 이름"""
```

---

### Camera (독립 카메라)

```python
class Camera:
    """Arcball 카메라 (독립적)"""

    def __init__(self):
        """기본 카메라 생성"""

    # 이동/회전/줌
    def rotate(self, delta_azim: float, delta_elev: float):
        """회전 (도)"""

    def zoom(self, factor: float):
        """줌 (> 1: 가까이, < 1: 멀리)"""

    def pan(self, delta_x: float, delta_y: float):
        """팬 (타겟 이동)"""

    # 뷰 프리셋
    def view_front(self):
        """Front view (Elev=0°, Azim=90°)"""

    def view_top(self):
        """Top view (Elev=90°, Azim=0°)"""

    def view_isometric(self):
        """Isometric view (Elev=30°, Azim=45°)"""

    # 행렬
    def get_view_matrix(self) -> np.ndarray:
        """뷰 행렬 (4x4)"""

    def get_projection_matrix(self, aspect: float) -> np.ndarray:
        """투영 행렬 (4x4)"""

    # 자동 조정
    def fit_to_bounds(self, min_bounds: np.ndarray, max_bounds: np.ndarray):
        """모델에 맞춤"""
```

---

### MeshData (독립 메쉬)

```python
class MeshData:
    """메쉬 데이터 (렌더링 독립적)"""

    @staticmethod
    def from_parsed_model(model) -> 'MeshData':
        """K-file 모델로부터 생성"""

    # 데이터
    nodes: np.ndarray              # (N, 3) 노드 좌표
    elements: np.ndarray           # (M, 8) 요소 노드 인덱스
    part_elements: Dict[int, List] # {part_id: [elem_idx, ...]}
    part_names: Dict[int, str]     # {part_id: "name"}
    bounds: Tuple[np.ndarray, np.ndarray]  # (min, max)

    # 메서드
    def extract_exterior_faces(self) -> Dict:
        """외곽면 추출"""
```

---

### BaseRenderer (백엔드 인터페이스)

```python
class BaseRenderer(ABC):
    """렌더러 공통 인터페이스"""

    @abstractmethod
    def initialize(self):
        """OpenGL 초기화"""

    @abstractmethod
    def render(self, width: int, height: int):
        """렌더링"""

    def set_mesh(self, mesh: MeshData):
        """메쉬 설정"""

    def set_camera(self, camera: Camera):
        """카메라 설정"""

    def set_visible_parts(self, part_ids: Set[int]):
        """표시할 Part 설정"""
```

---

## ✅ 모듈화 체크리스트

- [x] **관심사 분리** - 데이터/렌더링/UI 독립적
- [x] **의존성 주입** - 각 모듈이 필요한 것만 받음
- [x] **인터페이스 기반** - BaseRenderer로 백엔드 교체 가능
- [x] **독립 실행 가능** - 각 레벨에서 독립적으로 사용 가능
- [x] **재사용성** - 다른 애플리케이션에 쉽게 통합
- [x] **테스트 용이** - 각 모듈 개별 테스트 가능
- [x] **확장성** - 새 백엔드/기능 추가 용이

---

## 🎉 결론

### 완전히 모듈화된 아키텍처!

| 레벨 | 컴포넌트 | 독립성 | 사용 사례 |
|------|---------|--------|----------|
| **Level 1** | MeshData, Camera | 100% | 데이터 분석, 변환 |
| **Level 2** | Renderer (VBO/Legacy) | 95% | 오프스크린 렌더링 |
| **Level 3** | ModelGLWidget | 90% | 커스텀 뷰어 앱 |
| **Level 4** | ModelViewerModule | 0% | 통합 UI |

### 유연한 통합 방식

```
┌─────────────────────────────────────────────────┐
│  다른 애플리케이션                                │
│  ┌───────────────────────────────────────────┐  │
│  │  커스텀 UI                                 │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  ModelGLWidget (임베드)              │  │  │
│  │  │  ├── VBORenderer                     │  │  │
│  │  │  ├── Camera                          │  │  │
│  │  │  └── MeshData                        │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**완벽한 재사용성과 확장성을 갖춘 CAE 뷰어!** 🚀
