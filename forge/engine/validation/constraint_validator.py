"""
Level 2 Validation: Cross-field physics constraints.
These rules cannot be expressed in JSON Schema alone.

This module implements physics-based constraint checks for battery cell design.
These rules come directly from prismatic_master.yaml and represent fundamental
physics constraints and manufacturing feasibility checks.

This module implements the second guard transition in the supervision Petri Net:
  Valid Structure → [T_constraint_check] → Valid Design (or Feedback)
"""

import time
from collections.abc import Callable
from typing import Any

from .schema_validator import ConstraintResult, ValidationError, ValidationResult

# Type for constraint validation functions
ConstraintFunc = Callable[[dict], ValidationError | None]


def _get_nested(d: dict, path: str, default: Any = None) -> Any:
    """Get nested value by dot path, e.g., 'envelope.external.height_mm'"""
    keys = path.split(".")
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def _set_nested(d: dict, path: str, value: Any) -> None:
    """Set nested value by dot path."""
    keys = path.split(".")
    current = d
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


# ═══════════════════════════════════════════════════════════════
# GEOMETRY CONSTRAINTS
# ═══════════════════════════════════════════════════════════════


def check_internal_height_positive(cell: dict) -> ValidationError | None:
    """
    Constraint: internal_height = height - wall_top - wall_bottom > 0

    The cavity must have positive height after accounting for top and bottom walls.
    """
    height = _get_nested(cell, "envelope.external.cell_height_mm", 0)
    wall_top = _get_nested(cell, "envelope.walls.wall_top_mm", 0)
    wall_bottom = _get_nested(cell, "envelope.walls.wall_bottom_mm", 0)

    internal = height - wall_top - wall_bottom
    if internal <= 0:
        return ValidationError(
            path="envelope (geometry constraint)",
            message=f"Internal cavity height must be positive. "
            f"Got {internal:.2f} mm = {height} - {wall_top} - {wall_bottom}. "
            f"Reduce wall thickness or increase cell height.",
            value=internal,
            constraint="internal_height > 0",
        )
    return None


def check_internal_width_positive(cell: dict) -> ValidationError | None:
    """
    Constraint: internal_width = width - 2*wall_side > 0

    The cavity must have positive width after accounting for side walls.
    """
    width = _get_nested(cell, "envelope.external.cell_width_mm", 0)
    wall_side = _get_nested(cell, "envelope.walls.wall_sides_mm", 0)

    internal = width - 2 * wall_side
    if internal <= 0:
        return ValidationError(
            path="envelope.walls (geometry constraint)",
            message=f"Internal cavity width must be positive. "
            f"Got {internal:.2f} mm = {width} - 2*{wall_side}. "
            f"Reduce side wall thickness or increase cell width.",
            value=internal,
            constraint="internal_width > 0",
        )
    return None


def check_internal_thickness_positive(cell: dict) -> ValidationError | None:
    """
    Constraint: internal_thickness = thickness - 2*wall_front_back > 0

    The cavity must have positive thickness (primary dimension) after walls.
    """
    thickness = _get_nested(cell, "envelope.external.cell_thickness_mm", 0)
    wall_fb = _get_nested(cell, "envelope.walls.wall_front_back_mm", 0)

    internal = thickness - 2 * wall_fb
    if internal <= 0:
        return ValidationError(
            path="envelope.walls (geometry constraint)",
            message=f"Internal cavity thickness must be positive. "
            f"Got {internal:.2f} mm = {thickness} - 2*{wall_fb}. "
            f"Reduce front/back wall thickness or increase cell thickness.",
            value=internal,
            constraint="internal_thickness > 0",
        )
    return None


def check_cathode_fits_in_cavity(cell: dict) -> ValidationError | None:
    """
    Constraint: cathode_height < internal_cavity_height

    The cathode sheet must fit within the available cavity space.
    """
    cathode_height = _get_nested(cell, "stack_config.sheet_geometry.cathode_height_mm", 0)
    cell_height = _get_nested(cell, "envelope.external.cell_height_mm", 0)
    wall_top = _get_nested(cell, "envelope.walls.wall_top_mm", 0)
    wall_bottom = _get_nested(cell, "envelope.walls.wall_bottom_mm", 0)

    internal_height = cell_height - wall_top - wall_bottom
    if cathode_height > internal_height:
        return ValidationError(
            path="stack_config.sheet_geometry.cathode_height_mm",
            message=f"Cathode height {cathode_height} mm exceeds internal cavity height {internal_height:.2f} mm. "
            f"Reduce cathode height, reduce wall thickness, or increase cell height.",
            value=cathode_height,
            constraint="cathode_height < internal_cavity_height",
        )
    return None


# ═══════════════════════════════════════════════════════════════
# ELECTROCHEMISTRY CONSTRAINTS
# ═══════════════════════════════════════════════════════════════


