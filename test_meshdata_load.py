#!/usr/bin/env python3
"""Test MeshData loading from AppContext"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from gui.app_context import AppContext
from gui.modules.model_viewer.core.mesh_data import MeshData

def test_meshdata():
    """Test MeshData.from_parsed_model"""
    print("=" * 80)
    print("MeshData Loading Test")
    print("=" * 80)

    # Load via AppContext
    ctx = AppContext()
    kfile = "examples/DropSet.k"

    print(f"\n1. Loading {kfile} via AppContext...")
    success = ctx.load_k_file(kfile, use_fast_parser=True)
    print(f"   Success: {success}")

    if not ctx.model:
        print("ERROR: No model loaded")
        return

    print(f"\n2. Model stats:")
    print(f"   Parts: {ctx.model.part_count}")
    print(f"   Nodes: {ctx.model.node_count}")
    print(f"   Elements: {ctx.model.element_count}")

    elements = ctx.model.elements
    print(f"\n3. Model elements:")
    print(f"   Shell: {len(elements.get('shell', []))}")
    print(f"   Solid: {len(elements.get('solid', []))}")
    print(f"   Beam: {len(elements.get('beam', []))}")

    # Create MeshData
    print(f"\n4. Creating MeshData...")
    mesh_data = MeshData.from_parsed_model(ctx.model)

    if mesh_data is None:
        print("ERROR: MeshData.from_parsed_model returned None!")
        return

    print(f"   ✓ MeshData created")

    print(f"\n5. MeshData stats:")
    print(f"   Parts: {len(mesh_data.part_ids)}")
    print(f"   Nodes: {len(mesh_data.nodes)}")
    print(f"   Elements: {len(mesh_data.elements)}")

    # List parts with element counts
    print(f"\n6. Parts with elements:")
    for pid in sorted(mesh_data.part_ids)[:10]:  # First 10
        name = mesh_data.part_names.get(pid, f"Part {pid}")
        elem_count = len(mesh_data.part_elements.get(pid, []))
        print(f"   Part {pid:3d}: {name:30s} - {elem_count:6d} elements")

    # Find PKG parts
    pkg_parts = []
    for pid in mesh_data.part_ids:
        name = mesh_data.part_names.get(pid, "").upper()
        if "PKG" in name:
            pkg_parts.append((pid, mesh_data.part_names.get(pid, "")))

    print(f"\n7. PKG Parts ({len(pkg_parts)}):")
    for pid, name in pkg_parts:
        elem_count = len(mesh_data.part_elements.get(pid, []))
        print(f"   Part {pid}: {name} ({elem_count} elements)")

    print(f"\n{'=' * 80}")
    print("SUCCESS: MeshData loaded correctly!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    test_meshdata()
