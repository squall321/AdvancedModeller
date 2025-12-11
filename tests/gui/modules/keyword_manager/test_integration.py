"""Integration tests for Keyword Manager

전체 모듈의 통합 동작을 테스트합니다.
"""
import pytest
import tempfile
import os
from dataclasses import dataclass
from typing import List

from gui.modules.keyword_manager.core.keyword_model import KeywordModel
from gui.modules.keyword_manager.core.clipboard import get_clipboard
from gui.modules.keyword_manager.core.exporter import ExportOptions


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
        self.solids: List = []
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
        self.title: str = "Integration Test Model"
        self.filepath: str = "test_integration.k"
        self.filename: str = "test_integration.k"
        self.is_loaded: bool = True


class TestEndToEndWorkflow:
    """전체 워크플로우 통합 테스트"""

    def setup_method(self):
        """각 테스트 전 초기화"""
        self.model = KeywordModel()
        self.parsed_model = DummyParsedModel()

        # 초기 데이터 설정
        self.parsed_model.nodes = [
            DummyNode(nid=1, x=0.0, y=0.0, z=0.0),
            DummyNode(nid=2, x=1.0, y=0.0, z=0.0),
            DummyNode(nid=3, x=1.0, y=1.0, z=0.0),
        ]
        self.parsed_model.shells = [
            DummyShell(eid=1, pid=1, nodes=[1, 2, 3, 1]),
        ]
        self.parsed_model.materials = [
            DummyMaterial(mid=1, ro=7850.0, e=2.1e11, pr=0.3),
        ]
        self.parsed_model.sections = [
            DummySection(secid=1, t1=1.0),
        ]
        self.parsed_model.parts = [
            DummyPart(pid=1, name="Part1", secid=1, mid=1),
        ]

        self.model.set_model(self.parsed_model)

    def test_modify_undo_redo_workflow(self):
        """수정 → Undo → Redo 전체 워크플로우 테스트"""
        # 1. 초기 상태 확인
        node = self.parsed_model.nodes[0]
        assert node.x == 0.0
        assert self.model.can_undo() is False
        assert self.model.is_dirty is False

        # 2. 수정
        self.model.modify_item('nodes', node, 'x', 10.0)
        assert node.x == 10.0
        assert self.model.can_undo() is True
        assert self.model.is_dirty is True

        # 3. Undo
        self.model.undo()
        assert node.x == 0.0
        assert self.model.can_undo() is False
        assert self.model.can_redo() is True

        # 4. Redo
        self.model.redo()
        assert node.x == 10.0
        assert self.model.can_undo() is True
        assert self.model.can_redo() is False

    def test_copy_paste_workflow(self):
        """복사 → 붙여넣기 워크플로우 테스트"""
        clipboard = get_clipboard()
        clipboard.clear()

        # 1. 노드 복사
        nodes_to_copy = self.parsed_model.nodes[:2]
        result = clipboard.copy('nodes', nodes_to_copy)
        assert result is True
        assert clipboard.has_data() is True

        # 2. 붙여넣기
        paste_result = clipboard.paste()
        assert paste_result is not None

        category, pasted_items, was_cut = paste_result
        assert category == 'nodes'
        assert len(pasted_items) == 2
        assert pasted_items[0].x == 0.0
        assert pasted_items[1].x == 1.0

        # 3. 원본은 변경되지 않음
        assert len(self.parsed_model.nodes) == 3

    def test_add_delete_undo_workflow(self):
        """추가 → 삭제 → Undo 워크플로우 테스트"""
        # 1. 초기 개수
        initial_count = len(self.parsed_model.nodes)
        assert initial_count == 3

        # 2. 노드 추가
        new_node = DummyNode(nid=4, x=2.0, y=2.0, z=0.0)
        self.model.add_item('nodes', new_node)
        assert len(self.parsed_model.nodes) == 4
        assert self.model.can_undo() is True

        # 3. Undo (추가 취소)
        self.model.undo()
        assert len(self.parsed_model.nodes) == 3
        assert new_node not in self.parsed_model.nodes

        # 4. Redo (다시 추가)
        self.model.redo()
        assert len(self.parsed_model.nodes) == 4
        assert new_node in self.parsed_model.nodes

        # 5. 삭제
        self.model.delete_item('nodes', new_node)
        assert len(self.parsed_model.nodes) == 3
        assert new_node not in self.parsed_model.nodes

        # 6. Undo (삭제 취소)
        self.model.undo()
        assert len(self.parsed_model.nodes) == 4
        assert new_node in self.parsed_model.nodes

    def test_batch_modification_workflow(self):
        """일괄 수정 워크플로우 테스트"""
        nodes = self.parsed_model.nodes

        # 1. 배치 시작
        self.model.undo_manager.begin_batch("Batch move nodes")

        # 2. 여러 노드 수정
        for node in nodes:
            self.model.modify_item('nodes', node, 'z', 5.0)

        # 3. 배치 종료
        self.model.undo_manager.end_batch()

        # 4. 모든 노드가 수정됨
        for node in nodes:
            assert node.z == 5.0

        # 5. Undo 한 번으로 모든 변경 취소
        self.model.undo()
        for node in nodes:
            assert node.z == 0.0

        # 6. Redo 한 번으로 모든 변경 복원
        self.model.redo()
        for node in nodes:
            assert node.z == 5.0

    def test_export_workflow(self):
        """내보내기 워크플로우 테스트"""
        # 1. Export 옵션 설정
        opts = ExportOptions(
            include_comments=True,
            default_field_width=10,
            float_precision=8
        )
        self.model.export_options = opts

        # 2. 임시 파일로 내보내기
        with tempfile.NamedTemporaryFile(mode='w', suffix='.k', delete=False) as f:
            filepath = f.name

        try:
            from gui.modules.keyword_manager.core.exporter import KFileExporter
            exporter = KFileExporter(self.parsed_model, opts)
            result = exporter.export(filepath)

            assert result is True
            assert os.path.exists(filepath)

            # 3. 내보낸 파일 검증
            with open(filepath, 'r') as f:
                content = f.read()

            assert '*KEYWORD' in content
            assert '*NODE' in content
            assert '*ELEMENT_SHELL' in content
            assert '*PART' in content
            assert '*SECTION_SHELL' in content
            assert '*MAT_ELASTIC' in content
            assert '*END' in content

        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_complex_workflow(self):
        """복잡한 시나리오 통합 테스트"""
        clipboard = get_clipboard()
        clipboard.clear()

        # 1. 여러 노드 수정
        self.model.modify_item('nodes', self.parsed_model.nodes[0], 'x', 100.0)
        self.model.modify_item('nodes', self.parsed_model.nodes[1], 'y', 200.0)

        # 2. 노드 추가
        new_node = DummyNode(nid=10, x=50.0, y=50.0, z=50.0)
        self.model.add_item('nodes', new_node)

        # 3. 일부 노드 복사
        clipboard.copy('nodes', [self.parsed_model.nodes[0]])

        # 4. 요소 수정
        self.model.modify_item('shell', self.parsed_model.shells[0], 'pid', 2)

        # 5. Dirty 상태 확인
        assert self.model.is_dirty is True

        # 6. Undo 여러 번
        assert self.model.can_undo() is True
        self.model.undo()  # 요소 수정 취소
        assert self.parsed_model.shells[0].pid == 1

        self.model.undo()  # 노드 추가 취소
        assert len(self.parsed_model.nodes) == 3

        self.model.undo()  # 노드 y 수정 취소
        assert self.parsed_model.nodes[1].y == 0.0

        self.model.undo()  # 노드 x 수정 취소
        assert self.parsed_model.nodes[0].x == 0.0

        # 7. 모든 변경이 취소됨
        assert self.model.can_undo() is False

        # 8. 붙여넣기는 여전히 가능
        assert clipboard.has_data() is True


