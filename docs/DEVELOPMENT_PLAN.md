# Laminate Modeller GUI - 개발 계획서

## 프로젝트 개요

기존 CLI 기반의 라미네이트 적층 구성 자동화 도구를 **PySide6 기반 현대적 GUI 애플리케이션**으로 확장합니다.
사용자가 LS-DYNA k파일에서 Part ID를 읽어오고, 직관적인 인터페이스로 적층 구성을 정의하여
`*_display.txt` 스크립트를 생성하고 `KooMeshModifier`를 실행할 수 있도록 합니다.

---

## 기술 스택

| 구성요소 | 기술 | 라이선스 |
|---------|------|----------|
| GUI 프레임워크 | **PySide6** | LGPL v3 (상업적 무료) |
| 아이콘 | QtAwesome (Font Awesome) | MIT |
| Python 버전 | 3.9+ | - |
| 패키지 관리 | venv + pip | - |
| 설정 저장 | JSON | - |

---

## UI/UX 디자인

### 디자인 원칙
- **다크 모드 기본** - 엔지니어링 소프트웨어 트렌드
- **카드 기반 레이아웃** - 섹션별 시각적 구분
- **미니멀리즘** - 필요한 것만 표시
- **즉각적 피드백** - 호버, 클릭 애니메이션
- **적층 시각화** - 설정한 레이어를 실시간 미리보기

### 컬러 팔레트 (다크 테마)
```
배경 (Background):     #1a1a2e, #16213e
카드 (Card):           #1f2937, #374151
강조 (Accent):         #3b82f6 (Blue), #10b981 (Green)
텍스트 (Text):         #f3f4f6, #9ca3af
경고 (Warning):        #f59e0b
오류 (Error):          #ef4444
```

### 메인 윈도우 레이아웃

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ◉ Laminate Modeller                                          ─  □  ✕     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📁 K파일    [/path/to/model.k                        ] [열기]      │   │
│  │  📋 Material [/path/to/MaterialSource.txt             ] [열기]      │   │
│  │  💾 출력명   [B5                                      ] [K파일 로드]│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Parts ──────────────┐  ┌─ Layer Editor ─────────────────────────────┐  │
│  │                      │  │                                            │  │
│  │  ┌────────────────┐  │  │  Part 44 - 레이어 구성                     │  │
│  │  │ ☑ Part 35     │  │  │  ┌────────────────────────────────────┐   │  │
│  │  │   2 layers     │  │  │  │ #   Material ▼    두께    층구분  │   │  │
│  │  └────────────────┘  │  │  │ 1   PL            0.080   [1]     │   │  │
│  │  ┌────────────────┐  │  │  │ 2   PSA0          0.035   [2]     │   │  │
│  │  │ ☑ Part 44  ◀──┼──┼──│  │                                    │   │  │
│  │  │   2 layers     │  │  │  └────────────────────────────────────┘   │  │
│  │  └────────────────┘  │  │                                            │  │
│  │  ┌────────────────┐  │  │  [＋ 추가]  [－ 삭제]  [📋 복사] [📄 붙여넣기] │  │
│  │  │ ☑ Part 45     │  │  │                                            │  │
│  │  │   5 layers     │  │  └────────────────────────────────────────────┘  │
│  │  └────────────────┘  │                                                  │
│  │  ┌────────────────┐  │  ┌─ Layer Preview ────────────────────────────┐  │
│  │  │ ☐ Part 157    │  │  │                                            │  │
│  │  │   미설정       │  │  │    ┌─────────────────────────┐  총 두께   │  │
│  │  └────────────────┘  │  │    │░░░░░░░ PSA0 ░░░░░░░░░░░│  0.035    │  │
│  │                      │  │    ├─────────────────────────┤            │  │
│  │  [전체선택][전체해제]│  │    │▓▓▓▓▓▓▓▓ PL ▓▓▓▓▓▓▓▓▓▓▓▓│  0.080    │  │
│  │                      │  │    └─────────────────────────┘            │  │
│  └──────────────────────┘  │                                            │  │
│                            │    합계: 0.115 mm                          │  │
│                            └────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Actions ────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │  [ 📝 스크립트 생성 ]  [ 👁 미리보기 ]  [ ▶ KooMeshModifier 실행 ]  │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─ Log ────────────────────────────────────────────────────────────────┐  │
│  │ 10:30:15  ✓ K파일 로드 완료: 4 parts found                          │  │
│  │ 10:30:20  ✓ 스크립트 생성: B5_display.txt                           │  │
│  │ 10:30:21  ▶ KooMeshModifier 실행 중...                              │  │
│  │ 10:30:22    Processing Part 35...                                    │  │
│  │ 10:30:23    Processing Part 44... Done                               │  │
│  │                                                            [지우기]  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Ready                                              🌙 Dark   v1.0.0       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 적층 시각화 (Layer Preview)

레이어를 **실제 두께 비율**로 시각화:

