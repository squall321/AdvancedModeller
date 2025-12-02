# K-File High-Performance Parser 개발 계획

pybind11을 활용한 고속 LS-DYNA K-file 파서 모듈 개발 계획서입니다.

---

## 목차
1. [개요](#개요)
2. [전체 키워드 분석](#전체-키워드-분석)
3. [구현 우선순위](#구현-우선순위)
4. [최적화 전략](#최적화-전략)
5. [데이터 포맷 상세](#데이터-포맷-상세)
6. [구현 로드맵](#구현-로드맵)
7. [성능 목표](#성능-목표)

---

## 개요

### 프로젝트 목적
LS-DYNA K-file에서 메시 데이터(NODE, PART, ELEMENT 등)를 고속으로 파싱하는 C++ 기반 모듈

### 왜 C++인가?
- K-file은 수십만~수백만 라인의 대용량 파일
- Python의 문자열 파싱은 느림 (특히 고정 폭 컬럼 파싱)
- C++로 **10-100배** 성능 향상 기대
- 메모리 효율적인 데이터 구조 사용 가능

### 현재 상태
- **Phase 1 완료**: NODE, PART, ELEMENT_SHELL, ELEMENT_SOLID 파싱
- **Python 폴백**: C++ 빌드 없이도 작동 (느림)
- **테스트**: 모든 기본 테스트 통과

---

## 전체 키워드 분석

KooDynaKeyword.py 분석 결과, 총 **200+ 키워드 클래스**가 존재합니다.

### 카테고리별 분류

| 카테고리 | 키워드 수 | 예시 |
|----------|----------|------|
| **Mesh Data** | ~15 | NODE, PART, ELEMENT_* |
| **Set Definition** | ~20 | SET_NODE_*, SET_PART_*, SET_SEGMENT_* |
| **Contact** | ~40 | CONTACT_AUTOMATIC_*, CONTACT_TIED_* |
| **Material** | ~25 | MAT_ELASTIC, MAT_RIGID, MAT_PLASTIC_* |
| **Section** | ~15 | SECTION_SHELL, SECTION_SOLID, SECTION_BEAM |
| **Boundary** | ~15 | BOUNDARY_SPC_*, BOUNDARY_PRESCRIBED_* |
| **Control** | ~30 | CONTROL_TERMINATION, CONTROL_TIMESTEP |
| **Database** | ~35 | DATABASE_BINARY_*, DATABASE_HISTORY_* |
| **Load** | ~15 | LOAD_NODE_*, LOAD_BODY_*, LOAD_SEGMENT_* |
| **Define** | ~5 | DEFINE_CURVE, DEFINE_BOX |
| **기타** | ~15 | CONSTRAINED_*, DAMPING_*, HOURGLASS |

### 메시 관련 키워드 상세

#### 완료됨 ✅

| 키워드 | 설명 | 컬럼 폭 |
|--------|------|---------|
| *NODE | 노드 정의 | [8,16,16,16,8,8] |
| *PART | 파트 정의 | [80], [10x8] |
| *ELEMENT_SHELL | 쉘 요소 | [8x10] |
| *ELEMENT_SOLID | 솔리드 요소 | [8x10] |

#### Phase 2 예정 🚧

| 키워드 | 설명 | 컬럼 폭 |
|--------|------|---------|
| *ELEMENT_BEAM | 빔 요소 | [8,8,8,8,8] |
| *SET_NODE_LIST | 노드 세트 | [10x8] |
| *SET_PART_LIST | 파트 세트 | [10x8] |
| *SET_SEGMENT | 세그먼트 세트 | [10x4 per line] |
| *SET_SHELL | 쉘 세트 | [10x8] |
| *SET_SOLID | 솔리드 세트 | [10x8] |
| *SECTION_SHELL | 쉘 섹션 | [10x8] multiple lines |
| *SECTION_SOLID | 솔리드 섹션 | [10x8] |
| *SECTION_BEAM | 빔 섹션 | [10x8] multiple lines |

---

## 구현 우선순위

### Phase 1: 핵심 메시 데이터 ✅ (완료)
```
NODE → PART → ELEMENT_SHELL → ELEMENT_SOLID
```

### Phase 2: 세트 및 섹션 (다음 목표)
```
SET_NODE_LIST → SET_PART_LIST → SET_SEGMENT →
SET_SHELL → SET_SOLID →
SECTION_SHELL → SECTION_SOLID → SECTION_BEAM →
ELEMENT_BEAM
```

### Phase 3: 접촉 및 재료
```
CONTACT_* (주요 유형) → MAT_* (주요 유형)
```

### Phase 4: 경계조건 및 하중
```
BOUNDARY_SPC_* → BOUNDARY_PRESCRIBED_* → LOAD_*
```

### Phase 5: 제어 및 출력
```
CONTROL_* → DATABASE_* → DEFINE_CURVE
```

---

## 최적화 전략

### 1. 파싱 알고리즘 최적화

#### 1.1 메모리 사전 할당 (Pre-allocation)
```cpp
// 파일 크기 기반 예측 할당
size_t estimated_nodes = file_size / 80;  // 약 80 bytes per node
result.nodes.reserve(estimated_nodes);
result.elements.reserve(estimated_nodes * 5);  // 대략 5배
```

#### 1.2 Memory-Mapped File I/O
```cpp
#include <sys/mman.h>

// 대용량 파일은 mmap으로 읽기
void* mapped = mmap(NULL, file_size, PROT_READ, MAP_PRIVATE, fd, 0);
// 직접 메모리 접근으로 버퍼 복사 제거
```

#### 1.3 SIMD 활용 (Advanced)
```cpp
// AVX2로 8개 숫자 동시 파싱
__m256d parse_8_doubles_simd(const char* data);
```

### 2. 고정 폭 파싱 최적화

#### 2.1 직접 숫자 변환 (strtod 회피)
```cpp
// 빠른 정수 파싱
inline int32_t fast_atoi(const char* str, size_t len) {
    int32_t result = 0;
    bool negative = false;
    const char* end = str + len;

    // 공백 스킵
    while (str < end && *str == ' ') ++str;

    // 부호 처리
    if (str < end && *str == '-') {
        negative = true;
        ++str;
    }

    // 숫자 변환
    while (str < end && *str >= '0' && *str <= '9') {
        result = result * 10 + (*str - '0');
        ++str;
    }

    return negative ? -result : result;
}

// 빠른 실수 파싱
inline double fast_atof(const char* str, size_t len) {
    // 지수 표기 포함한 빠른 파싱
    // charconv (C++17) 사용 권장
    double result;
    std::from_chars(str, str + len, result);
    return result;
}
```

### 3. 병렬 처리

#### 3.1 청크 기반 병렬 파싱
```cpp
#pragma omp parallel for
for (size_t i = 0; i < chunks.size(); ++i) {
    auto local_result = parse_chunk(chunks[i]);

    #pragma omp critical
    merge_results(result, local_result);
}
```

#### 3.2 파이프라인 병렬화
```
[파일 읽기] → [라인 분리] → [키워드 분류] → [데이터 파싱]
     ↓             ↓              ↓              ↓
   Thread1      Thread2       Thread3        Thread4
```

### 4. 인덱스 최적화

#### 4.1 해시맵 vs 정렬 배열
```cpp
// ID가 연속적이면 직접 배열 접근
if (is_contiguous_ids) {
    // O(1) 직접 접근
    node = nodes[nid - min_nid];
} else {
    // O(1) 해시맵
    auto it = node_index.find(nid);
}
```

#### 4.2 인덱스 지연 생성
```cpp
// 필요할 때만 인덱스 생성
const Node* get_node(int32_t nid) {
    if (!index_built_) {
        build_index();  // lazy initialization
    }
    return find_in_index(nid);
}
```

---

## 데이터 포맷 상세

### Phase 2 키워드 포맷

#### *ELEMENT_BEAM
```
*ELEMENT_BEAM
$#   eid     pid      n1      n2      n3
       1       1       1       2       3
```
컬럼: [8, 8, 8, 8, 8]

#### *SET_NODE_LIST
```
*SET_NODE_LIST
$#     sid       da1       da2       da3       da4    solver
         1       0.0       0.0       0.0       0.0MECH
$#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
         1         2         3         4         5         6         7         8
```
헤더: [10, 10, 10, 10, 10, 10]
데이터: [10x8] 반복

#### *SET_PART_LIST
```
*SET_PART_LIST
$#     sid       da1       da2       da3       da4    solver
         1       0.0       0.0       0.0       0.0MECH
$#    pid1      pid2      pid3      pid4      pid5      pid6      pid7      pid8
         1         2         3         4         0         0         0         0
```
헤더: [10, 10, 10, 10, 10, 10]
데이터: [10x8] 반복

#### *SET_SEGMENT
```
*SET_SEGMENT
$#     sid       da1       da2       da3       da4    solver
         1       0.0       0.0       0.0       0.0MECH
$#      n1        n2        n3        n4
         1         2         3         4
         5         6         7         8
```
헤더: [10, 10, 10, 10, 10, 10]
데이터: [10x4] 반복 (세그먼트당 4노드)

#### *SECTION_SHELL
```
*SECTION_SHELL
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         1         2       1.0         2       1.0         0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
       1.0       1.0       1.0       1.0       0.0       0.0       0.0       0.0
```
라인1: [10x8]
라인2: [10x8]

#### *SECTION_SOLID
```
*SECTION_SOLID
$#   secid    elform       aet    unused    unused    unused    cohoff   gasession
         1         1         0
```
[10x8]

---

## 구현 로드맵

### Phase 1 ✅ 완료 (2024-11-28)
- [x] 프로젝트 구조 생성
- [x] NODE 파싱
- [x] PART 파싱
- [x] ELEMENT_SHELL 파싱
- [x] ELEMENT_SOLID 파싱
- [x] Python 래퍼
- [x] 테스트

### Phase 2 🚧 진행 예정
- [ ] SET_NODE_LIST 파싱
- [ ] SET_PART_LIST 파싱
- [ ] SET_SEGMENT 파싱
- [ ] SET_SHELL / SET_SOLID 파싱
- [ ] ELEMENT_BEAM 파싱
- [ ] SECTION_SHELL / SECTION_SOLID 파싱
- [ ] 최적화: 메모리 사전 할당
- [ ] 최적화: fast_atoi/fast_atof

### Phase 3 📋 계획됨
- [ ] CONTACT_* 파싱 (주요 10종)
- [ ] MAT_* 파싱 (주요 10종)
- [ ] 최적화: Memory-mapped I/O
- [ ] 최적화: 병렬 파싱 (OpenMP)

### Phase 4 📋 계획됨
- [ ] BOUNDARY_SPC_* 파싱
- [ ] BOUNDARY_PRESCRIBED_* 파싱
- [ ] LOAD_* 파싱
- [ ] 최적화: SIMD 활용

### Phase 5 📋 계획됨
- [ ] CONTROL_* 파싱
- [ ] DATABASE_* 파싱
- [ ] DEFINE_CURVE 파싱
- [ ] 전체 최적화 및 벤치마크

---

## 성능 목표

### 파싱 속도

| 데이터 크기 | Python (현재) | C++ (목표) | 배율 |
|-------------|---------------|------------|------|
| 10만 노드 | ~2초 | <0.2초 | 10x |
| 100만 노드 | ~20초 | <2초 | 10x |
| 500만 노드 | ~100초 | <10초 | 10x |

### 메모리 사용량

| 데이터 | 크기 (bytes) | 100만 개 |
|--------|-------------|----------|
| Node | 40 | ~40 MB |
| Part | 48 | ~48 KB |
| Element | 48 | ~48 MB |
| 인덱스 | 16 per entry | ~16 MB |
| **총합** | - | **~100 MB** |

### 최적화 후 목표

| 항목 | 현재 | 최적화 후 |
|------|------|----------|
| 100만 노드 파싱 | 2초 (Python) | <1초 (C++) |
| 메모리 | 200 MB | 100 MB |
| 인덱스 빌드 | 동기 | 지연/병렬 |

---

## 참고 자료

- [pybind11 문서](https://pybind11.readthedocs.io/)
- [LS-DYNA Keyword Manual](https://www.dynasupport.com/manuals)
- [references/KooDynaKeyword.py](../../references/KooDynaKeyword.py) - 기존 Python 파서 참조
- [charconv (C++17)](https://en.cppreference.com/w/cpp/utility/from_chars) - 빠른 숫자 파싱

---

## 관련 문서

- [README.md](README.md) - 사용법 가이드
- [CHANGELOG.md](CHANGELOG.md) - 변경 이력
