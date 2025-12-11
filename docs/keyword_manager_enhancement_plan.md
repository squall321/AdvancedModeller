# Keyword Manager 기능 확장 계획

## 개요

Keyword Manager 모듈에 다음 4가지 주요 기능을 추가합니다:
1. K-file Export 기능 개선
2. 키워드 추가/삭제 기능
3. 복사/붙여넣기 기능
4. Undo/Redo 기능

---

## 1. K-file Export 기능 개선

### 현재 상태
- `KeywordModel.export_kfile()`에서 기본적인 키워드만 출력
- Section, Material 등의 상세 필드들이 Card 정의와 일치하지 않음
- 원본 파일의 순서와 주석이 유지되지 않음

### 목표
- 모든 키워드를 Card 정의(`KEYWORD_CARDS`)에 맞춰 완전히 출력
- 원본 파일 구조 최대한 유지
- Include 파일 처리 지원

### 구현 계획

#### 1.1 Export 유틸리티 클래스 생성
```
gui/modules/keyword_manager/core/kfile_exporter.py
```

```python
class KFileExporter:
    """K-file 형식으로 내보내는 유틸리티"""

    def __init__(self, model: ParsedModelData):
        self._model = model
        self._card_defs = KEYWORD_CARDS  # 카드 정의 참조

    def export(self, filepath: str) -> bool:
        """전체 모델 내보내기"""

    def export_keyword(self, category: str, item: Any) -> List[str]:
        """단일 키워드를 K-file 형식 문자열로 변환"""

    def _format_field(self, value: Any, field_def: FieldDef) -> str:
        """필드를 K-file 고정폭 형식으로 포맷"""
```

#### 1.2 카테고리별 Export 메서드 구현

| 카테고리 | 출력 형식 | 구현 복잡도 |
|---------|----------|------------|
| NODE | `{nid:8d}{x:16.8f}{y:16.8f}{z:16.8f}` | 낮음 |
| ELEMENT_SHELL | `{eid:8d}{pid:8d}{n1:8d}...{n4:8d}` | 낮음 |
| ELEMENT_SOLID | EID/PID + 8 nodes (2줄) | 중간 |
| PART | Title + Card 2 (8 fields) | 중간 |
| SECTION_SHELL | Card 1 (8 fields) + Card 2 (8 fields) | 중간 |
| MAT_* | keyword_type별 다른 카드 구조 | 높음 |
| CONTACT_* | 3-4개 Card | 중간 |
| SET_* | Header + Members (8개씩) | 중간 |
| CONTROL_* | 단일 Card | 낮음 |
| DATABASE_* | 단일 Card | 낮음 |
| BOUNDARY_* | 단일 Card | 낮음 |
| LOAD_* | 단일 Card | 낮음 |
| INITIAL_* | 1-2개 Card | 낮음 |
| CONSTRAINED_* | 1-2개 Card | 낮음 |

#### 1.3 고정폭 포맷터 구현
```python
def _format_field(self, value: Any, field_def: FieldDef) -> str:
    """K-file 고정폭 형식으로 포맷"""
    width = field_def.width
    field_type = field_def.field_type

    if field_type == 'int':
        return f"{int(value):>{width}d}"
    elif field_type == 'float':
        # 숫자 크기에 따라 과학적 표기법 또는 소수점 표기
        if width >= 16:
            return f"{float(value):>{width}.8f}"
        elif abs(value) > 1e6 or (abs(value) < 1e-4 and value != 0):
            return f"{float(value):>{width}.4e}"
        else:
            return f"{float(value):>{width}.4f}"
    else:  # str
        return f"{str(value):<{width}s}"[:width]
```

#### 1.4 파일 구조
```
$# LS-DYNA Keyword file exported by LaminateModeller
$# Original file: {original_filename}
$# Export date: {datetime}
*KEYWORD
*TITLE
{model_title}
$
$# ========== NODES ==========
*NODE
{node_data...}
$
$# ========== ELEMENTS ==========
*ELEMENT_SHELL
{shell_data...}
*ELEMENT_SOLID
{solid_data...}
$
$# ========== PARTS ==========
*PART
{part_data...}
$
... (카테고리별 섹션)
$
*END
```

