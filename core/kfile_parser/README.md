# K-File High-Performance Parser

pybind11 기반 고속 LS-DYNA K-file 파서

## 빠른 시작

### 1. 빌드

**Linux/Mac:**
```bash
cd core/kfile_parser
./build.sh
```

**Windows:**
```cmd
cd core\kfile_parser
build.bat
```

### 2. 사용

```python
from core.kfile_parser import KFileParser

parser = KFileParser()
result = parser.parse("model.k")

print(f"노드: {len(result.nodes)}개")
print(f"파트: {len(result.parts)}개")
print(f"엘리먼트: {len(result.elements)}개")
print(f"파싱 시간: {result.stats['parse_time_ms']}ms")
```

---

## 빌드 스크립트 옵션

### Linux/Mac (build.sh)

| 명령 | 설명 |
|------|------|
| `./build.sh` | 기본 빌드 |
| `./build.sh clean` | 빌드 파일 정리 |
| `./build.sh test` | 빌드 + 테스트 실행 |
| `./build.sh all` | 정리 + 빌드 + 테스트 |

### Windows (build.bat)

| 명령 | 설명 |
|------|------|
| `build.bat` | 기본 빌드 |
| `build.bat clean` | 빌드 파일 정리 |
| `build.bat test` | 빌드 + 테스트 실행 |
| `build.bat all` | 정리 + 빌드 + 테스트 |

---

## 요구사항

### 공통
- Python 3.8+
- pip
- pybind11 (자동 설치됨)

### Linux
- g++ 또는 clang++
- python3-dev

```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev

# CentOS/RHEL
sudo yum install gcc-c++ python3-devel
```

### Mac
- Xcode Command Line Tools

```bash
xcode-select --install
```

### Windows
- Visual Studio Build Tools (C++ 빌드 도구)
- [다운로드](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- "Desktop development with C++" 워크로드 선택
- **Developer Command Prompt**에서 빌드 실행 권장

---

## 사용 방법

### 방법 1: 직접 사용

```python
from core.kfile_parser import KFileParser, ParsedKFile

# 파서 생성 (옵션 설정 가능)
parser = KFileParser(
    parse_nodes=True,      # 노드 파싱
    parse_parts=True,      # 파트 파싱
    parse_elements=True,   # 엘리먼트 파싱
    build_index=True       # ID 인덱스 빌드
)

# 파일 파싱
result = parser.parse("model.k")

# 노드 접근
for node in result.nodes:
    print(f"Node {node.nid}: ({node.x}, {node.y}, {node.z})")

# ID로 조회
node = result.get_node(12345)
part = result.get_part(1)
element = result.get_element(100)

# 파트별 엘리먼트
elements = result.get_elements_by_part(1)
```

### 방법 2: KooDynaKeyword 호환 방식

```python
from core.KooDynaKeyword import KFileReader, read_kfile

# 편의 함수
reader = read_kfile("model.k")

# numpy 배열로 접근
nodes = reader.node_array()      # (N, 6) [NID, X, Y, Z, TC, RC]
parts = reader.part_array()      # (N, 8) [PID, SECID, MID, ...]
elements = reader.element_array()  # (N, 10) [EID, PID, N1-N8]

# 기존 객체 방식
dyna_nodes = reader.get_nodes()
print(dyna_nodes.NID(0, 0))
print(dyna_nodes.X(0, 0))
```

### 방법 3: 문자열 파싱

```python
kfile_content = """
*NODE
       1       0.000000       0.000000       0.000000
       2       1.000000       0.000000       0.000000
*END
"""

parser = KFileParser()
result = parser.parse_string(kfile_content)
```

---

## 배포 방법

`KooDynaKeyword.py`와 `kfile_parser/` 폴더를 함께 복사하면 됩니다:

```
your_project/
├── KooDynaKeyword.py    # 호환 래퍼
└── kfile_parser/        # 고속 파서 모듈
    ├── __init__.py
    ├── wrapper.py
    └── _kfile_parser*.so (또는 .pyd)
```

```python
# 복사한 위치에서 바로 사용
from KooDynaKeyword import KFileReader
reader = KFileReader("model.k")
```

---

## 성능

| 데이터 크기 | Python 파서 | C++ 파서 | 속도 향상 |
|-------------|-------------|----------|-----------|
| 10만 노드 | ~2초 | ~0.1초 | 20배 |
| 100만 노드 | ~20초 | ~1초 | 20배 |
| 500만 노드 | ~100초 | ~5초 | 20배 |

*테스트 환경: Intel i7, 32GB RAM, SSD*

---

## 지원 키워드

| 키워드 | 지원 | 비고 |
|--------|------|------|
| *NODE | ✅ | NID, X, Y, Z, TC, RC |
| *PART | ✅ | NAME, PID, SECID, MID, ... |
| *ELEMENT_SHELL | ✅ | EID, PID, N1-N8 |
| *ELEMENT_SOLID | ✅ | EID, PID, N1-N8 |
| *CONTACT_* | 🚧 | 개발 예정 |
| *SET_* | 🚧 | 개발 예정 |
| *MAT_* | 🚧 | 개발 예정 |

---

## 문제 해결

### 빌드 실패: "Python.h not found"

```bash
# Ubuntu/Debian
sudo apt install python3-dev

# CentOS/RHEL
sudo yum install python3-devel
```

### 빌드 실패: "pybind11 not found"

```bash
pip install pybind11
```

### Windows: "cl.exe not found"

Developer Command Prompt에서 실행하거나 Visual Studio Build Tools 설치

### ImportError: C++ 모듈 없음

C++ 빌드 없이도 Python 폴백 파서가 자동으로 작동합니다. 다만 속도가 느립니다.

---

## 파일 구조

```
kfile_parser/
├── README.md              # 이 문서
├── DEVELOPMENT_PLAN.md    # 개발 계획
├── CHANGELOG.md           # 변경 이력
├── setup.py               # 빌드 설정
├── build.sh               # Linux/Mac 빌드
├── build.bat              # Windows 빌드
├── src/                   # C++ 소스
│   ├── node.hpp
│   ├── part.hpp
│   ├── element.hpp
│   ├── parser.hpp/cpp
│   └── bindings.cpp
├── kfile_parser/          # Python 패키지
│   ├── __init__.py
│   └── wrapper.py
└── tests/
    ├── sample.k
    └── test_parser.py
```

---

## 라이선스

MIT License
