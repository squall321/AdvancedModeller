# 6-View Feature - CAE 표준 뷰

**Date**: 2025-12-08

---

## 🎯 개요

**CAE 표준 6면 뷰**를 Model Viewer에 추가했습니다.

### 핵심 기능

1. **7가지 프리셋 뷰** - Front/Back/Left/Right/Top/Bottom/Isometric
2. **원클릭 뷰 전환** - 버튼 클릭만으로 즉시 뷰 변경
3. **Orthographic Views** - 정투영 뷰 (Elevation 0° or ±90°)
4. **Isometric View** - 기본 3D 뷰 복귀

---

## 📊 뷰 프리셋 정의

### Orthographic Views (정투영)

| 뷰 | Elevation | Azimuth | 설명 |
|-------|-----------|---------|------|
| **Front** | 0° | 90° | +Y 방향에서 XZ 평면 보기 |
| **Back** | 0° | -90° | -Y 방향에서 보기 |
| **Left** | 0° | 180° | -X 방향에서 YZ 평면 보기 |
| **Right** | 0° | 0° | +X 방향에서 보기 |
| **Top** | 90° | 0° | +Z 방향에서 XY 평면 보기 |
| **Bottom** | -90° | 0° | -Z 방향에서 보기 |

### Isometric View (등각 투영)

| 뷰 | Elevation | Azimuth | 설명 |
|-------|-----------|---------|------|
| **Isometric** | 30° | 45° | 기본 3D 뷰 (대각선) |

---

## 🎨 UI 구성

### 버튼 레이아웃

```
[뷰 리셋] [뷰:] [F] [B] [L] [R] [T] [Bo] [Iso] [FPS: 60]
```

### 버튼 상세

- **F** - Front view
- **B** - Back view
- **L** - Left view
- **R** - Right view
- **T** - Top view
- **Bo** - Bottom view
- **Iso** - Isometric view

각 버튼에는 툴팁이 있어 마우스 오버 시 전체 이름 표시.

---

## 🏗️ 구현 세부사항

### 1. Camera 클래스 (camera.py)

7가지 뷰 프리셋 메서드 추가:

```python
class Camera:
    # ... existing methods ...

    def view_front(self):
        """Front view (+Y direction, XZ plane)"""
        self.elevation = 0.0
        self.azimuth = 90.0

    def view_back(self):
        """Back view (-Y direction)"""
        self.elevation = 0.0
        self.azimuth = -90.0

    def view_left(self):
        """Left view (-X direction, YZ plane)"""
        self.elevation = 0.0
        self.azimuth = 180.0

    def view_right(self):
        """Right view (+X direction)"""
        self.elevation = 0.0
        self.azimuth = 0.0

    def view_top(self):
        """Top view (+Z direction, XY plane)"""
        self.elevation = 90.0
        self.azimuth = 0.0

    def view_bottom(self):
        """Bottom view (-Z direction)"""
        self.elevation = -90.0
        self.azimuth = 0.0

    def view_isometric(self):
        """Isometric view (default 3D perspective)"""
        self.elevation = 30.0
        self.azimuth = 45.0
```

### 2. GLWidget 클래스 (gl_widget.py)

Camera 메서드를 래핑하여 `update()` 호출:

```python
def view_front(self):
    """Front view"""
    self._camera.view_front()
    self.update()

def view_back(self):
    """Back view"""
    self._camera.view_back()
    self.update()

# ... (나머지 뷰들도 동일 패턴)
```

### 3. Module UI (module.py)

컴팩트한 버튼 UI 추가:

```python
# 6-View buttons
view_buttons = [
    ("F", "Front", self._gl_widget.view_front),
    ("B", "Back", self._gl_widget.view_back),
    ("L", "Left", self._gl_widget.view_left),
    ("R", "Right", self._gl_widget.view_right),
    ("T", "Top", self._gl_widget.view_top),
    ("Bo", "Bottom", self._gl_widget.view_bottom),
    ("Iso", "Isometric", self._gl_widget.view_isometric),
]

for text, tooltip, callback in view_buttons:
    btn = QPushButton(text)
    btn.setToolTip(f"{tooltip} view")
    btn.setFixedWidth(32 if len(text) <= 1 else 40)
    btn.clicked.connect(callback)
    options_layout.addWidget(btn)
```

---

## 🎮 사용 방법

### GUI에서

1. Model Viewer 모듈 열기
2. K-file 로드
3. 상단 뷰 버튼 클릭:
   - **F**: Front view
   - **B**: Back view
   - **L**: Left view
   - **R**: Right view
   - **T**: Top view
   - **Bo**: Bottom view
   - **Iso**: Isometric view (기본 뷰로 복귀)

### 프로그래밍 방식

```python
from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget

gl_widget = ModelGLWidget()

# 뷰 변경
gl_widget.view_front()     # Front
gl_widget.view_top()       # Top
gl_widget.view_isometric() # Isometric
```

### Camera 직접 사용

```python
from gui.modules.model_viewer.core.camera import Camera

camera = Camera()

# 뷰 프리셋 적용
camera.view_front()
camera.view_top()

# 카메라 행렬 얻기
view_matrix = camera.get_view_matrix()
proj_matrix = camera.get_projection_matrix(aspect=16/9)
```

---

## 📈 좌표계 규칙

