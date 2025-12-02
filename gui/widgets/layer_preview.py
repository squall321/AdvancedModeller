"""Layer preview widget - visual representation of laminate stack"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolTip
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics
from typing import List, Dict, Optional, Tuple
from models import LayerConfig
from gui.styles.theme import Theme

# Direction labels based on vector
DIRECTION_LABELS = {
    (0, 1, 0): ("Bottom-Up ↑", "BOTTOM", "TOP"),
    (0, -1, 0): ("Top-Down ↓", "TOP", "BOTTOM"),
    (1, 0, 0): ("Left-Right →", "LEFT", "RIGHT"),
    (-1, 0, 0): ("Right-Left ←", "RIGHT", "LEFT"),
    (0, 0, 1): ("Front-Back", "FRONT", "BACK"),
    (0, 0, -1): ("Back-Front", "BACK", "FRONT"),
}

class LayerPreviewWidget(QWidget):
    """Visual preview of laminate layer stack"""

    # Material type to color mapping
    MATERIAL_COLORS = {
        'ELASTIC': Theme.MAT_ELASTIC,
        'VISCOELASTIC': Theme.MAT_VISCOELASTIC,
        'ELASTOPLASTIC': Theme.MAT_ELASTOPLASTIC,
        'PSA': Theme.MAT_PSA,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layers: List[LayerConfig] = []
        self.material_types: Dict[str, str] = {}  # name -> type mapping
        self.material_db = None  # Reference to MaterialDatabase
        self._stack_direction: Tuple[float, float, float] = (0, 1, 0)
        self._stack_angle: float = 5.0
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self._hovered_layer: int = -1

    def set_material_types(self, material_types: Dict[str, str]):
        """Set material name to type mapping"""
        self.material_types = material_types

    def set_material_db(self, material_db):
        """Set material database for tooltip display"""
        self.material_db = material_db

    def set_layers(self, layers: List[LayerConfig]):
        """Update layers and repaint"""
        self.layers = layers
        self.update()

    def set_stack_settings(self, direction: Tuple[float, float, float], angle: float):
        """Set stack direction and angle"""
        self._stack_direction = direction
        self._stack_angle = angle
        self.update()

    def _get_direction_labels(self) -> Tuple[str, str, str]:
        """Get direction name and start/end labels based on current direction"""
        # Convert to tuple of ints for lookup
        dir_key = (int(self._stack_direction[0]),
                   int(self._stack_direction[1]),
                   int(self._stack_direction[2]))
        if dir_key in DIRECTION_LABELS:
            return DIRECTION_LABELS[dir_key]
        # Custom direction
        return (f"Custom ({self._stack_direction[0]},{self._stack_direction[1]},{self._stack_direction[2]})",
                "START", "END")

    def paintEvent(self, event):
        if not self.layers:
            self._draw_empty()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        margin = 20
        label_width = 80
        thickness_width = 60

        # Drawing area
        draw_x = margin
        draw_width = width - 2 * margin - label_width - thickness_width
        draw_height = height - 2 * margin - 40  # Reserve space for labels

        # Calculate total thickness and scale
        total_thickness = sum(l.thickness for l in self.layers)
        if total_thickness <= 0:
            return

        # Get direction labels
        dir_name, start_label, end_label = self._get_direction_labels()

        # Draw layers (bottom to top, so reverse order in display)
        y_offset = margin + 20  # Start after top label

        # Draw end label (top of stack - where layers end)
        painter.setPen(QColor(Theme.TEXT_DIM))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(margin, margin + 12, end_label)

        # Draw layers
        for i, layer in enumerate(reversed(self.layers)):
            layer_height = max(20, (layer.thickness / total_thickness) * draw_height)

            # Get color based on material type
            mat_type = self._get_material_type(layer.material_name)
            color = QColor(self.MATERIAL_COLORS.get(mat_type, Theme.MAT_PSA))

            # Highlight hovered layer
            actual_idx = len(self.layers) - 1 - i
            if actual_idx == self._hovered_layer:
                color = color.lighter(130)

            # Draw layer rectangle
            rect = QRectF(draw_x, y_offset, draw_width, layer_height)

            # Fill
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#374151"), 1))
            painter.drawRoundedRect(rect, 4, 4)

            # Layer name (centered)
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            fm = QFontMetrics(painter.font())
            text = layer.material_name
            text_rect = fm.boundingRect(text)

            if text_rect.width() < draw_width - 10 and layer_height > 18:
                text_x = draw_x + (draw_width - text_rect.width()) / 2
                text_y = y_offset + (layer_height + text_rect.height()) / 2 - 2
                painter.drawText(int(text_x), int(text_y), text)

            # Thickness label (right side)
            painter.setPen(QColor(Theme.TEXT_DIM))
            painter.setFont(QFont("Segoe UI", 9))
            thickness_text = f"{layer.thickness:.3f}"
            painter.drawText(int(draw_x + draw_width + 10), int(y_offset + layer_height / 2 + 4), thickness_text)

            # Draw merge indicator (dashed border for same layer_set)
            if i > 0:
                prev_layer = list(reversed(self.layers))[i - 1]
                if prev_layer.layer_set == layer.layer_set:
                    pen = QPen(QColor(Theme.WARNING), 2, Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawLine(int(draw_x), int(y_offset), int(draw_x + draw_width), int(y_offset))

            y_offset += layer_height

        # Draw start label (bottom of stack - where layers start)
        painter.setPen(QColor(Theme.TEXT_DIM))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(margin, int(y_offset + 15), start_label)

        # Draw direction and angle info (right side, top)
        painter.setPen(QColor(Theme.PRIMARY))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        dir_info = f"{dir_name}  {self._stack_angle}°"
        fm = QFontMetrics(painter.font())
        dir_width = fm.horizontalAdvance(dir_info)
        painter.drawText(int(width - margin - dir_width), margin + 12, dir_info)

        # Draw total thickness
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(QColor(Theme.TEXT))
        summary = f"총 두께: {total_thickness:.3f} mm  |  레이어: {len(self.layers)}개"
        painter.drawText(margin, height - 8, summary)

    def _draw_empty(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(Theme.TEXT_DIM))
        painter.setFont(QFont("Segoe UI", 12))

        text = "레이어를 추가하세요"
        fm = QFontMetrics(painter.font())
        text_rect = fm.boundingRect(text)
        x = (self.width() - text_rect.width()) / 2
        y = (self.height() + text_rect.height()) / 2
        painter.drawText(int(x), int(y), text)

    def _get_material_type(self, material_name: str) -> str:
        """Get material type from name"""
        # Check exact match first
        if material_name in self.material_types:
            return self.material_types[material_name]

        # Check if it's a PSA variant
        if material_name.upper().startswith('PSA') or material_name.upper().startswith('OCA'):
            return 'PSA'

        # Try prefix match
        for name, mat_type in self.material_types.items():
            if material_name.startswith(name):
                return mat_type

        return 'VISCOELASTIC'  # Default

    def mouseMoveEvent(self, event):
        """Track mouse for hover effects and show tooltip"""
        if not self.layers:
            return

        # Calculate which layer is hovered
        margin = 20
        y_offset = margin + 20
        draw_height = self.height() - 2 * margin - 40
        total_thickness = sum(l.thickness for l in self.layers)

        mouse_y = event.position().y()
        prev_hovered = self._hovered_layer
        self._hovered_layer = -1

        for i, layer in enumerate(reversed(self.layers)):
            layer_height = max(20, (layer.thickness / total_thickness) * draw_height)
            if y_offset <= mouse_y <= y_offset + layer_height:
                self._hovered_layer = len(self.layers) - 1 - i
                break
            y_offset += layer_height

        # Show tooltip if hovering over a layer
        if self._hovered_layer >= 0:
            layer = self.layers[self._hovered_layer]
            tooltip_text = self._get_material_tooltip(layer.material_name, layer.thickness)
            QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
        else:
            QToolTip.hideText()

        if prev_hovered != self._hovered_layer:
            self.update()

    def _get_material_tooltip(self, material_name: str, thickness: float) -> str:
        """Generate tooltip text based on material type"""
        lines = [f"<b>{material_name}</b>", f"두께: {thickness:.3f} mm"]

        if self.material_db:
            try:
                mat = self.material_db.get_material(material_name)
                lines.append(f"<hr>")
                lines.append(f"타입: <b>{mat.mat_type}</b>")
                lines.append(f"밀도: {mat.density:.3f} g/cm³")

                if mat.mat_type == 'ELASTIC':
                    lines.append(f"<hr>")
                    lines.append(f"탄성계수 E: {mat.modulus:.1f} MPa")
                    lines.append(f"포아송비 ν: {mat.add1:.3f}")

                elif mat.mat_type == 'ELASTOPLASTIC':
                    lines.append(f"<hr>")
                    lines.append(f"탄성계수 E: {mat.modulus:.1f} MPa")
                    lines.append(f"포아송비 ν: {mat.add1:.3f}")
                    lines.append(f"항복응력 σy: {mat.add2:.1f} MPa")
                    lines.append(f"접선계수 Et: {mat.add3:.1f} MPa")

                else:  # VISCOELASTIC
                    lines.append(f"<hr>")
                    lines.append(f"체적탄성계수 K: {mat.modulus:.1f} MPa")
                    lines.append(f"전단탄성계수 G0: {mat.add1:.3f} MPa")
                    lines.append(f"장기전단계수 Gi: {mat.add2:.3f} MPa")
                    lines.append(f"감쇠계수 β: {mat.add3:.4f}")

            except KeyError:
                lines.append(f"<i>(물성 정보 없음)</i>")

        return "<br>".join(lines)

    def leaveEvent(self, event):
        self._hovered_layer = -1
        QToolTip.hideText()
        self.update()
