# 모델 뷰어 & 키워드 관리 모듈 설계안

## 개요

K-file 파서로 읽은 LS-DYNA 모델을 3D로 시각화하고, 키워드를 편집/관리할 수 있는 GUI 모듈을 설계합니다.

---

## 모듈 구성

### 1. Model Viewer 모듈 (3D 뷰어)
**목적**: K-file의 노드/요소를 3D로 렌더링하여 시각화

### 2. Keyword Manager 모듈 (키워드 관리자)
**목적**: 파싱된 키워드를 트리 구조로 보여주고 편집/추가/삭제

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AppShell (기존)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌──────────────────────────────────────────────┐  │
│  │   Sidebar       │  │              Content Area                     │  │
│  │                 │  │  ┌─────────────────────────────────────────┐  │  │
│  │  📦 적층 고도화 │  │  │                                         │  │  │
│  │  🤝 접촉 고도화 │  │  │   Model Viewer Module                   │  │  │
│  │  ──────────────│  │  │   or                                     │  │  │
│  │  🎯 모델 뷰어  │  │  │   Keyword Manager Module                 │  │  │
│  │  📋 키워드관리 │  │  │                                         │  │  │
│  │                 │  │  └─────────────────────────────────────────┘  │  │
│  └─────────────────┘  └──────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 모듈 1: Model Viewer (모델 뷰어)

### UI 레이아웃

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Model Viewer                                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─ 파일 ──────────────────────────────────────────────────────────────┐│
│  │ K-File: [/path/to/model.k                            ] [열기] [로드]││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─ Part 목록 ─────────┐  ┌─ 3D View ─────────────────────────────────┐ │
│  │ ☑ All               │  │                                           │ │
│  │ ─────────────────── │  │                    ┌───┐                  │ │
│  │ ☑ Part 1 (Shell)    │  │                   /│   │\                 │ │
│  │ ☑ Part 2 (Solid)    │  │                  / │   │ \                │ │
│  │ ☐ Part 3 (Beam)     │  │                 /  │   │  \               │ │
│  │ ☑ Part 4 (Shell)    │  │                /   └───┘   \              │ │
│  │ ...                  │  │               ─────────────              │ │
│  │                      │  │                                           │ │
│  │ [전체선택] [해제]    │  │  Rotate: 드래그 | Zoom: 스크롤 | Pan: Shift+드래그 │
│  └──────────────────────┘  └───────────────────────────────────────────┘ │
│                                                                          │
│  ┌─ 정보 ───────────────────────────────────────────────────────────────┐│
│  │ Nodes: 29,624 | Elements: 44,657 | Parts: 22 | 파싱 시간: 26ms      ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─ 뷰 옵션 ────────────────────────────────────────────────────────────┐│
│  │ [와이어프레임] [솔리드] [노드표시] [요소ID] | 색상: [Part별▼]        ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 클래스 구조

```python
# gui/modules/model_viewer/
├── __init__.py
├── module.py              # ModelViewerModule (BaseModule 상속)
├── widgets/
│   ├── __init__.py
│   ├── gl_widget.py       # OpenGL 3D 렌더링 위젯
│   ├── part_tree.py       # Part 목록 트리 위젯
│   └── view_controls.py   # 뷰 옵션 컨트롤
└── core/
    ├── __init__.py
    ├── mesh_data.py       # 메쉬 데이터 구조
    ├── renderer.py        # OpenGL 렌더러
    └── camera.py          # 카메라 컨트롤
```

### 핵심 클래스

