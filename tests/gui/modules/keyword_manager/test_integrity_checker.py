"""Integrity Checker 테스트

참조 무결성 검사 기능 테스트
"""
import pytest
from dataclasses import dataclass
from typing import List

from gui.modules.keyword_manager.core.integrity_checker import (
    IntegrityChecker, IntegrityReport, IntegrityIssue, SeverityLevel
)


# 테스트용 더미 데이터 클래스
@dataclass
class DummyNode:
    nid: int
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    tc: int = 0
    rc: int = 0


@dataclass
class DummyShell:
    eid: int
    pid: int = 0
    nodes: List[int] = None

    def __post_init__(self):
        if self.nodes is None:
            self.nodes = [0, 0, 0, 0]


@dataclass
class DummySolid:
    eid: int
    pid: int = 0
    nodes: List[int] = None

    def __post_init__(self):
        if self.nodes is None:
            self.nodes = [0] * 8


@dataclass
class DummyPart:
    pid: int
    name: str = ""
    secid: int = 0
    mid: int = 0
    eosid: int = 0
    hgid: int = 0
    grav: int = 0
    adpopt: int = 0
    tmid: int = 0


@dataclass
class DummyMaterial:
    mid: int
    material_type: str = "MAT_ELASTIC"
    keyword_type: str = "MAT_ELASTIC"
    title: str = ""
    ro: float = 0.0
    e: float = 0.0
    pr: float = 0.0
    da: float = 0.0
    db: float = 0.0
    k: float = 0.0


@dataclass
class DummySection:
    secid: int
    keyword_type: str = "SECTION_SHELL"
    title: str = ""
    elform: int = 2
    shrf: float = 1.0
    nip: int = 2
    propt: float = 0.0
    qr_irid: int = 0
    icomp: int = 0
    setyp: int = 1
    t1: float = 1.0
    t2: float = 1.0
    t3: float = 1.0
    t4: float = 1.0
    nloc: float = 0.0


class DummyParsedModel:
    """테스트용 ParsedModelData 대체"""

    def __init__(self):
        self.nodes: List[DummyNode] = []
        self.shells: List[DummyShell] = []
        self.solids: List[DummySolid] = []
        self.beams: List = []
        self.parts: List[DummyPart] = []
        self.materials: List[DummyMaterial] = []
        self.sections: List[DummySection] = []
        self.contacts: List = []
        self.sets: List = []
        self.controls: dict = {}
        self.databases: dict = {}
        self.boundaries: dict = {}
        self.loads: dict = {}
        self.initials: dict = {}
        self.constraineds: dict = {}
        self.title: str = "Test Model"
        self.filepath: str = "test.k"
        self.filename: str = "test.k"
        self.is_loaded: bool = True


class TestIntegrityReport:
    """IntegrityReport 테스트"""

    def test_empty_report(self):
        """빈 보고서 테스트"""
        report = IntegrityReport()

        assert report.total_issues == 0
        assert report.has_errors is False
        assert report.has_warnings is False
        assert len(report.get_all_issues()) == 0

    def test_add_error(self):
        """에러 추가 테스트"""
        report = IntegrityReport()
        issue = IntegrityIssue(
            severity=SeverityLevel.ERROR,
            category='nodes',
            item_id=1,
            field_name='nid',
            message="Duplicate ID"
        )

        report.add_issue(issue)

        assert report.total_issues == 1
        assert report.has_errors is True
        assert len(report.errors) == 1

    def test_add_warning(self):
        """경고 추가 테스트"""
        report = IntegrityReport()
        issue = IntegrityIssue(
            severity=SeverityLevel.WARNING,
            category='nodes',
            item_id=1,
            field_name='x',
            message="Large coordinate"
        )

        report.add_issue(issue)

        assert report.total_issues == 1
        assert report.has_warnings is True
        assert len(report.warnings) == 1

    def test_mixed_issues(self):
        """다양한 심각도 테스트"""
        report = IntegrityReport()

        report.add_issue(IntegrityIssue(
            severity=SeverityLevel.ERROR,
            category='nodes',
            item_id=1,
            field_name='nid',
            message="Error 1"
        ))
        report.add_issue(IntegrityIssue(
            severity=SeverityLevel.WARNING,
            category='nodes',
            item_id=2,
            field_name='x',
            message="Warning 1"
        ))
        report.add_issue(IntegrityIssue(
            severity=SeverityLevel.INFO,
            category='nodes',
            item_id=3,
            field_name='y',
            message="Info 1"
        ))

        assert report.total_issues == 3
        assert len(report.errors) == 1
        assert len(report.warnings) == 1
        assert len(report.infos) == 1

        all_issues = report.get_all_issues()
        assert len(all_issues) == 3
        assert all_issues[0].severity == SeverityLevel.ERROR


