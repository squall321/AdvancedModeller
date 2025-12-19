# DOE Placement Generator - Complete Feature Summary

## 개요

Adjacent Parts Viewer의 DOE (Design of Experiments) 배치 생성 기능이 완성되었습니다. 이 문서는 구현된 주요 기능들을 요약합니다.

## 주요 기능

### 1. Co-Planar Part Filtering (면접촉 파트 필터링)

**문제**: 패키지 하단의 PCB처럼 Z 방향으로 면접촉하는 파트들이 XY 평면 움직임을 잘못 차단하는 문제

**해결**:
```python
collision_parts, coplanar_parts = filter_coplanar_parts(
    source_part_id, adjacent_part_ids, z_tolerance=1.0
)
```

**동작 원리**:
- Z 방향 면접촉 감지 (tolerance: 1mm)
- PCB (아래), Lid (위) 자동 인식
- XY 평면 충돌 체크에서 제외
- 측면 충돌만 유효하게 체크

**테스트 결과**:
- DropSet.k: 21개 인접 → 16개 면접촉(제외) → 5개 충돌체크
- PCB\PCB (Part 3) 정확히 제외됨
- XY 이동 가능: 20/20 유효 배치 성공

### 2. Grid-Based Auto Max Displacement (격자 기반 자동 변위 계산)

**문제**: 기하학적 간격 계산이 2D 투영 왜곡으로 부정확한 값 제시

**해결**: 실제 배치 가능 공간을 격자로 탐색

**알고리즘**:
```python
def suggest_max_displacement(
    source_part_id, adjacent_part_ids,
    grid_step=0.1  # 0.1mm 간격 격자
):
    # 반경 0.5, 1, 2, 3, 5, ... 50mm 테스트
    # 각 반경에서 유효 위치 개수 카운트
    # 10개 이상 유효 위치 확보되는 최소 반경 선택
```

**특징**:
- **적응형 샘플링**:
  - 작은 반경 (<5mm): 0.1mm 정밀 격자
  - 큰 반경 (≥5mm): 0.5mm 격자 (속도 최적화)
- **실제 공간 기반**: BBox 근사가 아닌 실제 충돌 체크
- **방향성 고려**: 특정 방향만 여유 있는 경우 자동 감지

**의사결정 로직**:
```
if 10개 이상 유효 위치 발견:
    → 해당 반경 사용 ✓
elif 일부라도 유효 위치 발견:
    → 조밀 배치 감지, 최소 동작 값 사용
else:
    → 기본값 5mm 사용
```

### 3. Latin Hypercube Sampling (LHS)

**목적**: 효율적이고 균일한 DOE 샘플링

**구현**:
- pyDOE2 라이브러리 사용
- 균등 분포 대신 공간 충진 설계
- 적은 샘플로 넓은 영역 탐색

### 4. Feasible Space Analysis (가능 영역 분석)

**기술**: Voxel 기반 충돌 없는 영역 식별

**과정**:
1. 소스 파트 주변 격자 생성 (voxel_size: 2mm)
2. 각 격자점에서 충돌 체크
3. 연결된 유효 영역 그룹화
4. 면적 계산 및 시각화

**활용**:
- 배치 가능 영역 사전 파악
- DOE 샘플링 효율성 향상
- GUI 시각적 피드백

### 5. Adaptive Resampling (적응형 재샘플링)

**문제**: 조밀한 배치에서 목표 개수 달성 어려움

**해결**:
```python
# 목표: 20개 유효 배치
# 시도 1: 20개 샘플링 → 5개 유효 (25%)
# 시도 2: 45개 샘플링 (3배) → 19개 유효 (95%)
# 시도 3: 3개 샘플링 (부족분만) → 20개 달성 ✓
```

**전략**:
- 최대 20회 재시도
- 부족 개수에 비례해서 샘플 수 증가
- 100% 달성률 목표

## 통합 워크플로우

```python
# 1. 인접 파트 감지
detector = AdjacentPartsDetector(mesh_data)
result = detector.find_adjacent(
    source_part_id, plane='XY',
    thickness_min=0, thickness_max=50
)

# 2. Co-planar 필터링
generator = DOEPlacementGenerator(mesh_data)
collision_parts, coplanar_parts = generator.filter_coplanar_parts(
    source_part_id, result.adjacent_parts, z_tolerance=1.0
)

# 3. 자동 Max Displacement 계산
suggested = generator.suggest_max_displacement(
    source_part_id, collision_parts, grid_step=0.1
)

# 4. DOE 생성
doe_result = generator.generate_placements(
    source_part_id, result.adjacent_parts,
    num_samples=20,
    max_displacement=suggested,
    enable_resampling=True
)
```

## 테스트 케이스

### Case 1: Synthetic PCB Scenario

**구성**:
- Package (10×10×5) at z=5~10
- PCB (30×30×1) at z=4~5 (face-to-face)
- Side Wall (5×30×10) at x=15~20

