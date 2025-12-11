"""Clipboard 테스트

KeywordClipboard 복사/붙여넣기 기능 테스트
"""
import pytest
from dataclasses import dataclass
from typing import List

from gui.modules.keyword_manager.core.clipboard import (
    KeywordClipboard, ClipboardData, ClipboardFormat,
    KeywordFactory, get_clipboard
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


class TestKeywordClipboard:
    """KeywordClipboard 테스트"""

    def setup_method(self):
        """각 테스트 전 클립보드 초기화"""
        self.clipboard = KeywordClipboard()

    def test_copy_single_item(self):
        """단일 항목 복사 테스트"""
        node = DummyNode(nid=1, x=10.0, y=20.0, z=30.0)

        result = self.clipboard.copy('nodes', [node])

        assert result is True
        assert self.clipboard.has_data() is True
        assert self.clipboard.get_category() == 'nodes'
        assert self.clipboard.get_item_count() == 1

    def test_copy_multiple_items(self):
        """다중 항목 복사 테스트"""
        nodes = [
            DummyNode(nid=1, x=10.0),
            DummyNode(nid=2, x=20.0),
            DummyNode(nid=3, x=30.0),
        ]

        result = self.clipboard.copy('nodes', nodes)

        assert result is True
        assert self.clipboard.get_item_count() == 3

    def test_copy_empty_list_fails(self):
        """빈 리스트 복사 실패 테스트"""
        result = self.clipboard.copy('nodes', [])

        assert result is False
        assert self.clipboard.has_data() is False

    def test_paste_returns_copied_items(self):
        """붙여넣기가 복사된 항목을 반환하는지 테스트"""
        node = DummyNode(nid=1, x=10.0)
        self.clipboard.copy('nodes', [node])

        result = self.clipboard.paste()

        assert result is not None
        category, items, was_cut = result
        assert category == 'nodes'
        assert len(items) == 1
        assert items[0].x == 10.0

    def test_paste_returns_deep_copy(self):
        """붙여넣기가 깊은 복사본을 반환하는지 테스트"""
        node = DummyNode(nid=1, x=10.0)
        self.clipboard.copy('nodes', [node])

        result = self.clipboard.paste()
        category, items, was_cut = result

        # 원본 수정
        node.x = 999.0

        # 복사본은 영향받지 않음
        assert items[0].x == 10.0

    def test_cut_marks_cut_mode(self):
        """잘라내기가 cut 모드를 설정하는지 테스트"""
        node = DummyNode(nid=1)

        result = self.clipboard.cut('nodes', [node])

        assert result is True
        assert self.clipboard.is_cut_mode() is True

    def test_paste_after_cut_clears_clipboard(self):
        """잘라내기 후 붙여넣기가 클립보드를 비우는지 테스트"""
        node = DummyNode(nid=1)
        cut_result = self.clipboard.cut('nodes', [node])
        assert cut_result is True
        assert self.clipboard.has_data() is True

        result = self.clipboard.paste()

        assert result is not None
        assert self.clipboard.has_data() is False

    def test_paste_after_copy_keeps_clipboard(self):
        """복사 후 붙여넣기가 클립보드를 유지하는지 테스트"""
        node = DummyNode(nid=1)
        self.clipboard.copy('nodes', [node])

        result = self.clipboard.paste()

        assert result is not None
        assert self.clipboard.has_data() is True

    def test_clear(self):
        """clear가 클립보드를 비우는지 테스트"""
        node = DummyNode(nid=1)
        self.clipboard.copy('nodes', [node])

        self.clipboard.clear()

        assert self.clipboard.has_data() is False
        assert self.clipboard.is_cut_mode() is False

    def test_can_paste_to_same_category(self):
        """같은 카테고리에 붙여넣기 가능 테스트"""
        node = DummyNode(nid=1)
        self.clipboard.copy('nodes', [node])

        assert self.clipboard.can_paste_to('nodes') is True

    def test_cannot_paste_to_different_category(self):
        """다른 카테고리에 붙여넣기 불가 테스트"""
        node = DummyNode(nid=1)
        self.clipboard.copy('nodes', [node])

        assert self.clipboard.can_paste_to('shell') is False
        assert self.clipboard.can_paste_to('parts') is False

    def test_element_types_not_compatible(self):
        """요소 타입 간 호환되지 않음 테스트"""
        shell = DummyShell(eid=1)
        self.clipboard.copy('shell', [shell])

        assert self.clipboard.can_paste_to('solid') is False
        assert self.clipboard.can_paste_to('beam') is False

    def test_get_preview_text(self):
        """미리보기 텍스트 테스트"""
        nodes = [DummyNode(nid=1), DummyNode(nid=2)]
        self.clipboard.copy('nodes', nodes)

        preview = self.clipboard.get_preview_text()

        assert 'Copy' in preview
        assert '2' in preview
        assert 'nodes' in preview


class TestKeywordFactory:
    """KeywordFactory 테스트"""

    def test_create_node(self):
        """노드 생성 테스트"""
        node = KeywordFactory.create_node(100, x=1.0, y=2.0, z=3.0)

        assert node.nid == 100
        assert node.x == 1.0
        assert node.y == 2.0
        assert node.z == 3.0
        assert node.tc == 0
        assert node.rc == 0

    def test_create_shell(self):
        """쉘 요소 생성 테스트"""
        shell = KeywordFactory.create_shell(200, pid=1, nodes=[1, 2, 3, 4])

        assert shell.eid == 200
        assert shell.pid == 1
        assert shell.nodes == [1, 2, 3, 4]

    def test_create_shell_default_nodes(self):
        """쉘 요소 기본 노드 생성 테스트"""
        shell = KeywordFactory.create_shell(200)

        assert shell.nodes == [0, 0, 0, 0]

    def test_create_solid(self):
        """솔리드 요소 생성 테스트"""
        solid = KeywordFactory.create_solid(300, pid=2, nodes=[1, 2, 3, 4, 5, 6, 7, 8])

        assert solid.eid == 300
        assert solid.pid == 2
        assert len(solid.nodes) == 8

    def test_create_part(self):
        """파트 생성 테스트"""
        part = KeywordFactory.create_part(400, name="TestPart", secid=1, mid=2)

        assert part.pid == 400
        assert part.name == "TestPart"
        assert part.secid == 1
        assert part.mid == 2


class TestGetClipboard:
    """get_clipboard 싱글톤 테스트"""

    def test_returns_same_instance(self):
        """동일한 인스턴스를 반환하는지 테스트"""
        clipboard1 = get_clipboard()
        clipboard2 = get_clipboard()

        assert clipboard1 is clipboard2

    def test_shared_state(self):
        """상태가 공유되는지 테스트"""
        clipboard1 = get_clipboard()
        clipboard2 = get_clipboard()

        node = DummyNode(nid=1)
        clipboard1.copy('nodes', [node])

        assert clipboard2.has_data() is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
