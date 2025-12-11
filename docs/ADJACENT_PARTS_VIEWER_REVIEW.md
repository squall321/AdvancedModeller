# Adjacent Parts Viewer - 계획서 리뷰 및 보강 사항

## 📋 현재 계획서 분석

### ✅ 잘 설계된 부분

1. **명확한 알고리즘 단계**
   - Bounding Box → Spatial Index → Projection → Ray Tracing
   - 각 단계별 역할이 명확

2. **성능 최적화 고려**
   - Octree 공간 인덱싱
   - Convex Hull 외곽선
   - 결과 캐싱
   - 병렬 처리

3. **완전한 UI 설계**
   - 3-패널 레이아웃
   - 직관적인 컨트롤

---

## ⚠️ 보강이 필요한 부분

### 1. **"마주보는" 조건의 모호함** ⭐ 중요

#### 문제점
현재 계획에서는 단순히 "Ray가 교차하는 Part"를 검출합니다.
하지만 실제로 **마주보는지** 여부는 더 복잡합니다:

```
Case 1: 실제로 마주봄 ✓
Part A ──────→
              ←────── Part B

Case 2: Ray는 교차하지만 안 마주봄 ✗
Part A ──────→
    Part B (옆에 있음, 각도가 다름)

Case 3: 부분적으로 마주봄 ?
Part A (큰 평면)
    Part B (작은 평면, 일부만 겹침)
```

#### 해결 방안

**Option A: Surface Normal 체크 (추천)**
```python
def _check_facing(self, source_part, target_part, plane, ray_dir):
    """
    실제로 마주보는지 체크

    조건:
    1. Ray 교차 ✓
    2. Source의 Normal과 Target의 Normal이 반대 방향
    """
    # Source part의 평면 normal (평균)
    source_normal = self._compute_average_normal(source_part, plane)

    # Target part의 평면 normal (평균)
    target_normal = self._compute_average_normal(target_part, plane)

    # Dot product < 0 이면 반대 방향 (마주봄)
    dot = np.dot(source_normal, target_normal)

    return dot < -0.5  # 임계값 조정 가능
```

**추가 구현 필요**:
```python
class SurfaceAnalyzer:
    """Surface normal 분석"""

    def compute_part_normal(self, part_id: int, plane: str):
        """Part의 평균 normal 계산"""
        elements = self._get_part_elements(part_id)

        normals = []
        for elem in elements:
            # Triangle normal 계산
            normal = self._compute_triangle_normal(elem)
            normals.append(normal)

        # 평균 normal
        avg_normal = np.mean(normals, axis=0)
        return avg_normal / np.linalg.norm(avg_normal)
```

---

### 2. **Convex Hull의 한계** ⭐ 중요

#### 문제점
Convex Hull은 **볼록 껍질**만 추출합니다.
복잡한 형상(오목한 부분)은 무시됩니다:

```
실제 형상:    Convex Hull:
┌─┐           ┌───────┐
│ │           │       │
│ ├──┐        │       │
│ │  │   →    │       │
│ └──┘        │       │
└─────┘       └───────┘
```

#### 해결 방안

**Option A: Alpha Shape (추천)**
```python
from scipy.spatial import Delaunay
import alphashape

def extract_outline_alpha(self, part_id, plane, alpha=0.1):
    """
    Alpha shape으로 실제 외곽선 추출

    장점: 오목한 부분도 정확히 추출
    단점: 약간 느림 (하지만 캐싱으로 해결)
    """
    projected = self._project_nodes(part_id, plane)

    # Alpha shape
    alpha_shape = alphashape.alphashape(projected, alpha)

    # 외곽선 점 추출
    outline = alpha_shape.exterior.coords

    return np.array(outline)
```

**Option B: Hybrid 방식**
```python
def extract_outline_hybrid(self, part_id, plane):
    """
    빠른 응답: Convex Hull
    정확한 결과: Alpha Shape (백그라운드)
    """
    # Level 1: Convex Hull (즉시)
    convex = self._convex_hull(part_id, plane)
    yield convex  # 즉시 반환

    # Level 2: Alpha Shape (정밀)
    alpha = self._alpha_shape(part_id, plane)
    yield alpha  # 업데이트
```

---

### 3. **Ray 밀도 자동 조정 누락**

#### 문제점
현재는 고정된 Ray 밀도 (5 rays/point).
Part 크기에 따라 부족하거나 과도할 수 있음.

#### 해결 방안