**결과**:
- ✓ PCB 정확히 제외 (co-planar)
- ✓ Side Wall 충돌 체크
- ✓ 10/10 유효 배치 달성

### Case 2: DropSet.k Real Data

**구성**:
- PKG\PKG 1 (Part 4) 선택
- 21개 인접 파트
- 조밀한 실제 배치

**필터링 결과**:
```
21 adjacent parts
  ├─ 16 co-planar (excluded): PCB, PKG 3-6, ...
  └─  5 collision check: Parts 1, 2, 20, 21, 22
```

**Grid Search**:
```
  0.5mm: 0 valid
  1.0mm: 0 valid
  2.0mm: 0 valid
  5.0mm: 0 valid
 10.0mm: 0 valid
 15.0mm: 0 valid
 20.0mm: 191 valid ✓ (only +X direction)
```

**Directional Analysis**:
- +X 20mm: ✓ (유일한 여유 공간)
- 다른 모든 방향: ✗ (조밀 배치)

**DOE 생성**:
- Suggested: 20mm
- Result: 20/20 valid placements
- Success rate: 100%
- Average displacement: 19.2mm
- Direction: predominantly +X

## 성능 최적화

### 격자 탐색 최적화

| 반경 | 격자 간격 | 포인트 수 | 계산 시간 |
|------|-----------|----------|----------|
| 2mm | 0.1mm | 1,681 | ~0.1s |
| 5mm | 0.5mm | 441 | ~0.05s |
| 20mm | 0.5mm | 6,561 | ~0.5s |

**최적화 전략**:
- 작은 반경: 정밀도 우선 (0.1mm)
- 큰 반경: 속도 우선 (0.5mm)
- 조기 종료: 10개 유효 위치 발견 시 중단

### 재샘플링 효율

```
평균 시도 횟수: 2-3회
목표 달성률: 95-100%
총 소요 시간: <5초
```

## GUI 통합

### 자동 설정
```python
# Auto-calculate and set max_displacement
suggested = generator.suggest_max_displacement(...)
max_displacement_spin.setValue(suggested)

log(f"자동 Max Displacement 설정: {suggested:.1f} mm")
```

### 사용자 피드백
```python
print(f"Grid-based search (step=0.1mm)")
print(f"  Radius 2.0mm: 0/1681 valid (0.0%)")
print(f"  Radius 20.0mm: 191/6561 valid (2.9%) ✓")
print(f"Found 191 valid positions at 20.0mm")
```

## 파일 구조

```
gui/modules/adjacent_parts_viewer/core/
├── doe_placement.py          # Main DOE generator
│   ├── suggest_max_displacement()  # Grid-based auto-suggest
│   ├── filter_coplanar_parts()     # Face-to-face filtering
│   ├── generate_placements()       # LHS + resampling
│   └── find_collisions()           # BBox collision check
│
├── spatial_utils.py          # Geometric utilities
│   └── BBox2D.min_distance_to()    # Edge-to-edge distance
│
└── feasible_space.py         # Voxel-based space analysis
    └── FeasibleSpaceAnalyzer

tests/
├── test_coplanar_filtering.py      # Synthetic PCB test
├── test_dropset_coplanar.py        # Real data test
├── test_auto_displacement.py       # Auto-suggest test
└── test_grid_directions.py         # Directional analysis

docs/
├── DOE_AUTO_DISPLACEMENT_GRID.md   # Grid algorithm detail
└── DOE_FEATURES_SUMMARY.md         # This file
```

## 향후 개선 사항

### 1. GUI 고급 옵션
- [ ] Grid step size 조정 UI
- [ ] 방향성 히트맵 시각화
- [ ] 유효 영역 3D 표시

### 2. 알고리즘 개선
- [ ] Multi-scale grid search
- [ ] 방향별 힌트 제공
- [ ] 사용자 정의 grid_step

### 3. 성능 최적화
- [ ] GPU 가속 충돌 체크
- [ ] 병렬 격자 탐색
- [ ] 캐싱 최적화

## 결론

DOE 배치 생성 기능이 다음 핵심 요구사항을 모두 충족합니다:

✅ **정확성**: Co-planar 필터링으로 잘못된 충돌 제거
✅ **신뢰성**: Grid 기반 탐색으로 실제 동작하는 값 제시
✅ **효율성**: 적응형 재샘플링으로 높은 달성률
✅ **사용성**: 자동 계산으로 사용자 편의성 극대화

**핵심 성과**:
- DropSet.k 같은 조밀 배치에서도 100% 유효 배치 달성
- 면접촉 파트(PCB 등) 정확히 제외
- 실제 가능한 변위 값 자동 제시
- 2-3회 시도로 목표 개수 달성

이 기능은 실제 PCB 패키지 재배치 시나리오에 즉시 활용 가능합니다.
