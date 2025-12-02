"""Parser for display.txt files to restore configurations"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ParsedLayer:
    """Parsed layer info from display.txt"""
    material_name: str
    thickness: float
    layer_set: int


@dataclass
class ParsedPart:
    """Parsed part info from display.txt"""
    part_id: int
    layers: List[ParsedLayer]


class DisplayParser:
    """Parser for display.txt format files"""

    def parse(self, filepath: str) -> Tuple[str, List[ParsedPart]]:
        """
        Parse display.txt file.
        Returns: (k_filename, list of ParsedPart)
        """
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.split('\n')
        k_filename = ""
        parts: List[ParsedPart] = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Get input K file
            if line == '*Inputfile' and i + 1 < len(lines):
                k_filename = lines[i + 1].strip()
                i += 2
                continue

            # Parse PartExchange block
            if line.startswith('**PartExchange,'):
                part_id = int(line.split(',')[1])
                part_layers, end_idx = self._parse_part_block(lines, i + 1)
                if part_layers:
                    parts.append(ParsedPart(part_id=part_id, layers=part_layers))
                i = end_idx
                continue

            i += 1

        return k_filename, parts

    def _parse_part_block(self, lines: List[str], start: int) -> Tuple[List[ParsedLayer], int]:
        """Parse a single PartExchange block"""
        layers: List[ParsedLayer] = []
        material_names: Dict[int, str] = {}  # mid -> name
        thicknesses: Dict[int, float] = {}  # mid -> thickness

        i = start
        while i < len(lines):
            line = lines[i].strip()

            if line == '**EndPartExchange':
                break

            # Parse material title line: *MID01,*MAT_xxx_TITLE
            mid_match = re.match(r'\*MID(\d+),\*MAT_\w+_TITLE', line)
            if mid_match and i + 1 < len(lines):
                mid = int(mid_match.group(1))
                # Next line is material name
                mat_name = lines[i + 1].strip()
                material_names[mid] = mat_name
                i += 2
                continue

            # Parse thickness: *THK01,0.050
            thk_match = re.match(r'\*THK(\d+),(\d+\.?\d*)', line)
            if thk_match:
                mid = int(thk_match.group(1))
                thickness = float(thk_match.group(2))
                thicknesses[mid] = thickness
                i += 1
                continue

            i += 1

        # Build layer list from parsed data
        for mid in sorted(material_names.keys()):
            mat_name = material_names[mid]
            thickness = thicknesses.get(mid, 0.05)

            # Check if merged material (contains underscore from merge)
            if '_' in mat_name and not mat_name.startswith('_'):
                # Split merged materials
                sub_names = mat_name.split('_')
                sub_thickness = thickness / len(sub_names)
                for sub_name in sub_names:
                    layers.append(ParsedLayer(
                        material_name=sub_name,
                        thickness=sub_thickness,
                        layer_set=mid
                    ))
            else:
                layers.append(ParsedLayer(
                    material_name=mat_name,
                    thickness=thickness,
                    layer_set=mid
                ))

        return layers, i

    def to_part_configs(self, parsed_parts: List[ParsedPart]) -> Dict[int, List[dict]]:
        """
        Convert parsed parts to layer config dicts.
        Returns: {part_id: [layer_dict, ...]}
        """
        result = {}
        for part in parsed_parts:
            result[part.part_id] = [
                {
                    'material_name': layer.material_name,
                    'thickness': layer.thickness,
                    'layer_set': layer.layer_set
                }
                for layer in part.layers
            ]
        return result
