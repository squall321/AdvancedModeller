#!/usr/bin/env python3
"""Detailed AppContext debug"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from gui.app_context import AppContext

def test_appcontext():
    """Test AppContext loading in detail"""
    print("=" * 80)
    print("AppContext Detailed Debug")
    print("=" * 80)

    ctx = AppContext()
    kfile = "examples/DropSet.k"

    print(f"\n1. Loading: {kfile}")
    success = ctx.load_k_file(kfile, use_fast_parser=True)
    print(f"   Load success: {success}")

    if not ctx.model:
        print("ERROR: ctx.model is None!")
        return

    print(f"\n2. Model basic info:")
    print(f"   Part count: {ctx.model.part_count}")
    print(f"   Node count: {ctx.model.node_count}")
    print(f"   Element count: {ctx.model.element_count}")

    print(f"\n3. Model._reader:")
    print(f"   Type: {type(ctx.model._reader)}")
    print(f"   Has _parsed: {hasattr(ctx.model._reader, '_parsed')}")

    if hasattr(ctx.model._reader, '_parsed'):
        parsed = ctx.model._reader._parsed
        print(f"   _parsed type: {type(parsed)}")
        print(f"   _parsed is None: {parsed is None}")

        if parsed:
            print(f"   _parsed has elements: {hasattr(parsed, 'elements')}")
            if hasattr(parsed, 'elements'):
                elements_list = list(parsed.elements)
                print(f"   _parsed.elements count: {len(elements_list)}")
                if elements_list:
                    print(f"   First element type: {type(elements_list[0])}")
                    print(f"   First element_type: {elements_list[0].element_type}")

    print(f"\n4. Model.elements (via property):")
    elements_dict = ctx.model.elements
    print(f"   Type: {type(elements_dict)}")
    print(f"   Keys: {elements_dict.keys() if elements_dict else 'None'}")
    for key in ['shell', 'solid', 'beam']:
        count = len(elements_dict.get(key, [])) if elements_dict else 0
        print(f"   {key}: {count}")

    print(f"\n5. Model._elements_cache:")
    print(f"   Type: {type(ctx.model._elements_cache)}")
    if ctx.model._elements_cache:
        for key in ['shell', 'solid', 'beam']:
            count = len(ctx.model._elements_cache.get(key, []))
            print(f"   {key}: {count}")


if __name__ == "__main__":
    test_appcontext()