def check_np_ratio(cell: dict) -> ValidationError | None:
    """
    CRITICAL Constraint: computed N/P ratio ∈ [1.05, 1.25].

    Computes the per-unit-area N/P ratio from actual electrode parameters:
        N/P = (anode_loading × anode_spec_capacity) / (cathode_loading × cathode_spec_capacity)

    This is the same formula as calculate_np_ratio() in energy.py with area and
    sheet-count terms cancelled (they are equal per unit area on each side).

    The PASS/FAIL decision is based on the COMPUTED value, not any declared
    np_ratio field. If a declared field exists and disagrees with the computed
    value by more than 0.05, the discrepancy is noted in the error message.

    Returns None (can't check) when any of the four required fields
    (cathode loading, cathode spec capacity, anode loading, anode spec capacity)
    are missing from the spec.
    """
    cathode_loading = _get_nested(cell, "electrochemistry.cathode.loading_mg_cm2")
    cathode_spec_cap = _get_nested(cell, "electrochemistry.cathode.rev_spec_capacity_mahg")
    anode_loading = _get_nested(cell, "electrochemistry.anode.loading_mg_cm2")
    anode_spec_cap = _get_nested(cell, "electrochemistry.anode.rev_spec_capacity_mahg")

    if any(v is None for v in (cathode_loading, cathode_spec_cap, anode_loading, anode_spec_cap)):
        return None  # Can't compute — loadings or specific capacities missing

    cathode_areal_cap = cathode_loading * cathode_spec_cap
    if cathode_areal_cap <= 0:
        return None  # Degenerate cathode — can't compute ratio

    computed_np = (anode_loading * anode_spec_cap) / cathode_areal_cap

    # Check for discrepancy with declared value (informational, not gating)
    declared_np = _get_nested(cell, "electrochemistry.anode.np_ratio")
    discrepancy_note = ""
    if declared_np is not None and abs(declared_np - computed_np) > 0.05:
        discrepancy_note = (
            f" Declared np_ratio={declared_np:.3f} disagrees with computed "
            f"value {computed_np:.3f} (delta={abs(declared_np - computed_np):.3f})."
        )

    if computed_np < 1.05:
        return ValidationError(
            path="electrochemistry (computed N/P ratio)",
            message=f"Computed N/P ratio {computed_np:.3f} is below minimum 1.05. "
            f"Calculated from: anode ({anode_loading} mg/cm² × {anode_spec_cap} mAh/g) "
            f"/ cathode ({cathode_loading} mg/cm² × {cathode_spec_cap} mAh/g). "
            f"Risk of lithium plating on anode. "
            f"Increase anode loading or decrease cathode loading.{discrepancy_note}",
            value=computed_np,
            constraint="computed N/P ratio >= 1.05 (lithium plating prevention)",
        )

    if computed_np > 1.25:
        return ValidationError(
            path="electrochemistry (computed N/P ratio)",
            message=f"Computed N/P ratio {computed_np:.3f} exceeds maximum 1.25. "
            f"Calculated from: anode ({anode_loading} mg/cm² × {anode_spec_cap} mAh/g) "
            f"/ cathode ({cathode_loading} mg/cm² × {cathode_spec_cap} mAh/g). "
            f"Risk of interface instability. "
            f"Decrease anode loading or increase cathode loading.{discrepancy_note}",
            value=computed_np,
            constraint="computed N/P ratio <= 1.25 (interface stability)",
        )

    return None


def check_cathode_loading_reasonable(cell: dict) -> ValidationError | None:
    """
    Constraint: Cathode loading should be within typical automotive ranges.

    From YAML: RANGE: [5.0 - 30.0] mg/cm², Typical: 15-25 mg/cm²
    """
    loading = _get_nested(cell, "electrochemistry.cathode.loading_mg_cm2")

    if loading is None:
        return None

    if loading < 5.0 or loading > 30.0:
        return ValidationError(
            path="electrochemistry.cathode.loading_mg_cm2",
            message=f"Cathode loading {loading} mg/cm² is outside valid range [5.0 - 30.0]. "
            f"Typical automotive range: 15-25 mg/cm².",
            value=loading,
            constraint="5.0 <= loading <= 30.0 mg/cm²",
        )

    return None


def check_anode_loading_reasonable(cell: dict) -> ValidationError | None:
    """
    Constraint: Anode loading should be within typical ranges.

    From YAML: RANGE: [5.0 - 20.0] mg/cm²
    """
    loading = _get_nested(cell, "electrochemistry.anode.loading_mg_cm2")

    if loading is None:
        return None

    if loading < 5.0 or loading > 20.0:
        return ValidationError(
            path="electrochemistry.anode.loading_mg_cm2",
            message=f"Anode loading {loading} mg/cm² is outside valid range [5.0 - 20.0].",
            value=loading,
            constraint="5.0 <= loading <= 20.0 mg/cm²",
        )

    return None


def check_separator_porosity_valid(cell: dict) -> ValidationError | None:
    """
    Constraint: Separator porosity must be in physically meaningful range.

    From YAML: RANGE: [30.0 - 55.0] %
    """
    porosity = _get_nested(cell, "electrochemistry.separator.porosity_pct")

    if porosity is None:
        return None

    if porosity < 30.0 or porosity > 55.0:
        return ValidationError(
            path="electrochemistry.separator.porosity_pct",
            message=f"Separator porosity {porosity}% is outside range [30.0 - 55.0]%. "
            f"Lower porosity = stronger, higher = faster ion transport.",
            value=porosity,
            constraint="30.0 <= porosity <= 55.0 %",
        )

    return None


