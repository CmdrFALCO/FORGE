"""Color schemes for battery cell visualization."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ColorScheme:
    """RGBA colors for cell components.

    Colors are specified as RGBA strings for Plotly compatibility.
    Alpha values control transparency (0 = fully transparent, 1 = fully opaque).

    Attributes:
        cathode_coating: Dark red for cathode active material
        anode_coating: Dark gray for graphite anode
        cathode_collector: Silver for aluminum foil
        anode_collector: Copper color for copper foil
        separator: White, semi-transparent for separator film
        can_wall: Steel gray for metal casing
        pouch_film: Light gray for pouch film
        electrode_pair: Neutral color for simplified view blocks
    """

    # Electrode materials - high contrast colors for dark backgrounds
    cathode_coating: str = "rgba(255, 80, 80, 0.95)"  # Bright red
    anode_coating: str = "rgba(70, 130, 180, 0.95)"  # Steel blue (stands out on dark)
    cathode_collector: str = "rgba(192, 192, 210, 0.98)"  # Bright silver (Al)
    anode_collector: str = "rgba(255, 180, 100, 0.98)"  # Bright copper/orange
    separator: str = "rgba(255, 255, 200, 0.95)"  # Light yellow (visible on dark)

    # Casing
    can_wall: str = "rgba(160, 160, 170, 0.4)"  # Steel gray, transparent
    pouch_film: str = "rgba(200, 200, 200, 0.3)"  # Light gray, very transparent

    # Simplified view (electrode pairs as single blocks)
    electrode_pair: str = "rgba(120, 120, 150, 0.8)"  # Neutral gray-blue

    # Chemistry-specific cathode colors
    _cathode_by_chemistry: dict[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        """Initialize chemistry-specific color mapping."""
        self._cathode_by_chemistry = {
            "LFP": "rgba(100, 200, 100, 0.9)",  # Bright green (iron phosphate)
            "NMC811": "rgba(240, 80, 80, 0.9)",  # Bright red
            "NMC622": "rgba(220, 100, 100, 0.9)",  # Medium red
            "NMC712": "rgba(230, 90, 90, 0.9)",  # Red
            "NMC532": "rgba(210, 110, 110, 0.9)",  # Light red
            "NCA": "rgba(200, 80, 160, 0.9)",  # Bright purple-red
            "LCO": "rgba(80, 80, 220, 0.9)",  # Bright blue (cobalt)
            "LMO": "rgba(240, 160, 60, 0.9)",  # Bright orange (manganese)
            "LMFP": "rgba(80, 180, 150, 0.9)",  # Bright teal (LFP variant)
        }

    def get_cathode_color(self, chemistry: str) -> str:
        """Get chemistry-specific cathode color.

        Args:
            chemistry: Cathode chemistry string (e.g., "NMC811", "LFP", "NCM811")

        Returns:
            RGBA color string for the cathode active material
        """
        # Normalize chemistry name (NCM -> NMC, uppercase)
        normalized = chemistry.upper().replace("NCM", "NMC")

        # Try exact match first
        if normalized in self._cathode_by_chemistry:
            return self._cathode_by_chemistry[normalized]

        # Try prefix match for variants (e.g., NMC811-Si -> NMC811)
        for key in self._cathode_by_chemistry:
            if normalized.startswith(key):
                return self._cathode_by_chemistry[key]

        # Default to generic cathode color
        return self.cathode_coating

    def get_layer_color(self, layer_type: str, chemistry: str = "") -> str:
        """Get color for a layer type.

        Args:
            layer_type: Layer type string (from LayerType enum value)
            chemistry: Optional chemistry for cathode color selection

        Returns:
            RGBA color string for the layer
        """
        layer_type_lower = layer_type.lower()

        if "cathode_coating" in layer_type_lower:
            return self.get_cathode_color(chemistry) if chemistry else self.cathode_coating
        elif "anode_coating" in layer_type_lower:
            return self.anode_coating
        elif "cathode_collector" in layer_type_lower:
            return self.cathode_collector
        elif "anode_collector" in layer_type_lower:
            return self.anode_collector
        elif "separator" in layer_type_lower:
            return self.separator
        else:
            return self.electrode_pair


# Default color scheme instance
DEFAULT_COLORS = ColorScheme()

