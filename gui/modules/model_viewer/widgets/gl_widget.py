"""OpenGL 3D 렌더링 위젯 (Multi-Backend)

여러 렌더링 백엔드를 지원하는 통합 3D 뷰어
"""
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from OpenGL.GL import *
import numpy as np
import time
from typing import Optional, Set

from ..core.mesh_data import MeshData
from ..core.camera import Camera
from ..backends.legacy_renderer import LegacyRenderer
from ..backends.vbo_renderer import VBORenderer


class ModelGLWidget(QOpenGLWidget):
    """OpenGL 기반 3D 모델 뷰어 (Multi-Backend)

    Features:
    - 여러 렌더링 백엔드 지원
    - Legacy OpenGL (기본) - 최대 호환성
    - VBO OpenGL (향후) - GPU 가속
    - PyVista (향후) - 병렬 렌더링
    - Part별 색상
    - 와이어프레임/솔리드/노드 렌더링
    - 마우스 인터랙션
    """

    # 시그널
    statusMessage = Signal(str)
    fpsUpdate = Signal(float)
    elementSelected = Signal(int)  # 요소 선택 시그널 (element_index)

    def __init__(self, parent=None, backend='legacy'):
        """
        Args:
            parent: Parent widget
            backend: 렌더링 백엔드 ('legacy', 'vbo', 'pyvista')
        """
        super().__init__(parent)

        # 백엔드 선택
        self._backend_name = backend
        self._renderer = None
        self._create_backend(backend)

        # 카메라
        self._camera = Camera()
        if self._renderer:
            self._renderer.set_camera(self._camera)

        # 마우스
        self._last_mouse_pos: Optional[QPoint] = None
        self._is_rotating = False
        self._is_panning = False
        self._mouse_moved = False  # 드래그 vs 클릭 구분

        # FPS
        self._frame_count = 0
        self._fps_timer = 0.0

        # Scale bar
        self._show_scale_bar = True

    def _create_backend(self, backend: str):
        """백엔드 생성"""
        if backend == 'legacy':
            self._renderer = LegacyRenderer()
        elif backend == 'vbo':
            self._renderer = VBORenderer()
        elif backend == 'pyvista':
            # TODO: PyVista renderer
            self.statusMessage.emit("PyVista backend not implemented yet, using Legacy")
            self._renderer = LegacyRenderer()
        else:
            self.statusMessage.emit(f"Unknown backend '{backend}', using Legacy")
            self._renderer = LegacyRenderer()

    def set_backend(self, backend: str):
        """렌더링 백엔드 변경"""
        if backend == self._backend_name:
            return

        # 현재 상태 저장
        mesh = self._renderer._mesh if self._renderer else None
        visible_parts = self._renderer._visible_parts if self._renderer else set()
        show_nodes = self._renderer._show_nodes if self._renderer else False
        show_wireframe = self._renderer._show_wireframe if self._renderer else False
        show_edges = self._renderer._show_edges if self._renderer else True
        show_solid = self._renderer._show_solid if self._renderer else True

        # 새 백엔드 생성
        self._backend_name = backend
        self._create_backend(backend)
        self._renderer.set_camera(self._camera)

        # 상태 복원
        if mesh:
            self._renderer.set_mesh(mesh)
        self._renderer.set_visible_parts(visible_parts)
        self._renderer.set_show_nodes(show_nodes)
        self._renderer.set_show_wireframe(show_wireframe)
        self._renderer.set_show_edges(show_edges)
        self._renderer.set_show_solid(show_solid)

        # OpenGL 재초기화 필요
        self.makeCurrent()
        self._renderer.initialize()
        self.update()

        self.statusMessage.emit(f"Switched to {self._renderer.name} backend")

    def get_backend_name(self) -> str:
        """현재 백엔드 이름"""
        return self._renderer.name if self._renderer else "None"

    def set_mesh(self, mesh: MeshData):
        """메쉬 설정"""
        if self._renderer:
            self._renderer.set_mesh(mesh)
            if mesh:
                self._camera.fit_to_bounds(mesh.bounds[0], mesh.bounds[1])
        self.update()

    def set_visible_parts(self, part_ids: Set[int]):
        if self._renderer:
            self._renderer.set_visible_parts(part_ids)
        self.update()

    def set_show_nodes(self, show: bool):
        if self._renderer:
            self._renderer.set_show_nodes(show)
        self.update()

    def set_show_wireframe(self, show: bool):
        if self._renderer:
            self._renderer.set_show_wireframe(show)
        self.update()

    def set_show_edges(self, show: bool):
        if self._renderer:
            self._renderer.set_show_edges(show)
        self.update()

    def set_show_solid(self, show: bool):
        if self._renderer:
            self._renderer.set_show_solid(show)
        self.update()

    def reset_view(self):
        mesh = self._renderer._mesh if self._renderer else None
        if mesh:
            self._camera.fit_to_bounds(mesh.bounds[0], mesh.bounds[1])
        self.update()

    # ========== 6-View Presets ==========

    def view_front(self):
        """Front view"""
        self._camera.view_front()
        self.update()

    def view_back(self):
        """Back view"""
        self._camera.view_back()
        self.update()

    def view_left(self):
        """Left view"""
        self._camera.view_left()
        self.update()

    def view_right(self):
        """Right view"""
        self._camera.view_right()
        self.update()

    def view_top(self):
        """Top view"""
        self._camera.view_top()
        self.update()

    def view_bottom(self):
        """Bottom view"""
        self._camera.view_bottom()
        self.update()

    def view_isometric(self):
        """Isometric view"""
        self._camera.view_isometric()
        self.update()

    # ===== OpenGL =====

    def initializeGL(self):
        """OpenGL 초기화"""
        if self._renderer:
            self._renderer.initialize()

    def resizeGL(self, width: int, height: int):
        if self._renderer:
            self._renderer.resize(width, height)

    def paintGL(self):
        """렌더링"""
        t0 = time.time()

        if self._renderer:
            self._renderer.render()

        # Draw scale bar overlay
        if self._show_scale_bar:
            self._draw_scale_bar()

        # FPS
        self._frame_count += 1
        if time.time() - self._fps_timer > 1.0:
            self.fpsUpdate.emit(self._frame_count)
            self._frame_count = 0
            self._fps_timer = time.time()

    def _draw_scale_bar(self):
        """Draw scale bar in bottom-left corner"""
        width = self.width()
        height = self.height()

        if width <= 0 or height <= 0:
            return

        # Calculate world size visible on screen
        # Using camera distance and FOV to estimate world units per pixel
        fov_rad = np.radians(self._camera.fov)
        # Vertical field of view determines world height at camera distance
        world_height = 2.0 * self._camera.distance * np.tan(fov_rad / 2.0)
        world_per_pixel = world_height / height

        # Target scale bar length in pixels (100-150 pixels)
        target_bar_pixels = 120

        # Calculate world length for target bar
        world_length = target_bar_pixels * world_per_pixel

        # Round to nice number (1, 2, 5, 10, 20, 50, 100, ...)
        nice_length = self._round_to_nice_number(world_length)

        # Actual bar length in pixels
        bar_pixels = int(nice_length / world_per_pixel)
        bar_pixels = max(30, min(200, bar_pixels))  # Clamp to reasonable range

        # Format label
        if nice_length >= 1000:
            label = f"{nice_length/1000:.0f} m"
        elif nice_length >= 1:
            label = f"{nice_length:.0f} mm"
        else:
            label = f"{nice_length:.2f} mm"

        # Draw using QPainter overlay
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Position: bottom-left corner with margin
        margin = 15
        bar_x = margin
        bar_y = height - margin - 10

        # Draw background rectangle for visibility
        bg_width = bar_pixels + 20
        bg_height = 30
        painter.fillRect(bar_x - 5, bar_y - 20, bg_width, bg_height,
                        QColor(0, 0, 0, 120))

        # Draw scale bar line
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(bar_x, bar_y, bar_x + bar_pixels, bar_y)

        # Draw end ticks
        tick_height = 6
        painter.drawLine(bar_x, bar_y - tick_height, bar_x, bar_y + tick_height)
        painter.drawLine(bar_x + bar_pixels, bar_y - tick_height,
                        bar_x + bar_pixels, bar_y + tick_height)

        # Draw label
        font = QFont("Arial", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(bar_x, bar_y - 8, label)

        painter.end()

    def _round_to_nice_number(self, value: float) -> float:
        """Round to a nice number (1, 2, 5, 10, 20, 50, ...)"""
        if value <= 0:
            return 1.0

        # Find order of magnitude
        magnitude = 10 ** np.floor(np.log10(value))
        normalized = value / magnitude

        # Round to 1, 2, or 5
        if normalized < 1.5:
            nice = 1.0
        elif normalized < 3.5:
            nice = 2.0
        elif normalized < 7.5:
            nice = 5.0
        else:
            nice = 10.0

        return nice * magnitude

    def set_show_scale_bar(self, show: bool):
        """Enable/disable scale bar"""
        self._show_scale_bar = show
        self.update()

    # ===== 마우스 =====

    def mousePressEvent(self, event):
        self._last_mouse_pos = event.pos()
        self._mouse_moved = False  # 리셋
        if event.button() == Qt.LeftButton:
            self._is_panning = bool(event.modifiers() & Qt.ShiftModifier)
            self._is_rotating = not self._is_panning
        elif event.button() == Qt.MiddleButton:
            self._is_panning = True

    def mouseReleaseEvent(self, event):
        # 클릭 (드래그 없음) → 요소 선택
        if event.button() == Qt.LeftButton and not self._mouse_moved:
            self._handle_element_pick(event.x(), event.y())

        self._is_rotating = False
        self._is_panning = False
        self._last_mouse_pos = None
        self._mouse_moved = False

    def mouseMoveEvent(self, event):
        if not self._last_mouse_pos:
            return
        dx = event.x() - self._last_mouse_pos.x()
        dy = event.y() - self._last_mouse_pos.y()

        # 마우스 이동 감지 (클릭 vs 드래그 구분)
        if abs(dx) > 2 or abs(dy) > 2:
            self._mouse_moved = True

        if self._is_rotating:
            self._camera.rotate(dx * 0.5, dy * 0.5)
            self.update()
        elif self._is_panning:
            scale = self._camera.distance * 0.001
            self._camera.pan(dx * scale, -dy * scale)
            self.update()
        self._last_mouse_pos = event.pos()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._camera.zoom(1.1 if delta > 0 else 0.9)
        self.update()

    def _handle_element_pick(self, x: int, y: int):
        """요소 선택 처리 (클릭)"""
        if not self._renderer or not hasattr(self._renderer, 'pick_element'):
            return

        # OpenGL 컨텍스트 활성화
        self.makeCurrent()

        # 렌더러의 picking 기능 호출
        elem_idx = self._renderer.pick_element(x, y)

        # 화면 다시 그리기 (picking 렌더링 이후)
        self.update()

        # 시그널 발생
        if elem_idx is not None:
            self.elementSelected.emit(elem_idx)
            self.statusMessage.emit(f"Element {elem_idx} selected")