def check_electrolyte_salt_concentration(cell: dict) -> ValidationError | None:
    """
    Constraint: Electrolyte salt concentration in reasonable range.

    From YAML: RANGE: [0.8 - 1.5] mol/L, Default: 1.2 M
    """
    concentration = _get_nested(cell, "electrochemistry.electrolyte.salt_concentration_m")

    if concentration is None:
        return None

    if concentration < 0.8 or concentration > 1.5:
        return ValidationError(
            path="electrochemistry.electrolyte.salt_concentration_m",
            message=f"Salt concentration {concentration} M is outside range [0.8 - 1.5]. "
            f"Typical: 1.2 M.",
            value=concentration,
            constraint="0.8 <= concentration <= 1.5 M",
        )

    return None


# ═══════════════════════════════════════════════════════════════
# STACK CONFIGURATION CONSTRAINTS
# ═══════════════════════════════════════════════════════════════


def check_stacks_positive(cell: dict) -> ValidationError | None:
    """
    Constraint: Must have at least one stack.

    From YAML: RANGE: [1 - 4], Typical: 2 stacks
    """
    stacks = _get_nested(cell, "stack_config.architecture.num_stacks")

    if stacks is None or stacks < 1:
        return ValidationError(
            path="stack_config.architecture.num_stacks",
            message=f"Must have at least 1 stack. Got {stacks}.",
            value=stacks,
            constraint="num_stacks >= 1",
        )

    if stacks > 4:
        return ValidationError(
            path="stack_config.architecture.num_stacks",
            message=f"Number of stacks {stacks} exceeds typical maximum of 4.",
            value=stacks,
            constraint="num_stacks <= 4",
        )

    return None


def check_electrode_pairs_positive(cell: dict) -> ValidationError | None:
    """
    Constraint: Must have at least one electrode pair per stack.

    From YAML: RANGE: [10 - 100], Typical: 30-60 pairs per stack
    """
    pairs = _get_nested(cell, "stack_config.architecture.electrode_pairs_per_stack")

    if pairs is None or pairs < 10:
        return ValidationError(
            path="stack_config.architecture.electrode_pairs_per_stack",
            message=f"Must have at least 10 electrode pairs per stack. Got {pairs}.",
            value=pairs,
            constraint="electrode_pairs >= 10",
        )

    if pairs > 100:
        return ValidationError(
            path="stack_config.architecture.electrode_pairs_per_stack",
            message=f"Number of electrode pairs {pairs} exceeds maximum of 100.",
            value=pairs,
            constraint="electrode_pairs <= 100",
        )

    return None


def check_end_electrode_config_valid(cell: dict) -> ValidationError | None:
    """
    Constraint: End electrode configuration must be one of the valid options.

    From YAML: OPTIONS: ["BothNegative", "BothPositive", "PositiveNegative"]
    """
    config = _get_nested(cell, "stack_config.architecture.end_electrode_config")

    if config is None:
        return None

    valid_options = ["BothNegative", "BothPositive", "PositiveNegative"]
    if config not in valid_options:
        return ValidationError(
            path="stack_config.architecture.end_electrode_config",
            message=f"Invalid end electrode configuration '{config}'. "
            f"Must be one of: {valid_options}.",
            value=config,
            constraint=f"end_electrode_config in {valid_options}",
        )

    return None


def check_cathode_material_valid(cell: dict) -> ValidationError | None:
    """
    Constraint: Cathode material should be a known chemistry.

    Common options: NCM811, NCA, LFP, LCO
    """
    material = _get_nested(cell, "electrochemistry.cathode.material_name")

    if material is None:
        return None

    # Just check it's non-empty and string
    if not isinstance(material, str) or len(material) == 0:
        return ValidationError(
            path="electrochemistry.cathode.material_name",
            message=f"Cathode material must be a non-empty string. Got: {material}",
            value=material,
            constraint="material_name is non-empty string",
        )

    return None


def check_anode_material_valid(cell: dict) -> ValidationError | None:
    """
    Constraint: Anode material should be a known type.

    Common options: Graphite, SiOx, Li-metal
    """
    material = _get_nested(cell, "electrochemistry.anode.material_name")

    if material is None:
        return None

    if not isinstance(material, str) or len(material) == 0:
        return ValidationError(
            path="electrochemistry.anode.material_name",
            message=f"Anode material must be a non-empty string. Got: {material}",
            value=material,
            constraint="material_name is non-empty string",
        )

    return None


# ═══════════════════════════════════════════════════════════════
# POUCH-SPECIFIC CONSTRAINTS
# ═══════════════════════════════════════════════════════════════


