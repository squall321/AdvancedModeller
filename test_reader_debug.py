#!/usr/bin/env python3
"""Debug KFileReader to see what it parses"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.KooDynaKeyword import KFileReader

def test_reader():
    """Test KFileReader directly"""
    kfile = "examples/DropSet.k"

    print(f"Loading: {kfile}")
    print("=" * 80)

    reader = KFileReader(
        kfile,
        parse_nodes=True,
        parse_parts=True,
        parse_elements=True,
        parse_sets=True,
        parse_sections=True,
        parse_contacts=True,
        parse_materials=True,
        parse_includes=True,
        parse_curves=True,
        parse_boundaries=True,
        parse_loads=True,
        parse_controls=True,
        parse_databases=True,
        parse_initials=True,
        parse_constraineds=True,
    )

    # Get stats
    stats = reader.stats
    print(f"\nStats:")
    print(f"  Nodes: {stats.get('nodes', 0)}")
    print(f"  Parts: {stats.get('parts', 0)}")
    print(f"  Elements: {stats.get('elements', {})}")

    # Get parsed data
    parsed = reader._parsed
    print(f"\nParsed data:")
    print(f"  Type: {type(parsed)}")
    print(f"  Has elements: {hasattr(parsed, 'elements')}")

    if hasattr(parsed, 'elements'):
        elements = parsed.elements
        print(f"  Elements type: {type(elements)}")
        print(f"  Elements len: {len(elements) if hasattr(elements, '__len__') else 'N/A'}")

        # Try to get first few elements
        try:
            elements_list = list(elements)
            print(f"  Elements list len: {len(elements_list)}")

            if elements_list:
                print(f"\nFirst element:")
                elem = elements_list[0]
                print(f"    Type: {type(elem)}")
                print(f"    Attributes: {dir(elem)}")
                print(f"    Has element_type: {hasattr(elem, 'element_type')}")
                if hasattr(elem, 'element_type'):
                    print(f"    element_type: {elem.element_type}")
                if hasattr(elem, 'eid'):
                    print(f"    eid: {elem.eid}")
                if hasattr(elem, 'pid'):
                    print(f"    pid: {elem.pid}")
                if hasattr(elem, 'nodes'):
                    print(f"    nodes: {elem.nodes}")
        except Exception as e:
            print(f"  Error iterating elements: {e}")

    # Check parts
    if hasattr(parsed, 'parts'):
        parts = list(parsed.parts)
        print(f"\n  Parts count: {len(parts)}")
        if parts:
            part = parts[0]
            print(f"  First part: pid={part.pid}, name={getattr(part, 'name', 'N/A')}")

    # Check nodes
    if hasattr(parsed, 'nodes'):
        nodes = list(parsed.nodes)
        print(f"\n  Nodes count: {len(nodes)}")


if __name__ == "__main__":
    test_reader()
