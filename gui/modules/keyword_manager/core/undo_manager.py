"""Undo/Redo Manager using Command Pattern

키워드 편집 작업의 실행 취소 및 다시 실행을 관리합니다.
"""
from typing import Any, Optional, List, Dict, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from copy import deepcopy
from PySide6.QtCore import QObject, Signal


class Command(ABC):
    """추상 명령 클래스"""

    @abstractmethod
    def execute(self) -> bool:
        """명령 실행"""
        pass

    @abstractmethod
    def undo(self) -> bool:
        """명령 취소"""
        pass

    @abstractmethod
    def description(self) -> str:
        """명령 설명"""
        pass

    def redo(self) -> bool:
        """다시 실행 (기본적으로 execute와 동일)"""
        return self.execute()


class ModifyCommand(Command):
    """속성 수정 명령

    단일 속성 값을 변경하는 명령입니다.
    """

    def __init__(self, item: Any, field_name: str, old_value: Any, new_value: Any,
                 category: str = "", item_id: Any = None):
        self._item = item
        self._field_name = field_name
        self._old_value = old_value
        self._new_value = new_value
        self._category = category
        self._item_id = item_id

    def execute(self) -> bool:
        try:
            setattr(self._item, self._field_name, self._new_value)
            return True
        except Exception as e:
            print(f"[ModifyCommand] Execute error: {e}")
            return False

    def undo(self) -> bool:
        try:
            setattr(self._item, self._field_name, self._old_value)
            return True
        except Exception as e:
            print(f"[ModifyCommand] Undo error: {e}")
            return False

    def description(self) -> str:
        return f"Modify {self._category} {self._field_name}: {self._old_value} → {self._new_value}"

    @property
    def item(self) -> Any:
        return self._item

    @property
    def category(self) -> str:
        return self._category

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def old_value(self) -> Any:
        return self._old_value

    @property
    def new_value(self) -> Any:
        return self._new_value


class ModifyNodesCommand(Command):
    """노드 리스트 수정 명령

    요소의 nodes 리스트 내 특정 인덱스 값을 변경합니다.
    """

    def __init__(self, item: Any, index: int, old_value: int, new_value: int,
                 category: str = "", item_id: Any = None):
        self._item = item
        self._index = index
        self._old_value = old_value
        self._new_value = new_value
        self._category = category
        self._item_id = item_id

    def execute(self) -> bool:
        try:
            nodes = list(getattr(self._item, 'nodes', []))
            while len(nodes) <= self._index:
                nodes.append(0)
            nodes[self._index] = self._new_value
            setattr(self._item, 'nodes', nodes)
            return True
        except Exception as e:
            print(f"[ModifyNodesCommand] Execute error: {e}")
            return False

    def undo(self) -> bool:
        try:
            nodes = list(getattr(self._item, 'nodes', []))
            if self._index < len(nodes):
                nodes[self._index] = self._old_value
                setattr(self._item, 'nodes', nodes)
            return True
        except Exception as e:
            print(f"[ModifyNodesCommand] Undo error: {e}")
            return False

    def description(self) -> str:
        return f"Modify {self._category} n{self._index + 1}: {self._old_value} → {self._new_value}"

    @property
    def item(self) -> Any:
        return self._item

    @property
    def category(self) -> str:
        return self._category


class AddCommand(Command):
    """항목 추가 명령"""

    def __init__(self, items_list: List, item: Any, index: int = -1,
                 category: str = "", on_add: Callable = None, on_remove: Callable = None):
        self._items_list = items_list
        self._item = item
        self._index = index if index >= 0 else len(items_list)
        self._category = category
        self._on_add = on_add
        self._on_remove = on_remove

    def execute(self) -> bool:
        try:
            if self._index >= len(self._items_list):
                self._items_list.append(self._item)
            else:
                self._items_list.insert(self._index, self._item)
            if self._on_add:
                self._on_add(self._category, self._item)
            return True
        except Exception as e:
            print(f"[AddCommand] Execute error: {e}")
            return False

    def undo(self) -> bool:
        try:
            self._items_list.remove(self._item)
            if self._on_remove:
                self._on_remove(self._category, self._item)
            return True
        except Exception as e:
            print(f"[AddCommand] Undo error: {e}")
            return False

    def description(self) -> str:
        return f"Add {self._category} item"

    @property
    def item(self) -> Any:
        return self._item

    @property
    def category(self) -> str:
        return self._category


class DeleteCommand(Command):
    """항목 삭제 명령"""

    def __init__(self, items_list: List, item: Any, index: int = -1,
                 category: str = "", on_add: Callable = None, on_remove: Callable = None):
        self._items_list = items_list
        self._item = item
        self._index = index if index >= 0 else items_list.index(item) if item in items_list else -1
        self._category = category
        self._on_add = on_add
        self._on_remove = on_remove

    def execute(self) -> bool:
        try:
            if self._item in self._items_list:
                self._index = self._items_list.index(self._item)
                self._items_list.remove(self._item)
                if self._on_remove:
                    self._on_remove(self._category, self._item)
            return True
        except Exception as e:
            print(f"[DeleteCommand] Execute error: {e}")
            return False

    def undo(self) -> bool:
        try:
            if self._index >= 0:
                if self._index >= len(self._items_list):
                    self._items_list.append(self._item)
                else:
                    self._items_list.insert(self._index, self._item)
                if self._on_add:
                    self._on_add(self._category, self._item)
            return True
        except Exception as e:
            print(f"[DeleteCommand] Undo error: {e}")
            return False

    def description(self) -> str:
        return f"Delete {self._category} item"

    @property
    def item(self) -> Any:
        return self._item

    @property
    def category(self) -> str:
        return self._category


