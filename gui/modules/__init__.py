"""Module registry for auto-registration"""
from dataclasses import dataclass, field
from typing import Dict, Type, List, Optional


@dataclass
class MethodInfo:
    """메소드 메타데이터 (모듈 내 하위 항목)"""
    method_id: str
    name: str
    icon: str = "fa5s.cog"


@dataclass
class ModuleInfo:
    """모듈 메타데이터"""
    module_id: str
    name: str
    description: str
    icon: str              # qtawesome 아이콘명 (예: 'fa5s.layer-group')
    module_class: Type     # BaseModule 서브클래스
    order: int = 0         # 홈 화면/사이드바 정렬 순서
    methods: List[MethodInfo] = field(default_factory=list)  # 하위 메소드 목록

    @property
    def has_methods(self) -> bool:
        """메소드 목록이 있는지 확인"""
        return len(self.methods) > 0


class ModuleRegistry:
    """모듈 자동 등록 및 관리"""
    _modules: Dict[str, ModuleInfo] = {}

    @classmethod
    def register(cls, module_id: str, name: str, description: str,
                 icon: str, order: int = 0, methods: List[dict] = None):
        """
        데코레이터로 모듈 등록

        사용 예시:
        @ModuleRegistry.register(
            module_id="advanced_contact",
            name="접촉 고도화",
            description="Contact 정의 자동화",
            icon="fa5s.handshake",
            order=2,
            methods=[
                {'id': 'remove_duplicate_tied', 'name': '중복 Tied 제거'},
                {'id': 'auto_contact', 'name': 'Auto Contact'},
            ]
        )
        class AdvancedContactModule(BaseModule):
            ...
        """
        method_list = []
        if methods:
            for m in methods:
                method_list.append(MethodInfo(
                    method_id=m.get('id', ''),
                    name=m.get('name', ''),
                    icon=m.get('icon', 'fa5s.cog')
                ))

        def decorator(module_class):
            cls._modules[module_id] = ModuleInfo(
                module_id=module_id,
                name=name,
                description=description,
                icon=icon,
                module_class=module_class,
                order=order,
                methods=method_list
            )
            return module_class
        return decorator

    @classmethod
    def get_all(cls) -> List[ModuleInfo]:
        """정렬된 모듈 목록 반환"""
        return sorted(cls._modules.values(), key=lambda m: m.order)

    @classmethod
    def get(cls, module_id: str) -> Optional[ModuleInfo]:
        """모듈 ID로 조회"""
        return cls._modules.get(module_id)

    @classmethod
    def get_ids(cls) -> List[str]:
        """등록된 모듈 ID 목록"""
        return list(cls._modules.keys())


def load_modules():
    """모든 모듈 임포트 (등록 트리거)"""
    from . import file_loader  # 첫 번째 모듈
    from . import advanced_laminate
    from . import advanced_contact
    from . import keyword_manager
    from . import model_viewer
    from . import adjacent_parts_viewer