```python
# module.py
@ModuleRegistry.register(
    module_id="model_viewer",
    name="모델 뷰어",
    description="K-file 3D 시각화",
    icon="fa5s.cube",
    order=10
)
class ModelViewerModule(BaseModule):
    """3D 모델 뷰어 모듈"""

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(ctx, parent)
        self._parsed_model = None  # ParsedKFile

    def _setup_ui(self):
        # 파일 입력
        # Part 트리
        # 3D 뷰어 (QOpenGLWidget)
        # 정보 패널
        # 뷰 옵션
        pass

    def load_model(self, k_file_path: str):
        """K-file 로드 및 3D 렌더링"""
        from core.KooDynaKeyword import KFileReader
        reader = KFileReader(k_file_path)
        self._parsed_model = reader
        self._update_3d_view()


# widgets/gl_widget.py
class ModelGLWidget(QOpenGLWidget):
    """OpenGL 기반 3D 렌더링 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nodes = []       # [(x, y, z), ...]
        self._elements = []    # [(n1, n2, n3, n4), ...]
        self._parts = {}       # {part_id: [element_indices]}
        self._visible_parts = set()

        # 카메라
        self._camera = Camera()

    def set_mesh_data(self, nodes, elements, parts):
        """메쉬 데이터 설정"""
        pass

    def set_visible_parts(self, part_ids: set):
        """표시할 Part 설정"""
        pass

    def paintGL(self):
        """OpenGL 렌더링"""
        pass

    # 마우스 이벤트 (회전, 줌, 팬)
    def mousePressEvent(self, event): pass
    def mouseMoveEvent(self, event): pass
    def wheelEvent(self, event): pass
```

### 기술 스택 옵션

| 옵션 | 라이브러리 | 장점 | 단점 |
|------|-----------|------|------|
| **A. PyOpenGL** | QOpenGLWidget + PyOpenGL | 가볍고 직접 제어 | 직접 셰이더 작성 필요 |
| **B. PyVista** | pyvista + pyvistaqt | 고수준 API, 쉬운 사용 | 의존성 많음 |
| **C. VTK** | vtk + QVTKRenderWindowInteractor | 강력한 시각화 | 무거움, 복잡 |
| **D. vispy** | vispy.scene | 빠르고 현대적 | 학습 곡선 |

**권장: PyOpenGL (옵션 A)** - 가볍고 PySide6와 잘 통합됨

---

## 모듈 2: Keyword Manager (키워드 관리자)

### UI 레이아웃

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Keyword Manager                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─ 파일 ──────────────────────────────────────────────────────────────┐│
│  │ K-File: [/path/to/model.k                            ] [열기] [로드]││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─ 키워드 트리 ────────┐  ┌─ 키워드 상세 ─────────────────────────────┐│
│  │ 📁 Nodes (29,624)    │  │                                           ││
│  │ 📁 Elements          │  │  *PART                                    ││
│  │   ├─ Shell (0)       │  │  ──────────────────────────────────────   ││
│  │   ├─ Solid (44,657)  │  │  Title: Front_Panel                       ││
│  │   └─ Beam (0)        │  │  PID: 35                                   ││
│  │ 📁 Parts (22)        │  │  SID: 1                                    ││
│  │   ├─ Part 35 ◀──────┼──│  MID: 1                                    ││
│  │   ├─ Part 36         │  │  EOSID: 0                                  ││
│  │   └─ ...             │  │  HGID: 0                                   ││
│  │ 📁 Materials (6)     │  │                                           ││
│  │ 📁 Sections (23)     │  │  [수정] [복사] [삭제]                      ││
│  │ 📁 Contacts (27)     │  │                                           ││
│  │ 📁 Sets (53)         │  └───────────────────────────────────────────┘│
│  │ 📁 Controls          │                                               │
│  │   ├─ TERMINATION (1) │  ┌─ 미리보기 (K-file 형식) ─────────────────┐│
│  │   ├─ TIMESTEP (1)    │  │ *PART                                     ││
│  │   └─ ...             │  │ Front_Panel                               ││
│  │ 📁 Databases         │  │        35         1         1         0...││
│  │ 📁 Boundaries        │  │                                           ││
│  │ 📁 Loads             │  │                                           ││
│  │ 📁 Initial           │  └───────────────────────────────────────────┘│
│  │ 📁 Constrained       │                                               │
│  │                      │                                               │
│  │ [새 키워드 추가]      │                                               │
│  └──────────────────────┘                                               │
│                                                                          │
│  ┌─ 액션 ───────────────────────────────────────────────────────────────┐│
│  │ [K-file 내보내기] [선택 항목 내보내기] [검증]                        ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 클래스 구조

```python
# gui/modules/keyword_manager/
├── __init__.py
├── module.py              # KeywordManagerModule (BaseModule 상속)
├── widgets/
│   ├── __init__.py
│   ├── keyword_tree.py    # 키워드 트리 위젯
│   ├── keyword_detail.py  # 키워드 상세 편집 패널
│   ├── keyword_preview.py # K-file 형식 미리보기
│   └── add_keyword_dialog.py  # 새 키워드 추가 다이얼로그
└── core/
    ├── __init__.py
    ├── keyword_model.py   # 키워드 데이터 모델
    └── kfile_writer.py    # K-file 내보내기
```

