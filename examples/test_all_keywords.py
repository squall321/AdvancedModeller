#!/usr/bin/env python3
"""
Comprehensive test script demonstrating usage of all implemented LS-DYNA keyword wrappers.

This script shows how to access and work with all keyword types supported by the kfile_parser.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.KooDynaKeyword import KFileReader


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")


def test_nodes(reader: KFileReader):
    """Test node access"""
    print_section("NODES")
    nodes = reader.get_nodes()
    node_array = nodes.getNodeList()

    print(f"Total nodes: {len(node_array)}")
    if len(node_array) > 0:
        print(f"\nFirst 3 nodes:")
        for i in range(min(3, len(node_array))):
            node = node_array[i]
            print(f"  Node {int(node[0])}: ({node[1]:.3f}, {node[2]:.3f}, {node[3]:.3f})")

        # Test node lookup by ID
        test_id = int(node_array[0][0])
        found_node = reader.get_node(test_id)
        if found_node:
            print(f"\nLookup test - Node {test_id}: Found ✓")


def test_parts(reader: KFileReader):
    """Test part access"""
    print_section("PARTS")
    parts = reader.get_parts()
    part_array = parts.getPartList()

    print(f"Total parts: {len(part_array)}")
    if len(part_array) > 0:
        print(f"\nFirst 3 parts:")
        for i in range(min(3, len(part_array))):
            part = part_array[i]
            print(f"  Part {int(part[0])}: SECID={int(part[1])}, MID={int(part[2])}")


def test_elements(reader: KFileReader):
    """Test element access"""
    print_section("ELEMENTS")

    # Shell elements
    shells = reader.get_element_shell()
    shell_array = shells.getShellElementList()
    print(f"Shell elements: {len(shell_array)}")
    if len(shell_array) > 0:
        shell = shell_array[0]
        print(f"  First shell: EID={int(shell[0])}, PID={int(shell[1])}, nodes={[int(shell[i]) for i in range(2, 6)]}")

    # Solid elements
    solids = reader.get_element_solid()
    solid_array = solids.getSolidElementList()
    print(f"Solid elements: {len(solid_array)}")
    if len(solid_array) > 0:
        solid = solid_array[0]
        print(f"  First solid: EID={int(solid[0])}, PID={int(solid[1])}, nodes={[int(solid[i]) for i in range(2, 10)]}")


def test_sets(reader: KFileReader):
    """Test set access"""
    print_section("SETS")
    sets = reader.get_sets()
    set_data = sets.sets

    print(f"Total sets: {len(set_data)}")
    if len(set_data) > 0:
        print(f"\nFirst 3 sets:")
        for i in range(min(3, len(set_data))):
            s = set_data[i]
            print(f"  Set {s.sid}: type={s.type}, title='{s.title}', {len(s.ids)} items")
            if s.segments:
                print(f"    {len(s.segments)} segments")


def test_sections(reader: KFileReader):
    """Test section access"""
    print_section("SECTIONS")
    sections = reader.get_sections()
    section_data = sections.sections

    print(f"Total sections: {len(section_data)}")
    if len(section_data) > 0:
        print(f"\nFirst 3 sections:")
        for i in range(min(3, len(section_data))):
            sec = section_data[i]
            print(f"  Section {sec.secid}: type={sec.type}, title='{sec.title}'")
            if sec.type == 'SHELL':
                print(f"    ELFORM={sec.elform}, thickness={sec.t1}")
            elif sec.type == 'SOLID':
                print(f"    ELFORM={sec.elform}")


def test_contacts(reader: KFileReader):
    """Test contact access"""
    print_section("CONTACTS")
    contacts = reader.get_contacts()
    contact_data = contacts.contacts

    print(f"Total contacts: {len(contact_data)}")
    if len(contact_data) > 0:
        print(f"\nFirst 3 contacts:")
        for i in range(min(3, len(contact_data))):
            c = contact_data[i]
            print(f"  Contact {c.ssid}: type='{c.contact_type}', title='{c.title}'")
            print(f"    SSID={c.ssid}, MSID={c.msid}, FS={c.fs}, FD={c.fd}")


def test_materials(reader: KFileReader):
    """Test material access"""
    print_section("MATERIALS")
    materials = reader.get_materials()
    material_data = materials.materials

    print(f"Total materials: {len(material_data)}")
    if len(material_data) > 0:
        print(f"\nFirst 3 materials:")
        for i in range(min(3, len(material_data))):
            mat = material_data[i]
            print(f"  Material {mat.mid}: type='{mat.material_type}', title='{mat.title}'")
            print(f"    RO={mat.ro}, E={mat.e}, PR={mat.pr}")


def test_curves(reader: KFileReader):
    """Test curve access"""
    print_section("CURVES")
    curves = reader.get_curves()
    curve_data = curves.curves

    print(f"Total curves: {len(curve_data)}")
    if len(curve_data) > 0:
        print(f"\nFirst 3 curves:")
        for i in range(min(3, len(curve_data))):
            curve = curve_data[i]
            print(f"  Curve {curve.lcid}: title='{curve.title}'")
            print(f"    {len(curve.abscissa)} points, SFA={curve.sfa}, SFO={curve.sfo}")


def test_boundaries(reader: KFileReader):
    """Test boundary condition access"""
    print_section("BOUNDARY CONDITIONS")
    boundaries = reader.get_boundaries()

    print(f"Boundary SPCs: {len(boundaries.boundary_spcs)}")
    if len(boundaries.boundary_spcs) > 0:
        spc = boundaries.boundary_spcs[0]
        print(f"  First SPC: NID={spc.nid}, DOF={spc.dof}")

    print(f"Prescribed motions: {len(boundaries.boundary_motions)}")
    if len(boundaries.boundary_motions) > 0:
        motion = boundaries.boundary_motions[0]
        print(f"  First motion: NID={motion.nid}, DOF={motion.dof}, LCID={motion.lcid}")


def test_loads(reader: KFileReader):
    """Test load access"""
    print_section("LOADS")
    loads = reader.get_loads()

    print(f"Node loads: {len(loads.load_nodes)}")
    if len(loads.load_nodes) > 0:
        load = loads.load_nodes[0]
        print(f"  First node load: NID={load.nid}, DOF={load.dof}, LCID={load.lcid}, SF={load.sf}")

    print(f"Segment loads: {len(loads.load_segments)}")
    if len(loads.load_segments) > 0:
        load = loads.load_segments[0]
        print(f"  First segment load: LCID={load.lcid}, SF={load.sf}, AT={load.at}")

    print(f"Body loads: {len(loads.load_bodies)}")
    if len(loads.load_bodies) > 0:
        load = loads.load_bodies[0]
        print(f"  First body load: LCID={load.lcid}, LCIDDR={load.lciddr}")


def test_controls(reader: KFileReader):
    """Test control keyword access"""
    print_section("CONTROL KEYWORDS")
    controls = reader.get_controls()

    print(f"Control terminations: {len(controls.control_terminations)}")
    if len(controls.control_terminations) > 0:
        ctrl = controls.control_terminations[0]
        print(f"  Endtim={ctrl.endtim}, Endcyc={ctrl.endcyc}")

    print(f"Control timesteps: {len(controls.control_timesteps)}")
    if len(controls.control_timesteps) > 0:
        ctrl = controls.control_timesteps[0]
        print(f"  DTINIT={ctrl.dtinit}, TSSFAC={ctrl.tssfac}")


def test_databases(reader: KFileReader):
    """Test database output access"""
    print_section("DATABASE OUTPUTS")
    databases = reader.get_databases()

    print(f"Binary databases: {len(databases.database_binaries)}")
    if len(databases.database_binaries) > 0:
        db = databases.database_binaries[0]
        print(f"  Type='{db.db_type}', DT={db.dt}")

    print(f"ASCII databases: {len(databases.database_asciis)}")
    if len(databases.database_asciis) > 0:
        db = databases.database_asciis[0]
        print(f"  Type='{db.db_type}', DT={db.dt}")

    print(f"History node outputs: {len(databases.database_history_nodes)}")
    print(f"History element outputs: {len(databases.database_history_elements)}")


def test_initials(reader: KFileReader):
    """Test initial condition access"""
    print_section("INITIAL CONDITIONS")
    initials = reader.get_initials()

    print(f"Initial velocities: {len(initials.initial_velocities)}")
    if len(initials.initial_velocities) > 0:
        init = initials.initial_velocities[0]
        print(f"  NSID={init.nsid}, STYP={init.styp}, VX={init.vx}, VY={init.vy}, VZ={init.vz}")


def test_constraineds(reader: KFileReader):
    """Test constrained keyword access"""
    print_section("CONSTRAINED KEYWORDS")
    constraineds = reader.get_constraineds()

    print(f"Nodal rigid bodies: {len(constraineds.constrained_nodal_rigid_bodies)}")
    if len(constraineds.constrained_nodal_rigid_bodies) > 0:
        rb = constraineds.constrained_nodal_rigid_bodies[0]
        print(f"  PID={rb.pid}, CID={rb.cid}, NSID={rb.nsid}, {len(rb.node_ids)} nodes")

    print(f"Joints: {len(constraineds.constrained_joints)}")
    if len(constraineds.constrained_joints) > 0:
        joint = constraineds.constrained_joints[0]
        print(f"  Type='{joint.joint_type}', JID={joint.jid}")

    print(f"Spotwelds: {len(constraineds.constrained_spotwelds)}")
    if len(constraineds.constrained_spotwelds) > 0:
        sw = constraineds.constrained_spotwelds[0]
        print(f"  Type='{sw.spotweld_type}', N1={sw.n1}, N2={sw.n2}")


def main():
    """Main test function"""
    kfile_path = os.path.join(os.path.dirname(__file__), 'DropSet.k')

    if not os.path.exists(kfile_path):
        print(f"Error: K-file not found at {kfile_path}")
        sys.exit(1)

    print(f"\nLoading K-file: {kfile_path}")
    print("=" * 80)

    # Parse the file
    reader = KFileReader(kfile_path)

    # Test all keyword types
    test_nodes(reader)
    test_parts(reader)
    test_elements(reader)
    test_sets(reader)
    test_sections(reader)
    test_contacts(reader)
    test_materials(reader)
    test_curves(reader)
    test_boundaries(reader)
    test_loads(reader)
    test_controls(reader)
    test_databases(reader)
    test_initials(reader)
    test_constraineds(reader)

    print("\n" + "=" * 80)
    print("  All keyword types tested successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