class TestDataConsistency:
    """데이터 일관성 테스트"""

    def setup_method(self):
        """각 테스트 전 초기화"""
        self.model = KeywordModel()
        self.parsed_model = DummyParsedModel()
        self.model.set_model(self.parsed_model)

    def test_node_modification_consistency(self):
        """노드 수정 시 일관성 테스트"""
        node = DummyNode(nid=1, x=0.0, y=0.0, z=0.0)
        self.parsed_model.nodes.append(node)

        # 수정
        self.model.modify_item('nodes', node, 'x', 10.0)
        assert node.x == 10.0

        # 같은 노드를 다시 조회해도 동일
        nodes = self.model.get_items('nodes')
        assert nodes[0].x == 10.0
        assert nodes[0] is node  # 동일 객체

    def test_add_item_id_consistency(self):
        """항목 추가 시 ID 일관성 테스트"""
        # 기존 노드
        self.parsed_model.nodes = [
            DummyNode(nid=1),
            DummyNode(nid=5),
            DummyNode(nid=3),
        ]

        # 다음 ID 확인
        next_id = self.model.get_next_id('nodes')
        assert next_id == 6  # max(1, 5, 3) + 1

    def test_delete_preserves_order(self):
        """삭제 후 Undo 시 순서 보존 테스트"""
        nodes = [
            DummyNode(nid=1),
            DummyNode(nid=2),
            DummyNode(nid=3),
        ]
        self.parsed_model.nodes = nodes.copy()

        # 중간 노드 삭제
        self.model.delete_item('nodes', nodes[1])
        assert len(self.parsed_model.nodes) == 2
        assert self.parsed_model.nodes[0].nid == 1
        assert self.parsed_model.nodes[1].nid == 3

        # Undo로 복원
        self.model.undo()
        assert len(self.parsed_model.nodes) == 3
        assert self.parsed_model.nodes[0].nid == 1
        assert self.parsed_model.nodes[1].nid == 2
        assert self.parsed_model.nodes[2].nid == 3


