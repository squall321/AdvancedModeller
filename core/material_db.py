"""Material database loader - reuses logic from dyna_material_generator.py"""
import csv
import re
from typing import Dict, List
from dataclasses import dataclass
from pathlib import Path

def parse_value_with_unit(value_str: str) -> float:
    """Parse value with unit (GPa, MPa) and convert to MPa"""
    if not isinstance(value_str, str) or not value_str.strip():
        return 0.0

    value_str = value_str.strip()
    match = re.match(r'([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*([A-Za-z]*)', value_str)

    if not match:
        return float(value_str)

    value = float(match.group(1))
    unit = match.group(2).upper()

    if unit == 'GPA':
        return value * 1000.0
    elif unit == 'MPA':
        return value
    elif unit == 'KPA':
        return value / 1000.0
    elif unit == 'PA':
        return value / 1.0e6
    return value


@dataclass
class Material:
    """Material data"""
    name: str
    mat_type: str  # ELASTIC, VISCOELASTIC, ELASTOPLASTIC
    density: float
    modulus: float  # MPa
    add1: float = 0.0
    add2: float = 0.0
    add3: float = 0.0


class MaterialDatabase:
    """Material database loaded from MaterialSource.txt"""

    def __init__(self):
        self.materials: Dict[str, Material] = {}

    def load(self, filepath: str) -> bool:
        """Load materials from CSV file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['Name'].strip()
                    mat_type = row['type'].strip().upper()
                    density = float(row['Density'])
                    modulus = parse_value_with_unit(row['Modulus'])

                    add1 = parse_value_with_unit(row.get('add1', '0')) if row.get('add1') else 0.0
                    add2 = parse_value_with_unit(row.get('add2', '0')) if row.get('add2') else 0.0
                    add3 = parse_value_with_unit(row.get('add3', '0')) if row.get('add3') else 0.0

                    self.materials[name] = Material(
                        name=name,
                        mat_type=mat_type,
                        density=density,
                        modulus=modulus,
                        add1=add1,
                        add2=add2,
                        add3=add3
                    )
            return True
        except Exception as e:
            print(f"Error loading materials: {e}")
            return False

    def get_names(self) -> List[str]:
        """Get all material names"""
        return list(self.materials.keys())

    def get_type(self, name: str) -> str:
        """Get material type by name"""
        # Exact match
        if name in self.materials:
            return self.materials[name].mat_type

        # PSA/OCA variants
        if name.upper().startswith('PSA') or name.upper().startswith('OCA'):
            return 'VISCOELASTIC'

        # Prefix match
        for mat_name, mat in self.materials.items():
            if name.startswith(mat_name):
                return mat.mat_type

        return 'VISCOELASTIC'

    def get_material(self, name: str) -> Material:
        """Get material by name with flexible matching"""
        if name in self.materials:
            return self.materials[name]

        # Try prefix match
        for mat_name in self.materials:
            if name.startswith(mat_name):
                return self.materials[mat_name]

        # Try reverse prefix match
        for mat_name in self.materials:
            if mat_name.startswith(name):
                return self.materials[mat_name]

        raise KeyError(f"Material not found: {name}")

    def get_type_mapping(self) -> Dict[str, str]:
        """Get name -> type mapping for all materials"""
        return {name: mat.mat_type for name, mat in self.materials.items()}
