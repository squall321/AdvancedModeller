"""Keyword Manager Module - K-file keyword browsing and editing"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QGroupBox, QFrame, QStackedWidget, QToolBar, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence, QAction
from typing import TYPE_CHECKING

try:
    import qtawesome as qta
except ImportError:
    qta = None

from gui.modules.base import BaseModule
from gui.modules import ModuleRegistry
from .widgets.keyword_tree import KeywordTreeWidget
from .widgets.keyword_detail import KeywordDetailWidget
from .widgets.keyword_preview import KeywordPreviewWidget
from .widgets.keyword_card_editor import KeywordCardEditor
from .core.keyword_model import KeywordModel
from .core.clipboard import get_clipboard, KeywordFactory
from .dialogs.batch_edit_dialog import BatchEditDialog

if TYPE_CHECKING:
    from gui.app_context import AppContext


@ModuleRegistry.register(
    module_id="keyword_manager",
    name="키워드 관리",
    description="K-file 키워드 탐색 및 편집",
    icon="fa5s.list-alt",
    order=11,
    methods=[
        {'id': 'browse', 'name': '키워드 탐색', 'icon': 'fa5s.search'},
        {'id': 'refresh', 'name': '새로고침', 'icon': 'fa5s.sync'},
        {'id': 'export', 'name': 'K-file 내보내기', 'icon': 'fa5s.file-export'},
    ]
)
class KeywordManagerModule(BaseModule):
    """키워드 관리 모듈

    파싱된 K-file 키워드를 트리 구조로 표시하고 상세 정보를 제공합니다.
    """

    @property
    def module_id(self) -> str:
        return "keyword_manager"

    def __init__(self, ctx: 'AppContext', parent=None):
        self._keyword_model = KeywordModel()
        self._clipboard = get_clipboard()
        self._current_selection = None  # (category, item) 튜플
        super().__init__(ctx, parent)
        self._setup_shortcuts()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 상단 툴바 (파일 선택 제거, Export만 유지)
        toolbar_layout = QHBoxLayout()

        # 파일 정보 표시 (읽기 전용)
        self._file_label = QLabel("K-file: (파일 로더에서 로드하세요)")
        self._file_label.setStyleSheet("padding: 4px; color: gray;")
        toolbar_layout.addWidget(self._file_label, 1)

        # Export 버튼
        if qta:
            self._export_btn = QPushButton(qta.icon('fa5s.file-export'), " Export")
            self._export_btn.setToolTip("수정된 K-file 내보내기")
        else:
            self._export_btn = QPushButton("Export")
        self._export_btn.clicked.connect(self._export_kfile)
        self._export_btn.setEnabled(False)  # 모델 로드 전에는 비활성화
        toolbar_layout.addWidget(self._export_btn)

        layout.addLayout(toolbar_layout)

        # 편집 툴바
        edit_toolbar = QHBoxLayout()
        edit_toolbar.setSpacing(4)

        # Undo 버튼
        if qta:
            self._undo_btn = QPushButton(qta.icon('fa5s.undo'), "")
            self._undo_btn.setToolTip("실행 취소 (Ctrl+Z)")
        else:
            self._undo_btn = QPushButton("↶")
        self._undo_btn.setFixedWidth(32)
        self._undo_btn.clicked.connect(self._undo)
        self._undo_btn.setEnabled(False)
        edit_toolbar.addWidget(self._undo_btn)

        # Redo 버튼
        if qta:
            self._redo_btn = QPushButton(qta.icon('fa5s.redo'), "")
            self._redo_btn.setToolTip("다시 실행 (Ctrl+Y)")
        else:
            self._redo_btn = QPushButton("↷")
        self._redo_btn.setFixedWidth(32)
        self._redo_btn.clicked.connect(self._redo)
        self._redo_btn.setEnabled(False)
        edit_toolbar.addWidget(self._redo_btn)

        # 구분선
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        edit_toolbar.addWidget(separator1)

        # Copy 버튼
        if qta:
            self._copy_btn = QPushButton(qta.icon('fa5s.copy'), "")
            self._copy_btn.setToolTip("복사 (Ctrl+C)")
        else:
            self._copy_btn = QPushButton("📋")
        self._copy_btn.setFixedWidth(32)
        self._copy_btn.clicked.connect(self._copy)
        self._copy_btn.setEnabled(False)
        edit_toolbar.addWidget(self._copy_btn)

        # Cut 버튼
        if qta:
            self._cut_btn = QPushButton(qta.icon('fa5s.cut'), "")
            self._cut_btn.setToolTip("잘라내기 (Ctrl+X)")
        else:
            self._cut_btn = QPushButton("✂")
        self._cut_btn.setFixedWidth(32)
        self._cut_btn.clicked.connect(self._cut)
        self._cut_btn.setEnabled(False)
        edit_toolbar.addWidget(self._cut_btn)

        # Paste 버튼
        if qta:
            self._paste_btn = QPushButton(qta.icon('fa5s.paste'), "")
            self._paste_btn.setToolTip("붙여넣기 (Ctrl+V)")
        else:
            self._paste_btn = QPushButton("📄")
        self._paste_btn.setFixedWidth(32)
        self._paste_btn.clicked.connect(self._paste)
        self._paste_btn.setEnabled(False)
        edit_toolbar.addWidget(self._paste_btn)

        # 구분선
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        edit_toolbar.addWidget(separator2)

        # Add 버튼
        if qta:
            self._add_btn = QPushButton(qta.icon('fa5s.plus'), "")
            self._add_btn.setToolTip("새 항목 추가 (Ctrl+N)")
        else:
            self._add_btn = QPushButton("+")
        self._add_btn.setFixedWidth(32)
        self._add_btn.clicked.connect(self._add_item)
        self._add_btn.setEnabled(False)
        edit_toolbar.addWidget(self._add_btn)

        # Delete 버튼
        if qta:
            self._delete_btn = QPushButton(qta.icon('fa5s.trash'), "")
            self._delete_btn.setToolTip("삭제 (Delete)")
        else:
            self._delete_btn = QPushButton("🗑")
        self._delete_btn.setFixedWidth(32)
        self._delete_btn.clicked.connect(self._delete_item)
        self._delete_btn.setEnabled(False)
        edit_toolbar.addWidget(self._delete_btn)

        edit_toolbar.addStretch()

        layout.addLayout(edit_toolbar)

        # 메인 스플리터
        splitter = QSplitter(Qt.Horizontal)

        # 좌측: 키워드 트리
        left_widget = QWidget()
        left_widget.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._tree = KeywordTreeWidget()
        self._tree.setMinimumWidth(250)
        self._tree.setMinimumHeight(200)
        self._tree.itemSelected.connect(self._on_item_selected)
        self._tree.categorySelected.connect(self._on_category_selected)
        self._tree.rangeSelected.connect(self._on_range_selected)
        self._tree.multiSelected.connect(self._on_multi_selected)

        # 컨텍스트 메뉴 시그널 연결
        self._tree.addRequested.connect(self._on_add_requested)
        self._tree.deleteRequested.connect(self._on_delete_requested)
        self._tree.copyRequested.connect(self._on_copy_requested)
        self._tree.cutRequested.connect(self._on_cut_requested)
        self._tree.pasteRequested.connect(self._on_paste_requested)
        self._tree.batchEditRequested.connect(self._on_batch_edit_requested)

        left_layout.addWidget(self._tree)

        splitter.addWidget(left_widget)

        # 우측: 상세 정보 (스택 위젯으로 전환 가능)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 스택 위젯 (Card 편집기 / 기존 상세+미리보기)
        self._right_stack = QStackedWidget()

        # 페이지 0: Card 편집기 (Node/Element용)
        self._card_editor = KeywordCardEditor()
        self._card_editor.keywordModified.connect(self._on_keyword_modified)
        self._right_stack.addWidget(self._card_editor)

        # 페이지 1: 기존 상세 + 미리보기 (기타 키워드용)
        detail_preview_widget = QWidget()
        detail_preview_layout = QVBoxLayout(detail_preview_widget)
        detail_preview_layout.setContentsMargins(0, 0, 0, 0)
        detail_preview_layout.setSpacing(8)

        self._detail = KeywordDetailWidget()
        detail_preview_layout.addWidget(self._detail, stretch=2)

        self._preview = KeywordPreviewWidget()
        detail_preview_layout.addWidget(self._preview, stretch=1)

        self._right_stack.addWidget(detail_preview_widget)

        right_layout.addWidget(self._right_stack)
        splitter.addWidget(right_widget)

        # 스플리터 비율
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)

        # 상태바
        self._status = QLabel("준비됨")
        self._status.setStyleSheet("padding: 4px; background: palette(alternate-base);")
        layout.addWidget(self._status)

    def on_activate(self):
        """모듈 활성화 시"""
        # AppContext에서 모델이 로드되어 있으면 사용
        if self.ctx.model.is_loaded:
            import os
            self._file_label.setText(f"K-file: {os.path.basename(self.ctx.model.filepath)}")
            self._file_label.setStyleSheet("padding: 4px;")
            self._keyword_model.set_model(self.ctx.model)
            self._tree.set_model(self._keyword_model)
            self._export_btn.setEnabled(True)
            self._update_status()
        else:
            self._file_label.setText("K-file: (파일 로더에서 로드하세요)")
            self._file_label.setStyleSheet("padding: 4px; color: gray;")
            self.log("파일 로더에서 K-file을 먼저 로드해주세요", "info")

    def on_action(self, action_id: str):
        """액션 처리"""
        if action_id == 'browse':
            self.log("파일 로더 모듈을 사용하여 K-file을 로드하세요", "info")
        elif action_id == 'refresh':
            self.on_activate()  # 모델 다시 로드
        elif action_id == 'export':
            self._export_kfile()

    def _browse_file(self):
        """파일 선택 다이얼로그"""
        # 시작 디렉토리 설정 (현재 디렉토리 또는 examples)
        import os
        start_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "examples")
        if not os.path.exists(start_dir):
            start_dir = ""

        path, _ = QFileDialog.getOpenFileName(
            self,
            "K-file 열기",
            start_dir,
            "K-files (*.k *.key *.dyn);;All files (*.*)"
        )
        if path:
            self._file_path.setText(path)
            self.log(f"파일 선택됨: {path}", "info")
            self._load_model()

    def _load_model(self):
        """모델 로드"""
        path = self._file_path.text()
        if not path:
            self.log("파일 경로를 입력해주세요", "warning")
            return

        self.status("모델 로딩 중...")

        # AppContext를 통해 로드
        load_result = self.ctx.load_k_file(path)

        if load_result:
            self._keyword_model.set_model(self.ctx.model)
            self._tree.set_model(self._keyword_model)
            self._update_status()
            self._export_btn.setEnabled(True)  # Export 버튼 활성화
            self.log(f"모델 로드 완료: {self.ctx.model.filename}", "info")
        else:
            self.log(f"모델 로드 실패: {path}", "error")
            self._status.setText("로드 실패")
            self._export_btn.setEnabled(False)

    def _update_status(self):
        """상태바 업데이트"""
        if not self._keyword_model.is_loaded:
            self._status.setText("모델 없음")
            return

        stats = self._keyword_model.get_stats()
        self._status.setText(
            f"Nodes: {stats.get('nodes', 0):,} | "
            f"Elements: {stats.get('elements', {}).get('total', 0):,} | "
            f"Parts: {stats.get('parts', 0)} | "
            f"파싱: {stats.get('parse_time_ms', 0):.1f}ms"
        )

    def _on_item_selected(self, category: str, item):
        """아이템 선택 시"""
        # 현재 선택 저장
        self._current_selection = (category, item)
        self._update_edit_buttons()

        # Card 편집기를 사용하는 카테고리 (모든 주요 카테고리)
        card_categories = (
            # 기본 구조
            'nodes', 'shell', 'solid', 'beam', 'parts', 'sections', 'materials',
            # Contact, Set
            'contacts', 'sets',
            # Controls
            'termination', 'timestep', 'energy', 'output', 'hourglass', 'bulk_viscosity',
            # Databases
            'binary', 'ascii', 'history_node', 'history_element', 'cross_section',
            # Boundaries
            'spc', 'motion',
            # Loads
            'node', 'segment', 'body',
            # Initials
            'velocity', 'stress',
            # Constraineds
            'rigid_body', 'joint', 'spotweld',
        )
        if category in card_categories:
            self._card_editor.set_keyword(category, item)
            self._right_stack.setCurrentIndex(0)  # Card 편집기
        else:
            # 기타 키워드는 기존 상세+미리보기 사용
            self._detail.set_keyword(category, item)
            self._preview.set_keyword(category, item)
            self._right_stack.setCurrentIndex(1)  # 상세+미리보기

    def _on_range_selected(self, category: str, items: list):
        """범위 선택 시 - 해당 범위의 K-file 미리보기 표시"""
        # Node/Element 카테고리는 Card 편집기로 범위 표시
        if category in ('nodes', 'shell', 'solid', 'beam'):
            self._card_editor.set_range(category, items)
            self._right_stack.setCurrentIndex(0)  # Card 편집기
        else:
            self._detail.clear()
            self._preview.set_range(category, items)
            self._right_stack.setCurrentIndex(1)  # 상세+미리보기
        self.status(f"{category}: {len(items):,}개 항목 선택됨")

    def _on_category_selected(self, category_id: str):
        """카테고리 선택 시"""
        count = self._keyword_model.get_category_count(category_id)
        self.status(f"{category_id}: {count}개 항목")

    def get_actions(self):
        """모듈 액션 버튼"""
        return [
            {'id': 'browse', 'name': 'K-file 열기', 'icon': 'fa5s.folder-open'},
            {'id': 'refresh', 'name': '새로고침', 'icon': 'fa5s.sync'},
            {'id': 'export', 'name': 'K-file 내보내기', 'icon': 'fa5s.file-export'},
        ]

    def _on_keyword_modified(self, category: str, item, field_name: str, old_value, new_value):
        """키워드 수정 시 호출 (Undo 지원)

        Args:
            category: 카테고리 ID
            item: 수정된 항목
            field_name: 수정된 필드명
            old_value: 이전 값
            new_value: 새 값
        """
        # keyword_model.modify_item()을 통해 Undo 스택에 기록
        if self._keyword_model.modify_item(category, item, field_name, new_value):
            self._update_status()
            self._update_edit_buttons()

            # Card Editor의 Raw 미리보기 업데이트
            if hasattr(self._card_editor, '_update_raw_preview'):
                self._card_editor._update_raw_preview()

            # Export 버튼 강조 표시 (수정사항 있음)
            if self._keyword_model.is_dirty:
                self._export_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4a7c59;
                        color: white;
                        font-weight: bold;
                    }
                """)

    def _export_kfile(self):
        """K-file 내보내기"""
        import os

        if not self._keyword_model.is_loaded:
            self.log("내보낼 모델이 없습니다", "warning")
            return

        # 기본 파일명 설정
        current_path = self._file_path.text()
        if current_path:
            default_path = os.path.splitext(current_path)[0] + "_modified.k"
        else:
            default_path = "model_export.k"

        # 저장 경로 선택
        path, _ = QFileDialog.getSaveFileName(
            self,
            "K-file 내보내기",
            default_path,
            "K-files (*.k *.key *.dyn);;All files (*.*)"
        )

        if not path:
            return

        # Export 실행
        self.status("K-file 내보내기 중...")
        success = self._keyword_model.export_kfile(path)

        if success:
            self.log(f"K-file 내보내기 완료: {path}", "info")
            self.status(f"내보내기 완료: {os.path.basename(path)}")
            # Export 버튼 스타일 초기화
            self._export_btn.setStyleSheet("")
        else:
            self.log(f"K-file 내보내기 실패: {path}", "error")
            self.status("내보내기 실패")

    def _setup_shortcuts(self):
        """단축키 설정"""
        # Undo: Ctrl+Z
        undo_shortcut = QShortcut(QKeySequence.Undo, self)
        undo_shortcut.activated.connect(self._undo)

        # Redo: Ctrl+Y / Ctrl+Shift+Z
        redo_shortcut = QShortcut(QKeySequence.Redo, self)
        redo_shortcut.activated.connect(self._redo)

        # Copy: Ctrl+C
        copy_shortcut = QShortcut(QKeySequence.Copy, self)
        copy_shortcut.activated.connect(self._copy)

        # Cut: Ctrl+X
        cut_shortcut = QShortcut(QKeySequence.Cut, self)
        cut_shortcut.activated.connect(self._cut)

        # Paste: Ctrl+V
        paste_shortcut = QShortcut(QKeySequence.Paste, self)
        paste_shortcut.activated.connect(self._paste)

        # Delete: Delete key
        delete_shortcut = QShortcut(QKeySequence.Delete, self)
        delete_shortcut.activated.connect(self._delete_item)

        # New: Ctrl+N
        new_shortcut = QShortcut(QKeySequence.New, self)
        new_shortcut.activated.connect(self._add_item)

    def _update_edit_buttons(self):
        """편집 버튼 상태 업데이트"""
        has_selection = self._current_selection is not None
        model_loaded = self._keyword_model.is_loaded

        # Undo/Redo 버튼
        self._undo_btn.setEnabled(self._keyword_model.can_undo())
        self._redo_btn.setEnabled(self._keyword_model.can_redo())

        # Copy/Cut/Delete 버튼 - 선택 항목이 있을 때만 활성화
        self._copy_btn.setEnabled(has_selection)
        self._cut_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)

        # Paste 버튼 - 클립보드에 데이터가 있을 때만 활성화
        self._paste_btn.setEnabled(self._clipboard.has_data() and model_loaded)

        # Add 버튼 - 모델이 로드되어 있을 때만 활성화
        self._add_btn.setEnabled(model_loaded)

    def _undo(self):
        """실행 취소"""
        if self._keyword_model.undo():
            self._update_edit_buttons()
            self._tree.refresh()
            # Card Editor 새로고침
            if self._current_selection:
                category, item = self._current_selection
                self._card_editor.set_keyword(category, item)
            self.status("실행 취소됨")
            self._update_dirty_state()

    def _redo(self):
        """다시 실행"""
        if self._keyword_model.redo():
            self._update_edit_buttons()
            self._tree.refresh()
            # Card Editor 새로고침
            if self._current_selection:
                category, item = self._current_selection
                self._card_editor.set_keyword(category, item)
            self.status("다시 실행됨")
            self._update_dirty_state()

    def _copy(self):
        """선택 항목 복사"""
        if not self._current_selection:
            return

        category, item = self._current_selection
        if self._clipboard.copy(category, [item], self._keyword_model.filepath):
            self.status(f"복사됨: {category}")
            self._update_edit_buttons()

    def _cut(self):
        """선택 항목 잘라내기"""
        if not self._current_selection:
            return

        category, item = self._current_selection
        if self._clipboard.cut(category, [item], self._keyword_model.filepath):
            # 잘라내기는 삭제까지 수행
            if self._keyword_model.delete_item(category, item):
                self._tree.refresh()
                self._current_selection = None
                self.status(f"잘라내기 완료: {category}")
                self._update_edit_buttons()
                self._update_dirty_state()

    def _paste(self):
        """붙여넣기"""
        if not self._clipboard.has_data():
            return

        result = self._clipboard.paste()
        if not result:
            return

        category, items, was_cut = result

        # 새 ID 할당 및 추가
        for item in items:
            new_id = self._keyword_model.get_next_id(category)
            # ID 필드 업데이트
            if category == 'nodes':
                item.nid = new_id
            elif category in ('shell', 'solid', 'beam'):
                item.eid = new_id
            elif category == 'parts':
                item.pid = new_id
            elif category == 'materials':
                item.mid = new_id
            elif category == 'sections':
                item.secid = new_id
            elif category == 'sets':
                item.sid = new_id

            self._keyword_model.add_item(category, item)

        self._tree.refresh()
        self.status(f"붙여넣기 완료: {len(items)}개 {category}")
        self._update_edit_buttons()
        self._update_dirty_state()

    def _add_item(self):
        """새 항목 추가"""
        if not self._keyword_model.is_loaded:
            return

        # 현재 선택된 카테고리 확인
        if self._current_selection:
            category = self._current_selection[0]
        else:
            # 기본값: nodes
            category = 'nodes'

        # 새 ID 생성
        new_id = self._keyword_model.get_next_id(category)

        # 카테고리별 새 항목 생성
        new_item = None
        if category == 'nodes':
            new_item = KeywordFactory.create_node(new_id)
        elif category == 'shell':
            new_item = KeywordFactory.create_shell(new_id)
        elif category == 'solid':
            new_item = KeywordFactory.create_solid(new_id)
        elif category == 'parts':
            new_item = KeywordFactory.create_part(new_id, f"Part_{new_id}")
        else:
            self.log(f"'{category}' 카테고리에 대한 추가 기능이 아직 구현되지 않았습니다", "warning")
            return

        if new_item:
            if self._keyword_model.add_item(category, new_item):
                self._tree.refresh()
                self.status(f"새 {category} 추가됨: ID {new_id}")
                self._update_edit_buttons()
                self._update_dirty_state()

    def _delete_item(self):
        """선택 항목 삭제"""
        if not self._current_selection:
            return

        category, item = self._current_selection

        # 확인 다이얼로그
        item_id = self._keyword_model._get_item_id(category, item)
        reply = QMessageBox.question(
            self,
            "삭제 확인",
            f"{category} #{item_id}을(를) 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self._keyword_model.delete_item(category, item):
                self._tree.refresh()
                self._current_selection = None
                self.status(f"삭제됨: {category} #{item_id}")
                self._update_edit_buttons()
                self._update_dirty_state()

    def _update_dirty_state(self):
        """수정 상태 업데이트"""
        if self._keyword_model.is_dirty:
            self._export_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a7c59;
                    color: white;
                    font-weight: bold;
                }
            """)
        else:
            self._export_btn.setStyleSheet("")

    # =========================================================================
    # 컨텍스트 메뉴 핸들러
    # =========================================================================

    def _on_multi_selected(self, category: str, items: list):
        """다중 선택 핸들러

        Args:
            category: 카테고리 ID
            items: 선택된 항목 리스트
        """
        if not items:
            self._current_selection = None
            self._update_edit_buttons()
            return

        # 마지막 항목을 현재 선택으로 설정 (상세 표시용)
        self._current_selection = (category, items[-1])
        self._update_edit_buttons()

        # 상태 표시
        self.status(f"{category}: {len(items)}개 항목 선택됨")

        # 다중 선택 시 Card Editor에 범위 표시
        if category in ('nodes', 'shell', 'solid', 'beam'):
            self._card_editor.set_range(category, items)
            self._right_stack.setCurrentIndex(0)
        else:
            self._preview.set_range(category, items)
            self._right_stack.setCurrentIndex(1)

    def _on_add_requested(self, category: str):
        """추가 요청 핸들러 (컨텍스트 메뉴)

        Args:
            category: 추가할 카테고리 ID
        """
        if not self._keyword_model.is_loaded:
            return

        # 새 ID 생성
        new_id = self._keyword_model.get_next_id(category)

        # 카테고리별 새 항목 생성
        new_item = None
        if category == 'nodes':
            new_item = KeywordFactory.create_node(new_id)
        elif category == 'shell':
            new_item = KeywordFactory.create_shell(new_id)
        elif category == 'solid':
            new_item = KeywordFactory.create_solid(new_id)
        elif category == 'parts':
            new_item = KeywordFactory.create_part(new_id, f"Part_{new_id}")
        else:
            self.log(f"'{category}' 카테고리에 대한 추가 기능이 아직 구현되지 않았습니다", "warning")
            return

        if new_item:
            if self._keyword_model.add_item(category, new_item):
                self._tree.refresh()
                self.status(f"새 {category} 추가됨: ID {new_id}")
                self._update_edit_buttons()
                self._update_dirty_state()

    def _on_delete_requested(self, category: str, items: list):
        """삭제 요청 핸들러 (컨텍스트 메뉴 - 다중 삭제 지원)

        Args:
            category: 카테고리 ID
            items: 삭제할 항목 리스트
        """
        if not items:
            return

        # 확인 다이얼로그
        count = len(items)
        if count == 1:
            item_id = self._keyword_model._get_item_id(category, items[0])
            msg = f"{category} #{item_id}을(를) 삭제하시겠습니까?"
        else:
            msg = f"{category} {count}개 항목을 삭제하시겠습니까?"

        reply = QMessageBox.question(
            self,
            "삭제 확인",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            for item in items:
                if self._keyword_model.delete_item(category, item):
                    deleted_count += 1

            if deleted_count > 0:
                self._tree.refresh()
                self._current_selection = None
                self.status(f"삭제됨: {category} {deleted_count}개 항목")
                self._update_edit_buttons()
                self._update_dirty_state()

    def _on_copy_requested(self, category: str, items: list):
        """복사 요청 핸들러 (컨텍스트 메뉴 - 다중 복사 지원)

        Args:
            category: 카테고리 ID
            items: 복사할 항목 리스트
        """
        if not items:
            return

        if self._clipboard.copy(category, items, self._keyword_model.filepath):
            self.status(f"복사됨: {category} {len(items)}개 항목")
            self._update_edit_buttons()

    def _on_cut_requested(self, category: str, items: list):
        """잘라내기 요청 핸들러 (컨텍스트 메뉴 - 다중 잘라내기 지원)

        Args:
            category: 카테고리 ID
            items: 잘라낼 항목 리스트
        """
        if not items:
            return

        if self._clipboard.cut(category, items, self._keyword_model.filepath):
            # 잘라내기는 삭제까지 수행
            deleted_count = 0
            for item in items:
                if self._keyword_model.delete_item(category, item):
                    deleted_count += 1

            if deleted_count > 0:
                self._tree.refresh()
                self._current_selection = None
                self.status(f"잘라내기 완료: {category} {deleted_count}개 항목")
                self._update_edit_buttons()
                self._update_dirty_state()

    def _on_paste_requested(self, category: str):
        """붙여넣기 요청 핸들러 (컨텍스트 메뉴)

        Args:
            category: 붙여넣을 대상 카테고리
        """
        if not self._clipboard.has_data():
            return

        # 호환성 확인
        if not self._clipboard.can_paste_to(category):
            src_category = self._clipboard.get_category()
            self.log(f"'{src_category}'를 '{category}'에 붙여넣을 수 없습니다", "warning")
            return

        result = self._clipboard.paste()
        if not result:
            return

        src_category, items, was_cut = result

        # 새 ID 할당 및 추가
        for item in items:
            new_id = self._keyword_model.get_next_id(category)
            # ID 필드 업데이트
            if category == 'nodes':
                item.nid = new_id
            elif category in ('shell', 'solid', 'beam'):
                item.eid = new_id
            elif category == 'parts':
                item.pid = new_id
            elif category == 'materials':
                item.mid = new_id
            elif category == 'sections':
                item.secid = new_id
            elif category == 'sets':
                item.sid = new_id

            self._keyword_model.add_item(category, item)

        self._tree.refresh()
        self.status(f"붙여넣기 완료: {len(items)}개 {category}")
        self._update_edit_buttons()
        self._update_dirty_state()

    def _on_batch_edit_requested(self, category: str, items: list):
        """일괄 수정 요청 핸들러 (컨텍스트 메뉴)

        Args:
            category: 카테고리 ID
            items: 수정할 항목 리스트
        """
        if not items or len(items) < 2:
            self.log("일괄 수정은 2개 이상의 항목이 필요합니다", "warning")
            return

        # BatchEditDialog 표시
        dialog = BatchEditDialog(self, category, items)

        if dialog.exec_() == dialog.Accepted:
            result = dialog.get_result()
            if result:
                # 변경 적용
                changes = dialog.apply_to_items(items)

                # 각 변경사항을 Undo 스택에 기록
                for item, field_name, old_value, new_value in changes:
                    if old_value != new_value:
                        # modify_item은 값을 설정하고 Undo 스택에 기록
                        self._keyword_model.modify_item(category, item, field_name, new_value)

                if changes:
                    self._tree.refresh()
                    self.status(f"일괄 수정 완료: {len(changes)}개 항목")
                    self._update_edit_buttons()
                    self._update_dirty_state()

                    # Card Editor 새로고침
                    if self._current_selection:
                        cat, sel_item = self._current_selection
                        if cat == category:
                            self._card_editor.set_keyword(cat, sel_item)
