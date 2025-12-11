"""OpenGL 3D 렌더링 위젯

초고속 와이어프레임 렌더링에 집중
"""
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from typing import Optional, Set

from ..core.mesh_data import MeshData
from ..core.camera import Camera


class ModelGLWidget(QOpenGLWidget):
    """OpenGL 기반 3D 모델 뷰어

    빠른 와이어프레임 렌더링
    """

    # 시그널
    statusMessage = Signal(str)  # 상태 메시지

    def __init__(self, parent=None):
        # OpenGL 포맷 설정 (Legacy 함수 사용을 위해 Compatibility Profile)
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)  # OpenGL 2.1 (Legacy 지원)
        fmt.setProfile(QSurfaceFormat.CompatibilityProfile)
        fmt.setDepthBufferSize(24)
        fmt.setSamples(4)  # MSAA (안티에일리어싱)
        QSurfaceFormat.setDefaultFormat(fmt)

        super().__init__(parent)

        # 데이터
        self._mesh: Optional[MeshData] = None
        self._visible_parts: Set[int] = set()

        # 카메라
        self._camera = Camera()

        # 마우스 상태
        self._last_mouse_pos: Optional[QPoint] = None
        self._is_rotating = False
        self._is_panning = False

        # 렌더링 옵션
        self._show_nodes = False
        self._show_wireframe = True
        self._background_color = (0.2, 0.2, 0.2, 1.0)

        # 성능 카운터
        self._frame_count = 0

    def set_mesh(self, mesh: MeshData):
        """메쉬 데이터 설정"""
        self._mesh = mesh

        # 모든 Part 표시
        if mesh:
            self._visible_parts = set(mesh.part_elements.keys())
            # 카메라를 모델에 맞춤
            self._camera.fit_to_bounds(mesh.bounds[0], mesh.bounds[1])

        self.update()
        self.statusMessage.emit(f"Loaded: {len(mesh.nodes) if mesh else 0} nodes, "
                                f"{len(mesh.elements) if mesh else 0} elements")

    def set_visible_parts(self, part_ids: Set[int]):
        """표시할 Part 설정"""
        self._visible_parts = part_ids
        self.update()

    def set_show_nodes(self, show: bool):
        """노드 표시 ON/OFF"""
        self._show_nodes = show
        self.update()

    def set_show_wireframe(self, show: bool):
        """와이어프레임 표시 ON/OFF"""
        self._show_wireframe = show
        self.update()

    # =========================================================================
    # OpenGL 초기화 및 렌더링
    # =========================================================================

    def initializeGL(self):
        """OpenGL 초기화"""
        # 배경색
        glClearColor(*self._background_color)

        # Depth 테스트
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        # 라인 안티에일리어싱
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        # 라인 두께
        glLineWidth(1.0)

        # 포인트 크기
        glPointSize(3.0)

        print("[GL] OpenGL initialized")
        print(f"[GL] Vendor: {glGetString(GL_VENDOR).decode()}")
        print(f"[GL] Renderer: {glGetString(GL_RENDERER).decode()}")
        print(f"[GL] Version: {glGetString(GL_VERSION).decode()}")

    def resizeGL(self, width: int, height: int):
        """윈도우 크기 변경"""
        glViewport(0, 0, width, height)

    def paintGL(self):
        """렌더링"""
        # 화면 클리어
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if not self._mesh or len(self._mesh.nodes) == 0:
            return

        # 행렬 설정
        aspect = self.width() / max(self.height(), 1)
        proj_matrix = self._camera.get_projection_matrix(aspect)
        view_matrix = self._camera.get_view_matrix()

        # Legacy OpenGL (호환성 및 속도)
        glMatrixMode(GL_PROJECTION)
        glLoadMatrixf(proj_matrix.T)

        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(view_matrix.T)

        # 그리드 그리기 (참고용)
        self._draw_grid()

        # 메쉬 그리기
        if self._show_wireframe:
            self._draw_wireframe()

        if self._show_nodes:
            self._draw_nodes()

        self._frame_count += 1

    def _draw_grid(self):
        """바닥 그리드 그리기"""
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)

        grid_size = 10
        grid_spacing = 10.0

        for i in range(-grid_size, grid_size + 1):
            pos = i * grid_spacing
            # X축 평행선
            glVertex3f(pos, -grid_size * grid_spacing, 0)
            glVertex3f(pos, grid_size * grid_spacing, 0)
            # Y축 평행선
            glVertex3f(-grid_size * grid_spacing, pos, 0)
            glVertex3f(grid_size * grid_spacing, pos, 0)

        glEnd()

        # 축 표시
        glBegin(GL_LINES)
        # X축 (빨강)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(20, 0, 0)
        # Y축 (초록)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 20, 0)
        # Z축 (파랑)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 20)
        glEnd()

    def _draw_wireframe(self):
        """와이어프레임 그리기 (초고속)"""
        if not self._visible_parts:
            return

        # 표시할 요소 인덱스
        visible_elem_indices = self._mesh.get_visible_elements(self._visible_parts)
        if len(visible_elem_indices) == 0:
            return

        # 요소별 색상 (Part별로 다르게)
        glColor3f(0.8, 0.8, 0.8)

        nodes = self._mesh.nodes
        elements = self._mesh.elements[visible_elem_indices]

        # 라인 그리기
        if self._mesh.element_type == 'shell':
            # Shell: 4개 노드 -> 4개 라인
            glBegin(GL_LINES)
            for elem in elements:
                n1, n2, n3, n4 = elem
                # 4개 모서리
                for i, j in [(n1, n2), (n2, n3), (n3, n4), (n4, n1)]:
                    glVertex3fv(nodes[i])
                    glVertex3fv(nodes[j])
            glEnd()

        else:  # solid
            # Solid: 8개 노드 -> 12개 라인
            glBegin(GL_LINES)
            for elem in elements:
                n1, n2, n3, n4, n5, n6, n7, n8 = elem
                # 12개 모서리
                edges = [
                    (n1, n2), (n2, n3), (n3, n4), (n4, n1),  # 아래면
                    (n5, n6), (n6, n7), (n7, n8), (n8, n5),  # 위면
                    (n1, n5), (n2, n6), (n3, n7), (n4, n8),  # 수직
                ]
                for i, j in edges:
                    glVertex3fv(nodes[i])
                    glVertex3fv(nodes[j])
            glEnd()

    def _draw_nodes(self):
        """노드 점 그리기"""
        if not self._visible_parts:
            return

        glColor3f(1.0, 1.0, 0.0)  # 노란색
        glBegin(GL_POINTS)

        nodes = self._mesh.nodes
        # 표시할 요소의 노드만
        visible_elem_indices = self._mesh.get_visible_elements(self._visible_parts)
        if len(visible_elem_indices) > 0:
            elements = self._mesh.elements[visible_elem_indices]
            # 중복 제거를 위해 set 사용
            node_indices = set(elements.flatten())
            for idx in node_indices:
                glVertex3fv(nodes[idx])

        glEnd()

    # =========================================================================
    # 마우스 이벤트
    # =========================================================================

    def mousePressEvent(self, event):
        """마우스 버튼 눌림"""
        self._last_mouse_pos = event.pos()

        if event.button() == Qt.LeftButton:
            self._is_rotating = True
        elif event.button() == Qt.MiddleButton or \
             (event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier):
            self._is_panning = True

    def mouseReleaseEvent(self, event):
        """마우스 버튼 떼짐"""
        self._is_rotating = False
        self._is_panning = False
        self._last_mouse_pos = None

    def mouseMoveEvent(self, event):
        """마우스 이동"""
        if not self._last_mouse_pos:
            return

        current_pos = event.pos()
        dx = current_pos.x() - self._last_mouse_pos.x()
        dy = current_pos.y() - self._last_mouse_pos.y()

        if self._is_rotating:
            # 회전
            sensitivity = 0.5
            self._camera.rotate(dx * sensitivity, -dy * sensitivity)
            self.update()

        elif self._is_panning:
            # 팬
            self._camera.pan(-dx, dy)
            self.update()

        self._last_mouse_pos = current_pos

    def wheelEvent(self, event):
        """마우스 휠 (줌)"""
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9

        self._camera.zoom(zoom_factor)
        self.update()

    # =========================================================================
    # 유틸리티
    # =========================================================================

    def reset_view(self):
        """뷰 리셋"""
        if self._mesh:
            self._camera.fit_to_bounds(self._mesh.bounds[0], self._mesh.bounds[1])
            self.update()
