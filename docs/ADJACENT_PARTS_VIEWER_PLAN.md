# Adjacent Parts Viewer - 이웃한 파트 뷰어 설계

## 🎯 목표

**선택한 Part와 마주보는 이웃 Part들만 빠르게 추출하여 시각화**

DOE 작업 시 접촉/간섭 분석을 위해 불필요한 Part는 제거하고,
실제로 마주보는 Part들만 보여주어 깔끔한 분석 환경 제공.

---

## 📋 핵심 요구사항

### 1. 평면 선택
- **XY 평면** (Z축 방향)
- **YZ 평면** (X축 방향)
- **ZX 평면** (Y축 방향)

### 2. Part 선택
- 기준 Part 선택
- 즉시 이웃 Part 추출

### 3. Ray Tracing 기반 검색
```
1. 기준 Part의 외곽선 추출
2. 선택한 평면에 투영
3. 수직 벡터 방향으로 Ray 발사
4. 두께 범위 내 (하한~상한) Part 검색
5. 실제 마주보는 Part만 필터링
```

### 4. 최적화 목표
- **실시간 반응** (<100ms)
- **대용량 지원** (10K+ Parts)
- **정확한 검출**

---

## 🏗️ 아키텍처 설계

### 전체 구조
```
GUI Layer (UI)
    ↓
Adjacent Parts Detector (핵심 알고리즘)
    ↓
Spatial Index (공간 인덱싱)
    ↓
Mesh Data (기존)
```

### 모듈 구조
```
gui/modules/adjacent_parts_viewer/
├── core/
│   ├── ray_tracer.py          # Ray tracing 엔진
│   ├── spatial_index.py       # 공간 인덱싱 (Octree/BVH)
│   ├── projection.py          # 평면 투영
│   └── adjacency_detector.py  # 이웃 Part 검출 (메인)
│
├── widgets/
│   ├── plane_selector.py      # XY/YZ/ZX 선택
│   ├── thickness_slider.py    # 두께 범위 설정
│   └── adjacent_view.py       # 결과 3D 뷰어
│
└── module.py                  # 통합 모듈
```

---

## 🔬 핵심 알고리즘

### Step 1: Bounding Box 사전 계산
```python
class PartBounds:
    """Part별 Bounding Box 캐싱"""

    def __init__(self, mesh_data: MeshData):
        self.part_bounds = {}  # {part_id: (min, max)}

        for pid, elem_indices in mesh_data.part_elements.items():
            elements = mesh_data.elements[elem_indices]
            nodes = mesh_data.nodes[elements.flatten()]

            self.part_bounds[pid] = (
                np.min(nodes, axis=0),  # min [x, y, z]
                np.max(nodes, axis=0)   # max [x, y, z]
            )
```

**최적화**: 한 번만 계산, 메모리 캐싱

---

### Step 2: 공간 인덱싱 (Octree)
```python
class SpatialIndex:
    """공간 분할 트리 - 빠른 범위 검색"""

    def __init__(self, part_bounds: Dict):
        self.octree = self._build_octree(part_bounds)

    def query_range(self, min_point, max_point) -> Set[int]:
        """범위 내 Part ID 반환 (O(log n))"""
        return self._octree_query(min_point, max_point)
```

**효과**: O(n) → O(log n) 검색

---

### Step 3: 평면 투영 및 외곽선 추출
```python
class ProjectionEngine:
    """평면 투영 및 2D 외곽선 추출"""

    def project_to_plane(self, part_id: int, plane: str):
        """
        Args:
            part_id: Part ID
            plane: 'XY', 'YZ', 'ZX'

        Returns:
            2D 외곽선 점들 (Convex Hull)
        """
        # 1. Part의 모든 노드 가져오기
        nodes = self._get_part_nodes(part_id)

        # 2. 평면에 투영
        if plane == 'XY':
            projected = nodes[:, [0, 1]]  # x, y만
            normal_axis = 2  # z축
        elif plane == 'YZ':
            projected = nodes[:, [1, 2]]  # y, z만
            normal_axis = 0  # x축
        elif plane == 'ZX':
            projected = nodes[:, [2, 0]]  # z, x만
            normal_axis = 1  # y축

        # 3. 2D Convex Hull (외곽선)
        from scipy.spatial import ConvexHull
        hull = ConvexHull(projected)
        outline_points = projected[hull.vertices]

        return outline_points, normal_axis
```

