"""Configurable validation thresholds."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class ValidationThresholds:
    """Threshold values for validation rules.

    All values can be overridden at instantiation.
    Default values represent typical industry standards.
    """

    # --- Dimensional Tolerances ---
    # Stack/jellyroll must fit with this margin (mm)
    casing_fit_margin_mm: float = 0.0

    # Layer thickness consistency tolerance (fraction, e.g., 0.10 = 10%)
    layer_thickness_tolerance: float = 0.10

    # --- Safety Geometry ---
    # Minimum anode overhang beyond cathode (mm)
    min_anode_overhang_mm: float = 0.0

    # Minimum separator overhang beyond anode (mm)
    min_separator_overhang_mm: float = 0.0

    # N/P ratio acceptable range
    np_ratio_min: float = 1.0
    np_ratio_max: float = 1.3

    # --- Manufacturing Limits ---
    # Minimum layer thicknesses (um)
    min_coating_thickness_um: float = 30.0
    min_collector_thickness_um: float = 5.0
    min_separator_thickness_um: float = 8.0

    # Maximum layer counts
    max_electrode_pairs_pouch: int = 100
    max_electrode_pairs_prismatic: int = 120
    max_winds_cylindrical: int = 60

    # --- Cross-Validation Tolerances ---
    # Acceptable deviation from declared values (fraction)
    capacity_tolerance: float = 0.10
    mass_tolerance: float = 0.10
    energy_density_tolerance: float = 0.15

    # --- Chemistry-Specific Overrides ---
    CHEMISTRY_OVERRIDES: ClassVar[dict[str, dict]] = {
        "LFP": {
            "np_ratio_max": 1.25,  # LFP more tolerant
            "min_coating_thickness_um": 40.0,  # Thicker LFP coatings typical
        },
        "NMC811": {
            "np_ratio_max": 1.20,  # NMC811 needs tighter control
        },
        "NMC622": {
            "np_ratio_max": 1.25,
        },
    }

    @classmethod
    def for_chemistry(cls, chemistry: str, **overrides) -> "ValidationThresholds":
        """Get thresholds with chemistry-specific adjustments."""
        base = cls(**overrides)

        # Apply chemistry overrides
        normalized = chemistry.upper().replace("NCM", "NMC")
        if normalized in cls.CHEMISTRY_OVERRIDES:
            chem_overrides = cls.CHEMISTRY_OVERRIDES[normalized]
            for key, value in chem_overrides.items():
                if key not in overrides:  # Don't override explicit user values
                    setattr(base, key, value)

        return base


# Default thresholds instance
DEFAULT_THRESHOLDS = ValidationThresholds()