### 예상 작업량
- **파일**: 1개 신규 (`kfile_exporter.py`)
- **수정**: `keyword_model.py` (export_kfile → KFileExporter 사용)
- **코드량**: ~400줄
- **난이도**: ★★★☆☆

---

## 2. 키워드 추가/삭제 기능

### 현재 상태
- 기존 키워드 편집만 가능
- 새 키워드 생성 불가
- 키워드 삭제 불가

### 목표
- 새 Node, Element, Part 등 추가
- 선택한 키워드 삭제
- ID 자동 생성 (최대 ID + 1)

### 구현 계획

#### 2.1 데이터 조작 클래스
```
gui/modules/keyword_manager/core/keyword_operations.py
```

```python
class KeywordOperations:
    """키워드 추가/삭제/복사 연산"""

    def __init__(self, model: KeywordModel):
        self._model = model
        self._undo_stack = UndoStack()  # Undo/Redo와 연동

    # === 추가 ===
    def add_node(self, x: float = 0, y: float = 0, z: float = 0) -> Node:
        """새 노드 추가 (자동 ID 생성)"""

    def add_element(self, elem_type: str, pid: int, nodes: List[int]) -> Element:
        """새 요소 추가"""

    def add_part(self, name: str = "", secid: int = 0, mid: int = 0) -> Part:
        """새 파트 추가"""

    def add_keyword(self, category: str, **kwargs) -> Any:
        """일반 키워드 추가"""

    # === 삭제 ===
    def delete_node(self, nid: int) -> bool:
        """노드 삭제 (참조 체크)"""

    def delete_element(self, eid: int) -> bool:
        """요소 삭제"""

    def delete_keyword(self, category: str, item: Any) -> bool:
        """일반 키워드 삭제"""

    # === ID 관리 ===
    def get_next_id(self, category: str) -> int:
        """다음 사용 가능한 ID 반환"""

    def check_references(self, category: str, item_id: int) -> List[str]:
        """해당 ID를 참조하는 항목 확인"""
```

#### 2.2 ID 자동 생성 로직
```python
def get_next_id(self, category: str) -> int:
    """다음 사용 가능한 ID"""
    items = self._model.get_items(category)
    if not items:
        return 1

    id_attr = {
        'nodes': 'nid',
        'shell': 'eid', 'solid': 'eid', 'beam': 'eid',
        'parts': 'pid',
        'materials': 'mid',
        'sections': 'secid',
        'sets': 'sid',
    }.get(category, 'id')

    max_id = max(getattr(item, id_attr, 0) for item in items)
    return max_id + 1
```

#### 2.3 참조 체크 로직 (삭제 전)
```python
def check_references(self, category: str, item_id: int) -> List[str]:
    """삭제 전 참조 체크"""
    refs = []

    if category == 'nodes':
        # 요소에서 참조 체크
        for elem in self._model.get_items('shell'):
            if item_id in getattr(elem, 'nodes', []):
                refs.append(f"Element {elem.eid}")
        # Set에서 참조 체크
        for set_item in self._model.get_items('sets'):
            if getattr(set_item, 'set_type', '') == 'NODE':
                if item_id in getattr(set_item, 'members', []):
                    refs.append(f"Set {set_item.sid}")

    elif category == 'parts':
        # 요소에서 참조 체크
        for elem in self._model.get_items('shell'):
            if getattr(elem, 'pid', 0) == item_id:
                refs.append(f"Element {elem.eid}")

    return refs
```

#### 2.4 UI 변경