### 핵심 클래스

```python
# module.py
@ModuleRegistry.register(
    module_id="keyword_manager",
    name="키워드 관리",
    description="K-file 키워드 편집/관리",
    icon="fa5s.list-alt",
    order=11,
    methods=[
        {'id': 'browse', 'name': '키워드 탐색', 'icon': 'fa5s.search'},
        {'id': 'edit', 'name': '키워드 편집', 'icon': 'fa5s.edit'},
        {'id': 'export', 'name': 'K-file 내보내기', 'icon': 'fa5s.file-export'},
    ]
)
class KeywordManagerModule(BaseModule):
    """키워드 관리 모듈"""

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(ctx, parent)
        self._keyword_model = None  # KeywordModel

    def _setup_ui(self):
        # 파일 입력
        # 키워드 트리
        # 상세 편집 패널
        # 미리보기
        # 액션 버튼
        pass

    def load_model(self, k_file_path: str):
        """K-file 로드"""
        from core.KooDynaKeyword import KFileReader
        reader = KFileReader(k_file_path,
            parse_nodes=True,
            parse_elements=True,
            parse_parts=True,
            parse_materials=True,
            parse_sections=True,
            parse_contacts=True,
            parse_sets=True,
            parse_controls=True,
            parse_databases=True,
            parse_boundaries=True,
            parse_loads=True,
            parse_initials=True,
            parse_constraineds=True
        )
        self._keyword_model = KeywordModel.from_reader(reader)
        self._update_tree()


# widgets/keyword_tree.py
class KeywordTreeWidget(QTreeWidget):
    """키워드 계층 트리"""

    itemSelected = Signal(str, object)  # (keyword_type, keyword_data)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["키워드", "개수"])

    def set_model(self, keyword_model: KeywordModel):
        """키워드 모델로 트리 구성"""
        self.clear()

        # 카테고리별 루트 노드
        categories = [
            ("nodes", "Nodes", "fa5s.dot-circle"),
            ("elements", "Elements", "fa5s.th"),
            ("parts", "Parts", "fa5s.cubes"),
            ("materials", "Materials", "fa5s.palette"),
            ("sections", "Sections", "fa5s.layer-group"),
            ("contacts", "Contacts", "fa5s.handshake"),
            ("sets", "Sets", "fa5s.object-group"),
            ("controls", "Controls", "fa5s.sliders-h"),
            ("databases", "Databases", "fa5s.database"),
            ("boundaries", "Boundaries", "fa5s.border-style"),
            ("loads", "Loads", "fa5s.arrow-down"),
            ("initials", "Initial", "fa5s.play-circle"),
            ("constraineds", "Constrained", "fa5s.lock"),
        ]

        for cat_id, cat_name, icon in categories:
            items = keyword_model.get_items(cat_id)
            root = QTreeWidgetItem([f"{cat_name} ({len(items)})", ""])
            # ... 하위 항목 추가


# widgets/keyword_detail.py
class KeywordDetailWidget(QWidget):
    """키워드 상세 편집 패널"""

    keywordModified = Signal(str, object)  # (keyword_type, modified_data)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_type = None
        self._current_data = None
        self._editors = {}  # {field_name: editor_widget}

    def set_keyword(self, keyword_type: str, keyword_data):
        """키워드 데이터 표시/편집"""
        self._current_type = keyword_type
        self._current_data = keyword_data
        self._build_editors()

    def _build_editors(self):
        """키워드 타입에 맞는 편집기 생성"""
        # 동적으로 필드별 편집기 생성
        # Part: PID, SID, MID, Title 등
        # Material: MID, RO, E, PR 등
        pass


# core/keyword_model.py
class KeywordModel:
    """키워드 데이터 모델 (편집 가능)"""

    def __init__(self):
        self._data = {
            'nodes': [],
            'elements': {'shell': [], 'solid': [], 'beam': []},
            'parts': [],
            'materials': [],
            'sections': [],
            'contacts': [],
            'sets': [],
            'controls': {},
            'databases': {},
            'boundaries': {},
            'loads': {},
            'initials': {},
            'constraineds': {},
        }
        self._modified = set()  # 수정된 키워드 추적

    @classmethod
    def from_reader(cls, reader: 'KFileReader') -> 'KeywordModel':
        """KFileReader에서 모델 생성"""
        model = cls()
        model._data['nodes'] = list(reader.get_nodes())
        model._data['parts'] = list(reader.get_parts())
        # ... 나머지 데이터 로드
        return model

    def get_items(self, category: str) -> list:
        """카테고리별 항목 조회"""
        return self._data.get(category, [])

    def update_item(self, category: str, item_id: int, data: dict):
        """항목 수정"""
        # 수정 로직
        self._modified.add((category, item_id))

    def add_item(self, category: str, data: dict):
        """새 항목 추가"""
        pass

    def delete_item(self, category: str, item_id: int):
        """항목 삭제"""
        pass


# core/kfile_writer.py
class KFileWriter:
    """K-file 내보내기"""

    def __init__(self, keyword_model: KeywordModel):
        self._model = keyword_model

    def write(self, output_path: str):
        """전체 K-file 내보내기"""
        with open(output_path, 'w') as f:
            f.write("$ Generated by KooMesh Modeller\n")
            f.write("*KEYWORD\n")

            self._write_nodes(f)
            self._write_elements(f)
            self._write_parts(f)
            # ... 나머지 키워드

            f.write("*END\n")

    def _write_nodes(self, f):
        """*NODE 키워드 출력"""
        nodes = self._model.get_items('nodes')
        if nodes:
            f.write("*NODE\n")
            for node in nodes:
                f.write(f"{node.id:8d}{node.x:16.8f}{node.y:16.8f}{node.z:16.8f}\n")
```