class TestIntegrityCheckerBasic:
    """IntegrityChecker 기본 테스트"""

    def test_valid_model(self):
        """유효한 모델 테스트"""
        model = DummyParsedModel()

        # 유효한 데이터 설정
        model.nodes = [
            DummyNode(nid=1, x=0.0, y=0.0, z=0.0),
            DummyNode(nid=2, x=1.0, y=0.0, z=0.0),
            DummyNode(nid=3, x=1.0, y=1.0, z=0.0),
            DummyNode(nid=4, x=0.0, y=1.0, z=0.0),
        ]
        model.materials = [
            DummyMaterial(mid=1, ro=7850.0, e=2.1e11, pr=0.3),
        ]
        model.sections = [
            DummySection(secid=1, t1=1.0),
        ]
        model.parts = [
            DummyPart(pid=1, secid=1, mid=1),
        ]
        model.shells = [
            DummyShell(eid=1, pid=1, nodes=[1, 2, 3, 4]),
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.total_issues == 0
        assert report.has_errors is False

    def test_empty_model(self):
        """빈 모델 테스트"""
        model = DummyParsedModel()

        checker = IntegrityChecker(model)
        report = checker.check_all()

        # 빈 모델은 문제 없음
        assert report.total_issues == 0


class TestDuplicateIDCheck:
    """중복 ID 검사 테스트"""

    def test_duplicate_node_ids(self):
        """중복 노드 ID 테스트"""
        model = DummyParsedModel()
        model.nodes = [
            DummyNode(nid=1),
            DummyNode(nid=2),
            DummyNode(nid=1),  # 중복
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.has_errors is True
        assert len(report.errors) == 1
        assert 'Duplicate' in report.errors[0].message

    def test_duplicate_element_ids(self):
        """중복 요소 ID 테스트"""
        model = DummyParsedModel()
        model.shells = [
            DummyShell(eid=1, pid=0),
            DummyShell(eid=2, pid=0),
            DummyShell(eid=1, pid=0),  # 중복
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.has_errors is True

    def test_no_duplicate_ids(self):
        """중복 없음 테스트"""
        model = DummyParsedModel()
        model.nodes = [
            DummyNode(nid=1),
            DummyNode(nid=2),
            DummyNode(nid=3),
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.total_issues == 0


class TestReferenceCheck:
    """참조 검사 테스트"""

    def test_element_missing_node(self):
        """요소가 존재하지 않는 노드 참조 테스트"""
        model = DummyParsedModel()
        model.nodes = [
            DummyNode(nid=1),
            DummyNode(nid=2),
        ]
        model.shells = [
            DummyShell(eid=1, pid=0, nodes=[1, 2, 999, 0]),  # 999는 존재하지 않음
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.has_errors is True
        assert any('non-existent node' in err.message.lower() for err in report.errors)

    def test_element_missing_part(self):
        """요소가 존재하지 않는 파트 참조 테스트"""
        model = DummyParsedModel()
        model.nodes = [DummyNode(nid=1), DummyNode(nid=2), DummyNode(nid=3), DummyNode(nid=4)]
        model.parts = [DummyPart(pid=1)]
        model.shells = [
            DummyShell(eid=1, pid=999, nodes=[1, 2, 3, 4]),  # pid=999는 존재하지 않음
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.has_errors is True
        assert any('non-existent part' in err.message.lower() for err in report.errors)

    def test_part_missing_section(self):
        """파트가 존재하지 않는 섹션 참조 테스트"""
        model = DummyParsedModel()
        model.sections = [DummySection(secid=1)]
        model.parts = [
            DummyPart(pid=1, secid=999, mid=0),  # secid=999는 존재하지 않음
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.has_errors is True
        assert any('non-existent section' in err.message.lower() for err in report.errors)

    def test_part_missing_material(self):
        """파트가 존재하지 않는 재료 참조 테스트"""
        model = DummyParsedModel()
        model.materials = [DummyMaterial(mid=1)]
        model.parts = [
            DummyPart(pid=1, secid=0, mid=999),  # mid=999는 존재하지 않음
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.has_errors is True
        assert any('non-existent material' in err.message.lower() for err in report.errors)

    def test_zero_references_allowed(self):
        """0 참조는 허용 테스트"""
        model = DummyParsedModel()
        model.parts = [
            DummyPart(pid=1, secid=0, mid=0),  # 0은 "정의되지 않음"을 의미
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        # 0 참조는 에러가 아님
        assert report.has_errors is False


class TestNodeCoordinateCheck:
    """노드 좌표 검사 테스트"""

    def test_large_coordinates(self):
        """매우 큰 좌표값 테스트"""
        model = DummyParsedModel()
        model.nodes = [
            DummyNode(nid=1, x=1e15, y=0.0, z=0.0),  # 매우 큰 값
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.has_warnings is True
        assert any('large coordinates' in warn.message.lower() for warn in report.warnings)

    def test_normal_coordinates(self):
        """정상 좌표값 테스트"""
        model = DummyParsedModel()
        model.nodes = [
            DummyNode(nid=1, x=100.0, y=200.0, z=300.0),
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        # 정상 좌표는 경고 없음
        assert report.has_warnings is False


class TestCategoryCheck:
    """카테고리별 검사 테스트"""

    def test_check_nodes_only(self):
        """노드만 검사 테스트"""
        model = DummyParsedModel()
        model.nodes = [
            DummyNode(nid=1),
            DummyNode(nid=1),  # 중복
        ]
        model.shells = [
            DummyShell(eid=1, pid=999),  # 잘못된 참조 (검사하지 않음)
        ]

        checker = IntegrityChecker(model)
        report = checker.check_category('nodes')

        # 노드 중복만 검출
        assert report.has_errors is True
        assert len(report.errors) == 1
        assert report.errors[0].category == 'nodes'

    def test_check_parts_only(self):
        """파트만 검사 테스트"""
        model = DummyParsedModel()
        model.parts = [
            DummyPart(pid=1, secid=999),  # 잘못된 참조
        ]

        checker = IntegrityChecker(model)
        report = checker.check_category('parts')

        assert report.has_errors is True
        assert report.errors[0].category == 'parts'


class TestItemCheck:
    """개별 항목 검사 테스트"""

    def test_check_single_node(self):
        """단일 노드 검사 테스트"""
        model = DummyParsedModel()
        node = DummyNode(nid=1, x=0.0, y=0.0, z=0.0)
        model.nodes = [node]

        checker = IntegrityChecker(model)
        report = checker.check_item('nodes', node)

        assert report.total_issues == 0

    def test_check_single_element(self):
        """단일 요소 검사 테스트"""
        model = DummyParsedModel()
        model.nodes = [DummyNode(nid=1), DummyNode(nid=2)]
        model.parts = [DummyPart(pid=1)]
        shell = DummyShell(eid=1, pid=1, nodes=[1, 2, 0, 0])
        model.shells = [shell]

        checker = IntegrityChecker(model)
        report = checker.check_item('shell', shell)

        assert report.total_issues == 0

    def test_check_invalid_element(self):
        """잘못된 요소 검사 테스트"""
        model = DummyParsedModel()
        model.nodes = [DummyNode(nid=1)]
        shell = DummyShell(eid=1, pid=999, nodes=[999, 0, 0, 0])  # 잘못된 참조
        model.shells = [shell]

        checker = IntegrityChecker(model)
        report = checker.check_item('shell', shell)

        assert report.has_errors is True


class TestComplexScenarios:
    """복잡한 시나리오 테스트"""

    def test_multiple_errors(self):
        """여러 오류 동시 발생 테스트"""
        model = DummyParsedModel()

        # 중복 노드
        model.nodes = [
            DummyNode(nid=1),
            DummyNode(nid=1),
        ]

        # 잘못된 참조
        model.shells = [
            DummyShell(eid=1, pid=999, nodes=[999, 0, 0, 0]),
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        # 최소 2개 이상의 에러
        assert len(report.errors) >= 2

    def test_cascading_references(self):
        """연쇄 참조 테스트"""
        model = DummyParsedModel()

        # 정상 참조 체인
        model.nodes = [DummyNode(nid=i) for i in range(1, 5)]
        model.materials = [DummyMaterial(mid=1)]
        model.sections = [DummySection(secid=1)]
        model.parts = [DummyPart(pid=1, secid=1, mid=1)]
        model.shells = [DummyShell(eid=1, pid=1, nodes=[1, 2, 3, 4])]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.total_issues == 0

    def test_mixed_valid_invalid(self):
        """유효한 것과 무효한 것 혼재 테스트"""
        model = DummyParsedModel()

        model.nodes = [DummyNode(nid=i) for i in range(1, 5)]
        model.parts = [DummyPart(pid=1)]

        model.shells = [
            DummyShell(eid=1, pid=1, nodes=[1, 2, 3, 4]),  # 정상
            DummyShell(eid=2, pid=999, nodes=[1, 2, 3, 4]),  # 잘못된 PID
            DummyShell(eid=3, pid=1, nodes=[1, 2, 999, 4]),  # 잘못된 노드
        ]

        checker = IntegrityChecker(model)
        report = checker.check_all()

        assert report.has_errors is True
        assert len(report.errors) == 2  # PID 오류 1개 + 노드 오류 1개


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