def check_pouch_anode_offset_positive(cell: dict) -> ValidationError | None:
    """
    Pouch Constraint: Anode offset must be positive (anode larger than cathode).

    The anode must extend beyond the cathode on all sides to prevent lithium
    plating at the edges. Typical range: 0.5-5.0 mm offset.
    """
    offset = _get_nested(cell, "geometry.anode_offset_mm")

    if offset is None:
        return None

    if offset < 0.5:
        return ValidationError(
            path="geometry.anode_offset_mm",
            message=f"Anode offset {offset} mm is below minimum 0.5 mm. "
            f"Anode must extend beyond cathode to prevent edge lithium plating.",
            value=offset,
            constraint="anode_offset >= 0.5 mm",
        )

    if offset > 5.0:
        return ValidationError(
            path="geometry.anode_offset_mm",
            message=f"Anode offset {offset} mm exceeds typical maximum 5.0 mm. "
            f"Excessive offset wastes material without safety benefit.",
            value=offset,
            constraint="anode_offset <= 5.0 mm",
        )

    return None


def check_pouch_separator_offset_positive(cell: dict) -> ValidationError | None:
    """
    Pouch Constraint: Separator offset must be positive (separator larger than anode).

    The separator must extend beyond the anode to ensure complete electrical
    isolation and prevent short circuits. Typical range: 0.5-5.0 mm offset.
    """
    offset = _get_nested(cell, "geometry.separator_offset_mm")

    if offset is None:
        return None

    if offset < 0.5:
        return ValidationError(
            path="geometry.separator_offset_mm",
            message=f"Separator offset {offset} mm is below minimum 0.5 mm. "
            f"Separator must extend beyond anode to prevent short circuits.",
            value=offset,
            constraint="separator_offset >= 0.5 mm",
        )

    if offset > 5.0:
        return ValidationError(
            path="geometry.separator_offset_mm",
            message=f"Separator offset {offset} mm exceeds typical maximum 5.0 mm. "
            f"Excessive offset wastes material.",
            value=offset,
            constraint="separator_offset <= 5.0 mm",
        )

    return None


def check_pouch_separator_larger_than_anode(cell: dict) -> ValidationError | None:
    """
    Pouch Constraint: Separator offset should be >= anode offset.

    The separator must fully cover the anode to ensure electrical isolation.
    """
    anode_offset = _get_nested(cell, "geometry.anode_offset_mm")
    sep_offset = _get_nested(cell, "geometry.separator_offset_mm")

    if anode_offset is None or sep_offset is None:
        return None

    if sep_offset < anode_offset:
        return ValidationError(
            path="geometry.separator_offset_mm",
            message=f"Separator offset {sep_offset} mm is smaller than anode offset {anode_offset} mm. "
            f"Separator must extend beyond anode for proper isolation.",
            value=sep_offset,
            constraint="separator_offset >= anode_offset",
        )

    return None


def check_pouch_electrode_pairs_positive(cell: dict) -> ValidationError | None:
    """
    Pouch Constraint: Must have at least 5 electrode pairs per stack.

    Pouch cells typically have fewer pairs than prismatic (5-100 range).
    """
    pairs = _get_nested(cell, "stack_config.electrode_pairs_per_stack")

    if pairs is None or pairs < 5:
        return ValidationError(
            path="stack_config.electrode_pairs_per_stack",
            message=f"Must have at least 5 electrode pairs per stack. Got {pairs}.",
            value=pairs,
            constraint="electrode_pairs >= 5",
        )

    if pairs > 100:
        return ValidationError(
            path="stack_config.electrode_pairs_per_stack",
            message=f"Number of electrode pairs {pairs} exceeds maximum of 100.",
            value=pairs,
            constraint="electrode_pairs <= 100",
        )

    return None


def check_pouch_stacks_positive(cell: dict) -> ValidationError | None:
    """
    Pouch Constraint: Must have at least one stack.

    From schema: RANGE: [1 - 4]
    """
    stacks = _get_nested(cell, "stack_config.num_stacks")

    if stacks is None or stacks < 1:
        return ValidationError(
            path="stack_config.num_stacks",
            message=f"Must have at least 1 stack. Got {stacks}.",
            value=stacks,
            constraint="num_stacks >= 1",
        )

    if stacks > 4:
        return ValidationError(
            path="stack_config.num_stacks",
            message=f"Number of stacks {stacks} exceeds typical maximum of 4.",
            value=stacks,
            constraint="num_stacks <= 4",
        )

    return None


def check_pouch_end_electrode_config_valid(cell: dict) -> ValidationError | None:
    """
    Pouch Constraint: End electrode configuration must be one of the valid options.
    """
    config = _get_nested(cell, "stack_config.end_electrode_config")

    if config is None:
        return None

    valid_options = ["BothNegative", "BothPositive", "PositiveNegative"]
    if config not in valid_options:
        return ValidationError(
            path="stack_config.end_electrode_config",
            message=f"Invalid end electrode configuration '{config}'. "
            f"Must be one of: {valid_options}.",
            value=config,
            constraint=f"end_electrode_config in {valid_options}",
        )

    return None


