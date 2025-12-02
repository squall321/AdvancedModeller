"""Part data model"""
from dataclasses import dataclass, field
from typing import List, Tuple
from .layer import LayerConfig

@dataclass
class PartConfig:
    part_id: int
    part_name: str = ""
    enabled: bool = False
    layers: List[LayerConfig] = field(default_factory=list)
    # Stack direction and angle for layer generation
    stack_direction: Tuple[float, float, float] = (0, 1, 0)  # Bottom-Up default
    stack_angle: float = 5.0

    def to_dict(self) -> dict:
        return {
            "part_id": self.part_id,
            "part_name": self.part_name,
            "enabled": self.enabled,
            "layers": [l.to_dict() for l in self.layers],
            "stack_direction": list(self.stack_direction),
            "stack_angle": self.stack_angle
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PartConfig':
        direction = data.get("stack_direction", [0, 1, 0])
        return cls(
            part_id=data.get("part_id", 0),
            part_name=data.get("part_name", ""),
            enabled=data.get("enabled", False),
            layers=[LayerConfig.from_dict(l) for l in data.get("layers", [])],
            stack_direction=tuple(direction) if direction else (0, 1, 0),
            stack_angle=data.get("stack_angle", 5.0)
        )

    @property
    def total_thickness(self) -> float:
        return sum(l.thickness for l in self.layers)

    @property
    def layer_count(self) -> int:
        return len(self.layers)
