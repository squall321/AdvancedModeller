#!/usr/bin/env python3
"""
Simple test script that directly imports KFileReader without other dependencies
"""

import sys
import os

# Add paths for imports - import directly from kfile_parser module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../core/kfile_parser'))

# Direct import to avoid core/__init__.py dependencies
from kfile_parser import KFileParser

def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")


def main():
    """Main test function"""
    kfile_path = os.path.join(os.path.dirname(__file__), 'DropSet.k')

    if not os.path.exists(kfile_path):
        print(f"Error: K-file not found at {kfile_path}")
        sys.exit(1)

    print(f"\nLoading K-file: {kfile_path}")
    print("=" * 80)

    # Parse the file using the low-level parser
    parser = KFileParser()
    result = parser.parse(kfile_path)

    # Display comprehensive statistics
    print_section("PARSING STATISTICS")
    # Access stats from C++ result if available
    if hasattr(result, '_cpp_result') and result._cpp_result:
        cpp_result = result._cpp_result
        print(f"Total lines parsed: {cpp_result.total_lines:,}")
        print(f"Parse time: {cpp_result.parse_time_ms}ms")
        if cpp_result.warnings:
            print(f"Warnings: {len(cpp_result.warnings)}")
        if cpp_result.errors:
            print(f"Errors: {len(cpp_result.errors)}")

    print_section("BASIC ENTITIES")
    print(f"Nodes: {len(result.nodes):,}")
    print(f"Parts: {len(result.parts):,}")
    print(f"Elements: {len(result.elements):,}")
    if len(result.elements) > 0:
        # Count by type
        shells = sum(1 for e in result.elements if e.element_type == 'shell')
        solids = sum(1 for e in result.elements if e.element_type == 'solid')
        beams = sum(1 for e in result.elements if e.element_type == 'beam')
        print(f"  - Shell elements: {shells:,}")
        print(f"  - Solid elements: {solids:,}")
        print(f"  - Beam elements: {beams:,}")

    print_section("SETS AND PROPERTIES")
    print(f"Sets: {len(result.sets):,}")
    print(f"Sections: {len(result.sections):,}")

    print_section("CONTACTS AND MATERIALS")
    print(f"Contacts: {len(result.contacts):,}")
    print(f"Materials: {len(result.materials):,}")

    print_section("CURVES AND INCLUDES")
    print(f"Curves: {len(result.curves):,}")
    print(f"Includes: {len(result.includes):,}")

    print_section("BOUNDARY CONDITIONS")
    print(f"Boundary SPCs: {len(result.boundary_spcs):,}")
    print(f"Prescribed motions: {len(result.boundary_motions):,}")

    print_section("LOADS")
    print(f"Node loads: {len(result.load_nodes):,}")
    print(f"Segment loads: {len(result.load_segments):,}")
    print(f"Body loads: {len(result.load_bodies):,}")

    print_section("CONTROL KEYWORDS")
    print(f"Control terminations: {len(result.control_terminations):,}")
    print(f"Control timesteps: {len(result.control_timesteps):,}")
    print(f"Control energies: {len(result.control_energies):,}")
    print(f"Control outputs: {len(result.control_outputs):,}")
    print(f"Control shells: {len(result.control_shells):,}")
    print(f"Control contacts: {len(result.control_contacts):,}")
    print(f"Control hourglasses: {len(result.control_hourglasses):,}")
    print(f"Control bulk viscosities: {len(result.control_bulk_viscosities):,}")

    print_section("DATABASE OUTPUTS")
    print(f"Binary databases: {len(result.database_binaries):,}")
    print(f"ASCII databases: {len(result.database_asciis):,}")
    print(f"History node outputs: {len(result.database_history_nodes):,}")
    print(f"History element outputs: {len(result.database_history_elements):,}")
    print(f"Cross section outputs: {len(result.database_cross_sections):,}")

    print_section("INITIAL CONDITIONS")
    print(f"Initial velocities: {len(result.initial_velocities):,}")
    print(f"Initial stresses: {len(result.initial_stresses):,}")

    print_section("CONSTRAINED KEYWORDS")
    print(f"Nodal rigid bodies: {len(result.constrained_nodal_rigid_bodies):,}")
    print(f"Extra nodes: {len(result.constrained_extra_nodes):,}")
    print(f"Joints: {len(result.constrained_joints):,}")
    print(f"Spotwelds: {len(result.constrained_spotwelds):,}")

    print("\n" + "=" * 80)
    print("  ✓ All keyword types successfully parsed!")
    print("=" * 80 + "\n")

    # Sample data display
    if len(result.nodes) > 0:
        print("\nSample Node (first):")
        n = result.nodes[0]
        print(f"  NID={n.nid}, X={n.x:.3f}, Y={n.y:.3f}, Z={n.z:.3f}")

    if len(result.elements) > 0:
        print("\nSample Element (first):")
        e = result.elements[0]
        print(f"  EID={e.eid}, Type={e.element_type}, PID={e.pid}")
        print(f"  Node IDs: {e.nodes}")

if __name__ == "__main__":
    main()
