#!/usr/bin/env python3
"""Simple DropSet test with AppContext"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from gui.app_context import AppContext
from gui.modules.model_viewer.core.mesh_data import MeshData
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector

print("Loading DropSet.k via AppContext...")
ctx = AppContext()

success = ctx.load_k_file("examples/DropSet.k")
print(f"Load success: {success}")
print(f"Model loaded: {ctx.model.is_loaded}")
print(f"Part count: {ctx.model.part_count}")
print(f"Node count: {ctx.model.node_count}")
print(f"Element count: {ctx.model.element_count}")

if ctx.model.nodes:
    print(f"Actual nodes: {len(ctx.model.nodes)}")
else:
    print("Nodes is None or empty")

print(f"Shells: {ctx.model.shells if ctx.model.shells else 'None'}")
print(f"Elements: {ctx.model.elements if ctx.model.elements else 'None'}")
print(f"Solids: {ctx.model.solids if ctx.model.solids else 'None'}")

if ctx.model.shells:
    print(f"  Shells count: {len(ctx.model.shells)}")
if ctx.model.elements:
    print(f"  Elements count: {len(ctx.model.elements)}")
if ctx.model.solids:
    print(f"  Solids count: {len(ctx.model.solids)}")

# Create MeshData
mesh_data = MeshData.from_parsed_model(ctx.model)
print(f"\nMeshData parts: {len(mesh_data.part_elements)}")
print(f"Part IDs: {sorted(mesh_data.part_ids)[:10]}")

# Find PKG parts
pkg_count = 0
for pid in mesh_data.part_ids:
    name = mesh_data.part_names.get(pid, "")
    if 'PKG' in name.upper():
        pkg_count += 1
        print(f"  PKG Part {pid}: {name}")

print(f"\nTotal PKG parts: {pkg_count}")
