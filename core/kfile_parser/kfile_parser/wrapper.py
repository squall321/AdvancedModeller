"""Python wrapper for C++ KFileParser

C++ 모듈이 빌드되지 않은 경우 순수 Python 폴백 구현도 포함
"""
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# C++ 모듈 임포트 시도
try:
    from ._kfile_parser import (
        KFileParser as _CppParser,
        ParseResult as _CppResult,
        Node as _CppNode,
        Part as _CppPart,
        Element as _CppElement,
        ElementType as _CppElementType,
        Set as _CppSet,
        SetType as _CppSetType,
        Section as _CppSection,
        SectionType as _CppSectionType,
        Contact as _CppContact,
        ContactType as _CppContactType,
        Material as _CppMaterial,
        MaterialType as _CppMaterialType,
    )
    _USE_CPP = True
except ImportError:
    _USE_CPP = False


class SetType(Enum):
    """Set type enumeration"""
    NODE_LIST = 0
    PART_LIST = 1
    SEGMENT = 2
    SHELL = 3
    SOLID = 4


class SectionType(Enum):
    """Section type enumeration"""
    SHELL = 0
    SOLID = 1
    BEAM = 2


class ContactType(Enum):
    """Contact type enumeration"""
    AUTOMATIC_SINGLE_SURFACE = 0
    AUTOMATIC_SURFACE_TO_SURFACE = 1
    AUTOMATIC_NODES_TO_SURFACE = 2
    AUTOMATIC_GENERAL = 3
    TIED_SURFACE_TO_SURFACE = 4
    TIED_NODES_TO_SURFACE = 5
    TIED_SHELL_EDGE_TO_SURFACE = 6
    SURFACE_TO_SURFACE = 7
    NODES_TO_SURFACE = 8
    OTHER = 99


class MaterialType(Enum):
    """Material type enumeration"""
    ELASTIC = 1
    ORTHOTROPIC_ELASTIC = 2
    PLASTIC_KINEMATIC = 3
    RIGID = 20
    PIECEWISE_LINEAR_PLASTICITY = 24
    FABRIC = 34
    COMPOSITE_DAMAGE = 54
    LAMINATED_COMPOSITE_FABRIC = 58
    COMPOSITE_FAILURE = 59
    OTHER = 0


@dataclass
class NodeData:
    """노드 데이터 (Python-friendly)"""
    nid: int
    x: float
    y: float
    z: float
    tc: int = 0
    rc: int = 0

    @classmethod
    def from_cpp(cls, node) -> 'NodeData':
        """C++ Node에서 변환"""
        return cls(
            nid=node.nid,
            x=node.x, y=node.y, z=node.z,
            tc=node.tc, rc=node.rc
        )


@dataclass
class PartData:
    """파트 데이터 (Python-friendly)"""
    pid: int
    name: str
    secid: int
    mid: int
    eosid: int = 0
    hgid: int = 0
    grav: int = 0
    adpopt: int = 0
    tmid: int = 0

    @classmethod
    def from_cpp(cls, part) -> 'PartData':
        """C++ Part에서 변환"""
        return cls(
            pid=part.pid,
            name=part.name,
            secid=part.secid,
            mid=part.mid,
            eosid=part.eosid,
            hgid=part.hgid,
            grav=part.grav,
            adpopt=part.adpopt,
            tmid=part.tmid
        )


@dataclass
class ElementData:
    """엘리먼트 데이터 (Python-friendly)"""
    eid: int
    pid: int
    nodes: List[int]
    element_type: str  # 'shell', 'solid', or 'beam'
    node_count: int = 0

    @classmethod
    def from_cpp(cls, elem) -> 'ElementData':
        """C++ Element에서 변환"""
        node_list = [elem.nodes[i] for i in range(elem.node_count)]
        type_map = {0: 'shell', 1: 'solid', 2: 'beam'}
        return cls(
            eid=elem.eid,
            pid=elem.pid,
            nodes=node_list,
            element_type=type_map.get(elem.type.value, 'shell'),
            node_count=elem.node_count
        )


@dataclass
class SetData:
    """Set 데이터 (Python-friendly)"""
    sid: int
    set_type: SetType
    ids: List[int] = field(default_factory=list)
    segments: List[Tuple[int, int, int, int]] = field(default_factory=list)
    da1: float = 0.0
    da2: float = 0.0
    da3: float = 0.0
    da4: float = 0.0
    solver: str = "MECH"

    @classmethod
    def from_cpp(cls, s) -> 'SetData':
        """C++ Set에서 변환"""
        set_type_map = {
            0: SetType.NODE_LIST,
            1: SetType.PART_LIST,
            2: SetType.SEGMENT,
            3: SetType.SHELL,
            4: SetType.SOLID,
        }
        set_type = set_type_map.get(s.type.value, SetType.NODE_LIST)

        ids = list(s.ids) if s.ids else []
        segments = [(seg[0], seg[1], seg[2], seg[3]) for seg in s.segments] if s.segments else []

        return cls(
            sid=s.sid,
            set_type=set_type,
            ids=ids,
            segments=segments,
            da1=s.da1,
            da2=s.da2,
            da3=s.da3,
            da4=s.da4,
            solver=s.solver
        )

    @property
    def count(self) -> int:
        """Set의 아이템 수"""
        if self.set_type == SetType.SEGMENT:
            return len(self.segments)
        return len(self.ids)


@dataclass
class SectionData:
    """Section 데이터 (Python-friendly)"""
    secid: int
    section_type: SectionType
    elform: int = 0
    # Shell fields
    shrf: float = 1.0
    nip: int = 2
    propt: float = 1.0
    qr_irid: int = 0
    icomp: int = 0
    setyp: int = 1
    thickness: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    nloc: float = 0.0
    marea: float = 0.0
    idof: float = 0.0
    edgset: float = 0.0
    # Solid fields
    aet: int = 0
    # Beam fields
    cst: float = 0.0
    scoor: float = 0.0
    ts: List[float] = field(default_factory=lambda: [0.0, 0.0])
    tt: List[float] = field(default_factory=lambda: [0.0, 0.0])
    nsloc: float = 0.0
    ntloc: float = 0.0

    @classmethod
    def from_cpp(cls, s) -> 'SectionData':
        """C++ Section에서 변환"""
        type_map = {0: SectionType.SHELL, 1: SectionType.SOLID, 2: SectionType.BEAM}
        section_type = type_map.get(s.type.value, SectionType.SHELL)
        return cls(
            secid=s.secid,
            section_type=section_type,
            elform=s.elform,
            shrf=s.shrf,
            nip=s.nip,
            propt=s.propt,
            qr_irid=s.qr_irid,
            icomp=s.icomp,
            setyp=s.setyp,
            thickness=list(s.thickness),
            nloc=s.nloc,
            marea=s.marea,
            idof=s.idof,
            edgset=s.edgset,
            aet=s.aet,
            cst=s.cst,
            scoor=s.scoor,
            ts=list(s.ts),
            tt=list(s.tt),
            nsloc=s.nsloc,
            ntloc=s.ntloc
        )


