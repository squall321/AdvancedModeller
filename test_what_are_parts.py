#!/usr/bin/env python3
"""Check what parts 15, 20, 21 are"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from gui.app_context import AppContext
from gui.modules.model_viewer.core.mesh_data import MeshData

ctx = AppContext()
ctx.load_k_file("examples/DropSet.k")
mesh = MeshData.from_parsed_model(ctx.model)

print("Parts found as adjacent to PKG 1:")
for pid in [15, 20, 21]:
    name = mesh.part_names.get(pid, f"Part {pid}")
    bbox_data = []
    if pid in mesh.part_elements:
        elem_indices = mesh.part_elements[pid]
        node_indices = set()
        for elem_idx in elem_indices:
            node_list = mesh.elements[elem_idx]
            node_indices.update(node_list)

        if node_indices:
            coords = mesh.nodes[list(node_indices)]
            bbox_min = coords.min(axis=0)
            bbox_max = coords.max(axis=0)
            print(f"\nPart {pid}: {name}")
            print(f"  BBox: {bbox_min} ~ {bbox_max}")
            print(f"  Elements: {len(elem_indices)}")
