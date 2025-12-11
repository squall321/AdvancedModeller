"""Legacy OpenGL Renderer

Fixed-pipeline OpenGL (glBegin/glEnd) - 최대 호환성
"""
from OpenGL.GL import *
import numpy as np

from .base_renderer import BaseRenderer


class LegacyRenderer(BaseRenderer):
    """Legacy OpenGL 렌더러 (glBegin/glEnd)

    Features:
    - 최대 호환성 (OpenGL 2.1+)
    - 간단한 구현
    - Part별 색상
    - Wireframe/Solid/Nodes
    """

    def __init__(self):
        super().__init__()
        self._width = 1
        self._height = 1

    def initialize(self):
        """OpenGL 초기화"""
        print("[Legacy Renderer] Initializing...")
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

        print(f"[Legacy Renderer] OpenGL initialized")
        print(f"  Vendor: {vendor}")
        print(f"  Renderer: {renderer}")
        print(f"  Version: {version}")

        # Mesa 소프트웨어 렌더링 경고
        if 'llvmpipe' in renderer.lower() or 'software' in renderer.lower():
            print(f"  ⚠️  WARNING: Software rendering detected (Mesa)!")
            print(f"  ⚠️  GPU acceleration disabled - performance will be slow")
            print(f"  ⚠️  Check your graphics drivers or DISPLAY settings")

    def resize(self, width: int, height: int):
        """리사이즈"""
        self._width = width
        self._height = height
        glViewport(0, 0, width, height)

    def render(self):
        """메인 렌더링"""
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

        # 그리드
        self._draw_grid()

        # 렌더링
        if self._show_solid:
            glEnable(GL_POLYGON_OFFSET_FILL)
            glPolygonOffset(1.0, 1.0)
            self._draw_solid()
            glDisable(GL_POLYGON_OFFSET_FILL)

        if self._show_edges:
            self._draw_edges()  # 외곽 엣지만 (검은색 윤곽선)

        if self._show_wireframe:
            self._draw_wireframe()  # 모든 엣지 (Part 색상)

        if self._show_nodes:
            self._draw_nodes()

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
                node_indices = self._mesh.elements[elem_idx]
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
        """솔리드 (외곽면만 렌더링 - 성능 최적화)"""
        if not self._exterior_faces:
            return

        glEnable(GL_LIGHTING)  # Enable lighting for surfaces
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        for pid in self._visible_parts:
            if pid not in self._exterior_faces:
                continue

            color = self._part_colors.get(pid, (0.7, 0.7, 0.7))
            glColor4f(color[0], color[1], color[2], 0.85)  # Slightly more opaque

            glBegin(GL_QUADS)
            # 외곽면만 렌더링 (내부 폴리곤 제외)
            for elem_idx, face_indices in self._exterior_faces[pid]:
                node_indices = self._mesh.elements[elem_idx]

                # 면의 노드들 렌더링
                for i in face_indices:
                    idx = node_indices[i]
                    p = self._mesh.nodes[idx]
                    glVertex3f(p[0], p[1], p[2])
            glEnd()

        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)  # Disable after solid rendering

    def _draw_edges(self):
        """외곽 엣지만 (검은색 윤곽선)"""
        if not self._exterior_faces:
            return

        glColor3f(0.0, 0.0, 0.0)  # 검은색 윤곽선
        glLineWidth(1.0)
        glBegin(GL_LINES)

        for pid in self._visible_parts:
            if pid not in self._exterior_faces:
                continue

            # 외곽면의 엣지만 그리기
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
                        glVertex3f(p1[0], p1[1], p1[2])
                        glVertex3f(p2[0], p2[1], p2[2])

        glEnd()
        glLineWidth(1.5)

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

    @property
    def name(self) -> str:
        return "Legacy OpenGL"
