"""Excel repository for CellCAD.

This module provides material data from Excel files (fallback/override for PyBaMM).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
)

from .base import MaterialRepository

if TYPE_CHECKING:
    import pandas as pd

# pandas is optional - only import if available
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def check_pandas_available() -> bool:
    """Check if pandas is available.

    Returns:
        True if pandas is installed and importable
    """
    return PANDAS_AVAILABLE


class ExcelRepository(MaterialRepository):
    """Repository that loads material data from Excel files.

    Expected Excel structure with sheets:
    - CathodeMaterials: Cathode material data
    - AnodeMaterials: Anode material data
    - SeparatorMaterials: Separator material data
    - ElectrolyteModels: Electrolyte model data
    - PackagingLayers: Packaging layer data (optional)

    Attributes:
        excel_path: Path to the Excel file
    """

    # Expected column names for each sheet
    CATHODE_COLUMNS = [
        "CathodeId",
        "Name",
        "Chemistry",
        "RevSpecCapacity_mAhg",
        "MaxSpecCapacity_mAhg",
        "ArealWeight_mgcm2",
        "CollectorThickness_um",
        "CoatingDensity_gcm3",
        "CoatingThickness0_um",
        "CoatingThickness100_um",
    ]

    ANODE_COLUMNS = [
        "AnodeId",
        "Name",
        "Chemistry",
        "RevSpecCapacity_mAhg",
        "MaxSpecCapacity_mAhg",
        "ArealWeight_mgcm2",
        "CollectorThickness_um",
        "CoatingDensity_gcm3",
        "CoatingThickness0_um",
        "CoatingThickness100_um",
    ]

    SEPARATOR_COLUMNS = [
        "SeparatorId",
        "Name",
        "Thickness_um",
        "Porosity_pct",
        "Density_gcm3",
        "ArealWeight_mgcm2",
    ]

    ELECTROLYTE_COLUMNS = ["ElectrolyteId", "Name", "Density_gcm3", "Conductivity_Sm"]

    PACKAGING_COLUMNS = [
        "PresetName",
        "LayerName",
        "Version",
        "Thickness_um",
        "Porosity_pct",
        "Density_gcm3",
    ]

    def __init__(self, excel_path: str | Path):
        """Initialize with path to Excel file.

        Args:
            excel_path: Path to Excel file containing material data

        Raises:
            ImportError: If pandas is not installed
            FileNotFoundError: If Excel file not found
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is not installed. Install with: pip install pandas openpyxl")

        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")

        self._load_data()

    def _load_data(self) -> None:
        """Load all sheets from the Excel file."""
        self._cathodes = self._load_sheet("CathodeMaterials")
        self._anodes = self._load_sheet("AnodeMaterials")
        self._separators = self._load_sheet("SeparatorMaterials")
        self._electrolytes = self._load_sheet("ElectrolyteModels")
        self._packaging = self._load_sheet("PackagingLayers")

    def _load_sheet(self, sheet_name: str) -> pd.DataFrame | None:
        """Load a single sheet from the Excel file.

        Args:
            sheet_name: Name of the sheet to load

        Returns:
            DataFrame or None if sheet doesn't exist
        """
        try:
            return pd.read_excel(self.excel_path, sheet_name=sheet_name)
        except Exception:
            return None

    # =========================================================================
    # MaterialRepository interface implementation
    # =========================================================================

    def list_cathodes(self) -> list[str]:
        """List available cathode material IDs."""
        if self._cathodes is None:
            return []
        return self._cathodes["CathodeId"].tolist()

    def get_cathode(self, material_id: str) -> CathodeMaterial:
        """Get cathode material by ID."""
        if self._cathodes is None:
            raise KeyError("No cathode data available")

        row = self._cathodes[self._cathodes["CathodeId"] == material_id]
        if row.empty:
            raise KeyError(f"Cathode '{material_id}' not found")

        r = row.iloc[0]
        return CathodeMaterial(
            id=r["CathodeId"],
            name=r["Name"],
            chemistry=r["Chemistry"],
            rev_spec_capacity_mahg=float(r["RevSpecCapacity_mAhg"]),
            max_spec_capacity_mahg=float(r["MaxSpecCapacity_mAhg"]),
            areal_weight_mgcm2=float(r["ArealWeight_mgcm2"]),
            collector_thickness_um=float(r["CollectorThickness_um"]),
            coating_density_gcm3=float(r["CoatingDensity_gcm3"]),
            coating_thickness_0pct_um=float(r["CoatingThickness0_um"]),
            coating_thickness_100pct_um=float(r["CoatingThickness100_um"]),
        )

    def list_anodes(self) -> list[str]:
        """List available anode material IDs."""
        if self._anodes is None:
            return []
        return self._anodes["AnodeId"].tolist()

    def get_anode(self, material_id: str) -> AnodeMaterial:
        """Get anode material by ID."""
        if self._anodes is None:
            raise KeyError("No anode data available")

        row = self._anodes[self._anodes["AnodeId"] == material_id]
        if row.empty:
            raise KeyError(f"Anode '{material_id}' not found")

        r = row.iloc[0]
        return AnodeMaterial(
            id=r["AnodeId"],
            name=r["Name"],
            chemistry=r["Chemistry"],
            rev_spec_capacity_mahg=float(r["RevSpecCapacity_mAhg"]),
            max_spec_capacity_mahg=float(r["MaxSpecCapacity_mAhg"]),
            areal_weight_mgcm2=float(r["ArealWeight_mgcm2"]),
            collector_thickness_um=float(r["CollectorThickness_um"]),
            coating_density_gcm3=float(r["CoatingDensity_gcm3"]),
            coating_thickness_0pct_um=float(r["CoatingThickness0_um"]),
            coating_thickness_100pct_um=float(r["CoatingThickness100_um"]),
        )

    def list_separators(self) -> list[str]:
        """List available separator material IDs."""
        if self._separators is None:
            return []
        return self._separators["SeparatorId"].tolist()

    def get_separator(self, material_id: str) -> SeparatorMaterial:
        """Get separator material by ID."""
        if self._separators is None:
            raise KeyError("No separator data available")

        row = self._separators[self._separators["SeparatorId"] == material_id]
        if row.empty:
            raise KeyError(f"Separator '{material_id}' not found")

        r = row.iloc[0]
        return SeparatorMaterial(
            id=r["SeparatorId"],
            name=r["Name"],
            thickness_um=float(r["Thickness_um"]),
            porosity_pct=float(r["Porosity_pct"]),
            density_gcm3=float(r["Density_gcm3"]),
            areal_weight_mgcm2=float(r["ArealWeight_mgcm2"]),
        )

    def list_electrolytes(self) -> list[str]:
        """List available electrolyte model IDs."""
        if self._electrolytes is None:
            return []
        return self._electrolytes["ElectrolyteId"].tolist()

    def get_electrolyte(self, electrolyte_id: str) -> ElectrolyteModel:
        """Get electrolyte model by ID."""
        if self._electrolytes is None:
            raise KeyError("No electrolyte data available")

        row = self._electrolytes[self._electrolytes["ElectrolyteId"] == electrolyte_id]
        if row.empty:
            raise KeyError(f"Electrolyte '{electrolyte_id}' not found")

        r = row.iloc[0]
        conductivity = r.get("Conductivity_Sm")
        if pd.isna(conductivity):
            conductivity = None

        return ElectrolyteModel(
            id=r["ElectrolyteId"],
            name=r["Name"],
            density_gcm3=float(r["Density_gcm3"]),
            conductivity_sm=float(conductivity) if conductivity else None,
        )

    def list_packaging_presets(self) -> list[str]:
        """List available packaging preset names."""
        if self._packaging is None:
            return []
        return self._packaging["PresetName"].unique().tolist()

    def get_packaging_layers(self, preset_name: str) -> list[PackagingLayer]:
        """Get packaging layers for a preset."""
        if self._packaging is None:
            raise KeyError("No packaging data available")

        rows = self._packaging[self._packaging["PresetName"] == preset_name]
        if rows.empty:
            raise KeyError(f"Packaging preset '{preset_name}' not found")

        layers = []
        for _, r in rows.iterrows():
            layers.append(
                PackagingLayer(
                    name=r["LayerName"],
                    version=str(r["Version"]),
                    thickness_um=float(r["Thickness_um"]),
                    porosity_pct=float(r["Porosity_pct"]),
                    density_gcm3=float(r["Density_gcm3"]),
                )
            )

        return layers


