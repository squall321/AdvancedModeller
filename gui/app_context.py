"""App context - shared state between modules"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pathlib import Path

from core import ConfigManager, MaterialDatabase

# C++ 파서 가용성 확인
try:
    from core.KooDynaKeyword import KFileReader, is_fast_parser_available
    _KFILE_READER_AVAILABLE = is_fast_parser_available()
except ImportError:
    _KFILE_READER_AVAILABLE = False
    KFileReader = None

# 기본 Python 파서 (fallback)
from core import KFileParser as BasicKFileParser


@dataclass
class ParsedModelData:
    """파싱된 K-file 모델 데이터를 저장하는 클래스

    모든 모듈에서 공유하는 중앙 데이터 저장소입니다.
    C++ 파서로 파싱한 결과를 캐시하여 재파싱을 방지합니다.
    """

    # 파일 정보
    filepath: str = ""
    filename: str = ""
    parse_time_ms: float = 0.0

    # 기본 통계
    node_count: int = 0
    element_count: int = 0
    part_count: int = 0

    # KFileReader 인스턴스 (C++ 파서 결과)
    _reader: Optional['KFileReader'] = None

    # 캐시된 데이터 (lazy loading)
    _nodes_cache: Optional[List] = None
    _parts_cache: Optional[List] = None
    _elements_cache: Optional[Dict] = None
    _sets_cache: Optional[List] = None
    _sections_cache: Optional[List] = None
    _contacts_cache: Optional[List] = None
    _materials_cache: Optional[List] = None
    _controls_cache: Optional[Dict] = None
    _databases_cache: Optional[Dict] = None
    _boundaries_cache: Optional[Dict] = None
    _loads_cache: Optional[Dict] = None
    _initials_cache: Optional[Dict] = None
    _constraineds_cache: Optional[Dict] = None

    @property
    def is_loaded(self) -> bool:
        """모델이 로드되었는지 확인"""
        return self._reader is not None

    @property
    def reader(self) -> Optional['KFileReader']:
        """KFileReader 인스턴스 직접 접근"""
        return self._reader

    # ========== 노드 ==========
    @property
    def nodes(self) -> List:
        """노드 목록 (lazy loading)"""
        if self._nodes_cache is None and self._reader:
            # ParsedKFile에서 직접 접근
            parsed = self._reader._parsed
            self._nodes_cache = list(parsed.nodes) if parsed else []
        return self._nodes_cache or []

    def get_node_by_id(self, nid: int):
        """ID로 노드 검색"""
        if self._reader and self._reader._parsed:
            return self._reader._parsed.get_node(nid)
        return None

    # ========== 파트 ==========
    @property
    def parts(self) -> List:
        """파트 목록 (lazy loading)"""
        if self._parts_cache is None and self._reader:
            parsed = self._reader._parsed
            self._parts_cache = list(parsed.parts) if parsed else []
        return self._parts_cache or []

    def get_part_by_id(self, pid: int):
        """ID로 파트 검색"""
        if self._reader and self._reader._parsed:
            return self._reader._parsed.get_part(pid)
        return None

    def get_part_ids(self) -> List[int]:
        """파트 ID 목록"""
        return [p.pid for p in self.parts]

    # ========== 요소 ==========
    @property
    def elements(self) -> Dict:
        """요소 목록 (타입별 딕셔너리)"""
        if self._elements_cache is None and self._reader:
            parsed = self._reader._parsed
            if parsed:
                # elements는 리스트, element_type으로 필터링
                all_elements = list(parsed.elements)
                self._elements_cache = {
                    'shell': [e for e in all_elements if e.element_type == 'shell'],
                    'solid': [e for e in all_elements if e.element_type == 'solid'],
                    'beam': [e for e in all_elements if e.element_type == 'beam'],
                }
            else:
                self._elements_cache = {'shell': [], 'solid': [], 'beam': []}
        return self._elements_cache or {'shell': [], 'solid': [], 'beam': []}

    @property
    def shells(self) -> List:
        return self.elements.get('shell', [])

    @property
    def solids(self) -> List:
        return self.elements.get('solid', [])

    @property
    def beams(self) -> List:
        return self.elements.get('beam', [])

    # ========== 세트 ==========
    @property
    def sets(self) -> List:
        """세트 목록"""
        if self._sets_cache is None and self._reader:
            parsed = self._reader._parsed
            self._sets_cache = list(parsed.sets) if parsed else []
        return self._sets_cache or []

    # ========== 섹션 ==========
    @property
    def sections(self) -> List:
        """섹션 목록"""
        if self._sections_cache is None and self._reader:
            parsed = self._reader._parsed
            self._sections_cache = list(parsed.sections) if parsed else []
        return self._sections_cache or []

    # ========== 접촉 ==========
    @property
    def contacts(self) -> List:
        """접촉 목록"""
        if self._contacts_cache is None and self._reader:
            parsed = self._reader._parsed
            self._contacts_cache = list(parsed.contacts) if parsed else []
        return self._contacts_cache or []

    # ========== 재료 ==========
    @property
    def materials(self) -> List:
        """재료 목록"""
        if self._materials_cache is None and self._reader:
            parsed = self._reader._parsed
            self._materials_cache = list(parsed.materials) if parsed else []
        return self._materials_cache or []

    # ========== 컨트롤 ==========
    @property
    def controls(self) -> Dict:
        """컨트롤 키워드"""
        if self._controls_cache is None and self._reader:
            parsed = self._reader._parsed
            if parsed:
                self._controls_cache = {
                    'termination': list(parsed.control_terminations),
                    'timestep': list(parsed.control_timesteps),
                    'energy': list(parsed.control_energies),
                    'output': list(parsed.control_outputs),
                    'shell': list(parsed.control_shells),
                    'contact': list(parsed.control_contacts),
                    'hourglass': list(parsed.control_hourglasses),
                    'bulk_viscosity': list(parsed.control_bulk_viscosities),
                }
            else:
                self._controls_cache = {}
        return self._controls_cache or {}

    # ========== 데이터베이스 ==========
    @property
    def databases(self) -> Dict:
        """데이터베이스 출력 설정"""
        if self._databases_cache is None and self._reader:
            parsed = self._reader._parsed
            if parsed:
                self._databases_cache = {
                    'binary': list(parsed.database_binaries),
                    'ascii': list(parsed.database_asciis),
                    'history_node': list(parsed.database_history_nodes),
                    'history_element': list(parsed.database_history_elements),
                    'cross_section': list(parsed.database_cross_sections),
                }
            else:
                self._databases_cache = {}
        return self._databases_cache or {}

    # ========== 경계조건 ==========
    @property
    def boundaries(self) -> Dict:
        """경계조건"""
        if self._boundaries_cache is None and self._reader:
            parsed = self._reader._parsed
            if parsed:
                self._boundaries_cache = {
                    'spc': list(parsed.boundary_spcs),
                    'motion': list(parsed.boundary_motions),
                }
            else:
                self._boundaries_cache = {}
        return self._boundaries_cache or {}

    # ========== 하중 ==========
    @property
    def loads(self) -> Dict:
        """하중 조건"""
        if self._loads_cache is None and self._reader:
            parsed = self._reader._parsed
            if parsed:
                self._loads_cache = {
                    'node': list(parsed.load_nodes),
                    'segment': list(parsed.load_segments),
                    'body': list(parsed.load_bodies),
                }
            else:
                self._loads_cache = {}
        return self._loads_cache or {}

    # ========== 초기조건 ==========
    @property
    def initials(self) -> Dict:
        """초기조건"""
        if self._initials_cache is None and self._reader:
            parsed = self._reader._parsed
            if parsed:
                self._initials_cache = {
                    'velocity': list(parsed.initial_velocities),
                    'stress': list(parsed.initial_stresses),
                }
            else:
                self._initials_cache = {}
        return self._initials_cache or {}

    # ========== 구속조건 ==========
    @property
    def constraineds(self) -> Dict:
        """구속조건"""
        if self._constraineds_cache is None and self._reader:
            parsed = self._reader._parsed
            if parsed:
                self._constraineds_cache = {
                    'rigid_body': list(parsed.constrained_nodal_rigid_bodies),
                    'joint': list(parsed.constrained_joints),
                    'spotweld': list(parsed.constrained_spotwelds),
                }
            else:
                self._constraineds_cache = {}
        return self._constraineds_cache or {}

    # ========== 통계 ==========
    def get_stats(self) -> Dict[str, Any]:
        """모델 통계 정보"""
        return {
            'filepath': self.filepath,
            'filename': self.filename,
            'parse_time_ms': self.parse_time_ms,
            'nodes': len(self.nodes),
            'parts': len(self.parts),
            'elements': {
                'shell': len(self.shells),
                'solid': len(self.solids),
                'beam': len(self.beams),
                'total': len(self.shells) + len(self.solids) + len(self.beams),
            },
            'sets': len(self.sets),
            'sections': len(self.sections),
            'contacts': len(self.contacts),
            'materials': len(self.materials),
        }

    def clear_cache(self):
        """캐시 초기화"""
        self._nodes_cache = None
        self._parts_cache = None
        self._elements_cache = None
        self._sets_cache = None
        self._sections_cache = None
        self._contacts_cache = None
        self._materials_cache = None
        self._controls_cache = None
        self._databases_cache = None
        self._boundaries_cache = None
        self._loads_cache = None
        self._initials_cache = None
        self._constraineds_cache = None


@dataclass
class AppContext:
    """
    모듈들이 공유하는 데이터 및 서비스

    사용 예시:
        ctx = AppContext()

        # K-file 로드 (C++ 고속 파서 사용)
        if ctx.load_k_file("/path/to/model.k"):
            nodes = ctx.model.nodes
            parts = ctx.model.parts
            stats = ctx.model.get_stats()

        # Material 로드
        ctx.load_materials("/path/to/MaterialSource.txt")
        names = ctx.material_db.get_names()
    """

    # 서비스
    config: ConfigManager = field(default_factory=ConfigManager)
    material_db: MaterialDatabase = field(default_factory=MaterialDatabase)

    # 파싱된 모델 데이터 (새로 추가)
    model: ParsedModelData = field(default_factory=ParsedModelData)

    # 기본 파서 (fallback, 호환성)
    _basic_parser: BasicKFileParser = field(default_factory=BasicKFileParser)

    # 공유 상태
    current_k_file: str = ""
    current_material_file: str = ""
    current_project_path: str = ""

    @property
    def is_fast_parser_available(self) -> bool:
        """C++ 고속 파서 사용 가능 여부"""
        return _KFILE_READER_AVAILABLE

    def load_k_file(self, path: str, use_fast_parser: bool = True) -> bool:
        """K파일 로드

        Args:
            path: K-file 경로
            use_fast_parser: C++ 고속 파서 사용 여부 (기본: True)

        Returns:
            성공 여부
        """
        try:
            filepath = Path(path)
            if not filepath.exists():
                return False

            if use_fast_parser and _KFILE_READER_AVAILABLE:
                # C++ 고속 파서 사용
                import time
                start = time.perf_counter()

                reader = KFileReader(
                    str(path),
                    parse_nodes=True,
                    parse_parts=True,
                    parse_elements=True,
                    parse_sets=True,
                    parse_sections=True,
                    parse_contacts=True,
                    parse_materials=True,
                    parse_includes=True,
                    parse_curves=True,
                    parse_boundaries=True,
                    parse_loads=True,
                    parse_controls=True,
                    parse_databases=True,
                    parse_initials=True,
                    parse_constraineds=True,
                )

                elapsed = (time.perf_counter() - start) * 1000

                # 모델 데이터 저장
                self.model = ParsedModelData(
                    filepath=str(path),
                    filename=filepath.name,
                    parse_time_ms=elapsed,
                )
                # _reader를 별도로 설정 (dataclass 생성자에서 underscore 필드 처리 문제 회피)
                self.model._reader = reader

                # 통계 업데이트
                stats = reader.stats
                self.model.node_count = stats.get('nodes', 0)
                self.model.element_count = stats.get('elements', {}).get('total', 0)
                self.model.part_count = stats.get('parts', 0)

            else:
                # 기본 Python 파서 사용 (Part ID만)
                part_ids = self._basic_parser.parse(str(path))

                self.model = ParsedModelData(
                    filepath=str(path),
                    filename=filepath.name,
                    part_count=len(part_ids),
                )

            self.current_k_file = str(path)
            return True

        except Exception as e:
            print(f"K-file 로드 오류: {e}")
            return False

    def load_materials(self, path: str) -> bool:
        """Material DB 로드"""
        if self.material_db.load(path):
            self.current_material_file = path
            return True
        return False

    def get_part_ids(self) -> List[int]:
        """파싱된 Part ID 목록"""
        if self.model.is_loaded:
            return self.model.get_part_ids()
        return []

    def get_material_names(self) -> List[str]:
        """Material 이름 목록"""
        return self.material_db.get_names() if self.material_db else []

    def clear_model(self):
        """현재 모델 데이터 초기화"""
        self.model = ParsedModelData()
        self.current_k_file = ""

    # ========== 편의 메서드 (model 프록시) ==========

    @property
    def nodes(self):
        """노드 목록 (model.nodes 프록시)"""
        return self.model.nodes

    @property
    def parts(self):
        """파트 목록 (model.parts 프록시)"""
        return self.model.parts

    @property
    def elements(self):
        """요소 목록 (model.elements 프록시)"""
        return self.model.elements

    @property
    def contacts(self):
        """접촉 목록 (model.contacts 프록시)"""
        return self.model.contacts

    @property
    def materials(self):
        """재료 목록 (model.materials 프록시)"""
        return self.model.materials
