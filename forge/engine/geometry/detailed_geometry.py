"""Detailed geometry composition model for CAD generation.

This module provides the DetailedGeometry class which combines all
computed geometry into a single structure suitable for CAD export.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .coating_zones import CoatingZoneGeometry
    from .layer_stack import (
        LayerStackGeometry,
        WindingGeometry,
    )
    from .swelling import SwellingProfile
    from .tabs import TabGeometry
    from .validation import ValidationReport


@dataclass
class ExternalDimensions:
    """External cell dimensions.

    Holds the outer dimensions of the cell based on form factor.
    Prismatic/Pouch cells have length/width/height or thickness.
    Cylindrical cells have diameter and height.

    Attributes:
        length_mm: Cell length (X dimension) for prismatic/pouch
        width_mm: Cell width (Y dimension) for prismatic/pouch
        height_mm: Cell height (Z dimension) for prismatic/pouch
        thickness_mm: Cell thickness for pouch cells
        diameter_mm: Outer diameter for cylindrical cells
        wall_thickness_mm: Can/pouch wall thickness
    """

    length_mm: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    thickness_mm: float | None = None
    diameter_mm: float | None = None
    wall_thickness_mm: float | None = None

    @property
    def volume_cm3(self) -> float | None:
        """Calculate external volume in cm³."""
        import math

        if self.diameter_mm is not None and self.height_mm is not None:
            # Cylindrical
            r = self.diameter_mm / 2.0
            return math.pi * r * r * self.height_mm / 1000.0

        if self.length_mm and self.width_mm:
            # Prismatic or Pouch
            h = self.height_mm or self.thickness_mm
            if h:
                return self.length_mm * self.width_mm * h / 1000.0

        return None

    @property
    def internal_thickness_mm(self) -> float | None:
        """Calculate internal available thickness for stack."""
        thickness = self.height_mm or self.thickness_mm
        if thickness is None or self.wall_thickness_mm is None:
            return None
        # Subtract walls from top and bottom
        return thickness - 2 * self.wall_thickness_mm

    @property
    def internal_diameter_mm(self) -> float | None:
        """Calculate internal diameter for cylindrical cells."""
        if self.diameter_mm is None or self.wall_thickness_mm is None:
            return None
        return self.diameter_mm - 2 * self.wall_thickness_mm


@dataclass
class DetailedGeometry:
    """Complete internal geometry for CAD generation.

    This is the bridge between archetype data and CAD export.
    Contains computed layer positions with optional EOL swelling applied.

    Attributes:
        archetype_name: Name of the source archetype
        cell_type: Cell form factor ("pouch", "prismatic", "cylindrical")
        chemistry: Cathode chemistry (e.g., "NMC811", "LFP")
        layer_stack: Computed layer geometry (LayerStackGeometry or WindingGeometry)
        coating_zones: Electrode coating zone boundaries
        external_geometry: External cell dimensions
        swelling_profile: Swelling profile used (if any)
        warnings: List of warnings from loading/calculation
        confidence: Aggregated data confidence level
        source_cell_design_id: Optional reference to source CellCAD model
    """

    # Identification
    archetype_name: str
    cell_type: str  # "pouch", "prismatic", "cylindrical"
    chemistry: str

    # Computed geometry
    layer_stack: "LayerStackGeometry | WindingGeometry"
    coating_zones: "CoatingZoneGeometry | None"
    external_geometry: ExternalDimensions

    # Swelling
    swelling_profile: "SwellingProfile | None" = None

    # Tab geometry
    tab_geometry: "TabGeometry | None" = None

    # Quality tracking
    warnings: list[str] = field(default_factory=list)
    confidence: str = "MEDIUM"

    # Optional: existing CellCAD model references (for round-tripping)
    source_cell_design_id: str | None = None

    def total_stack_thickness_mm(self) -> float:
        """Get total electrode stack thickness in mm.

        Returns:
            Stack thickness for stacked cells, or jellyroll radial
            thickness for wound cells.
        """
        if hasattr(self.layer_stack, "total_thickness_um"):
            return self.layer_stack.total_thickness_um / 1000.0
        elif hasattr(self.layer_stack, "outer_diameter_mm"):
            # Wound cell: radial thickness
            return (
                self.layer_stack.outer_diameter_mm
                - self.layer_stack.mandrel_diameter_mm
            ) / 2.0
        return 0.0

    def calculate_tabs(
        self,
        configuration: str | None = None,
        tabs_per_polarity: int | None = None,
    ) -> "TabGeometry":
        """Calculate and store tab geometry.

        Args:
            configuration: Override default configuration:
                - Pouch: "standard", "same_side", "staggered"
                - Prismatic: "top_terminal", "side_terminal"
                - Cylindrical: "tabless", "traditional"
            tabs_per_polarity: Override default tab count (pouch/prismatic only)

        Returns:
            Calculated TabGeometry
        """
        from .tabs import calculate_tab_geometry

        self.tab_geometry = calculate_tab_geometry(
            self,
            configuration=configuration,
            tabs_per_polarity=tabs_per_polarity,
        )
        return self.tab_geometry

    def validate(self) -> "ValidationReport":
        """Run comprehensive validation on this geometry.

        Returns:
            ValidationReport with all validation results
        """
        from .validation import validate_geometry

        return validate_geometry(self)

    def validate_legacy(self) -> list[str]:
        """Validate geometry constraints (legacy method).

        Checks that:
        - Stack fits in case (for stacked cells)
        - Jellyroll fits in can (for wound cells)
        - Coating zone overhangs are positive

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check stack fits in case for stacked cells
        if self.cell_type in ("pouch", "prismatic"):
            internal = self.external_geometry.internal_thickness_mm
            if internal is not None:
                stack = self.total_stack_thickness_mm()
                if stack > internal:
                    errors.append(
                        f"Stack thickness ({stack:.2f} mm) exceeds "
                        f"internal space ({internal:.2f} mm)"
                    )

        # Check jellyroll fits in can for wound cells
        if self.cell_type == "cylindrical":
            if hasattr(self.layer_stack, "outer_diameter_mm"):
                jellyroll_od = self.layer_stack.outer_diameter_mm
                internal_d = self.external_geometry.internal_diameter_mm
                if internal_d is not None and jellyroll_od > internal_d:
                    errors.append(
                        f"Jellyroll diameter ({jellyroll_od:.2f} mm) exceeds "
                        f"can internal diameter ({internal_d:.2f} mm)"
                    )

        # Check coating zone overhangs
        if self.coating_zones is not None:
            errors.extend(self.coating_zones.validate_overhangs())

        return errors

    def is_valid(self) -> bool:
        """Quick check if geometry passes all error-level validations.

        Returns:
            True if no errors (warnings OK)
        """
        return self.validate().passed

    def get_layer_count_summary(self) -> dict[str, int]:
        """Get summary of layer counts.

        Returns:
            Dict with layer type names and counts
        """
        if hasattr(self.layer_stack, "to_layer_summary"):
            return self.layer_stack.to_layer_summary()
        elif hasattr(self.layer_stack, "num_winds"):
            return {"winds": self.layer_stack.num_winds}
        return {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON export/caching.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        result: dict[str, Any] = {
            "archetype_name": self.archetype_name,
            "cell_type": self.cell_type,
            "chemistry": self.chemistry,
            "confidence": self.confidence,
            "warnings": self.warnings,
            "external_geometry": {
                "length_mm": self.external_geometry.length_mm,
                "width_mm": self.external_geometry.width_mm,
                "height_mm": self.external_geometry.height_mm,
                "thickness_mm": self.external_geometry.thickness_mm,
                "diameter_mm": self.external_geometry.diameter_mm,
                "wall_thickness_mm": self.external_geometry.wall_thickness_mm,
            },
            "layer_count_summary": self.get_layer_count_summary(),
            "total_stack_thickness_mm": self.total_stack_thickness_mm(),
        }

        # Add swelling info
        if self.swelling_profile is not None:
            result["swelling"] = {
                "cathode_coating": self.swelling_profile.cathode_coating,
                "anode_coating": self.swelling_profile.anode_coating,
                "separator": self.swelling_profile.separator,
            }

        # Add layer positions for stacked cells
        if hasattr(self.layer_stack, "layers"):
            result["layer_positions"] = [
                {
                    "index": layer.layer_index,
                    "type": layer.layer_type.value,
                    "z_bottom_mm": layer.z_bottom_mm,
                    "z_top_mm": layer.z_top_mm,
                    "thickness_mm": layer.thickness_mm,
                    "material": layer.material,
                }
                for layer in self.layer_stack.layers
            ]

        # Add wind positions for wound cells
        if hasattr(self.layer_stack, "winds"):
            result["wind_positions"] = [
                {
                    "index": wind.wind_index,
                    "r_inner_mm": wind.r_inner_mm,
                    "r_outer_mm": wind.r_outer_mm,
                    "thickness_mm": wind.thickness_mm,
                }
                for wind in self.layer_stack.winds
            ]

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetailedGeometry":
        """Deserialize from dictionary.

        Note: This creates a minimal representation without full layer data.
        Full restoration would require storing more layer details.

        Args:
            data: Dictionary from to_dict()

        Returns:
            DetailedGeometry instance
        """
        from .layer_stack import LayerStackGeometry
        from .swelling import SwellingProfile

        # Create external geometry
        ext_data = data.get("external_geometry", {})
        external_geometry = ExternalDimensions(
            length_mm=ext_data.get("length_mm"),
            width_mm=ext_data.get("width_mm"),
            height_mm=ext_data.get("height_mm"),
            thickness_mm=ext_data.get("thickness_mm"),
            diameter_mm=ext_data.get("diameter_mm"),
            wall_thickness_mm=ext_data.get("wall_thickness_mm"),
        )

        # Create swelling profile if present
        swelling_profile = None
        if "swelling" in data:
            sw = data["swelling"]
            swelling_profile = SwellingProfile(
                cathode_coating=sw.get("cathode_coating", 1.0),
                anode_coating=sw.get("anode_coating", 1.0),
                separator=sw.get("separator", 1.0),
            )

        # Create minimal layer stack
        summary = data.get("layer_count_summary", {})
        layer_stack = LayerStackGeometry(
            num_electrode_pairs=summary.get("cathode_coating", 0) // 2,
            total_thickness_um=data.get("total_stack_thickness_mm", 0) * 1000,
            chemistry=data.get("chemistry", ""),
            swelling_applied=swelling_profile is not None,
        )

        return cls(
            archetype_name=data.get("archetype_name", ""),
            cell_type=data.get("cell_type", ""),
            chemistry=data.get("chemistry", ""),
            layer_stack=layer_stack,
            coating_zones=None,  # Not restored from dict
            external_geometry=external_geometry,
            swelling_profile=swelling_profile,
            warnings=data.get("warnings", []),
            confidence=data.get("confidence", "MEDIUM"),
        )