@dataclass
class ContactData:
    """Contact 데이터 (Python-friendly)"""
    contact_type: ContactType
    type_name: str = ""
    # Card 1
    ssid: int = 0
    msid: int = 0
    sstyp: int = 0
    mstyp: int = 0
    sboxid: int = 0
    mboxid: int = 0
    spr: int = 0
    mpr: int = 0
    # Card 2
    fs: float = 0.0
    fd: float = 0.0
    dc: float = 0.0
    vc: float = 0.0
    vdc: float = 0.0
    penchk: int = 0
    bt: float = 0.0
    dt: float = 1.0e20
    # Card 3
    sfs: float = 1.0
    sfm: float = 1.0
    sst: float = 0.0
    mst: float = 0.0
    sfst: float = 1.0
    sfmt: float = 1.0
    fsf: float = 1.0
    vsf: float = 1.0
    # Parsing state
    cards_parsed: int = 0

    @classmethod
    def from_cpp(cls, c) -> 'ContactData':
        """C++ Contact에서 변환"""
        type_map = {
            0: ContactType.AUTOMATIC_SINGLE_SURFACE,
            1: ContactType.AUTOMATIC_SURFACE_TO_SURFACE,
            2: ContactType.AUTOMATIC_NODES_TO_SURFACE,
            3: ContactType.AUTOMATIC_GENERAL,
            4: ContactType.TIED_SURFACE_TO_SURFACE,
            5: ContactType.TIED_NODES_TO_SURFACE,
            6: ContactType.TIED_SHELL_EDGE_TO_SURFACE,
            7: ContactType.SURFACE_TO_SURFACE,
            8: ContactType.NODES_TO_SURFACE,
            99: ContactType.OTHER,
        }
        contact_type = type_map.get(c.type.value, ContactType.OTHER)
        return cls(
            contact_type=contact_type,
            type_name=c.type_name,
            ssid=c.ssid, msid=c.msid, sstyp=c.sstyp, mstyp=c.mstyp,
            sboxid=c.sboxid, mboxid=c.mboxid, spr=c.spr, mpr=c.mpr,
            fs=c.fs, fd=c.fd, dc=c.dc, vc=c.vc, vdc=c.vdc,
            penchk=c.penchk, bt=c.bt, dt=c.dt,
            sfs=c.sfs, sfm=c.sfm, sst=c.sst, mst=c.mst,
            sfst=c.sfst, sfmt=c.sfmt, fsf=c.fsf, vsf=c.vsf,
            cards_parsed=c.cards_parsed
        )


@dataclass
class MaterialData:
    """Material 데이터 (Python-friendly)"""
    mid: int
    material_type: MaterialType
    type_name: str = ""
    # Common properties
    ro: float = 0.0
    e: float = 0.0
    pr: float = 0.0
    # Orthotropic properties
    eb: float = 0.0
    ec: float = 0.0
    prca: float = 0.0
    prcb: float = 0.0
    gab: float = 0.0
    gbc: float = 0.0
    gca: float = 0.0
    # Plasticity properties
    sigy: float = 0.0
    etan: float = 0.0
    fail: float = 0.0
    tdel: float = 0.0
    # Rigid properties
    cmo: float = 0.0
    con1: float = 0.0
    con2: float = 0.0
    # Composite strength properties
    xc: float = 0.0
    xt: float = 0.0
    yc: float = 0.0
    yt: float = 0.0
    sc: float = 0.0
    # Additional options
    aopt: int = 0
    macf: int = 0
    # Raw card data
    cards: List[List[float]] = field(default_factory=list)
    cards_parsed: int = 0
    title: str = ""

    @classmethod
    def from_cpp(cls, m) -> 'MaterialData':
        """C++ Material에서 변환"""
        type_map = {
            1: MaterialType.ELASTIC,
            2: MaterialType.ORTHOTROPIC_ELASTIC,
            3: MaterialType.PLASTIC_KINEMATIC,
            20: MaterialType.RIGID,
            24: MaterialType.PIECEWISE_LINEAR_PLASTICITY,
            34: MaterialType.FABRIC,
            54: MaterialType.COMPOSITE_DAMAGE,
            58: MaterialType.LAMINATED_COMPOSITE_FABRIC,
            59: MaterialType.COMPOSITE_FAILURE,
            0: MaterialType.OTHER,
        }
        mat_type = type_map.get(m.type.value, MaterialType.OTHER)
        cards = [list(card) for card in m.cards] if m.cards else []
        return cls(
            mid=m.mid,
            material_type=mat_type,
            type_name=m.type_name,
            ro=m.ro, e=m.e, pr=m.pr,
            eb=m.eb, ec=m.ec, prca=m.prca, prcb=m.prcb,
            gab=m.gab, gbc=m.gbc, gca=m.gca,
            sigy=m.sigy, etan=m.etan, fail=m.fail, tdel=m.tdel,
            cmo=m.cmo, con1=m.con1, con2=m.con2,
            xc=m.xc, xt=m.xt, yc=m.yc, yt=m.yt, sc=m.sc,
            aopt=m.aopt, macf=m.macf,
            cards=cards,
            cards_parsed=m.cards_parsed,
            title=m.title
        )

    def get_card_value(self, card_idx: int, col_idx: int) -> float:
        """Get a value from a specific card and column (0-indexed)"""
        if card_idx < len(self.cards) and col_idx < len(self.cards[card_idx]):
            return self.cards[card_idx][col_idx]
        return 0.0