def check_pouch_packaging_offsets(cell: dict) -> ValidationError | None:
    """
    Pouch Constraint: Packaging offsets must be reasonable.

    Offsets define space between stack edge and pouch seal (2-20 mm typical).
    """
    offset_top = _get_nested(cell, "packaging.offset_top_mm")
    offset_bottom = _get_nested(cell, "packaging.offset_bottom_mm")
    offset_sides = _get_nested(cell, "packaging.offset_sides_mm")

    for name, offset in [("top", offset_top), ("bottom", offset_bottom), ("sides", offset_sides)]:
        if offset is None:
            continue

        if offset < 2.0:
            return ValidationError(
                path=f"packaging.offset_{name}_mm",
                message=f"Packaging offset {name} ({offset} mm) is below minimum 2.0 mm. "
                f"Insufficient space for pouch sealing.",
                value=offset,
                constraint=f"offset_{name} >= 2.0 mm",
            )

        if offset > 20.0:
            return ValidationError(
                path=f"packaging.offset_{name}_mm",
                message=f"Packaging offset {name} ({offset} mm) exceeds typical maximum 20.0 mm.",
                value=offset,
                constraint=f"offset_{name} <= 20.0 mm",
            )

    return None


# ═══════════════════════════════════════════════════════════════
# CYLINDRICAL-SPECIFIC CONSTRAINTS
# ═══════════════════════════════════════════════════════════════


def check_cylindrical_mandrel_diameter(cell: dict) -> ValidationError | None:
    """
    Cylindrical Constraint: Mandrel diameter must be reasonable for cell size.

    The mandrel (inner core) should be small enough to allow sufficient
    winding space but large enough to be manufacturable.
    Typical range: 1.5-8.0 mm
    """
    mandrel = _get_nested(cell, "winding.mandrel_diameter_mm")

    if mandrel is None:
        return None

    if mandrel < 1.5:
        return ValidationError(
            path="winding.mandrel_diameter_mm",
            message=f"Mandrel diameter {mandrel} mm is below minimum 1.5 mm. "
            f"Too small for manufacturing.",
            value=mandrel,
            constraint="mandrel_diameter >= 1.5 mm",
        )

    if mandrel > 8.0:
        return ValidationError(
            path="winding.mandrel_diameter_mm",
            message=f"Mandrel diameter {mandrel} mm exceeds typical maximum 8.0 mm. "
            f"Excessive mandrel wastes internal volume.",
            value=mandrel,
            constraint="mandrel_diameter <= 8.0 mm",
        )

    return None


def check_cylindrical_winding_clearance(cell: dict) -> ValidationError | None:
    """
    Cylindrical Constraint: Winding clearance must be positive but small.

    The gap between jelly roll outer diameter and can wall should allow
    for insertion while maximizing active material volume.
    Typical range: 0.05-0.5 mm
    """
    clearance = _get_nested(cell, "winding.winding_clearance_mm")

    if clearance is None:
        return None

    if clearance < 0.05:
        return ValidationError(
            path="winding.winding_clearance_mm",
            message=f"Winding clearance {clearance} mm is below minimum 0.05 mm. "
            f"Jelly roll may not fit in can.",
            value=clearance,
            constraint="winding_clearance >= 0.05 mm",
        )

    if clearance > 0.5:
        return ValidationError(
            path="winding.winding_clearance_mm",
            message=f"Winding clearance {clearance} mm exceeds typical maximum 0.5 mm. "
            f"Excessive clearance wastes internal volume.",
            value=clearance,
            constraint="winding_clearance <= 0.5 mm",
        )

    return None


def check_cylindrical_tension_factor(cell: dict) -> ValidationError | None:
    """
    Cylindrical Constraint: Winding tension factor must be in valid range.

    The tension factor represents compression during winding.
    1.0 = no compression, 0.95 = 5% compressed.
    Typical range: 0.90-1.0
    """
    tension = _get_nested(cell, "winding.winding_tension_factor")

    if tension is None:
        return None

    if tension < 0.90:
        return ValidationError(
            path="winding.winding_tension_factor",
            message=f"Winding tension factor {tension} is below minimum 0.90. "
            f"Excessive compression may damage electrodes.",
            value=tension,
            constraint="winding_tension_factor >= 0.90",
        )

    if tension > 1.0:
        return ValidationError(
            path="winding.winding_tension_factor",
            message=f"Winding tension factor {tension} exceeds maximum 1.0. "
            f"Cannot expand beyond theoretical thickness.",
            value=tension,
            constraint="winding_tension_factor <= 1.0",
        )

    return None


def check_cylindrical_tab_type_valid(cell: dict) -> ValidationError | None:
    """
    Cylindrical Constraint: Tab type must be valid.

    Options: "traditional" (welded tabs) or "tabless" (4680-style foil extensions)
    """
    tab_type = _get_nested(cell, "winding.tab_type")

    if tab_type is None:
        return None

    valid_options = ["traditional", "tabless"]
    if tab_type not in valid_options:
        return ValidationError(
            path="winding.tab_type",
            message=f"Invalid tab type '{tab_type}'. Must be one of: {valid_options}.",
            value=tab_type,
            constraint=f"tab_type in {valid_options}",
        )

    return None


def check_cylindrical_can_material_valid(cell: dict) -> ValidationError | None:
    """
    Cylindrical Constraint: Can material must be valid.

    Options: "steel", "aluminum", "nickel_plated_steel"
    """
    can_material = _get_nested(cell, "housing.can_material")

    if can_material is None:
        return None

    valid_options = ["steel", "aluminum", "nickel_plated_steel"]
    if can_material not in valid_options:
        return ValidationError(
            path="housing.can_material",
            message=f"Invalid can material '{can_material}'. Must be one of: {valid_options}.",
            value=can_material,
            constraint=f"can_material in {valid_options}",
        )

    return None


