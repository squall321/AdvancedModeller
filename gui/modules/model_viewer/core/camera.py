"""Camera controller for 3D view

Arcball 방식의 빠르고 직관적인 카메라 컨트롤
"""
import numpy as np
from typing import Tuple


class Camera:
    """3D 카메라

    - Arcball 회전 (직관적)
    - 줌 (거리 조절)
    - 팬 (이동)
    """

    def __init__(self):
        # 카메라 위치
        self.distance = 100.0  # 타겟으로부터의 거리
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)  # 주시점

        # 회전 (오일러 각도 - 간단함)
        self.elevation = 30.0  # 위/아래 (도)
        self.azimuth = 45.0    # 좌/우 (도)

        # 투영
        self.fov = 45.0  # Field of view
        self.near = 0.1
        self.far = 10000.0

    def get_view_matrix(self) -> np.ndarray:
        """뷰 행렬 생성

        Returns:
            4x4 view matrix
        """
        # 구면 좌표계 -> 카르테시안 좌표계
        elev_rad = np.radians(self.elevation)
        azim_rad = np.radians(self.azimuth)

        # 카메라 위치 계산
        x = self.distance * np.cos(elev_rad) * np.cos(azim_rad)
        y = self.distance * np.cos(elev_rad) * np.sin(azim_rad)
        z = self.distance * np.sin(elev_rad)

        eye = self.target + np.array([x, y, z], dtype=np.float32)

        # Up 벡터
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        # LookAt 행렬 생성
        return look_at(eye, self.target, up)

    def get_projection_matrix(self, aspect: float) -> np.ndarray:
        """투영 행렬 생성

        Args:
            aspect: 종횡비 (width / height)

        Returns:
            4x4 projection matrix
        """
        return perspective(self.fov, aspect, self.near, self.far)

    def rotate(self, delta_azim: float, delta_elev: float):
        """회전

        Args:
            delta_azim: 방위각 변화 (도)
            delta_elev: 고도각 변화 (도)
        """
        self.azimuth += delta_azim
        self.elevation += delta_elev

        # 고도각 제한 (-89 ~ 89도)
        self.elevation = np.clip(self.elevation, -89.0, 89.0)

    def zoom(self, factor: float):
        """줌

        Args:
            factor: 줌 팩터 (> 1: 가까이, < 1: 멀리)
        """
        self.distance /= factor
        # 거리 제한
        self.distance = np.clip(self.distance, 1.0, 10000.0)

    def pan(self, delta_x: float, delta_y: float):
        """팬 (타겟 이동)

        Args:
            delta_x: X축 이동 (화면 좌표계)
            delta_y: Y축 이동 (화면 좌표계)
        """
        # 거리에 비례한 팬 속도
        scale = self.distance * 0.001

        # 카메라 방향 벡터 계산
        elev_rad = np.radians(self.elevation)
        azim_rad = np.radians(self.azimuth)

        # 우측 벡터
        right = np.array([
            -np.sin(azim_rad),
            np.cos(azim_rad),
            0.0
        ], dtype=np.float32)

        # 상향 벡터 (카메라 기준)
        up = np.array([
            -np.cos(azim_rad) * np.sin(elev_rad),
            -np.sin(azim_rad) * np.sin(elev_rad),
            np.cos(elev_rad)
        ], dtype=np.float32)

        # 타겟 이동
        self.target += right * delta_x * scale
        self.target += up * delta_y * scale

    def fit_to_bounds(self, min_bounds: np.ndarray, max_bounds: np.ndarray):
        """모델이 화면에 꽉 차도록 카메라 조정

        Args:
            min_bounds: 최소 좌표 [x, y, z]
            max_bounds: 최대 좌표 [x, y, z]
        """
        # 모델 중심
        center = (min_bounds + max_bounds) / 2.0
        self.target = center

        # 모델 크기
        size = np.linalg.norm(max_bounds - min_bounds)

        # FOV에 맞는 거리 계산
        fov_rad = np.radians(self.fov)
        self.distance = size / (2.0 * np.tan(fov_rad / 2.0)) * 1.5  # 1.5배 여유

        # 기본 뷰 각도
        self.elevation = 30.0
        self.azimuth = 45.0

    # ========== 6-View Presets (CAE Standard Views) ==========

    def view_front(self):
        """Front view (+Y direction, XZ plane)"""
        self.elevation = 0.0
        self.azimuth = 90.0

    def view_back(self):
        """Back view (-Y direction)"""
        self.elevation = 0.0
        self.azimuth = -90.0

    def view_left(self):
        """Left view (-X direction, YZ plane)"""
        self.elevation = 0.0
        self.azimuth = 180.0

    def view_right(self):
        """Right view (+X direction)"""
        self.elevation = 0.0
        self.azimuth = 0.0

    def view_top(self):
        """Top view (+Z direction, XY plane)"""
        self.elevation = 90.0
        self.azimuth = 0.0

    def view_bottom(self):
        """Bottom view (-Z direction)"""
        self.elevation = -90.0
        self.azimuth = 0.0

    def view_isometric(self):
        """Isometric view (default 3D perspective)"""
        self.elevation = 30.0
        self.azimuth = 45.0


# 유틸리티 함수들

def look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    """LookAt 행렬 생성

    Args:
        eye: 카메라 위치
        target: 주시점
        up: 상향 벡터

    Returns:
        4x4 view matrix
    """
    # Forward 벡터 (z축)
    f = target - eye
    f = f / np.linalg.norm(f)

    # Right 벡터 (x축)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)

    # Up 벡터 (y축)
    u = np.cross(s, f)

    # 행렬 구성
    mat = np.eye(4, dtype=np.float32)
    mat[0, :3] = s
    mat[1, :3] = u
    mat[2, :3] = -f

    # 이동 부분
    mat[0, 3] = -np.dot(s, eye)
    mat[1, 3] = -np.dot(u, eye)
    mat[2, 3] = np.dot(f, eye)

    return mat


def perspective(fov: float, aspect: float, near: float, far: float) -> np.ndarray:
    """원근 투영 행렬

    Args:
        fov: Field of view (도)
        aspect: 종횡비
        near: Near clipping plane
        far: Far clipping plane

    Returns:
        4x4 projection matrix
    """
    fov_rad = np.radians(fov)
    f = 1.0 / np.tan(fov_rad / 2.0)

    mat = np.zeros((4, 4), dtype=np.float32)
    mat[0, 0] = f / aspect
    mat[1, 1] = f
    mat[2, 2] = (far + near) / (near - far)
    mat[2, 3] = (2.0 * far * near) / (near - far)
    mat[3, 2] = -1.0

    return mat