**최적화**: Convex Hull로 외곽선만 추출

---

### Step 4: Ray Tracing
```python
class RayTracer:
    """Ray tracing 기반 이웃 검색"""

    def find_adjacent_parts(
        self,
        source_part_id: int,
        plane: str,
        thickness_min: float,
        thickness_max: float
    ) -> Set[int]:
        """
        Returns:
            이웃한 Part ID 집합
        """
        # 1. 외곽선 추출
        outline, normal_axis = self.projection.project_to_plane(
            source_part_id, plane
        )

        # 2. 외곽선 점들에서 Ray 발사
        rays_per_point = 5  # 밀도
        adjacent_parts = set()

        for point_2d in outline:
            # 3D 점으로 복원 (normal_axis 방향으로 확장)
            point_3d = self._restore_3d(point_2d, normal_axis)

            # Ray 방향 (normal 방향 양쪽)
            for direction in [1, -1]:
                ray_dir = np.zeros(3)
                ray_dir[normal_axis] = direction

                # Ray casting
                hits = self._cast_ray(
                    origin=point_3d,
                    direction=ray_dir,
                    min_dist=thickness_min,
                    max_dist=thickness_max
                )

                adjacent_parts.update(hits)

        # Source part 제거
        adjacent_parts.discard(source_part_id)

        return adjacent_parts
```

**최적화 포인트**:
1. Convex Hull로 점 개수 최소화
2. Spatial Index로 후보 Part 사전 필터링
3. Ray 밀도 조절 가능

---

### Step 5: Ray-AABB 교차 테스트 (고속)
```python
def _cast_ray(self, origin, direction, min_dist, max_dist):
    """Ray와 교차하는 Part 검색 (AABB 기반)"""

    # 1. 범위 내 후보 Part 추출 (Spatial Index)
    search_box_min = origin + direction * min_dist - margin
    search_box_max = origin + direction * max_dist + margin

    candidate_parts = self.spatial_index.query_range(
        search_box_min, search_box_max
    )

    # 2. Ray-AABB 교차 테스트 (빠름!)
    hit_parts = set()

    for pid in candidate_parts:
        aabb_min, aabb_max = self.part_bounds[pid]

        if self._ray_aabb_intersect(origin, direction, aabb_min, aabb_max):
            # 거리 체크
            hit_dist = self._compute_hit_distance(
                origin, direction, aabb_min, aabb_max
            )

            if min_dist <= hit_dist <= max_dist:
                hit_parts.add(pid)

    return hit_parts

def _ray_aabb_intersect(self, origin, direction, aabb_min, aabb_max):
    """Ray-AABB 교차 테스트 (슬랩 방식)"""
    tmin = (aabb_min - origin) / (direction + 1e-10)
    tmax = (aabb_max - origin) / (direction + 1e-10)

    t1 = np.minimum(tmin, tmax)
    t2 = np.maximum(tmin, tmax)

    tnear = np.max(t1)
    tfar = np.min(t2)

    return tnear <= tfar and tfar >= 0
```

**복잡도**: O(log n) - Spatial Index 덕분

---

## ⚡ 최적화 전략

### 1. 사전 계산 (Pre-computation)
```python
class AdjacentPartsCache:
    """이웃 Part 캐싱"""

    def __init__(self):
        self._cache = {}  # {(part_id, plane, thickness): adjacent_parts}

    def get(self, part_id, plane, thickness_range):
        key = (part_id, plane, tuple(thickness_range))
        return self._cache.get(key)

    def put(self, part_id, plane, thickness_range, adjacent_parts):
        key = (part_id, plane, tuple(thickness_range))
        self._cache[key] = adjacent_parts
```

**효과**: 동일 조건 재선택 시 즉시 반환

---

### 2. Progressive Refinement
```python
def find_adjacent_progressive(self, part_id, plane, thickness):
    """점진적 정밀도 향상"""

    # Level 1: Coarse (즉시 반응)
    candidates = self._coarse_search(part_id, plane, thickness)
    self._update_ui(candidates)  # 0.01초

    # Level 2: Medium (백그라운드)
    refined = self._medium_search(candidates, plane, thickness)
    self._update_ui(refined)  # 0.05초

    # Level 3: Fine (최종)
    final = self._fine_search(refined, plane, thickness)
    self._update_ui(final)  # 0.1초
```

