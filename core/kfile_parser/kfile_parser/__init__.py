"""K-File High-Performance Parser

pybind11 기반 고속 LS-DYNA K-file 파서

Example:
    from core.kfile_parser import KFileParser

    parser = KFileParser()
    result = parser.parse("model.k")

    print(f"Nodes: {len(result.nodes)}")
    print(f"Parts: {len(result.parts)}")
    print(f"Elements: {len(result.elements)}")
"""

__version__ = '0.1.0'

try:
    # C++ 바인딩 모듈 임포트
    from ._kfile_parser import (
        KFileParser as _CppKFileParser,
        ParseResult as CppParseResult,
        Node as CppNode,
        Part as CppPart,
        Element as CppElement,
        ElementType,
    )
    _CPP_AVAILABLE = True
except ImportError as e:
    _CPP_AVAILABLE = False
    _IMPORT_ERROR = str(e)

from .wrapper import KFileParser, ParsedKFile, NodeData, PartData, ElementData

__all__ = [
    'KFileParser',
    'ParsedKFile',
    'NodeData',
    'PartData',
    'ElementData',
    'ElementType',
    'is_cpp_available',
]


def is_cpp_available() -> bool:
    """C++ 바인딩이 사용 가능한지 확인

    Returns:
        bool: C++ 모듈이 빌드되어 있으면 True
    """
    return _CPP_AVAILABLE


def get_import_error() -> str:
    """C++ 임포트 에러 메시지 반환"""
    if _CPP_AVAILABLE:
        return ""
    return _IMPORT_ERROR
