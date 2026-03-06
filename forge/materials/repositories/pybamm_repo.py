"""PyBaMM repository for CellCAD.

This module extracts cell parameters from PyBaMM parameter sets.
"""

from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    SeparatorMaterial,
)

from .base import MaterialRepository

# PyBaMM is optional - only import if available
try:
    import pybamm

    PYBAMM_AVAILABLE = True
except ImportError:
    PYBAMM_AVAILABLE = False


# Available PyBaMM parameter sets (built-in)
AVAILABLE_PARAMETER_SETS = [
    "Chen2020",  # NMC532/Graphite (LG M50)
    "Marquis2019",  # NMC811/Graphite
    "Ecker2015",  # NMC/Graphite (Kokam)
    "Ai2020",  # LFP/Graphite (A123)
    "Ramadass2004",  # LCO/Graphite (Sony)
    "Prada2013",  # LFP/Graphite
]

# Custom academic-validated parameter sets
CUSTOM_PARAMETER_SETS = [
    "Gunter2022",  # LG E78 Pouch (NCM652015/Graphite) - DOI: 10.1149/1945-7111/ac4e11
    "Stock2023",  # CATL 161Ah LFP Prismatic - DOI: 10.1016/j.electacta.2023.143341
    "Heenan2020",  # LG MJ1 18650 (NMC811/Graphite+Si) - DOI: 10.1149/1945-7111/ab728d
]

# All available parameter sets
ALL_PARAMETER_SETS = AVAILABLE_PARAMETER_SETS + CUSTOM_PARAMETER_SETS

# Chemistry detection map
CHEMISTRY_MAP = {
    "Chen2020": ("NMC532", "Graphite"),
    "Marquis2019": ("NMC811", "Graphite"),
    "Ecker2015": ("NMC", "Graphite"),
    "Ai2020": ("LFP", "Graphite"),
    "Ramadass2004": ("LCO", "Graphite"),
    "Prada2013": ("LFP", "Graphite"),
    # Custom academic-validated sets
    "Gunter2022": ("NCM652015", "Graphite"),
    "Stock2023": ("LFP", "Graphite"),
    "Heenan2020": ("NMC811", "Graphite_Si"),
}

# Typical specific capacities by chemistry [mAh/g]
CATHODE_CAPACITIES = {
    "NMC532": 165.0,
    "NMC622": 175.0,
    "NMC811": 200.0,
    "NCM652015": 180.0,  # Ni65 Co20 Mn15
    "NMC": 170.0,
    "LFP": 150.0,  # Updated to match Stock2023
    "LCO": 155.0,
}


def check_pybamm_available() -> bool:
    """Check if PyBaMM is available.

    Returns:
        True if PyBaMM is installed and importable
    """
    return PYBAMM_AVAILABLE


