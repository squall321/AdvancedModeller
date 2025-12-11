"""Exporter 테스트

KFileExporter K-file 내보내기 기능 테스트
"""
import pytest
import tempfile
import os
from dataclasses import dataclass, field
from typing import List, Optional

from gui.modules.keyword_manager.core.exporter import (
    KFileExporter, ExportOptions
)


# 테스트용 더미 모델 클래스
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
    keyword_type: str = "MAT_ELASTIC"
    name: str = ""
    ro: float = 0.0
    e: float = 0.0
    pr: float = 0.0


@dataclass
class DummySection:
    secid: int
    keyword_type: str = "SECTION_SHELL"
    elform: int = 0
    shrf: float = 0.0
    nip: int = 0
    propt: float = 0.0
    qr_irid: int = 0
    icomp: int = 0
    setyp: int = 0
    t1: float = 0.0
    t2: float = 0.0
    t3: float = 0.0
    t4: float = 0.0
    nloc: float = 0.0
    marea: float = 0.0


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
        self.filename: str = "test.k"  # 실제 API에서 사용하는 속성
        self.is_loaded: bool = True


class TestExportOptions:
    """ExportOptions 테스트"""

    def test_default_options(self):
        """기본 옵션 테스트"""
        opts = ExportOptions()

        assert opts.include_comments is True
        assert opts.default_field_width == 10
        assert opts.node_coord_width == 16
        assert opts.float_format == 'auto'
        assert opts.float_precision == 6
        assert opts.modified_only is False
        assert opts.skip_empty is True

    def test_custom_options(self):
        """커스텀 옵션 테스트"""
        opts = ExportOptions(
            include_comments=False,
            default_field_width=8,
            float_format='scientific'
        )

        assert opts.include_comments is False
        assert opts.default_field_width == 8
        assert opts.float_format == 'scientific'


class TestKFileExporter:
    """KFileExporter 테스트"""

    def setup_method(self):
        """각 테스트 전 모델 초기화"""
        self.model = DummyParsedModel()

    def test_export_empty_model(self):
        """빈 모델 내보내기 테스트"""
        exporter = KFileExporter(self.model)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                content = f.read()

            assert '*KEYWORD' in content
            assert '*END' in content
        finally:
            os.unlink(filepath)

    def test_export_nodes(self):
        """노드 내보내기 테스트"""
        self.model.nodes = [
            DummyNode(nid=1, x=0.0, y=0.0, z=0.0),
            DummyNode(nid=2, x=1.0, y=0.0, z=0.0),
            DummyNode(nid=3, x=0.0, y=1.0, z=0.0),
        ]

        exporter = KFileExporter(self.model)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                content = f.read()

            assert '*NODE' in content
            # 노드 ID가 포함되어 있는지 확인
            lines = content.split('\n')
            node_section = False
            node_count = 0
            for line in lines:
                if '*NODE' in line:
                    node_section = True
                    continue
                if node_section and line.startswith('*'):
                    break
                if node_section and line.strip() and not line.startswith('$'):
                    node_count += 1

            assert node_count == 3
        finally:
            os.unlink(filepath)

    def test_export_shells(self):
        """쉘 요소 내보내기 테스트"""
        self.model.shells = [
            DummyShell(eid=1, pid=1, nodes=[1, 2, 3, 4]),
            DummyShell(eid=2, pid=1, nodes=[2, 3, 5, 6]),
        ]

        exporter = KFileExporter(self.model)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                content = f.read()

            assert '*ELEMENT_SHELL' in content
        finally:
            os.unlink(filepath)

    def test_export_parts(self):
        """파트 내보내기 테스트"""
        self.model.parts = [
            DummyPart(pid=1, name="Part1", secid=1, mid=1),
            DummyPart(pid=2, name="Part2", secid=2, mid=2),
        ]

        exporter = KFileExporter(self.model)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                content = f.read()

            assert '*PART' in content
            assert 'Part1' in content
            assert 'Part2' in content
        finally:
            os.unlink(filepath)

    def test_export_with_comments(self):
        """주석 포함 내보내기 테스트"""
        opts = ExportOptions(include_comments=True)
        exporter = KFileExporter(self.model, opts)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                content = f.read()

            assert 'LaminateModeller' in content or '$#' in content
        finally:
            os.unlink(filepath)

    def test_export_without_comments(self):
        """주석 제외 내보내기 테스트"""
        opts = ExportOptions(include_comments=False)
        exporter = KFileExporter(self.model, opts)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                lines = f.readlines()

            # 첫 줄이 *KEYWORD여야 함
            first_non_empty = None
            for line in lines:
                if line.strip():
                    first_non_empty = line.strip()
                    break

            assert first_non_empty == '*KEYWORD'
        finally:
            os.unlink(filepath)

    def test_export_materials(self):
        """재료 내보내기 테스트"""
        self.model.materials = [
            DummyMaterial(mid=1, keyword_type="MAT_ELASTIC", ro=7800.0, e=2.1e11, pr=0.3),
        ]

        exporter = KFileExporter(self.model)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                content = f.read()

            assert '*MAT' in content
        finally:
            os.unlink(filepath)

    def test_export_sections(self):
        """섹션 내보내기 테스트"""
        self.model.sections = [
            DummySection(secid=1, keyword_type="SECTION_SHELL", t1=1.0, t2=1.0, t3=1.0, t4=1.0),
        ]

        exporter = KFileExporter(self.model)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                content = f.read()

            assert '*SECTION' in content
        finally:
            os.unlink(filepath)


class TestExportIntegration:
    """통합 내보내기 테스트"""

    def test_full_model_export(self):
        """전체 모델 내보내기 테스트"""
        model = DummyParsedModel()

        # 노드 추가
        model.nodes = [
            DummyNode(nid=i, x=float(i), y=0.0, z=0.0)
            for i in range(1, 5)
        ]

        # 요소 추가
        model.shells = [
            DummyShell(eid=1, pid=1, nodes=[1, 2, 3, 4]),
        ]

        # 파트 추가
        model.parts = [
            DummyPart(pid=1, name="TestPart", secid=1, mid=1),
        ]

        # 섹션 추가
        model.sections = [
            DummySection(secid=1, t1=1.0),
        ]

        # 재료 추가
        model.materials = [
            DummyMaterial(mid=1, ro=7800.0, e=2.1e11, pr=0.3),
        ]

        exporter = KFileExporter(model)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            result = exporter.export(filepath)
            assert result is True

            with open(filepath, 'r') as f:
                content = f.read()

            # 모든 섹션이 포함되어 있는지 확인
            assert '*NODE' in content
            assert '*ELEMENT_SHELL' in content
            assert '*PART' in content
            assert '*SECTION' in content
            assert '*MAT' in content
            assert '*END' in content

        finally:
            os.unlink(filepath)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
