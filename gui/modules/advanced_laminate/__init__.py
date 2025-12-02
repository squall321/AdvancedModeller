"""Advanced Laminate Module - 적층 고도화"""
from gui.modules import ModuleRegistry
from .module import AdvancedLaminateModule

# 모듈 등록
ModuleRegistry.register(
    module_id="advanced_laminate",
    name="적층 고도화",
    description="라미네이트 적층 구성 및 물성 자동화",
    icon="fa5s.layer-group",
    order=1
)(AdvancedLaminateModule)