**KeywordTreeWidget에 컨텍스트 메뉴 추가:**
```python
def _setup_context_menu(self):
    self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
    self._tree.customContextMenuRequested.connect(self._show_context_menu)

def _show_context_menu(self, pos):
    item = self._tree.itemAt(pos)
    data = item.data(0, Qt.UserRole) if item else None

    menu = QMenu(self)

    if data and data.get('type') == 'category':
        # 카테고리 선택 시
        add_action = menu.addAction("새 항목 추가")
        add_action.triggered.connect(lambda: self._add_new_item(data['id']))

    elif data and data.get('type') == 'item':
        # 개별 항목 선택 시
        delete_action = menu.addAction("삭제")
        delete_action.triggered.connect(lambda: self._delete_item(data))

        copy_action = menu.addAction("복사")
        copy_action.triggered.connect(lambda: self._copy_item(data))

    menu.exec_(self._tree.mapToGlobal(pos))
```

**KeywordManagerModule에 툴바 추가:**
```python
# 파일 섹션 아래에 툴바 추가
toolbar = QHBoxLayout()

add_btn = QPushButton(qta.icon('fa5s.plus'), " 추가")
add_btn.clicked.connect(self._add_keyword)
toolbar.addWidget(add_btn)

delete_btn = QPushButton(qta.icon('fa5s.trash'), " 삭제")
delete_btn.clicked.connect(self._delete_keyword)
toolbar.addWidget(delete_btn)

toolbar.addStretch()
layout.addLayout(toolbar)
```

#### 2.5 추가 다이얼로그
```
gui/modules/keyword_manager/dialogs/add_keyword_dialog.py
```

```python
class AddKeywordDialog(QDialog):
    """새 키워드 추가 다이얼로그"""

    def __init__(self, category: str, parent=None):
        super().__init__(parent)
        self._category = category
        self._setup_ui()

    def _setup_ui(self):
        # 카테고리별 필드 생성
        # Card 정의 기반으로 폼 생성
        pass

    def get_values(self) -> Dict[str, Any]:
        """입력된 값 반환"""
        pass
```

### 예상 작업량
- **파일**: 2개 신규 (`keyword_operations.py`, `add_keyword_dialog.py`)
- **수정**: `keyword_tree.py`, `module.py`
- **코드량**: ~500줄
- **난이도**: ★★★★☆

---

## 3. 복사/붙여넣기 기능

### 현재 상태
- 복사/붙여넣기 미지원
- 범위 선택 후 일괄 수정 불가

### 목표
- 키워드 복사 (새 ID로 붙여넣기)
- 다중 선택 지원
- 클립보드 연동 (K-file 텍스트 형식)

### 구현 계획

#### 3.1 클립보드 매니저
```
gui/modules/keyword_manager/core/clipboard_manager.py
```

```python
@dataclass
class ClipboardItem:
    """클립보드에 저장되는 항목"""
    category: str
    items: List[Any]
    source_ids: List[int]  # 원본 ID (참조용)

class KeywordClipboard:
    """키워드 클립보드 관리"""

    _instance = None  # 싱글톤

    def __init__(self):
        self._content: Optional[ClipboardItem] = None
        self._qt_clipboard = QApplication.clipboard()

    @classmethod
    def instance(cls) -> 'KeywordClipboard':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def copy(self, category: str, items: List[Any]):
        """항목 복사"""
        self._content = ClipboardItem(
            category=category,
            items=[self._deep_copy(item) for item in items],
            source_ids=[self._get_id(category, item) for item in items]
        )
        # K-file 형식으로 시스템 클립보드에도 복사
        kfile_text = self._to_kfile_text(category, items)
        self._qt_clipboard.setText(kfile_text)

    def paste(self, operations: KeywordOperations) -> List[Any]:
        """붙여넣기 (새 ID로)"""
        if not self._content:
            return []

        new_items = []
        for item in self._content.items:
            new_id = operations.get_next_id(self._content.category)
            new_item = operations.add_keyword(
                self._content.category,
                **self._item_to_dict(item, new_id)
            )
            new_items.append(new_item)

        return new_items

    def can_paste(self) -> bool:
        return self._content is not None

    def _deep_copy(self, item: Any) -> Any:
        """객체 깊은 복사"""
        import copy
        return copy.deepcopy(item)
```

#### 3.2 다중 선택 지원

