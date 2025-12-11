"""KeywordModel 테스트

KeywordModel 데이터 모델 기능 테스트
"""
import pytest
from dataclasses import dataclass, field
from typing import List, Optional

from gui.modules.keyword_manager.core.keyword_model import (
    KeywordModel, CategoryInfo, KEYWORD_CATEGORIES
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
class DummyPart:
    pid: int
    name: str = ""
    secid: int = 0
    mid: int = 0


class DummyParsedModel:
    """테스트용 ParsedModelData 대체"""

    def __init__(self):
        self._nodes: List[DummyNode] = []
        self._shells: List[DummyShell] = []
        self._solids: List = []
        self._beams: List = []
        self._parts: List[DummyPart] = []
        self._materials: List = []
        self._sections: List = []
        self._contacts: List = []
        self._sets: List = []
        self.controls: dict = {}
        self.databases: dict = {}
        self.boundaries: dict = {}
        self.loads: dict = {}
        self.initials: dict = {}
        self.constraineds: dict = {}
        self.title: str = "Test Model"
        self._filepath: str = "test.k"
        self._is_loaded: bool = True
        self.parse_time_ms: float = 0.0

    @property
    def nodes(self):
        return self._nodes

    @property
    def shells(self):
        return self._shells

    @property
    def solids(self):
        return self._solids

    @property
    def beams(self):
        return self._beams

    @property
    def parts(self):
        return self._parts

    @property
    def materials(self):
        return self._materials

    @property
    def sections(self):
        return self._sections

    @property
    def contacts(self):
        return self._contacts

    @property
    def sets(self):
        return self._sets

    @property
    def is_loaded(self):
        return self._is_loaded

    @property
    def filepath(self):
        return self._filepath

    @property
    def filename(self):
        return "test.k"


class TestKeywordModel:
    """KeywordModel 기본 테스트"""

    def setup_method(self):
        """각 테스트 전 모델 초기화"""
        self.parsed_model = DummyParsedModel()
        self.model = KeywordModel(self.parsed_model)

    def test_is_loaded(self):
        """로드 상태 테스트"""
        assert self.model.is_loaded is True

        empty_model = KeywordModel()
        assert empty_model.is_loaded is False

    def test_set_model(self):
        """모델 설정 테스트"""
        empty_model = KeywordModel()
        assert empty_model.is_loaded is False

        empty_model.set_model(self.parsed_model)
        assert empty_model.is_loaded is True

    def test_filepath(self):
        """파일 경로 테스트"""
        assert self.model.filepath == "test.k"

    def test_filename(self):
        """파일명 테스트"""
        assert self.model.filename == "test.k"


class TestKeywordModelItems:
    """KeywordModel 항목 관리 테스트"""

    def setup_method(self):
        """각 테스트 전 모델 초기화"""
        self.parsed_model = DummyParsedModel()
        self.parsed_model._nodes = [
            DummyNode(nid=1, x=0.0),
            DummyNode(nid=2, x=1.0),
            DummyNode(nid=3, x=2.0),
        ]
        self.parsed_model._shells = [
            DummyShell(eid=1, pid=1, nodes=[1, 2, 3, 4]),
        ]
        self.parsed_model._parts = [
            DummyPart(pid=1, name="Part1"),
        ]
        self.model = KeywordModel(self.parsed_model)

    def test_get_items_nodes(self):
        """노드 항목 가져오기 테스트"""
        items = self.model.get_items('nodes')
        assert len(items) == 3
        assert items[0].nid == 1

    def test_get_items_shells(self):
        """쉘 요소 항목 가져오기 테스트"""
        items = self.model.get_items('shell')
        assert len(items) == 1
        assert items[0].eid == 1

    def test_get_items_parts(self):
        """파트 항목 가져오기 테스트"""
        items = self.model.get_items('parts')
        assert len(items) == 1
        assert items[0].name == "Part1"

    def test_get_items_empty_category(self):
        """빈 카테고리 항목 가져오기 테스트"""
        items = self.model.get_items('materials')
        assert len(items) == 0

    def test_get_items_invalid_category(self):
        """잘못된 카테고리 테스트"""
        items = self.model.get_items('invalid_category')
        assert items == []

    def test_get_category_count(self):
        """카테고리 개수 테스트"""
        assert self.model.get_category_count('nodes') == 3
        assert self.model.get_category_count('shell') == 1
        assert self.model.get_category_count('materials') == 0


class TestKeywordModelModify:
    """KeywordModel 수정 기능 테스트"""

    def setup_method(self):
        """각 테스트 전 모델 초기화"""
        self.parsed_model = DummyParsedModel()
        self.parsed_model._nodes = [
            DummyNode(nid=1, x=0.0, y=0.0, z=0.0),
        ]
        self.parsed_model._shells = [
            DummyShell(eid=1, pid=1, nodes=[1, 2, 3, 4]),
        ]
        self.model = KeywordModel(self.parsed_model)

    def test_modify_item(self):
        """항목 수정 테스트"""
        node = self.parsed_model._nodes[0]

        result = self.model.modify_item('nodes', node, 'x', 10.0)

        assert result is True
        assert node.x == 10.0
        assert self.model.is_dirty is True

    def test_modify_item_undo(self):
        """항목 수정 후 Undo 테스트"""
        node = self.parsed_model._nodes[0]
        original_x = node.x

        self.model.modify_item('nodes', node, 'x', 10.0)
        assert node.x == 10.0

        self.model.undo()
        assert node.x == original_x

    def test_modify_nodes_list(self):
        """요소 노드 리스트 수정 테스트"""
        shell = self.parsed_model._shells[0]

        result = self.model.modify_item('shell', shell, 'n1', 100)

        assert result is True
        assert shell.nodes[0] == 100

    def test_modify_invalid_field(self):
        """존재하지 않는 필드 수정 테스트"""
        node = self.parsed_model._nodes[0]

        result = self.model.modify_item('nodes', node, 'invalid_field', 10.0)

        assert result is False


class TestKeywordModelAddDelete:
    """KeywordModel 추가/삭제 테스트"""

    def setup_method(self):
        """각 테스트 전 모델 초기화"""
        self.parsed_model = DummyParsedModel()
        self.parsed_model._nodes = [
            DummyNode(nid=1),
            DummyNode(nid=2),
        ]
        self.model = KeywordModel(self.parsed_model)

    def test_add_item(self):
        """항목 추가 테스트"""
        new_node = DummyNode(nid=3, x=10.0)

        result = self.model.add_item('nodes', new_node)

        assert result is True
        assert len(self.parsed_model._nodes) == 3
        assert self.parsed_model._nodes[-1] == new_node

    def test_add_item_undo(self):
        """항목 추가 후 Undo 테스트"""
        new_node = DummyNode(nid=3)

        self.model.add_item('nodes', new_node)
        assert len(self.parsed_model._nodes) == 3

        self.model.undo()
        assert len(self.parsed_model._nodes) == 2

    def test_delete_item(self):
        """항목 삭제 테스트"""
        node_to_delete = self.parsed_model._nodes[0]

        result = self.model.delete_item('nodes', node_to_delete)

        assert result is True
        assert len(self.parsed_model._nodes) == 1
        assert node_to_delete not in self.parsed_model._nodes

    def test_delete_item_undo(self):
        """항목 삭제 후 Undo 테스트"""
        node_to_delete = self.parsed_model._nodes[0]

        self.model.delete_item('nodes', node_to_delete)
        assert len(self.parsed_model._nodes) == 1

        self.model.undo()
        assert len(self.parsed_model._nodes) == 2
        assert node_to_delete in self.parsed_model._nodes

    def test_get_next_id(self):
        """다음 ID 가져오기 테스트"""
        next_id = self.model.get_next_id('nodes')
        assert next_id == 3  # 기존 최대 ID(2) + 1

    def test_get_next_id_empty(self):
        """빈 카테고리의 다음 ID 테스트"""
        next_id = self.model.get_next_id('parts')
        assert next_id == 1


class TestKeywordModelUndoRedo:
    """KeywordModel Undo/Redo 테스트"""

    def setup_method(self):
        """각 테스트 전 모델 초기화"""
        self.parsed_model = DummyParsedModel()
        self.parsed_model._nodes = [
            DummyNode(nid=1, x=0.0),
        ]
        self.model = KeywordModel(self.parsed_model)

    def test_can_undo_initially_false(self):
        """초기 상태에서 Undo 불가 테스트"""
        assert self.model.can_undo() is False

    def test_can_redo_initially_false(self):
        """초기 상태에서 Redo 불가 테스트"""
        assert self.model.can_redo() is False

    def test_can_undo_after_modify(self):
        """수정 후 Undo 가능 테스트"""
        node = self.parsed_model._nodes[0]
        self.model.modify_item('nodes', node, 'x', 10.0)

        assert self.model.can_undo() is True

    def test_can_redo_after_undo(self):
        """Undo 후 Redo 가능 테스트"""
        node = self.parsed_model._nodes[0]
        self.model.modify_item('nodes', node, 'x', 10.0)
        self.model.undo()

        assert self.model.can_redo() is True

    def test_multiple_undo_redo(self):
        """다중 Undo/Redo 테스트"""
        node = self.parsed_model._nodes[0]

        self.model.modify_item('nodes', node, 'x', 1.0)
        self.model.modify_item('nodes', node, 'x', 2.0)
        self.model.modify_item('nodes', node, 'x', 3.0)

        assert node.x == 3.0

        self.model.undo()
        assert node.x == 2.0

        self.model.undo()
        assert node.x == 1.0

        self.model.redo()
        assert node.x == 2.0


class TestKeywordModelDirtyState:
    """KeywordModel dirty 상태 테스트"""

    def setup_method(self):
        """각 테스트 전 모델 초기화"""
        self.parsed_model = DummyParsedModel()
        self.parsed_model._nodes = [
            DummyNode(nid=1),
        ]
        self.model = KeywordModel(self.parsed_model)

    def test_initially_not_dirty(self):
        """초기 상태에서 dirty 아님 테스트"""
        assert self.model.is_dirty is False

    def test_dirty_after_modify(self):
        """수정 후 dirty 테스트"""
        node = self.parsed_model._nodes[0]
        self.model.modify_item('nodes', node, 'x', 10.0)

        assert self.model.is_dirty is True

    def test_dirty_after_add(self):
        """추가 후 dirty 테스트"""
        new_node = DummyNode(nid=2)
        self.model.add_item('nodes', new_node)

        assert self.model.is_dirty is True

    def test_dirty_after_delete(self):
        """삭제 후 dirty 테스트"""
        node = self.parsed_model._nodes[0]
        self.model.delete_item('nodes', node)

        assert self.model.is_dirty is True


class TestCategoryInfo:
    """CategoryInfo 테스트"""

    def test_category_info_fields(self):
        """CategoryInfo 필드 테스트"""
        info = CategoryInfo(
            id='test',
            name='Test',
            name_ko='테스트',
            icon='test_icon'
        )

        assert info.id == 'test'
        assert info.name == 'Test'
        assert info.name_ko == '테스트'
        assert info.icon == 'test_icon'
        assert info.is_group is False
        assert info.subcategories == []

    def test_category_info_with_subcategories(self):
        """CategoryInfo 서브카테고리 테스트"""
        sub = CategoryInfo(id='sub', name='Sub', name_ko='서브', icon='sub_icon')
        info = CategoryInfo(
            id='group',
            name='Group',
            name_ko='그룹',
            icon='group_icon',
            is_group=True,
            subcategories=[sub]
        )

        assert info.is_group is True
        assert len(info.subcategories) == 1
        assert info.subcategories[0].id == 'sub'


class TestKeywordCategories:
    """KEYWORD_CATEGORIES 테스트"""

    def _get_all_category_ids(self):
        """모든 카테고리 ID 수집 (서브카테고리 포함)"""
        ids = []
        for cat in KEYWORD_CATEGORIES:
            ids.append(cat.id)
            for sub in cat.subcategories:
                ids.append(sub.id)
        return ids

    def test_categories_exist(self):
        """주요 카테고리 존재 테스트"""
        all_ids = self._get_all_category_ids()

        assert 'nodes' in all_ids
        assert 'shell' in all_ids  # elements 하위 카테고리
        assert 'solid' in all_ids  # elements 하위 카테고리
        assert 'parts' in all_ids
        assert 'materials' in all_ids
        assert 'sections' in all_ids

    def test_categories_have_names(self):
        """카테고리에 이름이 있는지 테스트"""
        for cat in KEYWORD_CATEGORIES:
            assert cat.name is not None
            assert len(cat.name) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
