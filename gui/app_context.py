"""App context - shared state between modules"""
from dataclasses import dataclass, field
from typing import Optional
from core import ConfigManager, MaterialDatabase, KFileParser


@dataclass
class AppContext:
    """
    모듈들이 공유하는 데이터 및 서비스

    사용 예시:
        ctx = AppContext()
        ctx.load_materials("/path/to/MaterialSource.txt")
        names = ctx.material_db.get_names()
    """

    # 서비스
    config: ConfigManager = field(default_factory=ConfigManager)
    material_db: MaterialDatabase = field(default_factory=MaterialDatabase)
    k_parser: KFileParser = field(default_factory=KFileParser)

    # 공유 상태
    current_k_file: str = ""
    current_material_file: str = ""
    current_project_path: str = ""

    def load_materials(self, path: str) -> bool:
        """Material DB 로드"""
        if self.material_db.load(path):
            self.current_material_file = path
            return True
        return False

    def load_k_file(self, path: str) -> bool:
        """K파일 파싱"""
        if self.k_parser.parse(path):
            self.current_k_file = path
            return True
        return False

    def get_part_ids(self):
        """파싱된 Part ID 목록"""
        return self.k_parser.get_part_ids() if self.k_parser else []

    def get_material_names(self):
        """Material 이름 목록"""
        return self.material_db.get_names() if self.material_db else []