**KeywordTreeWidget 수정:**
```python
def _setup_ui(self):
    # 다중 선택 활성화
    self._tree.setSelectionMode(QAbstractItemView.ExtendedSelection)

def get_selected_items(self) -> List[Tuple[str, Any]]:
    """선택된 모든 항목 반환"""
    selected = []
    for item in self._tree.selectedItems():
        data = item.data(0, Qt.UserRole)
        if data and data.get('type') == 'item':
            selected.append((data['category'], data['data']))
    return selected
```

#### 3.3 키보드 단축키

**KeywordManagerModule에 단축키 추가:**
```python
def _setup_shortcuts(self):
    # Ctrl+C: 복사
    copy_shortcut = QShortcut(QKeySequence.Copy, self)
    copy_shortcut.activated.connect(self._copy_selected)

    # Ctrl+V: 붙여넣기
    paste_shortcut = QShortcut(QKeySequence.Paste, self)
    paste_shortcut.activated.connect(self._paste_items)

    # Ctrl+D: 복제 (복사 + 즉시 붙여넣기)
    duplicate_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
    duplicate_shortcut.activated.connect(self._duplicate_selected)

    # Delete: 삭제
    delete_shortcut = QShortcut(QKeySequence.Delete, self)
    delete_shortcut.activated.connect(self._delete_selected)

def _copy_selected(self):
    selected = self._tree.get_selected_items()
    if selected:
        categories = set(cat for cat, _ in selected)
        if len(categories) == 1:
            category = categories.pop()
            items = [item for _, item in selected]
            KeywordClipboard.instance().copy(category, items)
            self.status(f"{len(items)}개 항목 복사됨")
        else:
            self.log("같은 카테고리의 항목만 복사할 수 있습니다", "warning")
```

#### 3.4 일괄 수정 기능

**범위 선택 후 일괄 수정:**
```python
class BatchEditDialog(QDialog):
    """범위 일괄 수정 다이얼로그"""

    def __init__(self, category: str, items: List[Any], parent=None):
        super().__init__(parent)
        self._category = category
        self._items = items
        self._setup_ui()

    def _setup_ui(self):
        # 공통 필드만 표시
        # 체크박스로 수정할 필드 선택
        # 값 입력 후 일괄 적용
        pass
```

### 예상 작업량
- **파일**: 2개 신규 (`clipboard_manager.py`, `batch_edit_dialog.py`)
- **수정**: `keyword_tree.py`, `module.py`
- **코드량**: ~400줄
- **난이도**: ★★★☆☆

---

## 4. Undo/Redo 기능

### 현재 상태
- 변경 이력 저장 안 함
- Undo/Redo 불가
- dirty flag만 존재

### 목표
- Command 패턴으로 모든 작업 기록
- Ctrl+Z/Ctrl+Y로 Undo/Redo
- 작업 이력 표시 (선택적)

### 구현 계획

#### 4.1 Command 패턴 구현
```
gui/modules/keyword_manager/core/undo_redo.py
```

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from collections import deque


class Command(ABC):
    """실행 취소 가능한 명령 기본 클래스"""

    @abstractmethod
    def execute(self) -> bool:
        """명령 실행"""
        pass

    @abstractmethod
    def undo(self) -> bool:
        """명령 취소"""
        pass

    @abstractmethod
    def description(self) -> str:
        """명령 설명 (UI 표시용)"""
        pass


@dataclass
class ModifyCommand(Command):
    """값 수정 명령"""
    category: str
    item: Any
    field_name: str
    old_value: Any
    new_value: Any

    def execute(self) -> bool:
        setattr(self.item, self.field_name, self.new_value)
        return True

    def undo(self) -> bool:
        setattr(self.item, self.field_name, self.old_value)
        return True

    def description(self) -> str:
        return f"수정: {self.category} {self.field_name}"


@dataclass
class AddCommand(Command):
    """항목 추가 명령"""
    category: str
    item: Any
    model: 'KeywordModel'

    def execute(self) -> bool:
        self.model._add_item(self.category, self.item)
        return True

    def undo(self) -> bool:
        self.model._remove_item(self.category, self.item)
        return True

    def description(self) -> str:
        return f"추가: {self.category}"


