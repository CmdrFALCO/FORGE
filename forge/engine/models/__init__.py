"""FORGE engine data models.

All dataclass definitions for cell inputs, outputs, geometry, and materials.
"""

# Materials + constants
# Cylindrical
from .cylindrical import (
    CanMaterial,
    CylindricalCellInput,
    CylindricalGeometry,
    HeaderComponents,
    JellyRollResult,
    SimplifiedHeader,
    TabType,
    WindingConfig,
    create_4680_geometry,
    create_18650_geometry,
    create_21700_geometry,
    get_can_material_density,
)

# Geometry
from .geometry import (
    PouchPackaging,
    PrismaticGeometry,
    PrismaticSheetGeometry,
    SheetGeometry,
)
from .materials import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    DENSITY_NICKEL,
    DENSITY_PE,
    DENSITY_PET,
    DENSITY_PP,
    LFP_NOMINAL_VOLTAGE,
    NMC_NOMINAL_VOLTAGE,
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
    TabConfig,
)

# Pouch
from .pouch import (
    DEFAULT_EXCESS_FACTOR,
    PouchCellInput,
)

# Prismatic
from .prismatic import (
    PrismaticCADExport,
    PrismaticCADFeatures,
    PrismaticCellInput,
    TerminalGeometry,
    VentGeometry,
)
from .prismatic import (
    PrismaticGeometry as PrismaticCaseGeometry,
)
from .prismatic import (
    PrismaticSheetGeometry as PrismaticDirectionalSheetGeometry,
)

# Results
from .results import (
    BillOfMaterials,
    BomItem,
    CellReport,
)

# Stack
from .stack import (
    EndElectrodesMode,
    SheetCounts,
    StackConfiguration,
    StackThicknessResult,
    SwellingParameters,
    ThicknessParameters,
)

__all__ = [
    # Materials + constants
    "DENSITY_ALUMINUM",
    "DENSITY_COPPER",
    "DENSITY_NICKEL",
    "DENSITY_PE",
    "DENSITY_PET",
    "DENSITY_PP",
    "NMC_NOMINAL_VOLTAGE",
    "LFP_NOMINAL_VOLTAGE",
    "CathodeMaterial",
    "AnodeMaterial",
    "SeparatorMaterial",
    "ElectrolyteModel",
    "PackagingLayer",
    "TabConfig",
    # Geometry
    "SheetGeometry",
    "PrismaticSheetGeometry",
    "PouchPackaging",
    "PrismaticGeometry",
    # Stack
    "EndElectrodesMode",
    "SheetCounts",
    "StackConfiguration",
    "ThicknessParameters",
    "SwellingParameters",
    "StackThicknessResult",
    # Results
    "CellReport",
    "BomItem",
    "BillOfMaterials",
    # Pouch
    "PouchCellInput",
    "DEFAULT_EXCESS_FACTOR",
    # Prismatic
    "PrismaticCellInput",
    "PrismaticCaseGeometry",
    "PrismaticDirectionalSheetGeometry",
    "PrismaticCADFeatures",
    "PrismaticCADExport",
    "TerminalGeometry",
    "VentGeometry",
    # Cylindrical
    "TabType",
    "CanMaterial",
    "CylindricalGeometry",
    "WindingConfig",
    "HeaderComponents",
    "SimplifiedHeader",
    "JellyRollResult",
    "CylindricalCellInput",
    "get_can_material_density",
    "create_21700_geometry",
    "create_4680_geometry",
    "create_18650_geometry",
]
