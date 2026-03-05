"""Layer stack geometry for battery cells.

This module provides data structures for representing layer-by-layer
positions in stacked cells (pouch/prismatic) and radial positions
in wound cells (cylindrical jellyroll).
"""

from dataclasses import dataclass, field
from enum import Enum


class LayerType(str, Enum):
    """Type of layer in the electrode stack."""

    CATHODE_COLLECTOR = "cathode_collector"
    CATHODE_COATING = "cathode_coating"
    SEPARATOR = "separator"
    ANODE_COATING = "anode_coating"
    ANODE_COLLECTOR = "anode_collector"


@dataclass
class Layer:
    """Single layer in the electrode stack.

    Represents a single layer with its position, thickness, and material.
    For stacked cells, z_bottom_um is the position from the stack bottom.

    Attributes:
        layer_type: Type of layer (collector, coating, separator)
        z_bottom_um: Position from stack bottom in micrometers
        thickness_um: Layer thickness in micrometers (with swelling applied)
        material: Material name (e.g., "Al", "NMC811", "Graphite", "Cu")
        layer_index: 0-based index in the complete stack
    """

    layer_type: LayerType
    z_bottom_um: float
    thickness_um: float
    material: str
    layer_index: int

    @property
    def z_top_um(self) -> float:
        """Top Z position of layer in micrometers."""
        return self.z_bottom_um + self.thickness_um

    @property
    def z_center_um(self) -> float:
        """Center Z position of layer in micrometers."""
        return self.z_bottom_um + self.thickness_um / 2

    @property
    def z_bottom_mm(self) -> float:
        """Bottom Z position in millimeters."""
        return self.z_bottom_um / 1000.0

    @property
    def z_top_mm(self) -> float:
        """Top Z position in millimeters."""
        return self.z_top_um / 1000.0

    @property
    def thickness_mm(self) -> float:
        """Layer thickness in millimeters."""
        return self.thickness_um / 1000.0


@dataclass
class LayerStackGeometry:
    """Complete layer-by-layer stack geometry for stacked cells.

    This is the primary output for pouch and prismatic cell calculations.
    Contains all layers with their positions and materials.

    Attributes:
        layers: List of Layer objects in Z order (bottom to top)
        num_electrode_pairs: Number of cathode-anode pairs
        total_thickness_um: Total stack thickness in micrometers
        chemistry: Cathode chemistry (e.g., "NMC811")
        swelling_applied: Whether EOL swelling was applied
        confidence: Data confidence level
    """

    layers: list[Layer] = field(default_factory=list)
    num_electrode_pairs: int = 0
    total_thickness_um: float = 0.0

    # Metadata
    chemistry: str = ""
    swelling_applied: bool = False
    confidence: str = "MEDIUM"

    @property
    def total_thickness_mm(self) -> float:
        """Total stack thickness in millimeters."""
        return self.total_thickness_um / 1000.0

    @property
    def num_layers(self) -> int:
        """Total number of layers in the stack."""
        return len(self.layers)

    def get_layers_by_type(self, layer_type: LayerType) -> list[Layer]:
        """Get all layers of a specific type.

        Args:
            layer_type: Type of layer to filter

        Returns:
            List of layers matching the type
        """
        return [layer for layer in self.layers if layer.layer_type == layer_type]

    def get_cathode_layers(self) -> list[Layer]:
        """Get all cathode coating layers."""
        return self.get_layers_by_type(LayerType.CATHODE_COATING)

    def get_anode_layers(self) -> list[Layer]:
        """Get all anode coating layers."""
        return self.get_layers_by_type(LayerType.ANODE_COATING)

    def get_separator_layers(self) -> list[Layer]:
        """Get all separator layers."""
        return self.get_layers_by_type(LayerType.SEPARATOR)

    def get_collector_layers(self) -> list[Layer]:
        """Get all current collector layers (both cathode and anode)."""
        return self.get_layers_by_type(
            LayerType.CATHODE_COLLECTOR
        ) + self.get_layers_by_type(LayerType.ANODE_COLLECTOR)

    def to_z_coordinates_mm(self) -> list[float]:
        """Get Z coordinates of all layer boundaries in mm.

        Returns:
            List of Z coordinates starting from 0.0 (bottom)
        """
        coords = [0.0]
        for layer in self.layers:
            coords.append(layer.z_top_um / 1000.0)
        return coords

    def to_layer_summary(self) -> dict[str, int]:
        """Get summary of layer counts by type.

        Returns:
            Dict mapping layer type to count
        """
        summary: dict[str, int] = {}
        for layer_type in LayerType:
            count = len(self.get_layers_by_type(layer_type))
            if count > 0:
                summary[layer_type.value] = count
        return summary

    def get_material_thicknesses(self) -> dict[str, float]:
        """Get total thickness by material in micrometers.

        Returns:
            Dict mapping material name to total thickness
        """
        thicknesses: dict[str, float] = {}
        for layer in self.layers:
            if layer.material not in thicknesses:
                thicknesses[layer.material] = 0.0
            thicknesses[layer.material] += layer.thickness_um
        return thicknesses


