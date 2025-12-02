#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LS-DYNA Material Card Generator
Supports ELASTIC, GENERAL_VISCOELASTIC (MAT 006), and BILINEAR ELASTOPLASTIC materials
"""

import csv
import re
import sys
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass


# =============================================================================
# Configuration
# =============================================================================

# Default minimum shear modulus for numerical stability (MPa)
# Values below this threshold can cause negative volume in LS-DYNA
DEFAULT_MIN_SHEAR_MODULUS = 1.0  # MPa


# =============================================================================
# Unit Conversion Utilities
# =============================================================================

def parse_value_with_unit(value_str: str) -> float:
    """
    Parse value with unit (GPa, MPa, KPa) and convert to base units (MPa for stress, ton/mm^3 for density)
    
    Args:
        value_str: String containing value and unit (e.g., "70GPa", "250MPa")
    
    Returns:
        float: Converted value in MPa
    """
    if not isinstance(value_str, str) or not value_str.strip():
        return 0.0
    
    value_str = value_str.strip()
    
    # Extract number and unit
    match = re.match(r'([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*([A-Za-z]*)', value_str)
    
    if not match:
        return float(value_str)
    
    value = float(match.group(1))
    unit = match.group(2).upper()
    
    # Convert to MPa (LS-DYNA standard: ton-mm-s-K system uses MPa)
    if unit == 'GPA':
        return value * 1000.0  # GPa to MPa
    elif unit == 'MPA':
        return value
    elif unit == 'KPA':
        return value / 1000.0  # KPa to MPa
    elif unit == 'PA':
        return value / 1.0e6  # Pa to MPa
    else:
        return value


def density_to_dyna_unit(density_gcc: float) -> float:
    """
    Convert density from g/cm^3 to ton/mm^3 (LS-DYNA ton-mm-s system)
    
    Args:
        density_gcc: Density in g/cm^3
    
    Returns:
        float: Density in ton/mm^3
    """
    # 1 g/cm^3 = 1e-9 ton/mm^3
    return density_gcc * 1.0e-9


# =============================================================================
# Material Classes
# =============================================================================

@dataclass
class Material:
    """Base material class"""
    name: str
    density: float  # g/cm^3
    mat_type: str
    
    def to_dyna_card(self, mat_id: int) -> str:
        """Generate LS-DYNA material card"""
        raise NotImplementedError


@dataclass
class ElasticMaterial(Material):
    """Elastic material (MAT_ELASTIC)"""
    elastic_modulus: float  # MPa
    poisson_ratio: float
    
    def to_dyna_card(self, mat_id: int) -> str:
        """Generate LS-DYNA MAT_ELASTIC card"""
        rho = density_to_dyna_unit(self.density)
        E = self.elastic_modulus
        nu = self.poisson_ratio
        
        card = f"*MAT_ELASTIC_TITLE\n"
        card += f"{self.name}\n"
        card += f"$#     mid       rho         e        pr\n"
        card += f"{mat_id:>10d}{rho:>10.4e}{E:>10.3e}{nu:>10.4f}\n"
        return card


@dataclass
class ElastoplasticMaterial(Material):
    """Bilinear elastoplastic material (MAT_PLASTIC_KINEMATIC)"""
    elastic_modulus: float  # MPa
    poisson_ratio: float
    yield_stress: float  # MPa
    tangent_modulus: float  # MPa
    
    def to_dyna_card(self, mat_id: int) -> str:
        """Generate LS-DYNA MAT_PLASTIC_KINEMATIC card"""
        rho = density_to_dyna_unit(self.density)
        E = self.elastic_modulus
        nu = self.poisson_ratio
        sigy = self.yield_stress
        etan = self.tangent_modulus
        
        card = f"*MAT_PLASTIC_KINEMATIC_TITLE\n"
        card += f"{self.name}\n"
        card += f"$#     mid       rho         e        pr      sigy      etan\n"
        card += f"{mat_id:>10d}{rho:>10.4e}{E:>10.3e}{nu:>10.4f}{sigy:>10.3e}{etan:>10.3e}\n"
        return card


@dataclass
class ViscoelasticMaterial(Material):
    """General viscoelastic material (MAT_VISCOELASTIC)"""
    bulk_modulus: float  # MPa
    G0: float  # Short-time shear modulus, MPa
    GI: float  # Long-time shear modulus, MPa
    beta: float  # Decay constant
    
    def to_dyna_card(self, mat_id: int) -> str:
        """Generate LS-DYNA MAT_VISCOELASTIC (MAT 006) card"""
        rho = density_to_dyna_unit(self.density)
        K = self.bulk_modulus
        g0 = self.G0
        gi = self.GI
        
        card = f"*MAT_VISCOELASTIC_TITLE\n"
        card += f"{self.name}\n"
        card += f"$#     mid       rho      bulk        g0        gi      beta\n"
        card += f"{mat_id:>10d}{rho:>10.4e}{K:>10.3e}{g0:>10.3e}{gi:>10.3e}{self.beta:>10.4f}\n"
        return card


# =============================================================================
# Material Database Manager
# =============================================================================

class MaterialDatabase:
    """Material database loaded from MaterialSource.txt"""
    
    def __init__(self, min_shear_modulus: float = DEFAULT_MIN_SHEAR_MODULUS):
        self.materials: Dict[str, Material] = {}
        self.min_shear_modulus = min_shear_modulus
    
    def load_from_file(self, filename: str):
        """Load materials from CSV file"""
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['Name'].strip()
                density = float(row['Density'])
                mat_type = row['type'].strip().upper()
                
                if mat_type == 'ELASTIC':
                    modulus = parse_value_with_unit(row['Modulus'])
                    poisson = float(row['add1'])
                    mat = ElasticMaterial(
                        name=name,
                        density=density,
                        mat_type=mat_type,
                        elastic_modulus=modulus,
                        poisson_ratio=poisson
                    )
                
                elif mat_type == 'ELASTOPLASTIC':
                    modulus = parse_value_with_unit(row['Modulus'])
                    poisson = float(row['add1'])
                    yield_stress = parse_value_with_unit(row['add2'])
                    tangent_mod = parse_value_with_unit(row['add3'])
                    mat = ElastoplasticMaterial(
                        name=name,
                        density=density,
                        mat_type=mat_type,
                        elastic_modulus=modulus,
                        poisson_ratio=poisson,
                        yield_stress=yield_stress,
                        tangent_modulus=tangent_mod
                    )
                
                elif mat_type == 'VISCOELASTIC':
                    bulk_modulus = parse_value_with_unit(row['Modulus'])
                    g0 = parse_value_with_unit(row['add1'])
                    gi = parse_value_with_unit(row['add2'])
                    beta = float(row['add3'])
                    
                    # Apply minimum shear modulus for numerical stability
                    # Maintain viscoelastic behavior: G0 >= GI
                    g0_original = g0
                    gi_original = gi
                    
                    # First clamp GI to minimum
                    gi = max(gi, self.min_shear_modulus)
                    
                    # Then ensure G0 is at least as large as GI (and at least the minimum)
                    # Use a ratio to preserve viscoelastic character
                    if g0_original > gi_original:
                        ratio = g0_original / gi_original
                        g0 = max(gi * ratio, self.min_shear_modulus)
                    else:
                        # If originally G0 <= GI, just use minimum for both
                        g0 = max(g0, gi)
                    
                    if g0 != g0_original or gi != gi_original:
                        print(f"  WARNING: {name} - Shear modulus adjusted for numerical stability")
                        print(f"           Original: G0={g0_original:.4f}, GI={gi_original:.4f} MPa (ratio={g0_original/gi_original:.2f})")
                        print(f"           Applied:  G0={g0:.4f}, GI={gi:.4f} MPa (ratio={g0/gi:.2f})")
                        print(f"           Min threshold: {self.min_shear_modulus} MPa")
                    
                    mat = ViscoelasticMaterial(
                        name=name,
                        density=density,
                        mat_type=mat_type,
                        bulk_modulus=bulk_modulus,
                        G0=g0,
                        GI=gi,
                        beta=beta
                    )
                
                else:
                    raise ValueError(f"Unknown material type: {mat_type}")
                
                self.materials[name] = mat
    
    def get_material(self, name: str) -> Material:
        """Get material by name with flexible matching"""
        # Try exact match first
        if name in self.materials:
            return self.materials[name]
        
        # Try to find material that starts with the given name
        # (e.g., "Panel" matches "Panel-F" or "Panel-PI")
        candidates = [mat_name for mat_name in self.materials if mat_name.startswith(name)]
        if candidates:
            # Return first match, preferring shortest name
            return self.materials[sorted(candidates, key=len)[0]]
        
        # Try partial match in reverse (for cases like PSA0, PSA1 matching a base PSA)
        for mat_name in self.materials:
            if name.startswith(mat_name):
                return self.materials[mat_name]
        
        raise KeyError(f"Material not found: {name}")


# =============================================================================
# Laminate Layer and Merging Logic
# =============================================================================

@dataclass
class LaminateLayer:
    """Single layer in laminate"""
    material_name: str
    thickness: float  # mm
    layer_set: int
    part_id: int = 0  # Part ID for grouping multiple layers


class LaminateMerger:
    """Merge laminate layers using Voigt (bulk) and Reuss (shear) models"""
    
    def __init__(self, mat_db: MaterialDatabase):
        self.mat_db = mat_db
    
    def load_laminate_from_csv(self, filename: str) -> List[LaminateLayer]:
        """Load laminate configuration from CSV"""
        layers = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    mat_name = row[0].strip()
                    thickness = float(row[1])
                    layer_set = int(row[2])
                    part_id = int(row[3]) if len(row) >= 4 else 0
                    layers.append(LaminateLayer(mat_name, thickness, layer_set, part_id))
        return layers
    
    def merge_layers_by_set(self, layers: List[LaminateLayer]) -> Dict[int, Material]:
        """
        Merge layers with same layer_set number
        Single layer: keep original material type with actual layer name
        Multiple layers: merge into viscoelastic material using Voigt/Reuss model
        """
        # Group layers by set number
        layer_sets = {}
        for layer in layers:
            if layer.layer_set not in layer_sets:
                layer_sets[layer.layer_set] = []
            layer_sets[layer.layer_set].append(layer)
        
        # Process each set
        merged_materials = {}
        for set_num, set_layers in layer_sets.items():
            if len(set_layers) == 1:
                # Single layer: keep original material type with actual layer name
                layer = set_layers[0]
                mat = self.mat_db.get_material(layer.material_name)
                # Create a copy with the actual layer name (not the material database name)
                mat_copy = self._copy_material_with_name(mat, layer.material_name)
                merged_materials[set_num] = mat_copy
            else:
                # Multiple layers: merge into viscoelastic
                merged_mat = self._merge_single_set(set_num, set_layers)
                merged_materials[set_num] = merged_mat
        
        return merged_materials
    
    def _copy_material_with_name(self, mat: Material, new_name: str) -> Material:
        """Create a copy of material with a new name"""
        if isinstance(mat, ElasticMaterial):
            return ElasticMaterial(
                name=new_name,
                density=mat.density,
                mat_type=mat.mat_type,
                elastic_modulus=mat.elastic_modulus,
                poisson_ratio=mat.poisson_ratio
            )
        elif isinstance(mat, ElastoplasticMaterial):
            return ElastoplasticMaterial(
                name=new_name,
                density=mat.density,
                mat_type=mat.mat_type,
                elastic_modulus=mat.elastic_modulus,
                poisson_ratio=mat.poisson_ratio,
                yield_stress=mat.yield_stress,
                tangent_modulus=mat.tangent_modulus
            )
        elif isinstance(mat, ViscoelasticMaterial):
            return ViscoelasticMaterial(
                name=new_name,
                density=mat.density,
                mat_type=mat.mat_type,
                bulk_modulus=mat.bulk_modulus,
                G0=mat.G0,
                GI=mat.GI,
                beta=mat.beta
            )
        else:
            return mat
    
    def _merge_single_set(self, set_num: int, layers: List[LaminateLayer]) -> ViscoelasticMaterial:
        """Merge a single set of layers"""
        total_thickness = sum(layer.thickness for layer in layers)
        
        # Volume fraction for each layer
        volume_fractions = [layer.thickness / total_thickness for layer in layers]
        
        # Convert all materials to equivalent viscoelastic properties
        bulk_moduli = []
        g0_values = []
        gi_values = []
        beta_values = []
        densities = []
        layer_names = []  # Store actual layer names from CSV
        
        for layer, vf in zip(layers, volume_fractions):
            mat = self.mat_db.get_material(layer.material_name)
            layer_names.append(layer.material_name)  # Use actual layer name, not material DB name
            densities.append(mat.density)
            
            if isinstance(mat, ViscoelasticMaterial):
                bulk_moduli.append(mat.bulk_modulus)
                g0_values.append(mat.G0)
                gi_values.append(mat.GI)
                beta_values.append(mat.beta)
            
            elif isinstance(mat, ElasticMaterial):
                # Convert elastic to viscoelastic
                E = mat.elastic_modulus
                nu = mat.poisson_ratio
                K = E / (3 * (1 - 2 * nu))  # Bulk modulus
                G = E / (2 * (1 + nu))  # Shear modulus
                
                bulk_moduli.append(K)
                g0_values.append(G)
                gi_values.append(G)  # No relaxation for elastic
                beta_values.append(0.0)  # No decay
            
            elif isinstance(mat, ElastoplasticMaterial):
                # Convert elastoplastic to viscoelastic (use elastic part)
                E = mat.elastic_modulus
                nu = mat.poisson_ratio
                K = E / (3 * (1 - 2 * nu))
                G = E / (2 * (1 + nu))
                
                bulk_moduli.append(K)
                g0_values.append(G)
                gi_values.append(G)
                beta_values.append(0.0)
        
        # Voigt average for bulk modulus (parallel model)
        K_avg = sum(K * vf for K, vf in zip(bulk_moduli, volume_fractions))
        
        # Reuss average for shear modulus (series model)
        G0_avg = 1.0 / sum(vf / G for G, vf in zip(g0_values, volume_fractions))
        GI_avg = 1.0 / sum(vf / G for G, vf in zip(gi_values, volume_fractions))
        
        # Apply minimum shear modulus for numerical stability
        # Maintain viscoelastic behavior: G0 >= GI
        G0_avg_original = G0_avg
        GI_avg_original = GI_avg
        
        # First clamp GI to minimum
        GI_avg = max(GI_avg, self.mat_db.min_shear_modulus)
        
        # Then ensure G0 is at least as large as GI
        if G0_avg_original > GI_avg_original:
            ratio = G0_avg_original / GI_avg_original
            G0_avg = max(GI_avg * ratio, self.mat_db.min_shear_modulus)
        else:
            G0_avg = max(G0_avg, GI_avg)
        
        # Simple average for beta and density
        beta_avg = sum(beta * vf for beta, vf in zip(beta_values, volume_fractions))
        rho_avg = sum(rho * vf for rho, vf in zip(densities, volume_fractions))
        
        # Create merged material name by joining all actual layer names
        merged_name = "_".join(layer_names)
        
        return ViscoelasticMaterial(
            name=merged_name,
            density=rho_avg,
            mat_type='VISCOELASTIC',
            bulk_modulus=K_avg,
            G0=G0_avg,
            GI=GI_avg,
            beta=beta_avg
        )


# =============================================================================
# Display File Generator
# =============================================================================

def generate_display_file(output_file: str, merged_materials: Dict[int, Material], 
                          layers: List[LaminateLayer], csv_basename: str):
    """Generate display.txt file for visualization"""
    
    # Group layers by PID
    pid_groups = {}
    for layer in layers:
        pid = layer.part_id if layer.part_id > 0 else layer.layer_set
        if pid not in pid_groups:
            pid_groups[pid] = []
        pid_groups[pid].append(layer)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("*Inputfile\n")
        f.write(f"{csv_basename}.k\n")
        f.write("*Mode\n")
        
        # Write PART_EXCHANGE lines for all PIDs
        for pid in sorted(pid_groups.keys()):
            f.write(f"PART_EXCHANGE,{pid}\n")
        
        # Write each PartExchange block (one per PID)
        mid_counter = 1  # Global MID counter
        
        for pid in sorted(pid_groups.keys()):
            pid_layers = pid_groups[pid]
            
            f.write(f"**PartExchange,{pid}\n")
            f.write(f"*PID,{pid}\n")
            f.write(f"*ConvertHexato,SolidComp,(0,-1,0),5.0\n")
            
            # Store MID info for this PID's layers
            layer_mids = []
            
            # Get unique layer_sets in this PID (preserve order)
            seen_sets = []
            for layer in pid_layers:
                if layer.layer_set not in seen_sets:
                    seen_sets.append(layer.layer_set)
            
            # Write material card for each unique layer_set in this PID
            for set_num in seen_sets:
                if set_num in merged_materials:
                    mat = merged_materials[set_num]
                    
                    # Material card with MID prefix
                    mat_card = mat.to_dyna_card(mid_counter)
                    lines = mat_card.split('\n')
                    
                    # Process material card lines
                    for line in lines:
                        if line.startswith('*MAT_'):
                            # Add MID prefix
                            f.write(f"*MID{mid_counter:02d},{line}\n")
                        elif line.startswith('$#'):
                            # Comment line
                            f.write(f"{line}\n")
                        elif line.strip():
                            # Check if this is a data line (starts with spaces followed by digits)
                            stripped = line.lstrip()
                            if stripped and stripped[0].isdigit():
                                # Data line - replace first 10 characters (MID field) with MIDxx
                                mid_str = f"MID{mid_counter:02d}".rjust(10)
                                modified_line = mid_str + line[10:]
                                f.write(f"{modified_line}\n")
                            else:
                                # Material name line or other text
                                f.write(f"{line}\n")
                    
                    # Calculate thickness for this layer_set
                    set_layers = [l for l in layers if l.layer_set == set_num]
                    total_thickness = sum(l.thickness for l in set_layers)
                    
                    # Thickness
                    f.write(f"*THK{mid_counter:02d},{total_thickness:.3f}\n")
                    
                    # NUME (number of elements through thickness)
                    f.write(f"*NUME{mid_counter},2\n")
                    
                    # Store for Layup section
                    layer_mids.append(mid_counter)
                    mid_counter += 1
            
            # Layup section with all layers in this PID
            f.write("*Layup\n")
            f.write("$$THK,MID,EOSID,HGID from bottom side\n")
            for mid in layer_mids:
                f.write(f"THK{mid:02d},MID{mid:02d},EOS,HGID,NUME{mid}\n")
            f.write("*EndLayup\n")
            f.write("**EndPartExchange\n")
        
        # Footer
        f.write("*End\n")


# =============================================================================
# Main Program
# =============================================================================

def main():
    """Main program"""
    print("=" * 70)
    print("LS-DYNA Material Card Generator")
    print("=" * 70)
    print()
    
    # Get input file names
    min_shear_modulus = DEFAULT_MIN_SHEAR_MODULUS
    
    if len(sys.argv) >= 3:
        # Command line arguments provided
        material_source_file = sys.argv[1]
        laminate_csv_file = sys.argv[2]
        
        # Optional: minimum shear modulus
        if len(sys.argv) >= 4:
            try:
                min_shear_modulus = parse_value_with_unit(sys.argv[3])
                print(f"Using minimum shear modulus: {min_shear_modulus} MPa")
                print()
            except Exception as e:
                print(f"WARNING: Could not parse minimum shear modulus '{sys.argv[3]}': {e}")
                print(f"Using default: {DEFAULT_MIN_SHEAR_MODULUS} MPa")
                print()
    else:
        # Interactive input
        print("Enter input file names:")
        material_source_file = input("  Material source file (e.g., MaterialSource.txt): ").strip()
        laminate_csv_file = input("  Laminate CSV file (e.g., B8_MetalBPI.csv): ").strip()
        min_shear_input = input(f"  Minimum shear modulus (default: {DEFAULT_MIN_SHEAR_MODULUS}MPa, press Enter to skip): ").strip()
        
        if min_shear_input:
            try:
                min_shear_modulus = parse_value_with_unit(min_shear_input)
            except Exception as e:
                print(f"WARNING: Could not parse '{min_shear_input}': {e}")
                print(f"Using default: {DEFAULT_MIN_SHEAR_MODULUS} MPa")
        
        print()
    
    # Check if files exist
    if not os.path.exists(material_source_file):
        print(f"ERROR: Material source file '{material_source_file}' not found!")
        sys.exit(1)
    if not os.path.exists(laminate_csv_file):
        print(f"ERROR: Laminate CSV file '{laminate_csv_file}' not found!")
        sys.exit(1)
    
    # Generate output filename from CSV filename
    csv_basename = os.path.splitext(laminate_csv_file)[0]
    output_file = f"{csv_basename}.k"
    
    # Load material database
    print(f"Loading material database from {material_source_file}...")
    print(f"Minimum shear modulus: {min_shear_modulus} MPa")
    mat_db = MaterialDatabase(min_shear_modulus=min_shear_modulus)
    mat_db.load_from_file(material_source_file)
    print(f"Loaded {len(mat_db.materials)} materials")
    print()
    
    # Load laminate configuration
    print(f"Loading laminate configuration from {laminate_csv_file}...")
    merger = LaminateMerger(mat_db)
    layers = merger.load_laminate_from_csv(laminate_csv_file)
    print(f"Loaded {len(layers)} layers")
    print()
    
    # Merge layers by set
    print("Merging layers by set number...")
    merged_materials = merger.merge_layers_by_set(layers)
    print(f"Created {len(merged_materials)} merged materials")
    print()
    
    # Generate DYNA cards
    print("=" * 70)
    print("Generated LS-DYNA Material Cards:")
    print("=" * 70)
    print()
    
    mat_id = 1
    for set_num in sorted(merged_materials.keys()):
        mat = merged_materials[set_num]
        print(mat.to_dyna_card(mat_id))
        mat_id += 1
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("$# LS-DYNA Material Cards\n")
        f.write("$# Generated by DYNA Material Generator\n")
        f.write("$# \n")
        f.write("$# Single layers: original material type preserved\n")
        f.write("$# Multiple layers: merged as VISCOELASTIC (Voigt/Reuss model)\n")
        f.write("$# \n")
        f.write("\n")
        
        mat_id = 1
        for set_num in sorted(merged_materials.keys()):
            mat = merged_materials[set_num]
            f.write(mat.to_dyna_card(mat_id))
            #f.write("\n")
            mat_id += 1
    
    print()
    print(f"Material cards saved to: {output_file}")
    
    # Generate display file
    display_file = f"{csv_basename}_display.txt"
    print(f"Generating display file: {display_file}...")
    generate_display_file(display_file, merged_materials, layers, csv_basename)
    print(f"Display file saved to: {display_file}")
    
    print()
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    for set_num in sorted(merged_materials.keys()):
        mat = merged_materials[set_num]
        print(f"Set {set_num}: {mat.name} ({mat.mat_type})")
        print(f"  Density: {mat.density:.4f} g/cm³")
        
        if isinstance(mat, ElasticMaterial):
            print(f"  Elastic Modulus (E): {mat.elastic_modulus:.2f} MPa")
            print(f"  Poisson's Ratio (ν): {mat.poisson_ratio:.4f}")
        
        elif isinstance(mat, ElastoplasticMaterial):
            print(f"  Elastic Modulus (E): {mat.elastic_modulus:.2f} MPa")
            print(f"  Poisson's Ratio (ν): {mat.poisson_ratio:.4f}")
            print(f"  Yield Stress (σy): {mat.yield_stress:.2f} MPa")
            print(f"  Tangent Modulus (Et): {mat.tangent_modulus:.2f} MPa")
        
        elif isinstance(mat, ViscoelasticMaterial):
            print(f"  Bulk Modulus (K): {mat.bulk_modulus:.2f} MPa")
            print(f"  G0 (short-time): {mat.G0:.2f} MPa")
            print(f"  GI (long-time): {mat.GI:.2f} MPa")
            print(f"  Beta: {mat.beta:.4f}")
        
        print()


if __name__ == '__main__':
    # Show usage if -h or --help
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("=" * 70)
        print("LS-DYNA Material Card Generator")
        print("=" * 70)
        print()
        print("Usage:")
        print("  python3 dyna_material_generator.py <material_source> <laminate_csv> [min_shear]")
        print()
        print("Arguments:")
        print("  material_source : Material database file (e.g., MaterialSource.txt)")
        print("  laminate_csv    : Laminate configuration CSV file (e.g., B8_MetalBPI.csv)")
        print("  min_shear       : (Optional) Minimum shear modulus with unit (default: 1MPa)")
        print("                    Examples: 0.5MPa, 5MPa, 0.01GPa")
        print()
        print("Output:")
        print("  <laminate_csv_basename>.k           : LS-DYNA keyword file")
        print("  <laminate_csv_basename>_display.txt : Display configuration file")
        print()
        print("Examples:")
        print("  # Use default minimum shear modulus (1 MPa)")
        print("  python3 dyna_material_generator.py MaterialSource.txt B8_MetalBPI.csv")
        print()
        print("  # Set minimum shear modulus to 0.5 MPa")
        print("  python3 dyna_material_generator.py MaterialSource.txt B8_MetalBPI.csv 0.5MPa")
        print()
        print("  # Set minimum shear modulus to 5 MPa")
        print("  python3 dyna_material_generator.py MaterialSource.txt B8_MetalBPI.csv 5MPa")
        print()
        print("Interactive mode:")
        print("  python3 dyna_material_generator.py")
        print("  (will prompt for input files and settings)")
        print()
        sys.exit(0)
    
    main()

