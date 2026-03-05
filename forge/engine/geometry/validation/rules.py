"""Individual validation rule implementations."""

from typing import TYPE_CHECKING

from .models import Severity, ValidationCategory, ValidationResult
from .thresholds import DEFAULT_THRESHOLDS, ValidationThresholds


if TYPE_CHECKING:
    from ..detailed_geometry import DetailedGeometry


# =============================================================================
# DIMENSIONAL RULES
# =============================================================================


def validate_stack_fits_in_casing(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """DIM_001: Verify electrode stack fits within casing internal dimensions."""
    rule_id = "DIM_001"
    rule_name = "Stack fits in casing"
    category = ValidationCategory.DIMENSIONAL

    ext = geometry.external_geometry
    stack_thickness_mm = geometry.total_stack_thickness_mm()

    # Calculate available internal space
    if geometry.cell_type in ("pouch", "prismatic"):
        total_thickness = ext.thickness_mm or ext.height_mm or 0
        wall = ext.wall_thickness_mm or 0.5
        available = total_thickness - 2 * wall - thresholds.casing_fit_margin_mm

        passed = stack_thickness_mm <= available
        margin = available - stack_thickness_mm

        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.ERROR,
            passed=passed,
            message=(
                f"Stack thickness ({stack_thickness_mm:.2f} mm) "
                f"{'fits within' if passed else 'exceeds'} "
                f"available space ({available:.2f} mm). Margin: {margin:.2f} mm"
            ),
            details={
                "stack_thickness_mm": stack_thickness_mm,
                "available_space_mm": available,
                "margin_mm": margin,
            },
        )

    elif geometry.cell_type == "cylindrical":
        # For cylindrical, check jellyroll diameter
        winding = geometry.layer_stack
        if hasattr(winding, "outer_diameter_mm"):
            jellyroll_od = winding.outer_diameter_mm
            can_id = (ext.diameter_mm or 46) - 2 * (ext.wall_thickness_mm or 0.5)
            available = can_id - thresholds.casing_fit_margin_mm

            passed = jellyroll_od <= available
            margin = available - jellyroll_od

            return ValidationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                category=category,
                severity=Severity.ERROR,
                passed=passed,
                message=(
                    f"Jellyroll OD ({jellyroll_od:.2f} mm) "
                    f"{'fits within' if passed else 'exceeds'} "
                    f"can ID ({available:.2f} mm). Margin: {margin:.2f} mm"
                ),
                details={
                    "jellyroll_od_mm": jellyroll_od,
                    "can_id_mm": available,
                    "margin_mm": margin,
                },
            )

    # Fallback if dimensions not available
    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.INFO,
        passed=True,
        message="Insufficient dimension data for validation",
        details={},
    )


def validate_layer_thickness_consistency(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """DIM_002: Verify calculated stack matches sum of individual layers."""
    rule_id = "DIM_002"
    rule_name = "Layer thickness consistency"
    category = ValidationCategory.DIMENSIONAL

    stack = geometry.layer_stack

    if not hasattr(stack, "layers") or not stack.layers:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No individual layer data to validate",
            details={},
        )

    # Sum individual layer thicknesses
    sum_thickness_um = sum(layer.thickness_um for layer in stack.layers)
    reported_thickness_um = stack.total_thickness_um

    if reported_thickness_um == 0:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No reported total thickness to compare",
            details={},
        )

    deviation = abs(sum_thickness_um - reported_thickness_um) / reported_thickness_um
    passed = deviation <= thresholds.layer_thickness_tolerance

    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.WARNING,
        passed=passed,
        message=(
            f"Layer sum ({sum_thickness_um:.1f} um) vs reported "
            f"({reported_thickness_um:.1f} um): "
            f"{deviation * 100:.1f}% deviation "
            f"(threshold: {thresholds.layer_thickness_tolerance * 100:.0f}%)"
        ),
        details={
            "sum_thickness_um": sum_thickness_um,
            "reported_thickness_um": reported_thickness_um,
            "deviation_pct": deviation * 100,
        },
    )


# =============================================================================
# SAFETY RULES
# =============================================================================


def validate_anode_overhang(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """SAF_001: Verify anode extends beyond cathode (prevents lithium plating)."""
    rule_id = "SAF_001"
    rule_name = "Anode overhang positive"
    category = ValidationCategory.SAFETY

    zones = geometry.coating_zones

    if zones is None:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No coating zone data available",
            details={},
        )

    overhang_x = zones.anode_overhang_x_mm or 0
    overhang_y = zones.anode_overhang_y_mm or 0
    min_overhang = min(overhang_x, overhang_y)

    passed = min_overhang > thresholds.min_anode_overhang_mm

    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.ERROR,
        passed=passed,
        message=(
            f"Anode overhang: X={overhang_x:.2f} mm, Y={overhang_y:.2f} mm. "
            f"{'Adequate' if passed else 'INSUFFICIENT - risk of lithium plating'}"
        ),
        details={
            "overhang_x_mm": overhang_x,
            "overhang_y_mm": overhang_y,
            "min_required_mm": thresholds.min_anode_overhang_mm,
        },
    )