class PyBaMMRepository(MaterialRepository):
    """Repository that extracts material parameters from PyBaMM.

    This repository wraps PyBaMM ParameterValues to provide material
    properties for CellCAD calculations.

    Attributes:
        parameter_set: Name of the PyBaMM parameter set
        params: PyBaMM ParameterValues object
    """

    def __init__(self, parameter_set: str = "Chen2020"):
        """Initialize with a PyBaMM or custom parameter set.

        Args:
            parameter_set: Name of parameter set. Can be:
                - Built-in PyBaMM: "Chen2020", "Marquis2019", "Ai2020", etc.
                - Custom academic: "Gunter2022", "Stock2023", "Heenan2020"

        Raises:
            ImportError: If PyBaMM is not installed (for built-in sets only)
            ValueError: If parameter set is not found
        """
        self.parameter_set = parameter_set
        self._is_custom = parameter_set in CUSTOM_PARAMETER_SETS

        if self._is_custom:
            # Load custom academic-validated parameter set
            self.params = self._load_custom_parameters(parameter_set)
        else:
            # Load built-in PyBaMM parameter set
            if not PYBAMM_AVAILABLE:
                raise ImportError("PyBaMM is not installed. Install with: pip install pybamm")
            try:
                self.params = pybamm.ParameterValues(parameter_set)
            except Exception as e:
                raise ValueError(f"Failed to load parameter set '{parameter_set}': {e}")

    def _load_custom_parameters(self, set_name: str) -> dict:
        """Load custom parameter set from forge.materials.academic module.

        Args:
            set_name: Name of custom parameter set

        Returns:
            Dictionary of parameters

        Raises:
            ValueError: If set_name is not found
        """
        from forge.materials.academic import get_custom_parameters

        return get_custom_parameters(set_name)

    def _get_chemistry(self) -> tuple:
        """Detect cathode and anode chemistry from parameter set name.

        Returns:
            Tuple of (cathode_chemistry, anode_chemistry)
        """
        return CHEMISTRY_MAP.get(self.parameter_set, ("NMC", "Graphite"))

    def _safe_get(self, key: str, default: float = 0.0) -> float:
        """Safely get a parameter value with fallback.

        Works with both PyBaMM ParameterValues objects and plain dictionaries
        (for custom parameter sets).

        Args:
            key: Parameter key
            default: Default value if key not found

        Returns:
            Parameter value or default
        """
        try:
            if self._is_custom:
                # Custom params are plain dictionaries
                value = self.params.get(key, default)
            else:
                # PyBaMM ParameterValues
                value = self.params[key]

            # Handle callable parameters (functions of other params)
            if callable(value):
                return default
            return float(value)
        except (KeyError, TypeError):
            return default

    def _calculate_loading(self, electrode: str) -> float:
        """Calculate electrode loading [mg/cmÂ²].

        For custom parameter sets, uses directly specified loading if available.
        Otherwise calculates: Loading = thickness Ã— density Ã— active_fraction Ã— (1 - porosity) Ã— 100

        Args:
            electrode: "Positive" or "Negative"

        Returns:
            Loading in mg/cmÂ²
        """
        prefix = electrode

        # For custom sets, try to get directly specified loading first
        if self._is_custom:
            direct_loading = self._safe_get(f"{prefix} electrode loading [mg.cm-2]", 0.0)
            if direct_loading > 0:
                return direct_loading

        # Calculate from components
        thickness_m = self._safe_get(f"{prefix} electrode thickness [m]", 70e-6)
        thickness_cm = thickness_m * 100

        # Try to get density - different parameter names in different sets
        density_kg_m3 = self._safe_get(
            f"{prefix} electrode active material density [kg.m-3]",
            self._safe_get(f"{prefix} particle density [kg.m-3]", 4500),
        )
        density_g_cm3 = density_kg_m3 / 1000

        active_frac = self._safe_get(f"{prefix} electrode active material volume fraction", 0.6)
        porosity = self._safe_get(f"{prefix} electrode porosity", 0.3)

        # Loading = thickness Ã— density Ã— active_fraction Ã— (1 - porosity)
        loading_g_cm2 = thickness_cm * density_g_cm3 * active_frac * (1 - porosity)
        return loading_g_cm2 * 1000  # Convert to mg/cmÂ²

    def _calculate_coating_density(self, electrode: str) -> float:
        """Calculate effective coating density [g/cmÂ³].

        For custom parameter sets, uses directly specified coating density if available.

        Args:
            electrode: "Positive" or "Negative"

        Returns:
            Effective coating density in g/cmÂ³
        """
        prefix = electrode

        # For custom sets, try to get directly specified coating density first
        if self._is_custom:
            direct_density = self._safe_get(f"{prefix} electrode coating density [kg.m-3]", 0.0)
            if direct_density > 0:
                return direct_density / 1000  # Convert kg/m3 to g/cm3

        # Calculate from particle density and porosity
        density_kg_m3 = self._safe_get(
            f"{prefix} electrode active material density [kg.m-3]",
            self._safe_get(f"{prefix} particle density [kg.m-3]", 4500),
        )
        density_g_cm3 = density_kg_m3 / 1000

        porosity = self._safe_get(f"{prefix} electrode porosity", 0.3)

        return density_g_cm3 * (1 - porosity)

    # =========================================================================
    # MaterialRepository interface implementation
    # =========================================================================

    def list_cathodes(self) -> list[str]:
        """List available cathode material IDs."""
        return [f"{self.parameter_set}_cathode"]

    def get_cathode(self, material_id: str = None) -> CathodeMaterial:
        """Get cathode material from PyBaMM parameters.

        Args:
            material_id: Ignored for PyBaMM (only one cathode per set)

        Returns:
            CathodeMaterial with properties extracted from PyBaMM
        """
        cathode_chem, _ = self._get_chemistry()

        # Get thickness [Âµm]
        thickness_m = self._safe_get("Positive electrode thickness [m]", 70e-6)
        thickness_um = thickness_m * 1e6

        # Get collector thickness [Âµm]
        collector_m = self._safe_get("Positive current collector thickness [m]", 15e-6)
        collector_um = collector_m * 1e6

        # Get specific capacity
        spec_capacity = CATHODE_CAPACITIES.get(cathode_chem, 170.0)

        return CathodeMaterial(
            id=f"{self.parameter_set}_cathode",
            name=f"{self.parameter_set} {cathode_chem}",
            chemistry=cathode_chem,
            rev_spec_capacity_mahg=spec_capacity,
            max_spec_capacity_mahg=spec_capacity * 1.1,
            areal_weight_mgcm2=self._calculate_loading("Positive"),
            collector_thickness_um=collector_um,
            coating_density_gcm3=self._calculate_coating_density("Positive"),
            coating_thickness_0pct_um=thickness_um,
            coating_thickness_100pct_um=thickness_um * 1.02,  # ~2% swelling
        )

    def list_anodes(self) -> list[str]:
        """List available anode material IDs."""
        return [f"{self.parameter_set}_anode"]

    def get_anode(self, material_id: str = None) -> AnodeMaterial:
        """Get anode material from PyBaMM parameters.

        Args:
            material_id: Ignored for PyBaMM (only one anode per set)

        Returns:
            AnodeMaterial with properties extracted from PyBaMM
        """
        _, anode_chem = self._get_chemistry()

        # Get thickness [Âµm]
        thickness_m = self._safe_get("Negative electrode thickness [m]", 80e-6)
        thickness_um = thickness_m * 1e6

        # Get collector thickness [Âµm]
        collector_m = self._safe_get("Negative current collector thickness [m]", 10e-6)
        collector_um = collector_m * 1e6

        # Graphite typical capacity
        spec_capacity = 360.0

        return AnodeMaterial(
            id=f"{self.parameter_set}_anode",
            name=f"{self.parameter_set} {anode_chem}",
            chemistry=anode_chem,
            rev_spec_capacity_mahg=spec_capacity,
            max_spec_capacity_mahg=372.0,  # Theoretical graphite
            areal_weight_mgcm2=self._calculate_loading("Negative"),
            collector_thickness_um=collector_um,
            coating_density_gcm3=self._calculate_coating_density("Negative"),
            coating_thickness_0pct_um=thickness_um,
            coating_thickness_100pct_um=thickness_um * 1.05,  # ~5% swelling
        )

    def list_separators(self) -> list[str]:
        """List available separator material IDs."""
        return [f"{self.parameter_set}_separator"]

    def get_separator(self, material_id: str = None) -> SeparatorMaterial:
        """Get separator material from PyBaMM parameters.

        Args:
            material_id: Ignored for PyBaMM (only one separator per set)

        Returns:
            SeparatorMaterial with properties extracted from PyBaMM
        """
        # Get thickness [Âµm]
        thickness_m = self._safe_get("Separator thickness [m]", 20e-6)
        thickness_um = thickness_m * 1e6

        # Get porosity
        porosity = self._safe_get("Separator porosity", 0.4)
        porosity_pct = porosity * 100

        # Typical separator density (PE/PP)
        density = 0.95

        # Calculate areal weight
        areal_weight = thickness_um * density * (1 - porosity) / 10

        return SeparatorMaterial(
            id=f"{self.parameter_set}_separator",
            name=f"{self.parameter_set} Separator",
            thickness_um=thickness_um,
            porosity_pct=porosity_pct,
            density_gcm3=density,
            areal_weight_mgcm2=areal_weight,
        )

    def list_electrolytes(self) -> list[str]:
        """List available electrolyte model IDs."""
        return [f"{self.parameter_set}_electrolyte"]

    def get_electrolyte(self, electrolyte_id: str = None) -> ElectrolyteModel:
        """Get electrolyte model from PyBaMM parameters.

        Args:
            electrolyte_id: Ignored for PyBaMM (only one electrolyte per set)

        Returns:
            ElectrolyteModel with properties extracted from PyBaMM
        """
        # Try to get density from PyBaMM
        density_kg_m3 = self._safe_get("Electrolyte density [kg.m-3]", 1200)
        density_g_cm3 = density_kg_m3 / 1000

        return ElectrolyteModel(
            id=f"{self.parameter_set}_electrolyte",
            name=f"{self.parameter_set} Electrolyte",
            density_gcm3=density_g_cm3,
        )

    def get_parameter_summary(self) -> dict:
        """Get a summary of key parameters from the PyBaMM set.

        Returns:
            Dictionary with parameter summary
        """
        cathode_chem, anode_chem = self._get_chemistry()

        return {
            "parameter_set": self.parameter_set,
            "cathode_chemistry": cathode_chem,
            "anode_chemistry": anode_chem,
            "cathode_thickness_um": self._safe_get("Positive electrode thickness [m]", 70e-6) * 1e6,
            "anode_thickness_um": self._safe_get("Negative electrode thickness [m]", 80e-6) * 1e6,
            "separator_thickness_um": self._safe_get("Separator thickness [m]", 20e-6) * 1e6,
            "cathode_porosity": self._safe_get("Positive electrode porosity", 0.3),
            "anode_porosity": self._safe_get("Negative electrode porosity", 0.3),
            "separator_porosity": self._safe_get("Separator porosity", 0.4),
        }
