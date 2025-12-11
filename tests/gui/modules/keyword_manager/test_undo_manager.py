"""Undo Manager 테스트

UndoManager 및 Command 패턴 테스트
"""
import pytest
from dataclasses import dataclass
from typing import List

from gui.modules.keyword_manager.core.undo_manager import (
    UndoManager, Command, ModifyCommand, ModifyNodesCommand,
    AddCommand, DeleteCommand, BatchCommand
)


# 테스트용 더미 데이터 클래스
@dataclass
class DummyNode:
    nid: int
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class DummyElement:
    eid: int
    pid: int = 0
    nodes: List[int] = None

    def __post_init__(self):
        if self.nodes is None:
            self.nodes = [0, 0, 0, 0]


class TestModifyCommand:
    """ModifyCommand 테스트"""

    def test_execute_changes_value(self):
        """execute가 값을 변경하는지 테스트"""
        node = DummyNode(nid=1, x=0.0)
        cmd = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')

        assert cmd.execute() is True
        assert node.x == 10.0

    def test_undo_restores_value(self):
        """undo가 값을 복원하는지 테스트"""
        node = DummyNode(nid=1, x=0.0)
        cmd = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')

        cmd.execute()
        assert node.x == 10.0

        assert cmd.undo() is True
        assert node.x == 0.0

    def test_description(self):
        """description이 올바른지 테스트"""
        node = DummyNode(nid=1)
        cmd = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')

        desc = cmd.description()
        assert 'nodes' in desc
        assert 'x' in desc


class TestModifyNodesCommand:
    """ModifyNodesCommand 테스트"""

    def test_execute_changes_node_value(self):
        """execute가 nodes 리스트의 값을 변경하는지 테스트"""
        elem = DummyElement(eid=1, nodes=[1, 2, 3, 4])
        cmd = ModifyNodesCommand(elem, 0, 1, 100, 'shell')

        assert cmd.execute() is True
        assert elem.nodes[0] == 100

    def test_undo_restores_node_value(self):
        """undo가 nodes 값을 복원하는지 테스트"""
        elem = DummyElement(eid=1, nodes=[1, 2, 3, 4])
        cmd = ModifyNodesCommand(elem, 0, 1, 100, 'shell')

        cmd.execute()
        assert elem.nodes[0] == 100

        cmd.undo()
        assert elem.nodes[0] == 1


class TestAddCommand:
    """AddCommand 테스트"""

    def test_execute_adds_item(self):
        """execute가 항목을 추가하는지 테스트"""
        items = []
        node = DummyNode(nid=1)
        cmd = AddCommand(items, node, -1, 'nodes')

        assert cmd.execute() is True
        assert len(items) == 1
        assert items[0] == node

    def test_undo_removes_item(self):
        """undo가 항목을 제거하는지 테스트"""
        items = []
        node = DummyNode(nid=1)
        cmd = AddCommand(items, node, -1, 'nodes')

        cmd.execute()
        assert len(items) == 1

        cmd.undo()
        assert len(items) == 0

    def test_on_add_callback(self):
        """on_add 콜백이 호출되는지 테스트"""
        items = []
        node = DummyNode(nid=1)
        callback_called = []

        def on_add(category, item):
            callback_called.append((category, item))

        cmd = AddCommand(items, node, -1, 'nodes', on_add=on_add)
        cmd.execute()

        assert len(callback_called) == 1
        assert callback_called[0] == ('nodes', node)


class TestDeleteCommand:
    """DeleteCommand 테스트"""

    def test_execute_removes_item(self):
        """execute가 항목을 제거하는지 테스트"""
        node = DummyNode(nid=1)
        items = [node]
        cmd = DeleteCommand(items, node, -1, 'nodes')

        assert cmd.execute() is True
        assert len(items) == 0

    def test_undo_restores_item(self):
        """undo가 항목을 복원하는지 테스트"""
        node = DummyNode(nid=1)
        items = [node]
        cmd = DeleteCommand(items, node, -1, 'nodes')

        cmd.execute()
        assert len(items) == 0

        cmd.undo()
        assert len(items) == 1
        assert items[0] == node

    def test_preserves_index(self):
        """삭제 후 복원 시 원래 위치에 복원되는지 테스트"""
        node1 = DummyNode(nid=1)
        node2 = DummyNode(nid=2)
        node3 = DummyNode(nid=3)
        items = [node1, node2, node3]

        cmd = DeleteCommand(items, node2, -1, 'nodes')
        cmd.execute()

        assert items == [node1, node3]

        cmd.undo()
        assert items[1] == node2


