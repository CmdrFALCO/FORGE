"""Base class for internal geometry calculators.

This module defines the abstract base class for geometry calculators
that compute layer positions from cell design parameters.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..layer_stack import (
        LayerStackGeometry,
        WindingGeometry,
    )
    from ..swelling import SwellingProfile


class InternalGeometryCalculator(ABC):
    """Abstract base class for internal geometry calculators.

    Subclasses implement specific calculation methods for different
    cell types (stacked vs wound).

    Attributes:
        swelling_profile: Swelling profile to apply (or None for BOL)
    """

    def __init__(self, swelling_profile: "SwellingProfile | None" = None):
        """Initialize calculator with optional swelling profile.

        Args:
            swelling_profile: SwellingProfile to apply for EOL calculations.
                If None, no swelling is applied (BOL state).
        """
        from ..swelling import SwellingProfile

        self.swelling_profile = swelling_profile or SwellingProfile.no_swelling()

    @abstractmethod
    def calculate(self, **kwargs) -> "LayerStackGeometry | WindingGeometry":
        """Calculate the internal geometry.

        Args:
            **kwargs: Cell-specific parameters

        Returns:
            LayerStackGeometry for stacked cells or WindingGeometry for wound cells
        """
        pass

    def apply_swelling(self, component: str, thickness_um: float) -> float:
        """Apply swelling to a component thickness.

        Args:
            component: Component name (e.g., "cathode_coating", "separator")
            thickness_um: Original thickness in micrometers

        Returns:
            Swollen thickness in micrometers
        """
        return self.swelling_profile.apply_to_thickness(component, thickness_um)

    @property
    def is_swelling_applied(self) -> bool:
        """Check if swelling is being applied.

        Returns:
            True if any swelling factor is > 1.0
        """
        return (
            self.swelling_profile.cathode_coating > 1.0
            or self.swelling_profile.anode_coating > 1.0
            or self.swelling_profile.separator > 1.0
        )
