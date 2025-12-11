# Model Viewer & Keyword Manager 통합 계획

## 🎯 목표

**Keyword Manager ↔ Model Viewer 양방향 실시간 연동**

---

## 📋 통합 기능

### 1. Element Picking & Selection
- **마우스 클릭** → Element 선택
- **Ctrl + 클릭** → 다중 선택
- **선택 하이라이트** → 다른 색상으로 표시
- **Info Panel** → 선택 요소 상세 정보

### 2. 양방향 동기화
```
Keyword Manager              Model Viewer
      ↓                           ↓
 Part 선택 ────────────→    Part 하이라이트
      ↑                           ↑
Element 하이라이트 ←────── Element 선택
```

### 3. 실시간 업데이트
- Keyword 수정 → 3D 즉시 반영
- 3D 선택 → Keyword 트리 포커스

---

## 🔧 구현 방법

### Phase 1: Picking UI 통합 (1시간)

#### 1.1 Info Panel Widget 추가
```python
# gui/modules/model_viewer/widgets/info_panel.py
class ElementInfoPanel(QWidget):
    def __init__(self):
        self._element_id = None
        self._part_id = None
        self._node_ids = []

    def set_element(self, element_id, part_id, node_ids):
        """선택된 Element 정보 표시"""
        self._element_id = element_id
        self._part_id = part_id
        self._node_ids = node_ids
        self._update_display()
```

#### 1.2 Selection Highlight VBO
```python
# gl_widget.py에 추가
def _create_selection_vbo(self):
    """선택된 요소를 밝은 색으로 렌더링"""
    selected_elements = self._selection.get_selected()

    # Highlight 색상 (밝은 노란색)
    highlight_color = (1.0, 1.0, 0.0)

    # VBO 데이터 생성
    # ... (선택된 요소만)
```

#### 1.3 마우스 이벤트 통합
```python
def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        # Picking
        element_id = self._pick_element(event.x(), event.y())

        if element_id:
            # 선택 처리
            multi = event.modifiers() & Qt.ControlModifier
            self._selection.select(element_id, multi)

            # 시그널 발행
            self.elementSelected.emit(element_id)

            # 업데이트
            self.update()
```

---

### Phase 2: Keyword Manager 연동 (1시간)

#### 2.1 시그널 연결
```python
# module.py
def _setup_connections(self):
    # Model Viewer → Keyword Manager
    self._gl_widget.elementSelected.connect(
        self._on_element_selected
    )

    # Keyword Manager → Model Viewer
    if self.ctx.keyword_manager:
        self.ctx.keyword_manager.itemSelected.connect(
            self._on_keyword_selected
        )
```

#### 2.2 Element 선택 핸들러
```python
def _on_element_selected(self, element_id: int):
    """3D 뷰에서 Element 선택됨"""
    # Element 정보 조회
    element_info = self._mesh_data.get_element_info(element_id)

    # Keyword Manager에 알림
    if self.ctx.keyword_manager:
        self.ctx.keyword_manager.highlight_element(element_id)

    # Info Panel 업데이트
    self._info_panel.set_element(
        element_id,
        element_info.part_id,
        element_info.node_ids
    )
```

#### 2.3 Keyword 선택 핸들러
```python
def _on_keyword_selected(self, category: str, item_id: int):
    """Keyword Manager에서 항목 선택됨"""
    if category == 'parts':
        # Part 하이라이트
        self._gl_widget.highlight_part(item_id)

    elif category == 'elements':
        # Element 하이라이트
        self._gl_widget.highlight_element(item_id)

    elif category == 'nodes':
        # Node 하이라이트
        self._gl_widget.highlight_node(item_id)
```

---

### Phase 3: 실시간 업데이트 (30분)

#### 3.1 Keyword 수정 감지
```python
# Keyword Manager의 modify 이벤트 리스닝
def _on_keyword_modified(self, category: str, item_id: int):
    """Keyword가 수정됨 → 3D 업데이트"""

    if category == 'nodes':
        # 노드 좌표 변경 → VBO 재생성
        self._gl_widget.update_node(item_id)

    elif category == 'parts':
        # Part 정보 변경 → 색상/가시성 업데이트
        self._gl_widget.update_part(item_id)
```

#### 3.2 부분 VBO 업데이트
```python
def update_node(self, node_id: int):
    """특정 노드만 업데이트 (전체 재생성 불필요)"""
    # 해당 노드를 사용하는 요소 찾기
    affected_elements = self._mesh.get_elements_using_node(node_id)

    # 해당 요소의 VBO만 재생성
    self._update_partial_vbo(affected_elements)
```

---

## 🎨 UI 레이아웃

### 통합된 UI
```
┌─────────────────────────────────────────────────────┐
│ K-File: [examples/DropSet.k]  [파일 선택] [로드]    │
├─────────────────────────────────────────────────────┤
│                                                       │
│ ┌──────────┬──────────────────────┬──────────────┐  │
│ │Part Tree │   3D Viewer          │ Info Panel   │  │
│ │          │                      │              │  │
│ │□ Part 1  │                      │ Element Info │  │
│ │□ Part 2  │    [3D Model]        │ ID: 12345    │  │
│ │□ Part 3  │                      │ Part: 2      │  │
│ │...       │                      │ Nodes: 4     │  │
│ │          │                      │ - 1001       │  │
│ │          │                      │ - 1002       │  │
│ │          │                      │ - 1003       │  │
│ │          │                      │ - 1004       │  │
│ └──────────┴──────────────────────┴──────────────┘  │
│                                                       │
│ [□ Solid] [✓ 와이어프레임] [□ 노드] [뷰 리셋]        │
│ FPS: 120.5 | Selected: 3 elements                    │
├─────────────────────────────────────────────────────┤
│ Nodes: 29,624 | Elements: 44,657 | Parts: 23         │
└─────────────────────────────────────────────────────┘
```

