"""렌더링 캐시 시스템

VBO 데이터 캐싱 및 부분 업데이트
"""
import numpy as np
from typing import Dict, Set, Optional, Tuple
from dataclasses import dataclass
import time


@dataclass
class VBOCache:
    """VBO 캐시 항목"""
    vbo_id: int  # OpenGL VBO ID
    vao_id: int  # OpenGL VAO ID
    vertex_count: int  # Vertex 개수
    data_hash: int  # 데이터 해시 (변경 감지)
    last_used: float  # 마지막 사용 시간
    memory_size: int  # 메모리 크기 (bytes)


class RenderCache:
    """렌더링 캐시 관리자

    Features:
    - VBO 재사용
    - 부분 업데이트
    - LRU 캐시
    - 메모리 관리
    """

    def __init__(self, max_memory_mb: int = 512):
        """
        Args:
            max_memory_mb: 최대 캐시 메모리 (MB)
        """
        self._cache: Dict[str, VBOCache] = {}
        self._max_memory = max_memory_mb * 1024 * 1024  # bytes
        self._current_memory = 0

    def get(self, key: str) -> Optional[VBOCache]:
        """캐시 항목 가져오기

        Args:
            key: 캐시 키 (예: "wireframe_part_123")

        Returns:
            캐시 항목 (없으면 None)
        """
        if key in self._cache:
            cache = self._cache[key]
            cache.last_used = time.time()
            return cache
        return None

    def put(self, key: str, cache: VBOCache):
        """캐시 항목 저장

        Args:
            key: 캐시 키
            cache: 캐시 항목
        """
        # 기존 항목 제거
        if key in self._cache:
            old_cache = self._cache[key]
            self._current_memory -= old_cache.memory_size

        # 메모리 부족 시 LRU 제거
        while self._current_memory + cache.memory_size > self._max_memory:
            self._evict_lru()

        # 저장
        self._cache[key] = cache
        self._current_memory += cache.memory_size

    def _evict_lru(self):
        """LRU (Least Recently Used) 항목 제거"""
        if not self._cache:
            return

        # 가장 오래 사용하지 않은 항목 찾기
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_used)
        lru_cache = self._cache.pop(lru_key)

        # OpenGL 리소스 삭제
        from OpenGL.GL import glDeleteBuffers, glDeleteVertexArrays
        glDeleteBuffers(1, [lru_cache.vbo_id])
        glDeleteVertexArrays(1, [lru_cache.vao_id])

        self._current_memory -= lru_cache.memory_size

        print(f"[Cache] Evicted LRU: {lru_key} ({lru_cache.memory_size / 1024 / 1024:.1f} MB)")

    def clear(self):
        """모든 캐시 제거"""
        from OpenGL.GL import glDeleteBuffers, glDeleteVertexArrays

        for cache in self._cache.values():
            glDeleteBuffers(1, [cache.vbo_id])
            glDeleteVertexArrays(1, [cache.vao_id])

        self._cache.clear()
        self._current_memory = 0

    def get_stats(self) -> Dict:
        """캐시 통계"""
        return {
            'items': len(self._cache),
            'memory_mb': self._current_memory / 1024 / 1024,
            'max_memory_mb': self._max_memory / 1024 / 1024,
            'usage_percent': (self._current_memory / self._max_memory) * 100 if self._max_memory > 0 else 0
        }