def check_cylindrical_jelly_roll_fits(cell: dict) -> ValidationError | None:
    """
    Cylindrical Constraint: Jelly roll must fit in can.

    The mandrel diameter plus typical electrode stack must leave room
    for winding clearance inside the can inner diameter.
    Inner diameter = diameter - 2 * wall_thickness
    """
    diameter = _get_nested(cell, "geometry.diameter_mm")
    wall_thickness = _get_nested(cell, "geometry.can_wall_thickness_mm")
    mandrel = _get_nested(cell, "winding.mandrel_diameter_mm")
    clearance = _get_nested(cell, "winding.winding_clearance_mm")

    if any(v is None for v in [diameter, wall_thickness, mandrel, clearance]):
        return None

    inner_diameter = diameter - 2 * wall_thickness
    available_for_winding = inner_diameter - mandrel - 2 * clearance

    # Need at least 2mm for electrodes (very minimal, most cells have ~7-15mm)
    if available_for_winding < 2.0:
        return ValidationError(
            path="geometry (jelly roll fit constraint)",
            message=f"Insufficient space for jelly roll. Available: {available_for_winding:.2f} mm. "
            f"Inner diameter {inner_diameter:.2f} mm - mandrel {mandrel} mm - "
            f"2 * clearance {clearance} mm leaves < 2 mm for electrodes. "
            f"Increase cell diameter, reduce mandrel, or reduce clearance.",
            value=available_for_winding,
            constraint="available_for_winding >= 2.0 mm",
        )

    return None


def check_cylindrical_header_height(cell: dict) -> ValidationError | None:
    """
    Cylindrical Constraint: Header height must be reasonable.

    Header should be tall enough for safety components but not too tall.
    Typical range: 2.0-6.0 mm
    """
    header = _get_nested(cell, "geometry.header_height_mm")

    if header is None:
        return None

    if header < 2.0:
        return ValidationError(
            path="geometry.header_height_mm",
            message=f"Header height {header} mm is below minimum 2.0 mm. "
            f"Insufficient space for safety components.",
            value=header,
            constraint="header_height >= 2.0 mm",
        )

    if header > 6.0:
        return ValidationError(
            path="geometry.header_height_mm",
            message=f"Header height {header} mm exceeds typical maximum 6.0 mm.",
            value=header,
            constraint="header_height <= 6.0 mm",
        )

    return None


def check_cylindrical_format_consistency(cell: dict) -> ValidationError | None:
    """
    Cylindrical Constraint: If format is specified, dimensions should be close.

    Standard formats: 18650 (18x65), 21700 (21x70), 4680 (46x80)
    Allow 1mm tolerance for manufacturing variations.
    """
    format_type = _get_nested(cell, "_meta.format")
    diameter = _get_nested(cell, "geometry.diameter_mm")
    length = _get_nested(cell, "geometry.length_mm")

    if format_type is None or format_type == "custom":
        return None

    if diameter is None or length is None:
        return None

    standard_formats = {
        "18650": (18.0, 65.0),
        "21700": (21.0, 70.0),
        "4680": (46.0, 80.0),
    }

    if format_type in standard_formats:
        expected_dia, expected_len = standard_formats[format_type]
        tolerance = 1.0

        if abs(diameter - expected_dia) > tolerance:
            return ValidationError(
                path="geometry.diameter_mm",
                message=f"Diameter {diameter} mm doesn't match {format_type} format "
                f"(expected ~{expected_dia} mm, tolerance {tolerance} mm). "
                f"Use 'custom' format for non-standard dimensions.",
                value=diameter,
                constraint=f"diameter within {tolerance} mm of {expected_dia}",
            )

        if abs(length - expected_len) > tolerance:
            return ValidationError(
                path="geometry.length_mm",
                message=f"Length {length} mm doesn't match {format_type} format "
                f"(expected ~{expected_len} mm, tolerance {tolerance} mm). "
                f"Use 'custom' format for non-standard dimensions.",
                value=length,
                constraint=f"length within {tolerance} mm of {expected_len}",
            )

    return None


# ═══════════════════════════════════════════════════════════════
# CONSTRAINT REGISTRY
# ═══════════════════════════════════════════════════════════════

# Common constraints that apply to both prismatic and pouch cells
COMMON_CONSTRAINTS: list[ConstraintFunc] = [
    # Electrochemistry constraints (common to all cell types)
    check_np_ratio,
    check_cathode_loading_reasonable,
    check_anode_loading_reasonable,
    check_separator_porosity_valid,
    check_electrolyte_salt_concentration,
    check_cathode_material_valid,
    check_anode_material_valid,
]

# Prismatic-specific constraints (geometry with walls)
PRISMATIC_CONSTRAINTS: list[ConstraintFunc] = [
    # Geometry constraints (prismatic uses cavity with walls)
    check_internal_height_positive,
    check_internal_width_positive,
    check_internal_thickness_positive,
    check_cathode_fits_in_cavity,
    # Stack configuration constraints (prismatic paths)
    check_stacks_positive,
    check_electrode_pairs_positive,
    check_end_electrode_config_valid,
]

