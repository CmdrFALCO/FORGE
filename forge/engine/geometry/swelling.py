"""Swelling profiles for battery cell components.

This module provides per-component swelling factors for EOL (End of Life)
thickness calculations. Swelling is chemistry-dependent and applies only
to the thickness direction (Z for stacked, R for wound cells).
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class SwellingProfile:
    """Per-component swelling factors (BOL to EOL thickness multipliers).

    Values represent typical EOL state after ~1000 cycles.
    Swelling is thickness-only (Z-direction for stacked, R-direction for wound).

    Attributes:
        cathode_coating: Cathode active material swelling factor
        anode_coating: Anode active material swelling factor (graphite ~5-10%)
        separator: Separator swelling factor
        current_collector: Metal foil swelling factor (metals don't swell)
        pouch_film: Pouch film swelling factor (accommodates internal swelling)
        can_wall: Can wall swelling factor (rigid constraint)
    """

    cathode_coating: float = 1.05
    anode_coating: float = 1.08
    separator: float = 1.02
    current_collector: float = 1.00  # Metals don't swell
    pouch_film: float = 1.00  # Accommodates internal swelling
    can_wall: float = 1.00  # Rigid constraint

    # Chemistry-specific profiles based on literature
    CHEMISTRY_PROFILES: ClassVar[dict[str, "SwellingProfile"]] = {}

    @classmethod
    def for_chemistry(cls, chemistry: str) -> "SwellingProfile":
        """Get swelling profile for specific cathode chemistry.

        Args:
            chemistry: Cathode chemistry (e.g., "NMC811", "LFP", "NCM712")

        Returns:
            SwellingProfile with chemistry-appropriate swelling factors
        """
        # Normalize chemistry name (handle NCM vs NMC variants)
        normalized = chemistry.upper().replace("NCM", "NMC")

        profiles = {
            # LFP has lower swelling due to stable olivine structure
            "LFP": cls(
                cathode_coating=1.03,
                anode_coating=1.06,
                separator=1.01,
            ),
            # NMC811 has higher swelling due to high-Ni content
            "NMC811": cls(
                cathode_coating=1.06,
                anode_coating=1.10,
                separator=1.02,
            ),
            # NMC622 moderate swelling
            "NMC622": cls(
                cathode_coating=1.05,
                anode_coating=1.08,
                separator=1.02,
            ),
            # NMC712 (NCM712) - between 622 and 811
            "NMC712": cls(
                cathode_coating=1.05,
                anode_coating=1.09,
                separator=1.02,
            ),
            # NMC532 lower Ni content, lower swelling
            "NMC532": cls(
                cathode_coating=1.04,
                anode_coating=1.07,
                separator=1.02,
            ),
            # NMC111 balanced composition
            "NMC111": cls(
                cathode_coating=1.04,
                anode_coating=1.07,
                separator=1.02,
            ),
            # NCA similar to NMC811
            "NCA": cls(
                cathode_coating=1.06,
                anode_coating=1.10,
                separator=1.02,
            ),
            # LCO (legacy chemistry)
            "LCO": cls(
                cathode_coating=1.04,
                anode_coating=1.07,
                separator=1.02,
            ),
        }

        return profiles.get(normalized, cls())  # Default profile if unknown

    @classmethod
    def no_swelling(cls) -> "SwellingProfile":
        """Get a profile with no swelling (BOL state).

        Returns:
            SwellingProfile with all factors set to 1.0
        """
        return cls(
            cathode_coating=1.0,
            anode_coating=1.0,
            separator=1.0,
            current_collector=1.0,
            pouch_film=1.0,
            can_wall=1.0,
        )

    def apply_to_thickness(self, component: str, thickness_um: float) -> float:
        """Apply swelling factor to component thickness.

        Args:
            component: Component name, one of:
                - "cathode_coating"
                - "anode_coating"
                - "separator"
                - "cathode_collector" or "anode_collector"
                - "pouch_film"
                - "can_wall"
            thickness_um: Original thickness in micrometers

        Returns:
            Swollen thickness in micrometers
        """
        factors = {
            "cathode_coating": self.cathode_coating,
            "anode_coating": self.anode_coating,
            "separator": self.separator,
            "cathode_collector": self.current_collector,
            "anode_collector": self.current_collector,
            "pouch_film": self.pouch_film,
            "can_wall": self.can_wall,
        }
        return thickness_um * factors.get(component, 1.0)

    def get_stack_swelling_factor(self) -> float:
        """Estimate overall stack thickness swelling.

        This is a rough estimate based on typical electrode layer composition.
        Assumes approximately:
        - 40% cathode coating
        - 40% anode coating
        - 10% separator
        - 10% current collectors

        Returns:
            Approximate overall stack swelling factor
        """
        return (
            0.40 * self.cathode_coating
            + 0.40 * self.anode_coating
            + 0.10 * self.separator
            + 0.10 * self.current_collector
        )

    def describe(self) -> str:
        """Get human-readable description of swelling profile.

        Returns:
            Multi-line description string
        """
        return (
            f"Swelling Profile:\n"
            f"  Cathode coating: {(self.cathode_coating - 1) * 100:.1f}%\n"
            f"  Anode coating: {(self.anode_coating - 1) * 100:.1f}%\n"
            f"  Separator: {(self.separator - 1) * 100:.1f}%\n"
            f"  Current collector: {(self.current_collector - 1) * 100:.1f}%"
        )


# Pre-defined profiles for common chemistries
SWELLING_LFP = SwellingProfile.for_chemistry("LFP")
SWELLING_NMC811 = SwellingProfile.for_chemistry("NMC811")
SWELLING_NMC622 = SwellingProfile.for_chemistry("NMC622")
SWELLING_NCA = SwellingProfile.for_chemistry("NCA")
SWELLING_NONE = SwellingProfile.no_swelling()