def validate_separator_overhang(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """SAF_002: Verify separator extends beyond anode (prevents short circuit)."""
    rule_id = "SAF_002"
    rule_name = "Separator covers anode"
    category = ValidationCategory.SAFETY

    zones = geometry.coating_zones

    if zones is None:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No coating zone data available",
            details={},
        )

    separator_overhang = zones.separator_overhang_mm or 0
    passed = separator_overhang > thresholds.min_separator_overhang_mm

    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.ERROR,
        passed=passed,
        message=(
            f"Separator overhang beyond anode: {separator_overhang:.2f} mm. "
            f"{'Adequate' if passed else 'INSUFFICIENT - risk of internal short circuit'}"
        ),
        details={
            "separator_overhang_mm": separator_overhang,
            "min_required_mm": thresholds.min_separator_overhang_mm,
        },
    )


def validate_np_ratio(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """SAF_003: Verify N/P ratio is within safe range."""
    rule_id = "SAF_003"
    rule_name = "N/P ratio in range"
    category = ValidationCategory.SAFETY

    # N/P ratio might be stored in various places
    np_ratio = None

    # Check if stored in geometry metadata or archetype
    if hasattr(geometry, "np_ratio"):
        np_ratio = geometry.np_ratio

    if np_ratio is None:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="N/P ratio data not available",
            details={},
        )

    passed = thresholds.np_ratio_min <= np_ratio <= thresholds.np_ratio_max

    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.WARNING,
        passed=passed,
        message=(
            f"N/P ratio: {np_ratio:.2f} "
            f"(acceptable range: {thresholds.np_ratio_min:.2f}-"
            f"{thresholds.np_ratio_max:.2f})"
        ),
        details={
            "np_ratio": np_ratio,
            "min_acceptable": thresholds.np_ratio_min,
            "max_acceptable": thresholds.np_ratio_max,
        },
    )


# =============================================================================
# MANUFACTURING RULES
# =============================================================================


def validate_min_coating_thickness(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """MFG_001: Verify coating thicknesses are manufacturable."""
    rule_id = "MFG_001"
    rule_name = "Minimum coating thickness"
    category = ValidationCategory.MANUFACTURING

    stack = geometry.layer_stack

    if not hasattr(stack, "layers") or not stack.layers:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No layer data available",
            details={},
        )

    from ..layer_stack import LayerType

    coating_layers = [
        layer
        for layer in stack.layers
        if layer.layer_type in (LayerType.CATHODE_COATING, LayerType.ANODE_COATING)
    ]

    if not coating_layers:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No coating layers found",
            details={},
        )

    min_thickness = min(layer.thickness_um for layer in coating_layers)
    passed = min_thickness >= thresholds.min_coating_thickness_um

    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.WARNING,
        passed=passed,
        message=(
            f"Minimum coating thickness: {min_thickness:.1f} um "
            f"(minimum manufacturable: {thresholds.min_coating_thickness_um:.1f} um)"
        ),
        details={
            "min_thickness_um": min_thickness,
            "threshold_um": thresholds.min_coating_thickness_um,
        },
    )


def validate_min_collector_thickness(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """MFG_002: Verify current collector thicknesses are manufacturable."""
    rule_id = "MFG_002"
    rule_name = "Minimum collector thickness"
    category = ValidationCategory.MANUFACTURING

    stack = geometry.layer_stack

    if not hasattr(stack, "layers") or not stack.layers:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No layer data available",
            details={},
        )

    from ..layer_stack import LayerType

    collector_layers = [
        layer
        for layer in stack.layers
        if layer.layer_type in (LayerType.CATHODE_COLLECTOR, LayerType.ANODE_COLLECTOR)
    ]

    if not collector_layers:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No collector layers found",
            details={},
        )

    min_thickness = min(layer.thickness_um for layer in collector_layers)
    passed = min_thickness >= thresholds.min_collector_thickness_um

    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.WARNING,
        passed=passed,
        message=(
            f"Minimum collector thickness: {min_thickness:.1f} um "
            f"(minimum manufacturable: {thresholds.min_collector_thickness_um:.1f} um)"
        ),
        details={
            "min_thickness_um": min_thickness,
            "threshold_um": thresholds.min_collector_thickness_um,
        },
    )


