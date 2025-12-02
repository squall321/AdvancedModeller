"""Contact methods registry"""
from typing import Dict, Type, List
from .base import BaseContactMethod
from .remove_duplicate_tied import RemoveDuplicateTiedMethod

# 메소드 등록
CONTACT_METHODS: Dict[str, Type[BaseContactMethod]] = {
    "remove_duplicate_tied": RemoveDuplicateTiedMethod,
    # 향후 추가:
    # "auto_contact_generation": AutoContactGenerationMethod,
    # "contact_optimization": ContactOptimizationMethod,
}


def get_method_list() -> List[tuple]:
    """(method_id, method_name) 리스트 반환"""
    result = []
    for method_id, method_cls in CONTACT_METHODS.items():
        # Create temp instance to get name
        temp = type(method_cls.__name__, (object,), {
            'method_id': property(lambda s, mid=method_id: mid),
            'method_name': property(lambda s, cls=method_cls: cls.method_name.fget(None))
        })
        result.append((method_id, method_cls.method_name.fget(None)))
    return result


def get_method_class(method_id: str) -> Type[BaseContactMethod]:
    """메소드 클래스 반환"""
    return CONTACT_METHODS.get(method_id)
