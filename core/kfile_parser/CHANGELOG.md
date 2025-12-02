# 변경 이력 (CHANGELOG)

모든 주요 변경사항을 기록합니다.

---

## [0.2.2] - 2025-11-28

### 완료된 항목 (Phase 2.5 - SECTION 파싱)

#### C++ 데이터 구조 (src/)
- [x] `section.hpp` - Section 구조체 정의
  - SectionType enum (SHELL, SOLID, BEAM)
  - SECID, ELFORM 공통 필드
  - Shell: SHRF, NIP, PROPT, QR_IRID, ICOMP, SETYP, T1-T4, NLOC, MAREA, IDOF, EDGSET
  - Solid: AET
  - Beam: CST, SCOOR, TS1-TS2, TT1-TT2, NSLOC, NTLOC

#### C++ 파서 업데이트 (src/)
- [x] `parser.hpp` - SECTION 파싱 상태 추가
  - IN_SECTION_SHELL_HEADER/DATA 상태
  - IN_SECTION_SOLID 상태
  - IN_SECTION_BEAM_HEADER/DATA 상태
- [x] `parser.cpp` - SECTION 파싱 로직 구현
  - SECTION_SHELL (2줄: 헤더 + 데이터)
  - SECTION_SOLID (1줄)
  - SECTION_BEAM (2줄: 헤더 + 데이터)

#### Python 바인딩 (src/)
- [x] `bindings.cpp` - SECTION 타입 Python 노출
  - SectionType enum 바인딩
  - Section 구조체 바인딩 (모든 필드)
  - SectionVector 바인딩
  - ParseResult.sections, section_index 추가
  - KFileParser.set/get_parse_sections 추가

#### Python 래퍼 (kfile_parser/)
- [x] `wrapper.py` - SECTION 지원 추가
  - SectionType enum (Python)
  - SectionData dataclass
  - ParsedKFile.sections 속성
  - get_section() / get_sections_by_type() 메서드
  - Python 폴백 파서 SECTION 지원

#### 테스트
- [x] `sample.k` - SECTION 테스트 데이터 추가
- [x] `test_parser.py` - SECTION 파싱 테스트 추가

---

## [0.2.1] - 2025-11-28

### 완료된 항목 (Phase 2 - ELEMENT_BEAM 파싱)

#### C++ 파서 업데이트 (src/)
- [x] `element.hpp` - ElementType에 BEAM 추가
- [x] `parser.hpp` - IN_ELEMENT_BEAM 상태 추가
- [x] `parser.cpp` - ELEMENT_BEAM 키워드 감지 및 파싱 로직 구현
- [x] `bindings.cpp` - ElementType.BEAM Python 노출

#### Python 래퍼 (kfile_parser/)
- [x] `wrapper.py` - BEAM 타입 지원 추가
  - ElementData.from_cpp BEAM 매핑
  - Python 폴백 파서 BEAM 처리

#### 테스트
- [x] `sample.k` - ELEMENT_BEAM 테스트 데이터 추가
- [x] `test_parser.py` - ELEMENT_BEAM 파싱 테스트 추가

---

## [0.2.0] - 2025-11-28

### 완료된 항목 (Phase 2 - SET 파싱)

#### C++ SET 데이터 구조 (src/)
- [x] `set.hpp` - Set 구조체 정의
  - SetType enum (NODE_LIST, PART_LIST, SEGMENT, SHELL, SOLID)
  - SID, DA1-DA4, SOLVER 필드
  - IDs 리스트 (NODE_LIST, PART_LIST, SHELL, SOLID용)
  - Segments 리스트 (SEGMENT용, 4노드씩)

#### C++ 파서 업데이트 (src/)
- [x] `parser.hpp` - SET 파싱 상태 추가
  - IN_SET_NODE_HEADER/DATA 상태
  - IN_SET_PART_HEADER/DATA 상태
  - IN_SET_SEGMENT_HEADER/DATA 상태
  - IN_SET_SHELL_HEADER/DATA 상태
  - IN_SET_SOLID_HEADER/DATA 상태
- [x] `parser.cpp` - SET 파싱 로직 구현
  - parse_set_header() - 헤더 라인 파싱
  - parse_set_data_line() - 데이터 라인 파싱 (8 IDs per line)
  - parse_segment_data_line() - 세그먼트 데이터 파싱 (4 nodes per segment)

#### Python 바인딩 (src/)
- [x] `bindings.cpp` - SET 타입 Python 노출
  - SetType enum 바인딩
  - Set 구조체 바인딩
  - SetVector 바인딩
  - ParseResult.sets 추가

#### Python 래퍼 (kfile_parser/)
- [x] `wrapper.py` - SET 지원 추가
  - SetType enum (Python)
  - SetData dataclass
  - ParsedKFile.sets 속성
  - get_set() / get_sets_by_type() 메서드
  - Python 폴백 파서 SET 지원

#### 테스트
- [x] `sample.k` - SET 테스트 데이터 추가
- [x] `test_parser.py` - SET 파싱 테스트 추가

