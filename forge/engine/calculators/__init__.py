"""FORGE engine calculators package.

Top-level orchestrators that coordinate models, geometry, and calculations
to produce complete cell reports for each cell type.
"""

from .base import BaseCalculator
from .cylindrical_calculator import (
    CylindricalCalculator,
    CylindricalElectrodeMass,
    calculate_cylindrical_anode_mass,
    calculate_cylindrical_cathode_mass,
    calculate_cylindrical_separator_mass,
)
from .pouch_calculator import (
    CellCalculator,
    generate_report_text,
)
from .prismatic_calculator import (
    GapToWallResult,
    PrismaticCalculator,
    PrismaticHousingResult,
    SeparatorCompressionResult,
    create_v1_prismatic_input,
)

__all__ = [
    # Pouch
    "BaseCalculator",
    "CellCalculator",
    "generate_report_text",
    # Prismatic
    "PrismaticCalculator",
    "PrismaticHousingResult",
    "GapToWallResult",
    "SeparatorCompressionResult",
    "create_v1_prismatic_input",
    # Cylindrical
    "CylindricalCalculator",
    "CylindricalElectrodeMass",
    "calculate_cylindrical_cathode_mass",
    "calculate_cylindrical_anode_mass",
    "calculate_cylindrical_separator_mass",
]