def create_template_excel(output_path: str | Path) -> None:
    """Create a template Excel file with the expected structure.

    Args:
        output_path: Path for the template Excel file
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is not installed. Install with: pip install pandas openpyxl")

    output_path = Path(output_path)

    # Create sample data for each sheet
    cathodes = pd.DataFrame(
        {
            "CathodeId": ["NMC811_V1", "NMC622_V1", "LFP_V1"],
            "Name": ["NMC811", "NMC622", "LFP"],
            "Chemistry": ["NMC811", "NMC622", "LFP"],
            "RevSpecCapacity_mAhg": [200.0, 175.0, 160.0],
            "MaxSpecCapacity_mAhg": [220.0, 192.0, 170.0],
            "ArealWeight_mgcm2": [20.0, 18.5, 16.0],
            "CollectorThickness_um": [15.0, 15.0, 15.0],
            "CoatingDensity_gcm3": [3.8, 3.6, 2.5],
            "CoatingThickness0_um": [75.0, 70.0, 80.0],
            "CoatingThickness100_um": [76.5, 71.4, 81.6],
        }
    )

    anodes = pd.DataFrame(
        {
            "AnodeId": ["Graphite_V1", "SiO_Graphite_V1"],
            "Name": ["Graphite", "SiO-Graphite"],
            "Chemistry": ["Graphite", "SiO_Graphite"],
            "RevSpecCapacity_mAhg": [360.0, 450.0],
            "MaxSpecCapacity_mAhg": [372.0, 500.0],
            "ArealWeight_mgcm2": [10.5, 8.0],
            "CollectorThickness_um": [10.0, 10.0],
            "CoatingDensity_gcm3": [1.6, 1.8],
            "CoatingThickness0_um": [85.0, 70.0],
            "CoatingThickness100_um": [89.25, 77.0],
        }
    )

    separators = pd.DataFrame(
        {
            "SeparatorId": ["PE_PP_20um", "Ceramic_25um"],
            "Name": ["PE/PP Trilayer", "Ceramic Coated PE"],
            "Thickness_um": [20.0, 25.0],
            "Porosity_pct": [40.0, 45.0],
            "Density_gcm3": [0.95, 1.2],
            "ArealWeight_mgcm2": [1.14, 1.65],
        }
    )

    electrolytes = pd.DataFrame(
        {
            "ElectrolyteId": ["LiPF6_EC_DMC", "LiPF6_EC_EMC"],
            "Name": ["LiPF6 in EC:DMC", "LiPF6 in EC:EMC"],
            "Density_gcm3": [1.25, 1.22],
            "Conductivity_Sm": [1.1, 1.0],
        }
    )

    packaging = pd.DataFrame(
        {
            "PresetName": ["Standard_Pouch"] * 3 + ["Thin_Pouch"] * 3,
            "LayerName": ["PET", "Aluminum", "PP", "PET", "Aluminum", "PP"],
            "Version": ["1.0"] * 6,
            "Thickness_um": [12.0, 40.0, 80.0, 10.0, 30.0, 60.0],
            "Porosity_pct": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "Density_gcm3": [1.38, 2.70, 0.95, 1.38, 2.70, 0.95],
        }
    )

    # Write to Excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        cathodes.to_excel(writer, sheet_name="CathodeMaterials", index=False)
        anodes.to_excel(writer, sheet_name="AnodeMaterials", index=False)
        separators.to_excel(writer, sheet_name="SeparatorMaterials", index=False)
        electrolytes.to_excel(writer, sheet_name="ElectrolyteModels", index=False)
        packaging.to_excel(writer, sheet_name="PackagingLayers", index=False)