```python
class AdaptiveRayDensity:
    """Part 크기에 따른 Ray 밀도 자동 조정"""

    def compute_ray_density(self, part_id, plane):
        """
        Part의 투영 면적에 비례하여 Ray 개수 결정
        """
        outline = self._get_outline(part_id, plane)

        # 2D 면적 계산
        area = self._compute_polygon_area(outline)

        # 면적에 비례한 Ray 개수
        # 1 unit² 당 1개 ray
        num_rays = max(10, int(area * 0.1))  # 최소 10개

        return num_rays

    def distribute_rays(self, outline, num_rays):
        """외곽선에 균등 분포"""
        # 외곽선 길이 계산
        perimeter = self._compute_perimeter(outline)

        # 균등 간격
        spacing = perimeter / num_rays

        # 외곽선을 따라 점 샘플링
        ray_points = self._sample_along_perimeter(outline, spacing)

        return ray_points
```

---

### 4. **Edge Case 처리 부족**

#### 추가 필요한 케이스

```python
class EdgeCaseHandler:
    """예외 상황 처리"""

    def handle_thin_parts(self, part_id):
        """얇은 Part (Shell) 특수 처리"""
        thickness = self._estimate_part_thickness(part_id)

        if thickness < 0.1:  # 매우 얇음
            # Ray 양방향 모두 검사
            return True
        return False

    def handle_overlapping_parts(self, source, target):
        """겹치는 Part 처리"""
        # Bounding box overlap 체크
        if self._bboxes_overlap(source, target):
            # 실제 요소 간 거리 계산 (정밀)
            return self._compute_mesh_distance(source, target)
        return float('inf')

    def handle_tilted_parts(self, part_id, plane):
        """경사진 Part 처리"""
        normal = self._compute_part_normal(part_id)
        plane_normal = self._get_plane_normal(plane)

        angle = np.arccos(np.dot(normal, plane_normal))

        if angle > np.pi/4:  # 45도 이상 경사
            # Warning: 결과가 부정확할 수 있음
            return True
        return False
```

---

### 5. **성능 프로파일링 전략 부족**

#### 추가 필요

```python
class PerformanceProfiler:
    """성능 병목 지점 측정"""

    def profile_search(self, part_id, plane, thickness):
        """각 단계별 시간 측정"""
        timings = {}

        # 1. Bounding box
        t0 = time.time()
        bbox = self._get_bbox(part_id)
        timings['bbox'] = time.time() - t0

        # 2. Projection
        t0 = time.time()
        outline = self._project(part_id, plane)
        timings['projection'] = time.time() - t0

        # 3. Spatial query
        t0 = time.time()
        candidates = self._spatial_query(bbox, thickness)
        timings['spatial_query'] = time.time() - t0

        # 4. Ray casting
        t0 = time.time()
        hits = self._ray_cast(outline, candidates)
        timings['ray_casting'] = time.time() - t0

        # 5. Total
        timings['total'] = sum(timings.values())

        return timings

    def suggest_optimization(self, timings):
        """병목 지점 제안"""
        bottleneck = max(timings.items(), key=lambda x: x[1])

        suggestions = {
            'projection': "Alpha shape 대신 Convex hull 사용",
            'spatial_query': "Octree 깊이 조정",
            'ray_casting': "병렬 처리 증가",
        }

        return suggestions.get(bottleneck[0])
```

---

### 6. **시각화 피드백 강화**

#### 현재 부족한 부분
- Ray 경로 표시 없음
- 검출 실패 이유 불명확

#### 추가 기능

```python
class VisualizationHelper:
    """디버깅 및 사용자 피드백"""

    def visualize_rays(self, part_id, plane, thickness):
        """Ray 경로를 3D로 시각화"""
        outline = self._get_outline(part_id, plane)

        ray_lines = []
        for point in outline:
            # Ray 시작/끝 점
            start = self._restore_3d(point, plane)
            end = start + direction * thickness_max

            ray_lines.append((start, end))

        return ray_lines  # 3D viewer에 표시

    def explain_no_hits(self, part_id, plane, thickness):
        """검출 실패 이유 분석"""
        reasons = []

        # 1. Thickness 범위 부족?
        nearest = self._find_nearest_part(part_id, plane)
        if nearest:
            dist = self._compute_distance(part_id, nearest)
            if dist > thickness[1]:
                reasons.append(
                    f"Nearest part at {dist:.1f}, "
                    f"increase max thickness (current: {thickness[1]})"
                )

        # 2. 방향이 잘못됨?
        normal = self._compute_part_normal(part_id)
        plane_normal = self._get_plane_normal(plane)
        angle = np.arccos(np.dot(normal, plane_normal))

        if angle > np.pi/4:
            reasons.append(
                f"Part is tilted {np.degrees(angle):.1f}°, "
                f"try different plane"
            )

        return reasons
```

---

### 7. **Model Viewer 연동 상세화 필요**

#### 추가 명세

