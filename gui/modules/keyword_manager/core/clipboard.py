"""Keyword Clipboard for Copy/Paste operations

키워드 항목의 복사, 잘라내기, 붙여넣기 기능을 제공합니다.
"""
from typing import Any, Optional, List, Dict, Tuple
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import json
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class ClipboardFormat(Enum):
    """클립보드 데이터 형식"""
    INTERNAL = "internal"  # 내부 Python 객체
    KFILE = "kfile"        # K-file 텍스트 형식
    JSON = "json"          # JSON 형식


@dataclass
class ClipboardData:
    """클립보드에 저장되는 데이터"""
    category: str
    items: List[Any]
    format: ClipboardFormat = ClipboardFormat.INTERNAL
    source_file: str = ""


class KeywordClipboard(QObject):
    """키워드 클립보드 매니저

    키워드 항목의 복사/붙여넣기를 관리합니다.
    내부 버퍼와 시스템 클립보드 모두 지원합니다.
    """

    # 시그널
    clipboardChanged = Signal()
    pasteAvailable = Signal(bool)

    # 내부 MIME 타입
    MIME_TYPE = "application/x-laminatemodeller-keyword"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Optional[ClipboardData] = None
        self._cut_mode: bool = False

    def copy(self, category: str, items: List[Any], source_file: str = "") -> bool:
        """항목 복사

        Args:
            category: 카테고리 ID
            items: 복사할 항목 목록
            source_file: 원본 파일 경로

        Returns:
            성공 여부
        """
        if not items:
            return False

        try:
            # 깊은 복사로 원본과 분리
            copied_items = [self._deep_copy_item(item) for item in items]

            self._data = ClipboardData(
                category=category,
                items=copied_items,
                format=ClipboardFormat.INTERNAL,
                source_file=source_file
            )
            self._cut_mode = False

            # 시스템 클립보드에도 K-file 형식으로 저장
            kfile_text = self._to_kfile_text(category, copied_items)
            if kfile_text:
                clipboard = QApplication.clipboard()
                clipboard.setText(kfile_text)

            self.clipboardChanged.emit()
            self.pasteAvailable.emit(True)
            return True

        except Exception as e:
            print(f"[KeywordClipboard] Copy error: {e}")
            return False

    def cut(self, category: str, items: List[Any], source_file: str = "") -> bool:
        """항목 잘라내기 (복사 + 삭제 플래그)

        Args:
            category: 카테고리 ID
            items: 잘라낼 항목 목록
            source_file: 원본 파일 경로

        Returns:
            성공 여부
        """
        if self.copy(category, items, source_file):
            self._cut_mode = True
            return True
        return False

    def paste(self) -> Optional[Tuple[str, List[Any], bool]]:
        """붙여넣기

        Returns:
            (category, items, was_cut) 튜플 또는 None
        """
        if not self._data or not self._data.items:
            return None

        try:
            # 붙여넣기할 항목들 (새 ID 할당 필요)
            category = self._data.category  # clear() 전에 저장
            pasted_items = [self._deep_copy_item(item) for item in self._data.items]
            was_cut = self._cut_mode

            # 잘라내기의 경우 클립보드 비우기
            if was_cut:
                self.clear()

            return (category, pasted_items, was_cut)

        except Exception as e:
            print(f"[KeywordClipboard] Paste error: {e}")
            return None

    def clear(self):
        """클립보드 비우기"""
        self._data = None
        self._cut_mode = False
        self.clipboardChanged.emit()
        self.pasteAvailable.emit(False)

    def has_data(self) -> bool:
        """데이터 존재 여부"""
        return self._data is not None and len(self._data.items) > 0

    def is_cut_mode(self) -> bool:
        """잘라내기 모드 여부"""
        return self._cut_mode

    def get_category(self) -> Optional[str]:
        """현재 클립보드의 카테고리"""
        return self._data.category if self._data else None

    def get_item_count(self) -> int:
        """클립보드 항목 수"""
        return len(self._data.items) if self._data else 0

    def can_paste_to(self, target_category: str) -> bool:
        """대상 카테고리에 붙여넣기 가능 여부

        같은 카테고리 또는 호환되는 카테고리에만 붙여넣기 가능
        """
        if not self._data:
            return False

        src = self._data.category
        tgt = target_category

        # 동일 카테고리
        if src == tgt:
            return True

        # 호환 카테고리 (예: shell, solid, beam은 요소 계열)
        element_types = {'shell', 'solid', 'beam'}
        if src in element_types and tgt in element_types:
            return False  # 요소 타입은 서로 호환되지 않음

        return False

    def _deep_copy_item(self, item: Any) -> Any:
        """항목 깊은 복사"""
        try:
            return deepcopy(item)
        except Exception:
            # deepcopy 실패 시 수동 복사
            return self._manual_copy(item)

    def _manual_copy(self, item: Any) -> Any:
        """수동 객체 복사 (deepcopy 실패 시 폴백)"""
        if hasattr(item, '__dict__'):
            # 객체의 __dict__ 복사
            new_item = object.__new__(type(item))
            new_item.__dict__.update(deepcopy(item.__dict__))
            return new_item
        else:
            return item

    def _to_kfile_text(self, category: str, items: List[Any]) -> str:
        """K-file 텍스트 형식으로 변환"""
        lines = []

        for item in items:
            if category == 'nodes':
                nid = getattr(item, 'nid', 0)
                x = getattr(item, 'x', 0.0)
                y = getattr(item, 'y', 0.0)
                z = getattr(item, 'z', 0.0)
                lines.append(f"{nid:8d}{x:16.8f}{y:16.8f}{z:16.8f}")

            elif category in ('shell', 'solid', 'beam'):
                eid = getattr(item, 'eid', 0)
                pid = getattr(item, 'pid', 0)
                nodes = getattr(item, 'nodes', [])

                if category == 'shell':
                    nodes_padded = list(nodes) + [0] * (4 - len(nodes))
                    line = f"{eid:8d}{pid:8d}" + ''.join(f"{n:8d}" for n in nodes_padded[:4])
                elif category == 'solid':
                    nodes_padded = list(nodes) + [0] * (8 - len(nodes))
                    line = f"{eid:8d}{pid:8d}" + ''.join(f"{n:8d}" for n in nodes_padded[:8])
                else:  # beam
                    n1 = nodes[0] if len(nodes) > 0 else 0
                    n2 = nodes[1] if len(nodes) > 1 else 0
                    n3 = nodes[2] if len(nodes) > 2 else 0
                    line = f"{eid:8d}{pid:8d}{n1:8d}{n2:8d}{n3:8d}"
                lines.append(line)

            elif category == 'parts':
                name = getattr(item, 'name', '')
                lines.append(f"$# {name}")
                pid = getattr(item, 'pid', 0)
                secid = getattr(item, 'secid', 0)
                mid = getattr(item, 'mid', 0)
                lines.append(f"{pid:10d}{secid:10d}{mid:10d}")

            else:
                # 기타 카테고리는 문자열 표현 사용
                lines.append(str(item))

        return '\n'.join(lines)

    def get_preview_text(self) -> str:
        """클립보드 미리보기 텍스트"""
        if not self._data:
            return ""

        count = len(self._data.items)
        mode = "Cut" if self._cut_mode else "Copy"
        return f"{mode}: {count} {self._data.category} item(s)"


