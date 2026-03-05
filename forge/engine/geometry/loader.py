"""Archetype loader for converting JSON to CellCAD geometry models.

This module provides the ArchetypeLoader class which loads archetype JSON
files, validates them, and converts them to DetailedGeometry models with
computed layer positions.
"""

import json
from pathlib import Path
from typing import Any

from .calculators.stacked import StackedGeometryCalculator
from .calculators.wound import WoundGeometryCalculator
from .coating_zones import CoatingZoneGeometry
from .detailed_geometry import (
    DetailedGeometry,
    ExternalDimensions,
)
from .layer_stack import (
    LayerStackGeometry,
    WindingGeometry,
)
from .schemas import ArchetypeSchema, ConfidenceLevel
from .swelling import SwellingProfile


class ArchetypeLoader:
    """Load archetype JSON and map to CellCAD geometry models.

    Provides methods to load, validate, and convert archetype data
    to DetailedGeometry with computed layer positions.

    Attributes:
        path: Path to the archetype JSON file
        raw_data: Raw JSON data after loading
        schema: Validated ArchetypeSchema object
        warnings: List of warnings generated during loading
    """

    # Default values for missing data (with confidence tracking)
    DEFAULTS: dict[str, Any] = {
        "separator_thickness_um": 20.0,  # Common PP/PE/PP
        "layer_count_estimate_factor": 0.9,  # Use 90% of range midpoint if uncertain
        "cathode_collector_um": 15.0,  # Typical Al foil
        "anode_collector_um": 10.0,  # Typical Cu foil
        "cathode_coating_um": 70.0,  # Typical NMC coating
        "anode_coating_um": 80.0,  # Typical graphite coating
        "wall_thickness_mm": 0.5,  # Typical can/pouch wall
        "mandrel_diameter_mm": 4.0,  # Typical for 21700
        "anode_overhang_mm": 1.5,  # Typical safety margin
        "separator_overhang_mm": 1.5,  # Typical safety margin
    }

    def __init__(self, archetype_path: Path | str):
        """Initialize loader with path to archetype file.

        Args:
            archetype_path: Path to the archetype JSON file
        """
        self.path = Path(archetype_path)
        self.raw_data: dict[str, Any] = {}
        self.schema: ArchetypeSchema | None = None
        self.warnings: list[str] = []

    def load(self) -> ArchetypeSchema:
        """Load and validate archetype JSON.

        Returns:
            Validated ArchetypeSchema object

        Raises:
            FileNotFoundError: If archetype file doesn't exist
            json.JSONDecodeError: If JSON is malformed
            pydantic.ValidationError: If schema validation fails
        """
        with open(self.path, encoding="utf-8") as f:
            self.raw_data = json.load(f)

        # Validate with Pydantic
        self.schema = ArchetypeSchema.model_validate(self.raw_data)
        return self.schema

    def to_detailed_geometry(
        self,
        apply_swelling: bool = True,
        swelling_profile: SwellingProfile | None = None,
    ) -> DetailedGeometry:
        """Convert archetype to DetailedGeometry with computed positions.

        Args:
            apply_swelling: Whether to apply EOL swelling
            swelling_profile: Custom swelling profile (auto-detected if None)

        Returns:
            DetailedGeometry with all computed layer positions
        """
        if self.schema is None:
            self.load()

        assert self.schema is not None  # For type checker

        # Reset warnings for this conversion
        self.warnings = []

        # Determine cell type
        cell_type = self.schema.get_cell_type_normalized()

        # Get chemistry for swelling profile
        chemistry = self.schema.get_chemistry()
        if swelling_profile is None and apply_swelling:
            swelling_profile = SwellingProfile.for_chemistry(chemistry)
        elif not apply_swelling:
            swelling_profile = SwellingProfile.no_swelling()

        # Extract layer thicknesses
        stack = self.schema.electrode_stack

        cathode_coating_um = self._get_cathode_coating_um(stack)
        cathode_collector_um = self._get_cathode_collector_um(stack)
        anode_coating_um = self._get_anode_coating_um(stack)
        anode_collector_um = self._get_anode_collector_um(stack)
        separator_um = self._get_separator_um(stack)

        # Calculate layer stack based on cell type
        if cell_type in ("pouch", "prismatic"):
            layer_stack = self._calculate_stacked_geometry(
                swelling_profile,
                cathode_coating_um,
                cathode_collector_um,
                anode_coating_um,
                anode_collector_um,
                separator_um,
            )
        elif cell_type == "cylindrical":
            layer_stack = self._calculate_wound_geometry(
                swelling_profile,
                cathode_coating_um,
                cathode_collector_um,
                anode_coating_um,
                anode_collector_um,
                separator_um,
            )
        else:
            raise ValueError(f"Unknown cell type: {cell_type}")

        # Calculate coating zones
        coating_zones = self._calculate_coating_zones()

        # Extract external geometry
        external_geometry = self._extract_external_geometry()

        # Aggregate confidence
        confidence = self._aggregate_confidence()

        return DetailedGeometry(
            archetype_name=self.schema.metadata.name,
            cell_type=cell_type,
            chemistry=chemistry,
            layer_stack=layer_stack,
            coating_zones=coating_zones,
            external_geometry=external_geometry,
            swelling_profile=swelling_profile,
            warnings=self.warnings.copy(),
            confidence=confidence,
        )

    def _get_cathode_coating_um(self, stack) -> float:
        """Extract cathode coating thickness, using defaults if missing."""
        if stack.cathode.coating_thickness_um is not None:
            return stack.cathode.coating_thickness_um
        self.warnings.append(
            f"Cathode coating thickness missing, using default: "
            f"{self.DEFAULTS['cathode_coating_um']} µm"
        )
        return self.DEFAULTS["cathode_coating_um"]

    def _get_cathode_collector_um(self, stack) -> float:
        """Extract cathode collector thickness, using defaults if missing."""
        if (
            stack.cathode.current_collector is not None
            and stack.cathode.current_collector.thickness_um is not None
        ):
            return stack.cathode.current_collector.thickness_um
        # Check alternative location
        if (
            stack.current_collectors is not None
            and stack.current_collectors.aluminum_um is not None
        ):
            return stack.current_collectors.aluminum_um
        self.warnings.append(
            f"Cathode collector thickness missing, using default: "
            f"{self.DEFAULTS['cathode_collector_um']} µm"
        )
        return self.DEFAULTS["cathode_collector_um"]

    def _get_anode_coating_um(self, stack) -> float:
        """Extract anode coating thickness, using defaults if missing."""
        if stack.anode.coating_thickness_um is not None:
            return stack.anode.coating_thickness_um
        self.warnings.append(
            f"Anode coating thickness missing, using default: "
            f"{self.DEFAULTS['anode_coating_um']} µm"
        )
        return self.DEFAULTS["anode_coating_um"]

    def _get_anode_collector_um(self, stack) -> float:
        """Extract anode collector thickness, using defaults if missing."""
        if (
            stack.anode.current_collector is not None
            and stack.anode.current_collector.thickness_um is not None
        ):
            return stack.anode.current_collector.thickness_um
        # Check alternative location
        if (
            stack.current_collectors is not None
            and stack.current_collectors.copper_um is not None
        ):
            return stack.current_collectors.copper_um
        self.warnings.append(
            f"Anode collector thickness missing, using default: "
            f"{self.DEFAULTS['anode_collector_um']} µm"
        )
        return self.DEFAULTS["anode_collector_um"]

    def _get_separator_um(self, stack) -> float:
        """Extract separator thickness, using defaults if missing."""
        thickness = self.schema.get_separator_thickness_um()
        if thickness is not None:
            return thickness
        self.warnings.append(
            f"Separator thickness missing, using default: "
            f"{self.DEFAULTS['separator_thickness_um']} µm"
        )
        return self.DEFAULTS["separator_thickness_um"]

    def _calculate_stacked_geometry(
        self,
        swelling_profile: SwellingProfile,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
    ) -> LayerStackGeometry:
        """Calculate layer stack for pouch/prismatic cells."""
        assert self.schema is not None

        stack = self.schema.electrode_stack

        # Get layer count
        num_pairs = self.schema.get_num_electrode_pairs()
        if num_pairs is None:
            # Estimate from range if available
            if stack.layer_count_range is not None:
                mid = (stack.layer_count_range[0] + stack.layer_count_range[1]) / 2
                num_pairs = int(mid * self.DEFAULTS["layer_count_estimate_factor"])
                self.warnings.append(
                    f"Layer count estimated from range: {num_pairs}"
                )
            else:
                # Use a reasonable default
                num_pairs = 30
                self.warnings.append(
                    f"Layer count unknown, using default: {num_pairs}"
                )

        # Get material names
        cathode_material = stack.cathode.active_material
        anode_material = stack.anode.active_material
        separator_material = stack.separator.type or "PP/PE/PP"

        calculator = StackedGeometryCalculator(swelling_profile)
        result = calculator.calculate(
            num_electrode_pairs=num_pairs,
            cathode_coating_um=cathode_coating_um,
            cathode_collector_um=cathode_collector_um,
            anode_coating_um=anode_coating_um,
            anode_collector_um=anode_collector_um,
            separator_um=separator_um,
            cathode_material=cathode_material,
            anode_material=anode_material,
            separator_material=separator_material,
        )

        result.chemistry = self.schema.get_chemistry()
        return result

    def _calculate_wound_geometry(
        self,
        swelling_profile: SwellingProfile,
        cathode_coating_um: float,
        cathode_collector_um: float,
        anode_coating_um: float,
        anode_collector_um: float,
        separator_um: float,
    ) -> WindingGeometry:
        """Calculate winding geometry for cylindrical cells."""
        assert self.schema is not None

        stack = self.schema.electrode_stack
        geometry = self.schema.geometry

        # Get number of winds
        num_winds = self.schema.get_num_winds()
        if num_winds is None:
            # Estimate from winding_turns_range if available
            if stack.winding_turns_range is not None:
                mid = (stack.winding_turns_range[0] + stack.winding_turns_range[1]) / 2
                num_winds = int(mid)
                self.warnings.append(
                    f"Winding turns estimated from range: {num_winds}"
                )
            else:
                num_winds = 30
                self.warnings.append(
                    f"Winding turns unknown, using default: {num_winds}"
                )

        # Get mandrel diameter
        mandrel_diameter_mm = self.DEFAULTS["mandrel_diameter_mm"]
        if geometry.core is not None:
            if geometry.core.void_diameter_mm is not None:
                mandrel_diameter_mm = geometry.core.void_diameter_mm
            elif geometry.core.mandrel_diameter_mm is not None:
                mandrel_diameter_mm = geometry.core.mandrel_diameter_mm
        else:
            self.warnings.append(
                f"Mandrel diameter missing, using default: {mandrel_diameter_mm} mm"
            )

        # Get material names
        cathode_material = stack.cathode.active_material
        anode_material = stack.anode.active_material
        separator_material = stack.separator.type or "PP/PE/PP"

        calculator = WoundGeometryCalculator(swelling_profile)
        result = calculator.calculate(
            num_winds=num_winds,
            mandrel_diameter_mm=mandrel_diameter_mm,
            cathode_coating_um=cathode_coating_um,
            cathode_collector_um=cathode_collector_um,
            anode_coating_um=anode_coating_um,
            anode_collector_um=anode_collector_um,
            separator_um=separator_um,
            cathode_material=cathode_material,
            anode_material=anode_material,
            separator_material=separator_material,
        )

        result.chemistry = self.schema.get_chemistry()
        return result

    def _calculate_coating_zones(self) -> CoatingZoneGeometry | None:
        """Calculate coating zone geometry if sheet dimensions available."""
        assert self.schema is not None

        stack = self.schema.electrode_stack
        safety = self.schema.safety_geometry
        cell_type = self.schema.get_cell_type_normalized()

        # For wound cells, coating zones are less meaningful
        if cell_type == "cylindrical":
            return None

        # Get cathode dimensions
        cathode_width_mm = None
        cathode_height_mm = None

        if stack.cathode.sheet_dimensions is not None:
            if stack.cathode.sheet_dimensions.width_mm is not None:
                cathode_width_mm = stack.cathode.sheet_dimensions.width_mm
            if stack.cathode.sheet_dimensions.length_mm is not None:
                cathode_height_mm = stack.cathode.sheet_dimensions.length_mm

        if cathode_width_mm is None or cathode_height_mm is None:
            self.warnings.append("Cathode sheet dimensions not available for coating zones")
            return None

        # Get overhang values
        anode_overhang_x_mm = self.DEFAULTS["anode_overhang_mm"]
        anode_overhang_y_mm = self.DEFAULTS["anode_overhang_mm"]

        if safety.anode_overhang is not None:
            if safety.anode_overhang.width_direction_mm is not None:
                anode_overhang_x_mm = safety.anode_overhang.width_direction_mm
            if safety.anode_overhang.length_direction_mm is not None:
                anode_overhang_y_mm = safety.anode_overhang.length_direction_mm
        elif safety.anode_overhang_mm is not None:
            anode_overhang_x_mm = safety.anode_overhang_mm
            anode_overhang_y_mm = safety.anode_overhang_mm

        separator_overhang_mm = safety.separator_overhang_mm or self.DEFAULTS["separator_overhang_mm"]

        return CoatingZoneGeometry.from_dimensions(
            cathode_width_mm=cathode_width_mm,
            cathode_height_mm=cathode_height_mm,
            anode_overhang_x_mm=anode_overhang_x_mm,
            anode_overhang_y_mm=anode_overhang_y_mm,
            separator_overhang_mm=separator_overhang_mm,
        )

    def _extract_external_geometry(self) -> ExternalDimensions:
        """Extract external dimensions from archetype."""
        assert self.schema is not None

        ext = self.schema.geometry.external
        cell_type = self.schema.get_cell_type_normalized()

        # Get wall thickness
        wall_thickness_mm = self.DEFAULTS["wall_thickness_mm"]
        if self.schema.geometry.can is not None:
            if self.schema.geometry.can.wall_thickness_mm is not None:
                wall_thickness_mm = self.schema.geometry.can.wall_thickness_mm
        elif self.schema.geometry.walls is not None:
            if self.schema.geometry.walls.wall_thickness_mm is not None:
                wall_thickness_mm = self.schema.geometry.walls.wall_thickness_mm
        elif (
            self.schema.geometry.pouch_film is not None
            and self.schema.geometry.pouch_film.total_thickness_um is not None
        ):
            wall_thickness_mm = self.schema.geometry.pouch_film.total_thickness_um / 1000.0

        if cell_type == "cylindrical":
            return ExternalDimensions(
                diameter_mm=ext.diameter_mm,
                height_mm=ext.height_mm,
                wall_thickness_mm=wall_thickness_mm,
            )
        else:
            return ExternalDimensions(
                length_mm=ext.length_mm,
                width_mm=ext.width_mm,
                height_mm=ext.height_mm,
                thickness_mm=ext.thickness_mm,
                wall_thickness_mm=wall_thickness_mm,
            )

    def _aggregate_confidence(self) -> str:
        """Aggregate confidence level from all components.

        Uses the minimum confidence level from key components.

        Returns:
            Aggregated confidence level string
        """
        assert self.schema is not None

        # Collect confidence levels from key components
        levels = []

        # External geometry confidence
        levels.append(self.schema.geometry.external.confidence)

        # Electrode stack confidence
        levels.append(self.schema.electrode_stack.confidence)

        # Mass confidence
        levels.append(self.schema.mass.confidence)

        # Map to ordinal for comparison
        order = {
            ConfidenceLevel.HIGH: 3,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.LOW: 1,
        }

        # Find minimum confidence
        min_level = min(levels, key=lambda x: order.get(x, 2))
        return min_level.value


def load_archetype(path: Path | str) -> DetailedGeometry:
    """Convenience function to load archetype and convert to DetailedGeometry.

    Args:
        path: Path to archetype JSON file

    Returns:
        DetailedGeometry with computed layer positions
    """
    loader = ArchetypeLoader(path)
    return loader.to_detailed_geometry()


def load_all_archetypes(directory: Path | str) -> dict[str, DetailedGeometry]:
    """Load all archetype files from a directory.

    Args:
        directory: Path to directory containing archetype JSON files

    Returns:
        Dict mapping archetype names to DetailedGeometry objects
    """
    directory = Path(directory)
    results = {}

    for path in directory.glob("*_archetype.json"):
        try:
            loader = ArchetypeLoader(path)
            geom = loader.to_detailed_geometry()
            results[geom.archetype_name] = geom
        except Exception as e:
            # Log but continue with other files
            print(f"Warning: Failed to load {path}: {e}")

    return results