```python
class ModelViewerIntegration:
    """Model Viewer와의 통합"""

    def highlight_adjacent_parts(self, source_id, adjacent_ids):
        """
        3D Viewer에 결과 표시

        - Source: 밝은 색 (노란색)
        - Adjacent: Part별 색상 유지
        - Others: 반투명 또는 숨김
        """
        self.model_viewer.clear_highlights()

        # Source part 하이라이트
        self.model_viewer.highlight_part(
            source_id,
            color=(1.0, 1.0, 0.0),  # 노란색
            opacity=1.0
        )

        # Adjacent parts 표시
        for pid in adjacent_ids:
            self.model_viewer.set_part_visible(pid, True)
            self.model_viewer.set_part_opacity(pid, 1.0)

        # 나머지 숨김
        other_parts = set(all_parts) - {source_id} - adjacent_ids
        for pid in other_parts:
            self.model_viewer.set_part_visible(pid, False)

        # 카메라 자동 조정
        self.model_viewer.fit_to_parts([source_id] + list(adjacent_ids))
```

---

## 📝 보강된 구현 우선순위

### Phase 1: 핵심 알고리즘 (3시간) ← 1시간 추가
1. ✅ Bounding Box 계산
2. ✅ Spatial Index (Octree)
3. ✅ Projection Engine (Convex Hull + Alpha Shape)
4. ✅ Ray Tracer (기본)
5. **🆕 Surface Normal 체크 (마주보기 검증)**
6. **🆕 Adaptive Ray Density**

### Phase 2: UI 통합 (1.5시간) ← 0.5시간 추가
7. ✅ Plane Selector
8. ✅ Thickness Slider
9. ✅ Adjacent Parts List
10. ✅ 3D Viewer 연동
11. **🆕 Ray 경로 시각화 (디버깅)**
12. **🆕 실패 이유 표시**

### Phase 3: 최적화 & 테스트 (1.5시간) ← 0.5시간 추가
13. ✅ 결과 캐싱
14. ✅ Progressive Refinement
15. ✅ 병렬 처리
16. **🆕 성능 프로파일링**
17. **🆕 Edge Case 테스트**

**총 예상 시간: 6시간** (4시간 → 6시간)

---

## 🎯 Critical Path (필수 구현)

### 최소 기능 (4시간)
1. Bounding Box + Octree
2. Convex Hull Projection
3. Ray-AABB Tracing
4. 기본 UI
5. Model Viewer 연동

### 권장 기능 (+2시간)
6. **Surface Normal 체크** ⭐ 중요
7. Alpha Shape Outline
8. Adaptive Ray Density
9. 성능 프로파일링

### 향후 개선 (선택)
10. Ray 경로 시각화
11. 실패 이유 분석
12. Edge Case 고급 처리

---

## 📊 개선된 API

```python
class AdjacentPartsDetector:
    """이웃 Part 검출기 (개선)"""

    def find_adjacent(
        self,
        source_part_id: int,
        plane: str,
        thickness_min: float,
        thickness_max: float,
        check_facing: bool = True,  # 🆕 마주보기 체크
        outline_method: str = 'convex',  # 🆕 'convex' or 'alpha'
        ray_density: str = 'auto',  # 🆕 'auto', 'low', 'medium', 'high'
        visualize: bool = False,  # 🆕 Ray 경로 시각화
    ) -> Dict[str, Any]:  # 🆕 더 많은 정보 반환
        """
        Returns:
            {
                'adjacent_parts': Set[int],
                'timings': Dict[str, float],
                'ray_count': int,
                'hit_count': int,
                'visualization': Optional[RayVisualization]
            }
        """
```

---

## ✨ 최종 권장사항

### 🚦 구현 전략

**Phase A: MVP (4시간)** - 즉시 동작하는 버전
- Convex Hull
- Ray-AABB
- 기본 UI

**Phase B: Production (+ 2시간)** - 실전 사용 가능
- Surface Normal 체크 ⭐
- Adaptive Ray Density
- 성능 최적화

**Phase C: Polish (+ 1시간)** - 완벽한 마무리
- 시각화 디버깅
- Edge Case 처리

---

## 📌 핵심 추가 사항 요약

1. **Surface Normal 체크** - 실제 마주보는지 검증 ⭐⭐⭐
2. **Alpha Shape** - 복잡한 형상 처리 ⭐⭐
3. **Adaptive Ray Density** - 효율성 ⭐⭐
4. **성능 프로파일링** - 병목 지점 식별 ⭐⭐
5. **시각화 피드백** - 사용자 경험 ⭐
6. **Edge Case 처리** - 안정성 ⭐

---

**이제 구현 시작할까요?** 🚀

추천: **Phase A (MVP 4시간)** 먼저 구현 → 테스트 → Phase B 진행