```
┌─ Layer Preview ─────────────────────────────┐
│                                             │
│   TOP (바깥쪽)                              │
│   ┌───────────────────────────────┐         │
│   │▒▒▒▒▒▒▒▒▒ Panel ▒▒▒▒▒▒▒▒▒▒▒▒▒▒│ 0.030   │  ← 각 레이어 색상 구분
│   ├───────────────────────────────┤         │
│   │░░░░░░░░░ PSA2 ░░░░░░░░░░░░░░░│ 0.050   │  ← 두께에 비례한 높이
│   ├───────────────────────────────┤         │
│   │▓▓▓▓▓▓▓▓▓ POL ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ 0.031   │
│   ├───────────────────────────────┤         │
│   │░░░░░░░░░ PSA1 ░░░░░░░░░░░░░░░│ 0.050   │  ← 같은 층구분은 같은 색
│   ├───────────────────────────────┤         │
│   │████████ FTG_F ███████████████│ 0.031   │
│   └───────────────────────────────┘         │
│   BOTTOM (안쪽)                             │
│                                             │
│   총 두께: 0.192 mm                         │
│   레이어: 5개 (병합 후 5개)                 │
│                                             │
└─────────────────────────────────────────────┘
```

**시각화 특징:**
- 재료 타입별 색상 (Elastic: 파랑, Viscoelastic: 초록, PSA류: 회색)
- 같은 층구분 번호는 점선 테두리로 병합 표시
- 호버 시 상세 물성 툴팁
- 실시간 업데이트

---

## 프로젝트 구조

```
LaminateModeller/
├── gui/
│   ├── __init__.py
│   ├── main.py                 # 애플리케이션 진입점
│   ├── main_window.py          # 메인 윈도우
│   ├── styles/
│   │   ├── __init__.py
│   │   ├── theme.py            # 다크/라이트 테마 정의
│   │   └── dark_theme.qss      # Qt 스타일시트
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── file_input.py       # 파일 경로 입력 위젯
│   │   ├── part_card.py        # Part 카드 위젯
│   │   ├── part_list.py        # Part 목록 컨테이너
│   │   ├── layer_table.py      # 레이어 편집 테이블
│   │   ├── layer_preview.py    # 적층 시각화 위젯 ★
│   │   └── log_viewer.py       # 로그 출력 위젯
│   └── dialogs/
│       ├── __init__.py
│       ├── settings_dialog.py  # 설정 다이얼로그
│       └── preview_dialog.py   # 스크립트 미리보기
├── core/
│   ├── __init__.py
│   ├── k_file_parser.py        # K파일 Part ID 파서
│   ├── material_db.py          # MaterialSource 로더 (기존 코드 활용)
│   ├── script_generator.py     # display.txt 생성기
│   ├── config_manager.py       # 설정 관리
│   └── executor.py             # KooMeshModifier 실행기
├── models/
│   ├── __init__.py
│   ├── part.py                 # Part 데이터 모델
│   └── layer.py                # Layer 데이터 모델
├── resources/
│   └── icons/                  # 아이콘 리소스 (선택)
├── config/
│   └── settings.json           # 사용자 설정 저장
├── requirements.txt
├── run_gui.sh                  # Linux 실행
├── run_gui.bat                 # Windows 실행
└── README.md
```

---

## 개발 Phase

### Phase 1: 환경 설정 및 기본 프레임
**목표**: 개발 환경 + 다크테마 메인 윈도우

- [ ] Python venv 가상환경 생성
- [ ] PySide6, qtawesome 설치
- [ ] 프로젝트 디렉토리 구조 생성
- [ ] 다크 테마 스타일시트 (QSS) 작성
- [ ] 메인 윈도우 기본 레이아웃 (카드 기반)
- [ ] 설정 파일 관리 클래스

**결과물**: 다크테마가 적용된 빈 메인 윈도우

---

### Phase 2: 파일 로딩 기능
**목표**: K파일 파싱 + Material 로딩

- [ ] 파일 입력 위젯 (경로 + 찾아보기 버튼)
- [ ] K파일 파서 구현 (`*PART` 키워드에서 PID 추출)
- [ ] MaterialSource.txt 로더 (기존 코드 모듈화)
- [ ] Part 카드 위젯 (체크박스 + 레이어 개수)
- [ ] Part 목록 컨테이너 (스크롤 가능)

**K파일 파싱 로직**:
```python
# LS-DYNA *PART 형식
# *PART
# title
# pid, secid, mid, eosid, hgid, grav, adpopt, tmid

# 또는 *PART_TITLE 형식
```

**결과물**: K파일 로드 → Part 목록 표시

---

### Phase 3: 레이어 편집기
**목표**: 직관적인 적층 구성 편집

- [ ] 레이어 테이블 위젯 (QTableWidget 커스텀)
- [ ] Material 콤보박스 (MaterialSource에서 로드)
- [ ] 두께 입력 (SpinBox, 소수점 3자리)
- [ ] 층구분 입력 (같은 번호 = 병합)
- [ ] 레이어 추가/삭제 버튼
- [ ] 드래그 앤 드롭으로 순서 변경
- [ ] 복사/붙여넣기 기능 (Part 간)