@dataclass
class DeleteCommand(Command):
    """항목 삭제 명령"""
    category: str
    item: Any
    model: 'KeywordModel'
    _index: int = -1  # 원래 위치 (복원용)

    def execute(self) -> bool:
        self._index = self.model._get_item_index(self.category, self.item)
        self.model._remove_item(self.category, self.item)
        return True

    def undo(self) -> bool:
        self.model._insert_item(self.category, self.item, self._index)
        return True

    def description(self) -> str:
        return f"삭제: {self.category}"


@dataclass
class BatchCommand(Command):
    """여러 명령을 하나로 묶음"""
    commands: List[Command] = field(default_factory=list)
    _description: str = "일괄 작업"

    def execute(self) -> bool:
        for cmd in self.commands:
            if not cmd.execute():
                return False
        return True

    def undo(self) -> bool:
        # 역순으로 취소
        for cmd in reversed(self.commands):
            if not cmd.undo():
                return False
        return True

    def description(self) -> str:
        return self._description


class UndoStack:
    """Undo/Redo 스택 관리"""

    def __init__(self, max_size: int = 100):
        self._undo_stack: deque[Command] = deque(maxlen=max_size)
        self._redo_stack: deque[Command] = deque(maxlen=max_size)
        self._is_executing: bool = False  # 재귀 방지

    def push(self, command: Command):
        """새 명령 추가 (실행 후)"""
        if self._is_executing:
            return

        self._undo_stack.append(command)
        self._redo_stack.clear()  # Redo 스택 초기화

    def undo(self) -> Optional[Command]:
        """실행 취소"""
        if not self._undo_stack:
            return None

        self._is_executing = True
        try:
            command = self._undo_stack.pop()
            if command.undo():
                self._redo_stack.append(command)
                return command
            else:
                # 실패 시 다시 스택에 넣기
                self._undo_stack.append(command)
                return None
        finally:
            self._is_executing = False

    def redo(self) -> Optional[Command]:
        """다시 실행"""
        if not self._redo_stack:
            return None

        self._is_executing = True
        try:
            command = self._redo_stack.pop()
            if command.execute():
                self._undo_stack.append(command)
                return command
            else:
                self._redo_stack.append(command)
                return None
        finally:
            self._is_executing = False

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def undo_description(self) -> str:
        """다음 Undo 작업 설명"""
        if self._undo_stack:
            return self._undo_stack[-1].description()
        return ""

    def redo_description(self) -> str:
        """다음 Redo 작업 설명"""
        if self._redo_stack:
            return self._redo_stack[-1].description()
        return ""

    def clear(self):
        """스택 초기화"""
        self._undo_stack.clear()
        self._redo_stack.clear()

    def get_history(self, limit: int = 10) -> List[str]:
        """최근 작업 이력"""
        return [cmd.description() for cmd in list(self._undo_stack)[-limit:]]
```

#### 4.2 KeywordModel 연동

**KeywordModel 수정:**
```python
class KeywordModel:
    def __init__(self, parsed_model=None):
        # 기존 코드...
        self._undo_stack = UndoStack()

    @property
    def undo_stack(self) -> UndoStack:
        return self._undo_stack

    def modify_value(self, category: str, item: Any,
                     field_name: str, new_value: Any):
        """값 수정 (Undo 지원)"""
        old_value = getattr(item, field_name, None)
        if old_value == new_value:
            return

        command = ModifyCommand(
            category=category,
            item=item,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value
        )
        command.execute()
        self._undo_stack.push(command)
        self.mark_modified(category, item)

    def _add_item(self, category: str, item: Any):
        """내부: 항목 추가"""
        # ParsedModelData의 캐시에 추가
        items = self._model._get_cache(category)
        if items is not None:
            items.append(item)

    def _remove_item(self, category: str, item: Any):
        """내부: 항목 제거"""
        items = self._model._get_cache(category)
        if items is not None and item in items:
            items.remove(item)
