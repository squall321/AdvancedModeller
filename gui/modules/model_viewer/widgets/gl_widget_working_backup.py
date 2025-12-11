"""OpenGL 3D 렌더링 위젯 (Legacy OpenGL)

Legacy OpenGL (glBegin/glEnd) - 최대 호환성, 확실한 작동
"""
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, Signal, QPoint
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from typing import Optional, Set, Dict
import time

from ..core.mesh_data import MeshData
from ..core.camera import Camera


class ModelGLWidget(QOpenGLWidget):
    """OpenGL 기반 3D 모델 뷰어 (Legacy 방식)
    
    Features:
    - Legacy OpenGL (glBegin/glEnd) - 최대 호환성
    - Part별 색상
    - 와이어프레임/솔리드/노드 렌더링
    - 마우스 인터랙션
    """
    
    # 시그널
    statusMessage = Signal(str)
    fpsUpdate = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 데이터
        self._mesh: Optional[MeshData] = None
        self._visible_parts: Set[int] = set()
        self._part_colors: Dict[int, tuple] = {}
        
        # 카메라
        self._camera = Camera()
        
        # 마우스
        self._last_mouse_pos: Optional[QPoint] = None
        self._is_rotating = False
        self._is_panning = False
        
        # 렌더링 옵션
        self._show_nodes = False
        self._show_wireframe = True
        self._show_solid = False
        self._background_color = (0.2, 0.2, 0.2, 1.0)
        
        # FPS
        self._frame_count = 0
        self._fps_timer = 0.0
        
    def set_mesh(self, mesh: MeshData):
        """메쉬 설정"""
        self._mesh = mesh
        if mesh:
            self._visible_parts = set(mesh.part_elements.keys())
            self._generate_part_colors()
            self._camera.fit_to_bounds(mesh.bounds[0], mesh.bounds[1])
        self.update()
        
    def _generate_part_colors(self):
        """Part별 색상 생성 (HSV)"""
        if not self._mesh:
            return
        part_ids = sorted(self._mesh.part_elements.keys())
        n = len(part_ids)
        for i, pid in enumerate(part_ids):
            h = i / max(n, 1)
            s, v = 0.7, 0.9
            c = v * s
            x = c * (1 - abs((h * 6) % 2 - 1))
            m = v - c
            if h < 1/6: r, g, b = c, x, 0
            elif h < 2/6: r, g, b = x, c, 0
            elif h < 3/6: r, g, b = 0, c, x
            elif h < 4/6: r, g, b = 0, x, c
            elif h < 5/6: r, g, b = x, 0, c
            else: r, g, b = c, 0, x
            self._part_colors[pid] = (r+m, g+m, b+m)
            
    def set_visible_parts(self, part_ids: Set[int]):
        self._visible_parts = part_ids
        self.update()
        
    def set_show_nodes(self, show: bool):
        self._show_nodes = show
        self.update()
        
    def set_show_wireframe(self, show: bool):
        self._show_wireframe = show
        self.update()
        
    def set_show_solid(self, show: bool):
        self._show_solid = show
        self.update()
        
    def reset_view(self):
        if self._mesh:
            self._camera.fit_to_bounds(self._mesh.bounds[0], self._mesh.bounds[1])
        else:
            self._camera = Camera()
        self.update()
        
    # ===== OpenGL =====
    
    def initializeGL(self):
        """OpenGL 초기화"""
        print("[GL Legacy] Initializing...")
        glClearColor(*self._background_color)

        # Depth test
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        # Line/Point rendering
        glLineWidth(1.5)
        glPointSize(4.0)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        # Lighting for surface view
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Light properties
        light_pos = [1.0, 1.0, 1.0, 0.0]  # Directional light
        light_ambient = [0.3, 0.3, 0.3, 1.0]
        light_diffuse = [0.8, 0.8, 0.8, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)

        # Disable lighting by default (enable only for solid rendering)
        glDisable(GL_LIGHTING)

        print(f"[GL Legacy] OpenGL {glGetString(GL_VERSION).decode()} initialized")
        
    def resizeGL(self, width: int, height: int):
        glViewport(0, 0, width, height)
        
    def paintGL(self):
        """렌더링 (Legacy)"""
        t0 = time.time()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if not self._mesh or len(self._mesh.nodes) == 0:
            return
            
        # 투영 행렬
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width() / max(self.height(), 1)
        proj = self._camera.get_projection_matrix(aspect)
        glLoadMatrixf(proj.T.astype(np.float32))
        
        # 모델뷰 행렬
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        view = self._camera.get_view_matrix()
        glLoadMatrixf(view.T.astype(np.float32))
        
        # 그리드
        self._draw_grid()
        
        # 렌더링
        if self._show_solid:
            glEnable(GL_POLYGON_OFFSET_FILL)
            glPolygonOffset(1.0, 1.0)
            self._draw_solid()
            glDisable(GL_POLYGON_OFFSET_FILL)
            
        if self._show_wireframe:
            self._draw_wireframe()
            
        if self._show_nodes:
            self._draw_nodes()
            
        # FPS
        self._frame_count += 1
        if time.time() - self._fps_timer > 1.0:
            self.fpsUpdate.emit(self._frame_count)
            self._frame_count = 0
            self._fps_timer = time.time()
            
    def _draw_grid(self):
        """그리드 & 축"""
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        for i in range(-10, 11):
            p = i * 10.0
            glVertex3f(p, -100, 0)
            glVertex3f(p, 100, 0)
            glVertex3f(-100, p, 0)
            glVertex3f(100, p, 0)
        glEnd()
        
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(20, 0, 0)
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 20, 0)
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 20)
        glEnd()
        glLineWidth(1.5)
        
    def _draw_wireframe(self):
        """와이어프레임"""
        for pid in self._visible_parts:
            if pid not in self._mesh.part_elements:
                continue
            color = self._part_colors.get(pid, (0.7, 0.7, 0.7))
            glColor3f(*color)

            glBegin(GL_LINES)
            for elem_idx in self._mesh.part_elements[pid]:
                node_indices = self._mesh.elements[elem_idx]  # 이미 인덱스임
                n = len(node_indices)

                if n == 4:  # Shell
                    edges = [(0,1),(1,2),(2,3),(3,0)]
                elif n == 8:  # Hex
                    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
                else:
                    continue

                for i, j in edges:
                    idx1, idx2 = node_indices[i], node_indices[j]
                    p1 = self._mesh.nodes[idx1]
                    p2 = self._mesh.nodes[idx2]
                    glVertex3f(p1[0], p1[1], p1[2])
                    glVertex3f(p2[0], p2[1], p2[2])
            glEnd()
            
    def _draw_solid(self):
        """솔리드 (Surface view)"""
        glEnable(GL_LIGHTING)  # Enable lighting for surfaces
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        for pid in self._visible_parts:
            if pid not in self._mesh.part_elements:
                continue
            color = self._part_colors.get(pid, (0.7, 0.7, 0.7))
            glColor4f(color[0], color[1], color[2], 0.8)  # 좀 더 불투명하게

            glBegin(GL_QUADS)
            for elem_idx in self._mesh.part_elements[pid]:
                node_indices = self._mesh.elements[elem_idx]
                n = len(node_indices)

                if n == 4:  # Shell - 1 face
                    for i in range(4):
                        idx = node_indices[i]
                        p = self._mesh.nodes[idx]
                        glVertex3f(p[0], p[1], p[2])

                elif n == 8:  # Hex - 6 faces
                    faces = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[0,3,7,4],[1,2,6,5]]
                    for face in faces:
                        for i in face:
                            idx = node_indices[i]
                            p = self._mesh.nodes[idx]
                            glVertex3f(p[0], p[1], p[2])
            glEnd()
        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)  # Disable after solid rendering
        
    def _draw_nodes(self):
        """노드 포인트"""
        glColor3f(1, 1, 0)  # 노란색
        glBegin(GL_POINTS)

        # 표시할 part의 모든 노드 수집
        node_indices = set()
        for pid in self._visible_parts:
            if pid in self._mesh.part_elements:
                for elem_idx in self._mesh.part_elements[pid]:
                    node_indices.update(self._mesh.elements[elem_idx])

        # 노드 그리기
        for idx in node_indices:
            p = self._mesh.nodes[idx]
            glVertex3f(p[0], p[1], p[2])
        glEnd()
        
    # ===== 마우스 =====
    
    def mousePressEvent(self, event):
        self._last_mouse_pos = event.pos()
        if event.button() == Qt.LeftButton:
            self._is_panning = bool(event.modifiers() & Qt.ShiftModifier)
            self._is_rotating = not self._is_panning
        elif event.button() == Qt.MiddleButton:
            self._is_panning = True
            
    def mouseReleaseEvent(self, event):
        self._is_rotating = False
        self._is_panning = False
        self._last_mouse_pos = None
        
    def mouseMoveEvent(self, event):
        if not self._last_mouse_pos:
            return
        dx = event.x() - self._last_mouse_pos.x()
        dy = event.y() - self._last_mouse_pos.y()
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