**UX**: 즉시 피드백 + 점진적 정확도

---

### 3. 병렬 처리
```python
from concurrent.futures import ThreadPoolExecutor

def _cast_rays_parallel(self, outline_points, ...):
    """Ray casting 병렬화"""

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(self._cast_ray_from_point, pt, ...)
            for pt in outline_points
        ]

        results = [f.result() for f in futures]

    return set.union(*results)
```

**효과**: 4배 속도 향상 (4코어 기준)

---

## 🎨 UI 설계

### 레이아웃
```
┌─────────────────────────────────────────────────┐
│ Adjacent Parts Viewer                           │
├─────────────────────────────────────────────────┤
│ ┌────────────┬──────────────────┬──────────────┐│
│ │ Controls   │ 3D View          │ Part List    ││
│ │            │                  │              ││
│ │ Plane:     │                  │ Source:      ││
│ │ ○ XY       │   [3D Model]     │ Part 5       ││
│ │ ○ YZ       │                  │              ││
│ │ ● ZX       │                  │ Adjacent:    ││
│ │            │                  │ □ Part 3     ││
│ │ Thickness: │                  │ □ Part 7     ││
│ │ Min: 1.0   │                  │ □ Part 12    ││
│ │ Max: 10.0  │                  │ □ Part 15    ││
│ │ [─────────]│                  │ ...          ││
│ │            │                  │              ││
│ │ Ray Density│                  │ Total: 4     ││
│ │ ○ Low      │                  │              ││
│ │ ● Medium   │                  │ [Clear]      ││
│ │ ○ High     │                  │ [Export]     ││
│ └────────────┴──────────────────┴──────────────┘│
│                                                  │
│ Status: Found 4 adjacent parts in 0.05s         │
└─────────────────────────────────────────────────┘
```

---

### Widget 상세

#### 1. Plane Selector
```python
class PlaneSelector(QWidget):
    """XY/YZ/ZX 선택"""

    planeChanged = Signal(str)  # 'XY', 'YZ', 'ZX'

    def __init__(self):
        # Radio buttons
        self._xy_radio = QRadioButton("XY (Z방향)")
        self._yz_radio = QRadioButton("YZ (X방향)")
        self._zx_radio = QRadioButton("ZX (Y방향)")
```

#### 2. Thickness Range Slider
```python
class ThicknessRangeSlider(QWidget):
    """두께 범위 설정"""

    rangeChanged = Signal(float, float)  # (min, max)

    def __init__(self):
        self._min_slider = QSlider()
        self._max_slider = QSlider()
        self._min_spin = QDoubleSpinBox()
        self._max_spin = QDoubleSpinBox()
```

#### 3. Adjacent Parts List
```python
class AdjacentPartsList(QWidget):
    """검출된 이웃 Part 리스트"""

    partSelected = Signal(int)  # Part ID

    def set_adjacent_parts(self, source_id: int, adjacent_ids: Set[int]):
        """리스트 업데이트"""
        self._list.clear()

        # Source part
        self._list.addItem(f"Source: Part {source_id}")

        # Adjacent parts (체크박스)
        for pid in sorted(adjacent_ids):
            item = QListWidgetItem(f"Part {pid}")
            item.setCheckState(Qt.Checked)
            self._list.addItem(item)
```

---

## 🔄 워크플로우

### 사용자 시나리오
```
1. Part Tree에서 기준 Part 선택 (예: Part 5)
   ↓
2. Adjacent Parts Viewer 자동 활성화
   ↓
3. Plane 선택 (예: ZX)
   ↓
4. Thickness 범위 설정 (1.0 ~ 10.0)
   ↓
5. [Auto] 자동 검색 시작
   ↓ (0.05초)
6. 결과 표시: Part 3, 7, 12, 15
   ↓
7. 3D 뷰어에 해당 Part들만 렌더링
   ↓
8. 체크박스로 개별 Part ON/OFF
```

### 데이터 흐름
```
User Input
    ↓
AdjacentPartsDetector.find_adjacent()
    ↓
    ├─> Projection.project_to_plane()
    ├─> RayTracer.cast_rays()
    └─> SpatialIndex.query_range()
    ↓
Result (Set[int])
    ↓
    ├─> AdjacentPartsList (UI 업데이트)
    ├─> ModelViewer (3D 렌더링)
    └─> Cache (저장)
```

---

## 📊 성능 목표

### 타겟 성능

