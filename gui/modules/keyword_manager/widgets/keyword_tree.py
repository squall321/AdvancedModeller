"""Keyword tree widget for hierarchical keyword display"""
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QHBoxLayout,
    QWidget, QLineEdit, QPushButton, QLabel, QMenu, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction
from typing import Any, Optional, List, Tuple

try:
    import qtawesome as qta
except ImportError:
    qta = None

from ..core.keyword_model import KeywordModel, KEYWORD_CATEGORIES, CategoryInfo


class KeywordTreeWidget(QWidget):
    """키워드 계층 트리 위젯

    카테고리별로 키워드를 그룹화하여 표시합니다.
    대량 데이터(노드/요소)는 범위별로 계층화하여 성능을 개선합니다.
    """

    # 시그널
    itemSelected = Signal(str, object)  # (category_id, item_data)
    categorySelected = Signal(str)       # category_id
    rangeSelected = Signal(str, list)    # (category_id, items_in_range)
    multiSelected = Signal(str, list)    # (category_id, items) - 다중 선택

    # 컨텍스트 메뉴 시그널
    addRequested = Signal(str)           # category_id - 추가 요청
    deleteRequested = Signal(str, list)  # (category_id, items) - 삭제 요청
    copyRequested = Signal(str, list)    # (category_id, items) - 복사 요청
    cutRequested = Signal(str, list)     # (category_id, items) - 잘라내기 요청
    pasteRequested = Signal(str)         # category_id - 붙여넣기 요청
    batchEditRequested = Signal(str, list)  # (category_id, items) - 일괄 수정 요청

    # 범위 분할 기준
    RANGE_SIZE = 10000  # 10,000개 단위로 분할
    MAX_ITEMS_BEFORE_RANGE = 100  # 100개 이하면 범위 없이 표시

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model: Optional[KeywordModel] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 검색 바
        search_layout = QHBoxLayout()
        search_layout.setSpacing(4)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("검색...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                background: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #7fbadc;
            }
        """)
        self._search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_input)

        if qta:
            clear_btn = QPushButton(qta.icon('fa5s.times'), "")
        else:
            clear_btn = QPushButton("X")
        clear_btn.setFixedWidth(28)
        clear_btn.clicked.connect(self._clear_search)
        search_layout.addWidget(clear_btn)

        layout.addLayout(search_layout)

        # 트리 위젯
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["키워드", "개수"])
        self._tree.setColumnWidth(0, 200)
        self._tree.setColumnWidth(1, 60)
        self._tree.setAlternatingRowColors(True)
        self._tree.setStyleSheet("""
            QTreeWidget {
                background: #2b2b2b;
                alternate-background-color: #323232;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
            }
            QTreeWidget::item {
                padding: 4px 2px;
                border-bottom: 1px solid #3a3a3a;
            }
            QTreeWidget::item:hover {
                background: #3a3a3a;
            }
            QTreeWidget::item:selected {
                background: #2d5a7b;
                color: #ffffff;
            }
            QTreeWidget::branch:has-children:closed {
                image: url(none);
                border-image: none;
            }
            QTreeWidget::branch:has-children:open {
                image: url(none);
                border-image: none;
            }
            QHeaderView::section {
                background: #3c3c3c;
                color: #b0b0b0;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #4a4a4a;
            }
        """)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)

        # 다중 선택 활성화
        self._tree.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # 컨텍스트 메뉴 설정
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self._tree)

    def set_model(self, model: KeywordModel):
        """키워드 모델 설정 및 트리 갱신"""
        self._model = model
        self._build_tree()

    def _build_tree(self):
        """트리 구조 구성"""
        self._tree.clear()

        if not self._model or not self._model.is_loaded:
            empty_item = QTreeWidgetItem(["모델이 로드되지 않았습니다", ""])
            self._tree.addTopLevelItem(empty_item)
            return

        for cat in KEYWORD_CATEGORIES:
            self._add_category_node(cat, None)  # None = top level

    def _add_category_node(self, cat: CategoryInfo, parent: QTreeWidgetItem = None):
        """카테고리 노드 추가"""
        count = self._model.get_category_count(cat.id)

        # 카테고리 아이템 생성
        item = QTreeWidgetItem()
        item.setText(0, f"{cat.name_ko} ({cat.name})")
        item.setText(1, str(count))
        item.setData(0, Qt.UserRole, {'type': 'category', 'id': cat.id, 'info': cat})

        # 아이콘 설정
        if qta:
            item.setIcon(0, qta.icon(cat.icon))

        # 부모에 추가
        if parent is None:
            self._tree.addTopLevelItem(item)
        else:
            parent.addChild(item)

        # 서브카테고리가 있는 경우
        if cat.is_group and cat.subcategories:
            for subcat in cat.subcategories:
                self._add_category_node(subcat, item)
        elif count > 0:
            # 더미 자식 추가 (lazy loading용)
            dummy = QTreeWidgetItem(["로딩 중...", ""])
            dummy.setData(0, Qt.UserRole, {'type': 'dummy'})
            item.addChild(dummy)

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """아이템 확장 시 실제 데이터 로드"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get('type')

        # 더미 자식이 있는 경우만 로드
        if item.childCount() == 1:
            child = item.child(0)
            child_data = child.data(0, Qt.UserRole)
            if child_data and child_data.get('type') == 'dummy':
                item.removeChild(child)

                if item_type == 'category':
                    self._load_category_items(item, data['id'])
                elif item_type == 'range':
                    # 범위 노드 확장 시 하위 범위 또는 개별 항목 로드
                    self._expand_range_node(item, data)

    def _load_category_items(self, parent: QTreeWidgetItem, category_id: str):
        """카테고리 항목 로드"""
        items = self._model.get_items(category_id)
        count = len(items)

        # 대량 데이터 카테고리인 경우 범위별로 분할
        if category_id in ('nodes', 'shell', 'solid', 'beam') and count > self.MAX_ITEMS_BEFORE_RANGE:
            self._load_ranged_items(parent, category_id, items)
        else:
            # 소량 데이터는 기존 방식대로 표시
            self._load_direct_items(parent, category_id, items)

    def _load_ranged_items(self, parent: QTreeWidgetItem, category_id: str, items: List):
        """범위별로 항목 분할하여 트리에 추가"""
        if not items:
            return

        # ID 추출 함수
        def get_id(item):
            if category_id == 'nodes':
                return getattr(item, 'nid', 0)
            else:
                return getattr(item, 'eid', 0)

        # ID 기준으로 정렬
        sorted_items = sorted(items, key=get_id)

        # ID 범위 계산
        min_id = get_id(sorted_items[0])
        max_id = get_id(sorted_items[-1])

        # 범위 크기 결정 (데이터 크기에 따라 동적으로)
        total_count = len(sorted_items)
        if total_count > 100000:
            range_size = 100000
        elif total_count > 10000:
            range_size = 10000
        else:
            range_size = 1000

        # 범위 시작점 계산 (범위에 맞게 정렬)
        range_start = (min_id // range_size) * range_size

        # 범위별로 그룹화
        current_range_start = range_start
        current_range_items = []

        for item in sorted_items:
            item_id = get_id(item)
            item_range_start = (item_id // range_size) * range_size

            if item_range_start != current_range_start:
                # 이전 범위 저장
                if current_range_items:
                    self._add_range_node(parent, category_id, current_range_start,
                                        current_range_start + range_size - 1,
                                        current_range_items, range_size)
                # 새 범위 시작
                current_range_start = item_range_start
                current_range_items = []

            current_range_items.append(item)

        # 마지막 범위 저장
        if current_range_items:
            self._add_range_node(parent, category_id, current_range_start,
                                current_range_start + range_size - 1,
                                current_range_items, range_size)

    def _add_range_node(self, parent: QTreeWidgetItem, category_id: str,
                        start: int, end: int, items: List, range_size: int):
        """범위 노드 추가"""
        count = len(items)
        range_text = f"{start:,} ~ {end:,}"

        range_item = QTreeWidgetItem([range_text, str(count)])
        range_item.setData(0, Qt.UserRole, {
            'type': 'range',
            'category': category_id,
            'start': start,
            'end': end,
            'items': items,
            'range_size': range_size
        })

        # 아이콘 설정
        if qta:
            range_item.setIcon(0, qta.icon('fa5s.folder'))

        parent.addChild(range_item)

        # 하위 범위가 필요한 경우 더미 추가 (lazy loading)
        # 항목이 1개 이상이면 확장 가능하게 (개별 항목 표시를 위해)
        print(f"[Tree] _add_range_node: range_size={range_size}, count={count}, range={range_text}")
        if count > 0:
            dummy = QTreeWidgetItem(["로딩 중...", ""])
            dummy.setData(0, Qt.UserRole, {'type': 'dummy'})
            range_item.addChild(dummy)
            print(f"[Tree] Added dummy child to range {range_text}")

    def _load_direct_items(self, parent: QTreeWidgetItem, category_id: str, items: List):
        """항목을 직접 트리에 추가 (소량 데이터용)"""
        print(f"[Tree] _load_direct_items: category={category_id}, count={len(items)}")
        for item_data in items:
            display_text = self._model.get_item_display_text(category_id, item_data)

            child = QTreeWidgetItem([display_text, ""])
            child.setData(0, Qt.UserRole, {
                'type': 'item',
                'category': category_id,
                'data': item_data
            })
            parent.addChild(child)

    def _expand_range_node(self, parent: QTreeWidgetItem, data: dict):
        """범위 노드 확장 - 하위 범위 또는 개별 항목 로드"""
        category_id = data['category']
        items = data['items']
        current_range_size = data['range_size']
        count = len(items)

        print(f"[Tree] _expand_range_node: range_size={current_range_size}, count={count}")

        # 다음 단계 범위 크기 결정
        if current_range_size > 100000:
            next_range_size = 100000
        elif current_range_size > 10000:
            next_range_size = 10000
        elif current_range_size > 1000:
            next_range_size = 1000
        elif current_range_size > 100:
            next_range_size = 100
        else:
            next_range_size = 0  # 개별 항목 표시

        print(f"[Tree] next_range_size={next_range_size}")

        # ID 추출 함수
        def get_id(item):
            if category_id == 'nodes':
                return getattr(item, 'nid', 0)
            else:
                return getattr(item, 'eid', 0)

        # 하위 범위가 있고, 항목 수가 많으면 더 분할
        if next_range_size > 0 and count > self.MAX_ITEMS_BEFORE_RANGE:
            # 더 작은 범위로 분할
            sorted_items = sorted(items, key=get_id)
            current_range_start = None
            current_range_items = []

            for item in sorted_items:
                item_id = get_id(item)
                item_range_start = (item_id // next_range_size) * next_range_size

                if current_range_start is None:
                    current_range_start = item_range_start

                if item_range_start != current_range_start:
                    if current_range_items:
                        self._add_range_node(parent, category_id, current_range_start,
                                            current_range_start + next_range_size - 1,
                                            current_range_items, next_range_size)
                    current_range_start = item_range_start
                    current_range_items = []

                current_range_items.append(item)

            if current_range_items:
                self._add_range_node(parent, category_id, current_range_start,
                                    current_range_start + next_range_size - 1,
                                    current_range_items, next_range_size)
        else:
            # 개별 항목 표시
            self._load_direct_items(parent, category_id, items)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """아이템 클릭 시 시그널 발생"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get('type')

        if item_type == 'item':
            self.itemSelected.emit(data['category'], data['data'])
        elif item_type == 'category':
            self.categorySelected.emit(data['id'])
        elif item_type == 'range':
            # 범위 선택 시 해당 범위의 항목들을 전달
            self.rangeSelected.emit(data['category'], data['items'])

    def _on_search(self, text: str):
        """검색 필터링"""
        text = text.lower().strip()

        def set_visible_recursive(item: QTreeWidgetItem, parent_visible: bool = False):
            # 현재 아이템 텍스트 검사
            item_text = item.text(0).lower()
            matches = text in item_text if text else True

            # 자식들 검사
            child_visible = False
            for i in range(item.childCount()):
                if set_visible_recursive(item.child(i), matches):
                    child_visible = True

            # 표시 여부 결정
            visible = matches or child_visible or parent_visible
            item.setHidden(not visible)

            # 매칭된 경우 펼치기
            if (matches or child_visible) and text:
                item.setExpanded(True)

            return matches or child_visible

        # 모든 최상위 아이템에 적용
        for i in range(self._tree.topLevelItemCount()):
            set_visible_recursive(self._tree.topLevelItem(i))

    def _clear_search(self):
        """검색 초기화"""
        self._search_input.clear()

    def refresh(self):
        """트리 새로고침"""
        self._build_tree()

    def expand_category(self, category_id: str):
        """특정 카테고리 펼치기"""
        def find_and_expand(item: QTreeWidgetItem):
            data = item.data(0, Qt.UserRole)
            if data and data.get('type') == 'category' and data.get('id') == category_id:
                item.setExpanded(True)
                self._tree.scrollToItem(item)
                return True

            for i in range(item.childCount()):
                if find_and_expand(item.child(i)):
                    return True
            return False

        for i in range(self._tree.topLevelItemCount()):
            if find_and_expand(self._tree.topLevelItem(i)):
                break

    def _on_selection_changed(self):
        """선택 변경 시 다중 선택 처리"""
        selected_items = self._tree.selectedItems()
        if len(selected_items) <= 1:
            return

        # 같은 카테고리의 항목들만 다중 선택 허용
        items_by_category = {}
        for tree_item in selected_items:
            data = tree_item.data(0, Qt.UserRole)
            if data and data.get('type') == 'item':
                category = data['category']
                if category not in items_by_category:
                    items_by_category[category] = []
                items_by_category[category].append(data['data'])

        # 단일 카테고리만 선택된 경우 시그널 발생
        if len(items_by_category) == 1:
            category, items = next(iter(items_by_category.items()))
            if len(items) > 1:
                self.multiSelected.emit(category, items)

    def get_selected_items(self) -> List[Tuple[str, Any]]:
        """선택된 모든 항목 반환

        Returns:
            [(category, item_data), ...] 형태의 리스트
        """
        result = []
        for tree_item in self._tree.selectedItems():
            data = tree_item.data(0, Qt.UserRole)
            if data and data.get('type') == 'item':
                result.append((data['category'], data['data']))
        return result

    def get_current_category(self) -> Optional[str]:
        """현재 선택된 카테고리 반환"""
        selected = self._tree.selectedItems()
        if not selected:
            return None

        data = selected[0].data(0, Qt.UserRole)
        if not data:
            return None

        item_type = data.get('type')
        if item_type == 'category':
            return data.get('id')
        elif item_type == 'item':
            return data.get('category')
        elif item_type == 'range':
            return data.get('category')
        return None

    def _show_context_menu(self, pos):
        """컨텍스트 메뉴 표시"""
        item = self._tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get('type')
        menu = QMenu(self)

        if item_type == 'category':
            category_id = data.get('id')
            # 카테고리 메뉴
            add_action = QAction("새 항목 추가", self)
            if qta:
                add_action.setIcon(qta.icon('fa5s.plus'))
            add_action.triggered.connect(lambda: self.addRequested.emit(category_id))
            menu.addAction(add_action)

            menu.addSeparator()

            paste_action = QAction("붙여넣기", self)
            if qta:
                paste_action.setIcon(qta.icon('fa5s.paste'))
            paste_action.triggered.connect(lambda: self.pasteRequested.emit(category_id))
            menu.addAction(paste_action)

        elif item_type == 'item':
            category = data.get('category')
            selected_items = self.get_selected_items()

            # 선택된 항목이 같은 카테고리인지 확인
            same_category_items = [
                item_data for cat, item_data in selected_items
                if cat == category
            ]

            if not same_category_items:
                same_category_items = [data['data']]

            # 복사
            copy_action = QAction(f"복사 ({len(same_category_items)}개)", self)
            if qta:
                copy_action.setIcon(qta.icon('fa5s.copy'))
            copy_action.triggered.connect(
                lambda: self.copyRequested.emit(category, same_category_items)
            )
            menu.addAction(copy_action)

            # 잘라내기
            cut_action = QAction(f"잘라내기 ({len(same_category_items)}개)", self)
            if qta:
                cut_action.setIcon(qta.icon('fa5s.cut'))
            cut_action.triggered.connect(
                lambda: self.cutRequested.emit(category, same_category_items)
            )
            menu.addAction(cut_action)

            menu.addSeparator()

            # 삭제
            delete_action = QAction(f"삭제 ({len(same_category_items)}개)", self)
            if qta:
                delete_action.setIcon(qta.icon('fa5s.trash'))
            delete_action.triggered.connect(
                lambda: self.deleteRequested.emit(category, same_category_items)
            )
            menu.addAction(delete_action)

            menu.addSeparator()

            # 일괄 수정 (2개 이상 선택 시)
            if len(same_category_items) > 1:
                batch_edit_action = QAction(f"일괄 수정 ({len(same_category_items)}개)", self)
                if qta:
                    batch_edit_action.setIcon(qta.icon('fa5s.edit'))
                batch_edit_action.triggered.connect(
                    lambda: self.batchEditRequested.emit(category, same_category_items)
                )
                menu.addAction(batch_edit_action)

        elif item_type == 'range':
            category = data.get('category')
            items = data.get('items', [])

            # 범위 전체 복사
            copy_action = QAction(f"범위 전체 복사 ({len(items)}개)", self)
            if qta:
                copy_action.setIcon(qta.icon('fa5s.copy'))
            copy_action.triggered.connect(
                lambda: self.copyRequested.emit(category, items)
            )
            menu.addAction(copy_action)

            menu.addSeparator()

            # 범위 일괄 수정
            batch_edit_action = QAction(f"범위 일괄 수정 ({len(items)}개)", self)
            if qta:
                batch_edit_action.setIcon(qta.icon('fa5s.edit'))
            batch_edit_action.triggered.connect(
                lambda: self.batchEditRequested.emit(category, items)
            )
            menu.addAction(batch_edit_action)

        if menu.actions():
            menu.exec_(self._tree.mapToGlobal(pos))
