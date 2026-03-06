"""Hybrid repository for CellCAD.

This module provides a repository that combines PyBaMM and Excel sources,
using PyBaMM as base and Excel for overrides and packaging data.
"""

from pathlib import Path

from forge.engine.models.materials import (
    DENSITY_ALUMINUM,
    DENSITY_PET,
    DENSITY_PP,
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
)

from .base import MaterialRepository
from .excel_repo import ExcelRepository, check_pandas_available
from .pybamm_repo import PyBaMMRepository, check_pybamm_available

# Default packaging presets (when no Excel file provided)
DEFAULT_PACKAGING_PRESETS = {
    "standard_pouch": [
        PackagingLayer("PET", "1.0", 12.0, 0.0, DENSITY_PET),
        PackagingLayer("Aluminum", "1.0", 40.0, 0.0, DENSITY_ALUMINUM),
        PackagingLayer("PP", "1.0", 80.0, 0.0, DENSITY_PP),
    ],
    "thin_pouch": [
        PackagingLayer("PET", "1.0", 10.0, 0.0, DENSITY_PET),
        PackagingLayer("Aluminum", "1.0", 30.0, 0.0, DENSITY_ALUMINUM),
        PackagingLayer("PP", "1.0", 60.0, 0.0, DENSITY_PP),
    ],
    "thick_pouch": [
        PackagingLayer("PET", "1.0", 15.0, 0.0, DENSITY_PET),
        PackagingLayer("Aluminum", "1.0", 50.0, 0.0, DENSITY_ALUMINUM),
        PackagingLayer("PP", "1.0", 100.0, 0.0, DENSITY_PP),
    ],
}