class TestErrorHandling:
    """오류 처리 테스트"""

    def setup_method(self):
        """각 테스트 전 초기화"""
        self.model = KeywordModel()
        self.parsed_model = DummyParsedModel()
        self.model.set_model(self.parsed_model)

    def test_modify_invalid_field(self):
        """존재하지 않는 필드 수정 시도 테스트"""
        node = DummyNode(nid=1)
        self.parsed_model.nodes.append(node)

        # 잘못된 필드 수정 시도 (실패해야 함)
        result = self.model.modify_item('nodes', node, 'invalid_field', 100)
        assert result is False
        assert self.model.can_undo() is False

    def test_empty_category_operations(self):
        """빈 카테고리 작업 테스트"""
        # 빈 카테고리 조회
        items = self.model.get_items('nodes')
        assert items == []
        assert self.model.get_category_count('nodes') == 0

        # 빈 카테고리에서 다음 ID
        next_id = self.model.get_next_id('nodes')
        assert next_id == 1

    def test_clipboard_empty_paste(self):
        """빈 클립보드 붙여넣기 테스트"""
        clipboard = get_clipboard()
        clipboard.clear()

        result = clipboard.paste()
        assert result is None


class TestPerformance:
    """성능 관련 테스트"""

    def setup_method(self):
        """각 테스트 전 초기화"""
        self.model = KeywordModel()
        self.parsed_model = DummyParsedModel()

    def test_large_dataset_operations(self):
        """큰 데이터셋 작업 테스트"""
        # 1000개 노드 생성
        nodes = [DummyNode(nid=i, x=float(i), y=float(i*2), z=0.0) for i in range(1, 1001)]
        self.parsed_model.nodes = nodes
        self.model.set_model(self.parsed_model)

        # 조회 성능
        items = self.model.get_items('nodes')
        assert len(items) == 1000

        # 개수 확인
        count = self.model.get_category_count('nodes')
        assert count == 1000

        # 다음 ID 확인
        next_id = self.model.get_next_id('nodes')
        assert next_id == 1001

    def test_undo_stack_limit(self):
        """Undo 스택 크기 제한 테스트"""
        from gui.modules.keyword_manager.core.undo_manager import UndoManager

        node = DummyNode(nid=1, x=0.0)
        self.parsed_model.nodes.append(node)
        self.model.set_model(self.parsed_model)

        # 원래 max size 저장
        original_max = UndoManager.MAX_HISTORY_SIZE
        UndoManager.MAX_HISTORY_SIZE = 5

        try:
            # 10번 수정
            for i in range(10):
                self.model.modify_item('nodes', node, 'x', float(i))

            # Undo는 최대 5번만 가능
            undo_count = 0
            while self.model.can_undo():
                self.model.undo()
                undo_count += 1

            assert undo_count == 5

        finally:
            UndoManager.MAX_HISTORY_SIZE = original_max


if __name__ == '__main__':
    pytest.main([__file__, '-v'])