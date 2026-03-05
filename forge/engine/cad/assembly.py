"""Assembly structure and naming conventions for CAD export.

This module defines the data structures for organizing CAD bodies
into assemblies with consistent naming conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MaterialGroup(str, Enum):
    """Material groups for assembly organization.

    Bodies are organized by material type for easier manipulation
    in downstream CAD/FEM software.
    """

    # Electrode stack
    CASING = "Casing"
    CATHODE_COLLECTOR = "Cathode_Collector"
    CATHODE_COATING = "Cathode_Coating"
    ANODE_COLLECTOR = "Anode_Collector"
    ANODE_COATING = "Anode_Coating"
    SEPARATOR = "Separator"
    JELLYROLL = "Jellyroll"  # For wound cells when not split by material

    # Terminals
    TERMINAL_POSITIVE = "Terminal_Positive"
    TERMINAL_NEGATIVE = "Terminal_Negative"

    # Tabs and busbars
    TAB_POSITIVE = "Tab_Positive"
    TAB_NEGATIVE = "Tab_Negative"
    BUSBAR_POSITIVE = "Busbar_Positive"
    BUSBAR_NEGATIVE = "Busbar_Negative"

    # Insulators and gaskets
    INSULATOR = "Insulator"
    GASKET = "Gasket"

    # Cylindrical cell header components
    VENT = "Vent"
    CID = "CID"
    HEADER = "Header"


# Material properties for downstream simulation
MATERIAL_PROPERTIES: dict[MaterialGroup, dict[str, float | str]] = {
    MaterialGroup.CASING: {
        "density_kg_m3": 2700.0,
        "thermal_conductivity_w_mk": 205.0,
        "electrical_conductivity_s_m": 3.5e7,
        "material_name": "Aluminum 3003",
    },
    MaterialGroup.CATHODE_COLLECTOR: {
        "density_kg_m3": 2700.0,
        "thermal_conductivity_w_mk": 205.0,
        "electrical_conductivity_s_m": 3.5e7,
        "material_name": "Aluminum Foil",
    },
    MaterialGroup.CATHODE_COATING: {
        "density_kg_m3": 3500.0,
        "thermal_conductivity_w_mk": 2.0,
        "electrical_conductivity_s_m": 1.0e2,
        "material_name": "LFP/NMC Active Material",
    },
    MaterialGroup.ANODE_COLLECTOR: {
        "density_kg_m3": 8960.0,
        "thermal_conductivity_w_mk": 401.0,
        "electrical_conductivity_s_m": 5.8e7,
        "material_name": "Copper Foil",
    },
    MaterialGroup.ANODE_COATING: {
        "density_kg_m3": 2200.0,
        "thermal_conductivity_w_mk": 1.5,
        "electrical_conductivity_s_m": 1.0e3,
        "material_name": "Graphite Active Material",
    },
    MaterialGroup.SEPARATOR: {
        "density_kg_m3": 900.0,
        "thermal_conductivity_w_mk": 0.33,
        "electrical_conductivity_s_m": 1e-14,
        "material_name": "PP/PE Separator",
    },
    MaterialGroup.TAB_POSITIVE: {
        "density_kg_m3": 2700.0,
        "thermal_conductivity_w_mk": 205.0,
        "electrical_conductivity_s_m": 3.5e7,
        "material_name": "Aluminum Tab",
    },
    MaterialGroup.TAB_NEGATIVE: {
        "density_kg_m3": 8900.0,
        "thermal_conductivity_w_mk": 90.0,
        "electrical_conductivity_s_m": 1.4e7,
        "material_name": "Nickel-plated Copper Tab",
    },
    MaterialGroup.BUSBAR_POSITIVE: {
        "density_kg_m3": 2700.0,
        "thermal_conductivity_w_mk": 205.0,
        "electrical_conductivity_s_m": 3.5e7,
        "material_name": "Aluminum Busbar",
    },
    MaterialGroup.BUSBAR_NEGATIVE: {
        "density_kg_m3": 8900.0,
        "thermal_conductivity_w_mk": 90.0,
        "electrical_conductivity_s_m": 1.4e7,
        "material_name": "Nickel-plated Copper Busbar",
    },
    MaterialGroup.TERMINAL_POSITIVE: {
        "density_kg_m3": 2700.0,
        "thermal_conductivity_w_mk": 205.0,
        "electrical_conductivity_s_m": 3.5e7,
        "material_name": "Aluminum Terminal",
    },
    MaterialGroup.TERMINAL_NEGATIVE: {
        "density_kg_m3": 8900.0,
        "thermal_conductivity_w_mk": 90.0,
        "electrical_conductivity_s_m": 1.4e7,
        "material_name": "Nickel-plated Copper Terminal",
    },
    MaterialGroup.INSULATOR: {
        "density_kg_m3": 1400.0,
        "thermal_conductivity_w_mk": 0.25,
        "electrical_conductivity_s_m": 1e-14,
        "material_name": "PEEK Insulator",
    },
    MaterialGroup.GASKET: {
        "density_kg_m3": 1200.0,
        "thermal_conductivity_w_mk": 0.15,
        "electrical_conductivity_s_m": 1e-16,
        "material_name": "Rubber Gasket",
    },
    MaterialGroup.VENT: {
        "density_kg_m3": 2700.0,
        "thermal_conductivity_w_mk": 205.0,
        "electrical_conductivity_s_m": 3.5e7,
        "material_name": "Aluminum Vent Disc",
    },
    MaterialGroup.CID: {
        "density_kg_m3": 2700.0,
        "thermal_conductivity_w_mk": 205.0,
        "electrical_conductivity_s_m": 3.5e7,
        "material_name": "Aluminum CID",
    },
    MaterialGroup.HEADER: {
        "density_kg_m3": 8900.0,
        "thermal_conductivity_w_mk": 90.0,
        "electrical_conductivity_s_m": 1.4e7,
        "material_name": "Nickel Header Cap",
    },
}


@dataclass
class CADBody:
    """Represents a single CAD body with metadata.

    Attributes:
        name: Unique name for the body
        material_group: Material category for organization
        layer_index: Layer index for individual mode (None for grouped)
        _solid: Build123d solid object (set at runtime, not serializable)
    """

    name: str
    material_group: MaterialGroup
    layer_index: int | None = None
    _solid: object = field(default=None, repr=False)

    @property
    def solid(self) -> object:
        """Get the Build123d solid object."""
        return self._solid

    @solid.setter
    def solid(self, value: object) -> None:
        """Set the Build123d solid object."""
        self._solid = value


@dataclass
class CADAssembly:
    """Complete CAD assembly with organized bodies.

    Attributes:
        name: Assembly name
        bodies: List of CADBody objects
        cell_type: Cell form factor (pouch, prismatic, cylindrical)
        chemistry: Cathode chemistry
        grouped_by_material: Whether bodies are grouped by material type
    """

    name: str
    bodies: list[CADBody] = field(default_factory=list)
    cell_type: str = ""
    chemistry: str = ""
    grouped_by_material: bool = True

    def get_bodies_by_group(self, group: MaterialGroup) -> list[CADBody]:
        """Get all bodies belonging to a material group.

        Args:
            group: Material group to filter by

        Returns:
            List of CADBody objects in the specified group
        """
        return [b for b in self.bodies if b.material_group == group]

    def get_all_solids(self) -> list[object]:
        """Get all Build123d solids.

        Returns:
            List of solid objects (excluding None values)
        """
        return [b.solid for b in self.bodies if b.solid is not None]

    def body_count(self) -> int:
        """Get total number of bodies.

        Returns:
            Number of bodies in the assembly
        """
        return len(self.bodies)

    def summary(self) -> dict[str, int]:
        """Count bodies per material group.

        Returns:
            Dictionary mapping group name to body count
        """
        counts: dict[str, int] = {}
        for group in MaterialGroup:
            count = len(self.get_bodies_by_group(group))
            if count > 0:
                counts[group.value] = count
        return counts


class AssemblyNamer:
    """Generate consistent names for CAD bodies and assemblies.

    Uses generic naming convention without archetype-specific information
    to ensure exported files are suitable for general use.
    """

    @staticmethod
    def body_name(
        group: MaterialGroup,
        index: int | None = None,
        total: int | None = None,
    ) -> str:
        """Generate body name.

        Args:
            group: Material group
            index: Layer index (for individual mode)
            total: Total layers (for padding calculation)

        Returns:
            Name like "Cathode_Coating" or "Cathode_Coating_001"
        """
        base = group.value

        if index is not None:
            # Pad index for proper sorting in file browsers
            if total is not None and total >= 100:
                return f"{base}_{index:03d}"
            elif total is not None and total >= 10:
                return f"{base}_{index:02d}"
            else:
                return f"{base}_{index}"

        return base

    @staticmethod
    def assembly_name(cell_type: str, chemistry: str) -> str:
        """Generate assembly name.

        Args:
            cell_type: Cell form factor
            chemistry: Cathode chemistry

        Returns:
            Assembly name like "Cell_Assembly_prismatic_LFP"
        """
        # Sanitize strings for file system compatibility
        cell_type_clean = cell_type.replace(" ", "_").replace("-", "_")
        chemistry_clean = chemistry.replace(" ", "_").replace("-", "_")
        return f"Cell_Assembly_{cell_type_clean}_{chemistry_clean}"

    @staticmethod
    def wind_name(wind_index: int, total_winds: int) -> str:
        """Generate wind name for cylindrical cells.

        Args:
            wind_index: Wind index (0-based)
            total_winds: Total number of winds

        Returns:
            Name like "Wind_001"
        """
        if total_winds >= 100:
            return f"Wind_{wind_index:03d}"
        elif total_winds >= 10:
            return f"Wind_{wind_index:02d}"
        else:
            return f"Wind_{wind_index}"