@dataclass
class WindLayer:
    """Single wind in jellyroll with sub-layer positions.

    Each wind contains all electrode and separator layers at a specific
    radial position. Positions are given as (r_inner, r_outer) tuples.

    Attributes:
        wind_index: 0-based index of this wind (0 = innermost)
        r_inner_um: Inner radius of this wind in micrometers
        r_outer_um: Outer radius after all layers in micrometers
        anode_collector_r: (r_inner, r_outer) of anode collector
        anode_coating_inner_r: (r_inner, r_outer) of inner anode coating
        separator_inner_r: (r_inner, r_outer) of inner separator
        cathode_coating_inner_r: (r_inner, r_outer) of inner cathode coating
        cathode_collector_r: (r_inner, r_outer) of cathode collector
        cathode_coating_outer_r: (r_inner, r_outer) of outer cathode coating
        separator_outer_r: (r_inner, r_outer) of outer separator
        anode_coating_outer_r: (r_inner, r_outer) of outer anode coating
    """

    wind_index: int
    r_inner_um: float
    r_outer_um: float

    # Sub-layers within this wind (order: anode -> separator -> cathode -> separator -> anode)
    anode_collector_r: tuple[float, float] = (0.0, 0.0)
    anode_coating_inner_r: tuple[float, float] = (0.0, 0.0)
    separator_inner_r: tuple[float, float] = (0.0, 0.0)
    cathode_coating_inner_r: tuple[float, float] = (0.0, 0.0)
    cathode_collector_r: tuple[float, float] = (0.0, 0.0)
    cathode_coating_outer_r: tuple[float, float] = (0.0, 0.0)
    separator_outer_r: tuple[float, float] = (0.0, 0.0)
    anode_coating_outer_r: tuple[float, float] = (0.0, 0.0)

    @property
    def r_inner_mm(self) -> float:
        """Inner radius in millimeters."""
        return self.r_inner_um / 1000.0

    @property
    def r_outer_mm(self) -> float:
        """Outer radius in millimeters."""
        return self.r_outer_um / 1000.0

    @property
    def thickness_um(self) -> float:
        """Radial thickness of this wind in micrometers."""
        return self.r_outer_um - self.r_inner_um

    @property
    def thickness_mm(self) -> float:
        """Radial thickness of this wind in millimeters."""
        return self.thickness_um / 1000.0


@dataclass
class WindingGeometry:
    """Radial geometry for wound cylindrical cells.

    Contains all winds with their radial positions for jellyroll cells.

    Attributes:
        winds: List of WindLayer objects (innermost to outermost)
        num_winds: Total number of winds
        mandrel_diameter_mm: Inner mandrel/void diameter
        outer_diameter_mm: Outer diameter of the jellyroll
        chemistry: Cathode chemistry
        swelling_applied: Whether EOL swelling was applied
        confidence: Data confidence level
    """

    winds: list[WindLayer] = field(default_factory=list)
    num_winds: int = 0
    mandrel_diameter_mm: float = 0.0
    outer_diameter_mm: float = 0.0

    chemistry: str = ""
    swelling_applied: bool = False
    confidence: str = "MEDIUM"

    @property
    def mandrel_radius_um(self) -> float:
        """Inner mandrel radius in micrometers."""
        return self.mandrel_diameter_mm * 1000.0 / 2.0

    @property
    def outer_radius_um(self) -> float:
        """Outer jellyroll radius in micrometers."""
        return self.outer_diameter_mm * 1000.0 / 2.0

    @property
    def jellyroll_thickness_mm(self) -> float:
        """Radial thickness of jellyroll (outer - inner radius)."""
        return (self.outer_diameter_mm - self.mandrel_diameter_mm) / 2.0

    @property
    def jellyroll_thickness_um(self) -> float:
        """Radial thickness of jellyroll in micrometers."""
        return self.jellyroll_thickness_mm * 1000.0

    def get_wind(self, index: int) -> WindLayer | None:
        """Get wind at specific index.

        Args:
            index: 0-based wind index

        Returns:
            WindLayer or None if index out of range
        """
        if 0 <= index < len(self.winds):
            return self.winds[index]
        return None

    def get_innermost_wind(self) -> WindLayer | None:
        """Get the innermost wind (closest to mandrel)."""
        return self.get_wind(0)

    def get_outermost_wind(self) -> WindLayer | None:
        """Get the outermost wind (closest to can)."""
        return self.get_wind(len(self.winds) - 1) if self.winds else None

    def to_r_coordinates_mm(self) -> list[float]:
        """Get R coordinates of all wind boundaries in mm.

        Returns:
            List of radial coordinates starting from mandrel radius
        """
        coords = [self.mandrel_diameter_mm / 2.0]
        for wind in self.winds:
            coords.append(wind.r_outer_um / 1000.0)
        return coords

    def calculate_electrode_length_mm(self, electrode_width_mm: float) -> float:
        """Estimate total electrode length from winding geometry.

        Uses the average radius of each wind to estimate the length.

        Args:
            electrode_width_mm: Width of electrode sheet

        Returns:
            Estimated total electrode length in mm
        """
        import math

        total_length = 0.0
        for wind in self.winds:
            avg_radius_mm = (wind.r_inner_um + wind.r_outer_um) / 2000.0
            circumference = 2 * math.pi * avg_radius_mm
            total_length += circumference
        return total_length