---

## 📊 데이터 흐름

### 선택 시나리오 1: 3D에서 선택
```
1. 사용자가 3D 뷰에서 Element 클릭
   ↓
2. GPU Picking → Element ID 추출
   ↓
3. SelectionManager에 저장
   ↓
4. elementSelected 시그널 발행
   ↓
5-1. Model Viewer: Highlight 렌더링
5-2. Info Panel: 정보 표시
5-3. Keyword Manager: 트리에서 해당 Element 포커스
```

### 선택 시나리오 2: Keyword Manager에서 선택
```
1. 사용자가 Keyword Manager에서 Part 선택
   ↓
2. itemSelected 시그널 발행
   ↓
3. Model Viewer: 해당 Part 하이라이트
   ↓
4. 카메라: 해당 Part로 Zoom
```

### 수정 시나리오
```
1. Keyword Manager에서 노드 좌표 수정
   ↓
2. itemModified 시그널 발행
   ↓
3. Model Viewer: 해당 노드 사용 요소의 VBO 재생성
   ↓
4. 3D 뷰 자동 업데이트
```

---

## 🔗 AppContext 통합

### Shared State
```python
# app_context.py
class AppContext:
    def __init__(self):
        # 공유 상태
        self.selected_elements: Set[int] = set()
        self.selected_parts: Set[int] = set()
        self.selected_nodes: Set[int] = set()

        # 시그널
        self.selectionChanged = Signal(str, set)  # (type, ids)
```

### 모듈 간 통신
```python
# Model Viewer
self.ctx.selected_elements.add(element_id)
self.ctx.selectionChanged.emit('elements', self.ctx.selected_elements)

# Keyword Manager
def _on_selection_changed(self, sel_type: str, ids: set):
    if sel_type == 'elements':
        self._tree.highlight_items('elements', ids)
```

---

## ⚡ 성능 최적화

### 1. 부분 업데이트
- **전체 VBO 재생성** → 느림 (10-100ms)
- **부분 업데이트** → 빠름 (<1ms)

```python
# Bad
def update_mesh(self):
    self._create_all_vbos()  # 전체 재생성

# Good
def update_element(self, element_id):
    affected_indices = self._get_affected_indices(element_id)
    glBufferSubData(GL_ARRAY_BUFFER, offset, size, data)  # 부분만
```

### 2. Selection VBO 분리
```python
# 일반 렌더링 VBO (변경 없음)
self._wireframe_vbo

# 선택 하이라이트 VBO (자주 변경)
self._selection_vbo  # 작은 크기, 빠른 재생성
```

### 3. 이벤트 디바운싱
```python
# Keyword Manager에서 연속 수정 시
@debounce(100)  # 100ms 내 연속 이벤트 무시
def _on_keyword_modified(self, ...):
    self._update_3d_view()
```

---

## 🎯 구현 우선순위

### High Priority (즉시)
1. ✅ **Info Panel** - 선택 정보 표시
2. ✅ **Selection Highlight** - 하이라이트 렌더링
3. ✅ **마우스 Picking** - 클릭 선택 기능

### Medium Priority (선택적)
4. **Keyword Manager 연동** - 양방향 동기화
5. **실시간 업데이트** - 수정 즉시 반영
6. **Camera Zoom to Selection** - 선택 항목으로 줌

### Low Priority (향후)
7. **Multi-view** - 여러 뷰포트
8. **Compare Mode** - Before/After 비교
9. **Annotation** - 3D에 노트 추가

---

## 📝 구현 체크리스트

### Phase 1: Picking UI
- [ ] ElementInfoPanel 위젯 생성
- [ ] Selection VBO 구현
- [ ] Highlight 렌더링 (밝은 색)
- [ ] 마우스 이벤트 처리
- [ ] 다중 선택 (Ctrl+Click)

### Phase 2: Keyword Manager 연동
- [ ] 시그널 정의 (elementSelected, itemSelected)
- [ ] AppContext 공유 상태 추가
- [ ] Model Viewer → Keyword Manager 연동
- [ ] Keyword Manager → Model Viewer 연동

### Phase 3: 실시간 업데이트
- [ ] Keyword 수정 감지
- [ ] 부분 VBO 업데이트
- [ ] 자동 리프레시

### Phase 4: 테스트 & 문서
- [ ] 통합 테스트
- [ ] 성능 테스트
- [ ] 사용자 가이드

---

## ✨ 기대 효과

### 사용자 경험
- **직관적 선택**: 3D 클릭 → 즉시 정보 표시
- **양방향 동기화**: 어디서 선택해도 일관성
- **실시간 피드백**: 수정 즉시 3D 반영

### 생산성
- **빠른 분석**: Element 정보 즉시 확인
- **편리한 편집**: 3D 보면서 Keyword 수정
- **시각적 검증**: 수정 결과 즉시 확인

### 확장성
- **DOE 통합**: 최적화 결과 3D 시각화
- **분석 도구**: 선택 요소 분석
- **보고서 생성**: 스크린샷 + 정보

---

## 🚀 다음 단계

1. **Info Panel 구현** (30분)
2. **Selection Highlight** (30분)
3. **마우스 Picking 통합** (30분)
4. **Keyword Manager 연동** (1시간)
5. **테스트 & 문서** (30분)

**총 예상 시간: 3시간**

---

**준비 완료! 구현 시작할까요?** 🎯
