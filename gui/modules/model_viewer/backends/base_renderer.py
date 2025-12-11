"""Base Renderer Interface

모든 렌더링 백엔드의 공통 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Set, Dict, Optional
import numpy as np

from ..core.mesh_data import MeshData
from ..core.camera import Camera


class BaseRenderer(ABC):
    """렌더링 백엔드 베이스 클래스

    모든 백엔드는 이 인터페이스를 구현해야 함
    """

    def __init__(self):
        self._mesh: Optional[MeshData] = None
        self._visible_parts: Set[int] = set()
        self._part_colors: Dict[int, tuple] = {}
        self._camera: Optional[Camera] = None

        # Rendering options (CAE 기본값)
        self._show_nodes = False
        self._show_wireframe = False  # 내부 엣지까지 (비효율적)
        self._show_edges = True  # 외곽 엣지만 (CAE 기본) - Solid와 함께 쓰면 좋음
        self._show_solid = True  # CAE에서는 기본적으로 Solid 뷰
        self._background_color = (0.2, 0.2, 0.2, 1.0)

        # Cached exterior faces for solid rendering
        self._exterior_faces: Optional[Dict] = None

    @abstractmethod
    def initialize(self):
        """렌더링 초기화 (initializeGL에서 호출)"""
        pass

    @abstractmethod
    def resize(self, width: int, height: int):
        """리사이즈 (resizeGL에서 호출)"""
        pass

    @abstractmethod
    def render(self):
        """메인 렌더링 함수 (paintGL에서 호출)"""
        pass

    def set_mesh(self, mesh: MeshData):
        """메쉬 데이터 설정"""
        self._mesh = mesh
        if mesh:
            self._visible_parts = set(mesh.part_elements.keys())
            self._generate_part_colors()
            # 외곽면 추출 (Solid 렌더링 최적화)
            print(f"[Renderer] Extracting exterior faces...")
            self._exterior_faces = mesh.extract_exterior_faces()
            # 통계 출력
            if self._exterior_faces:
                total_faces = sum(len(faces) for faces in self._exterior_faces.values())
                total_elements = len(mesh.elements)
                print(f"[Renderer] Exterior faces: {total_faces} (elements: {total_elements})")
                if mesh.element_type == 'solid':
                    reduction = 100 * (1 - total_faces / (total_elements * 6))
                    print(f"[Renderer] Rendering reduction: {reduction:.1f}%")

    def set_camera(self, camera: Camera):
        """카메라 설정"""
        self._camera = camera

    def set_visible_parts(self, part_ids: Set[int]):
        """표시할 Part 설정"""
        self._visible_parts = part_ids

    def set_show_nodes(self, show: bool):
        """노드 표시 ON/OFF"""
        self._show_nodes = show

    def set_show_wireframe(self, show: bool):
        """와이어프레임 표시 ON/OFF (내부 엣지까지)"""
        self._show_wireframe = show

    def set_show_edges(self, show: bool):
        """외곽 엣지 표시 ON/OFF (외곽면 엣지만)"""
        self._show_edges = show

    def set_show_solid(self, show: bool):
        """솔리드 표시 ON/OFF"""
        self._show_solid = show

    def _generate_part_colors(self):
        """Part별 색상 생성 (CAE 전용 컬러맵)

        CAE에서 주로 사용하는 색상들:
        - 각 Part를 구분하기 쉬운 고대비 색상
        - 시각적으로 명확한 색상 팔레트
        """
        if not self._mesh:
            return

        # CAE 표준 컬러 팔레트 (구분하기 쉬운 색상)
        cae_colors = [
            (0.00, 0.45, 0.74),  # Blue
            (0.85, 0.33, 0.10),  # Orange
            (0.93, 0.69, 0.13),  # Yellow
            (0.49, 0.18, 0.56),  # Purple
            (0.47, 0.67, 0.19),  # Green
            (0.30, 0.75, 0.93),  # Cyan
            (0.64, 0.08, 0.18),  # Dark Red
            (0.90, 0.60, 0.00),  # Gold
            (0.20, 0.63, 0.17),  # Forest Green
            (0.89, 0.10, 0.11),  # Red
            (0.55, 0.34, 0.29),  # Brown
            (0.50, 0.50, 0.50),  # Gray
            (0.00, 0.60, 0.50),  # Teal
            (0.80, 0.36, 0.36),  # Indian Red
            (0.13, 0.55, 0.13),  # Dark Green
        ]

        part_ids = sorted(self._mesh.part_elements.keys())
        for i, pid in enumerate(part_ids):
            # Cycle through CAE colors
            color = cae_colors[i % len(cae_colors)]
            self._part_colors[pid] = color

    @property
    def name(self) -> str:
        """백엔드 이름"""
        return self.__class__.__name__