# Pouch-specific constraints (symmetric offsets, flexible packaging)
POUCH_CONSTRAINTS: list[ConstraintFunc] = [
    # Geometry constraints (pouch uses symmetric offsets)
    check_pouch_anode_offset_positive,
    check_pouch_separator_offset_positive,
    check_pouch_separator_larger_than_anode,
    # Stack configuration constraints (pouch paths)
    check_pouch_stacks_positive,
    check_pouch_electrode_pairs_positive,
    check_pouch_end_electrode_config_valid,
    # Packaging constraints
    check_pouch_packaging_offsets,
]

# Cylindrical-specific constraints (jelly roll winding, can housing)
CYLINDRICAL_CONSTRAINTS: list[ConstraintFunc] = [
    # Winding constraints
    check_cylindrical_mandrel_diameter,
    check_cylindrical_winding_clearance,
    check_cylindrical_tension_factor,
    check_cylindrical_tab_type_valid,
    # Geometry constraints
    check_cylindrical_jelly_roll_fits,
    check_cylindrical_header_height,
    check_cylindrical_format_consistency,
    # Housing constraints
    check_cylindrical_can_material_valid,
]

# Legacy: ALL_CONSTRAINTS for backward compatibility (defaults to prismatic)
ALL_CONSTRAINTS: list[ConstraintFunc] = COMMON_CONSTRAINTS + PRISMATIC_CONSTRAINTS

# ═══════════════════════════════════════════════════════════════
# CONSTRAINT REGISTRY — ID mapping for per-constraint logging
# Each entry: (constraint_id, human_name, check_function)
# ═══════════════════════════════════════════════════════════════

_RegistryEntry = tuple[str, str, ConstraintFunc]

_COMMON_REGISTRY: list[_RegistryEntry] = [
    ("C1", "np_ratio", check_np_ratio),
    ("C2", "cathode_loading", check_cathode_loading_reasonable),
    ("C3", "anode_loading", check_anode_loading_reasonable),
    ("C4", "separator_porosity", check_separator_porosity_valid),
    ("C5", "electrolyte_concentration", check_electrolyte_salt_concentration),
    ("C6", "cathode_material", check_cathode_material_valid),
    ("C7", "anode_material", check_anode_material_valid),
]

_PRISMATIC_REGISTRY: list[_RegistryEntry] = [
    ("PR1", "internal_height", check_internal_height_positive),
    ("PR2", "internal_width", check_internal_width_positive),
    ("PR3", "internal_thickness", check_internal_thickness_positive),
    ("PR4", "cathode_fits_cavity", check_cathode_fits_in_cavity),
    ("PR5", "stacks_count", check_stacks_positive),
    ("PR6", "electrode_pairs", check_electrode_pairs_positive),
    ("PR7", "end_electrode_config", check_end_electrode_config_valid),
]

_POUCH_REGISTRY: list[_RegistryEntry] = [
    ("PO1", "anode_offset", check_pouch_anode_offset_positive),
    ("PO2", "separator_offset", check_pouch_separator_offset_positive),
    ("PO3", "separator_covers_anode", check_pouch_separator_larger_than_anode),
    ("PO4", "stacks_count", check_pouch_stacks_positive),
    ("PO5", "electrode_pairs", check_pouch_electrode_pairs_positive),
    ("PO6", "end_electrode_config", check_pouch_end_electrode_config_valid),
    ("PO7", "packaging_offsets", check_pouch_packaging_offsets),
]

_CYLINDRICAL_REGISTRY: list[_RegistryEntry] = [
    ("CY1", "mandrel_diameter", check_cylindrical_mandrel_diameter),
    ("CY2", "winding_clearance", check_cylindrical_winding_clearance),
    ("CY3", "tension_factor", check_cylindrical_tension_factor),
    ("CY4", "tab_type", check_cylindrical_tab_type_valid),
    ("CY5", "jelly_roll_fits", check_cylindrical_jelly_roll_fits),
    ("CY6", "header_height", check_cylindrical_header_height),
    ("CY7", "format_consistency", check_cylindrical_format_consistency),
    ("CY8", "can_material", check_cylindrical_can_material_valid),
]


def _get_registry(cell_type: str) -> list[_RegistryEntry]:
    """Select constraint registry based on cell type."""
    cell_type_lower = cell_type.lower()
    if cell_type_lower == "pouch":
        return _COMMON_REGISTRY + _POUCH_REGISTRY
    if cell_type_lower == "cylindrical":
        return _COMMON_REGISTRY + _CYLINDRICAL_REGISTRY
    return _COMMON_REGISTRY + _PRISMATIC_REGISTRY


