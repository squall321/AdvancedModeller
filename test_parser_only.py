#!/usr/bin/env python3
"""Test K-file parser directly"""
import sys
sys.path.insert(0, 'core/kfile_parser')

from kfile_parser.wrapper import KFileParser

kfile = "examples/DropSet.k"

print(f"Testing parser on: {kfile}")
print("=" * 60)

parser = KFileParser(
    parse_nodes=True,
    parse_parts=True,
    parse_elements=True,
    parse_sets=False,
    parse_sections=False,
    parse_contacts=False,
    parse_materials=False,
    parse_includes=False,
    parse_curves=False,
)
parsed = parser.parse(kfile)

print(f"Parts: {len(parsed.parts)}")
print(f"Nodes: {len(parsed.nodes)}")
print(f"Elements: {len(parsed.elements)}")

if parsed.parts:
    print("\nAll parts:")
    for part in parsed.parts:
        name = getattr(part, 'name', getattr(part, 'title', f'Part {part.pid}'))
        print(f"  Part {part.pid}: {name}")

print("\nLooking for PKG parts...")
pkg_parts = []
for part in parsed.parts:
    name = getattr(part, 'name', getattr(part, 'title', ''))
    if 'PKG' in name.upper():
        pkg_parts.append(part)
        print(f"  ✓ Part {part.pid}: {name}")

print(f"\nFound {len(pkg_parts)} PKG parts")

if parsed.nodes:
    print(f"\nFirst 3 nodes:")
    for node in parsed.nodes[:3]:
        print(f"  Node {node.nid}: ({node.x}, {node.y}, {node.z})")

if parsed.elements:
    print(f"\nFirst 3 elements:")
    for elem in parsed.elements[:3]:
        print(f"  Element {elem.eid}: nodes={elem.nodes}, pid={elem.pid}")