class BatchCommand(Command):
    """여러 명령을 하나로 묶는 배치 명령"""

    def __init__(self, commands: List[Command] = None, desc: str = "Batch operation"):
        self._commands: List[Command] = commands or []
        self._desc = desc

    def add(self, command: Command):
        """명령 추가"""
        self._commands.append(command)

    def execute(self) -> bool:
        success = True
        executed = []
        for cmd in self._commands:
            if cmd.execute():
                executed.append(cmd)
            else:
                # 롤백
                for done in reversed(executed):
                    done.undo()
                success = False
                break
        return success

    def undo(self) -> bool:
        success = True
        for cmd in reversed(self._commands):
            if not cmd.undo():
                success = False
        return success

    def description(self) -> str:
        return self._desc

    @property
    def commands(self) -> List[Command]:
        return self._commands

    def is_empty(self) -> bool:
        return len(self._commands) == 0


class UndoManager(QObject):
    """Undo/Redo 매니저

    실행된 명령들의 히스토리를 관리하고 undo/redo 기능을 제공합니다.
    """

    # 시그널
    undoAvailable = Signal(bool)
    redoAvailable = Signal(bool)
    commandExecuted = Signal(str)  # 명령 설명
    historyChanged = Signal()

    # 히스토리 최대 크기
    MAX_HISTORY_SIZE = 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._batch_command: Optional[BatchCommand] = None

    def execute(self, command: Command) -> bool:
        """명령 실행 및 히스토리에 추가"""
        # 배치 모드인 경우
        if self._batch_command is not None:
            self._batch_command.add(command)
            return command.execute()

        # 일반 실행
        if command.execute():
            self._undo_stack.append(command)
            self._redo_stack.clear()  # 새 명령 실행 시 redo 스택 클리어

            # 히스토리 크기 제한
            while len(self._undo_stack) > self.MAX_HISTORY_SIZE:
                self._undo_stack.pop(0)

            self._emit_state_signals()
            self.commandExecuted.emit(command.description())
            return True
        return False

    def undo(self) -> bool:
        """실행 취소"""
        if not self._undo_stack:
            return False

        command = self._undo_stack.pop()
        if command.undo():
            self._redo_stack.append(command)
            self._emit_state_signals()
            return True
        else:
            # 실패 시 스택에 다시 추가
            self._undo_stack.append(command)
            return False

    def redo(self) -> bool:
        """다시 실행"""
        if not self._redo_stack:
            return False

        command = self._redo_stack.pop()
        if command.redo():
            self._undo_stack.append(command)
            self._emit_state_signals()
            return True
        else:
            # 실패 시 스택에 다시 추가
            self._redo_stack.append(command)
            return False

    def begin_batch(self, description: str = "Batch operation"):
        """배치 명령 시작"""
        if self._batch_command is None:
            self._batch_command = BatchCommand(desc=description)

    def end_batch(self) -> bool:
        """배치 명령 종료 및 히스토리에 추가"""
        if self._batch_command is None:
            return False

        batch = self._batch_command
        self._batch_command = None

        if batch.is_empty():
            return True

        # 배치 명령의 execute는 이미 개별적으로 실행됨
        # 히스토리에만 추가
        self._undo_stack.append(batch)
        self._redo_stack.clear()

        while len(self._undo_stack) > self.MAX_HISTORY_SIZE:
            self._undo_stack.pop(0)

        self._emit_state_signals()
        self.commandExecuted.emit(batch.description())
        return True

    def cancel_batch(self):
        """배치 명령 취소 (실행된 것들 롤백)"""
        if self._batch_command is None:
            return

        # 이미 실행된 명령들 롤백
        for cmd in reversed(self._batch_command.commands):
            cmd.undo()

        self._batch_command = None

    def can_undo(self) -> bool:
        """undo 가능 여부"""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """redo 가능 여부"""
        return len(self._redo_stack) > 0

    def clear(self):
        """히스토리 초기화"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._batch_command = None
        self._emit_state_signals()

    def get_undo_description(self) -> str:
        """다음 undo 명령 설명"""
        if self._undo_stack:
            return self._undo_stack[-1].description()
        return ""

    def get_redo_description(self) -> str:
        """다음 redo 명령 설명"""
        if self._redo_stack:
            return self._redo_stack[-1].description()
        return ""

    def get_history(self) -> List[str]:
        """히스토리 설명 목록"""
        return [cmd.description() for cmd in self._undo_stack]

    def _emit_state_signals(self):
        """상태 변경 시그널 발신"""
        self.undoAvailable.emit(self.can_undo())
        self.redoAvailable.emit(self.can_redo())
        self.historyChanged.emit()


# Singleton instance (optional - can also create per-module)
_global_undo_manager: Optional[UndoManager] = None


def get_undo_manager() -> UndoManager:
    """글로벌 UndoManager 인스턴스 반환"""
    global _global_undo_manager
    if _global_undo_manager is None:
        _global_undo_manager = UndoManager()
    return _global_undo_manager