def validate_min_separator_thickness(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """MFG_003: Verify separator thickness is manufacturable."""
    rule_id = "MFG_003"
    rule_name = "Minimum separator thickness"
    category = ValidationCategory.MANUFACTURING

    stack = geometry.layer_stack

    if not hasattr(stack, "layers") or not stack.layers:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No layer data available",
            details={},
        )

    from ..layer_stack import LayerType

    separator_layers = [layer for layer in stack.layers if layer.layer_type == LayerType.SEPARATOR]

    if not separator_layers:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No separator layers found",
            details={},
        )

    min_thickness = min(layer.thickness_um for layer in separator_layers)
    passed = min_thickness >= thresholds.min_separator_thickness_um

    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.WARNING,
        passed=passed,
        message=(
            f"Minimum separator thickness: {min_thickness:.1f} um "
            f"(minimum manufacturable: {thresholds.min_separator_thickness_um:.1f} um)"
        ),
        details={
            "min_thickness_um": min_thickness,
            "threshold_um": thresholds.min_separator_thickness_um,
        },
    )


def validate_max_layer_count(
    geometry: "DetailedGeometry",
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """MFG_004: Verify layer/wind count is reasonable for cell type."""
    rule_id = "MFG_004"
    rule_name = "Layer count reasonable"
    category = ValidationCategory.MANUFACTURING

    stack = geometry.layer_stack

    if geometry.cell_type == "cylindrical":
        if hasattr(stack, "num_winds"):
            count = stack.num_winds
            max_count = thresholds.max_winds_cylindrical
            unit = "winds"
        else:
            return ValidationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                category=category,
                severity=Severity.INFO,
                passed=True,
                message="No wind count data available",
                details={},
            )
    else:
        if hasattr(stack, "num_electrode_pairs"):
            count = stack.num_electrode_pairs
            max_count = (
                thresholds.max_electrode_pairs_prismatic
                if geometry.cell_type == "prismatic"
                else thresholds.max_electrode_pairs_pouch
            )
            unit = "electrode pairs"
        else:
            return ValidationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                category=category,
                severity=Severity.INFO,
                passed=True,
                message="No layer count data available",
                details={},
            )

    passed = count <= max_count

    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.INFO,
        passed=passed,
        message=(
            f"{count} {unit} "
            f"({'typical' if passed else 'unusually high'} for "
            f"{geometry.cell_type}, max typical: {max_count})"
        ),
        details={
            "count": count,
            "max_typical": max_count,
            "unit": unit,
        },
    )


# =============================================================================
# CROSS-VALIDATION RULES
# =============================================================================


def validate_capacity_consistency(
    geometry: "DetailedGeometry",
    declared_capacity_ah: float | None = None,
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """XVAL_001: Verify geometry is consistent with declared capacity."""
    rule_id = "XVAL_001"
    rule_name = "Capacity consistency"
    category = ValidationCategory.CROSS_VALIDATION

    if declared_capacity_ah is None:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No declared capacity to validate against",
            details={},
        )

    # This would need electrode area and loading data to calculate
    # For now, return info-level pass
    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.INFO,
        passed=True,
        message=(
            f"Declared capacity: {declared_capacity_ah:.1f} Ah "
            "(detailed calculation not yet implemented)"
        ),
        details={
            "declared_capacity_ah": declared_capacity_ah,
        },
    )


def validate_mass_consistency(
    geometry: "DetailedGeometry",
    declared_mass_g: float | None = None,
    thresholds: ValidationThresholds = DEFAULT_THRESHOLDS,
) -> ValidationResult:
    """XVAL_002: Verify geometry is consistent with declared mass."""
    rule_id = "XVAL_002"
    rule_name = "Mass consistency"
    category = ValidationCategory.CROSS_VALIDATION

    if declared_mass_g is None:
        return ValidationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category=category,
            severity=Severity.INFO,
            passed=True,
            message="No declared mass to validate against",
            details={},
        )

    # This would need material densities and volumes to calculate
    # For now, return info-level pass
    return ValidationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        severity=Severity.INFO,
        passed=True,
        message=(
            f"Declared mass: {declared_mass_g:.1f} g (detailed calculation not yet implemented)"
        ),
        details={
            "declared_mass_g": declared_mass_g,
        },
    )


# =============================================================================
# RULE REGISTRY
# =============================================================================

ALL_RULES = [
    # Dimensional
    validate_stack_fits_in_casing,
    validate_layer_thickness_consistency,
    # Safety
    validate_anode_overhang,
    validate_separator_overhang,
    validate_np_ratio,
    # Manufacturing
    validate_min_coating_thickness,
    validate_min_collector_thickness,
    validate_min_separator_thickness,
    validate_max_layer_count,
    # Cross-validation
    validate_capacity_consistency,
    validate_mass_consistency,
]
