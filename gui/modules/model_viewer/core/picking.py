"""GPU 기반 Element Picking 시스템

마우스 클릭으로 요소 선택 기능
"""
import numpy as np
from OpenGL.GL import *
from typing import Optional, Tuple
import ctypes


class ElementPicker:
    """GPU 기반 Element Picking

    색상 ID 방식:
    - 각 요소를 고유한 색상으로 렌더링
    - 클릭한 픽셀의 색상을 읽어 요소 ID 추출
    """

    def __init__(self):
        # Picking용 FBO (Framebuffer Object)
        self._fbo = None
        self._color_texture = None
        self._depth_buffer = None

        # Shader program
        self._picking_shader = None

        # 해상도
        self._width = 0
        self._height = 0

    def initialize(self, width: int, height: int):
        """Picking 시스템 초기화

        Args:
            width: 렌더 타겟 너비
            height: 렌더 타겟 높이
        """
        self._width = width
        self._height = height

        # FBO 생성
        self._fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self._fbo)

        # Color texture (RGB32UI - element ID 저장)
        self._color_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self._color_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32UI, width, height, 0,
                     GL_RGB_INTEGER, GL_UNSIGNED_INT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                              GL_TEXTURE_2D, self._color_texture, 0)

        # Depth buffer
        self._depth_buffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self._depth_buffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, width, height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                                 GL_RENDERBUFFER, self._depth_buffer)

        # FBO 상태 확인
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(f"Picking FBO incomplete: {status}")

        # 원래 FBO로 복귀
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Shader 컴파일
        self._compile_picking_shader()

        print(f"[Picking] Initialized: {width}x{height}")

    def _compile_picking_shader(self):
        """Picking용 Shader 컴파일"""
        # Vertex Shader
        vertex_code = """
        #version 330 core
        layout(location = 0) in vec3 position;
        layout(location = 1) in uint elementId;  // Element ID

        uniform mat4 projection;
        uniform mat4 view;

        flat out uint fragElementId;

        void main() {
            gl_Position = projection * view * vec4(position, 1.0);
            fragElementId = elementId;
        }
        """

        # Fragment Shader
        fragment_code = """
        #version 330 core
        flat in uint fragElementId;

        out uvec3 outId;  // RGB = element ID

        void main() {
            // Element ID를 RGB로 인코딩
            uint id = fragElementId;
            outId = uvec3(
                (id >> 16) & 0xFFu,
                (id >> 8) & 0xFFu,
                id & 0xFFu
            );
        }
        """

        # Compile
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_code)
        glCompileShader(vertex_shader)

        if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(vertex_shader).decode()
            raise RuntimeError(f"Picking vertex shader error: {error}")

        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_code)
        glCompileShader(fragment_shader)

        if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(fragment_shader).decode()
            raise RuntimeError(f"Picking fragment shader error: {error}")

        # Link
        self._picking_shader = glCreateProgram()
        glAttachShader(self._picking_shader, vertex_shader)
        glAttachShader(self._picking_shader, fragment_shader)
        glLinkProgram(self._picking_shader)

        if not glGetProgramiv(self._picking_shader, GL_LINK_STATUS):
            error = glGetProgramInfoLog(self._picking_shader).decode()
            raise RuntimeError(f"Picking shader link error: {error}")

        # Cleanup
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        print("[Picking] Shaders compiled")

    def pick(self, mouse_x: int, mouse_y: int,
             proj_matrix: np.ndarray, view_matrix: np.ndarray,
             vao: int, vertex_count: int) -> Optional[int]:
        """마우스 위치에서 Element ID 읽기

        Args:
            mouse_x: 마우스 X 좌표 (화면)
            mouse_y: 마우스 Y 좌표 (화면, 위에서부터)
            proj_matrix: 투영 행렬
            view_matrix: 뷰 행렬
            vao: Picking용 VAO (element ID 포함)
            vertex_count: Vertex 개수

        Returns:
            선택된 Element ID (없으면 None)
        """
        if not self._fbo:
            return None

        # Picking FBO로 전환
        glBindFramebuffer(GL_FRAMEBUFFER, self._fbo)
        glViewport(0, 0, self._width, self._height)

        # 클리어 (ID = 0 = 선택 없음)
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Picking shader 사용
        glUseProgram(self._picking_shader)

        # Uniform 설정
        proj_loc = glGetUniformLocation(self._picking_shader, "projection")
        view_loc = glGetUniformLocation(self._picking_shader, "view")
        glUniformMatrix4fv(proj_loc, 1, GL_FALSE, proj_matrix.T.astype(np.float32))
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, view_matrix.T.astype(np.float32))

        # 렌더링
        glBindVertexArray(vao)
        glDrawArrays(GL_TRIANGLES, 0, vertex_count)
        glBindVertexArray(0)

        # 픽셀 읽기 (마우스 위치)
        # OpenGL은 Y축이 아래에서 위로 증가
        y_flipped = self._height - mouse_y - 1

        pixel = glReadPixels(mouse_x, y_flipped, 1, 1, GL_RGB_INTEGER, GL_UNSIGNED_INT)
        pixel_array = np.frombuffer(pixel, dtype=np.uint32)

        # RGB → Element ID 디코딩
        if len(pixel_array) >= 3:
            r, g, b = pixel_array[0], pixel_array[1], pixel_array[2]
            element_id = (r << 16) | (g << 8) | b

            if element_id > 0:
                result = int(element_id)
            else:
                result = None
        else:
            result = None

        # 원래 FBO로 복귀
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glUseProgram(0)

        return result

    def resize(self, width: int, height: int):
        """렌더 타겟 크기 변경

        Args:
            width: 새 너비
            height: 새 높이
        """
        if width == self._width and height == self._height:
            return

        # 기존 리소스 삭제
        if self._fbo:
            glDeleteFramebuffers(1, [self._fbo])
        if self._color_texture:
            glDeleteTextures(1, [self._color_texture])
        if self._depth_buffer:
            glDeleteRenderbuffers(1, [self._depth_buffer])

        # 재생성
        self.initialize(width, height)

    def cleanup(self):
        """리소스 정리"""
        if self._fbo:
            glDeleteFramebuffers(1, [self._fbo])
        if self._color_texture:
            glDeleteTextures(1, [self._color_texture])
        if self._depth_buffer:
            glDeleteRenderbuffers(1, [self._depth_buffer])
        if self._picking_shader:
            glDeleteProgram(self._picking_shader)

        self._fbo = None
        self._color_texture = None
        self._depth_buffer = None
        self._picking_shader = None


class SelectionManager:
    """선택된 요소 관리

    - 선택/해제
    - 다중 선택 (Ctrl+Click)
    - 선택 정보 저장
    """

    def __init__(self):
        self._selected_elements = set()  # 선택된 element ID들

    def select(self, element_id: int, multi_select: bool = False):
        """요소 선택

        Args:
            element_id: Element ID
            multi_select: True이면 기존 선택 유지 (Ctrl+Click)
        """
        if not multi_select:
            self._selected_elements.clear()

        if element_id in self._selected_elements:
            # 이미 선택된 경우 토글
            self._selected_elements.remove(element_id)
        else:
            self._selected_elements.add(element_id)

    def clear(self):
        """모든 선택 해제"""
        self._selected_elements.clear()

    def is_selected(self, element_id: int) -> bool:
        """선택 여부 확인"""
        return element_id in self._selected_elements

    def get_selected(self) -> set:
        """선택된 요소 ID 집합 반환"""
        return self._selected_elements.copy()

    def count(self) -> int:
        """선택된 요소 개수"""
        return len(self._selected_elements)
