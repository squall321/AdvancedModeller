"""VBO Renderer - GPU 가속 렌더링

Vertex Buffer Object (VBO)를 사용한 고성능 렌더링
- GPU 메모리에 메쉬 데이터 캐싱
- Immediate mode (glBegin/glEnd) 대비 10-100배 속도 향상
- 대용량 모델 (100만+ 요소) 실시간 렌더링
"""
from typing import Optional
from OpenGL.GL import *
from OpenGL.arrays import vbo
import numpy as np
import ctypes

from .base_renderer import BaseRenderer


class VBORenderer(BaseRenderer):
    """VBO 기반 고성능 렌더러

    Features:
    - GPU 메모리 캐싱 (VBO)
    - 외곽면만 렌더링
    - Part별 색상
    - Wireframe/Solid/Nodes
    - Modern OpenGL pipeline
    """

    def __init__(self):
        super().__init__()
        self._width = 1
        self._height = 1

        # VBO objects (Part별)
        self._wireframe_vbo = None
        self._edges_vbo = None       # 외곽 엣지 VBO
        self._solid_vbo = None
        self._nodes_vbo = None
        self._grid_vbo = None
        self._axes_vbo = None

        # VBO data counts (Part별)
        self._wireframe_counts = {}  # {part_id: vertex_count}
        self._edges_counts = {}      # {part_id: vertex_count}
        self._solid_counts = {}      # {part_id: vertex_count}
        self._nodes_count = 0
        self._grid_count = 0
        self._axes_count = 0

        # Batched VBOs (전체 통합, 성능 최적화)
        self._batched_solid_vbo = None
        self._batched_solid_count = 0
        self._batched_edges_vbo = None
        self._batched_edges_count = 0

        # Picking VBO (color-based element picking)
        self._picking_vbo = None
        self._picking_counts = {}    # {part_id: vertex_count}
        self._elem_id_map = {}       # {color_id: element_index}

        # Selection
        self._selected_element = None  # Selected element index

        # Shader program (optional - for now use fixed pipeline with VBO)
        self._use_shaders = False

    def initialize(self):
        """OpenGL 초기화"""
        print("[VBO Renderer] Initializing...")
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

        # GPU 정보 출력
        vendor = glGetString(GL_VENDOR).decode()
        renderer = glGetString(GL_RENDERER).decode()
        version = glGetString(GL_VERSION).decode()

        print(f"[VBO Renderer] OpenGL initialized")
        print(f"  Vendor: {vendor}")
        print(f"  Renderer: {renderer}")
        print(f"  Version: {version}")

        # Mesa 소프트웨어 렌더링 경고
        if 'llvmpipe' in renderer.lower() or 'software' in renderer.lower():
            print(f"  ⚠️  WARNING: Software rendering detected (Mesa)!")
            print(f"  ⚠️  VBO performance will be limited without GPU acceleration")

    def resize(self, width: int, height: int):
        """리사이즈"""
        self._width = width
        self._height = height
        glViewport(0, 0, width, height)

    def set_mesh(self, mesh):
        """메쉬 설정 - VBO 생성"""
        super().set_mesh(mesh)

        if mesh and len(mesh.nodes) > 0:
            print(f"[VBO Renderer] Building VBOs...")
            self._build_vbos()
            print(f"[VBO Renderer] VBOs ready!")

    def set_visible_parts(self, part_ids: set):
        """표시할 Part 설정 - Batched VBO 재생성"""
        super().set_visible_parts(part_ids)

        # Batched VBO 재생성 (가시성 변경 시)
        if self._mesh and self._exterior_faces:
            # 기존 batched VBO 삭제
            if self._batched_solid_vbo:
                self._batched_solid_vbo.delete()
                self._batched_solid_vbo = None
            if self._batched_edges_vbo:
                self._batched_edges_vbo.delete()
                self._batched_edges_vbo = None

            # 새로 생성
            self._build_batched_vbos()

    def _build_vbos(self):
        """VBO 생성 (GPU 메모리에 업로드)"""
        if not self._mesh:
            return

        # Clear old VBOs
        self._clear_vbos()

        # Build wireframe VBO (외곽면 기반)
        self._build_wireframe_vbo()

        # Build edges VBO (외곽 엣지만, 검은색)
        self._build_edges_vbo()

        # Build solid VBO (외곽면만)
        self._build_solid_vbo()

        # Build picking VBO (color-based element picking)
        self._build_picking_vbo()

        # Build nodes VBO
        self._build_nodes_vbo()

        # Build grid VBO
        self._build_grid_vbo()

        # Build axes VBO
        self._build_axes_vbo()

        # Build batched VBOs (성능 최적화)
        self._build_batched_vbos()

    def _build_batched_vbos(self):
        """Batched VBO 생성 (모든 visible Part를 하나의 VBO로 통합)

        Draw call 수를 대폭 줄여 렌더링 성능 향상
        - Part별 개별 draw call → 단일 draw call
        - CPU-GPU 통신 오버헤드 최소화
        """
        if not self._exterior_faces or not self._visible_parts:
            return

        # Solid batched VBO (모든 visible Part)
        solid_vertices = []
        for pid in self._visible_parts:
            if pid not in self._exterior_faces:
                continue

            color = self._part_colors.get(pid, (0.7, 0.7, 0.7))

            for elem_idx, face_indices in self._exterior_faces[pid]:
                node_indices = self._mesh.elements[elem_idx]

                if len(face_indices) == 4:
                    # Triangle 1: 0-1-2
                    for i in [face_indices[0], face_indices[1], face_indices[2]]:
                        idx = node_indices[i]
                        p = self._mesh.nodes[idx]
                        solid_vertices.extend([p[0], p[1], p[2]])
                        solid_vertices.extend(color)

                    # Triangle 2: 0-2-3
                    for i in [face_indices[0], face_indices[2], face_indices[3]]:
                        idx = node_indices[i]
                        p = self._mesh.nodes[idx]
                        solid_vertices.extend([p[0], p[1], p[2]])
                        solid_vertices.extend(color)

        if solid_vertices:
            vertex_data = np.array(solid_vertices, dtype=np.float32)
            self._batched_solid_vbo = vbo.VBO(vertex_data)
            self._batched_solid_count = len(solid_vertices) // 6
            print(f"[VBO Renderer] Batched Solid VBO: {self._batched_solid_count} vertices")

        # Edges batched VBO (모든 visible Part)
        edges_vertices = []
        black = (0.0, 0.0, 0.0)

        for pid in self._visible_parts:
            if pid not in self._exterior_faces:
                continue

            for elem_idx, face_indices in self._exterior_faces[pid]:
                node_indices = self._mesh.elements[elem_idx]

                if len(face_indices) == 4:
                    edges = [
                        (face_indices[0], face_indices[1]),
                        (face_indices[1], face_indices[2]),
                        (face_indices[2], face_indices[3]),
                        (face_indices[3], face_indices[0])
                    ]

                    for i, j in edges:
                        idx1 = node_indices[i]
                        idx2 = node_indices[j]
                        p1 = self._mesh.nodes[idx1]
                        p2 = self._mesh.nodes[idx2]

                        edges_vertices.extend([p1[0], p1[1], p1[2]])
                        edges_vertices.extend(black)
                        edges_vertices.extend([p2[0], p2[1], p2[2]])
                        edges_vertices.extend(black)

        if edges_vertices:
            vertex_data = np.array(edges_vertices, dtype=np.float32)
            self._batched_edges_vbo = vbo.VBO(vertex_data)
            self._batched_edges_count = len(edges_vertices) // 6
            print(f"[VBO Renderer] Batched Edges VBO: {self._batched_edges_count} vertices")

    def _build_wireframe_vbo(self):
        """와이어프레임 VBO 생성 (Part별)"""
        if not self._mesh:
            return

        # Part별로 VBO 생성 (색상 포함)
        wireframe_data = {}

        for pid in self._mesh.part_elements.keys():
            if pid not in self._mesh.part_elements:
                continue

            color = self._part_colors.get(pid, (0.7, 0.7, 0.7))
            vertices = []

            # 외곽면의 엣지만 렌더링
            if self._exterior_faces and pid in self._exterior_faces:
                for elem_idx, face_indices in self._exterior_faces[pid]:
                    node_indices = self._mesh.elements[elem_idx]
                    n = len(node_indices)

                    # Face 엣지 정의
                    if n == 4:  # Shell
                        edges = [(0,1),(1,2),(2,3),(3,0)]
                    elif n == 8:  # Hex
                        # 외곽면의 엣지만 (face_indices를 사용)
                        edges = [
                            (face_indices[0], face_indices[1]),
                            (face_indices[1], face_indices[2]),
                            (face_indices[2], face_indices[3]),
                            (face_indices[3], face_indices[0])
                        ]
                    else:
                        continue

                    for i, j in edges:
                        if n == 4:
                            idx1, idx2 = node_indices[i], node_indices[j]
                        else:  # Hex
                            idx1, idx2 = node_indices[i], node_indices[j]

                        p1 = self._mesh.nodes[idx1]
                        p2 = self._mesh.nodes[idx2]

                        # Vertex 1 (position + color)
                        vertices.extend([p1[0], p1[1], p1[2]])
                        vertices.extend(color)

                        # Vertex 2 (position + color)
                        vertices.extend([p2[0], p2[1], p2[2]])
                        vertices.extend(color)

            if vertices:
                # Create VBO
                vertex_data = np.array(vertices, dtype=np.float32)
                wireframe_data[pid] = vbo.VBO(vertex_data)
                self._wireframe_counts[pid] = len(vertices) // 6  # 6 floats per vertex (xyz + rgb)

        self._wireframe_vbo = wireframe_data

    def _build_edges_vbo(self):
        """외곽 엣지 VBO 생성 (검은색 윤곽선)"""
        if not self._exterior_faces:
            return

        edges_data = {}
        black = (0.0, 0.0, 0.0)  # 검은색

        for pid in self._mesh.part_elements.keys():
            if pid not in self._exterior_faces:
                continue

            vertices = []

            # 외곽면의 엣지만
            for elem_idx, face_indices in self._exterior_faces[pid]:
                node_indices = self._mesh.elements[elem_idx]

                # Face 엣지 (사각형)
                if len(face_indices) == 4:
                    edges = [
                        (face_indices[0], face_indices[1]),
                        (face_indices[1], face_indices[2]),
                        (face_indices[2], face_indices[3]),
                        (face_indices[3], face_indices[0])
                    ]

                    for i, j in edges:
                        idx1 = node_indices[i]
                        idx2 = node_indices[j]
                        p1 = self._mesh.nodes[idx1]
                        p2 = self._mesh.nodes[idx2]

                        # Vertex 1
                        vertices.extend([p1[0], p1[1], p1[2]])
                        vertices.extend(black)

                        # Vertex 2
                        vertices.extend([p2[0], p2[1], p2[2]])
                        vertices.extend(black)

            if vertices:
                vertex_data = np.array(vertices, dtype=np.float32)
                edges_data[pid] = vbo.VBO(vertex_data)
                self._edges_counts[pid] = len(vertices) // 6

        self._edges_vbo = edges_data

    def _build_solid_vbo(self):
        """솔리드 VBO 생성 (외곽면만, Part별)"""
        if not self._exterior_faces:
            return

        solid_data = {}

        for pid in self._visible_parts:
            if pid not in self._exterior_faces:
                continue

            color = self._part_colors.get(pid, (0.7, 0.7, 0.7))
            vertices = []

            # 외곽면만 렌더링
            for elem_idx, face_indices in self._exterior_faces[pid]:
                node_indices = self._mesh.elements[elem_idx]

                # Quad face → 2 triangles
                # face_indices: [0, 1, 2, 3]
                if len(face_indices) == 4:
                    # Triangle 1: 0-1-2
                    for i in [face_indices[0], face_indices[1], face_indices[2]]:
                        idx = node_indices[i]
                        p = self._mesh.nodes[idx]
                        vertices.extend([p[0], p[1], p[2]])
                        vertices.extend(color)

                    # Triangle 2: 0-2-3
                    for i in [face_indices[0], face_indices[2], face_indices[3]]:
                        idx = node_indices[i]
                        p = self._mesh.nodes[idx]
                        vertices.extend([p[0], p[1], p[2]])
                        vertices.extend(color)

            if vertices:
                vertex_data = np.array(vertices, dtype=np.float32)
                solid_data[pid] = vbo.VBO(vertex_data)
                self._solid_counts[pid] = len(vertices) // 6

        self._solid_vbo = solid_data

    def _build_picking_vbo(self):
        """Picking VBO 생성 (요소별 고유 색상)

        각 요소를 고유한 색상 ID로 렌더링하여 클릭 시 요소를 식별
        색상 ID는 24비트 RGB (16,777,216개 요소 지원)
        """
        if not self._exterior_faces:
            return

        picking_data = {}
        self._elem_id_map = {}  # Clear mapping
        color_id = 1  # Start from 1 (0 is background)

        for pid in self._mesh.part_elements.keys():
            if pid not in self._exterior_faces:
                continue

            vertices = []

            # 외곽면만 렌더링
            for elem_idx, face_indices in self._exterior_faces[pid]:
                # 요소 인덱스를 RGB 색상으로 인코딩
                r = (color_id >> 16) & 0xFF
                g = (color_id >> 8) & 0xFF
                b = color_id & 0xFF
                color = (r / 255.0, g / 255.0, b / 255.0)

                # Color ID → Element Index 매핑 저장
                self._elem_id_map[color_id] = elem_idx
                color_id += 1

                node_indices = self._mesh.elements[elem_idx]

                # Quad face → 2 triangles (solid와 동일한 구조)
                if len(face_indices) == 4:
                    # Triangle 1: 0-1-2
                    for i in [face_indices[0], face_indices[1], face_indices[2]]:
                        idx = node_indices[i]
                        p = self._mesh.nodes[idx]
                        vertices.extend([p[0], p[1], p[2]])
                        vertices.extend(color)

                    # Triangle 2: 0-2-3
                    for i in [face_indices[0], face_indices[2], face_indices[3]]:
                        idx = node_indices[i]
                        p = self._mesh.nodes[idx]
                        vertices.extend([p[0], p[1], p[2]])
                        vertices.extend(color)

            if vertices:
                vertex_data = np.array(vertices, dtype=np.float32)
                picking_data[pid] = vbo.VBO(vertex_data)
                self._picking_counts[pid] = len(vertices) // 6

        self._picking_vbo = picking_data
        print(f"[VBO Renderer] Picking VBO built: {len(self._elem_id_map)} elements")

    def _build_nodes_vbo(self):
        """노드 VBO 생성"""
        if not self._mesh:
            return

        vertices = []

        # 표시할 part의 모든 노드 수집
        node_indices = set()
        for pid in self._visible_parts:
            if pid in self._mesh.part_elements:
                for elem_idx in self._mesh.part_elements[pid]:
                    node_indices.update(self._mesh.elements[elem_idx])

        # 노드 데이터 생성
        for idx in node_indices:
            p = self._mesh.nodes[idx]
            vertices.extend([p[0], p[1], p[2]])
            vertices.extend([1.0, 1.0, 0.0])  # Yellow

        if vertices:
            vertex_data = np.array(vertices, dtype=np.float32)
            self._nodes_vbo = vbo.VBO(vertex_data)
            self._nodes_count = len(vertices) // 6

    def _build_grid_vbo(self):
        """그리드 VBO 생성"""
        vertices = []

        # Grid lines
        for i in range(-10, 11):
            p = i * 10.0
            # Horizontal lines
            vertices.extend([p, -100, 0, 0.3, 0.3, 0.3])
            vertices.extend([p, 100, 0, 0.3, 0.3, 0.3])
            # Vertical lines
            vertices.extend([-100, p, 0, 0.3, 0.3, 0.3])
            vertices.extend([100, p, 0, 0.3, 0.3, 0.3])

        vertex_data = np.array(vertices, dtype=np.float32)
        self._grid_vbo = vbo.VBO(vertex_data)
        self._grid_count = len(vertices) // 6

    def _build_axes_vbo(self):
        """축 VBO 생성"""
        vertices = [
            # X axis (red)
            0, 0, 0, 1, 0, 0,
            20, 0, 0, 1, 0, 0,
            # Y axis (green)
            0, 0, 0, 0, 1, 0,
            0, 20, 0, 0, 1, 0,
            # Z axis (blue)
            0, 0, 0, 0, 0, 1,
            0, 0, 20, 0, 0, 1,
        ]

        vertex_data = np.array(vertices, dtype=np.float32)
        self._axes_vbo = vbo.VBO(vertex_data)
        self._axes_count = len(vertices) // 6

    def _clear_vbos(self):
        """VBO 메모리 해제"""
        if self._wireframe_vbo:
            for vbo_obj in self._wireframe_vbo.values():
                vbo_obj.delete()
            self._wireframe_vbo = None

        if self._edges_vbo:
            for vbo_obj in self._edges_vbo.values():
                vbo_obj.delete()
            self._edges_vbo = None

        if self._solid_vbo:
            for vbo_obj in self._solid_vbo.values():
                vbo_obj.delete()
            self._solid_vbo = None

        if self._picking_vbo:
            for vbo_obj in self._picking_vbo.values():
                vbo_obj.delete()
            self._picking_vbo = None

        if self._nodes_vbo:
            self._nodes_vbo.delete()
            self._nodes_vbo = None

        if self._grid_vbo:
            self._grid_vbo.delete()
            self._grid_vbo = None

        if self._axes_vbo:
            self._axes_vbo.delete()
            self._axes_vbo = None

        if self._batched_solid_vbo:
            self._batched_solid_vbo.delete()
            self._batched_solid_vbo = None

        if self._batched_edges_vbo:
            self._batched_edges_vbo.delete()
            self._batched_edges_vbo = None

    def render(self):
        """메인 렌더링 (VBO 사용)"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if not self._mesh or len(self._mesh.nodes) == 0:
            return

        # 투영 행렬
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self._width / max(self._height, 1)
        proj = self._camera.get_projection_matrix(aspect)
        glLoadMatrixf(proj.T.astype(np.float32))

        # 모델뷰 행렬
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        view = self._camera.get_view_matrix()
        glLoadMatrixf(view.T.astype(np.float32))

        # Enable vertex arrays (한 번만)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        # 그리드
        self._draw_grid_vbo()

        # 렌더링 (Batched VBO 사용 - 최적화)
        if self._show_solid:
            glEnable(GL_POLYGON_OFFSET_FILL)
            glPolygonOffset(1.0, 1.0)
            # Batched VBO가 있으면 사용 (훨씬 빠름)
            if self._batched_solid_vbo:
                self._draw_batched_solid()
            else:
                self._draw_solid_vbo()  # Fallback
            glDisable(GL_POLYGON_OFFSET_FILL)

        if self._show_edges:
            # Batched VBO가 있으면 사용 (훨씬 빠름)
            if self._batched_edges_vbo:
                self._draw_batched_edges()
            else:
                self._draw_edges_vbo()  # Fallback

        if self._show_wireframe:
            self._draw_wireframe_vbo()  # 모든 엣지 (Part 색상)

        if self._show_nodes:
            self._draw_nodes_vbo()

        # 선택된 요소 하이라이트
        if self._selected_element is not None:
            self._draw_selected_element()

        # Disable vertex arrays
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

    def _draw_grid_vbo(self):
        """그리드 & 축 (VBO)"""
        if not self._grid_vbo or not self._axes_vbo:
            return

        # Grid
        self._grid_vbo.bind()
        glVertexPointer(3, GL_FLOAT, 24, self._grid_vbo)  # stride=24 (6 floats * 4 bytes)
        glColorPointer(3, GL_FLOAT, 24, self._grid_vbo + 12)  # offset=12 (3 floats * 4 bytes)
        glDrawArrays(GL_LINES, 0, self._grid_count)
        self._grid_vbo.unbind()

        # Axes (thicker)
        glLineWidth(3.0)
        self._axes_vbo.bind()
        glVertexPointer(3, GL_FLOAT, 24, self._axes_vbo)
        glColorPointer(3, GL_FLOAT, 24, self._axes_vbo + 12)
        glDrawArrays(GL_LINES, 0, self._axes_count)
        self._axes_vbo.unbind()
        glLineWidth(1.5)

    def _draw_edges_vbo(self):
        """외곽 엣지 (VBO, 검은색 윤곽선)"""
        if not self._edges_vbo:
            return

        glLineWidth(1.0)  # 얇은 윤곽선

        for pid in self._visible_parts:
            if pid not in self._edges_vbo:
                continue

            vbo_obj = self._edges_vbo[pid]
            count = self._edges_counts[pid]

            vbo_obj.bind()
            glVertexPointer(3, GL_FLOAT, 24, vbo_obj)
            glColorPointer(3, GL_FLOAT, 24, vbo_obj + 12)
            glDrawArrays(GL_LINES, 0, count)
            vbo_obj.unbind()

        glLineWidth(1.5)

    def _draw_wireframe_vbo(self):
        """와이어프레임 (VBO)"""
        if not self._wireframe_vbo:
            return

        for pid in self._visible_parts:
            if pid not in self._wireframe_vbo:
                continue

            vbo_obj = self._wireframe_vbo[pid]
            count = self._wireframe_counts[pid]

            vbo_obj.bind()
            glVertexPointer(3, GL_FLOAT, 24, vbo_obj)
            glColorPointer(3, GL_FLOAT, 24, vbo_obj + 12)
            glDrawArrays(GL_LINES, 0, count)
            vbo_obj.unbind()

    def _draw_solid_vbo(self):
        """솔리드 (VBO, 외곽면만)"""
        if not self._solid_vbo:
            return

        glEnable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        for pid in self._visible_parts:
            if pid not in self._solid_vbo:
                continue

            vbo_obj = self._solid_vbo[pid]
            count = self._solid_counts[pid]

            vbo_obj.bind()
            glVertexPointer(3, GL_FLOAT, 24, vbo_obj)
            glColorPointer(3, GL_FLOAT, 24, vbo_obj + 12)
            glDrawArrays(GL_TRIANGLES, 0, count)
            vbo_obj.unbind()

        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)

    def _draw_nodes_vbo(self):
        """노드 포인트 (VBO)"""
        if not self._nodes_vbo:
            return

        self._nodes_vbo.bind()
        glVertexPointer(3, GL_FLOAT, 24, self._nodes_vbo)
        glColorPointer(3, GL_FLOAT, 24, self._nodes_vbo + 12)
        glDrawArrays(GL_POINTS, 0, self._nodes_count)
        self._nodes_vbo.unbind()

    def _draw_batched_solid(self):
        """Batched Solid VBO (단일 draw call - 최적화)"""
        if not self._batched_solid_vbo:
            return

        glEnable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self._batched_solid_vbo.bind()
        glVertexPointer(3, GL_FLOAT, 24, self._batched_solid_vbo)
        glColorPointer(3, GL_FLOAT, 24, self._batched_solid_vbo + 12)
        glDrawArrays(GL_TRIANGLES, 0, self._batched_solid_count)
        self._batched_solid_vbo.unbind()

        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)

    def _draw_batched_edges(self):
        """Batched Edges VBO (단일 draw call - 최적화)"""
        if not self._batched_edges_vbo:
            return

        glLineWidth(1.0)

        self._batched_edges_vbo.bind()
        glVertexPointer(3, GL_FLOAT, 24, self._batched_edges_vbo)
        glColorPointer(3, GL_FLOAT, 24, self._batched_edges_vbo + 12)
        glDrawArrays(GL_LINES, 0, self._batched_edges_count)
        self._batched_edges_vbo.unbind()

        glLineWidth(1.5)

    def _draw_picking_vbo(self):
        """Picking 버퍼 렌더링 (요소별 고유 색상)"""
        if not self._picking_vbo:
            return

        glDisable(GL_LIGHTING)
        glDisable(GL_BLEND)

        for pid in self._visible_parts:
            if pid not in self._picking_vbo:
                continue

            vbo_obj = self._picking_vbo[pid]
            count = self._picking_counts[pid]

            vbo_obj.bind()
            glVertexPointer(3, GL_FLOAT, 24, vbo_obj)
            glColorPointer(3, GL_FLOAT, 24, vbo_obj + 12)
            glDrawArrays(GL_TRIANGLES, 0, count)
            vbo_obj.unbind()

    def pick_element(self, x: int, y: int) -> Optional[int]:
        """마우스 좌표에서 요소 선택 (GPU picking)

        Args:
            x: 윈도우 X 좌표
            y: 윈도우 Y 좌표 (top-down)

        Returns:
            선택된 요소 인덱스 (없으면 None)
        """
        if not self._picking_vbo or not self._elem_id_map:
            return None

        # Y 좌표 뒤집기 (OpenGL은 bottom-up)
        y_gl = self._height - y

        # Picking 렌더링
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # 투영 & 뷰 행렬 (일반 렌더링과 동일)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self._width / max(self._height, 1)
        proj = self._camera.get_projection_matrix(aspect)
        glLoadMatrixf(proj.T.astype(np.float32))

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        view = self._camera.get_view_matrix()
        glLoadMatrixf(view.T.astype(np.float32))

        # Enable vertex arrays
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        # Picking VBO 렌더링
        self._draw_picking_vbo()

        # Disable vertex arrays
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        # 픽셀 색상 읽기
        glFlush()
        glFinish()
        pixel = glReadPixels(x, y_gl, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)

        # RGB → Color ID 디코딩
        r, g, b = pixel[0][0]
        color_id = (r << 16) | (g << 8) | b

        # Color ID → Element Index 변환
        elem_idx = self._elem_id_map.get(color_id)

        if elem_idx is not None:
            self._selected_element = elem_idx
            print(f"[Picking] Element {elem_idx} selected (color_id={color_id})")

        return elem_idx

    def get_selected_element(self) -> Optional[int]:
        """선택된 요소 인덱스 반환"""
        return self._selected_element

    def set_selected_element(self, elem_idx: Optional[int]):
        """선택된 요소 설정"""
        self._selected_element = elem_idx

    def _draw_selected_element(self):
        """선택된 요소 하이라이트 (굵은 빨간색 외곽선)"""
        if self._selected_element is None or not self._exterior_faces:
            return

        elem_idx = self._selected_element

        # 선택된 요소가 어느 Part의 어느 face인지 찾기
        selected_face = None
        for pid, faces in self._exterior_faces.items():
            for e_idx, face_indices in faces:
                if e_idx == elem_idx:
                    selected_face = (e_idx, face_indices)
                    break
            if selected_face:
                break

        if not selected_face:
            return

        elem_idx, face_indices = selected_face
        node_indices = self._mesh.elements[elem_idx]

        # 하이라이트 색상 (밝은 노란색)
        highlight_color = (1.0, 1.0, 0.0)

        # 엣지 그리기
        glDisable(GL_LIGHTING)
        glLineWidth(4.0)  # 굵은 선
        glColor3f(*highlight_color)

        glBegin(GL_LINE_LOOP)
        for i in face_indices:
            idx = node_indices[i]
            p = self._mesh.nodes[idx]
            glVertex3f(p[0], p[1], p[2])
        glEnd()

        glLineWidth(1.5)  # 원래대로

    @property
    def name(self) -> str:
        return "VBO (GPU Accelerated)"

    def __del__(self):
        """소멸자 - VBO 메모리 해제"""
        self._clear_vbos()