### LS-DYNA / CAE 좌표계

```
       +Z (Up)
        |
        |
        +---- +X (Right)
       /
      /
    +Y (Front)
```

### 뷰 방향 정의

- **Front**: +Y 방향에서 보기 (XZ 평면)
- **Right**: +X 방향에서 보기 (YZ 평면)
- **Top**: +Z 방향에서 보기 (XY 평면)

---

## ✅ 테스트 결과

### Camera Preset Test (test_6view.py)

```bash
$ ./test_6view.py

================================================================================
  6-View Preset Test
================================================================================

Testing camera view presets:

  Front        → Elevation:    0.0°, Azimuth:   90.0°
  Back         → Elevation:    0.0°, Azimuth:  -90.0°
  Left         → Elevation:    0.0°, Azimuth:  180.0°
  Right        → Elevation:    0.0°, Azimuth:    0.0°
  Top          → Elevation:   90.0°, Azimuth:    0.0°
  Bottom       → Elevation:  -90.0°, Azimuth:    0.0°
  Isometric    → Elevation:   30.0°, Azimuth:   45.0°

================================================================================
  ✓ All 6-view presets working!
================================================================================
```

### GUI 테스트

1. ✅ 모든 뷰 버튼 정상 동작
2. ✅ 버튼 클릭 시 즉시 뷰 전환
3. ✅ 툴팁 정상 표시
4. ✅ Isometric 버튼으로 기본 뷰 복귀

---

## 🔧 기술적 특징

### 1. Arcball 카메라 시스템

- **Elevation**: 위/아래 각도 (-90° ~ 90°)
- **Azimuth**: 좌/우 각도 (0° ~ 360°)
- **Distance**: 타겟으로부터의 거리 (줌)
- **Target**: 주시점 (모델 중심)

### 2. 구면 좌표 → 카르테시안 변환

```python
elev_rad = np.radians(self.elevation)
azim_rad = np.radians(self.azimuth)

x = self.distance * np.cos(elev_rad) * np.cos(azim_rad)
y = self.distance * np.cos(elev_rad) * np.sin(azim_rad)
z = self.distance * np.sin(elev_rad)

eye = self.target + np.array([x, y, z])
```

### 3. LookAt 행렬

- Forward: `target - eye` 정규화
- Right: `cross(forward, up)` 정규화
- Up: `cross(right, forward)`

---

## 🎯 CAE 워크플로우

### 전형적인 사용 시나리오

1. **모델 로드**
   - K-file 불러오기
   - 자동으로 Isometric 뷰

2. **뷰 검토**
   - **F** (Front): 전면 형상 확인
   - **T** (Top): 평면도 확인
   - **R** (Right): 측면 확인

3. **상세 검토**
   - 마우스 드래그로 회전
   - **Iso** 버튼으로 기본 뷰 복귀

4. **DOE 결과 비교**
   - 여러 Part 조합 보기
   - 6-View로 빠르게 각도 전환

---

## 🔮 향후 개선사항

### 1. Orthographic Projection

현재: 모든 뷰가 Perspective projection 사용
향후: Top/Front/Right는 Orthographic projection 옵션

```python
def get_orthographic_matrix(self, width, height):
    """정투영 행렬 (CAD/CAE 스타일)"""
    # ...
```

### 2. 뷰 애니메이션

버튼 클릭 시 부드럽게 뷰 전환:

```python
def animate_to_view(self, target_elev, target_azim, duration=0.3):
    """뷰 전환 애니메이션"""
    # Interpolate between current and target
```

### 3. Custom View 저장

사용자가 현재 뷰를 저장하고 복원:

```python
def save_custom_view(self, name: str):
    """현재 뷰 저장"""
    self._custom_views[name] = (self.elevation, self.azimuth, self.distance)

def load_custom_view(self, name: str):
    """저장된 뷰 불러오기"""
    elev, azim, dist = self._custom_views[name]
    # ...
```

### 4. 뷰 북마크

자주 쓰는 뷰를 북마크로 저장.

---

## 📝 파일 변경사항

### 수정된 파일

1. **gui/modules/model_viewer/core/camera.py**
   - 7가지 뷰 프리셋 메서드 추가

2. **gui/modules/model_viewer/widgets/gl_widget.py**
   - Camera 프리셋 래퍼 메서드 추가

3. **gui/modules/model_viewer/module.py**
   - 7개 뷰 버튼 UI 추가

### 새 파일

- **test_6view.py** - 6-view 기능 테스트

---

## 🎉 결론

### 달성한 목표

✅ **CAE 표준 6-View** - Front/Back/Left/Right/Top/Bottom
✅ **Isometric 기본 뷰** - 3D 대각선 뷰
✅ **원클릭 전환** - 버튼 하나로 즉시 뷰 변경
✅ **컴팩트 UI** - 공간 효율적인 버튼 배치

### 사용자 편의성

| 기능 | Before | After |
|------|--------|-------|
| 뷰 전환 | 마우스 드래그 (느림) | 버튼 클릭 (즉시) |
| 정확한 뷰 | 수동 조정 필요 | 프리셋으로 정확 |
| 워크플로우 | 비효율적 | CAE 표준 워크플로우 |

**CAE 작업에 최적화된 직관적인 뷰 컨트롤 완성!** 🎯