class ParsedKFile:
    """파싱된 K파일 데이터

    C++ ParseResult를 Python-friendly하게 래핑
    """

    def __init__(self, cpp_result=None):
        self._cpp_result = cpp_result
        self._nodes: Optional[List[NodeData]] = None
        self._parts: Optional[List[PartData]] = None
        self._elements: Optional[List[ElementData]] = None
        self._sets: Optional[List[SetData]] = None
        self._sections: Optional[List[SectionData]] = None
        self._contacts: Optional[List[ContactData]] = None
        self._materials: Optional[List[MaterialData]] = None

        # Python fallback용
        self._py_nodes: List[NodeData] = []
        self._py_parts: List[PartData] = []
        self._py_elements: List[ElementData] = []
        self._py_sets: List[SetData] = []
        self._py_sections: List[SectionData] = []
        self._py_contacts: List[ContactData] = []
        self._py_materials: List[MaterialData] = []
        self._py_node_index: Dict[int, int] = {}
        self._py_part_index: Dict[int, int] = {}
        self._py_element_index: Dict[int, int] = {}
        self._py_set_index: Dict[int, int] = {}
        self._py_section_index: Dict[int, int] = {}
        self._py_contact_index: Dict[int, int] = {}
        self._py_material_index: Dict[int, int] = {}
        self._total_lines = 0
        self._parse_time_ms = 0
        self._warnings: List[str] = []
        self._errors: List[str] = []

    @property
    def nodes(self) -> List[NodeData]:
        """노드 목록"""
        if self._cpp_result is not None:
            if self._nodes is None:
                self._nodes = [NodeData.from_cpp(n) for n in self._cpp_result.nodes]
            return self._nodes
        return self._py_nodes

    @property
    def parts(self) -> List[PartData]:
        """파트 목록"""
        if self._cpp_result is not None:
            if self._parts is None:
                self._parts = [PartData.from_cpp(p) for p in self._cpp_result.parts]
            return self._parts
        return self._py_parts

    @property
    def elements(self) -> List[ElementData]:
        """엘리먼트 목록"""
        if self._cpp_result is not None:
            if self._elements is None:
                self._elements = [ElementData.from_cpp(e) for e in self._cpp_result.elements]
            return self._elements
        return self._py_elements

    @property
    def sets(self) -> List[SetData]:
        """Set 목록"""
        if self._cpp_result is not None:
            if self._sets is None:
                self._sets = [SetData.from_cpp(s) for s in self._cpp_result.sets]
            return self._sets
        return self._py_sets

    @property
    def sections(self) -> List[SectionData]:
        """Section 목록"""
        if self._cpp_result is not None:
            if self._sections is None:
                self._sections = [SectionData.from_cpp(s) for s in self._cpp_result.sections]
            return self._sections
        return self._py_sections

    @property
    def contacts(self) -> List[ContactData]:
        """Contact 목록"""
        if self._cpp_result is not None:
            if self._contacts is None:
                self._contacts = [ContactData.from_cpp(c) for c in self._cpp_result.contacts]
            return self._contacts
        return self._py_contacts

    @property
    def materials(self) -> List[MaterialData]:
        """Material 목록"""
        if self._cpp_result is not None:
            if self._materials is None:
                self._materials = [MaterialData.from_cpp(m) for m in self._cpp_result.materials]
            return self._materials
        return self._py_materials

    @property
    def includes(self):
        """Include 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.includes)
        return []

    @property
    def curves(self):
        """Curve 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.curves)
        return []

    @property
    def boundary_spcs(self):
        """BoundarySPC 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.boundary_spcs)
        return []

    @property
    def boundary_motions(self):
        """BoundaryPrescribedMotion 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.boundary_motions)
        return []

    @property
    def load_nodes(self):
        """LoadNode 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.load_nodes)
        return []

    @property
    def load_segments(self):
        """LoadSegment 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.load_segments)
        return []

    @property
    def load_bodies(self):
        """LoadBody 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.load_bodies)
        return []

    # Control keywords
    @property
    def control_terminations(self):
        """ControlTermination 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.control_terminations)
        return []

    @property
    def control_timesteps(self):
        """ControlTimestep 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.control_timesteps)
        return []

    @property
    def control_energies(self):
        """ControlEnergy 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.control_energies)
        return []

    @property
    def control_outputs(self):
        """ControlOutput 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.control_outputs)
        return []

    @property
    def control_shells(self):
        """ControlShell 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.control_shells)
        return []

    @property
    def control_contacts(self):
        """ControlContact 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.control_contacts)
        return []

    @property
    def control_hourglasses(self):
        """ControlHourglass 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.control_hourglasses)
        return []

    @property
    def control_bulk_viscosities(self):
        """ControlBulkViscosity 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.control_bulk_viscosities)
        return []

    # Database keywords
    @property
    def database_binaries(self):
        """DatabaseBinary 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.database_binaries)
        return []

    @property
    def database_asciis(self):
        """DatabaseASCII 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.database_asciis)
        return []

    @property
    def database_history_nodes(self):
        """DatabaseHistoryNode 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.database_history_nodes)
        return []

    @property
    def database_history_elements(self):
        """DatabaseHistoryElement 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.database_history_elements)
        return []

    @property
    def database_cross_sections(self):
        """DatabaseCrossSection 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.database_cross_sections)
        return []

    # Initial keywords
    @property
    def initial_velocities(self):
        """InitialVelocity 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.initial_velocities)
        return []

    @property
    def initial_stresses(self):
        """InitialStress 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.initial_stresses)
        return []

    # Constrained keywords
    @property
    def constrained_nodal_rigid_bodies(self):
        """ConstrainedNodalRigidBody 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.constrained_nodal_rigid_bodies)
        return []

    @property
    def constrained_extra_nodes(self):
        """ConstrainedExtraNodes 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.constrained_extra_nodes)
        return []

    @property
    def constrained_joints(self):
        """ConstrainedJoint 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.constrained_joints)
        return []

    @property
    def constrained_spotwelds(self):
        """ConstrainedSpotweld 목록 (C++ 직접 반환)"""
        if self._cpp_result is not None:
            return list(self._cpp_result.constrained_spotwelds)
        return []

    def get_node(self, nid: int) -> Optional[NodeData]:
        """ID로 노드 조회"""
        if self._cpp_result is not None:
            idx = self._cpp_result.node_index.get(nid)
            if idx is not None:
                return NodeData.from_cpp(self._cpp_result.nodes[idx])
            return None
        idx = self._py_node_index.get(nid)
        if idx is not None:
            return self._py_nodes[idx]
        return None

    def get_part(self, pid: int) -> Optional[PartData]:
        """ID로 파트 조회"""
        if self._cpp_result is not None:
            idx = self._cpp_result.part_index.get(pid)
            if idx is not None:
                return PartData.from_cpp(self._cpp_result.parts[idx])
            return None
        idx = self._py_part_index.get(pid)
        if idx is not None:
            return self._py_parts[idx]
        return None

    def get_element(self, eid: int) -> Optional[ElementData]:
        """ID로 엘리먼트 조회"""
        if self._cpp_result is not None:
            idx = self._cpp_result.element_index.get(eid)
            if idx is not None:
                return ElementData.from_cpp(self._cpp_result.elements[idx])
            return None
        idx = self._py_element_index.get(eid)
        if idx is not None:
            return self._py_elements[idx]
        return None

    def get_set(self, sid: int) -> Optional[SetData]:
        """ID로 Set 조회"""
        if self._cpp_result is not None:
            idx = self._cpp_result.set_index.get(sid)
            if idx is not None:
                return SetData.from_cpp(self._cpp_result.sets[idx])
            return None
        idx = self._py_set_index.get(sid)
        if idx is not None:
            return self._py_sets[idx]
        return None

    def get_sets_by_type(self, set_type: SetType) -> List[SetData]:
        """타입별 Set 필터링"""
        return [s for s in self.sets if s.set_type == set_type]

    def get_section(self, secid: int) -> Optional[SectionData]:
        """ID로 Section 조회"""
        if self._cpp_result is not None:
            idx = self._cpp_result.section_index.get(secid)
            if idx is not None:
                return SectionData.from_cpp(self._cpp_result.sections[idx])
            return None
        idx = self._py_section_index.get(secid)
        if idx is not None:
            return self._py_sections[idx]
        return None

    def get_sections_by_type(self, section_type: SectionType) -> List[SectionData]:
        """타입별 Section 필터링"""
        return [s for s in self.sections if s.section_type == section_type]

    def get_contact(self, ssid: int) -> Optional[ContactData]:
        """ID로 Contact 조회 (ssid 기준)"""
        if self._cpp_result is not None:
            idx = self._cpp_result.contact_index.get(ssid)
            if idx is not None:
                return ContactData.from_cpp(self._cpp_result.contacts[idx])
            return None
        idx = self._py_contact_index.get(ssid)
        if idx is not None:
            return self._py_contacts[idx]
        return None

    def get_contacts_by_type(self, contact_type: ContactType) -> List[ContactData]:
        """타입별 Contact 필터링"""
        return [c for c in self.contacts if c.contact_type == contact_type]

    def get_material(self, mid: int) -> Optional[MaterialData]:
        """ID로 Material 조회"""
        if self._cpp_result is not None:
            idx = self._cpp_result.material_index.get(mid)
            if idx is not None:
                return MaterialData.from_cpp(self._cpp_result.materials[idx])
            return None
        idx = self._py_material_index.get(mid)
        if idx is not None:
            return self._py_materials[idx]
        return None

    def get_materials_by_type(self, material_type: MaterialType) -> List[MaterialData]:
        """타입별 Material 필터링"""
        return [m for m in self.materials if m.material_type == material_type]

    def get_elements_by_part(self, pid: int) -> List[ElementData]:
        """파트 ID로 엘리먼트 필터링"""
        return [e for e in self.elements if e.pid == pid]

    @property
    def stats(self) -> Dict[str, Any]:
        """파싱 통계"""
        if self._cpp_result is not None:
            return {
                'node_count': len(self._cpp_result.nodes),
                'part_count': len(self._cpp_result.parts),
                'element_count': len(self._cpp_result.elements),
                'set_count': len(self._cpp_result.sets),
                'section_count': len(self._cpp_result.sections),
                'contact_count': len(self._cpp_result.contacts),
                'material_count': len(self._cpp_result.materials),
                'total_lines': self._cpp_result.total_lines,
                'parse_time_ms': self._cpp_result.parse_time_ms,
                'warnings': list(self._cpp_result.warnings),
                'errors': list(self._cpp_result.errors),
                'backend': 'cpp',
            }
        return {
            'node_count': len(self._py_nodes),
            'part_count': len(self._py_parts),
            'element_count': len(self._py_elements),
            'set_count': len(self._py_sets),
            'section_count': len(self._py_sections),
            'contact_count': len(self._py_contacts),
            'material_count': len(self._py_materials),
            'total_lines': self._total_lines,
            'parse_time_ms': self._parse_time_ms,
            'warnings': self._warnings,
            'errors': self._errors,
            'backend': 'python',
        }


class KFileParser:
    """K-File 고속 파서

    C++ 바인딩이 있으면 C++ 사용, 없으면 Python 폴백

    Example:
        parser = KFileParser()
        result = parser.parse("model.k")

        # 노드 접근
        for node in result.nodes:
            print(f"Node {node.nid}: ({node.x}, {node.y}, {node.z})")

        # ID로 조회
        node = result.get_node(12345)
        part = result.get_part(1)

        # Set 접근
        for s in result.sets:
            print(f"Set {s.sid}: {s.set_type.name}, {s.count} items")
    """

    def __init__(
        self,
        parse_nodes: bool = True,
        parse_parts: bool = True,
        parse_elements: bool = True,
        parse_sets: bool = True,
        parse_sections: bool = True,
        parse_contacts: bool = True,
        parse_materials: bool = True,
        parse_includes: bool = True,
        parse_curves: bool = True,
        parse_boundaries: bool = True,
        parse_loads: bool = True,
        parse_controls: bool = True,
        parse_databases: bool = True,
        parse_initials: bool = True,
        parse_constraineds: bool = True,
        build_index: bool = True
    ):
        self._parse_nodes = parse_nodes
        self._parse_parts = parse_parts
        self._parse_elements = parse_elements
        self._parse_sets = parse_sets
        self._parse_sections = parse_sections
        self._parse_contacts = parse_contacts
        self._parse_materials = parse_materials
        self._parse_includes = parse_includes
        self._parse_curves = parse_curves
        self._parse_boundaries = parse_boundaries
        self._parse_loads = parse_loads
        self._parse_controls = parse_controls
        self._parse_databases = parse_databases
        self._parse_initials = parse_initials
        self._parse_constraineds = parse_constraineds
        self._build_index = build_index

        if _USE_CPP:
            self._cpp_parser = _CppParser()
            self._cpp_parser.set_parse_nodes(parse_nodes)
            self._cpp_parser.set_parse_parts(parse_parts)
            self._cpp_parser.set_parse_elements(parse_elements)
            self._cpp_parser.set_parse_sets(parse_sets)
            self._cpp_parser.set_parse_sections(parse_sections)
            self._cpp_parser.set_parse_contacts(parse_contacts)
            self._cpp_parser.set_parse_materials(parse_materials)
            self._cpp_parser.set_parse_includes(parse_includes)
            self._cpp_parser.set_parse_curves(parse_curves)
            self._cpp_parser.set_parse_boundaries(parse_boundaries)
            self._cpp_parser.set_parse_loads(parse_loads)
            self._cpp_parser.set_parse_controls(parse_controls)
            self._cpp_parser.set_parse_databases(parse_databases)
            self._cpp_parser.set_parse_initials(parse_initials)
            self._cpp_parser.set_parse_constraineds(parse_constraineds)
            self._cpp_parser.set_build_index(build_index)
        else:
            self._cpp_parser = None

    @property
    def using_cpp(self) -> bool:
        """C++ 백엔드 사용 중인지 확인"""
        return _USE_CPP

    def parse(self, filepath: str) -> ParsedKFile:
        """K파일 파싱

        Args:
            filepath: K파일 경로

        Returns:
            ParsedKFile: 파싱 결과 객체
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")

        if self._cpp_parser is not None:
            cpp_result = self._cpp_parser.parse_file(str(path))
            return ParsedKFile(cpp_result)
        else:
            return self._parse_python(path)

    def parse_string(self, content: str) -> ParsedKFile:
        """문자열에서 파싱

        Args:
            content: K파일 내용

        Returns:
            ParsedKFile: 파싱 결과 객체
        """
        if self._cpp_parser is not None:
            cpp_result = self._cpp_parser.parse_string(content)
            return ParsedKFile(cpp_result)
        else:
            return self._parse_string_python(content)

    def _parse_python(self, path: Path) -> ParsedKFile:
        """Python 폴백 파싱"""
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return self._parse_string_python(content)

    def _parse_string_python(self, content: str) -> ParsedKFile:
        """Python 폴백 문자열 파싱"""
        import time
        start = time.time()

        result = ParsedKFile()
        state = 'IDLE'
        part_name = ''
        current_set: Optional[SetData] = None
        current_section: Optional[SectionData] = None
        current_contact: Optional[ContactData] = None
        current_material: Optional[MaterialData] = None
        material_expected_cards: int = 1

        lines = content.split('\n')
        result._total_lines = len(lines)

        for line in lines:
            line = line.rstrip()

            # Skip empty
            if not line.strip():
                continue

            # Keyword check
            if line.startswith('*'):
                upper = line.upper()

                # 현재 파싱 중인 set 저장
                if current_set is not None and current_set.sid > 0 and current_set.count > 0:
                    result._py_sets.append(current_set)
                    current_set = None

                # 현재 파싱 중인 material 저장
                if current_material is not None and current_material.mid > 0:
                    result._py_materials.append(current_material)
                    current_material = None

                if upper.startswith('*NODE') and not upper.startswith('*NODE_'):
                    state = 'NODE' if self._parse_nodes else 'IDLE'
                elif upper.startswith('*PART') and not upper.startswith('*PART_'):
                    state = 'PART_NAME' if self._parse_parts else 'IDLE'
                    part_name = ''
                elif upper.startswith('*ELEMENT_SHELL'):
                    state = 'SHELL' if self._parse_elements else 'IDLE'
                elif upper.startswith('*ELEMENT_SOLID'):
                    state = 'SOLID' if self._parse_elements else 'IDLE'
                elif upper.startswith('*ELEMENT_BEAM'):
                    state = 'BEAM' if self._parse_elements else 'IDLE'
                # SET keywords (with _TITLE support)
                elif upper.startswith('*SET_NODE_LIST'):
                    if self._parse_sets:
                        current_set = SetData(sid=0, set_type=SetType.NODE_LIST)
                        state = 'SET_TITLE' if '_TITLE' in upper else 'SET_NODE_HEADER'
                    else:
                        state = 'IDLE'
                elif upper.startswith('*SET_PART_LIST'):
                    if self._parse_sets:
                        current_set = SetData(sid=0, set_type=SetType.PART_LIST)
                        state = 'SET_TITLE' if '_TITLE' in upper else 'SET_PART_HEADER'
                    else:
                        state = 'IDLE'
                elif upper.startswith('*SET_SEGMENT'):
                    if self._parse_sets:
                        current_set = SetData(sid=0, set_type=SetType.SEGMENT)
                        state = 'SET_TITLE' if '_TITLE' in upper else 'SET_SEGMENT_HEADER'
                    else:
                        state = 'IDLE'
                elif upper.startswith('*SET_SHELL'):
                    if self._parse_sets:
                        current_set = SetData(sid=0, set_type=SetType.SHELL)
                        state = 'SET_TITLE' if '_TITLE' in upper else 'SET_SHELL_HEADER'
                    else:
                        state = 'IDLE'
                elif upper.startswith('*SET_SOLID'):
                    if self._parse_sets:
                        current_set = SetData(sid=0, set_type=SetType.SOLID)
                        state = 'SET_TITLE' if '_TITLE' in upper else 'SET_SOLID_HEADER'
                    else:
                        state = 'IDLE'
                # SECTION keywords (with _TITLE support)
                elif upper.startswith('*SECTION_SHELL'):
                    if self._parse_sections:
                        current_section = SectionData(secid=0, section_type=SectionType.SHELL)
                        state = 'SECTION_SHELL_TITLE' if '_TITLE' in upper else 'SECTION_SHELL_HEADER'
                    else:
                        state = 'IDLE'
                elif upper.startswith('*SECTION_SOLID'):
                    if self._parse_sections:
                        current_section = SectionData(secid=0, section_type=SectionType.SOLID)
                        state = 'SECTION_SOLID_TITLE' if '_TITLE' in upper else 'SECTION_SOLID'
                    else:
                        state = 'IDLE'
                elif upper.startswith('*SECTION_BEAM'):
                    if self._parse_sections:
                        current_section = SectionData(secid=0, section_type=SectionType.BEAM)
                        state = 'SECTION_BEAM_TITLE' if '_TITLE' in upper else 'SECTION_BEAM_HEADER'
                    else:
                        state = 'IDLE'
                # CONTACT keywords (with _ID/_TITLE support)
                elif upper.startswith('*CONTACT_'):
                    if self._parse_contacts:
                        type_name = upper[9:]  # After "*CONTACT_"
                        has_id = '_ID' in upper and '_TITLE' not in upper
                        has_title = '_TITLE' in upper
                        # Remove trailing options like _ID, _TITLE
                        for opt in ['_ID', '_TITLE', '_MPP']:
                            if type_name.endswith(opt):
                                type_name = type_name[:-len(opt)]
                                break

                        # Determine contact type
                        if 'AUTOMATIC_SINGLE_SURFACE' in type_name:
                            ct = ContactType.AUTOMATIC_SINGLE_SURFACE
                        elif 'AUTOMATIC_SURFACE_TO_SURFACE' in type_name:
                            ct = ContactType.AUTOMATIC_SURFACE_TO_SURFACE
                        elif 'AUTOMATIC_NODES_TO_SURFACE' in type_name:
                            ct = ContactType.AUTOMATIC_NODES_TO_SURFACE
                        elif 'AUTOMATIC_GENERAL' in type_name:
                            ct = ContactType.AUTOMATIC_GENERAL
                        elif 'TIED_SURFACE_TO_SURFACE' in type_name:
                            ct = ContactType.TIED_SURFACE_TO_SURFACE
                        elif 'TIED_NODES_TO_SURFACE' in type_name:
                            ct = ContactType.TIED_NODES_TO_SURFACE
                        elif 'TIED_SHELL_EDGE_TO_SURFACE' in type_name:
                            ct = ContactType.TIED_SHELL_EDGE_TO_SURFACE
                        elif 'SURFACE_TO_SURFACE' in type_name:
                            ct = ContactType.SURFACE_TO_SURFACE
                        elif 'NODES_TO_SURFACE' in type_name:
                            ct = ContactType.NODES_TO_SURFACE
                        else:
                            ct = ContactType.OTHER

                        current_contact = ContactData(contact_type=ct, type_name=type_name)
                        # Set initial state based on suffix
                        if has_id:
                            state = 'CONTACT_ID'
                        elif has_title:
                            state = 'CONTACT_TITLE'
                        else:
                            state = 'CONTACT_CARD1'
                    else:
                        state = 'IDLE'
                # MAT keywords (with _TITLE support)
                elif upper.startswith('*MAT_'):
                    if self._parse_materials:
                        type_str = upper[5:]  # After "*MAT_"
                        has_title = '_TITLE' in upper
                        # Remove _TITLE suffix for type determination
                        if has_title:
                            type_str = type_str.replace('_TITLE', '')

                        # Determine material type and expected cards
                        if type_str.startswith('ELASTIC') or type_str == '001':
                            mt = MaterialType.ELASTIC
                            material_expected_cards = 1
                        elif type_str.startswith('ORTHOTROPIC') or type_str == '002':
                            mt = MaterialType.ORTHOTROPIC_ELASTIC
                            material_expected_cards = 2
                        elif type_str.startswith('PLASTIC_KINEMATIC') or type_str == '003':
                            mt = MaterialType.PLASTIC_KINEMATIC
                            material_expected_cards = 1
                        elif type_str.startswith('RIGID') or type_str == '020':
                            mt = MaterialType.RIGID
                            material_expected_cards = 3
                        elif type_str.startswith('PIECEWISE') or type_str == '024':
                            mt = MaterialType.PIECEWISE_LINEAR_PLASTICITY
                            material_expected_cards = 2
                        elif type_str.startswith('FABRIC') or type_str == '034':
                            mt = MaterialType.FABRIC
                            material_expected_cards = 4
                        elif type_str.startswith('COMPOSITE_DAMAGE') or type_str in ['054', '055']:
                            mt = MaterialType.COMPOSITE_DAMAGE
                            material_expected_cards = 6
                        elif type_str.startswith('LAMINATED') or type_str == '058':
                            mt = MaterialType.LAMINATED_COMPOSITE_FABRIC
                            material_expected_cards = 5
                        elif type_str.startswith('COMPOSITE_FAILURE') or type_str == '059':
                            mt = MaterialType.COMPOSITE_FAILURE
                            material_expected_cards = 5
                        else:
                            mt = MaterialType.OTHER
                            material_expected_cards = 2  # Default

                        current_material = MaterialData(mid=0, material_type=mt, type_name=type_str)
                        state = 'MATERIAL_TITLE' if has_title else 'MATERIAL_DATA'
                    else:
                        state = 'IDLE'
                else:
                    state = 'IDLE'
                continue

            # Skip comments
            if line.startswith('$'):
                continue

            # Process data
            if state == 'NODE':
                node = self._parse_node_py(line)
                if node:
                    result._py_nodes.append(node)

            elif state == 'PART_NAME':
                part_name = line[:80].strip()
                state = 'PART_DATA'

            elif state == 'PART_DATA':
                part = self._parse_part_py(part_name, line)
                if part:
                    result._py_parts.append(part)
                state = 'IDLE'

            elif state == 'SHELL':
                elem = self._parse_element_py(line, 'shell')
                if elem:
                    result._py_elements.append(elem)

            elif state == 'SOLID':
                elem = self._parse_element_py(line, 'solid')
                if elem:
                    result._py_elements.append(elem)

            elif state == 'BEAM':
                elem = self._parse_element_py(line, 'beam')
                if elem:
                    result._py_elements.append(elem)

            # SET _TITLE state: skip title line and move to header
            elif state == 'SET_TITLE':
                if current_set:
                    # Title is just text, skip it and move to appropriate header
                    if current_set.set_type == SetType.NODE_LIST:
                        state = 'SET_NODE_HEADER'
                    elif current_set.set_type == SetType.PART_LIST:
                        state = 'SET_PART_HEADER'
                    elif current_set.set_type == SetType.SEGMENT:
                        state = 'SET_SEGMENT_HEADER'
                    elif current_set.set_type == SetType.SHELL:
                        state = 'SET_SHELL_HEADER'
                    elif current_set.set_type == SetType.SOLID:
                        state = 'SET_SOLID_HEADER'

            # SET states
            elif state.startswith('SET_') and state.endswith('_HEADER'):
                if current_set:
                    self._parse_set_header_py(line, current_set)
                    # 헤더 파싱 후 데이터 상태로 전환
                    state = state.replace('_HEADER', '_DATA')

            elif state == 'SET_SEGMENT_DATA':
                if current_set:
                    self._parse_segment_data_py(line, current_set)

            elif state.startswith('SET_') and state.endswith('_DATA'):
                if current_set:
                    self._parse_set_data_py(line, current_set)

            # SECTION _TITLE states: skip title line and move to header/data
            elif state == 'SECTION_SHELL_TITLE':
                # Title is just text, skip it and move to header
                state = 'SECTION_SHELL_HEADER'

            elif state == 'SECTION_SOLID_TITLE':
                # Title is just text, skip it and move to data state
                state = 'SECTION_SOLID'

            elif state == 'SECTION_BEAM_TITLE':
                # Title is just text, skip it and move to header
                state = 'SECTION_BEAM_HEADER'

            # SECTION states
            elif state == 'SECTION_SHELL_HEADER':
                if current_section:
                    self._parse_section_shell_header_py(line, current_section)
                    state = 'SECTION_SHELL_DATA'

            elif state == 'SECTION_SHELL_DATA':
                if current_section:
                    self._parse_section_shell_data_py(line, current_section)
                    result._py_sections.append(current_section)
                    current_section = None
                    state = 'IDLE'

            elif state == 'SECTION_SOLID':
                if current_section:
                    self._parse_section_solid_py(line, current_section)
                    result._py_sections.append(current_section)
                    current_section = None
                    state = 'IDLE'

            elif state == 'SECTION_BEAM_HEADER':
                if current_section:
                    self._parse_section_beam_header_py(line, current_section)
                    state = 'SECTION_BEAM_DATA'

            elif state == 'SECTION_BEAM_DATA':
                if current_section:
                    self._parse_section_beam_data_py(line, current_section)
                    result._py_sections.append(current_section)
                    current_section = None
                    state = 'IDLE'

            # CONTACT _ID/_TITLE states: skip ID card or title line and move to CARD1
            elif state == 'CONTACT_ID':
                # _ID card format: CID (10), HEADING (70) - skip it
                state = 'CONTACT_CARD1'

            elif state == 'CONTACT_TITLE':
                # Title is just a text line, skip it
                state = 'CONTACT_CARD1'

            # CONTACT states
            elif state == 'CONTACT_CARD1':
                if current_contact:
                    self._parse_contact_card1_py(line, current_contact)
                    current_contact.cards_parsed = 1
                    state = 'CONTACT_CARD2'

            elif state == 'CONTACT_CARD2':
                if current_contact:
                    self._parse_contact_card2_py(line, current_contact)
                    current_contact.cards_parsed = 2
                    state = 'CONTACT_CARD3'

            elif state == 'CONTACT_CARD3':
                if current_contact:
                    self._parse_contact_card3_py(line, current_contact)
                    current_contact.cards_parsed = 3
                    result._py_contacts.append(current_contact)
                    current_contact = None
                    state = 'IDLE'

            # MATERIAL states
            elif state == 'MATERIAL_TITLE':
                # Title is just text, store it and move to data
                if current_material:
                    current_material.title = line.strip()
                    state = 'MATERIAL_DATA'

            elif state == 'MATERIAL_DATA':
                if current_material:
                    self._parse_material_data_py(line, current_material, material_expected_cards)
                    current_material.cards_parsed += 1
                    if current_material.cards_parsed >= material_expected_cards:
                        result._py_materials.append(current_material)
                        current_material = None
                        state = 'IDLE'

        # 마지막 set 저장
        if current_set is not None and current_set.sid > 0 and current_set.count > 0:
            result._py_sets.append(current_set)

        # 마지막 material 저장
        if current_material is not None and current_material.mid > 0:
            result._py_materials.append(current_material)

        # Build index
        if self._build_index:
            for i, n in enumerate(result._py_nodes):
                result._py_node_index[n.nid] = i
            for i, p in enumerate(result._py_parts):
                result._py_part_index[p.pid] = i
            for i, e in enumerate(result._py_elements):
                result._py_element_index[e.eid] = i
            for i, s in enumerate(result._py_sets):
                result._py_set_index[s.sid] = i
            for i, sec in enumerate(result._py_sections):
                result._py_section_index[sec.secid] = i
            for i, con in enumerate(result._py_contacts):
                result._py_contact_index[con.ssid] = i
            for i, mat in enumerate(result._py_materials):
                result._py_material_index[mat.mid] = i

        result._parse_time_ms = int((time.time() - start) * 1000)
        return result

    def _parse_node_py(self, line: str) -> Optional[NodeData]:
        """Python 노드 파싱"""
        try:
            nid = int(line[0:8].strip() or 0)
            x = float(line[8:24].strip() or 0)
            y = float(line[24:40].strip() or 0)
            z = float(line[40:56].strip() or 0)
            tc = int(line[56:64].strip() or 0) if len(line) > 56 else 0
            rc = int(line[64:72].strip() or 0) if len(line) > 64 else 0
            return NodeData(nid=nid, x=x, y=y, z=z, tc=tc, rc=rc)
        except (ValueError, IndexError):
            return None

    def _parse_part_py(self, name: str, line: str) -> Optional[PartData]:
        """Python 파트 파싱"""
        try:
            pid = int(line[0:10].strip() or 0)
            secid = int(line[10:20].strip() or 0)
            mid = int(line[20:30].strip() or 0)
            return PartData(pid=pid, name=name, secid=secid, mid=mid)
        except (ValueError, IndexError):
            return None

    def _parse_element_py(self, line: str, elem_type: str) -> Optional[ElementData]:
        """Python 엘리먼트 파싱"""
        try:
            eid = int(line[0:8].strip() or 0)
            pid = int(line[8:16].strip() or 0)
            nodes = []
            for i in range(8):
                start = 16 + i * 8
                if start < len(line):
                    nid = int(line[start:start+8].strip() or 0)
                    if nid > 0:
                        nodes.append(nid)
            return ElementData(eid=eid, pid=pid, nodes=nodes,
                               element_type=elem_type, node_count=len(nodes))
        except (ValueError, IndexError):
            return None

    def _parse_set_header_py(self, line: str, s: SetData) -> None:
        """Python Set 헤더 파싱"""
        try:
            s.sid = int(line[0:10].strip() or 0)
            s.da1 = float(line[10:20].strip() or 0) if len(line) > 10 else 0.0
            s.da2 = float(line[20:30].strip() or 0) if len(line) > 20 else 0.0
            s.da3 = float(line[30:40].strip() or 0) if len(line) > 30 else 0.0
            s.da4 = float(line[40:50].strip() or 0) if len(line) > 40 else 0.0
            s.solver = line[50:60].strip() if len(line) > 50 else "MECH"
        except (ValueError, IndexError):
            pass

    def _parse_set_data_py(self, line: str, s: SetData) -> None:
        """Python Set 데이터 파싱 (8 IDs per line)"""
        try:
            for i in range(8):
                start = i * 10
                if start < len(line):
                    id_val = int(line[start:start+10].strip() or 0)
                    if id_val > 0:
                        s.ids.append(id_val)
        except (ValueError, IndexError):
            pass

    def _parse_segment_data_py(self, line: str, s: SetData) -> None:
        """Python Segment 데이터 파싱 (4 nodes per segment)"""
        try:
            n1 = int(line[0:10].strip() or 0)
            n2 = int(line[10:20].strip() or 0) if len(line) > 10 else 0
            n3 = int(line[20:30].strip() or 0) if len(line) > 20 else 0
            n4 = int(line[30:40].strip() or 0) if len(line) > 30 else 0
            if n1 > 0 or n2 > 0 or n3 > 0 or n4 > 0:
                s.segments.append((n1, n2, n3, n4))
        except (ValueError, IndexError):
            pass

    def _parse_section_shell_header_py(self, line: str, sec: SectionData) -> None:
        """Python SECTION_SHELL 헤더 파싱"""
        try:
            sec.secid = int(line[0:10].strip() or 0)
            sec.elform = int(line[10:20].strip() or 0) if len(line) > 10 else 0
            sec.shrf = float(line[20:30].strip() or 1.0) if len(line) > 20 else 1.0
            sec.nip = int(line[30:40].strip() or 2) if len(line) > 30 else 2
            sec.propt = float(line[40:50].strip() or 1.0) if len(line) > 40 else 1.0
            sec.qr_irid = int(line[50:60].strip() or 0) if len(line) > 50 else 0
            sec.icomp = int(line[60:70].strip() or 0) if len(line) > 60 else 0
            sec.setyp = int(line[70:80].strip() or 1) if len(line) > 70 else 1
        except (ValueError, IndexError):
            pass

    def _parse_section_shell_data_py(self, line: str, sec: SectionData) -> None:
        """Python SECTION_SHELL 데이터 파싱"""
        try:
            sec.thickness[0] = float(line[0:10].strip() or 0)
            sec.thickness[1] = float(line[10:20].strip() or 0) if len(line) > 10 else 0.0
            sec.thickness[2] = float(line[20:30].strip() or 0) if len(line) > 20 else 0.0
            sec.thickness[3] = float(line[30:40].strip() or 0) if len(line) > 30 else 0.0
            sec.nloc = float(line[40:50].strip() or 0) if len(line) > 40 else 0.0
            sec.marea = float(line[50:60].strip() or 0) if len(line) > 50 else 0.0
            sec.idof = float(line[60:70].strip() or 0) if len(line) > 60 else 0.0
            sec.edgset = float(line[70:80].strip() or 0) if len(line) > 70 else 0.0
        except (ValueError, IndexError):
            pass

    def _parse_section_solid_py(self, line: str, sec: SectionData) -> None:
        """Python SECTION_SOLID 파싱 (1줄)"""
        try:
            sec.secid = int(line[0:10].strip() or 0)
            sec.elform = int(line[10:20].strip() or 0) if len(line) > 10 else 0
            sec.aet = int(line[20:30].strip() or 0) if len(line) > 20 else 0
        except (ValueError, IndexError):
            pass

    def _parse_section_beam_header_py(self, line: str, sec: SectionData) -> None:
        """Python SECTION_BEAM 헤더 파싱"""
        try:
            sec.secid = int(line[0:10].strip() or 0)
            sec.elform = int(line[10:20].strip() or 0) if len(line) > 10 else 0
            sec.shrf = float(line[20:30].strip() or 1.0) if len(line) > 20 else 1.0
            sec.qr_irid = int(line[30:40].strip() or 0) if len(line) > 30 else 0
            sec.cst = float(line[40:50].strip() or 0) if len(line) > 40 else 0.0
            sec.scoor = float(line[50:60].strip() or 0) if len(line) > 50 else 0.0
        except (ValueError, IndexError):
            pass

    def _parse_section_beam_data_py(self, line: str, sec: SectionData) -> None:
        """Python SECTION_BEAM 데이터 파싱"""
        try:
            sec.ts[0] = float(line[0:10].strip() or 0)
            sec.ts[1] = float(line[10:20].strip() or 0) if len(line) > 10 else 0.0
            sec.tt[0] = float(line[20:30].strip() or 0) if len(line) > 20 else 0.0
            sec.tt[1] = float(line[30:40].strip() or 0) if len(line) > 30 else 0.0
            sec.nsloc = float(line[40:50].strip() or 0) if len(line) > 40 else 0.0
            sec.ntloc = float(line[50:60].strip() or 0) if len(line) > 50 else 0.0
        except (ValueError, IndexError):
            pass

    def _parse_contact_card1_py(self, line: str, con: ContactData) -> None:
        """Python CONTACT Card 1 파싱: ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr"""
        try:
            con.ssid = int(line[0:10].strip() or 0)
            con.msid = int(line[10:20].strip() or 0) if len(line) > 10 else 0
            con.sstyp = int(line[20:30].strip() or 0) if len(line) > 20 else 0
            con.mstyp = int(line[30:40].strip() or 0) if len(line) > 30 else 0
            con.sboxid = int(line[40:50].strip() or 0) if len(line) > 40 else 0
            con.mboxid = int(line[50:60].strip() or 0) if len(line) > 50 else 0
            con.spr = int(line[60:70].strip() or 0) if len(line) > 60 else 0
            con.mpr = int(line[70:80].strip() or 0) if len(line) > 70 else 0
        except (ValueError, IndexError):
            pass

    def _parse_contact_card2_py(self, line: str, con: ContactData) -> None:
        """Python CONTACT Card 2 파싱: fs, fd, dc, vc, vdc, penchk, bt, dt"""
        try:
            con.fs = float(line[0:10].strip() or 0)
            con.fd = float(line[10:20].strip() or 0) if len(line) > 10 else 0.0
            con.dc = float(line[20:30].strip() or 0) if len(line) > 20 else 0.0
            con.vc = float(line[30:40].strip() or 0) if len(line) > 30 else 0.0
            con.vdc = float(line[40:50].strip() or 0) if len(line) > 40 else 0.0
            con.penchk = int(line[50:60].strip() or 0) if len(line) > 50 else 0
            con.bt = float(line[60:70].strip() or 0) if len(line) > 60 else 0.0
            con.dt = float(line[70:80].strip() or 1.0e20) if len(line) > 70 else 1.0e20
        except (ValueError, IndexError):
            pass

    def _parse_contact_card3_py(self, line: str, con: ContactData) -> None:
        """Python CONTACT Card 3 파싱: sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf"""
        try:
            con.sfs = float(line[0:10].strip() or 1.0)
            con.sfm = float(line[10:20].strip() or 1.0) if len(line) > 10 else 1.0
            con.sst = float(line[20:30].strip() or 0) if len(line) > 20 else 0.0
            con.mst = float(line[30:40].strip() or 0) if len(line) > 30 else 0.0
            con.sfst = float(line[40:50].strip() or 1.0) if len(line) > 40 else 1.0
            con.sfmt = float(line[50:60].strip() or 1.0) if len(line) > 50 else 1.0
            con.fsf = float(line[60:70].strip() or 1.0) if len(line) > 60 else 1.0
            con.vsf = float(line[70:80].strip() or 1.0) if len(line) > 70 else 1.0
        except (ValueError, IndexError):
            pass

    def _parse_material_data_py(self, line: str, mat: MaterialData, expected_cards: int) -> None:
        """Python Material 데이터 파싱 (10-column fixed width format)

        Parses material card data. Common fields (mid, ro, e, pr) are extracted
        from the first card. Raw card data is stored for all cards.
        """
        try:
            # Parse 8 values per card (10 chars each)
            card_values = []
            for i in range(8):
                start = i * 10
                if start < len(line):
                    val_str = line[start:start+10].strip()
                    if val_str:
                        try:
                            card_values.append(float(val_str))
                        except ValueError:
                            card_values.append(0.0)
                    else:
                        card_values.append(0.0)
                else:
                    card_values.append(0.0)

            # Store raw card data
            mat.cards.append(card_values)

            # Extract common fields from first card
            if mat.cards_parsed == 0:  # First card
                mat.mid = int(card_values[0])
                mat.ro = card_values[1]
                mat.e = card_values[2]
                mat.pr = card_values[3]

                # Material-specific parsing based on type
                if mat.material_type == MaterialType.PIECEWISE_LINEAR_PLASTICITY:
                    # Card 1: mid, ro, e, pr, sigy, etan, fail, tdel
                    mat.sigy = card_values[4]
                    mat.etan = card_values[5]
                    mat.fail = card_values[6]
                    mat.tdel = card_values[7]
                elif mat.material_type == MaterialType.ORTHOTROPIC_ELASTIC:
                    # Card 1: mid, ro, ea, eb, ec, prba, prca, prcb
                    # Note: e is ea, pr is prba
                    mat.eb = card_values[3]
                    mat.ec = card_values[4]
                    mat.pr = card_values[5]  # prba
                    mat.prca = card_values[6]
                    mat.prcb = card_values[7]
                elif mat.material_type == MaterialType.COMPOSITE_DAMAGE:
                    # Card 1: mid, ro, ea, eb, (ec), prba, tau1, gamma1
                    mat.eb = card_values[3]
                    mat.ec = card_values[4]
                    mat.pr = card_values[5]  # prba

            # Second card parsing for orthotropic/composite materials
            elif mat.cards_parsed == 1:
                if mat.material_type == MaterialType.ORTHOTROPIC_ELASTIC:
                    # Card 2: gab, gbc, gca, aopt, g, sigf
                    mat.gab = card_values[0]
                    mat.gbc = card_values[1]
                    mat.gca = card_values[2]
                    mat.aopt = int(card_values[3])
                elif mat.material_type == MaterialType.COMPOSITE_DAMAGE:
                    # Card 2: gab, gbc, gca, kfail, aopt, ...
                    mat.gab = card_values[0]
                    mat.gbc = card_values[1]
                    mat.gca = card_values[2]
                    mat.aopt = int(card_values[4])
                elif mat.material_type == MaterialType.RIGID:
                    # Card 2: cmo, con1, con2, ...
                    mat.cmo = card_values[0]
                    mat.con1 = card_values[1]
                    mat.con2 = card_values[2]

            # Third card for composite materials (strength values)
            elif mat.cards_parsed == 2:
                if mat.material_type in [MaterialType.COMPOSITE_DAMAGE,
                                         MaterialType.LAMINATED_COMPOSITE_FABRIC,
                                         MaterialType.COMPOSITE_FAILURE]:
                    # Card 3: xc, xt, yc, yt, sc, ...
                    mat.xc = card_values[0]
                    mat.xt = card_values[1]
                    mat.yc = card_values[2]
                    mat.yt = card_values[3]
                    mat.sc = card_values[4]

        except (ValueError, IndexError):
            pass
