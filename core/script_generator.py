"""Script generator for creating display.txt files"""
from typing import List, Dict
from pathlib import Path
from models import PartConfig, LayerConfig
from .material_db import MaterialDatabase

class ScriptGenerator:
    """Generates display.txt script for KooMeshModifier"""

    def __init__(self, material_db: MaterialDatabase):
        self.mat_db = material_db

    def generate(self, parts: List[PartConfig], output_name: str,
                 k_filename: str = None) -> str:
        """Generate display.txt format script"""
        if k_filename is None:
            k_filename = f"{output_name}.k"

        lines = []

        # Header
        lines.append("*Inputfile")
        lines.append(k_filename)
        lines.append("*Mode")

        # Part exchange declarations
        for part in parts:
            if part.enabled and part.layers:
                lines.append(f"PART_EXCHANGE,{part.part_id}")

        # Part blocks
        mid_counter = 1
        for part in parts:
            if not part.enabled or not part.layers:
                continue

            lines.append(f"**PartExchange,{part.part_id}")
            lines.append(f"*PID,{part.part_id}")
            # Use part's stack direction and angle
            dir_x, dir_y, dir_z = part.stack_direction
            angle = part.stack_angle
            lines.append(f"*ConvertHexato,SolidComp,({dir_x},{dir_y},{dir_z}),{angle}")

            # Group layers by layer_set
            layer_sets: Dict[int, List[LayerConfig]] = {}
            for layer in part.layers:
                if layer.layer_set not in layer_sets:
                    layer_sets[layer.layer_set] = []
                layer_sets[layer.layer_set].append(layer)

            # Generate material cards for each unique layer_set
            set_mids = []
            for set_num in sorted(layer_sets.keys()):
                set_layers = layer_sets[set_num]

                # Generate material card
                mat_lines = self._generate_material_card(set_layers, mid_counter)
                lines.extend(mat_lines)

                # Calculate total thickness for this set
                total_thickness = sum(l.thickness for l in set_layers)
                lines.append(f"*THK{mid_counter:02d},{total_thickness:.3f}")
                lines.append(f"*NUME{mid_counter},2")

                set_mids.append(mid_counter)
                mid_counter += 1

            # Layup section
            lines.append("*Layup")
            lines.append("$$THK,MID,EOSID,HGID from bottom side")
            for mid in set_mids:
                lines.append(f"THK{mid:02d},MID{mid:02d},EOS,HGID,NUME{mid}")
            lines.append("*EndLayup")
            lines.append("**EndPartExchange")

        lines.append("*End")
        return "\n".join(lines)

    def _generate_material_card(self, layers: List[LayerConfig], mid: int) -> List[str]:
        """Generate material card for a layer set"""
        lines = []

        if len(layers) == 1:
            # Single layer - keep original material type
            layer = layers[0]
            mat = self._get_material_safe(layer.material_name)
            card = self._format_single_material(mat, layer.material_name, mid)
            lines.extend(card)
        else:
            # Multiple layers - merge into viscoelastic
            card = self._format_merged_material(layers, mid)
            lines.extend(card)

        return lines

    def _get_material_safe(self, name: str):
        """Get material with fallback"""
        try:
            return self.mat_db.get_material(name)
        except KeyError:
            # Return default viscoelastic properties
            from .material_db import Material
            return Material(name=name, mat_type='VISCOELASTIC',
                          density=1.2, modulus=2000, add1=0.002, add2=0.001, add3=2000)

    def _format_single_material(self, mat, layer_name: str, mid: int) -> List[str]:
        """Format single material card"""
        lines = []
        rho = mat.density * 1e-9  # Convert to ton/mm^3

        if mat.mat_type == 'ELASTIC':
            lines.append(f"*MID{mid:02d},*MAT_ELASTIC_TITLE")
            lines.append(layer_name)
            lines.append("$#     mid       rho         e        pr")
            lines.append(f"     MID{mid:02d}{rho:>10.4e}{mat.modulus:>10.3e}{mat.add1:>10.4f}")

        elif mat.mat_type == 'ELASTOPLASTIC':
            lines.append(f"*MID{mid:02d},*MAT_PLASTIC_KINEMATIC_TITLE")
            lines.append(layer_name)
            lines.append("$#     mid       rho         e        pr      sigy      etan")
            lines.append(f"     MID{mid:02d}{rho:>10.4e}{mat.modulus:>10.3e}{mat.add1:>10.4f}{mat.add2:>10.3e}{mat.add3:>10.3e}")

        else:  # VISCOELASTIC
            lines.append(f"*MID{mid:02d},*MAT_VISCOELASTIC_TITLE")
            lines.append(layer_name)
            lines.append("$#     mid       rho      bulk        g0        gi      beta")
            g0 = max(mat.add1, 1.0)  # Minimum shear modulus
            gi = max(mat.add2, 1.0)
            lines.append(f"     MID{mid:02d}{rho:>10.4e}{mat.modulus:>10.3e}{g0:>10.3e}{gi:>10.3e}{mat.add3:>10.4f}")

        return lines

    def _format_merged_material(self, layers: List[LayerConfig], mid: int) -> List[str]:
        """Format merged material card (Voigt/Reuss averaging)"""
        lines = []

        total_thickness = sum(l.thickness for l in layers)
        name_parts = [l.material_name for l in layers]
        merged_name = "_".join(name_parts)

        # Calculate averaged properties
        rho_sum = 0
        bulk_sum = 0
        g0_inv_sum = 0
        gi_inv_sum = 0
        beta_sum = 0

        for layer in layers:
            vf = layer.thickness / total_thickness
            mat = self._get_material_safe(layer.material_name)

            rho_sum += mat.density * vf

            # Convert to viscoelastic properties
            if mat.mat_type in ['ELASTIC', 'ELASTOPLASTIC']:
                E = mat.modulus
                nu = mat.add1 if mat.add1 < 0.5 else 0.3
                K = E / (3 * (1 - 2 * nu))
                G = E / (2 * (1 + nu))
                bulk_sum += K * vf
                g0_inv_sum += vf / max(G, 1.0)
                gi_inv_sum += vf / max(G, 1.0)
            else:
                bulk_sum += mat.modulus * vf
                g0_inv_sum += vf / max(mat.add1, 1.0)
                gi_inv_sum += vf / max(mat.add2, 1.0)
                beta_sum += mat.add3 * vf

        g0_avg = 1.0 / g0_inv_sum if g0_inv_sum > 0 else 1.0
        gi_avg = 1.0 / gi_inv_sum if gi_inv_sum > 0 else 1.0
        rho = rho_sum * 1e-9

        lines.append(f"*MID{mid:02d},*MAT_VISCOELASTIC_TITLE")
        lines.append(merged_name)
        lines.append("$#     mid       rho      bulk        g0        gi      beta")
        lines.append(f"     MID{mid:02d}{rho:>10.4e}{bulk_sum:>10.3e}{g0_avg:>10.3e}{gi_avg:>10.3e}{beta_sum:>10.4f}")

        return lines

    def save(self, content: str, filepath: str):
        """Save script to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
