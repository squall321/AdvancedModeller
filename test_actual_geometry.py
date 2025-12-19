#!/usr/bin/env python3
"""
Check actual 3D geometry vs 2D BBox projection issue
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from core.KooDynaKeyword import KFileReader
from gui.modules.adjacent_parts_viewer.core.detector import AdjacentPartsDetector
from gui.modules.adjacent_parts_viewer.core.doe_placement import DOEPlacementGenerator
from gui.modules.model_viewer.core.mesh_data import MeshData


def analyze_part_geometry(mesh_data, part_id, part_name):
    """Analyze actual 3D geometry of a part"""

    elem_indices = mesh_data.part_elements[part_id]
    part_node_indices = mesh_data.elements[elem_indices].flatten()
    part_nodes = mesh_data.nodes[part_node_indices]

    x_min, y_min, z_min = part_nodes.min(axis=0)
    x_max, y_max, z_max = part_nodes.max(axis=0)

    print(f"\nPart {part_id}: {part_name}")
    print(f"  Nodes: {len(part_nodes)}")
    print(f"  Elements: {len(elem_indices)}")
    print(f"  3D BBox:")
    print(f"    X: [{x_min:7.2f}, {x_max:7.2f}] → width:  {x_max-x_min:6.2f}mm")
    print(f"    Y: [{y_min:7.2f}, {y_max:7.2f}] → height: {y_max-y_min:6.2f}mm")
    print(f"    Z: [{z_min:7.2f}, {z_max:7.2f}] → thick:  {z_max-z_min:6.2f}mm")
    print(f"  Center: ({(x_min+x_max)/2:.2f}, {(y_min+y_max)/2:.2f}, {(z_min+z_max)/2:.2f})")

    # Check if it's a shell/surface (all elements share same Z)
    z_unique = np.unique(part_nodes[:, 2])
    if len(z_unique) <= 2:
        print(f"  Type: SURFACE/SHELL (Z values: {len(z_unique)})")
    else:
        print(f"  Type: SOLID (Z range: {z_unique.min():.2f} ~ {z_unique.max():.2f}mm)")

    return (x_min, y_min, z_min), (x_max, y_max, z_max)


def calculate_clearance_3d(bbox1, bbox2):
    """Calculate actual 3D clearance between two bboxes"""
    min1, max1 = bbox1
    min2, max2 = bbox2

    # X clearance
    if max1[0] < min2[0]:
        dx = min2[0] - max1[0]
    elif max2[0] < min1[0]:
        dx = min1[0] - max2[0]
    else:
        dx = 0  # Overlapping in X

    # Y clearance
    if max1[1] < min2[1]:
        dy = min2[1] - max1[1]
    elif max2[1] < min1[1]:
        dy = min1[1] - max2[1]
    else:
        dy = 0  # Overlapping in Y

    # Z clearance
    if max1[2] < min2[2]:
        dz = min2[2] - max1[2]
    elif max2[2] < min1[2]:
        dz = min1[2] - max2[2]
    else:
        dz = 0  # Overlapping in Z

    return dx, dy, dz


def main():
    print("="*70)
    print("Actual Geometry Analysis")
    print("="*70)

    # Load
    reader = KFileReader(
        "examples/DropSet.k",
        parse_nodes=True,
        parse_parts=True,
        parse_elements=True
    )

    parsed = reader._parsed
    nodes_list = list(parsed.nodes)
    elements_list = list(parsed.elements)
    parts_list = list(parsed.parts)

    nodes = np.array([[n.x, n.y, n.z] for n in nodes_list], dtype=np.float32)
    node_id_to_idx = {n.nid: i for i, n in enumerate(nodes_list)}

    part_elements = {}
    part_names = {}
    for part in parts_list:
        part_names[part.pid] = getattr(part, 'name', f'Part {part.pid}')
        part_elements[part.pid] = []

    elements = []
    for elem_idx, elem in enumerate(elements_list):
        node_indices = [node_id_to_idx.get(nid, 0) for nid in elem.nodes if nid != 0]
        elements.append(node_indices)
        if elem.pid in part_elements:
            part_elements[elem.pid].append(elem_idx)

    elements = np.array(elements, dtype=np.int32)
    bounds = (nodes.min(axis=0), nodes.max(axis=0))

    mesh_data = MeshData(
        nodes=nodes,
        elements=elements,
        part_elements=part_elements,
        part_names=part_names,
        element_type="solid",
        bounds=bounds
    )

    # Analyze Part 6 and its neighbors
    print("\n" + "="*70)
    print("Part 6 and Adjacent Parts Geometry")
    print("="*70)

    source_part = 6

    # Detect adjacent
    detector = AdjacentPartsDetector(mesh_data)
    result = detector.find_adjacent(
        source_part_id=source_part,
        plane='XY',
        thickness_min=0.0,
        thickness_max=50.0,
        check_facing=True,
        ray_density=0.1,
        coverage_threshold=0.1,
        visualize=False,
        layer_mode=True
    )

    adjacent_ids = list(result.adjacent_parts)

    # Filter coplanar
    generator = DOEPlacementGenerator(mesh_data, voxel_size=2.0)
    collision_parts, coplanar_parts = generator.filter_coplanar_parts(
        source_part_id=source_part,
        adjacent_part_ids=adjacent_ids,
        z_tolerance=1.0
    )

    # Analyze source
    source_bbox = analyze_part_geometry(mesh_data, source_part, part_names[source_part])

    # Analyze collision parts
    print(f"\n{'='*70}")
    print(f"Collision Parts (non-coplanar):")
    print(f"{'='*70}")

    collision_bboxes = {}
    for pid in collision_parts[:10]:  # First 10
        bbox = analyze_part_geometry(mesh_data, pid, part_names[pid])
        collision_bboxes[pid] = bbox

    # Calculate clearances
    print(f"\n{'='*70}")
    print(f"Clearances from Part 6:")
    print(f"{'='*70}")

    print(f"\n{'Part':<6} {'Name':<20} {'dX (mm)':<10} {'dY (mm)':<10} {'dZ (mm)':<10} {'XY Clear'}")
    print("-"*70)

    for pid in collision_parts[:10]:
        if pid not in collision_bboxes:
            continue

        dx, dy, dz = calculate_clearance_3d(source_bbox, collision_bboxes[pid])

        # XY clearance (2D)
        if dx == 0 and dy == 0:
            xy_clear = 0
        elif dx == 0:
            xy_clear = abs(dy)
        elif dy == 0:
            xy_clear = abs(dx)
        else:
            xy_clear = np.sqrt(dx**2 + dy**2)

        name = part_names.get(pid, '?')[:18]
        print(f"{pid:<6} {name:<20} {dx:>9.2f} {dy:>9.2f} {dz:>9.2f} {xy_clear:>9.2f}")

    # Find PKG parts specifically
    print(f"\n{'='*70}")
    print(f"PKG Parts Only:")
    print(f"{'='*70}")

    pkg_collision = [pid for pid in collision_parts if 'PKG' in part_names.get(pid, '').upper()]

    if pkg_collision:
        for pid in pkg_collision:
            if pid not in collision_bboxes:
                bbox = analyze_part_geometry(mesh_data, pid, part_names[pid])
                collision_bboxes[pid] = bbox

            dx, dy, dz = calculate_clearance_3d(source_bbox, collision_bboxes[pid])

            if dx == 0 and dy == 0:
                xy_clear = 0
            elif dx == 0:
                xy_clear = abs(dy)
            elif dy == 0:
                xy_clear = abs(dx)
            else:
                xy_clear = np.sqrt(dx**2 + dy**2)

            print(f"\nPart {pid}: {part_names[pid]}")
            print(f"  XY clearance: {xy_clear:.2f}mm")
            print(f"  Z clearance: {abs(dz):.2f}mm")

    else:
        print("No PKG parts in collision list!")
        print(f"\nAll PKG parts (including coplanar):")
        all_pkg = [pid for pid in part_names.keys() if 'PKG' in part_names[pid].upper()]
        for pid in all_pkg:
            if pid == source_part:
                continue
            is_coplanar = pid in coplanar_parts
            status = "(CO-PLANAR)" if is_coplanar else "(collision check)"
            print(f"  Part {pid}: {part_names[pid]} {status}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
