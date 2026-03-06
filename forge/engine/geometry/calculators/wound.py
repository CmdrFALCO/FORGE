"""Wound geometry calculator for cylindrical jellyroll cells.

This module calculates radial R positions for cells with wound
electrode assemblies (cylindrical form factor jellyroll).
"""

import math

from ..layer_stack import (
    WindingGeometry,
    WindLayer,
)
from ..swelling import SwellingProfile
from .base import InternalGeometryCalculator


class WoundGeometryCalculator(InternalGeometryCalculator):
    """Calculate radial positions for cylindrical wound jellyroll cells.

    Generates a complete WindingGeometry with all winds positioned
    from mandrel (center) to outer can wall.

    Wind structure (from center outward, for each wind):
    - Anode collector (Cu) - center of anode
    - Anode coating (inner side)
    - Separator (inner)
    - Cathode coating (inner side)
    - Cathode collector (Al) - center of cathode
    - Cathode coating (outer side)
    - Separator (outer)
    - Anode coating (outer side)
    ... next wind starts

    Note: This follows the standard jellyroll winding pattern where
    anode, separator, cathode, separator are wound together.
    """

    def __init__(self, swelling_profile: SwellingProfile | None = None):
        """Initialize calculator with optional swelling profile.

        Args:
            swelling_profile: SwellingProfile for EOL calculations.
                If None, no swelling is applied.
        """
        super().__init__(swelling_profile)

    def calculate(
        self,
        num_winds: int,
        mandrel_diameter_mm: float,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
        cathode_material: str = "NMC",
        anode_material: str = "Graphite",
        separator_material: str = "PP/PE/PP",
    ) -> WindingGeometry:
        """Calculate radial positions for all winds.

        Args:
            num_winds: Number of winding turns
            mandrel_diameter_mm: Inner mandrel/void diameter [mm]
            cathode_coating_um: Cathode coating thickness per side [um]
            cathode_collector_um: Cathode collector (Al) thickness [um]
            anode_coating_um: Anode coating thickness per side [um]
            anode_collector_um: Anode collector (Cu) thickness [um]
            separator_um: Separator thickness [um]
            cathode_material: Cathode active material name
            anode_material: Anode active material name
            separator_material: Separator material name

        Returns:
            WindingGeometry with all winds positioned
        """
        winds: list[WindLayer] = []
        r = mandrel_diameter_mm * 1000.0 / 2.0  # Current radius in um

        for wind_idx in range(num_winds):
            wind_r_inner = r

            # Anode collector
            t = self.apply_swelling("anode_collector", anode_collector_um)
            anode_collector_r = (r, r + t)
            r += t

            # Anode coating (inner side - toward center)
            t = self.apply_swelling("anode_coating", anode_coating_um)
            anode_coating_inner_r = (r, r + t)
            r += t

            # Inner separator
            t = self.apply_swelling("separator", separator_um)
            separator_inner_r = (r, r + t)
            r += t

            # Cathode coating (inner side)
            t = self.apply_swelling("cathode_coating", cathode_coating_um)
            cathode_coating_inner_r = (r, r + t)
            r += t

            # Cathode collector
            t = self.apply_swelling("cathode_collector", cathode_collector_um)
            cathode_collector_r = (r, r + t)
            r += t

            # Cathode coating (outer side)
            t = self.apply_swelling("cathode_coating", cathode_coating_um)
            cathode_coating_outer_r = (r, r + t)
            r += t

            # Outer separator
            t = self.apply_swelling("separator", separator_um)
            separator_outer_r = (r, r + t)
            r += t

            # Anode coating (outer side - toward can)
            t = self.apply_swelling("anode_coating", anode_coating_um)
            anode_coating_outer_r = (r, r + t)
            r += t

            wind_r_outer = r

            winds.append(
                WindLayer(
                    wind_index=wind_idx,
                    r_inner_um=wind_r_inner,
                    r_outer_um=wind_r_outer,
                    anode_collector_r=anode_collector_r,
                    anode_coating_inner_r=anode_coating_inner_r,
                    separator_inner_r=separator_inner_r,
                    cathode_coating_inner_r=cathode_coating_inner_r,
                    cathode_collector_r=cathode_collector_r,
                    cathode_coating_outer_r=cathode_coating_outer_r,
                    separator_outer_r=separator_outer_r,
                    anode_coating_outer_r=anode_coating_outer_r,
                )
            )

        outer_diameter_mm = 2 * r / 1000.0

        return WindingGeometry(
            winds=winds,
            num_winds=num_winds,
            mandrel_diameter_mm=mandrel_diameter_mm,
            outer_diameter_mm=outer_diameter_mm,
            chemistry=cathode_material,
            swelling_applied=self.is_swelling_applied,
            confidence="MEDIUM",
        )

    def calculate_wind_thickness(
        self,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
    ) -> float:
        """Calculate radial thickness of one complete wind.

        Args:
            cathode_coating_um: Cathode coating thickness per side [um]
            cathode_collector_um: Cathode collector thickness [um]
            anode_coating_um: Anode coating thickness per side [um]
            anode_collector_um: Anode collector thickness [um]
            separator_um: Separator thickness [um]

        Returns:
            Wind thickness in um
        """
        return (
            self.apply_swelling("anode_collector", anode_collector_um)
            + 2 * self.apply_swelling("anode_coating", anode_coating_um)
            + 2 * self.apply_swelling("separator", separator_um)
            + 2 * self.apply_swelling("cathode_coating", cathode_coating_um)
            + self.apply_swelling("cathode_collector", cathode_collector_um)
        )

    def estimate_num_winds(
        self,
        mandrel_diameter_mm: float,
        jellyroll_diameter_mm: float,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
    ) -> int:
        """Estimate number of winds from available radial space.

        Args:
            mandrel_diameter_mm: Inner mandrel/void diameter [mm]
            jellyroll_diameter_mm: Outer jellyroll diameter [mm]
            cathode_coating_um: Cathode coating thickness per side [um]
            cathode_collector_um: Cathode collector thickness [um]
            anode_coating_um: Anode coating thickness per side [um]
            anode_collector_um: Anode collector thickness [um]
            separator_um: Separator thickness [um]

        Returns:
            Estimated number of winds
        """
        available_thickness_um = (jellyroll_diameter_mm - mandrel_diameter_mm) * 500.0
        wind_thickness = self.calculate_wind_thickness(
            cathode_coating_um,
            cathode_collector_um,
            anode_coating_um,
            anode_collector_um,
            separator_um,
        )
        return max(1, int(available_thickness_um / wind_thickness))

    def calculate_electrode_length(
        self,
        num_winds: int,
        mandrel_diameter_mm: float,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
    ) -> float:
        """Calculate total electrode strip length.

        Uses the Archimedean spiral approximation.

        Args:
            num_winds: Number of winding turns
            mandrel_diameter_mm: Inner mandrel/void diameter [mm]
            cathode_coating_um: Cathode coating thickness per side [um]
            cathode_collector_um: Cathode collector thickness [um]
            anode_coating_um: Anode coating thickness per side [um]
            anode_collector_um: Anode collector thickness [um]
            separator_um: Separator thickness [um]

        Returns:
            Total electrode length in mm
        """
        wind_thickness_um = self.calculate_wind_thickness(
            cathode_coating_um,
            cathode_collector_um,
            anode_coating_um,
            anode_collector_um,
            separator_um,
        )
        wind_thickness_mm = wind_thickness_um / 1000.0
        r0 = mandrel_diameter_mm / 2.0

        # Archimedean spiral: r = r0 + b*theta
        # where b = wind_thickness / (2*pi) for one thickness per revolution
        wind_thickness_mm / (2 * math.pi)

        # Arc length of spiral from 0 to n*2*pi
        # L = integral of sqrt(r^2 + (dr/dtheta)^2) d_theta
        # For r = r0 + b*theta: dr/dtheta = b
        # Simplified for many turns: L ≈ pi * n * (2*r0 + n*wind_thickness)
        total_length = math.pi * num_winds * (2 * r0 + num_winds * wind_thickness_mm)

        return total_length