class PartBatcher:
    """Part별 렌더링 배치 최적화

    여러 Part를 하나의 VBO로 묶어 Draw call 감소
    """

    def __init__(self):
        self._batches: Dict[str, Set[int]] = {}  # batch_key -> part_ids

    def create_batch(self, part_ids: Set[int], element_type: str) -> str:
        """배치 생성

        Args:
            part_ids: Part ID 집합
            element_type: 'shell' or 'solid'

        Returns:
            배치 키
        """
        # 배치 키 생성 (정렬된 part_ids)
        sorted_ids = tuple(sorted(part_ids))
        batch_key = f"{element_type}_{hash(sorted_ids)}"

        self._batches[batch_key] = part_ids

        return batch_key

    def get_batch(self, batch_key: str) -> Optional[Set[int]]:
        """배치 가져오기"""
        return self._batches.get(batch_key)

    def needs_update(self, batch_key: str, current_parts: Set[int]) -> bool:
        """배치 업데이트 필요 여부

        Args:
            batch_key: 배치 키
            current_parts: 현재 표시할 Part ID들

        Returns:
            True if update needed
        """
        if batch_key not in self._batches:
            return True

        cached_parts = self._batches[batch_key]
        return cached_parts != current_parts


class VisibilityOptimizer:
    """가시성 최적화

    - Part별 가시성
    - Frustum culling 준비
    - Occlusion culling 준비
    """

    def __init__(self):
        self._visible_parts: Set[int] = set()
        self._part_bounds: Dict[int, Tuple[np.ndarray, np.ndarray]] = {}

    def set_visible_parts(self, part_ids: Set[int]):
        """표시할 Part 설정"""
        self._visible_parts = part_ids.copy()

    def set_part_bounds(self, part_id: int, min_bounds: np.ndarray, max_bounds: np.ndarray):
        """Part의 bounding box 설정"""
        self._part_bounds[part_id] = (min_bounds, max_bounds)

    def get_visible_parts(self) -> Set[int]:
        """표시할 Part ID 집합"""
        return self._visible_parts.copy()

    def is_visible(self, part_id: int) -> bool:
        """Part 가시성 확인"""
        return part_id in self._visible_parts

    def frustum_cull(self, frustum_planes: np.ndarray) -> Set[int]:
        """Frustum culling (향후 구현)

        Args:
            frustum_planes: 6개 평면 방정식

        Returns:
            보이는 Part ID 집합
        """
        # TODO: Frustum culling 구현
        # 지금은 모든 visible parts 반환
        return self._visible_parts.copy()


class PerformanceMonitor:
    """렌더링 성능 모니터링

    - FPS 추적
    - Draw call 카운트
    - 메모리 사용량
    - 병목 지점 식별
    """

    def __init__(self):
        self._frame_times = []
        self._max_samples = 60  # 1초치 (60 FPS 기준)

        self._draw_calls = 0
        self._vertices_rendered = 0

        self._start_time = None

    def frame_start(self):
        """프레임 시작"""
        self._start_time = time.time()
        self._draw_calls = 0
        self._vertices_rendered = 0

    def frame_end(self):
        """프레임 종료"""
        if self._start_time:
            frame_time = time.time() - self._start_time
            self._frame_times.append(frame_time)

            # 최대 샘플 수 유지
            if len(self._frame_times) > self._max_samples:
                self._frame_times.pop(0)

    def record_draw_call(self, vertex_count: int):
        """Draw call 기록

        Args:
            vertex_count: 렌더링된 vertex 수
        """
        self._draw_calls += 1
        self._vertices_rendered += vertex_count

    def get_fps(self) -> float:
        """현재 FPS"""
        if not self._frame_times:
            return 0.0

        avg_time = sum(self._frame_times) / len(self._frame_times)
        return 1.0 / avg_time if avg_time > 0 else 0.0

    def get_avg_frame_time(self) -> float:
        """평균 프레임 시간 (ms)"""
        if not self._frame_times:
            return 0.0

        return (sum(self._frame_times) / len(self._frame_times)) * 1000

    def get_stats(self) -> Dict:
        """성능 통계"""
        return {
            'fps': self.get_fps(),
            'avg_frame_time_ms': self.get_avg_frame_time(),
            'draw_calls': self._draw_calls,
            'vertices': self._vertices_rendered,
        }

    def reset(self):
        """통계 리셋"""
        self._frame_times.clear()
        self._draw_calls = 0
        self._vertices_rendered = 0
