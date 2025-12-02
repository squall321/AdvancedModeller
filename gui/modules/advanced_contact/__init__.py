"""Advanced Contact Module - 접촉 고도화"""
from gui.modules import ModuleRegistry
from .module import AdvancedContactModule

# 모듈 등록 (메소드 목록 포함)
ModuleRegistry.register(
    module_id="advanced_contact",
    name="접촉 고도화",
    description="Contact 정의 자동화 및 최적화",
    icon="fa5s.handshake",
    order=2,
    methods=[
        {'id': 'remove_duplicate_tied', 'name': '중복 Tied 제거', 'icon': 'fa5s.unlink'},
        # 향후 추가 예정:
        # {'id': 'auto_contact_generation', 'name': 'Auto Contact 생성', 'icon': 'fa5s.magic'},
        # {'id': 'contact_optimization', 'name': 'Contact 최적화', 'icon': 'fa5s.sliders-h'},
    ]
)(AdvancedContactModule)
