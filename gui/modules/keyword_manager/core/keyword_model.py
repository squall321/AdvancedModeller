"""Keyword data model for Keyword Manager"""
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from .exporter import KFileExporter, ExportOptions
from .undo_manager import UndoManager, ModifyCommand, ModifyNodesCommand, AddCommand, DeleteCommand

if TYPE_CHECKING:
    from gui.app_context import ParsedModelData


@dataclass
class CategoryInfo:
    """카테고리 메타데이터"""
    id: str
    name: str
    name_ko: str
    icon: str
    is_group: bool = False
    subcategories: List['CategoryInfo'] = field(default_factory=list)


# 카테고리 정의
KEYWORD_CATEGORIES = [
    CategoryInfo('nodes', 'Nodes', '노드', 'fa5s.dot-circle'),
    CategoryInfo('elements', 'Elements', '요소', 'fa5s.th', is_group=True, subcategories=[
        CategoryInfo('shell', 'Shell', '쉘', 'fa5s.square'),
        CategoryInfo('solid', 'Solid', '솔리드', 'fa5s.cube'),
        CategoryInfo('beam', 'Beam', '빔', 'fa5s.minus'),
    ]),
    CategoryInfo('parts', 'Parts', '파트', 'fa5s.cubes'),
    CategoryInfo('materials', 'Materials', '재료', 'fa5s.palette'),
    CategoryInfo('sections', 'Sections', '섹션', 'fa5s.layer-group'),
    CategoryInfo('contacts', 'Contacts', '접촉', 'fa5s.handshake'),
    CategoryInfo('sets', 'Sets', '세트', 'fa5s.object-group'),
    CategoryInfo('controls', 'Controls', '컨트롤', 'fa5s.sliders-h', is_group=True, subcategories=[
        CategoryInfo('termination', 'Termination', '종료 조건', 'fa5s.stop'),
        CategoryInfo('timestep', 'Timestep', '타임스텝', 'fa5s.clock'),
        CategoryInfo('energy', 'Energy', '에너지', 'fa5s.bolt'),
        CategoryInfo('output', 'Output', '출력', 'fa5s.file-export'),
        CategoryInfo('shell', 'Shell Control', '쉘 제어', 'fa5s.cog'),
        CategoryInfo('contact', 'Contact Control', '접촉 제어', 'fa5s.cogs'),
        CategoryInfo('hourglass', 'Hourglass', '아워글라스', 'fa5s.hourglass'),
        CategoryInfo('bulk_viscosity', 'Bulk Viscosity', '벌크 점성', 'fa5s.water'),
    ]),
    CategoryInfo('databases', 'Databases', '데이터베이스', 'fa5s.database', is_group=True, subcategories=[
        CategoryInfo('binary', 'Binary', 'Binary', 'fa5s.file'),
        CategoryInfo('ascii', 'ASCII', 'ASCII', 'fa5s.file-alt'),
        CategoryInfo('history_node', 'History Node', '히스토리 노드', 'fa5s.chart-line'),
        CategoryInfo('history_element', 'History Element', '히스토리 요소', 'fa5s.chart-bar'),
        CategoryInfo('cross_section', 'Cross Section', '단면력', 'fa5s.grip-lines'),
    ]),
    CategoryInfo('boundaries', 'Boundaries', '경계조건', 'fa5s.border-style', is_group=True, subcategories=[
        CategoryInfo('spc', 'SPC', 'SPC', 'fa5s.lock'),
        CategoryInfo('motion', 'Prescribed Motion', 'Motion', 'fa5s.play'),
    ]),
    CategoryInfo('loads', 'Loads', '하중', 'fa5s.arrow-down', is_group=True, subcategories=[
        CategoryInfo('node', 'Node Load', '노드 하중', 'fa5s.dot-circle'),
        CategoryInfo('segment', 'Segment Load', '세그먼트 하중', 'fa5s.arrows-alt'),
        CategoryInfo('body', 'Body Load', '체적 하중', 'fa5s.globe'),
    ]),
    CategoryInfo('initials', 'Initial', '초기조건', 'fa5s.play-circle', is_group=True, subcategories=[
        CategoryInfo('velocity', 'Initial Velocity', '초기 속도', 'fa5s.tachometer-alt'),
        CategoryInfo('stress', 'Initial Stress', '초기 응력', 'fa5s.compress'),
    ]),
    CategoryInfo('constraineds', 'Constrained', '구속조건', 'fa5s.lock', is_group=True, subcategories=[
        CategoryInfo('rigid_body', 'Rigid Body', '강체', 'fa5s.box'),
        CategoryInfo('joint', 'Joint', '조인트', 'fa5s.link'),
        CategoryInfo('spotweld', 'Spotweld', '스폿웰드', 'fa5s.circle'),
    ]),
]