| 모델 크기 | Part 수 | 응답 시간 | 정확도 |
|-----------|---------|----------|--------|
| Small | 10-50 | <10ms | 100% |
| Medium | 50-500 | <50ms | 100% |
| Large | 500-5K | <100ms | 99%+ |
| Huge | 5K-50K | <500ms | 99%+ |

### 최적화 체크리스트
- [x] Bounding Box 캐싱
- [x] Spatial Index (Octree)
- [x] Convex Hull 외곽선
- [x] Ray-AABB 고속 교차
- [x] Progressive Refinement
- [x] 병렬 Ray Casting
- [x] 결과 캐싱

---

## 🔧 구현 우선순위

### Phase 1: 핵심 알고리즘 (2시간)
1. ✅ Bounding Box 계산
2. ✅ Spatial Index (Octree)
3. ✅ Projection Engine
4. ✅ Ray Tracer (기본)

### Phase 2: UI 통합 (1시간)
5. ✅ Plane Selector
6. ✅ Thickness Slider
7. ✅ Adjacent Parts List
8. ✅ 3D Viewer 연동

### Phase 3: 최적화 (1시간)
9. ✅ 결과 캐싱
10. ✅ Progressive Refinement
11. ✅ 병렬 처리
12. ✅ 성능 벤치마크

**총 예상 시간: 4시간**

---

## 🧪 테스트 케이스

### Test Case 1: 단순 Box
```
Setup:
- Part 1: Box at z=0
- Part 2: Box at z=10 (마주봄)
- Part 3: Box at x=100 (멀리)

Input:
- Source: Part 1
- Plane: XY (Z방향)
- Thickness: 5~15

Expected:
- Adjacent: {Part 2}
```

### Test Case 2: 복잡한 형상
```
Setup:
- 10개 Part, 다양한 위치
- 일부 마주봄, 일부 안 마주봄

Input:
- Source: Part 5
- Plane: YZ
- Thickness: 1~20

Expected:
- Ray tracing으로 실제 마주보는 Part만 검출
```

### Test Case 3: 성능 테스트
```
Setup:
- 1000 Parts

Metric:
- 응답 시간 < 100ms
- 정확도 > 99%
```

---

## 📝 API 설계

### 메인 API
```python
class AdjacentPartsDetector:
    """이웃 Part 검출기 (메인 클래스)"""

    def __init__(self, mesh_data: MeshData):
        self.mesh_data = mesh_data
        self.part_bounds = PartBounds(mesh_data)
        self.spatial_index = SpatialIndex(self.part_bounds)
        self.projection = ProjectionEngine(mesh_data)
        self.ray_tracer = RayTracer(
            spatial_index=self.spatial_index,
            part_bounds=self.part_bounds
        )
        self.cache = AdjacentPartsCache()

    def find_adjacent(
        self,
        source_part_id: int,
        plane: str,  # 'XY', 'YZ', 'ZX'
        thickness_min: float,
        thickness_max: float,
        ray_density: str = 'medium'  # 'low', 'medium', 'high'
    ) -> Set[int]:
        """
        이웃 Part 검색

        Returns:
            이웃한 Part ID 집합
        """
        # 캐시 확인
        cached = self.cache.get(
            source_part_id, plane, (thickness_min, thickness_max)
        )
        if cached is not None:
            return cached

        # Ray tracing
        adjacent = self.ray_tracer.find_adjacent_parts(
            source_part_id, plane, thickness_min, thickness_max, ray_density
        )

        # 캐시 저장
        self.cache.put(
            source_part_id, plane, (thickness_min, thickness_max), adjacent
        )

        return adjacent
```

---

## ✨ 기대 효과

### DOE 작업 시
1. **시각적 명확성**: 마주보는 Part만 표시 → 분석 용이
2. **빠른 반응**: <100ms → 실시간 탐색
3. **정확한 검출**: Ray tracing → 오검출 최소화

### 접촉 분석
1. Contact 정의 시 후보 Part 자동 추천
2. 간섭 체크 전처리
3. 위치 최적화 가이드

---

## 🚀 다음 단계

1. **핵심 알고리즘 구현** (2시간)
2. **UI 통합** (1시간)
3. **최적화 & 테스트** (1시간)
4. **DOE 모듈 연동** (향후)

**총 4시간으로 완성 가능!**

---

**준비 완료! 구현 시작할까요?** 🎯
