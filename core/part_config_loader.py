"""CSV loader for predefined part configurations"""
import csv
from typing import Dict, List
from collections import defaultdict
from models import LayerConfig


class PartConfigLoader:
    """Load part layer configurations from CSV file"""

    def load(self, filepath: str) -> Dict[int, List[LayerConfig]]:
        """
        Load part configs from CSV file.
        CSV format (no header): material_name,thickness,layer_set,part_id

        Returns: {part_id: [LayerConfig, ...]}
        """
        configs: Dict[int, List[LayerConfig]] = defaultdict(list)

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 4:
                    continue

                try:
                    material_name = row[0].strip()
                    thickness = float(row[1])
                    layer_set = int(row[2])
                    part_id = int(row[3])

                    configs[part_id].append(LayerConfig(
                        material_name=material_name,
                        thickness=thickness,
                        layer_set=layer_set
                    ))
                except (ValueError, IndexError):
                    continue

        return dict(configs)
