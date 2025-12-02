# 모듈 개발 가이드

KooMesh Modeller의 모듈 개발을 위한 레퍼런스 문서입니다.

## 목차
1. [아키텍처 개요](#아키텍처-개요)
2. [디렉토리 구조](#디렉토리-구조)
3. [핵심 클래스](#핵심-클래스)
4. [새 모듈 만들기](#새-모듈-만들기)
5. [메소드가 있는 모듈 만들기](#메소드가-있는-모듈-만들기)
6. [공유 서비스](#공유-서비스)

---

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                        AppShell                              │
│  ┌──────────┐  ┌─────────────────────────────────────────┐  │
│  │ Sidebar  │  │            ContentStack                  │  │
│  │          │  │  ┌─────────────────────────────────┐    │  │
│  │ ▶ 모듈1  │  │  │         HomeScreen              │    │  │
│  │   └ 메소드│  │  │         (모듈 카드 목록)         │    │  │
│  │ ▶ 모듈2  │  │  ├─────────────────────────────────┤    │  │
│  │          │  │  │      Module (BaseModule)        │    │  │
│  │          │  │  │  ┌──────────────────────────┐   │    │  │
│  │          │  │  │  │   Method (StackedWidget) │   │    │  │
│  │          │  │  │  └──────────────────────────┘   │    │  │
│  └──────────┘  └─────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                     LogViewer                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 흐름
1. 앱 시작 → `AppShell` 생성 → `load_modules()` 호출
2. `ModuleRegistry`에 등록된 모듈들이 사이드바/홈에 표시
3. 사용자가 모듈 선택 → `_switch_to_module()` 또는 `_switch_to_method()`
4. 모듈 인스턴스 생성 (캐시됨) → `on_activate()` 호출

---

## 디렉토리 구조

```
gui/
├── main.py              # 진입점
├── shell.py             # AppShell (메인 컨테이너)
├── sidebar.py           # 계층적 사이드바
├── home_screen.py       # 홈 화면
├── app_context.py       # 공유 상태/서비스
├── modules/
│   ├── __init__.py      # ModuleRegistry, ModuleInfo, MethodInfo
│   ├── base.py          # BaseModule 추상 클래스
│   ├── advanced_laminate/
│   │   ├── __init__.py  # 모듈 등록
│   │   ├── module.py    # AdvancedLaminateModule
│   │   ├── widgets/     # 모듈 전용 위젯
│   │   └── core/        # 모듈 전용 로직
│   └── advanced_contact/
│       ├── __init__.py  # 모듈 등록 (methods 포함)
│       ├── module.py    # AdvancedContactModule
│       ├── methods/
│       │   ├── __init__.py  # CONTACT_METHODS 딕셔너리
│       │   ├── base.py      # BaseContactMethod
│       │   └── remove_duplicate_tied.py
│       └── widgets/
├── widgets/             # 공용 위젯
├── dialogs/             # 다이얼로그
└── styles/              # 테마/스타일
```

---

## 핵심 클래스

### ModuleRegistry (`gui/modules/__init__.py`)

모듈 자동 등록 및 관리 시스템.

```python
@dataclass
class MethodInfo:
    """메소드 메타데이터"""
    method_id: str      # 고유 ID (예: 'remove_duplicate_tied')
    name: str           # 표시 이름 (예: '중복 Tied 제거')
    icon: str           # qtawesome 아이콘 (예: 'fa5s.unlink')

@dataclass
class ModuleInfo:
    """모듈 메타데이터"""
    module_id: str      # 고유 ID (예: 'advanced_contact')
    name: str           # 표시 이름 (예: '접촉 고도화')
    description: str    # 홈 화면 카드 설명
    icon: str           # qtawesome 아이콘
    module_class: Type  # BaseModule 서브클래스
    order: int          # 정렬 순서 (낮을수록 위)
    methods: List[MethodInfo]  # 하위 메소드 (선택)
```

### BaseModule (`gui/modules/base.py`)

모든 모듈의 부모 클래스.

```python
class BaseModule(QWidget):
    # 시그널
    statusMessage = Signal(str)       # 상태바 메시지
    logMessage = Signal(str, str)     # 로그 (message, level)

    def __init__(self, ctx: AppContext, parent=None):
        self.ctx = ctx  # 공유 컨텍스트

    # 필수 구현
    @property
    @abstractmethod
    def module_id(self) -> str: ...

    @abstractmethod
    def _setup_ui(self): ...

    # 선택 구현
    def on_activate(self): ...      # 모듈 활성화 시
    def on_deactivate(self): ...    # 모듈 비활성화 시
    def get_actions(self) -> List[Dict]: ...  # 액션 버튼

    # 유틸리티
    def log(self, message: str, level: str = "info"): ...
    def status(self, message: str): ...
```

### AppContext (`gui/app_context.py`)

모듈 간 공유 데이터 및 서비스.

```python
@dataclass
class AppContext:
    # 서비스
    config: ConfigManager
    material_db: MaterialDatabase
    k_parser: KFileParser

    # 공유 상태
    current_k_file: str = ""
    current_material_file: str = ""
    current_project_path: str = ""

    # 메서드
    def load_materials(path: str) -> bool
    def load_k_file(path: str) -> bool
    def get_part_ids() -> List[int]
    def get_material_names() -> List[str]
```

---

## 새 모듈 만들기

### 타입 A: 단순 모듈 (하위 메소드 없음)

#### 1. 폴더 생성
```
gui/modules/my_module/
├── __init__.py
├── module.py
└── widgets/
    └── __init__.py
```

#### 2. module.py 작성
```python
"""My Module"""
from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtCore import Slot
from gui.modules.base import BaseModule


class MyModule(BaseModule):
    """내 새 모듈"""

    @property
    def module_id(self) -> str:
        return "my_module"

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Hello, Module!"))

    def on_activate(self):
        self.log("My Module 활성화", "info")
```

#### 3. __init__.py 작성 (등록)
```python
"""My Module"""
from gui.modules import ModuleRegistry
from .module import MyModule

ModuleRegistry.register(
    module_id="my_module",
    name="내 모듈",
    description="새로운 기능 모듈",
    icon="fa5s.star",      # https://fontawesome.com/v5/search
    order=10               # 정렬 순서
)(MyModule)
```

#### 4. load_modules()에 추가 (`gui/modules/__init__.py`)
```python
def load_modules():
    from . import advanced_laminate
    from . import advanced_contact
    from . import my_module  # 추가
```

---

## 메소드가 있는 모듈 만들기

### 타입 B: 메소드 기반 모듈 (사이드바 계층 구조)

사이드바에서 모듈 클릭 시 하위 메소드 목록이 펼쳐지는 구조.

#### 1. 폴더 구조
```
gui/modules/my_module/
├── __init__.py
├── module.py
├── methods/
│   ├── __init__.py
│   ├── base.py          # 메소드 베이스 클래스
│   ├── method_a.py
│   └── method_b.py
└── widgets/
    └── __init__.py
```

#### 2. methods/base.py (메소드 베이스)
```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from abc import abstractmethod

class BaseMyMethod(QWidget):
    logMessage = Signal(str, str)

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._setup_ui()

    @property
    @abstractmethod
    def method_id(self) -> str: ...

    @property
    @abstractmethod
    def method_name(self) -> str: ...

    @abstractmethod
    def _setup_ui(self): ...

    @abstractmethod
    def execute(self) -> bool: ...

    def validate(self) -> tuple:
        return True, ""

    def log(self, message: str, level: str = "info"):
        self.logMessage.emit(message, level)
```

#### 3. methods/method_a.py (구체 메소드)
```python
from PySide6.QtWidgets import QVBoxLayout, QLabel
from .base import BaseMyMethod

class MethodA(BaseMyMethod):
    @property
    def method_id(self) -> str:
        return "method_a"

    @property
    def method_name(self) -> str:
        return "Method A"

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Method A 옵션"))

    def execute(self) -> bool:
        self.log("Method A 실행", "info")
        return True
```

#### 4. methods/__init__.py (메소드 등록)
```python
from typing import Dict, Type
from .base import BaseMyMethod
from .method_a import MethodA
from .method_b import MethodB

MY_METHODS: Dict[str, Type[BaseMyMethod]] = {
    "method_a": MethodA,
    "method_b": MethodB,
}
```

#### 5. module.py (메인 모듈)
```python
from PySide6.QtWidgets import QVBoxLayout, QStackedWidget, QGroupBox
from gui.modules.base import BaseModule
from .methods import MY_METHODS

class MyModule(BaseModule):
    @property
    def module_id(self) -> str:
        return "my_module"

    def _setup_ui(self):
        self._method_widgets = {}
        self._current_method_id = None

        layout = QVBoxLayout(self)

        # 옵션 영역
        self.options_group = QGroupBox("옵션")
        options_layout = QVBoxLayout(self.options_group)

        # 메소드별 위젯 스택
        self.method_stack = QStackedWidget()
        for method_id, method_cls in MY_METHODS.items():
            widget = method_cls(self.ctx)
            widget.logMessage.connect(self.log)
            self._method_widgets[method_id] = widget
            self.method_stack.addWidget(widget)

        options_layout.addWidget(self.method_stack)
        layout.addWidget(self.options_group)

        # 첫 번째 메소드 선택
        if MY_METHODS:
            first = next(iter(MY_METHODS.keys()))
            self.select_method(first)

    def select_method(self, method_id: str):
        """사이드바에서 호출됨"""
        if method_id not in self._method_widgets:
            return
        self._current_method_id = method_id
        widget = self._method_widgets[method_id]
        self.method_stack.setCurrentWidget(widget)
        self.options_group.setTitle(f"옵션 - {widget.method_name}")
```

#### 6. __init__.py (모듈+메소드 등록)
```python
from gui.modules import ModuleRegistry
from .module import MyModule

ModuleRegistry.register(
    module_id="my_module",
    name="내 모듈",
    description="메소드 기반 모듈",
    icon="fa5s.cogs",
    order=5,
    methods=[
        {'id': 'method_a', 'name': 'Method A', 'icon': 'fa5s.cog'},
        {'id': 'method_b', 'name': 'Method B', 'icon': 'fa5s.wrench'},
    ]
)(MyModule)
```

---

## 공유 서비스

### core 패키지

| 클래스 | 설명 |
|--------|------|
| `ConfigManager` | 설정 저장/로드 (JSON) |
| `KFileParser` | LS-DYNA K파일 파싱 |
| `MaterialDatabase` | 재료 DB 관리 |
| `ScriptGenerator` | display.txt 스크립트 생성 |
| `ProcessExecutor` | 외부 프로세스 실행 (KooMeshModifier) |
| `DisplayParser` | display.txt 결과 파싱 |
| `PartConfigLoader` | CSV 파트 설정 로드 |

### models 패키지

| 클래스 | 설명 |
|--------|------|
| `PartConfig` | 파트 설정 데이터 |
| `LayerConfig` | 레이어 설정 데이터 |

### 사용 예시

```python
class MyModule(BaseModule):
    def _setup_ui(self):
        # K파일 로드
        if self.ctx.load_k_file("/path/to/model.k"):
            part_ids = self.ctx.get_part_ids()
            self.log(f"파트 {len(part_ids)}개 로드", "success")

        # 설정 접근
        koomesh_path = self.ctx.config.get("koomesh_path", "")

        # 재료 DB
        if self.ctx.load_materials("/path/to/MaterialSource.txt"):
            names = self.ctx.get_material_names()
```

---

## 로그 레벨

| 레벨 | 용도 | 색상 |
|------|------|------|
| `info` | 일반 정보 | 회색 |
| `success` | 성공 | 초록 |
| `warning` | 경고 | 노랑 |
| `error` | 오류 | 빨강 |
| `process` | 프로세스 실행 | 파랑 |

```python
self.log("작업 시작", "info")
self.log("완료!", "success")
self.log("주의 필요", "warning")
self.log("실패!", "error")
```

---

## 아이콘 참조

Font Awesome 5 Solid 아이콘 사용:
- 검색: https://fontawesome.com/v5/search?m=free&s=solid
- 사용법: `"fa5s.icon-name"` (예: `"fa5s.layer-group"`)

자주 사용하는 아이콘:
- `fa5s.cog` - 설정
- `fa5s.play` - 실행
- `fa5s.file-code` - 스크립트
- `fa5s.eye` - 미리보기
- `fa5s.folder-open` - 폴더
- `fa5s.save` - 저장
- `fa5s.trash` - 삭제