---

## 공유 컴포넌트

### AppContext 확장

```python
# gui/app_context.py
@dataclass
class AppContext:
    # 기존 필드...

    # 새 필드: 현재 로드된 K-file 모델 (모듈 간 공유)
    current_model: Optional['KeywordModel'] = None

    def load_k_file(self, path: str) -> bool:
        """K-file 로드 (공유 모델)"""
        try:
            reader = KFileReader(path, parse_all=True)
            self.current_model = KeywordModel.from_reader(reader)
            self.current_k_file = path
            return True
        except Exception as e:
            return False
```

---

## 개발 우선순위

### Phase 1: 기본 인프라 (1-2일)
1. [ ] 모듈 디렉토리 구조 생성
2. [ ] KeywordModel 기본 클래스 구현
3. [ ] ModuleRegistry에 새 모듈 등록

### Phase 2: Keyword Manager (3-4일)
1. [ ] KeywordTreeWidget 구현
2. [ ] KeywordDetailWidget 구현 (읽기 전용)
3. [ ] K-file 미리보기
4. [ ] 기본 내보내기 기능

### Phase 3: Model Viewer (4-5일)
1. [ ] PyOpenGL 기반 GLWidget
2. [ ] 메쉬 렌더링 (와이어프레임)
3. [ ] 카메라 컨트롤 (회전/줌/팬)
4. [ ] Part 표시/숨기기
5. [ ] 솔리드 렌더링

### Phase 4: 고급 기능 (2-3일)
1. [ ] 키워드 편집 기능
2. [ ] 새 키워드 추가
3. [ ] 검증 기능
4. [ ] Part별 색상

---

## 기술 요구사항

### 새 의존성

```txt
# requirements.txt 추가
PyOpenGL>=3.1.0          # OpenGL 바인딩
PyOpenGL-accelerate>=3.1.0  # 성능 향상 (선택)
numpy>=1.20.0            # 벡터/행렬 연산
```

### 호환성
- Python 3.8+
- PySide6 6.5+
- OpenGL 3.3+ (대부분의 시스템에서 지원)

---

## 결론

두 모듈 모두 기존 아키텍처(BaseModule, ModuleRegistry)를 따르며,
K-file 파서(core/kfile_parser)를 활용하여 데이터를 시각화/편집합니다.

**권장 개발 순서:**
1. **Keyword Manager 먼저** - 3D 렌더링 없이 트리/편집 UI만 필요
2. **Model Viewer 나중에** - OpenGL 렌더링 복잡도가 높음

이 설계로 진행할까요?
