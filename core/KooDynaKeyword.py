"""KooDynaKeyword - 고속 K-file 파서 래퍼

기존 KooDynaKeyword.py와 호환되는 API를 제공하면서
pybind11 기반 고속 파서를 사용합니다.

사용법:
    # 방법 1: 직접 임포트
    from KooDynaKeyword import DynaNode, Part, ElementShell, ElementSolid, KFileReader

    # 방법 2: 기존 코드와 동일하게 사용
    reader = KFileReader("model.k")
    nodes = reader.get_nodes()      # DynaNode 객체 반환
    parts = reader.get_parts()      # Part 객체 반환

배포 방법:
    1. KooDynaKeyword.py 파일과 kfile_parser/ 폴더를 함께 복사
    2. 기존 KooDynaKeyword.py를 이 파일로 교체
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import numpy as np

# kfile_parser 모듈 임포트 시도
try:
    from kfile_parser import KFileParser, ParsedKFile
    _FAST_PARSER_AVAILABLE = True
except ImportError:
    _FAST_PARSER_AVAILABLE = False


def is_fast_parser_available() -> bool:
    """고속 파서(C++) 사용 가능 여부"""
    return _FAST_PARSER_AVAILABLE


class DynaKeyword:
    """LS-DYNA 키워드 기본 클래스 (호환성)"""

    def __init__(self, keyword_name: str):
        self.keyword_name = keyword_name
        self.parameters = []

    def parse_whole(self, cur_string: str, chunk_list: List[int]) -> List[str]:
        """고정 폭 컬럼 파싱"""
        result = []
        pos = 0
        for width in chunk_list:
            if pos < len(cur_string):
                field = cur_string[pos:pos + width]
                result.append(field.strip())
                pos += width
            else:
                result.append('')
        return result


class DynaNode(DynaKeyword):
    """노드 키워드 클래스 (기존 API 호환)

    기존 사용법:
        node = DynaNode()
        node.parse(node_keywords)
        nid = node.NID(0, 0)
        x = node.X(0, 0)

    새로운 사용법:
        node = DynaNode.from_parsed(parsed_kfile)
        node_list = node.getNodeList()  # numpy array
    """

    def __init__(self):
        super().__init__("NODE")
        self._node_data: List[NodeData] = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaNode':
        """ParsedKFile에서 DynaNode 생성"""
        instance = cls()
        instance._node_data = parsed.nodes
        # 호환성을 위해 parameters도 채움
        instance.parameters = [[]]
        for node in parsed.nodes:
            instance.parameters[0].append([
                str(node.nid),
                str(node.x),
                str(node.y),
                str(node.z),
                str(node.tc),
                str(node.rc)
            ])
        return instance

    def parse(self, node_keywords):
        """기존 파싱 메서드 (하위 호환성)"""
        for i in range(len(node_keywords)):
            parameter_list = []
            for j in range(len(node_keywords[i])):
                parameters = self.parse_whole(node_keywords[i][j], [8, 16, 16, 16, 8, 8])
                parameter_list.append(parameters)
            self.parameters.append(parameter_list)

    def NID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][0]

    def X(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1]

    def Y(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][2]

    def Z(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][3]

    def TC(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][4]

    def RC(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][5]

    def getNodeList(self) -> np.ndarray:
        """노드 목록을 numpy 배열로 반환

        Returns:
            np.ndarray: (N, 6) 배열 [NID, X, Y, Z, TC, RC]
        """
        if self._node_data:
            # 고속 파서에서 로드된 데이터
            data = np.zeros((len(self._node_data), 6))
            for i, node in enumerate(self._node_data):
                data[i] = [node.nid, node.x, node.y, node.z, node.tc, node.rc]
            return data

        # 기존 방식 (parameters에서)
        n_total = sum(len(param) for param in self.parameters)
        data = np.zeros((n_total, 6))
        idx = 0
        for param in self.parameters:
            for entry in param:
                try:
                    data[idx, :len(entry)] = [float(x) if x.strip() else 0 for x in entry]
                except ValueError:
                    data[idx, :len(entry)] = 0
                idx += 1
        return data

    def write(self, stream):
        """K파일 형식으로 출력"""
        for i, param_list in enumerate(self.parameters):
            ordinal = "st" if i == 0 else "nd" if i == 1 else "rd" if i == 2 else "th"
            stream.write(f"$$ {i+1}{ordinal} Node List\n")
            stream.write("*NODE\n")
            stream.write("$$   NID               X               Y               Z      TC      RC\n")
            for param in param_list:
                formatted = f"{param[0]:>8}{param[1]:>16}{param[2]:>16}{param[3]:>16}{param[4]:>8}{param[5]:>8}"
                stream.write(formatted + "\n")


class Part(DynaKeyword):
    """파트 키워드 클래스 (기존 API 호환)"""

    def __init__(self):
        super().__init__("PART")
        self._part_data: List[PartData] = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'Part':
        """ParsedKFile에서 Part 생성"""
        instance = cls()
        instance._part_data = parsed.parts
        # 호환성을 위해 parameters도 채움
        instance.parameters = [[]]
        for part in parsed.parts:
            instance.parameters[0].append([
                [part.name],
                [str(part.pid), str(part.secid), str(part.mid),
                 str(part.eosid), str(part.hgid), str(part.grav),
                 str(part.adpopt), str(part.tmid)]
            ])
        return instance

    def parse(self, part_keywords):
        """기존 파싱 메서드 (하위 호환성)"""
        for i in range(len(part_keywords)):
            part_ith = part_keywords[i]
            parameter_matrix = []
            for j in range(0, len(part_ith), 2):
                parameter_list = []
                parameters = self.parse_whole(part_ith[j], [80])
                parameter_list.append(parameters)
                parameters = self.parse_whole(part_ith[j+1], [10, 10, 10, 10, 10, 10, 10, 10])
                parameter_list.append(parameters)
                parameter_matrix.append(parameter_list)
            self.parameters.append(parameter_matrix)

    def NAME(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][0]

    def PID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1][0]

    def SECID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1][1]

    def MID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1][2]

    def EOSID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1][3]

    def HGID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1][4]

    def GRAV(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1][5]

    def ADPOPT(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1][6]

    def TMID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1][7]

    def getPartList(self) -> np.ndarray:
        """파트 목록을 numpy 배열로 반환

        Returns:
            np.ndarray: (N, 8) 배열 [PID, SECID, MID, EOSID, HGID, GRAV, ADPOPT, TMID]
        """
        if self._part_data:
            data = np.zeros((len(self._part_data), 8))
            for i, part in enumerate(self._part_data):
                data[i] = [part.pid, part.secid, part.mid, part.eosid,
                           part.hgid, part.grav, part.adpopt, part.tmid]
            return data

        n_total = sum(len(param) for param in self.parameters)
        data = np.zeros((n_total, 8))
        idx = 0
        for param in self.parameters:
            for entry in param:
                try:
                    data[idx] = [float(x) if x.strip() else 0 for x in entry[1]]
                except (ValueError, IndexError):
                    pass
                idx += 1
        return data


class ElementShell(DynaKeyword):
    """쉘 엘리먼트 키워드 클래스 (기존 API 호환)"""

    def __init__(self):
        super().__init__("ELEMENT_SHELL")
        self._element_data: List[ElementData] = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'ElementShell':
        """ParsedKFile에서 ElementShell 생성"""
        instance = cls()
        instance._element_data = [e for e in parsed.elements if e.element_type == 'shell']
        # 호환성을 위해 parameters도 채움
        instance.parameters = [[]]
        for elem in instance._element_data:
            nodes = elem.nodes + [0] * (8 - len(elem.nodes))
            instance.parameters[0].append([
                str(elem.eid), str(elem.pid),
                str(nodes[0]), str(nodes[1]), str(nodes[2]), str(nodes[3]),
                str(nodes[4]), str(nodes[5]), str(nodes[6]), str(nodes[7])
            ])
        return instance

    def parse(self, element_keywords):
        """기존 파싱 메서드"""
        for i in range(len(element_keywords)):
            parameter_list = []
            for j in range(len(element_keywords[i])):
                parameters = self.parse_whole(element_keywords[i][j],
                                               [8, 8, 8, 8, 8, 8, 8, 8, 8, 8])
                parameter_list.append(parameters)
            self.parameters.append(parameter_list)

    def EID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][0]

    def PID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1]

    def N1(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][2]

    def N2(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][3]

    def N3(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][4]

    def N4(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][5]

    def N5(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][6]

    def N6(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][7]

    def N7(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][8]

    def N8(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][9]

    def getElementList(self) -> np.ndarray:
        """엘리먼트 목록을 numpy 배열로 반환

        Returns:
            np.ndarray: (N, 10) 배열 [EID, PID, N1-N8]
        """
        if self._element_data:
            data = np.zeros((len(self._element_data), 10))
            for i, elem in enumerate(self._element_data):
                nodes = elem.nodes + [0] * (8 - len(elem.nodes))
                data[i] = [elem.eid, elem.pid] + nodes
            return data

        n_total = sum(len(param) for param in self.parameters)
        data = np.zeros((n_total, 10))
        idx = 0
        for param in self.parameters:
            for entry in param:
                try:
                    data[idx] = [float(x) if x.strip() else 0 for x in entry[:10]]
                except ValueError:
                    pass
                idx += 1
        return data


class ElementSolid(DynaKeyword):
    """솔리드 엘리먼트 키워드 클래스 (기존 API 호환)"""

    def __init__(self):
        super().__init__("ELEMENT_SOLID")
        self._element_data: List[ElementData] = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'ElementSolid':
        """ParsedKFile에서 ElementSolid 생성"""
        instance = cls()
        instance._element_data = [e for e in parsed.elements if e.element_type == 'solid']
        instance.parameters = [[]]
        for elem in instance._element_data:
            nodes = elem.nodes + [0] * (8 - len(elem.nodes))
            instance.parameters[0].append([
                str(elem.eid), str(elem.pid),
                str(nodes[0]), str(nodes[1]), str(nodes[2]), str(nodes[3]),
                str(nodes[4]), str(nodes[5]), str(nodes[6]), str(nodes[7])
            ])
        return instance

    def parse(self, element_keywords):
        """기존 파싱 메서드"""
        for i in range(len(element_keywords)):
            parameter_list = []
            for j in range(len(element_keywords[i])):
                parameters = self.parse_whole(element_keywords[i][j],
                                               [8, 8, 8, 8, 8, 8, 8, 8, 8, 8])
                parameter_list.append(parameters)
            self.parameters.append(parameter_list)

    def EID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][0]

    def PID(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][1]

    def N1(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][2]

    def N2(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][3]

    def N3(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][4]

    def N4(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][5]

    def N5(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][6]

    def N6(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][7]

    def N7(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][8]

    def N8(self, ith: int, jth: int) -> str:
        return self.parameters[ith][jth][9]

    def getElementList(self) -> np.ndarray:
        """엘리먼트 목록을 numpy 배열로 반환"""
        if self._element_data:
            data = np.zeros((len(self._element_data), 10))
            for i, elem in enumerate(self._element_data):
                nodes = elem.nodes + [0] * (8 - len(elem.nodes))
                data[i] = [elem.eid, elem.pid] + nodes
            return data

        n_total = sum(len(param) for param in self.parameters)
        data = np.zeros((n_total, 10))
        idx = 0
        for param in self.parameters:
            for entry in param:
                try:
                    data[idx] = [float(x) if x.strip() else 0 for x in entry[:10]]
                except ValueError:
                    pass
                idx += 1
        return data


class ElementBeam(DynaKeyword):
    """빔 엘리먼트 키워드 클래스"""

    def __init__(self):
        super().__init__("ELEMENT_BEAM")
        self._element_data: List[ElementData] = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'ElementBeam':
        """ParsedKFile에서 ElementBeam 생성"""
        instance = cls()
        instance._element_data = [e for e in parsed.elements if e.element_type == 'beam']
        return instance

    def getElementList(self) -> np.ndarray:
        """빔 엘리먼트 목록을 numpy 배열로 반환"""
        if self._element_data:
            data = np.zeros((len(self._element_data), 10))
            for i, elem in enumerate(self._element_data):
                nodes = elem.nodes + [0] * (8 - len(elem.nodes))
                data[i] = [elem.eid, elem.pid] + nodes
            return data
        return np.zeros((0, 10))


class DynaSet(DynaKeyword):
    """Set 키워드 클래스"""

    def __init__(self):
        super().__init__("SET")
        self._set_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaSet':
        instance = cls()
        instance._set_data = parsed.sets
        return instance

    @property
    def sets(self):
        return self._set_data

    def get_set(self, sid: int):
        """ID로 Set 조회"""
        for s in self._set_data:
            if s.sid == sid:
                return s
        return None

    def get_node_sets(self):
        """NODE_LIST Set만 반환"""
        return [s for s in self._set_data if s.set_type.name == 'NODE_LIST']

    def get_part_sets(self):
        """PART_LIST Set만 반환"""
        return [s for s in self._set_data if s.set_type.name == 'PART_LIST']


class DynaSection(DynaKeyword):
    """Section 키워드 클래스"""

    def __init__(self):
        super().__init__("SECTION")
        self._section_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaSection':
        instance = cls()
        instance._section_data = parsed.sections
        return instance

    @property
    def sections(self):
        return self._section_data

    def get_section(self, secid: int):
        """ID로 Section 조회"""
        for s in self._section_data:
            if s.secid == secid:
                return s
        return None

    def get_shell_sections(self):
        """SHELL Section만 반환"""
        return [s for s in self._section_data if s.section_type.name == 'SHELL']

    def get_solid_sections(self):
        """SOLID Section만 반환"""
        return [s for s in self._section_data if s.section_type.name == 'SOLID']

    def get_beam_sections(self):
        """BEAM Section만 반환"""
        return [s for s in self._section_data if s.section_type.name == 'BEAM']


class DynaContact(DynaKeyword):
    """Contact 키워드 클래스"""

    def __init__(self):
        super().__init__("CONTACT")
        self._contact_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaContact':
        instance = cls()
        instance._contact_data = parsed.contacts
        return instance

    @property
    def contacts(self):
        return self._contact_data

    def get_contact(self, ssid: int):
        """SSID로 Contact 조회"""
        for c in self._contact_data:
            if c.ssid == ssid:
                return c
        return None


class DynaMaterial(DynaKeyword):
    """Material 키워드 클래스"""

    def __init__(self):
        super().__init__("MAT")
        self._material_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaMaterial':
        instance = cls()
        instance._material_data = parsed.materials
        return instance

    @property
    def materials(self):
        return self._material_data

    def get_material(self, mid: int):
        """ID로 Material 조회"""
        for m in self._material_data:
            if m.mid == mid:
                return m
        return None

    def get_materials_by_type(self, type_name: str):
        """타입별 Material 반환"""
        return [m for m in self._material_data if m.type_name == type_name]


class DynaInclude(DynaKeyword):
    """Include 키워드 클래스"""

    def __init__(self):
        super().__init__("INCLUDE")
        self._include_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaInclude':
        instance = cls()
        instance._include_data = parsed.includes
        return instance

    @property
    def includes(self):
        return self._include_data

    def get_filepaths(self) -> List[str]:
        """모든 include 파일 경로 반환"""
        return [inc.filepath for inc in self._include_data]


class DynaCurve(DynaKeyword):
    """DEFINE_CURVE 키워드 클래스"""

    def __init__(self):
        super().__init__("DEFINE_CURVE")
        self._curve_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaCurve':
        instance = cls()
        instance._curve_data = parsed.curves
        return instance

    @property
    def curves(self):
        return self._curve_data

    def get_curve(self, lcid: int):
        """LCID로 Curve 조회"""
        for c in self._curve_data:
            if c.lcid == lcid:
                return c
        return None


class DynaBoundarySPC(DynaKeyword):
    """BOUNDARY_SPC 키워드 클래스"""

    def __init__(self):
        super().__init__("BOUNDARY_SPC")
        self._spc_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaBoundarySPC':
        instance = cls()
        instance._spc_data = parsed.boundary_spcs
        return instance

    @property
    def spcs(self):
        return self._spc_data


class DynaBoundaryMotion(DynaKeyword):
    """BOUNDARY_PRESCRIBED_MOTION 키워드 클래스"""

    def __init__(self):
        super().__init__("BOUNDARY_PRESCRIBED_MOTION")
        self._motion_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaBoundaryMotion':
        instance = cls()
        instance._motion_data = parsed.boundary_motions
        return instance

    @property
    def motions(self):
        return self._motion_data


class DynaLoadNode(DynaKeyword):
    """LOAD_NODE 키워드 클래스"""

    def __init__(self):
        super().__init__("LOAD_NODE")
        self._load_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaLoadNode':
        instance = cls()
        instance._load_data = parsed.load_nodes
        return instance

    @property
    def loads(self):
        return self._load_data


class DynaLoadSegment(DynaKeyword):
    """LOAD_SEGMENT 키워드 클래스"""

    def __init__(self):
        super().__init__("LOAD_SEGMENT")
        self._load_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaLoadSegment':
        instance = cls()
        instance._load_data = parsed.load_segments
        return instance

    @property
    def loads(self):
        return self._load_data


class DynaLoadBody(DynaKeyword):
    """LOAD_BODY 키워드 클래스"""

    def __init__(self):
        super().__init__("LOAD_BODY")
        self._load_data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaLoadBody':
        instance = cls()
        instance._load_data = parsed.load_bodies
        return instance

    @property
    def loads(self):
        return self._load_data


class DynaControlTermination(DynaKeyword):
    """CONTROL_TERMINATION 키워드 클래스"""

    def __init__(self):
        super().__init__("CONTROL_TERMINATION")
        self._data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaControlTermination':
        instance = cls()
        instance._data = parsed.control_terminations
        return instance

    @property
    def terminations(self):
        return self._data


class DynaControlTimestep(DynaKeyword):
    """CONTROL_TIMESTEP 키워드 클래스"""

    def __init__(self):
        super().__init__("CONTROL_TIMESTEP")
        self._data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaControlTimestep':
        instance = cls()
        instance._data = parsed.control_timesteps
        return instance

    @property
    def timesteps(self):
        return self._data


class DynaDatabase(DynaKeyword):
    """DATABASE 키워드 클래스"""

    def __init__(self):
        super().__init__("DATABASE")
        self._binary_data = []
        self._ascii_data = []
        self._history_nodes = []
        self._history_elements = []
        self._cross_sections = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaDatabase':
        instance = cls()
        instance._binary_data = parsed.database_binaries
        instance._ascii_data = parsed.database_asciis
        instance._history_nodes = parsed.database_history_nodes
        instance._history_elements = parsed.database_history_elements
        instance._cross_sections = parsed.database_cross_sections
        return instance

    @property
    def binaries(self):
        return self._binary_data

    @property
    def asciis(self):
        return self._ascii_data

    @property
    def history_nodes(self):
        return self._history_nodes

    @property
    def history_elements(self):
        return self._history_elements

    @property
    def cross_sections(self):
        return self._cross_sections


class DynaInitialVelocity(DynaKeyword):
    """INITIAL_VELOCITY 키워드 클래스"""

    def __init__(self):
        super().__init__("INITIAL_VELOCITY")
        self._data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaInitialVelocity':
        instance = cls()
        instance._data = parsed.initial_velocities
        return instance

    @property
    def velocities(self):
        return self._data


class DynaConstrainedNodalRigidBody(DynaKeyword):
    """CONSTRAINED_NODAL_RIGID_BODY 키워드 클래스"""

    def __init__(self):
        super().__init__("CONSTRAINED_NODAL_RIGID_BODY")
        self._data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaConstrainedNodalRigidBody':
        instance = cls()
        instance._data = parsed.constrained_nodal_rigid_bodies
        return instance

    @property
    def rigid_bodies(self):
        return self._data


class DynaConstrainedJoint(DynaKeyword):
    """CONSTRAINED_JOINT 키워드 클래스"""

    def __init__(self):
        super().__init__("CONSTRAINED_JOINT")
        self._data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaConstrainedJoint':
        instance = cls()
        instance._data = parsed.constrained_joints
        return instance

    @property
    def joints(self):
        return self._data


class DynaConstrainedSpotweld(DynaKeyword):
    """CONSTRAINED_SPOTWELD 키워드 클래스"""

    def __init__(self):
        super().__init__("CONSTRAINED_SPOTWELD")
        self._data = []

    @classmethod
    def from_parsed(cls, parsed: 'ParsedKFile') -> 'DynaConstrainedSpotweld':
        instance = cls()
        instance._data = parsed.constrained_spotwelds
        return instance

    @property
    def spotwelds(self):
        return self._data


class KFileReader:
    """K파일 고속 리더

    기존 키워드 클래스들과 호환되는 인터페이스 제공

    Example:
        reader = KFileReader("model.k")

        # 방법 1: numpy 배열로 직접 접근
        node_array = reader.node_array()     # (N, 6) numpy array
        part_array = reader.part_array()     # (N, 8) numpy array
        element_array = reader.element_array()  # (N, 10) numpy array

        # 방법 2: 기존 키워드 객체로 접근
        nodes = reader.get_nodes()    # DynaNode 객체
        parts = reader.get_parts()    # Part 객체
        shells = reader.get_shells()  # ElementShell 객체
        solids = reader.get_solids()  # ElementSolid 객체

        # 통계
        stats = reader.stats
        print(f"파싱 시간: {stats['parse_time_ms']}ms")
    """

    def __init__(self, filepath: str, parse_nodes: bool = True,
                 parse_parts: bool = True, parse_elements: bool = True,
                 parse_sets: bool = True, parse_sections: bool = True,
                 parse_contacts: bool = True, parse_materials: bool = True,
                 parse_includes: bool = True, parse_curves: bool = True,
                 parse_boundaries: bool = True, parse_loads: bool = True,
                 parse_controls: bool = True, parse_databases: bool = True,
                 parse_initials: bool = True, parse_constraineds: bool = True):
        """K파일 로드

        Args:
            filepath: K파일 경로
            parse_nodes: 노드 파싱 여부
            parse_parts: 파트 파싱 여부
            parse_elements: 엘리먼트 파싱 여부
            parse_sets: 셋 파싱 여부
            parse_sections: 섹션 파싱 여부
            parse_contacts: 접촉 파싱 여부
            parse_materials: 재료 파싱 여부
            parse_includes: 인클루드 파싱 여부
            parse_curves: 곡선 파싱 여부
            parse_boundaries: 경계조건 파싱 여부
            parse_loads: 하중 파싱 여부
            parse_controls: 컨트롤 파싱 여부
            parse_databases: 데이터베이스 파싱 여부
            parse_initials: 초기조건 파싱 여부
            parse_constraineds: 구속조건 파싱 여부
        """
        self.filepath = filepath
        self._parsed: Optional[ParsedKFile] = None
        # Cached wrapper objects
        self._nodes: Optional[DynaNode] = None
        self._parts: Optional[Part] = None
        self._shells: Optional[ElementShell] = None
        self._solids: Optional[ElementSolid] = None
        self._beams: Optional[ElementBeam] = None
        self._sets: Optional[DynaSet] = None
        self._sections: Optional[DynaSection] = None
        self._contacts: Optional[DynaContact] = None
        self._materials: Optional[DynaMaterial] = None
        self._includes: Optional[DynaInclude] = None
        self._curves: Optional[DynaCurve] = None
        self._boundary_spcs: Optional[DynaBoundarySPC] = None
        self._boundary_motions: Optional[DynaBoundaryMotion] = None
        self._load_nodes: Optional[DynaLoadNode] = None
        self._load_segments: Optional[DynaLoadSegment] = None
        self._load_bodies: Optional[DynaLoadBody] = None
        self._control_terminations: Optional[DynaControlTermination] = None
        self._control_timesteps: Optional[DynaControlTimestep] = None
        self._databases: Optional[DynaDatabase] = None
        self._initial_velocities: Optional[DynaInitialVelocity] = None
        self._constrained_rigid_bodies: Optional[DynaConstrainedNodalRigidBody] = None
        self._constrained_joints: Optional[DynaConstrainedJoint] = None
        self._constrained_spotwelds: Optional[DynaConstrainedSpotweld] = None

        if _FAST_PARSER_AVAILABLE:
            parser = KFileParser(
                parse_nodes=parse_nodes,
                parse_parts=parse_parts,
                parse_elements=parse_elements,
                parse_sets=parse_sets,
                parse_sections=parse_sections,
                parse_contacts=parse_contacts,
                parse_materials=parse_materials,
                parse_includes=parse_includes,
                parse_curves=parse_curves,
                parse_boundaries=parse_boundaries,
                parse_loads=parse_loads,
                parse_controls=parse_controls,
                parse_databases=parse_databases,
                parse_initials=parse_initials,
                parse_constraineds=parse_constraineds
            )
            self._parsed = parser.parse(filepath)
        else:
            raise ImportError(
                "kfile_parser 모듈을 찾을 수 없습니다.\n"
                "빌드 방법: cd kfile_parser && python setup.py build_ext --inplace"
            )

    @property
    def stats(self) -> Dict[str, Any]:
        """파싱 통계"""
        if self._parsed:
            return self._parsed.stats
        return {}

    @property
    def using_fast_parser(self) -> bool:
        """고속 파서 사용 여부"""
        return _FAST_PARSER_AVAILABLE

    def node_array(self) -> np.ndarray:
        """노드 numpy 배열 반환 (N, 6) [NID, X, Y, Z, TC, RC]"""
        return self.get_nodes().getNodeList()

    def part_array(self) -> np.ndarray:
        """파트 numpy 배열 반환 (N, 8) [PID, SECID, MID, ...]"""
        return self.get_parts().getPartList()

    def element_array(self, element_type: str = 'all') -> np.ndarray:
        """엘리먼트 numpy 배열 반환 (N, 10) [EID, PID, N1-N8]

        Args:
            element_type: 'shell', 'solid', 또는 'all'
        """
        if element_type == 'shell':
            return self.get_shells().getElementList()
        elif element_type == 'solid':
            return self.get_solids().getElementList()
        else:
            shell_arr = self.get_shells().getElementList()
            solid_arr = self.get_solids().getElementList()
            if shell_arr.size > 0 and solid_arr.size > 0:
                return np.vstack([shell_arr, solid_arr])
            elif shell_arr.size > 0:
                return shell_arr
            return solid_arr

    def get_nodes(self) -> DynaNode:
        """DynaNode 객체 반환 (캐시됨)"""
        if self._nodes is None:
            self._nodes = DynaNode.from_parsed(self._parsed)
        return self._nodes

    def get_parts(self) -> Part:
        """Part 객체 반환 (캐시됨)"""
        if self._parts is None:
            self._parts = Part.from_parsed(self._parsed)
        return self._parts

    def get_shells(self) -> ElementShell:
        """ElementShell 객체 반환 (캐시됨)"""
        if self._shells is None:
            self._shells = ElementShell.from_parsed(self._parsed)
        return self._shells

    def get_solids(self) -> ElementSolid:
        """ElementSolid 객체 반환 (캐시됨)"""
        if self._solids is None:
            self._solids = ElementSolid.from_parsed(self._parsed)
        return self._solids

    def get_beams(self) -> ElementBeam:
        """ElementBeam 객체 반환 (캐시됨)"""
        if self._beams is None:
            self._beams = ElementBeam.from_parsed(self._parsed)
        return self._beams

    def get_sets(self) -> DynaSet:
        """DynaSet 객체 반환 (캐시됨)"""
        if self._sets is None:
            self._sets = DynaSet.from_parsed(self._parsed)
        return self._sets

    def get_sections(self) -> DynaSection:
        """DynaSection 객체 반환 (캐시됨)"""
        if self._sections is None:
            self._sections = DynaSection.from_parsed(self._parsed)
        return self._sections

    def get_contacts(self) -> DynaContact:
        """DynaContact 객체 반환 (캐시됨)"""
        if self._contacts is None:
            self._contacts = DynaContact.from_parsed(self._parsed)
        return self._contacts

    def get_materials(self) -> DynaMaterial:
        """DynaMaterial 객체 반환 (캐시됨)"""
        if self._materials is None:
            self._materials = DynaMaterial.from_parsed(self._parsed)
        return self._materials

    def get_includes(self) -> DynaInclude:
        """DynaInclude 객체 반환 (캐시됨)"""
        if self._includes is None:
            self._includes = DynaInclude.from_parsed(self._parsed)
        return self._includes

    def get_curves(self) -> DynaCurve:
        """DynaCurve 객체 반환 (캐시됨)"""
        if self._curves is None:
            self._curves = DynaCurve.from_parsed(self._parsed)
        return self._curves

    def get_boundary_spcs(self) -> DynaBoundarySPC:
        """DynaBoundarySPC 객체 반환 (캐시됨)"""
        if self._boundary_spcs is None:
            self._boundary_spcs = DynaBoundarySPC.from_parsed(self._parsed)
        return self._boundary_spcs

    def get_boundary_motions(self) -> DynaBoundaryMotion:
        """DynaBoundaryMotion 객체 반환 (캐시됨)"""
        if self._boundary_motions is None:
            self._boundary_motions = DynaBoundaryMotion.from_parsed(self._parsed)
        return self._boundary_motions

    def get_load_nodes(self) -> DynaLoadNode:
        """DynaLoadNode 객체 반환 (캐시됨)"""
        if self._load_nodes is None:
            self._load_nodes = DynaLoadNode.from_parsed(self._parsed)
        return self._load_nodes

    def get_load_segments(self) -> DynaLoadSegment:
        """DynaLoadSegment 객체 반환 (캐시됨)"""
        if self._load_segments is None:
            self._load_segments = DynaLoadSegment.from_parsed(self._parsed)
        return self._load_segments

    def get_load_bodies(self) -> DynaLoadBody:
        """DynaLoadBody 객체 반환 (캐시됨)"""
        if self._load_bodies is None:
            self._load_bodies = DynaLoadBody.from_parsed(self._parsed)
        return self._load_bodies

    def get_control_terminations(self) -> DynaControlTermination:
        """DynaControlTermination 객체 반환 (캐시됨)"""
        if self._control_terminations is None:
            self._control_terminations = DynaControlTermination.from_parsed(self._parsed)
        return self._control_terminations

    def get_control_timesteps(self) -> DynaControlTimestep:
        """DynaControlTimestep 객체 반환 (캐시됨)"""
        if self._control_timesteps is None:
            self._control_timesteps = DynaControlTimestep.from_parsed(self._parsed)
        return self._control_timesteps

    def get_databases(self) -> DynaDatabase:
        """DynaDatabase 객체 반환 (캐시됨)"""
        if self._databases is None:
            self._databases = DynaDatabase.from_parsed(self._parsed)
        return self._databases

    def get_initial_velocities(self) -> DynaInitialVelocity:
        """DynaInitialVelocity 객체 반환 (캐시됨)"""
        if self._initial_velocities is None:
            self._initial_velocities = DynaInitialVelocity.from_parsed(self._parsed)
        return self._initial_velocities

    def get_constrained_rigid_bodies(self) -> DynaConstrainedNodalRigidBody:
        """DynaConstrainedNodalRigidBody 객체 반환 (캐시됨)"""
        if self._constrained_rigid_bodies is None:
            self._constrained_rigid_bodies = DynaConstrainedNodalRigidBody.from_parsed(self._parsed)
        return self._constrained_rigid_bodies

    def get_constrained_joints(self) -> DynaConstrainedJoint:
        """DynaConstrainedJoint 객체 반환 (캐시됨)"""
        if self._constrained_joints is None:
            self._constrained_joints = DynaConstrainedJoint.from_parsed(self._parsed)
        return self._constrained_joints

    def get_constrained_spotwelds(self) -> DynaConstrainedSpotweld:
        """DynaConstrainedSpotweld 객체 반환 (캐시됨)"""
        if self._constrained_spotwelds is None:
            self._constrained_spotwelds = DynaConstrainedSpotweld.from_parsed(self._parsed)
        return self._constrained_spotwelds

    def get_node(self, nid: int) -> Optional[Any]:
        """ID로 노드 조회"""
        return self._parsed.get_node(nid)

    def get_part(self, pid: int) -> Optional[Any]:
        """ID로 파트 조회"""
        return self._parsed.get_part(pid)

    def get_element(self, eid: int) -> Optional[Any]:
        """ID로 엘리먼트 조회"""
        return self._parsed.get_element(eid)


# 편의 함수
def read_kfile(filepath: str, parse_nodes: bool = True,
               parse_parts: bool = True, parse_elements: bool = True) -> KFileReader:
    """K파일 읽기 편의 함수

    Example:
        reader = read_kfile("model.k")
        nodes = reader.node_array()
    """
    return KFileReader(filepath, parse_nodes, parse_parts, parse_elements)


__all__ = [
    # 키워드 클래스
    'DynaKeyword',
    'DynaNode',
    'Part',
    'ElementShell',
    'ElementSolid',
    'ElementBeam',
    'DynaSet',
    'DynaSection',
    'DynaContact',
    'DynaMaterial',
    'DynaInclude',
    'DynaCurve',
    'DynaBoundarySPC',
    'DynaBoundaryMotion',
    'DynaLoadNode',
    'DynaLoadSegment',
    'DynaLoadBody',
    'DynaControlTermination',
    'DynaControlTimestep',
    'DynaDatabase',
    'DynaInitialVelocity',
    'DynaConstrainedNodalRigidBody',
    'DynaConstrainedJoint',
    'DynaConstrainedSpotweld',

    # 리더
    'KFileReader',
    'read_kfile',

    # 유틸리티
    'is_fast_parser_available',
]
