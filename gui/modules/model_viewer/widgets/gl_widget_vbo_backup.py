"""OpenGL 3D 렌더링 위젯 (VBO 최적화)

VBO (Vertex Buffer Object)를 사용한 초고속 렌더링
- 10-100배 속도 향상
- Part별 색상 지원
- Solid 렌더링 지원
"""
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QSurfaceFormat
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from typing import Optional, Set, Dict
import ctypes

from ..core.mesh_data import MeshData
from ..core.camera import Camera


class ModelGLWidgetVBO(QOpenGLWidget):
    """OpenGL 기반 3D 모델 뷰어 (VBO 최적화)

    Features:
    - VBO/VAO for 10-100x performance
    - Part별 색상
    - Solid/Wireframe 렌더링
    - 초고속 대용량 모델 지원
    """

    # 시그널
    statusMessage = Signal(str)  # 상태 메시지
    fpsUpdate = Signal(float)  # FPS 업데이트

    def __init__(self, parent=None):
        super().__init__(parent)

        # 데이터
        self._mesh: Optional[MeshData] = None
        self._visible_parts: Set[int] = set()
        self._part_colors: Dict[int, tuple] = {}  # Part별 색상

        # 카메라
        self._camera = Camera()

        # 마우스 상태
        self._last_mouse_pos: Optional[QPoint] = None
        self._is_rotating = False
        self._is_panning = False

        # 렌더링 옵션
        self._show_nodes = False
        self._show_wireframe = True
        self._show_solid = False
        self._background_color = (0.2, 0.2, 0.2, 1.0)

        # VBO/VAO IDs
        self._wireframe_vao = None
        self._wireframe_vbo = None
        self._wireframe_vertex_count = 0

        self._solid_vao = None
        self._solid_vbo = None
        self._solid_vertex_count = 0

        self._node_vao = None
        self._node_vbo = None
        self._node_vertex_count = 0

        # Shader programs
        self._wireframe_shader = None
        self._solid_shader = None
        self._node_shader = None
        self._gl_initialized = False

        # 성능 카운터
        self._frame_count = 0
        self._fps_timer = 0.0
        self._last_fps = 0.0

    def set_mesh(self, mesh: MeshData):
        """메쉬 데이터 설정"""
        self._mesh = mesh

        if mesh:
            # 모든 Part 표시
            self._visible_parts = set(mesh.part_elements.keys())

            # Part별 랜덤 색상 생성
            self._generate_part_colors()

            # 카메라 맞춤
            self._camera.fit_to_bounds(mesh.bounds[0], mesh.bounds[1])

            # VBO 재생성 (다음 렌더링 시)
            self._wireframe_vao = None
            self._solid_vao = None
            self._node_vao = None

        self.update()
        self.statusMessage.emit(f"Loaded: {len(mesh.nodes) if mesh else 0} nodes, "
                                f"{len(mesh.elements) if mesh else 0} elements")

    def _generate_part_colors(self):
        """Part별 랜덤 색상 생성"""
        if not self._mesh:
            return

        np.random.seed(42)  # 재현 가능한 색상
        for pid in self._mesh.part_elements.keys():
            # HSV 색상 공간에서 랜덤 생성 (밝고 채도 높은 색상)
            h = np.random.rand()
            s = 0.6 + 0.4 * np.random.rand()  # 0.6-1.0
            v = 0.7 + 0.3 * np.random.rand()  # 0.7-1.0

            # HSV to RGB
            c = v * s
            x = c * (1 - abs((h * 6) % 2 - 1))
            m = v - c

            if h < 1/6:
                r, g, b = c, x, 0
            elif h < 2/6:
                r, g, b = x, c, 0
            elif h < 3/6:
                r, g, b = 0, c, x
            elif h < 4/6:
                r, g, b = 0, x, c
            elif h < 5/6:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x

            self._part_colors[pid] = (r + m, g + m, b + m)

    def set_visible_parts(self, part_ids: Set[int]):
        """표시할 Part 설정"""
        self._visible_parts = part_ids
        # VBO 재생성 필요
        self._wireframe_vao = None
        self._solid_vao = None
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
        """뷰 리셋"""
        if self._mesh:
            self._camera.fit_to_bounds(self._mesh.bounds[0], self._mesh.bounds[1])
        else:
            self._camera = Camera()
        self.update()

    # =========================================================================
    # OpenGL 초기화
    # =========================================================================

    def initializeGL(self):
        """OpenGL 초기화"""
        # 배경색
        glClearColor(*self._background_color)

        # Depth 테스트
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        # 라인 두께
        glLineWidth(1.5)

        # 포인트 크기
        glPointSize(4.0)

        # Shader 컴파일
        self._compile_shaders()

        self._gl_initialized = True

        print("[GL VBO] OpenGL initialized")
        print(f"[GL VBO] Vendor: {glGetString(GL_VENDOR).decode()}")
        print(f"[GL VBO] Renderer: {glGetString(GL_RENDERER).decode()}")
        print(f"[GL VBO] Version: {glGetString(GL_VERSION).decode()}")

    def _compile_shaders(self):
        """Shader 컴파일"""
        # Vertex Shader (공통)
        vertex_shader_code = """
        #version 330 core
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec3 color;

        uniform mat4 projection;
        uniform mat4 view;

        out vec3 fragColor;

        void main() {
            gl_Position = projection * view * vec4(position, 1.0);
            fragColor = color;
        }
        """

        # Fragment Shader (공통)
        fragment_shader_code = """
        #version 330 core
        in vec3 fragColor;
        out vec4 outColor;

        void main() {
            outColor = vec4(fragColor, 1.0);
        }
        """

        # Compile
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_shader_code)
        glCompileShader(vertex_shader)

        if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(vertex_shader).decode()
            raise RuntimeError(f"Vertex shader compile error: {error}")

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_shader_code)
        glCompileShader(fragment_shader)

        if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(fragment_shader).decode()
            raise RuntimeError(f"Fragment shader compile error: {error}")

        # Link
        self._wireframe_shader = glCreateProgram()
        glAttachShader(self._wireframe_shader, vertex_shader)
        glAttachShader(self._wireframe_shader, fragment_shader)
        glLinkProgram(self._wireframe_shader)

        if not glGetProgramiv(self._wireframe_shader, GL_LINK_STATUS):
            error = glGetProgramInfoLog(self._wireframe_shader).decode()
            raise RuntimeError(f"Shader link error: {error}")

        # 동일한 shader를 solid/node에도 사용
        self._solid_shader = self._wireframe_shader
        self._node_shader = self._wireframe_shader

        # Cleanup
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        print("[GL VBO] Shaders compiled successfully")

    def resizeGL(self, width: int, height: int):
        """윈도우 크기 변경"""
        glViewport(0, 0, width, height)

    # =========================================================================
    # 렌더링
    # =========================================================================

    def paintGL(self):
        """렌더링 (VBO 사용)"""
        import time
        t0 = time.time()

        # 화면 클리어
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # OpenGL 초기화 확인
        if not self._gl_initialized:
            print("[GL VBO] Waiting for OpenGL initialization...")
            return

        if not self._mesh or len(self._mesh.nodes) == 0:
            return

        # VBO 생성 (필요시)
        if self._wireframe_vao is None and self._show_wireframe:
            self._create_wireframe_vbo()

        if self._solid_vao is None and self._show_solid:
            self._create_solid_vbo()

        if self._node_vao is None and self._show_nodes:
            self._create_node_vbo()

        # 행렬 설정
        aspect = self.width() / max(self.height(), 1)
        proj_matrix = self._camera.get_projection_matrix(aspect)
        view_matrix = self._camera.get_view_matrix()

        # Shader 활성화
        glUseProgram(self._wireframe_shader)

        # Uniform 설정
        proj_loc = glGetUniformLocation(self._wireframe_shader, "projection")
        view_loc = glGetUniformLocation(self._wireframe_shader, "view")
        glUniformMatrix4fv(proj_loc, 1, GL_FALSE, proj_matrix.T.astype(np.float32))
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, view_matrix.T.astype(np.float32))

        # 그리드 그리기
        self._draw_grid_legacy()

        # Solid 렌더링
        if self._show_solid and self._solid_vao:
            glEnable(GL_POLYGON_OFFSET_FILL)
            glPolygonOffset(1.0, 1.0)
            glBindVertexArray(self._solid_vao)
            glDrawArrays(GL_TRIANGLES, 0, self._solid_vertex_count)
            glBindVertexArray(0)
            glDisable(GL_POLYGON_OFFSET_FILL)

        # Wireframe 렌더링
        if self._show_wireframe and self._wireframe_vao:
            glBindVertexArray(self._wireframe_vao)
            glDrawArrays(GL_LINES, 0, self._wireframe_vertex_count)
            glBindVertexArray(0)

        # Node 렌더링
        if self._show_nodes and self._node_vao:
            glBindVertexArray(self._node_vao)
            glDrawArrays(GL_POINTS, 0, self._node_vertex_count)
            glBindVertexArray(0)

        glUseProgram(0)

        # FPS 계산
        t1 = time.time()
        frame_time = t1 - t0
        self._frame_count += 1
        self._fps_timer += frame_time

        if self._fps_timer >= 1.0:
            fps = self._frame_count / self._fps_timer
            self._last_fps = fps
            self.fpsUpdate.emit(fps)
            self._frame_count = 0
            self._fps_timer = 0.0

    def _create_wireframe_vbo(self):
        """Wireframe VBO 생성"""
        if not self._mesh or not self._visible_parts:
            return

        print("[GL VBO] Creating wireframe VBO...")
        t0 = __import__('time').time()

        # 표시할 요소
        visible_elem_indices = self._mesh.get_visible_elements(self._visible_parts)
        if len(visible_elem_indices) == 0:
            return

        nodes = self._mesh.nodes
        elements = self._mesh.elements[visible_elem_indices]

        # Part ID 배열 생성
        part_ids = np.zeros(len(elements), dtype=np.int32)
        idx = 0
        for pid, elem_indices in self._mesh.part_elements.items():
            if pid in self._visible_parts:
                mask = np.isin(visible_elem_indices, elem_indices)
                part_ids[mask] = pid

        # VBO 데이터 생성 (position + color)
        if self._mesh.element_type == 'shell':
            # Shell: 4 edges per element, 2 vertices per edge = 8 vertices
            vertex_count = len(elements) * 8
            vbo_data = np.empty((vertex_count, 6), dtype=np.float32)  # [x,y,z, r,g,b]

            vidx = 0
            for i, elem in enumerate(elements):
                pid = part_ids[i]
                color = self._part_colors.get(pid, (0.8, 0.8, 0.8))

                n1, n2, n3, n4 = elem
                edges = [(n1, n2), (n2, n3), (n3, n4), (n4, n1)]

                for ni, nj in edges:
                    vbo_data[vidx] = [*nodes[ni], *color]
                    vbo_data[vidx + 1] = [*nodes[nj], *color]
                    vidx += 2

        else:  # solid
            # Solid: 12 edges per element, 2 vertices per edge = 24 vertices
            vertex_count = len(elements) * 24
            vbo_data = np.empty((vertex_count, 6), dtype=np.float32)

            vidx = 0
            for i, elem in enumerate(elements):
                pid = part_ids[i]
                color = self._part_colors.get(pid, (0.8, 0.8, 0.8))

                n1, n2, n3, n4, n5, n6, n7, n8 = elem
                edges = [
                    (n1, n2), (n2, n3), (n3, n4), (n4, n1),  # 아래
                    (n5, n6), (n6, n7), (n7, n8), (n8, n5),  # 위
                    (n1, n5), (n2, n6), (n3, n7), (n4, n8),  # 수직
                ]

                for ni, nj in edges:
                    vbo_data[vidx] = [*nodes[ni], *color]
                    vbo_data[vidx + 1] = [*nodes[nj], *color]
                    vidx += 2

        # VAO/VBO 생성
        self._wireframe_vao = glGenVertexArrays(1)
        self._wireframe_vbo = glGenBuffers(1)

        glBindVertexArray(self._wireframe_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._wireframe_vbo)
        glBufferData(GL_ARRAY_BUFFER, vbo_data.nbytes, vbo_data, GL_STATIC_DRAW)

        # Vertex attributes
        stride = 6 * 4  # 6 floats * 4 bytes
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))  # position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))  # color
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self._wireframe_vertex_count = vertex_count

        t1 = __import__('time').time()
        print(f"[GL VBO] Wireframe VBO created: {vertex_count:,} vertices, "
              f"{vbo_data.nbytes / 1024 / 1024:.2f} MB, {(t1-t0)*1000:.1f} ms")

    def _create_solid_vbo(self):
        """Solid 면 VBO 생성"""
        if not self._mesh or not self._visible_parts:
            return

        print("[GL VBO] Creating solid VBO...")
        t0 = __import__('time').time()

        visible_elem_indices = self._mesh.get_visible_elements(self._visible_parts)
        if len(visible_elem_indices) == 0:
            return

        nodes = self._mesh.nodes
        elements = self._mesh.elements[visible_elem_indices]

        # Part ID 배열
        part_ids = np.zeros(len(elements), dtype=np.int32)
        idx = 0
        for pid, elem_indices in self._mesh.part_elements.items():
            if pid in self._visible_parts:
                mask = np.isin(visible_elem_indices, elem_indices)
                part_ids[mask] = pid

        # Solid 면 삼각형 생성
        if self._mesh.element_type == 'shell':
            # Shell: 2 triangles per element = 6 vertices
            vertex_count = len(elements) * 6
            vbo_data = np.empty((vertex_count, 6), dtype=np.float32)

            vidx = 0
            for i, elem in enumerate(elements):
                pid = part_ids[i]
                color = self._part_colors.get(pid, (0.6, 0.6, 0.6))

                n1, n2, n3, n4 = elem
                # Triangle 1: n1-n2-n3
                vbo_data[vidx] = [*nodes[n1], *color]
                vbo_data[vidx + 1] = [*nodes[n2], *color]
                vbo_data[vidx + 2] = [*nodes[n3], *color]
                # Triangle 2: n1-n3-n4
                vbo_data[vidx + 3] = [*nodes[n1], *color]
                vbo_data[vidx + 4] = [*nodes[n3], *color]
                vbo_data[vidx + 5] = [*nodes[n4], *color]
                vidx += 6

        else:  # solid
            # Solid hex: 6 faces, 2 triangles per face = 36 vertices
            vertex_count = len(elements) * 36
            vbo_data = np.empty((vertex_count, 6), dtype=np.float32)

            vidx = 0
            for i, elem in enumerate(elements):
                pid = part_ids[i]
                color = self._part_colors.get(pid, (0.6, 0.6, 0.6))

                n1, n2, n3, n4, n5, n6, n7, n8 = elem

                # 6 faces (각 face는 2 triangles)
                faces = [
                    (n1, n2, n3, n4),  # 아래
                    (n5, n6, n7, n8),  # 위
                    (n1, n2, n6, n5),  # 앞
                    (n4, n3, n7, n8),  # 뒤
                    (n1, n4, n8, n5),  # 좌
                    (n2, n3, n7, n6),  # 우
                ]

                for f1, f2, f3, f4 in faces:
                    # Triangle 1
                    vbo_data[vidx] = [*nodes[f1], *color]
                    vbo_data[vidx + 1] = [*nodes[f2], *color]
                    vbo_data[vidx + 2] = [*nodes[f3], *color]
                    # Triangle 2
                    vbo_data[vidx + 3] = [*nodes[f1], *color]
                    vbo_data[vidx + 4] = [*nodes[f3], *color]
                    vbo_data[vidx + 5] = [*nodes[f4], *color]
                    vidx += 6

        # VAO/VBO
        self._solid_vao = glGenVertexArrays(1)
        self._solid_vbo = glGenBuffers(1)

        glBindVertexArray(self._solid_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._solid_vbo)
        glBufferData(GL_ARRAY_BUFFER, vbo_data.nbytes, vbo_data, GL_STATIC_DRAW)

        stride = 6 * 4
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self._solid_vertex_count = vertex_count

        t1 = __import__('time').time()
        print(f"[GL VBO] Solid VBO created: {vertex_count:,} vertices, "
              f"{vbo_data.nbytes / 1024 / 1024:.2f} MB, {(t1-t0)*1000:.1f} ms")

    def _create_node_vbo(self):
        """Node 점 VBO 생성"""
        if not self._mesh or not self._visible_parts:
            return

        visible_elem_indices = self._mesh.get_visible_elements(self._visible_parts)
        if len(visible_elem_indices) == 0:
            return

        nodes = self._mesh.nodes
        elements = self._mesh.elements[visible_elem_indices]

        # 사용된 노드만 추출
        node_indices = np.unique(elements.flatten())
        vertex_count = len(node_indices)

        # VBO 데이터 (position + color)
        vbo_data = np.empty((vertex_count, 6), dtype=np.float32)
        color = (1.0, 1.0, 0.0)  # 노란색

        for i, nidx in enumerate(node_indices):
            vbo_data[i] = [*nodes[nidx], *color]

        # VAO/VBO
        self._node_vao = glGenVertexArrays(1)
        self._node_vbo = glGenBuffers(1)

        glBindVertexArray(self._node_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._node_vbo)
        glBufferData(GL_ARRAY_BUFFER, vbo_data.nbytes, vbo_data, GL_STATIC_DRAW)

        stride = 6 * 4
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self._node_vertex_count = vertex_count

    def _draw_grid_legacy(self):
        """그리드 그리기 (Legacy - 나중에 VBO로 변환 가능)"""
        glUseProgram(0)  # Fixed pipeline

        glMatrixMode(GL_PROJECTION)
        aspect = self.width() / max(self.height(), 1)
        proj = self._camera.get_projection_matrix(aspect)
        glLoadMatrixf(proj.T)

        glMatrixMode(GL_MODELVIEW)
        view = self._camera.get_view_matrix()
        glLoadMatrixf(view.T)

        # 그리드
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        grid_size = 10
        grid_spacing = 10.0
        for i in range(-grid_size, grid_size + 1):
            pos = i * grid_spacing
            glVertex3f(pos, -grid_size * grid_spacing, 0)
            glVertex3f(pos, grid_size * grid_spacing, 0)
            glVertex3f(-grid_size * grid_spacing, pos, 0)
            glVertex3f(grid_size * grid_spacing, pos, 0)
        glEnd()

        # 축
        glBegin(GL_LINES)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(20, 0, 0)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 20, 0)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 20)
        glEnd()

    # =========================================================================
    # 마우스 인터랙션 (gl_widget.py와 동일)
    # =========================================================================

    def mousePressEvent(self, event):
        self._last_mouse_pos = event.pos()
        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ShiftModifier:
                self._is_panning = True
            else:
                self._is_rotating = True
        elif event.button() == Qt.MiddleButton:
            self._is_panning = True

    def mouseReleaseEvent(self, event):
        self._is_rotating = False
        self._is_panning = False
        self._last_mouse_pos = None

    def mouseMoveEvent(self, event):
        if not self._last_mouse_pos:
            return

        delta = event.pos() - self._last_mouse_pos
        self._last_mouse_pos = event.pos()

        if self._is_rotating:
            sensitivity = 0.5
            self._camera.rotate(delta.x() * sensitivity, -delta.y() * sensitivity)
            self.update()
        elif self._is_panning:
            sensitivity = 0.01
            self._camera.pan(delta.x() * sensitivity, -delta.y() * sensitivity)
            self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        self._camera.zoom(zoom_factor)
        self.update()