# 키워드 생성 헬퍼
class KeywordFactory:
    """새 키워드 항목 생성 팩토리"""

    @staticmethod
    def create_node(nid: int, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """새 노드 생성"""
        from dataclasses import dataclass

        @dataclass
        class Node:
            nid: int
            x: float = 0.0
            y: float = 0.0
            z: float = 0.0
            tc: int = 0
            rc: int = 0

        return Node(nid=nid, x=x, y=y, z=z)

    @staticmethod
    def create_shell(eid: int, pid: int = 0, nodes: List[int] = None):
        """새 쉘 요소 생성"""
        from dataclasses import dataclass

        @dataclass
        class ShellElement:
            eid: int
            pid: int = 0
            nodes: List[int] = None

            def __post_init__(self):
                if self.nodes is None:
                    self.nodes = [0, 0, 0, 0]

        return ShellElement(eid=eid, pid=pid, nodes=nodes or [0, 0, 0, 0])

    @staticmethod
    def create_solid(eid: int, pid: int = 0, nodes: List[int] = None):
        """새 솔리드 요소 생성"""
        from dataclasses import dataclass

        @dataclass
        class SolidElement:
            eid: int
            pid: int = 0
            nodes: List[int] = None

            def __post_init__(self):
                if self.nodes is None:
                    self.nodes = [0] * 8

        return SolidElement(eid=eid, pid=pid, nodes=nodes or [0] * 8)

    @staticmethod
    def create_part(pid: int, name: str = "", secid: int = 0, mid: int = 0):
        """새 파트 생성"""
        from dataclasses import dataclass

        @dataclass
        class Part:
            pid: int
            name: str = ""
            secid: int = 0
            mid: int = 0
            eosid: int = 0
            hgid: int = 0
            grav: int = 0
            adpopt: int = 0
            tmid: int = 0

        return Part(pid=pid, name=name, secid=secid, mid=mid)


# Singleton instance
_global_clipboard: Optional[KeywordClipboard] = None


def get_clipboard() -> KeywordClipboard:
    """글로벌 클립보드 인스턴스 반환"""
    global _global_clipboard
    if _global_clipboard is None:
        _global_clipboard = KeywordClipboard()
    return _global_clipboard