```

#### 4.3 CardEditor 연동

**KeywordCardEditor 수정:**
```python
def _on_card_value_changed(self, field_name: str, value):
    """Card 필드 값 변경 시 - Undo 지원"""
    if not self._current_item:
        return

    # KeywordModel을 통해 수정 (Undo 스택에 자동 추가)
    if hasattr(self._model, 'modify_value'):
        self._model.modify_value(
            self._current_category,
            self._current_item,
            field_name,
            value
        )
    else:
        # 기존 직접 수정 방식 (폴백)
        self._update_item_attribute(field_name, value)

    self._update_raw_preview()
    self.keywordModified.emit(self._current_category, self._current_item)
```

#### 4.4 UI 연동

**KeywordManagerModule 수정:**
```python
def _setup_ui(self):
    # 기존 코드...

    # Undo/Redo 버튼
    undo_btn = QPushButton(qta.icon('fa5s.undo'), "")
    undo_btn.setToolTip("실행 취소 (Ctrl+Z)")
    undo_btn.clicked.connect(self._undo)
    file_layout.addWidget(undo_btn)
    self._undo_btn = undo_btn

    redo_btn = QPushButton(qta.icon('fa5s.redo'), "")
    redo_btn.setToolTip("다시 실행 (Ctrl+Y)")
    redo_btn.clicked.connect(self._redo)
    file_layout.addWidget(redo_btn)
    self._redo_btn = redo_btn

    # 단축키
    QShortcut(QKeySequence.Undo, self, self._undo)
    QShortcut(QKeySequence.Redo, self, self._redo)

def _undo(self):
    if self._keyword_model.undo_stack.can_undo():
        cmd = self._keyword_model.undo_stack.undo()
        if cmd:
            self._refresh_view()
            self.status(f"취소: {cmd.description()}")

def _redo(self):
    if self._keyword_model.undo_stack.can_redo():
        cmd = self._keyword_model.undo_stack.redo()
        if cmd:
            self._refresh_view()
            self.status(f"다시 실행: {cmd.description()}")

def _update_undo_redo_buttons(self):
    """Undo/Redo 버튼 상태 업데이트"""
    stack = self._keyword_model.undo_stack

    self._undo_btn.setEnabled(stack.can_undo())
    self._undo_btn.setToolTip(
        f"실행 취소: {stack.undo_description()}" if stack.can_undo()
        else "실행 취소 (Ctrl+Z)"
    )

    self._redo_btn.setEnabled(stack.can_redo())
    self._redo_btn.setToolTip(
        f"다시 실행: {stack.redo_description()}" if stack.can_redo()
        else "다시 실행 (Ctrl+Y)"
    )
```

### 예상 작업량
- **파일**: 1개 신규 (`undo_redo.py`)
- **수정**: `keyword_model.py`, `keyword_card_editor.py`, `module.py`
- **코드량**: ~400줄
- **난이도**: ★★★★☆

---

## 구현 순서 및 의존성

```
┌─────────────────────────────────────────────────────────┐
│                    4. Undo/Redo                         │
│                    (Command 패턴)                        │
│                         ▲                               │
│                         │                               │
│     ┌───────────────────┴───────────────────┐          │
│     │                                        │          │
│     ▼                                        ▼          │
│ 2. 추가/삭제                           3. 복사/붙여넣기  │
│ (Operations)                          (Clipboard)       │
│     │                                        │          │
│     └───────────────────┬───────────────────┘          │
│                         │                               │
│                         ▼                               │
│               1. Export 개선                            │
│               (Exporter)                                │
└─────────────────────────────────────────────────────────┘
```

### 권장 구현 순서

| 순서 | 기능 | 이유 |
|-----|------|------|
| 1 | Export 개선 | 독립적, 기존 기능 개선 |
| 2 | Undo/Redo | 다른 기능의 기반 |
| 3 | 추가/삭제 | Undo/Redo 필요 |
| 4 | 복사/붙여넣기 | 추가/삭제 로직 재사용 |

---

## 파일 구조 (최종)

```
gui/modules/keyword_manager/
├── __init__.py
├── module.py                          # +Undo/Redo 버튼, 단축키
├── core/
│   ├── __init__.py
│   ├── keyword_model.py               # +Undo 연동
│   ├── kfile_exporter.py              # [신규] Export 유틸리티
│   ├── keyword_operations.py          # [신규] 추가/삭제 연산
│   ├── clipboard_manager.py           # [신규] 클립보드 관리
│   └── undo_redo.py                   # [신규] Command 패턴
├── widgets/
│   ├── __init__.py
│   ├── keyword_tree.py                # +컨텍스트 메뉴, 다중 선택
│   ├── keyword_detail.py
│   ├── keyword_preview.py
│   └── keyword_card_editor.py         # +Undo 연동
└── dialogs/
    ├── __init__.py                    # [신규]
    ├── add_keyword_dialog.py          # [신규] 추가 다이얼로그
    └── batch_edit_dialog.py           # [신규] 일괄 수정 다이얼로그
