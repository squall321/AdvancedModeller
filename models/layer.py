"""Layer data model"""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class LayerConfig:
    material_name: str = ""
    thickness: float = 0.05  # mm
    layer_set: int = 1       # 같은 번호 = 병합

    def to_dict(self) -> dict:
        return {
            "material": self.material_name,
            "thickness": self.thickness,
            "layer_set": self.layer_set
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LayerConfig':
        return cls(
            material_name=data.get("material", ""),
            thickness=data.get("thickness", 0.05),
            layer_set=data.get("layer_set", 1)
        )
