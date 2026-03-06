"""Repository module for CellCAD material data.

This module provides data repositories for loading material properties from:
- PyBaMM parameter sets
- Excel files
- Hybrid (combined) sources

Example usage:
    from forge.materials.repositories import create_repository

    # Use PyBaMM parameter set
    repo = create_repository(pybamm_set="Chen2020")
    cathode = repo.get_cathode()

    # Use Excel file
    repo = create_repository(excel_path="materials.xlsx")
    cathode = repo.get_cathode("NMC811_V1")

    # Use both (Excel overrides PyBaMM)
    repo = create_repository(pybamm_set="Chen2020", excel_path="overrides.xlsx")
"""

from .base import MaterialRepository
from .excel_repo import (
    ExcelRepository,
    check_pandas_available,
    create_template_excel,
)
from .hybrid_repo import (
    DEFAULT_PACKAGING_PRESETS,
    HybridRepository,
    create_repository,
)
from .pybamm_repo import (
    AVAILABLE_PARAMETER_SETS,
    PyBaMMRepository,
    check_pybamm_available,
)

__all__ = [
    # Base class
    "MaterialRepository",
    # PyBaMM
    "PyBaMMRepository",
    "check_pybamm_available",
    "AVAILABLE_PARAMETER_SETS",
    # Excel
    "ExcelRepository",
    "check_pandas_available",
    "create_template_excel",
    # Hybrid
    "HybridRepository",
    "create_repository",
    "DEFAULT_PACKAGING_PRESETS",
]
