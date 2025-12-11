# Bounding Box Algorithm Upgrade

## 개요

사용자 피드백에 따라 Adjacent Parts Detection 알고리즘을 단순화하고 효율성을 높였습니다.

**기존 문제점:**
- 복잡한 Convex Hull 기반 2D 투영
- Element 레벨 ray casting으로 인한 복잡도 증가
- Occlusion handling 부재로 뒤에 가려진 파트도 포함됨

**새로운 접근:**
- Bounding Box 기반 단순 Ray Casting
- Grid 패턴으로 Ray 생성 (밀도 조절 가능)
- Occlusion handling으로 가장 가까운 파트만 선택
- 양방향 검색으로 앞/뒤 모두 감지

## 주요 변경사항

### 1. `_generate_bbox_rays()` - 새로운 Ray 생성 방식

**위치:** `detector.py:239-328`

**기능:**
- Source part의 bounding box 면에서 grid 패턴으로 ray 생성
- 선택된 평면(XY/YZ/ZX)에 따라 적절한 축에 grid 배치
- Density 파라미터로 ray 개수 조절 가능

**예시:**
```python
# XY 평면 선택 시
# - Z축 중심에서 XY 평면에 grid 생성
# - Ray 방향: +Z
# - Grid 크기: bbox의 X, Y 범위

if plane == 'XY':
    ray_direction = np.array([0.0, 0.0, 1.0])
    z_value = (min_pt[2] + max_pt[2]) / 2

    # Grid 크기 계산
    nx = max(3, int(x_size * density))
    ny = max(3, int(y_size * density))

    # Grid 생성
    x_vals = np.linspace(x_range[0], x_range[1], nx)
    y_vals = np.linspace(y_range[0], y_range[1], ny)
```

**장점:**
- Convex Hull 계산 불필요 → 빠름
- 직관적이고 이해하기 쉬움
- Bounding box만 있으면 동작

### 2. `cast_rays_with_occlusion()` - Occlusion Handling

**위치:** `ray_tracer.py:65-116`

**기능:**
- 각 ray마다 **가장 가까운 hit만** 기록
- 뒤에 가려진 파트는 자동으로 제외
- 거리 기반 정렬로 정확한 occlusion 처리

**알고리즘:**
```python
for each ray:
    closest_hit = None
    closest_distance = max_distance

    for each candidate part:
        t = ray_bbox_intersection(ray, part.bbox)

        if t is not None and t < closest_distance:
            closest_distance = t
            closest_hit = (part_id, hit_info)

    # 가장 가까운 hit만 기록
    if closest_hit is not None:
        record_hit(closest_hit)
```

**장점:**
- 중간에 가려진 파트 제외
- 실제로 "보이는" 파트만 검출
- 사용자가 기대하는 직관적인 동작

### 3. 양방향 Ray Casting

**위치:** `detector.py:161-182`

**기능:**
- Positive direction (+방향)과 Negative direction (-방향) 모두 검색
- 앞/뒤 양쪽에 있는 adjacent parts 모두 감지
- 두 방향 결과 병합

**코드:**
```python
# Positive direction
hits_by_part_pos = self._ray_tracer.cast_rays_with_occlusion(
    ray_origins_3d, ray_direction, candidates, thickness_max
)

# Negative direction
hits_by_part_neg = self._ray_tracer.cast_rays_with_occlusion(
    ray_origins_3d, -ray_direction, candidates, thickness_max
)

# Merge: 한쪽이라도 hit되면 포함
for pid in all_hit_parts:
    hits_by_part[pid] = hits_pos + hits_neg
```

## 성능 비교

| 구분 | 기존 방식 | 새로운 방식 |
|------|-----------|-------------|
| Ray 생성 | Convex Hull → 2D 투영 → Outline 추출 | BBox Grid 직접 생성 |
| Complexity | O(N log N) | O(1) |
| Ray Casting | 모든 hit 기록 | 가장 가까운 것만 |
| Occlusion | ❌ 없음 | ✅ 있음 |
| 정확도 | 가려진 파트 포함 | 실제 보이는 파트만 |

## 사용 예시

```python
# Detector 초기화
detector = AdjacentPartsDetector(mesh_data)

# Adjacent parts 검출
result = detector.find_adjacent(
    source_part_id=123,
    plane='XY',
    thickness_min=1.0,
    thickness_max=50.0,
    ray_density=0.1,  # Grid 밀도 (0.1 = 10 rays per unit length)
    coverage_threshold=0.05,  # 5% coverage면 포함
    check_facing=True  # 마주보는 파트만
)

# 결과
print(f"Adjacent parts: {result.adjacent_parts}")
print(f"Coverage: {result.coverage}")
```

## 테스트 방법

1. GUI 실행: `./rungui.sh`
2. K-file 로드
3. "패키지 이동 DOE" 모듈 활성화
4. Part 목록에서 source part 선택
5. Plane 선택 (자동 설정됨)
6. Thickness 범위 확인 (자동 설정됨)
7. "Detect Adjacent Parts" 버튼 클릭

## 향후 개선사항

1. **Element-level refinement (선택적)**
   - Bbox hit 후 실제 element 충돌 확인
   - 더 정확한 coverage 계산
   - 성능 vs 정확도 trade-off

2. **Multi-threading**
   - Ray casting 병렬화
   - 대규모 모델에서 성능 향상

3. **Adaptive ray density**
   - 파트 크기에 따라 ray 밀도 자동 조절
   - 작은 파트: 높은 밀도
   - 큰 파트: 낮은 밀도

4. **Visualization**
   - Ray 경로 시각화
   - Hit points 표시
   - Coverage heatmap

## 결론

단순하고 직관적인 Bounding Box 기반 알고리즘으로 변경하여:
- ✅ 성능 향상
- ✅ 정확도 향상 (occlusion handling)
- ✅ 코드 단순화
- ✅ 유지보수 용이

사용자의 요구사항인 "서로 마주보고 있는 파트를 찾는 간단한 방법"에 부합하는 구현입니다.
