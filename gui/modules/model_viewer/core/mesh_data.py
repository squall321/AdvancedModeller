"""Mesh data structure for 3D rendering

초고속 렌더링을 위한 최소 데이터 구조
"""
import numpy as np
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from gui.app_context import ParsedModelData


@dataclass
class MeshData:
    """3D 메쉬 데이터

    빠른 렌더링을 위해 numpy 배열 사용
    """
    # 노드 좌표: (N, 3) array - [x, y, z]
    nodes: np.ndarray

    # 요소 연결성: (M, 4 or 8) array - node indices
    # Shell: 4개, Solid: 8개
    elements: np.ndarray

    # Part별 요소 인덱스: {part_id: [elem_idx1, elem_idx2, ...]}
    part_elements: Dict[int, np.ndarray]

    # Part 정보: {part_id: part_name}
    part_names: Dict[int, str]

    # 요소 타입: 'shell' or 'solid'
    element_type: str

    # Bounding box: (min_xyz, max_xyz)
    bounds: Tuple[np.ndarray, np.ndarray]

    @property
    def part_ids(self) -> set:
        """Get set of all part IDs"""
        return set(self.part_elements.keys())

    @classmethod
    def from_parsed_model(cls, model: 'ParsedModelData') -> 'MeshData':
        """ParsedModelData에서 MeshData 생성

        빠른 변환을 위해 최소한의 처리만 수행
        """
        # 노드 데이터 추출
        nodes_list = model.nodes if model.nodes else []
        if not nodes_list:
            # 빈 메쉬
            return cls(
                nodes=np.zeros((0, 3), dtype=np.float32),
                elements=np.zeros((0, 4), dtype=np.int32),
                part_elements={},
                part_names={},
                element_type='shell',
                bounds=(np.zeros(3), np.zeros(3))
            )

        # 노드 ID -> 인덱스 매핑 및 좌표 추출 (최적화: 직접 numpy 생성)
        node_count = len(nodes_list)
        node_id_to_idx = {}
        nodes_array = np.empty((node_count, 3), dtype=np.float32)

        for idx, node in enumerate(nodes_list):
            node_id = getattr(node, 'nid', idx + 1)
            node_id_to_idx[node_id] = idx
            nodes_array[idx, 0] = getattr(node, 'x', 0.0)
            nodes_array[idx, 1] = getattr(node, 'y', 0.0)
            nodes_array[idx, 2] = getattr(node, 'z', 0.0)

        # Handle both dict structure (new parser) and legacy list structure
        elements_list = []
        elem_type = 'shell'
        nodes_per_elem = 4

        if hasattr(model, 'elements') and isinstance(model.elements, dict):
            # New parser returns dict: {'shell': [...], 'solid': [...]}
            elements_list = model.elements.get('solid', [])
            if elements_list:
                elem_type = 'solid'
                nodes_per_elem = 8
            else:
                elements_list = model.elements.get('shell', [])
                elem_type = 'shell'
                nodes_per_elem = 4
        else:
            # Legacy structure: model.shells and model.solids as lists
            elements_list = model.shells if model.shells else []
            elem_type = 'shell'
            nodes_per_elem = 4

            # Shell이 없으면 Solid 사용
            if not elements_list:
                elements_list = model.solids if model.solids else []
                elem_type = 'solid'
                nodes_per_elem = 8

        # 요소 데이터 추출 (최적화: 직접 numpy 생성)
        elem_count = len(elements_list)
        elements_array = np.empty((elem_count, nodes_per_elem), dtype=np.int32)
        part_elem_dict = {}

        for elem_idx, elem in enumerate(elements_list):
            # 노드 리스트 추출
            if elem_type == 'shell':
                node_list = getattr(elem, 'nodes', [0, 0, 0, 0])
            else:  # solid
                node_list = getattr(elem, 'nodes', [0] * 8)

            # 노드 ID를 인덱스로 변환하여 직접 배열에 저장
            for i in range(nodes_per_elem):
                nid = node_list[i] if i < len(node_list) else 0
                elements_array[elem_idx, i] = node_id_to_idx.get(int(nid), 0)

            # Part ID 추출
            pid = getattr(elem, 'pid', 0)
            if pid not in part_elem_dict:
                part_elem_dict[pid] = []
            part_elem_dict[pid].append(elem_idx)

        # Part별 요소 인덱스를 numpy 배열로 변환
        part_elements = {
            pid: np.array(indices, dtype=np.int32)
            for pid, indices in part_elem_dict.items()
        }

        # Part 이름 추출
        parts_list = model.parts if model.parts else []
        part_names = {}
        for part in parts_list:
            pid = getattr(part, 'pid', 0)
            name = getattr(part, 'name', f'Part {pid}')
            part_names[pid] = name if name else f'Part {pid}'

        # Part 이름이 없는 경우 기본값
        for pid in part_elements.keys():
            if pid not in part_names:
                part_names[pid] = f'Part {pid}'

        # Bounding box 계산
        if len(nodes_array) > 0:
            min_bounds = nodes_array.min(axis=0)
            max_bounds = nodes_array.max(axis=0)
        else:
            min_bounds = np.zeros(3)
            max_bounds = np.zeros(3)

        return cls(
            nodes=nodes_array,
            elements=elements_array,
            part_elements=part_elements,
            part_names=part_names,
            element_type=elem_type,
            bounds=(min_bounds, max_bounds)
        )

    def get_center(self) -> np.ndarray:
        """모델 중심점 반환"""
        return (self.bounds[0] + self.bounds[1]) / 2.0

    def get_size(self) -> float:
        """모델 크기 (대각선 길이) 반환"""
        return np.linalg.norm(self.bounds[1] - self.bounds[0])

    def get_visible_elements(self, visible_part_ids: set) -> np.ndarray:
        """표시할 요소 인덱스 반환

        Args:
            visible_part_ids: 표시할 Part ID 집합

        Returns:
            요소 인덱스 배열
        """
        if not visible_part_ids:
            return np.array([], dtype=np.int32)

        indices_list = []
        for pid in visible_part_ids:
            if pid in self.part_elements:
                indices_list.append(self.part_elements[pid])

        if indices_list:
            return np.concatenate(indices_list)
        return np.array([], dtype=np.int32)

    def extract_exterior_faces(self) -> Dict[int, List[Tuple]]:
        """외곽면만 추출 (내부 폴리곤 제거)

        Solid 요소의 경우 인접 요소와 공유하는 면은 내부면이므로 제외
        Shell 요소는 이미 외곽면이므로 그대로 유지

        Returns:
            {part_id: [(elem_idx, face_indices), ...]}
            face_indices: Shell은 [0,1,2,3], Hex는 면별 인덱스
        """
        if self.element_type == 'shell':
            # Shell은 이미 외곽면
            result = {}
            for pid, elem_indices in self.part_elements.items():
                result[pid] = [(idx, [0, 1, 2, 3]) for idx in elem_indices]
            return result

        # Solid 요소: 면 해싱으로 외곽면 추출
        # 최적화: elem_idx -> part_id 역매핑 생성
        elem_to_part = {}
        for pid, elem_indices in self.part_elements.items():
            for elem_idx in elem_indices:
                elem_to_part[int(elem_idx)] = pid

        face_count = {}  # {sorted_face_tuple: count}
        face_to_elem = {}  # {sorted_face_tuple: (elem_idx, face_idx)}

        hex_faces = [
            [0, 1, 2, 3],  # Bottom
            [4, 5, 6, 7],  # Top
            [0, 1, 5, 4],  # Front
            [2, 3, 7, 6],  # Back
            [0, 3, 7, 4],  # Left
            [1, 2, 6, 5],  # Right
        ]

        # 모든 면을 해싱
        for elem_idx, node_indices in enumerate(self.elements):
            if len(node_indices) != 8:
                continue
            for face_idx, face_def in enumerate(hex_faces):
                # 면을 구성하는 노드 인덱스
                face_nodes = tuple(sorted([node_indices[i] for i in face_def]))
                face_count[face_nodes] = face_count.get(face_nodes, 0) + 1
                face_to_elem[face_nodes] = (elem_idx, face_idx)

        # 카운트가 1인 면만 외곽면 (공유되지 않은 면)
        exterior_faces = {}
        for face_nodes, count in face_count.items():
            if count == 1:
                elem_idx, face_idx = face_to_elem[face_nodes]
                # Part ID를 O(1)로 찾기
                pid = elem_to_part.get(elem_idx)
                if pid is not None:
                    if pid not in exterior_faces:
                        exterior_faces[pid] = []
                    exterior_faces[pid].append((elem_idx, hex_faces[face_idx]))

        return exterior_faces
