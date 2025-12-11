"""File Loader Module Registration"""

from gui.modules import ModuleRegistry
from gui.modules.file_loader import FileLoaderModule

@ModuleRegistry.register(
    module_id="file_loader",
    name="파일 로더",
    description="K-file 로드 및 미리보기",
    icon="fa5s.folder-open",
    order=-1  # 가장 먼저 표시
)
class RegisteredFileLoaderModule(FileLoaderModule):
    """등록된 File Loader 모듈"""
    pass
