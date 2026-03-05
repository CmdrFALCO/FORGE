"""Stacked geometry calculator for pouch/prismatic cells.

This module calculates layer-by-layer Z positions for cells with
stacked electrode assemblies (pouch and prismatic form factors).
"""

from .base import InternalGeometryCalculator
from ..layer_stack import (
    Layer,
    LayerType,
    LayerStackGeometry,
)
from ..swelling import SwellingProfile


class StackedGeometryCalculator(InternalGeometryCalculator):
    """Calculate layer positions for pouch/prismatic stacked cells.

    Generates a complete LayerStackGeometry with all layers positioned
    from bottom to top.

    Stack structure (bottom to top, for each electrode pair):
    - Separator
    - Anode coating (bottom side of collector)
    - Anode collector (Cu)
    - Anode coating (top side of collector)
    - Separator
    - Cathode coating (bottom side of collector)
    - Cathode collector (Al)
    - Cathode coating (top side of collector)
    ... repeated for num_electrode_pairs
    - Final separator (top)

    Note: Double-sided coating on collectors is standard.
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
        num_electrode_pairs: int,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
        cathode_material: str = "NMC",
        anode_material: str = "Graphite",
        separator_material: str = "PP/PE/PP",
        collector_materials: tuple[str, str] = ("Al", "Cu"),
    ) -> LayerStackGeometry:
        """Calculate layer-by-layer Z positions.

        Args:
            num_electrode_pairs: Number of cathode-anode pairs (layers)
            cathode_coating_um: Cathode coating thickness per side [µm]
            cathode_collector_um: Cathode collector (Al) thickness [µm]
            anode_coating_um: Anode coating thickness per side [µm]
            anode_collector_um: Anode collector (Cu) thickness [µm]
            separator_um: Separator thickness [µm]
            cathode_material: Cathode active material name
            anode_material: Anode active material name
            separator_material: Separator material name
            collector_materials: Tuple of (cathode_collector, anode_collector) material names

        Returns:
            LayerStackGeometry with all layers positioned
        """
        layers: list[Layer] = []
        z = 0.0  # Current Z position in µm
        layer_idx = 0

        cathode_collector_mat, anode_collector_mat = collector_materials

        for pair_idx in range(num_electrode_pairs):
            # Bottom separator
            t = self.apply_swelling("separator", separator_um)
            layers.append(
                Layer(
                    layer_type=LayerType.SEPARATOR,
                    z_bottom_um=z,
                    thickness_um=t,
                    material=separator_material,
                    layer_index=layer_idx,
                )
            )
            z += t
            layer_idx += 1

            # Anode coating (bottom side of collector)
            t = self.apply_swelling("anode_coating", anode_coating_um)
            layers.append(
                Layer(
                    layer_type=LayerType.ANODE_COATING,
                    z_bottom_um=z,
                    thickness_um=t,
                    material=anode_material,
                    layer_index=layer_idx,
                )
            )
            z += t
            layer_idx += 1

            # Anode collector (Cu)
            t = self.apply_swelling("anode_collector", anode_collector_um)
            layers.append(
                Layer(
                    layer_type=LayerType.ANODE_COLLECTOR,
                    z_bottom_um=z,
                    thickness_um=t,
                    material=anode_collector_mat,
                    layer_index=layer_idx,
                )
            )
            z += t
            layer_idx += 1

            # Anode coating (top side of collector)
            t = self.apply_swelling("anode_coating", anode_coating_um)
            layers.append(
                Layer(
                    layer_type=LayerType.ANODE_COATING,
                    z_bottom_um=z,
                    thickness_um=t,
                    material=anode_material,
                    layer_index=layer_idx,
                )
            )
            z += t
            layer_idx += 1

            # Middle separator
            t = self.apply_swelling("separator", separator_um)
            layers.append(
                Layer(
                    layer_type=LayerType.SEPARATOR,
                    z_bottom_um=z,
                    thickness_um=t,
                    material=separator_material,
                    layer_index=layer_idx,
                )
            )
            z += t
            layer_idx += 1

            # Cathode coating (bottom side of collector)
            t = self.apply_swelling("cathode_coating", cathode_coating_um)
            layers.append(
                Layer(
                    layer_type=LayerType.CATHODE_COATING,
                    z_bottom_um=z,
                    thickness_um=t,
                    material=cathode_material,
                    layer_index=layer_idx,
                )
            )
            z += t
            layer_idx += 1

            # Cathode collector (Al)
            t = self.apply_swelling("cathode_collector", cathode_collector_um)
            layers.append(
                Layer(
                    layer_type=LayerType.CATHODE_COLLECTOR,
                    z_bottom_um=z,
                    thickness_um=t,
                    material=cathode_collector_mat,
                    layer_index=layer_idx,
                )
            )
            z += t
            layer_idx += 1

            # Cathode coating (top side of collector)
            t = self.apply_swelling("cathode_coating", cathode_coating_um)
            layers.append(
                Layer(
                    layer_type=LayerType.CATHODE_COATING,
                    z_bottom_um=z,
                    thickness_um=t,
                    material=cathode_material,
                    layer_index=layer_idx,
                )
            )
            z += t
            layer_idx += 1

        # Final top separator
        t = self.apply_swelling("separator", separator_um)
        layers.append(
            Layer(
                layer_type=LayerType.SEPARATOR,
                z_bottom_um=z,
                thickness_um=t,
                material=separator_material,
                layer_index=layer_idx,
            )
        )
        z += t

        return LayerStackGeometry(
            layers=layers,
            num_electrode_pairs=num_electrode_pairs,
            total_thickness_um=z,
            chemistry=cathode_material,
            swelling_applied=self.is_swelling_applied,
            confidence="MEDIUM",
        )

    def calculate_unit_cell_thickness(
        self,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
    ) -> float:
        """Calculate thickness of one electrode pair (unit cell).

        This is useful for estimating layer count from total stack thickness.

        Args:
            cathode_coating_um: Cathode coating thickness per side [µm]
            cathode_collector_um: Cathode collector thickness [µm]
            anode_coating_um: Anode coating thickness per side [µm]
            anode_collector_um: Anode collector thickness [µm]
            separator_um: Separator thickness [µm]

        Returns:
            Unit cell thickness in µm
        """
        # Unit cell: sep + anode_coat + anode_coll + anode_coat + sep + cath_coat + cath_coll + cath_coat
        return (
            2 * self.apply_swelling("separator", separator_um)
            + 2 * self.apply_swelling("anode_coating", anode_coating_um)
            + self.apply_swelling("anode_collector", anode_collector_um)
            + 2 * self.apply_swelling("cathode_coating", cathode_coating_um)
            + self.apply_swelling("cathode_collector", cathode_collector_um)
        )

    def estimate_layer_count(
        self,
        available_thickness_um: float,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
    ) -> int:
        """Estimate number of electrode pairs that fit in available space.

        Args:
            available_thickness_um: Available internal thickness [µm]
            cathode_coating_um: Cathode coating thickness per side [µm]
            cathode_collector_um: Cathode collector thickness [µm]
            anode_coating_um: Anode coating thickness per side [µm]
            anode_collector_um: Anode collector thickness [µm]
            separator_um: Separator thickness [µm]

        Returns:
            Estimated number of electrode pairs
        """
        unit_cell = self.calculate_unit_cell_thickness(
            cathode_coating_um,
            cathode_collector_um,
            anode_coating_um,
            anode_collector_um,
            separator_um,
        )

        # Account for final separator
        final_separator = self.apply_swelling("separator", separator_um)
        usable = available_thickness_um - final_separator

        return max(1, int(usable / unit_cell))