**결과물**: Part 선택 → 레이어 편집 가능

---

### Phase 4: 적층 시각화 ★
**목표**: 레이어 구성을 실시간 시각화

- [ ] LayerPreviewWidget 구현 (QPainter 커스텀 드로잉)
- [ ] 두께 비율에 따른 높이 계산
- [ ] 재료 타입별 색상 매핑
- [ ] 같은 층구분 병합 표시 (점선 테두리)
- [ ] 호버 시 툴팁 (재료명, 두께, 물성)
- [ ] 레이어 편집 시 실시간 업데이트

**색상 매핑**:
```python
MATERIAL_COLORS = {
    'ELASTIC': '#3b82f6',      # Blue
    'VISCOELASTIC': '#10b981', # Green
    'ELASTOPLASTIC': '#f59e0b', # Orange
    'PSA': '#6b7280',          # Gray (PSA류)
}
```

**결과물**: 레이어 편집 → 즉시 시각화 반영

---

### Phase 5: 스크립트 생성
**목표**: B5_display.txt 형식 출력

- [ ] 기존 `dyna_material_generator.py` 로직 모듈화
- [ ] UI 데이터 → CSV 형식 → display.txt 변환
- [ ] 미리보기 다이얼로그 (구문 강조)
- [ ] 파일 저장 기능
- [ ] 생성 성공/실패 피드백

**결과물**: [스크립트 생성] 버튼 → display.txt 파일 생성

---

### Phase 6: KooMeshModifier 실행
**목표**: 외부 프로그램 실행 + 실시간 로그

- [ ] 설정에서 KooMeshModifier 경로 관리
- [ ] QProcess로 프로그램 실행
- [ ] stdout/stderr 실시간 캡처
- [ ] 로그 뷰어 (타임스탬프, 색상 구분)
- [ ] 실행 중 버튼 비활성화 + 스피너
- [ ] 실행 완료/실패 알림

**실행 방식**:
```python
# Linux:  ./KooMeshModifier/run.sh B5_display.txt
# Windows: KooMeshModifier\run.bat B5_display.txt
```

**결과물**: [실행] 버튼 → 로그 실시간 출력

---

### Phase 7: 편의 기능 및 마무리
**목표**: 사용성 개선

- [ ] 설정 다이얼로그 (경로, 테마)
- [ ] 다크/라이트 테마 토글
- [ ] 최근 파일 목록
- [ ] 프로젝트 저장/불러오기 (.laminate JSON)
- [ ] 키보드 단축키 (Ctrl+S, Ctrl+O 등)
- [ ] 상태바 메시지
- [ ] 에러 핸들링 개선

---

### Phase 8: 테스트 및 배포
**목표**: 크로스플랫폼 검증

- [ ] Linux 환경 테스트
- [ ] Windows 환경 테스트
- [ ] 엣지 케이스 처리
- [ ] README 작성
- [ ] (선택) PyInstaller 실행파일 생성

---

## 데이터 모델

### Part
```python
@dataclass
class PartConfig:
    part_id: int
    enabled: bool = False
    layers: List[LayerConfig] = field(default_factory=list)
```

### Layer
```python
@dataclass
class LayerConfig:
    material_name: str
    thickness: float      # mm
    layer_set: int        # 같은 번호 = 병합
```

### 프로젝트 저장 형식
```json
{
  "version": "1.0",
  "k_file": "/path/to/model.k",
  "material_source": "/path/to/MaterialSource.txt",
  "output_name": "B5",
  "parts": [
    {
      "part_id": 44,
      "enabled": true,
      "layers": [
        {"material": "PL", "thickness": 0.080, "layer_set": 1},
        {"material": "PSA0", "thickness": 0.035, "layer_set": 2}
      ]
    }
  ]
}
```

---

## 의존성

```txt
# requirements.txt
PySide6>=6.5.0
qtawesome>=1.2.0
```

---

## 실행 스크립트

### Linux (run_gui.sh)
```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python -m gui.main
```

### Windows (run_gui.bat)
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python -m gui.main
```

---

## 핵심 UX 포인트

1. **원클릭 워크플로우**: K파일 로드 → Part 선택 → 레이어 편집 → 실행
2. **실시간 피드백**: 적층 시각화가 편집과 동시에 업데이트
3. **복사/붙여넣기**: 동일 구성을 여러 Part에 빠르게 적용
4. **에러 방지**: 잘못된 입력 즉시 경고, Material 자동완성
5. **다크 테마**: 눈의 피로 감소, 전문 소프트웨어 느낌

---

## 다음 단계

사용자 승인 후 **Phase 1**부터 순차적으로 구현을 시작합니다.

```
Phase 1: 환경 설정 + 다크테마 메인 윈도우
Phase 2: 파일 로딩 (K파일, Material)
Phase 3: 레이어 편집기
Phase 4: 적층 시각화 ★
Phase 5: 스크립트 생성
Phase 6: KooMeshModifier 실행
Phase 7: 편의 기능
Phase 8: 테스트/배포
```
