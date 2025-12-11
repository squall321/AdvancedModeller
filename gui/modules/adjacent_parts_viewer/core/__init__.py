"""Core components for Adjacent Parts Viewer"""

from .detector import AdjacentPartsDetector, DetectionResult
from .spatial_index import SpatialIndex, BoundingBox
from .surface_analyzer import SurfaceAnalyzer
from .projection import ProjectionEngine, ProjectedOutline
from .ray_tracer import RayTracer, RayHit

__all__ = [
    'AdjacentPartsDetector',
    'DetectionResult',
    'SpatialIndex',
    'BoundingBox',
    'SurfaceAnalyzer',
    'ProjectionEngine',
    'ProjectedOutline',
    'RayTracer',
    'RayHit',
]
