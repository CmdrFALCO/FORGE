"""FreeCAD color mapping matching CellCAD visualization."""

from dataclasses import dataclass


@dataclass
class FreeCADColor:
    """RGB color for FreeCAD (0-1 range)."""

    r: float
    g: float
    b: float

    def to_tuple(self) -> tuple[float, float, float]:
        """Return color as tuple."""
        return (self.r, self.g, self.b)

    def to_freecad_string(self) -> str:
        """Format for FreeCAD script."""
        return f"({self.r:.3f}, {self.g:.3f}, {self.b:.3f})"


class FreeCADColorScheme:
    """Color scheme matching CellCAD visualization.

    Colors converted from RGBA (0-255) to RGB (0-1) for FreeCAD.
    """

    # Electrode materials
    CATHODE_COATING = FreeCADColor(0.706, 0.157, 0.157)  # Dark red
    ANODE_COATING = FreeCADColor(0.235, 0.235, 0.235)  # Dark gray (graphite)
    CATHODE_COLLECTOR = FreeCADColor(0.753, 0.753, 0.753)  # Silver (Al)
    ANODE_COLLECTOR = FreeCADColor(0.722, 0.451, 0.200)  # Copper
    SEPARATOR = FreeCADColor(0.941, 0.941, 0.941)  # White

    # Casing
    CASING = FreeCADColor(0.627, 0.627, 0.667)  # Steel gray

    # Chemistry-specific cathode colors
    CATHODE_BY_CHEMISTRY: dict[str, FreeCADColor] = {
        "LFP": FreeCADColor(0.314, 0.549, 0.314),  # Green
        "NMC811": FreeCADColor(0.706, 0.157, 0.157),  # Dark red
        "NMC622": FreeCADColor(0.627, 0.235, 0.235),  # Medium red
        "NMC712": FreeCADColor(0.667, 0.196, 0.196),  # Red
        "NMC532": FreeCADColor(0.588, 0.275, 0.275),  # Light red
        "NCA": FreeCADColor(0.549, 0.157, 0.392),  # Purple-red
        "LCO": FreeCADColor(0.196, 0.196, 0.588),  # Blue (cobalt)
        "LMO": FreeCADColor(0.706, 0.392, 0.157),  # Orange (manganese)
        "LMFP": FreeCADColor(0.235, 0.471, 0.392),  # Teal (LFP variant)
    }

    @classmethod
    def get_cathode_color(cls, chemistry: str) -> FreeCADColor:
        """Get chemistry-specific cathode color."""
        normalized = chemistry.upper().replace("NCM", "NMC")
        return cls.CATHODE_BY_CHEMISTRY.get(normalized, cls.CATHODE_COATING)

    @classmethod
    def get_color_for_material(cls, material_group: str, chemistry: str = "") -> FreeCADColor:
        """Get FreeCAD color for material group."""
        mapping = {
            "Cathode_Coating": cls.get_cathode_color(chemistry),
            "Anode_Coating": cls.ANODE_COATING,
            "Cathode_Collector": cls.CATHODE_COLLECTOR,
            "Anode_Collector": cls.ANODE_COLLECTOR,
            "Separator": cls.SEPARATOR,
            "Casing": cls.CASING,
        }
        return mapping.get(material_group, cls.CASING)


# Material transparency (0 = opaque, 100 = fully transparent)
MATERIAL_TRANSPARENCY: dict[str, int] = {
    "Cathode_Coating": 0,
    "Anode_Coating": 0,
    "Cathode_Collector": 0,
    "Anode_Collector": 0,
    "Separator": 40,
    "Casing": 60,
}
