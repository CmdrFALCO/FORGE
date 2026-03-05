"""Material data models for FORGE engine.

This module defines dataclasses for battery cell materials including:
- CathodeMaterial: Cathode active material and collector properties
- AnodeMaterial: Anode active material and collector properties
- SeparatorMaterial: Separator film properties
- ElectrolyteModel: Electrolyte properties
- PackagingLayer: Individual layers in pouch foil or other packaging
"""

from dataclasses import dataclass

# Material density constants [g/cm³]
# Previously in constants.py — now co-located with material dataclasses
DENSITY_ALUMINUM = 2.70
DENSITY_COPPER = 8.96
DENSITY_NICKEL = 8.90
DENSITY_PP = 0.90  # Polypropylene
DENSITY_PET = 1.38  # Polyethylene terephthalate
DENSITY_PE = 0.95  # Polyethylene

# Chemistry voltage constants [V]
NMC_NOMINAL_VOLTAGE = 3.65
LFP_NOMINAL_VOLTAGE = 3.20


@dataclass
class CathodeMaterial:
    """Cathode material properties.

    Attributes:
        id: Unique identifier for the material
        name: Display name
        chemistry: Chemistry type (NMC811, NMC622, LFP, etc.)
        rev_spec_capacity_mahg: Reversible specific capacity [mAh/g]
        max_spec_capacity_mahg: Maximum specific capacity [mAh/g]
        areal_weight_mgcm2: Coating loading/areal weight [mg/cm²]
        collector_thickness_um: Current collector (Al foil) thickness [µm]
        coating_density_gcm3: Coating bulk density [g/cm³]
        coating_thickness_0pct_um: Coating thickness at 0% SoC [µm]
        coating_thickness_100pct_um: Coating thickness at 100% SoC [µm]
    """

    id: str
    name: str
    chemistry: str
    rev_spec_capacity_mahg: float
    max_spec_capacity_mahg: float
    areal_weight_mgcm2: float
    collector_thickness_um: float
    coating_density_gcm3: float
    coating_thickness_0pct_um: float
    coating_thickness_100pct_um: float


@dataclass
class AnodeMaterial:
    """Anode material properties.

    Attributes:
        id: Unique identifier for the material
        name: Display name
        chemistry: Chemistry type (Graphite, SiO_Graphite, etc.)
        rev_spec_capacity_mahg: Reversible specific capacity [mAh/g]
        max_spec_capacity_mahg: Maximum specific capacity [mAh/g]
        areal_weight_mgcm2: Coating loading/areal weight [mg/cm²]
        collector_thickness_um: Current collector (Cu foil) thickness [µm]
        coating_density_gcm3: Coating bulk density [g/cm³]
        coating_thickness_0pct_um: Coating thickness at 0% SoC [µm]
        coating_thickness_100pct_um: Coating thickness at 100% SoC [µm]
    """

    id: str
    name: str
    chemistry: str
    rev_spec_capacity_mahg: float
    max_spec_capacity_mahg: float
    areal_weight_mgcm2: float
    collector_thickness_um: float
    coating_density_gcm3: float
    coating_thickness_0pct_um: float
    coating_thickness_100pct_um: float


@dataclass
class SeparatorMaterial:
    """Separator material properties.

    Attributes:
        id: Unique identifier for the material
        name: Display name
        thickness_um: Separator thickness [µm]
        porosity_pct: Porosity [%]
        density_gcm3: Bulk material density [g/cm³]
        areal_weight_mgcm2: Areal weight [mg/cm²]
    """

    id: str
    name: str
    thickness_um: float
    porosity_pct: float
    density_gcm3: float
    areal_weight_mgcm2: float


@dataclass
class ElectrolyteModel:
    """Electrolyte properties.

    Attributes:
        id: Unique identifier for the electrolyte
        name: Display name
        density_gcm3: Electrolyte density [g/cm³]
        conductivity_sm: Ionic conductivity [S/m] (optional)
    """

    id: str
    name: str
    density_gcm3: float
    conductivity_sm: float | None = None


@dataclass
class PackagingLayer:
    """Individual layer in packaging material (e.g., pouch foil).

    Used for multi-layer pouch foil composition (e.g., PET/Al/PP).

    Attributes:
        name: Layer material name (e.g., "Aluminum", "PP", "PET")
        version: Version identifier for the layer specification
        thickness_um: Layer thickness [µm]
        porosity_pct: Porosity [%]
        density_gcm3: Bulk material density [g/cm³]
    """

    name: str
    version: str
    thickness_um: float
    porosity_pct: float
    density_gcm3: float

    @property
    def effective_density_gcm3(self) -> float:
        """Calculate effective density accounting for porosity.

        Returns:
            Effective density [g/cm³]
        """
        return self.density_gcm3 * (1 - self.porosity_pct / 100)

    @property
    def areal_weight_mgcm2(self) -> float:
        """Calculate areal weight from thickness and effective density.

        Returns:
            Areal weight [mg/cm²]
        """
        return self.thickness_um * self.effective_density_gcm3 / 10


@dataclass
class TabConfig:
    """Tab (terminal) configuration for a single electrode.

    Attributes:
        material: Tab material name (e.g., "Copper", "Aluminum", "Nickel")
        height_mm: Tab height [mm]
        width_mm: Tab width [mm]
        thickness_mm: Tab thickness [mm]
        density_gcm3: Material density [g/cm³]
    """

    material: str
    height_mm: float
    width_mm: float
    thickness_mm: float
    density_gcm3: float

    @property
    def volume_cm3(self) -> float:
        """Calculate tab volume.

        Returns:
            Tab volume [cm³]
        """
        return self.height_mm * self.width_mm * self.thickness_mm / 1000

    @property
    def mass_g(self) -> float:
        """Calculate tab mass.

        Returns:
            Tab mass [g]
        """
        return self.volume_cm3 * self.density_gcm3