class HybridRepository(MaterialRepository):
    """Repository that combines PyBaMM and Excel data sources.

    This repository uses:
    - PyBaMM as the primary source for electrode and separator properties
    - Excel as an optional override/fallback source
    - Built-in defaults for packaging (or Excel if provided)

    Priority order:
    1. Excel (if material ID is found)
    2. PyBaMM (for parameter set materials)
    3. Defaults (for packaging only)

    Attributes:
        pybamm_repo: PyBaMM repository instance (or None if not available)
        excel_repo: Excel repository instance (or None if not configured)
    """

    def __init__(
        self,
        pybamm_set: str | None = None,
        excel_path: str | Path | None = None,
    ):
        """Initialize hybrid repository.

        Args:
            pybamm_set: PyBaMM parameter set name (e.g., "Chen2020")
            excel_path: Optional path to Excel file for overrides

        Raises:
            ValueError: If neither PyBaMM set nor Excel path is provided
        """
        self.pybamm_repo: PyBaMMRepository | None = None
        self.excel_repo: ExcelRepository | None = None

        # Initialize PyBaMM repository if specified and available
        if pybamm_set is not None:
            if check_pybamm_available():
                self.pybamm_repo = PyBaMMRepository(pybamm_set)
            else:
                raise ImportError(
                    f"PyBaMM parameter set '{pybamm_set}' requested but PyBaMM "
                    "is not installed. Install with: pip install pybamm"
                )

        # Initialize Excel repository if specified
        if excel_path is not None:
            if check_pandas_available():
                self.excel_repo = ExcelRepository(excel_path)
            else:
                raise ImportError(
                    f"Excel file '{excel_path}' specified but pandas is not "
                    "installed. Install with: pip install pandas openpyxl"
                )

        # Ensure at least one source is configured
        if self.pybamm_repo is None and self.excel_repo is None:
            raise ValueError("At least one data source (PyBaMM or Excel) must be configured")

    # =========================================================================
    # MaterialRepository interface implementation
    # =========================================================================

    def list_cathodes(self) -> list[str]:
        """List all available cathode material IDs from all sources."""
        ids = set()

        if self.excel_repo is not None:
            ids.update(self.excel_repo.list_cathodes())

        if self.pybamm_repo is not None:
            ids.update(self.pybamm_repo.list_cathodes())

        return sorted(ids)

    def get_cathode(self, material_id: str = None) -> CathodeMaterial:
        """Get cathode material, checking Excel first then PyBaMM.

        Args:
            material_id: Material ID. If None and PyBaMM is configured,
                         returns PyBaMM cathode.

        Returns:
            CathodeMaterial

        Raises:
            KeyError: If material not found in any source
        """
        # If specific ID provided, try Excel first
        if material_id is not None and self.excel_repo is not None:
            try:
                return self.excel_repo.get_cathode(material_id)
            except KeyError:
                pass  # Fall through to PyBaMM

        # Try PyBaMM
        if self.pybamm_repo is not None:
            return self.pybamm_repo.get_cathode(material_id)

        # If no PyBaMM and specific ID requested, try Excel again with error
        if self.excel_repo is not None:
            return self.excel_repo.get_cathode(material_id)

        raise KeyError(f"Cathode '{material_id}' not found")

    def list_anodes(self) -> list[str]:
        """List all available anode material IDs from all sources."""
        ids = set()

        if self.excel_repo is not None:
            ids.update(self.excel_repo.list_anodes())

        if self.pybamm_repo is not None:
            ids.update(self.pybamm_repo.list_anodes())

        return sorted(ids)

    def get_anode(self, material_id: str = None) -> AnodeMaterial:
        """Get anode material, checking Excel first then PyBaMM.

        Args:
            material_id: Material ID. If None and PyBaMM is configured,
                         returns PyBaMM anode.

        Returns:
            AnodeMaterial

        Raises:
            KeyError: If material not found in any source
        """
        # If specific ID provided, try Excel first
        if material_id is not None and self.excel_repo is not None:
            try:
                return self.excel_repo.get_anode(material_id)
            except KeyError:
                pass

        # Try PyBaMM
        if self.pybamm_repo is not None:
            return self.pybamm_repo.get_anode(material_id)

        # If no PyBaMM and specific ID requested, try Excel again with error
        if self.excel_repo is not None:
            return self.excel_repo.get_anode(material_id)

        raise KeyError(f"Anode '{material_id}' not found")

    def list_separators(self) -> list[str]:
        """List all available separator material IDs from all sources."""
        ids = set()

        if self.excel_repo is not None:
            ids.update(self.excel_repo.list_separators())

        if self.pybamm_repo is not None:
            ids.update(self.pybamm_repo.list_separators())

        return sorted(ids)

    def get_separator(self, material_id: str = None) -> SeparatorMaterial:
        """Get separator material, checking Excel first then PyBaMM.

        Args:
            material_id: Material ID. If None and PyBaMM is configured,
                         returns PyBaMM separator.

        Returns:
            SeparatorMaterial

        Raises:
            KeyError: If material not found in any source
        """
        # If specific ID provided, try Excel first
        if material_id is not None and self.excel_repo is not None:
            try:
                return self.excel_repo.get_separator(material_id)
            except KeyError:
                pass

        # Try PyBaMM
        if self.pybamm_repo is not None:
            return self.pybamm_repo.get_separator(material_id)

        # If no PyBaMM and specific ID requested, try Excel again with error
        if self.excel_repo is not None:
            return self.excel_repo.get_separator(material_id)

        raise KeyError(f"Separator '{material_id}' not found")

    def list_electrolytes(self) -> list[str]:
        """List all available electrolyte model IDs from all sources."""
        ids = set()

        if self.excel_repo is not None:
            ids.update(self.excel_repo.list_electrolytes())

        if self.pybamm_repo is not None:
            ids.update(self.pybamm_repo.list_electrolytes())

        return sorted(ids)

    def get_electrolyte(self, electrolyte_id: str = None) -> ElectrolyteModel:
        """Get electrolyte model, checking Excel first then PyBaMM.

        Args:
            electrolyte_id: Electrolyte ID. If None and PyBaMM is configured,
                            returns PyBaMM electrolyte.

        Returns:
            ElectrolyteModel

        Raises:
            KeyError: If electrolyte not found in any source
        """
        # If specific ID provided, try Excel first
        if electrolyte_id is not None and self.excel_repo is not None:
            try:
                return self.excel_repo.get_electrolyte(electrolyte_id)
            except KeyError:
                pass

        # Try PyBaMM
        if self.pybamm_repo is not None:
            return self.pybamm_repo.get_electrolyte(electrolyte_id)

        # If no PyBaMM and specific ID requested, try Excel again with error
        if self.excel_repo is not None:
            return self.excel_repo.get_electrolyte(electrolyte_id)

        raise KeyError(f"Electrolyte '{electrolyte_id}' not found")

    def list_packaging_presets(self) -> list[str]:
        """List all available packaging preset names."""
        presets = set(DEFAULT_PACKAGING_PRESETS.keys())

        if self.excel_repo is not None:
            presets.update(self.excel_repo.list_packaging_presets())

        return sorted(presets)

    def get_packaging_layers(self, preset_name: str) -> list[PackagingLayer]:
        """Get packaging layers for a preset.

        Checks Excel first, then defaults.

        Args:
            preset_name: Packaging preset name

        Returns:
            List of PackagingLayer objects

        Raises:
            KeyError: If preset not found
        """
        # Try Excel first
        if self.excel_repo is not None:
            try:
                return self.excel_repo.get_packaging_layers(preset_name)
            except KeyError:
                pass

        # Try defaults
        preset_lower = preset_name.lower()
        if preset_lower in DEFAULT_PACKAGING_PRESETS:
            return DEFAULT_PACKAGING_PRESETS[preset_lower]

        raise KeyError(f"Packaging preset '{preset_name}' not found")


def create_repository(
    pybamm_set: str | None = None,
    excel_path: str | Path | None = None,
) -> MaterialRepository:
    """Factory function to create the appropriate repository.

    Creates a HybridRepository if both sources are specified,
    or a single-source repository otherwise.

    Args:
        pybamm_set: PyBaMM parameter set name
        excel_path: Path to Excel file

    Returns:
        Configured MaterialRepository instance
    """
    if pybamm_set is not None or excel_path is not None:
        return HybridRepository(pybamm_set, excel_path)

    # Default: create PyBaMM repository with Chen2020 if available
    if check_pybamm_available():
        return PyBaMMRepository("Chen2020")

    raise ValueError(
        "No data source available. Either install PyBaMM (pip install pybamm) "
        "or provide an Excel file path."
    )