def validate_physics(cell_dict: dict, cell_type: str = "prismatic") -> ValidationResult:
    """
    Validate cell definition against physics constraints (Level 2).

    This checks cross-field constraints that represent physics rules and
    manufacturing feasibility. It should only be called AFTER schema validation
    (Level 1) has passed.

    Returns a ValidationResult with:
    - .valid: bool — overall pass/fail
    - .errors: list[ValidationError] — failures only (for LLM feedback)
    - .constraint_results: list[ConstraintResult] — ALL constraints, pass AND fail

    Args:
        cell_dict: Cell definition (already passed schema validation)
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical"

    Example:
        result = validate_physics(cell_dict, cell_type="pouch")
        for cr in result.constraint_results:
            print(f"{cr.constraint_id} {cr.name}: {'PASS' if cr.passed else 'FAIL'}")
    """
    errors: list[ValidationError] = []
    constraint_results: list[ConstraintResult] = []

    registry = _get_registry(cell_type)

    for constraint_id, name, check_fn in registry:
        t0 = time.perf_counter_ns()
        error = check_fn(cell_dict)
        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000

        if error is not None:
            errors.append(error)
            constraint_results.append(ConstraintResult(
                constraint_id=constraint_id,
                name=name,
                passed=False,
                actual_value=error.value,
                threshold=error.constraint,
                message=error.message,
                check_time_ms=elapsed_ms,
            ))
        else:
            constraint_results.append(ConstraintResult(
                constraint_id=constraint_id,
                name=name,
                passed=True,
                actual_value=None,
                threshold="",
                message="",
                check_time_ms=elapsed_ms,
            ))

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        level="physics",
        constraint_results=constraint_results,
    )


def get_constraint_descriptions(cell_type: str = "prismatic") -> str:
    """
    Get human-readable descriptions of all physics constraints.

    Useful for LLM context or documentation.

    Args:
        cell_type: Type of cell - "prismatic", "pouch", or "cylindrical" (default: "prismatic")

    Returns:
        Human-readable constraint descriptions string
    """
    common_descriptions = [
        "ELECTROCHEMISTRY CONSTRAINTS (common to all cell types):",
        "  - N/P ratio in [1.05, 1.25]: anode_capacity / cathode_capacity",
        "    (Prevents lithium plating below 1.05, interface instability above 1.25)",
        "  - Cathode loading in [5.0, 30.0] mg/cm²",
        "  - Anode loading in [5.0, 20.0] mg/cm²",
        "  - Separator porosity in [30, 55] %",
        "  - Electrolyte concentration in [0.8, 1.5] mol/L",
        "  - Cathode material is non-empty string",
        "  - Anode material is non-empty string",
    ]

    if cell_type.lower() == "pouch":
        descriptions = (
            [
                "Physics Constraints Enforced by CellCAD Validation Module (POUCH):",
                "",
                "GEOMETRY CONSTRAINTS (pouch - symmetric offsets):",
                "  - Anode offset in [0.5, 5.0] mm (anode larger than cathode)",
                "  - Separator offset in [0.5, 5.0] mm (separator larger than anode)",
                "  - Separator offset >= anode offset (proper isolation)",
                "",
            ]
            + common_descriptions
            + [
                "",
                "STACK CONFIGURATION CONSTRAINTS:",
                "  - Number of stacks in [1, 4]",
                "  - Electrode pairs per stack in [5, 100]",
                "  - End electrode config in ['BothNegative', 'BothPositive', 'PositiveNegative']",
                "",
                "PACKAGING CONSTRAINTS:",
                "  - Packaging offsets (top, bottom, sides) in [2.0, 20.0] mm",
            ]
        )
    elif cell_type.lower() == "cylindrical":
        descriptions = (
            [
                "Physics Constraints Enforced by CellCAD Validation Module (CYLINDRICAL):",
                "",
                "GEOMETRY CONSTRAINTS (cylindrical - jelly roll winding):",
                "  - Mandrel diameter in [1.5, 8.0] mm (inner winding core)",
                "  - Winding clearance in [0.05, 0.5] mm (gap to can wall)",
                "  - Winding tension factor in [0.90, 1.0] (compression during winding)",
                "  - Header height in [2.0, 6.0] mm (space for safety components)",
                "  - Jelly roll must fit: available winding space >= 2.0 mm",
                "  - Format consistency: if 18650/21700/4680 format, dimensions must match",
                "",
            ]
            + common_descriptions
            + [
                "",
                "WINDING CONFIGURATION CONSTRAINTS:",
                "  - Tab type in ['traditional', 'tabless'] (welded tabs vs 4680-style)",
                "",
                "HOUSING CONSTRAINTS:",
                "  - Can material in ['steel', 'aluminum', 'nickel_plated_steel']",
            ]
        )
    else:
        descriptions = (
            [
                "Physics Constraints Enforced by CellCAD Validation Module (PRISMATIC):",
                "",
                "GEOMETRY CONSTRAINTS (prismatic - rigid case with walls):",
                "  - Internal cavity height > 0: height - wall_top - wall_bottom > 0",
                "  - Internal cavity width > 0: width - 2*wall_sides > 0",
                "  - Internal cavity thickness > 0: thickness - 2*wall_front_back > 0",
                "  - Cathode fits: cathode_height < internal_cavity_height",
                "",
            ]
            + common_descriptions
            + [
                "",
                "STACK CONFIGURATION CONSTRAINTS:",
                "  - Number of stacks in [1, 4]",
                "  - Electrode pairs per stack in [10, 100]",
                "  - End electrode config in ['BothNegative', 'BothPositive', 'PositiveNegative']",
            ]
        )

    return "\n".join(descriptions)