class TestBatchCommand:
    """BatchCommand 테스트"""

    def test_execute_all_commands(self):
        """모든 명령이 실행되는지 테스트"""
        node = DummyNode(nid=1, x=0.0, y=0.0)
        cmd1 = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')
        cmd2 = ModifyCommand(node, 'y', 0.0, 20.0, 'nodes')

        batch = BatchCommand([cmd1, cmd2], "일괄 수정")

        assert batch.execute() is True
        assert node.x == 10.0
        assert node.y == 20.0

    def test_undo_all_commands_in_reverse(self):
        """모든 명령이 역순으로 취소되는지 테스트"""
        node = DummyNode(nid=1, x=0.0, y=0.0)
        cmd1 = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')
        cmd2 = ModifyCommand(node, 'y', 0.0, 20.0, 'nodes')

        batch = BatchCommand([cmd1, cmd2], "일괄 수정")
        batch.execute()

        batch.undo()
        assert node.x == 0.0
        assert node.y == 0.0


class TestUndoManager:
    """UndoManager 테스트"""

    def test_execute_and_undo(self):
        """execute 후 undo가 작동하는지 테스트"""
        manager = UndoManager()
        node = DummyNode(nid=1, x=0.0)
        cmd = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')

        manager.execute(cmd)
        assert node.x == 10.0
        assert manager.can_undo() is True

        manager.undo()
        assert node.x == 0.0
        assert manager.can_undo() is False

    def test_redo(self):
        """redo가 작동하는지 테스트"""
        manager = UndoManager()
        node = DummyNode(nid=1, x=0.0)
        cmd = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')

        manager.execute(cmd)
        manager.undo()
        assert node.x == 0.0
        assert manager.can_redo() is True

        manager.redo()
        assert node.x == 10.0
        assert manager.can_redo() is False

    def test_new_command_clears_redo_stack(self):
        """새 명령 실행 시 redo 스택이 비워지는지 테스트"""
        manager = UndoManager()
        node = DummyNode(nid=1, x=0.0)

        cmd1 = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')
        manager.execute(cmd1)
        manager.undo()
        assert manager.can_redo() is True

        cmd2 = ModifyCommand(node, 'x', 0.0, 20.0, 'nodes')
        manager.execute(cmd2)
        assert manager.can_redo() is False

    def test_max_stack_size(self):
        """최대 스택 크기 제한 테스트"""
        manager = UndoManager()
        # UndoManager.MAX_HISTORY_SIZE를 임시로 3으로 변경
        original_max = UndoManager.MAX_HISTORY_SIZE
        UndoManager.MAX_HISTORY_SIZE = 3

        try:
            node = DummyNode(nid=1, x=0.0)

            for i in range(5):
                cmd = ModifyCommand(node, 'x', float(i), float(i + 1), 'nodes')
                manager.execute(cmd)

            # 최대 3개만 유지
            undo_count = 0
            while manager.can_undo():
                manager.undo()
                undo_count += 1

            assert undo_count == 3
        finally:
            # 원래 값 복원
            UndoManager.MAX_HISTORY_SIZE = original_max

    def test_clear(self):
        """clear가 스택을 비우는지 테스트"""
        manager = UndoManager()
        node = DummyNode(nid=1, x=0.0)
        cmd = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')

        manager.execute(cmd)
        assert manager.can_undo() is True

        manager.clear()
        assert manager.can_undo() is False
        assert manager.can_redo() is False

    def test_undo_description(self):
        """get_undo_description이 올바른지 테스트"""
        manager = UndoManager()
        node = DummyNode(nid=1, x=0.0)
        cmd = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')

        manager.execute(cmd)
        desc = manager.get_undo_description()

        assert 'nodes' in desc
        assert 'x' in desc

    def test_get_history(self):
        """get_history가 올바른지 테스트"""
        manager = UndoManager()
        node = DummyNode(nid=1, x=0.0, y=0.0)

        cmd1 = ModifyCommand(node, 'x', 0.0, 10.0, 'nodes')
        cmd2 = ModifyCommand(node, 'y', 0.0, 20.0, 'nodes')

        manager.execute(cmd1)
        manager.execute(cmd2)

        history = manager.get_history()
        assert len(history) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