---

## [0.1.0] - 2024-11-28

### 완료된 항목

#### 프로젝트 구조
- [x] 디렉토리 구조 생성
  - `src/` - C++ 소스
  - `kfile_parser/` - Python 패키지
  - `tests/` - 테스트 파일
- [x] 빌드 시스템 구성
  - `setup.py` - Python 빌드 설정
  - `build.sh` - Linux/Mac 빌드 스크립트
  - `build.bat` - Windows 빌드 스크립트
- [x] 문서화
  - `README.md` - 사용법 가이드
  - `DEVELOPMENT_PLAN.md` - 개발 계획
  - `CHANGELOG.md` - 변경 이력 (이 파일)

#### C++ 데이터 구조 (src/)
- [x] `node.hpp` - Node 구조체 정의
  - NID, X, Y, Z, TC, RC 필드
  - 컬럼 폭: [8, 16, 16, 16, 8, 8]
- [x] `part.hpp` - Part 구조체 정의
  - NAME, PID, SECID, MID, EOSID, HGID, GRAV, ADPOPT, TMID
  - 컬럼 폭: [80], [10x8]
- [x] `element.hpp` - Element 구조체 정의
  - EID, PID, N1-N8
  - ElementType enum (SHELL, SOLID)
  - 컬럼 폭: [8x10]
- [x] `parser.hpp/cpp` - 핵심 파서 구현
  - 상태 머신 기반 파싱
  - 키워드 감지 및 라우팅
  - 고정 폭 컬럼 파싱 유틸리티
- [x] `bindings.cpp` - pybind11 바인딩
  - 모든 구조체 Python 노출
  - STL 컨테이너 바인딩

#### Python 래퍼 (kfile_parser/)
- [x] `__init__.py` - 패키지 진입점
  - C++ 모듈 동적 임포트
  - 임포트 에러 처리
- [x] `wrapper.py` - Python 래퍼 클래스
  - `KFileParser` - 메인 파서 클래스
  - `ParsedKFile` - 파싱 결과 컨테이너
  - `NodeData`, `PartData`, `ElementData` - Python 데이터클래스
  - Python 폴백 파서 (C++ 없이도 작동)

#### KooDynaKeyword 호환 래퍼 (core/)
- [x] `KooDynaKeyword.py` - 기존 API 호환
  - `DynaNode` - 노드 키워드 클래스
  - `Part` - 파트 키워드 클래스
  - `ElementShell` - 쉘 엘리먼트 클래스
  - `ElementSolid` - 솔리드 엘리먼트 클래스
  - `KFileReader` - 파일 리더 클래스
  - 기존 메서드 호환: NID(), X(), Y(), Z(), getNodeList() 등

#### 테스트
- [x] `sample.k` - 테스트용 K파일
- [x] `test_parser.py` - 테스트 코드
  - Python 폴백 테스트 통과
  - 문자열 파싱 테스트 통과
  - KooDynaKeyword 호환성 테스트 통과

---

## 지원 키워드 현황

### 구현 완료 (Phase 1)

| 키워드 | 파서 | 래퍼 | 테스트 |
|--------|------|------|--------|
| *NODE | ✅ | ✅ | ✅ |
| *PART | ✅ | ✅ | ✅ |
| *ELEMENT_SHELL | ✅ | ✅ | ✅ |
| *ELEMENT_SOLID | ✅ | ✅ | ✅ |

### 구현 완료 (Phase 2)

| 키워드 | 파서 | 래퍼 | 테스트 |
|--------|------|------|--------|
| *ELEMENT_BEAM | ✅ | ✅ | ✅ |
| *SET_NODE_LIST | ✅ | ✅ | ✅ |
| *SET_PART_LIST | ✅ | ✅ | ✅ |
| *SET_SEGMENT | ✅ | ✅ | ✅ |
| *SET_SHELL | ✅ | ✅ | ✅ |
| *SET_SOLID | ✅ | ✅ | ✅ |

### 구현 완료 (Phase 2.5 - SECTION)

| 키워드 | 파서 | 래퍼 | 테스트 |
|--------|------|------|--------|
| *SECTION_SHELL | ✅ | ✅ | ✅ |
| *SECTION_SOLID | ✅ | ✅ | ✅ |
| *SECTION_BEAM | ✅ | ✅ | ✅ |

### 구현 예정 (Phase 3)

| 키워드 | 우선순위 | 상태 |
|--------|----------|------|
| *CONTACT_* (30+ 종류) | 중간 | 📋 |
| *MAT_* (30+ 종류) | 중간 | 📋 |
| *BOUNDARY_* | 중간 | 📋 |
| *DEFINE_CURVE | 중간 | 📋 |
| *LOAD_* | 낮음 | 📋 |
| *CONTROL_* | 낮음 | 📋 |
| *DATABASE_* | 낮음 | 📋 |

---

## 범례

- ✅ 완료
- 🚧 진행 중
- 📋 계획됨
- ❌ 미지원
