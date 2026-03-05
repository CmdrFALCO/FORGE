"""Geometry calculators for different cell types.

Provides calculators for:
- Stacked cells (pouch, prismatic): Layer-by-layer Z positions
- Wound cells (cylindrical): Radial R positions in jellyroll
"""

from forge.engine.geometry.calculators.base import InternalGeometryCalculator
from forge.engine.geometry.calculators.stacked import StackedGeometryCalculator
from forge.engine.geometry.calculators.wound import WoundGeometryCalculator

__all__ = [
    "InternalGeometryCalculator",
    "StackedGeometryCalculator",
    "WoundGeometryCalculator",
]
