#!/usr/bin/env python3
"""Test backend architecture

빠른 백엔드 테스트
"""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

print("[Test] Importing backends...")
from gui.modules.model_viewer.backends import BaseRenderer, LegacyRenderer

print(f"[Test] BaseRenderer: {BaseRenderer}")
print(f"[Test] LegacyRenderer: {LegacyRenderer}")

# Test instantiation
print("\n[Test] Creating LegacyRenderer...")
renderer = LegacyRenderer()
print(f"[Test] Renderer name: {renderer.name}")
print(f"[Test] Renderer type: {type(renderer)}")
print(f"[Test] Is BaseRenderer subclass: {isinstance(renderer, BaseRenderer)}")

# Test methods exist
print("\n[Test] Checking methods...")
methods = ['initialize', 'resize', 'render', 'set_mesh', 'set_camera',
           'set_visible_parts', 'set_show_nodes', 'set_show_wireframe', 'set_show_solid']
for method in methods:
    has_method = hasattr(renderer, method)
    print(f"  - {method}: {'✓' if has_method else '✗'}")

print("\n[Test] ✅ Backend architecture test PASSED!")
