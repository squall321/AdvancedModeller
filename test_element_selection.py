#!/usr/bin/env python3
"""Test script for element selection feature"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core', 'kfile_parser'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

from gui.modules.model_viewer.widgets.gl_widget import ModelGLWidget
from gui.modules.model_viewer.widgets.element_info import ElementInfoWidget
from gui.modules.model_viewer.core.mesh_data import MeshData
from core.kfile_parser.parser import KFileParser


def main():
    """Test element selection feature"""
    app = QApplication(sys.argv)

    # Find test file
    test_file = "examples/DropSet.k"
    if not os.path.exists(test_file):
        print(f"⚠️  Test file not found: {test_file}")
        return 1

    print(f"📂 Loading: {test_file}")

    # Parse K-file
    parser = KFileParser()
    parsed_data = parser.parse_file(test_file)

    if not parsed_data:
        print("❌ Failed to parse K-file")
        return 1

    print(f"✅ Parsed: {len(parsed_data.nodes)} nodes, {len(parsed_data.shells)} shells")

    # Create mesh data
    mesh = MeshData.from_parsed_model(parsed_data)
    print(f"✅ MeshData created: {len(mesh.nodes)} nodes, {len(mesh.elements)} elements")

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Element Selection Test - Click elements to select")
    window.resize(900, 600)

    central = QWidget()
    layout = QVBoxLayout(central)

    # Instructions
    instructions = QLabel("🖱️  Click on elements in the 3D view to select them\n"
                         "Selected elements will be highlighted in yellow\n"
                         "Element info will appear in the panel below")
    instructions.setAlignment(Qt.AlignCenter)
    instructions.setStyleSheet("padding: 10px; background: #f0f0f0; font-weight: bold;")
    layout.addWidget(instructions)

    # GL widget (use VBO backend for picking support)
    gl_widget = ModelGLWidget(backend='vbo')
    gl_widget.set_mesh(mesh)
    gl_widget.set_visible_parts(set(mesh.part_elements.keys()))

    # Connect selection signal
    def on_element_selected(elem_idx):
        print(f"✨ Element {elem_idx} selected!")
        status_label.setText(f"Selected: Element {elem_idx}")

    gl_widget.elementSelected.connect(on_element_selected)

    layout.addWidget(gl_widget, 3)

    # Element info widget
    element_info = ElementInfoWidget()
    element_info.set_mesh(mesh)
    gl_widget.elementSelected.connect(element_info.show_element)
    layout.addWidget(element_info, 1)

    # Status
    status_label = QLabel("Ready - Click an element to select")
    status_label.setStyleSheet("padding: 5px; background: palette(alternate-base);")
    layout.addWidget(status_label)

    window.setCentralWidget(central)
    window.show()

    print("\n" + "="*60)
    print("🚀 Element Selection Test Running")
    print("="*60)
    print("Instructions:")
    print("  1. Click on any element in the 3D view")
    print("  2. Selected element will be highlighted in yellow")
    print("  3. Element info will appear in the bottom panel")
    print("  4. Drag to rotate, Shift+Drag to pan, Wheel to zoom")
    print("="*60)

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