```

---

## 전체 예상 작업량

| 항목 | 신규 파일 | 수정 파일 | 코드량 | 난이도 |
|-----|----------|----------|-------|--------|
| 1. Export 개선 | 1 | 1 | ~400줄 | ★★★☆☆ |
| 2. 추가/삭제 | 2 | 2 | ~500줄 | ★★★★☆ |
| 3. 복사/붙여넣기 | 2 | 2 | ~400줄 | ★★★☆☆ |
| 4. Undo/Redo | 1 | 3 | ~400줄 | ★★★★☆ |
| **합계** | **6** | **8** | **~1,700줄** | |

---

## 테스트 계획

### 단위 테스트
```
tests/gui/modules/keyword_manager/
├── test_kfile_exporter.py
├── test_keyword_operations.py
├── test_clipboard_manager.py
└── test_undo_redo.py
```

### 통합 테스트 시나리오

1. **Export 테스트**
   - 빈 모델 Export
   - 모든 키워드 타입 Export
   - Export 후 다시 로드하여 비교

2. **추가/삭제 테스트**
   - 노드 추가 → ID 자동 생성 확인
   - 참조된 노드 삭제 시도 → 경고 확인
   - 삭제 후 Undo → 복원 확인

3. **복사/붙여넣기 테스트**
   - 단일 항목 복사/붙여넣기
   - 다중 항목 복사/붙여넣기
   - 다른 카테고리에 붙여넣기 시도 → 실패 확인

4. **Undo/Redo 테스트**
   - 값 수정 → Undo → Redo
   - 추가 → Undo → 삭제됨 확인
   - 삭제 → Undo → 복원 확인
   - 100개 이상 작업 후 스택 제한 확인

---

## 리스크 및 고려사항

### 기술적 리스크

1. **C++ 파서와의 호환성**
   - 파싱된 객체가 immutable일 수 있음
   - 해결: Python wrapper 수준에서 mutable 객체로 변환

2. **대용량 데이터 성능**
   - 수십만 노드 Undo 시 메모리 문제
   - 해결: Undo 스택 크기 제한, 차분(delta) 저장

3. **참조 무결성**
   - 노드 삭제 시 참조하는 요소 처리
   - 해결: 삭제 전 참조 체크, 연쇄 삭제 옵션

### UI/UX 고려사항

1. **일관된 피드백**
   - 모든 작업에 상태바 메시지
   - Undo 가능 여부 명확히 표시

2. **확인 다이얼로그**
   - 삭제 시 항상 확인
   - 대량 작업 시 미리보기

3. **단축키 충돌**
   - 시스템/Qt 기본 단축키와 충돌 확인
   - 사용자 정의 가능하게 설계

---

## 마일스톤

| 단계 | 기능 | 목표 |
|-----|------|------|
| M1 | Export 개선 | Card 정의 기반 완전한 Export |
| M2 | Undo/Redo | Command 패턴 기반 이력 관리 |
| M3 | 추가/삭제 | UI + 참조 체크 |
| M4 | 복사/붙여넣기 | 클립보드 + 일괄 수정 |
| M5 | 테스트 & 안정화 | 단위/통합 테스트 완료 |
