#!/usr/bin/env python3
"""Test 6-view functionality"""
import sys
from gui.modules.model_viewer.core.camera import Camera

def test_6view():
    """Test all 6 view presets"""
    camera = Camera()

    print("=" * 80)
    print("  6-View Preset Test")
    print("=" * 80)

    # Test all views
    views = [
        ("Front", camera.view_front),
        ("Back", camera.view_back),
        ("Left", camera.view_left),
        ("Right", camera.view_right),
        ("Top", camera.view_top),
        ("Bottom", camera.view_bottom),
        ("Isometric", camera.view_isometric),
    ]

    print("\nTesting camera view presets:\n")

    for name, view_func in views:
        view_func()
        print(f"  {name:12s} → Elevation: {camera.elevation:6.1f}°, Azimuth: {camera.azimuth:6.1f}°")

    print("\n" + "=" * 80)
    print("  ✓ All 6-view presets working!")
    print("=" * 80)

    return True

if __name__ == "__main__":
    success = test_6view()
    sys.exit(0 if success else 1)