class KeywordModel:
    """키워드 데이터 모델

    ParsedModelData를 래핑하여 Keyword Manager UI에서 사용할 수 있는
    인터페이스를 제공합니다.
    """

    def __init__(self, parsed_model: Optional['ParsedModelData'] = None):
        self._model = parsed_model
        self._modified_items: Dict[str, set] = {}  # category -> set of item ids
        self._is_dirty: bool = False  # 모델 수정 여부
        self._undo_manager = UndoManager()
        self._export_options = ExportOptions()

    @property
    def is_loaded(self) -> bool:
        """모델 로드 여부"""
        return self._model is not None and self._model.is_loaded

    @property
    def filepath(self) -> str:
        """파일 경로"""
        return self._model.filepath if self._model else ""

    @property
    def filename(self) -> str:
        """파일명"""
        return self._model.filename if self._model else ""

    def set_model(self, parsed_model: 'ParsedModelData'):
        """모델 설정"""
        self._model = parsed_model
        self._modified_items.clear()
        self._is_dirty = False
        self._undo_manager.clear()

    @property
    def undo_manager(self) -> UndoManager:
        """Undo 매니저 반환"""
        return self._undo_manager

    @property
    def export_options(self) -> ExportOptions:
        """Export 옵션 반환"""
        return self._export_options

    @export_options.setter
    def export_options(self, value: ExportOptions):
        """Export 옵션 설정"""
        self._export_options = value

    @property
    def is_dirty(self) -> bool:
        """수정 여부"""
        return self._is_dirty

    def mark_modified(self, category: str, item: Any):
        """항목 수정 표시"""
        self._is_dirty = True
        if category not in self._modified_items:
            self._modified_items[category] = set()

        # 항목 ID 추출
        item_id = self._get_item_id(category, item)
        if item_id is not None:
            self._modified_items[category].add(item_id)

    def _get_item_id(self, category: str, item: Any) -> Optional[int]:
        """항목의 ID 추출"""
        if category == 'nodes':
            return getattr(item, 'nid', None)
        elif category in ('shell', 'solid', 'beam'):
            return getattr(item, 'eid', None)
        elif category == 'parts':
            return getattr(item, 'pid', None)
        elif category == 'materials':
            return getattr(item, 'mid', None)
        elif category == 'sections':
            return getattr(item, 'secid', None)
        elif category == 'sets':
            return getattr(item, 'sid', None)
        return id(item)  # 기본값으로 객체 ID 사용

    def get_modified_count(self) -> int:
        """수정된 항목 총 수"""
        return sum(len(items) for items in self._modified_items.values())

    def clear_modified(self):
        """수정 표시 초기화"""
        self._modified_items.clear()
        self._is_dirty = False

    @staticmethod
    def get_categories() -> List[CategoryInfo]:
        """카테고리 목록"""
        return KEYWORD_CATEGORIES

    def get_category_count(self, category_id: str) -> int:
        """카테고리별 항목 수"""
        if not self._model:
            return 0

        # 최상위 카테고리
        if category_id == 'nodes':
            return len(self._model.nodes)
        elif category_id == 'elements':
            return (len(self._model.shells) +
                    len(self._model.solids) +
                    len(self._model.beams))
        elif category_id == 'parts':
            return len(self._model.parts)
        elif category_id == 'materials':
            return len(self._model.materials)
        elif category_id == 'sections':
            return len(self._model.sections)
        elif category_id == 'contacts':
            return len(self._model.contacts)
        elif category_id == 'sets':
            return len(self._model.sets)

        # 요소 서브카테고리
        elif category_id == 'shell':
            return len(self._model.shells)
        elif category_id == 'solid':
            return len(self._model.solids)
        elif category_id == 'beam':
            return len(self._model.beams)

        # 컨트롤 서브카테고리
        elif category_id in self._model.controls:
            return len(self._model.controls.get(category_id, []))

        # 데이터베이스 서브카테고리
        elif category_id in self._model.databases:
            return len(self._model.databases.get(category_id, []))

        # 경계조건 서브카테고리
        elif category_id in self._model.boundaries:
            return len(self._model.boundaries.get(category_id, []))

        # 하중 서브카테고리
        elif category_id in self._model.loads:
            return len(self._model.loads.get(category_id, []))

        # 초기조건 서브카테고리
        elif category_id in self._model.initials:
            return len(self._model.initials.get(category_id, []))

        # 구속조건 서브카테고리
        elif category_id in self._model.constraineds:
            return len(self._model.constraineds.get(category_id, []))

        # 그룹 카테고리 (controls, databases 등)
        elif category_id == 'controls':
            return sum(len(v) for v in self._model.controls.values())
        elif category_id == 'databases':
            return sum(len(v) for v in self._model.databases.values())
        elif category_id == 'boundaries':
            return sum(len(v) for v in self._model.boundaries.values())
        elif category_id == 'loads':
            return sum(len(v) for v in self._model.loads.values())
        elif category_id == 'initials':
            return sum(len(v) for v in self._model.initials.values())
        elif category_id == 'constraineds':
            return sum(len(v) for v in self._model.constraineds.values())

        return 0

    def get_items(self, category_id: str) -> List[Any]:
        """카테고리별 항목 목록"""
        if not self._model:
            return []

        if category_id == 'nodes':
            return self._model.nodes
        elif category_id == 'parts':
            return self._model.parts
        elif category_id == 'materials':
            return self._model.materials
        elif category_id == 'sections':
            return self._model.sections
        elif category_id == 'contacts':
            return self._model.contacts
        elif category_id == 'sets':
            return self._model.sets
        elif category_id == 'shell':
            return self._model.shells
        elif category_id == 'solid':
            return self._model.solids
        elif category_id == 'beam':
            return self._model.beams

        # 딕셔너리 기반 카테고리
        if category_id in self._model.controls:
            return self._model.controls.get(category_id, [])
        if category_id in self._model.databases:
            return self._model.databases.get(category_id, [])
        if category_id in self._model.boundaries:
            return self._model.boundaries.get(category_id, [])
        if category_id in self._model.loads:
            return self._model.loads.get(category_id, [])
        if category_id in self._model.initials:
            return self._model.initials.get(category_id, [])
        if category_id in self._model.constraineds:
            return self._model.constraineds.get(category_id, [])

        return []

    def get_item_display_text(self, category_id: str, item: Any) -> str:
        """항목의 표시 텍스트"""
        if category_id == 'nodes':
            return f"Node {item.nid}"
        elif category_id == 'parts':
            return f"{item.pid}: {item.name}" if hasattr(item, 'name') else f"Part {item.pid}"
        elif category_id == 'materials':
            mid = getattr(item, 'mid', getattr(item, 'id', '?'))
            title = getattr(item, 'title', getattr(item, 'name', ''))
            return f"{mid}: {title}" if title else f"Material {mid}"
        elif category_id == 'sections':
            sid = getattr(item, 'secid', getattr(item, 'id', '?'))
            title = getattr(item, 'title', '')
            return f"{sid}: {title}" if title else f"Section {sid}"
        elif category_id == 'contacts':
            return f"Contact: {getattr(item, 'keyword_type', 'CONTACT')}"
        elif category_id == 'sets':
            sid = getattr(item, 'sid', '?')
            set_type = getattr(item, 'set_type', 'SET')
            return f"{sid}: {set_type}"
        elif category_id in ('shell', 'solid', 'beam'):
            eid = getattr(item, 'eid', '?')
            return f"Element {eid}"

        # 기타 키워드
        return str(item)[:50]

    def get_item_details(self, category_id: str, item: Any) -> Dict[str, Any]:
        """항목의 상세 정보를 딕셔너리로 반환"""
        details = {}

        # 객체의 모든 public 속성 추출
        for attr in dir(item):
            if not attr.startswith('_'):
                try:
                    value = getattr(item, attr)
                    if not callable(value):
                        details[attr] = value
                except:
                    pass

        return details

    def get_stats(self) -> Dict[str, Any]:
        """모델 통계"""
        if not self._model:
            return {}
        return self._model.get_stats()

    def export_kfile(self, filepath: str) -> bool:
        """K-file로 내보내기

        Args:
            filepath: 저장할 파일 경로

        Returns:
            성공 여부
        """
        if not self._model:
            return False

        try:
            exporter = KFileExporter(self._model, self._export_options)
            success = exporter.export(filepath)
            if success:
                self._is_dirty = False
            return success
        except Exception as e:
            print(f"[KeywordModel] Export error: {e}")
            return False

    def modify_item(self, category: str, item: Any, field_name: str, new_value: Any) -> bool:
        """항목 수정 (Undo 지원)

        Args:
            category: 카테고리 ID
            item: 수정할 항목
            field_name: 필드명
            new_value: 새 값

        Returns:
            성공 여부
        """
        # n1~n8 필드의 경우 nodes 리스트 수정
        if field_name.startswith('n') and field_name[1:].isdigit():
            idx = int(field_name[1:]) - 1
            if hasattr(item, 'nodes'):
                nodes = getattr(item, 'nodes', [])
                old_value = nodes[idx] if idx < len(nodes) else 0
                cmd = ModifyNodesCommand(item, idx, old_value, new_value, category)
                if self._undo_manager.execute(cmd):
                    self.mark_modified(category, item)
                    return True
            return False

        # 일반 속성 수정
        if hasattr(item, field_name):
            old_value = getattr(item, field_name)
            cmd = ModifyCommand(item, field_name, old_value, new_value, category)
            if self._undo_manager.execute(cmd):
                self.mark_modified(category, item)
                return True
        return False

    def add_item(self, category: str, item: Any) -> bool:
        """항목 추가 (Undo 지원)

        Args:
            category: 카테고리 ID
            item: 추가할 항목

        Returns:
            성공 여부
        """
        items_list = self._get_items_list(category)
        if items_list is None:
            return False

        cmd = AddCommand(
            items_list, item, -1, category,
            on_add=lambda c, i: self.mark_modified(c, i)
        )
        return self._undo_manager.execute(cmd)

    def delete_item(self, category: str, item: Any) -> bool:
        """항목 삭제 (Undo 지원)

        Args:
            category: 카테고리 ID
            item: 삭제할 항목

        Returns:
            성공 여부
        """
        items_list = self._get_items_list(category)
        if items_list is None or item not in items_list:
            return False

        cmd = DeleteCommand(
            items_list, item, -1, category,
            on_remove=lambda c, i: self.mark_modified(c, i)
        )
        return self._undo_manager.execute(cmd)

    def _get_items_list(self, category: str) -> Optional[List]:
        """카테고리의 리스트 참조 반환 (직접 수정용)"""
        if not self._model:
            return None

        if category == 'nodes':
            return self._model.nodes
        elif category == 'parts':
            return self._model.parts
        elif category == 'materials':
            return self._model.materials
        elif category == 'sections':
            return self._model.sections
        elif category == 'contacts':
            return self._model.contacts
        elif category == 'sets':
            return self._model.sets
        elif category == 'shell':
            return self._model.shells
        elif category == 'solid':
            return self._model.solids
        elif category == 'beam':
            return self._model.beams
        return None

    def undo(self) -> bool:
        """실행 취소"""
        return self._undo_manager.undo()

    def redo(self) -> bool:
        """다시 실행"""
        return self._undo_manager.redo()

    def can_undo(self) -> bool:
        """실행 취소 가능 여부"""
        return self._undo_manager.can_undo()

    def can_redo(self) -> bool:
        """다시 실행 가능 여부"""
        return self._undo_manager.can_redo()

    def get_next_id(self, category: str) -> int:
        """다음 사용 가능한 ID 반환"""
        items = self.get_items(category)
        if not items:
            return 1

        max_id = 0
        for item in items:
            item_id = self._get_item_id(category, item)
            if item_id and item_id > max_id:
                max_id = item_id
        return max_id + 1
