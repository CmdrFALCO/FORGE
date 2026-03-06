"""Internal geometry engine for CAD generation.

This module provides layer-by-layer position calculations for battery cells,
computing Z-positions (stacked cells) or R-positions (wound cells) from
cell design parameters.

Main components:
- ArchetypeSchema: Pydantic validation for archetype JSON files
- ArchetypeLoader: Load and map archetypes to FORGE models
- SwellingProfile: Per-component EOL swelling factors
- LayerStackGeometry: Stacked cell layer positions
- WindingGeometry: Wound cell radial positions
- CoatingZoneGeometry: Coated vs uncoated electrode areas
- DetailedGeometry: Complete geometry for CAD export
"""

from forge.engine.geometry.coating_zones import (
    CoatingZoneGeometry,
    Rectangle,
)
from forge.engine.geometry.detailed_geometry import (
    DetailedGeometry,
    ExternalDimensions,
)
from forge.engine.geometry.layer_stack import (
    Layer,
    LayerStackGeometry,
    LayerType,
    WindingGeometry,
    WindLayer,
)
from forge.engine.geometry.loader import ArchetypeLoader
from forge.engine.geometry.schemas import (
    ArchetypeSchema,
    ConfidenceLevel,
)
from forge.engine.geometry.swelling import SwellingProfile
from forge.engine.geometry.tabs import (
    Busbar,
    CylindricalTabCalculator,
    Point3D,
    PouchTabCalculator,
    PrismaticTabCalculator,
    TabGeometry,
    TabMaterial,
    TabPolarity,
    TabStrip,
    TerminalPost,
    calculate_tab_geometry,
)
from forge.engine.geometry.validation import (
    DEFAULT_THRESHOLDS,
    GeometryValidator,
    Severity,
    ValidationCategory,
    ValidationReport,
    ValidationResult,
    ValidationThresholds,
    validate_geometry,
)

__all__ = [
    # Schemas
    "ArchetypeSchema",
    "ConfidenceLevel",
    # Swelling
    "SwellingProfile",
    # Layer stack
    "Layer",
    "LayerType",
    "LayerStackGeometry",
    "WindLayer",
    "WindingGeometry",
    # Coating zones
    "Rectangle",
    "CoatingZoneGeometry",
    # Loader
    "ArchetypeLoader",
    # Detailed geometry
    "DetailedGeometry",
    "ExternalDimensions",
    # Tabs
    "TabPolarity",
    "TabMaterial",
    "Point3D",
    "TabStrip",
    "Busbar",
    "TerminalPost",
    "TabGeometry",
    "PouchTabCalculator",
    "PrismaticTabCalculator",
    "CylindricalTabCalculator",
    "calculate_tab_geometry",
    # Validation
    "Severity",
    "ValidationCategory",
    "ValidationResult",
    "ValidationReport",
    "ValidationThresholds",
    "DEFAULT_THRESHOLDS",
    "GeometryValidator",
    "validate_geometry",
]
