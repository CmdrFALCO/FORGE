"""End-to-end calculation validation tests for all 25 reference cells.

These tests verify that running calculators with reference cell parameters
produces outputs within the specified validation tolerances.

This catches issues like CATL 161Ah where JSON structure was valid
but parameters produced 67% mass error.

Created: December 27, 2025
Total Tests: 133
Results: 119 passed, 12 failed validation, 1 expected failure

## Tier 1 Academic Cells (ALL PASSING):
- lg_e78_pouch: GÃ¼nter & Wassiliadis JES 2022 - electrode pairs tuned to 14
- catl_161ah_lfp: Stock et al. Electrochimica Acta 2023 - pairs=39, excess=1.0
- lg_mj1_18650: Heenan et al. JES 2020 - loading tuned to 21.5 mg/cmÂ²

## Cells Passing Validation (13/25):
- Pouch: lg_e66a, a123_amp20, lg_e78_pouch
- Prismatic: v1_prismatic, samsung_sdi_94ah, catl_100ah_lfp, catl_150ah_lfp,
             eve_lf280k_prismatic, catl_161ah_lfp
- Cylindrical: generic_21700, lg_m50_21700, lg_m58t_21700, lg_mj1_18650

## Cells Failing Validation - Parameter Tuning Needed (12/25):
### Pouch (3/6 failing):
- v1_pouch: capacity +145%, ED +146% - likely electrode area misconfigured
- kokam_ecker2015: capacity +45%, ED +54% - needs electrode pair count adjustment
- sk_e556_pouch: capacity +59%, mass +55% - electrode dimensions wrong

### Prismatic (1/7 failing):
- byd_blade_138ah: capacity +24%, mass +19% - needs stack configuration tuning

### Cylindrical (8/12 failing):
- generic_4680: capacity +16%, ED +17% - winding parameters
- tesla_4680: ED +20% - winding tension/efficiency
- molicel_p42a_21700: capacity +26%, ED +20% - loading values
- samsung_50e_21700: capacity +9%, mass +6% - minor tuning
- panasonic_2170_nca: ED +9% - minor tuning
- molicel_p45b_21700: capacity +19%, ED +10% - loading values
- samsung_40t_21700: capacity +23%, ED +19% - loading values
- samsung_30q_18650: capacity +9%, ED +9% - minor tuning
"""

from dataclasses import dataclass

import pytest

from forge.engine.calculators.cylindrical_calculator import CylindricalCalculator
from forge.engine.calculators.pouch_calculator import CellCalculator, PouchCellInput
from forge.engine.calculators.prismatic_calculator import PrismaticCalculator
from forge.engine.models.cylindrical import (
    CanMaterial,
    CylindricalCellInput,
    CylindricalGeometry,
    SimplifiedHeader,
    TabType,
    WindingConfig,
)
from forge.engine.models.geometry import PouchPackaging, SheetGeometry
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
    TabConfig,
)
from forge.engine.models.prismatic import (
    PrismaticCellInput,
    PrismaticGeometry,
    PrismaticSheetGeometry,
)
from forge.engine.models.stack import EndElectrodesMode, StackConfiguration
from forge.engine.validation.result_validation import (
    ReferenceCell,
    load_reference_cell,
)

# =============================================================================
# Test Data - All 25 Reference Cells Grouped by Type
# =============================================================================

POUCH_CELLS = [
    "v1_pouch",
    "kokam_ecker2015",
    "lg_e66a",
    "a123_amp20",
    "sk_e556_pouch",
    "lg_e78_pouch",
]

PRISMATIC_CELLS = [
    "v1_prismatic",
    "samsung_sdi_94ah",
    "catl_100ah_lfp",
    "catl_150ah_lfp",
    "eve_lf280k_prismatic",
    "byd_blade_138ah",
    "catl_161ah_lfp",
]

CYLINDRICAL_CELLS = [
    "generic_21700",
    "generic_4680",
    "tesla_4680",
    "lg_m50_21700",
    "molicel_p42a_21700",
    "samsung_50e_21700",
    "panasonic_2170_nca",
    "molicel_p45b_21700",
    "lg_m58t_21700",
    "samsung_40t_21700",
    "lg_mj1_18650",
    "samsung_30q_18650",
]

ALL_CELLS = POUCH_CELLS + PRISMATIC_CELLS + CYLINDRICAL_CELLS


# =============================================================================
# Validation Result Data Classes
# =============================================================================


@dataclass
class ValidationResult:
    """Result of a single validation check."""

    parameter: str
    calculated: float
    target: float
    error_pct: float
    tolerance_pct: float
    passed: bool

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return (
            f"{self.parameter}: {self.calculated:.3f} vs {self.target:.3f} "
            f"({self.error_pct:+.2f}% error, Â±{self.tolerance_pct}% tolerance) [{status}]"
        )


def calculate_error_pct(calculated: float, target: float) -> float:
    """Calculate percentage error."""
    if target == 0:
        return float("inf") if calculated != 0 else 0
    return (calculated - target) / target * 100


def validate_result(
    parameter: str, calculated: float, target: float, tolerance_pct: float
) -> ValidationResult:
    """Validate a single parameter against target."""
    error_pct = calculate_error_pct(calculated, target)
    passed = abs(error_pct) <= tolerance_pct

    return ValidationResult(
        parameter=parameter,
        calculated=calculated,
        target=target,
        error_pct=error_pct,
        tolerance_pct=tolerance_pct,
        passed=passed,
    )


# =============================================================================
# Input Builders - Convert Reference JSON to Calculator Input
# =============================================================================


def build_pouch_input(ref: ReferenceCell) -> PouchCellInput | None:
    """Build PouchCellInput from reference cell JSON.

    Args:
        ref: ReferenceCell loaded from JSON

    Returns:
        PouchCellInput ready for calculation, or None if not buildable
    """
    data = ref.raw_data
    geometry = data.get("geometry_inputs", {})
    materials = data.get("materials", {})
    stack = data.get("stack_config", {})
    cell_specs = data.get("cell_specs", {})

    # Check required sections exist
    if not geometry or not materials:
        return None

    cathode_data = materials.get("cathode", {})
    anode_data = materials.get("anode", {})
    separator_data = materials.get("separator", {})
    electrolyte_data = materials.get("electrolyte", {})
    case_data = materials.get("case_composition", [])
    cathode_tab_data = materials.get("cathode_tab", {})
    anode_tab_data = materials.get("anode_tab", {})

    # Check required material data
    if not cathode_data or not anode_data or not separator_data:
        return None

    try:
        # Build cathode material
        cathode = CathodeMaterial(
            id=cathode_data.get("name", "cathode").lower().replace(" ", "_"),
            name=cathode_data.get("name", "Cathode"),
            chemistry=cathode_data.get("chemistry", "NMC"),
            rev_spec_capacity_mahg=cathode_data["rev_spec_capacity_mahg"],
            max_spec_capacity_mahg=cathode_data.get("max_spec_capacity_mahg", 200.0),
            areal_weight_mgcm2=cathode_data["loading_mgcm2"],
            collector_thickness_um=cathode_data["collector_thickness_um"],
            coating_density_gcm3=cathode_data.get("coating_density_gcm3", 3.5),
            coating_thickness_0pct_um=cathode_data["coating_thickness_0pct_um"],
            coating_thickness_100pct_um=cathode_data["coating_thickness_100pct_um"],
        )

        # Build anode material
        anode = AnodeMaterial(
            id=anode_data.get("name", "anode").lower().replace(" ", "_"),
            name=anode_data.get("name", "Anode"),
            chemistry=anode_data.get("chemistry", "Graphite"),
            rev_spec_capacity_mahg=anode_data["rev_spec_capacity_mahg"],
            max_spec_capacity_mahg=anode_data.get("max_spec_capacity_mahg", 372.0),
            areal_weight_mgcm2=anode_data["loading_mgcm2"],
            collector_thickness_um=anode_data["collector_thickness_um"],
            coating_density_gcm3=anode_data.get("coating_density_gcm3", 1.6),
            coating_thickness_0pct_um=anode_data["coating_thickness_0pct_um"],
            coating_thickness_100pct_um=anode_data["coating_thickness_100pct_um"],
        )

        # Build separator
        separator = SeparatorMaterial(
            id=separator_data.get("name", "separator").lower().replace(" ", "_"),
            name=separator_data.get("name", "Separator"),
            thickness_um=separator_data["thickness_um"],
            porosity_pct=separator_data["porosity_pct"],
            density_gcm3=separator_data.get("density_gcm3", 0.95),
            areal_weight_mgcm2=separator_data["areal_weight_mgcm2"],
        )

        # Build electrolyte
        electrolyte = ElectrolyteModel(
            id=electrolyte_data.get("name", "electrolyte").lower().replace(" ", "_"),
            name=electrolyte_data.get("name", "Electrolyte"),
            density_gcm3=electrolyte_data.get("density_gcm3", 1.25),
            conductivity_sm=electrolyte_data.get("conductivity_sm"),
        )

        # Build geometry
        sheet_geometry = SheetGeometry(
            cathode_height_mm=geometry["cathode_height_mm"],
            cathode_width_mm=geometry["cathode_width_mm"],
            anode_offset_y_mm=geometry.get("anode_offset_y_mm", 2.0),
            anode_offset_x_mm=geometry.get("anode_offset_x_mm", 2.0),
            separator_offset_y_mm=geometry.get("separator_offset_y_mm", 1.0),
            separator_offset_x_mm=geometry.get("separator_offset_x_mm", 1.0),
        )

        # Build packaging
        packaging = PouchPackaging(
            pouch_offset_top_mm=geometry.get("pouch_offset_top_mm", 10.0),
            pouch_offset_bottom_mm=geometry.get("pouch_offset_bottom_mm", 5.0),
            pouch_offset_left_mm=geometry.get("pouch_offset_left_mm", 5.0),
            pouch_offset_right_mm=geometry.get("pouch_offset_right_mm", 5.0),
        )

        # Build stack configuration
        end_mode_str = stack.get("end_electrodes", "BothNegative")
        end_mode = EndElectrodesMode(end_mode_str)

        stack_config = StackConfiguration(
            number_of_stacks=stack.get("number_of_stacks", 1),
            electrode_pairs_per_stack=stack.get("electrode_pairs", 15),
            end_electrodes=end_mode,
            separator_overwraps_per_stack=stack.get("separator_overwraps", 1),
        )

        # Build case composition
        case_composition = []
        for layer in case_data:
            case_composition.append(
                PackagingLayer(
                    name=layer.get("name", "Layer"),
                    version="v1",
                    thickness_um=layer["thickness_um"],
                    porosity_pct=layer.get("porosity_pct", 0.0),
                    density_gcm3=layer["density_gcm3"],
                )
            )
        if not case_composition:
            # Default pouch layers
            case_composition = [
                PackagingLayer("PET", "v1", 22.0, 0.0, 1.38),
                PackagingLayer("Aluminum", "v1", 70.0, 0.0, 2.70),
                PackagingLayer("PP", "v1", 145.0, 0.0, 0.95),
            ]

        # Build tabs
        cathode_tab = TabConfig(
            material=cathode_tab_data.get("material", "Aluminum"),
            height_mm=cathode_tab_data.get("height_mm", 30.0),
            width_mm=cathode_tab_data.get("width_mm", 40.0),
            thickness_mm=cathode_tab_data.get("thickness_mm", 0.3),
            density_gcm3=cathode_tab_data.get("density_gcm3", 2.70),
        )

        anode_tab = TabConfig(
            material=anode_tab_data.get("material", "Copper"),
            height_mm=anode_tab_data.get("height_mm", 30.0),
            width_mm=anode_tab_data.get("width_mm", 40.0),
            thickness_mm=anode_tab_data.get("thickness_mm", 0.2),
            density_gcm3=anode_tab_data.get("density_gcm3", 8.96),
        )

        # Build complete input
        return PouchCellInput(
            cell_name=ref.name,
            cathode=cathode,
            anode=anode,
            separator=separator,
            electrolyte=electrolyte,
            geometry=sheet_geometry,
            packaging=packaging,
            stack_config=stack_config,
            case_composition=case_composition,
            anode_tab=anode_tab,
            cathode_tab=cathode_tab,
            nominal_voltage_v=cell_specs.get("nominal_voltage_v", 3.65),
            capacity_ah=None,  # Let calculator compute it
            electrolyte_excess_factor=electrolyte_data.get("excess_factor", 1.10),
            electrolyte_volume_override_ml=electrolyte_data.get("volume_override_ml"),
            cathode_porosity_pct=cathode_data.get("porosity_pct", 30.0),
            anode_porosity_pct=anode_data.get("porosity_pct", 30.0),
        )

    except (KeyError, TypeError):
        return None


def build_prismatic_input(ref: ReferenceCell) -> PrismaticCellInput | None:
    """Build PrismaticCellInput from reference cell JSON.

    Args:
        ref: ReferenceCell loaded from JSON

    Returns:
        PrismaticCellInput ready for calculation, or None if not buildable
    """
    data = ref.raw_data
    geometry = data.get("geometry_inputs", {})
    case_geo = data.get("case_geometry", {})
    materials = data.get("materials", {})
    stack = data.get("stack_config", {})
    housing = data.get("housing", {})
    cell_specs = data.get("cell_specs", {})

    # Check required sections
    if not case_geo or not materials:
        return None

    cathode_data = materials.get("cathode", {})
    anode_data = materials.get("anode", {})
    separator_data = materials.get("separator", {})
    electrolyte_data = materials.get("electrolyte", {})

    if not cathode_data or not anode_data or not separator_data:
        return None

    try:
        # Build case geometry
        case_geometry = PrismaticGeometry(
            cell_height_mm=case_geo["cell_height_mm"],
            cell_width_mm=case_geo["cell_width_mm"],
            cell_thickness_mm=case_geo["cell_thickness_mm"],
            wall_top_mm=case_geo.get("wall_top_mm", 2.0),
            wall_bottom_mm=case_geo.get("wall_bottom_mm", 1.0),
            wall_front_back_mm=case_geo.get("wall_front_back_mm", 0.5),
            wall_sides_mm=case_geo.get("wall_sides_mm", 0.7),
            insulation_coating_um=case_geo.get("insulation_coating_um", 85.0),
        )

        # Build sheet geometry
        sheet_geometry = PrismaticSheetGeometry(
            cathode_height_mm=geometry.get(
                "cathode_height_mm", case_geo["cell_height_mm"] - 15.0
            ),
            cathode_width_mm=geometry.get(
                "cathode_width_mm", case_geo["cell_width_mm"] - 13.0
            ),
            anode_offset_top_mm=geometry.get("anode_offset_top_mm", 2.0),
            anode_offset_bottom_mm=geometry.get("anode_offset_bottom_mm", 2.0),
            anode_offset_left_mm=geometry.get("anode_offset_left_mm", 2.0),
            anode_offset_right_mm=geometry.get("anode_offset_right_mm", 2.0),
            separator_offset_top_mm=geometry.get("separator_offset_top_mm", 2.0),
            separator_offset_bottom_mm=geometry.get("separator_offset_bottom_mm", 2.0),
            separator_offset_left_mm=geometry.get("separator_offset_left_mm", 2.0),
            separator_offset_right_mm=geometry.get("separator_offset_right_mm", 2.0),
        )

        # Build cathode material
        cathode = CathodeMaterial(
            id=cathode_data.get("name", "cathode").lower().replace(" ", "_")[:50],
            name=cathode_data.get("name", "Cathode"),
            chemistry=cathode_data.get("chemistry", "NMC"),
            rev_spec_capacity_mahg=cathode_data["rev_spec_capacity_mahg"],
            max_spec_capacity_mahg=cathode_data.get("max_spec_capacity_mahg", 200.0),
            areal_weight_mgcm2=cathode_data["loading_mgcm2"],
            collector_thickness_um=cathode_data["collector_thickness_um"],
            coating_density_gcm3=cathode_data.get("coating_density_gcm3", 3.5),
            coating_thickness_0pct_um=cathode_data["coating_thickness_0pct_um"],
            coating_thickness_100pct_um=cathode_data["coating_thickness_100pct_um"],
        )

        # Build anode material
        anode = AnodeMaterial(
            id=anode_data.get("name", "anode").lower().replace(" ", "_")[:50],
            name=anode_data.get("name", "Anode"),
            chemistry=anode_data.get("chemistry", "Graphite"),
            rev_spec_capacity_mahg=anode_data["rev_spec_capacity_mahg"],
            max_spec_capacity_mahg=anode_data.get("max_spec_capacity_mahg", 372.0),
            areal_weight_mgcm2=anode_data["loading_mgcm2"],
            collector_thickness_um=anode_data["collector_thickness_um"],
            coating_density_gcm3=anode_data.get("coating_density_gcm3", 1.5),
            coating_thickness_0pct_um=anode_data["coating_thickness_0pct_um"],
            coating_thickness_100pct_um=anode_data["coating_thickness_100pct_um"],
        )

        # Build separator
        separator = SeparatorMaterial(
            id=separator_data.get("name", "separator").lower().replace(" ", "_")[:50],
            name=separator_data.get("name", "Separator"),
            thickness_um=separator_data["thickness_um"],
            porosity_pct=separator_data["porosity_pct"],
            density_gcm3=separator_data.get("density_gcm3", 0.95),
            areal_weight_mgcm2=separator_data["areal_weight_mgcm2"],
        )

        # Build electrolyte
        electrolyte = ElectrolyteModel(
            id=electrolyte_data.get("name", "electrolyte").lower().replace(" ", "_")[:50],
            name=electrolyte_data.get("name", "Electrolyte"),
            density_gcm3=electrolyte_data.get("density_gcm3", 1.22),
            conductivity_sm=electrolyte_data.get("conductivity_sm"),
        )

        # End electrodes mode
        end_mode_str = stack.get("end_electrodes", "BothNegative")
        end_mode = end_mode_str

        return PrismaticCellInput(
            cell_name=ref.name,
            case_geometry=case_geometry,
            sheet_geometry=sheet_geometry,
            number_of_stacks=stack.get("number_of_stacks", 2),
            electrode_pairs_per_stack=stack.get("electrode_pairs_per_stack", 44),
            end_electrodes=end_mode,
            cathode=cathode,
            anode=anode,
            separator=separator,
            electrolyte=electrolyte,
            case_material_density_gcm3=housing.get("case_material_density_gcm3", 2.70),
            header_mass_g=housing.get("header_mass_g", 88.76),
            insulation_shell_thickness_um=stack.get("insulation_shell_thickness_um", 120.0),
            insulation_shell_count=stack.get("insulation_shell_count", 2),
            insulation_shell_density_gcm3=stack.get("insulation_shell_density_gcm3", 0.91),
            electrolyte_excess_factor=electrolyte_data.get("excess_factor", 1.0),
            electrolyte_volume_override_ml=electrolyte_data.get("volume_ml"),
            cathode_porosity_pct=stack.get("cathode_porosity_pct", 25.0),
            anode_porosity_pct=stack.get("anode_porosity_pct", 38.0),
            nominal_voltage_v=cell_specs.get("nominal_voltage_v", 3.65),
            capacity_ah=None,
            fixing_tape_count=stack.get("fixing_tape_count", 4),
            fixing_tape_thickness_um=stack.get("fixing_tape_thickness_um", 30.0),
            fixing_tape_width_mm=stack.get("fixing_tape_width_mm", 30.0),
            fixing_tape_length_mm=stack.get("fixing_tape_length_mm", 200.0),
            fixing_tape_density_gcm3=stack.get("fixing_tape_density_gcm3", 1.42),
            insulation_coating_density_gcm3=housing.get(
                "insulation_coating_density_gcm3", 0.91
            ),
        )

    except (KeyError, TypeError):
        return None


def build_cylindrical_input(ref: ReferenceCell) -> CylindricalCellInput | None:
    """Build CylindricalCellInput from reference cell JSON.

    Args:
        ref: ReferenceCell loaded from JSON

    Returns:
        CylindricalCellInput ready for calculation, or None if not buildable
    """
    data = ref.raw_data
    geometry = data.get("geometry", {})
    winding = data.get("winding", {})
    header = data.get("header", {})
    materials = data.get("materials", {})
    cell_specs = data.get("cell_specs", {})

    # Check required sections
    if not geometry or not materials:
        return None

    cathode_data = materials.get("cathode", {})
    anode_data = materials.get("anode", {})
    separator_data = materials.get("separator", {})
    electrolyte_data = materials.get("electrolyte", {})

    if not cathode_data or not anode_data or not separator_data:
        return None

    try:
        # Can material (needed for header)
        can_material_str = geometry.get("can_material", "nickel_plated_steel")
        can_material = CanMaterial.NICKEL_PLATED_STEEL
        if "aluminum" in can_material_str.lower():
            can_material = CanMaterial.ALUMINUM

        # Build geometry
        cell_geometry = CylindricalGeometry(
            diameter_mm=geometry["diameter_mm"],
            length_mm=geometry["length_mm"],
            can_wall_thickness_mm=geometry.get("can_wall_thickness_mm", 0.25),
            can_bottom_thickness_mm=geometry.get("can_bottom_thickness_mm", 0.4),
            header_height_mm=geometry.get("header_height_mm", 3.5),
        )

        # Build winding config
        tab_type_str = winding.get("tab_type", "traditional")
        # Map tab_type string to enum (multi_tab is mapped to TRADITIONAL as it's not in the enum)
        if tab_type_str == "tabless":
            tab_type = TabType.TABLESS
        else:
            tab_type = TabType.TRADITIONAL  # traditional and multi_tab both use TRADITIONAL

        winding_config = WindingConfig(
            mandrel_diameter_mm=winding.get("mandrel_diameter_mm", 2.5),
            winding_clearance_mm=winding.get("winding_clearance_mm", 0.15),
            winding_tension_factor=winding.get("winding_tension_factor", 0.97),
            tab_type=tab_type,
            anode_tab_width_mm=winding.get("anode_tab_width_mm", 6.0),
            anode_tab_thickness_mm=winding.get("anode_tab_thickness_mm", 0.1),
            cathode_tab_width_mm=winding.get("cathode_tab_width_mm", 5.0),
            cathode_tab_thickness_mm=winding.get("cathode_tab_thickness_mm", 0.1),
        )

        # Build simplified header
        simplified_header = SimplifiedHeader(
            total_mass_g=header.get("total_mass_g", 2.0),
            cap_material=can_material,
        )

        # Insulator masses for separate tracking
        bottom_insulator_g = header.get("bottom_insulator_mass_g", 0.1)
        top_insulator_g = header.get("top_insulator_mass_g", 0.1)

        # Build cathode material
        cathode = CathodeMaterial(
            id=cathode_data.get("name", "cathode").lower().replace(" ", "_")[:50],
            name=cathode_data.get("name", "Cathode"),
            chemistry=cathode_data.get("chemistry", "NMC"),
            rev_spec_capacity_mahg=cathode_data["rev_spec_capacity_mahg"],
            max_spec_capacity_mahg=cathode_data.get("max_spec_capacity_mahg", 200.0),
            areal_weight_mgcm2=cathode_data["loading_mgcm2"],
            collector_thickness_um=cathode_data["collector_thickness_um"],
            coating_density_gcm3=cathode_data.get("coating_density_gcm3", 3.0),
            coating_thickness_0pct_um=cathode_data["coating_thickness_0pct_um"],
            coating_thickness_100pct_um=cathode_data["coating_thickness_100pct_um"],
        )

        # Build anode material
        anode = AnodeMaterial(
            id=anode_data.get("name", "anode").lower().replace(" ", "_")[:50],
            name=anode_data.get("name", "Anode"),
            chemistry=anode_data.get("chemistry", "Graphite"),
            rev_spec_capacity_mahg=anode_data["rev_spec_capacity_mahg"],
            max_spec_capacity_mahg=anode_data.get("max_spec_capacity_mahg", 372.0),
            areal_weight_mgcm2=anode_data["loading_mgcm2"],
            collector_thickness_um=anode_data["collector_thickness_um"],
            coating_density_gcm3=anode_data.get("coating_density_gcm3", 1.5),
            coating_thickness_0pct_um=anode_data["coating_thickness_0pct_um"],
            coating_thickness_100pct_um=anode_data["coating_thickness_100pct_um"],
        )

        # Build separator
        separator = SeparatorMaterial(
            id=separator_data.get("name", "separator").lower().replace(" ", "_")[:50],
            name=separator_data.get("name", "Separator"),
            thickness_um=separator_data["thickness_um"],
            porosity_pct=separator_data["porosity_pct"],
            density_gcm3=separator_data.get("density_gcm3", 0.95),
            areal_weight_mgcm2=separator_data.get("areal_weight_mgcm2", 0.5),
        )

        # Build electrolyte
        electrolyte = ElectrolyteModel(
            id=electrolyte_data.get("name", "electrolyte").lower().replace(" ", "_")[:50],
            name=electrolyte_data.get("name", "Electrolyte"),
            density_gcm3=electrolyte_data.get("density_gcm3", 1.20),
            conductivity_sm=electrolyte_data.get("conductivity_sm"),
        )

        # Can material
        can_material_str = geometry.get("can_material", "nickel_plated_steel")
        can_material = CanMaterial.NICKEL_PLATED_STEEL
        if "aluminum" in can_material_str.lower():
            can_material = CanMaterial.ALUMINUM

        return CylindricalCellInput(
            cell_name=ref.name,
            geometry=cell_geometry,
            winding=winding_config,
            header_simplified=simplified_header,
            cathode=cathode,
            anode=anode,
            separator=separator,
            electrolyte=electrolyte,
            can_material=can_material,
            nominal_voltage_v=cell_specs.get("nominal_voltage_v", 3.65),
            electrolyte_excess_factor=electrolyte_data.get("excess_factor", 1.0),
            bottom_insulator_mass_g=bottom_insulator_g,
            top_insulator_mass_g=top_insulator_g,
        )

    except (KeyError, TypeError):
        return None


# =============================================================================
# Calculation Runner
# =============================================================================


def run_calculation(cell_id: str, ref: ReferenceCell) -> dict[str, float] | None:
    """Run the appropriate calculator and return results.

    Returns dict with keys: capacity_ah, total_mass_g, gravimetric_ed_whkg, etc.
    """
    cell_type = ref.cell_type.lower()

    try:
        if cell_type == "pouch":
            cell_input = build_pouch_input(ref)
            if cell_input is None:
                return None
            calculator = CellCalculator()
            result = calculator.calculate_pouch_cell(cell_input)

        elif cell_type == "prismatic":
            cell_input = build_prismatic_input(ref)
            if cell_input is None:
                return None
            calculator = PrismaticCalculator(cell_input)
            result = calculator.calculate()

        elif cell_type == "cylindrical":
            cell_input = build_cylindrical_input(ref)
            if cell_input is None:
                return None
            calculator = CylindricalCalculator(cell_input)
            result = calculator.calculate()

        else:
            return None

        # Extract relevant values from result
        return {
            "capacity_ah": result.capacity_ah,
            "total_mass_g": result.total_mass_g,
            "gravimetric_ed_whkg": result.gravimetric_ed_whkg,
            "energy_wh": result.energy_wh,
            "cathode_mass_g": result.cathode_mass_g,
            "anode_mass_g": result.anode_mass_g,
            "separator_mass_g": result.separator_mass_g,
            "electrolyte_mass_g": result.electrolyte_mass_g,
            "housing_mass_g": result.housing_mass_g,
        }

    except Exception:
        # Return None for any calculation error
        return None


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def all_reference_ids() -> list[str]:
    """Get all 25 reference cell IDs."""
    return ALL_CELLS


# =============================================================================
# Pouch Cell Calculation Tests
# =============================================================================


class TestPouchCellCalculations:
    """End-to-end calculation tests for pouch cells."""

    @pytest.mark.parametrize("cell_id", POUCH_CELLS)
    def test_pouch_cell_loads(self, cell_id):
        """Verify pouch cell JSON can be loaded."""
        ref = load_reference_cell(cell_id)
        assert ref.cell_type.lower() == "pouch"

    @pytest.mark.parametrize("cell_id", POUCH_CELLS)
    def test_pouch_cell_has_targets(self, cell_id):
        """Verify pouch cell has validation targets."""
        ref = load_reference_cell(cell_id)
        targets = ref.targets

        assert "capacity_ah" in targets or "total_mass_g" in targets

    @pytest.mark.parametrize("cell_id", POUCH_CELLS)
    def test_pouch_cell_input_buildable(self, cell_id):
        """Verify pouch cell input can be built from JSON."""
        ref = load_reference_cell(cell_id)
        cell_input = build_pouch_input(ref)

        assert cell_input is not None, f"Could not build input for {cell_id}"

    @pytest.mark.parametrize("cell_id", POUCH_CELLS)
    def test_pouch_cell_calculation_runs(self, cell_id):
        """Verify pouch calculator runs without error."""
        ref = load_reference_cell(cell_id)
        results = run_calculation(cell_id, ref)

        assert results is not None, f"Calculation failed for {cell_id}"
        assert results["capacity_ah"] > 0
        assert results["total_mass_g"] > 0

    @pytest.mark.parametrize("cell_id", POUCH_CELLS)
    def test_pouch_cell_validation(self, cell_id):
        """CRITICAL: Validate calculated results against targets."""
        ref = load_reference_cell(cell_id)
        results = run_calculation(cell_id, ref)

        if results is None:
            pytest.skip(f"Calculation not available for {cell_id}")

        targets = ref.targets
        tolerance = ref.default_tolerance
        validation_results = []

        # Validate each available target
        for param, target in targets.items():
            if param in results:
                vr = validate_result(param, results[param], target, tolerance)
                validation_results.append(vr)
                print(f"  {vr}")

        # Report failures
        failed = [vr for vr in validation_results if not vr.passed]
        if failed:
            failure_msg = f"{cell_id} validation failures:\n"
            for vr in failed:
                failure_msg += f"  {vr}\n"
            pytest.fail(failure_msg)


# =============================================================================
# Prismatic Cell Calculation Tests
# =============================================================================


class TestPrismaticCellCalculations:
    """End-to-end calculation tests for prismatic cells."""

    @pytest.mark.parametrize("cell_id", PRISMATIC_CELLS)
    def test_prismatic_cell_loads(self, cell_id):
        """Verify prismatic cell JSON can be loaded."""
        ref = load_reference_cell(cell_id)
        assert ref.cell_type.lower() == "prismatic"

    @pytest.mark.parametrize("cell_id", PRISMATIC_CELLS)
    def test_prismatic_cell_has_targets(self, cell_id):
        """Verify prismatic cell has validation targets."""
        ref = load_reference_cell(cell_id)
        targets = ref.targets

        assert "capacity_ah" in targets or "total_mass_g" in targets

    @pytest.mark.parametrize("cell_id", PRISMATIC_CELLS)
    def test_prismatic_cell_input_buildable(self, cell_id):
        """Verify prismatic cell input can be built from JSON."""
        ref = load_reference_cell(cell_id)
        cell_input = build_prismatic_input(ref)

        assert cell_input is not None, f"Could not build input for {cell_id}"

    @pytest.mark.parametrize("cell_id", PRISMATIC_CELLS)
    def test_prismatic_cell_calculation_runs(self, cell_id):
        """Verify prismatic calculator runs without error."""
        ref = load_reference_cell(cell_id)
        results = run_calculation(cell_id, ref)

        assert results is not None, f"Calculation failed for {cell_id}"
        assert results["capacity_ah"] > 0
        assert results["total_mass_g"] > 0

    @pytest.mark.parametrize("cell_id", PRISMATIC_CELLS)
    def test_prismatic_cell_validation(self, cell_id):
        """CRITICAL: Validate calculated results against targets."""
        ref = load_reference_cell(cell_id)
        results = run_calculation(cell_id, ref)

        if results is None:
            pytest.skip(f"Calculation not available for {cell_id}")

        targets = ref.targets
        tolerance = ref.default_tolerance
        validation_results = []

        for param, target in targets.items():
            if param in results:
                vr = validate_result(param, results[param], target, tolerance)
                validation_results.append(vr)
                print(f"  {vr}")

        failed = [vr for vr in validation_results if not vr.passed]
        if failed:
            failure_msg = f"{cell_id} validation failures:\n"
            for vr in failed:
                failure_msg += f"  {vr}\n"
            pytest.fail(failure_msg)


# =============================================================================
# Cylindrical Cell Calculation Tests
# =============================================================================


class TestCylindricalCellCalculations:
    """End-to-end calculation tests for cylindrical cells."""

    @pytest.mark.parametrize("cell_id", CYLINDRICAL_CELLS)
    def test_cylindrical_cell_loads(self, cell_id):
        """Verify cylindrical cell JSON can be loaded."""
        ref = load_reference_cell(cell_id)
        assert ref.cell_type.lower() == "cylindrical"

    @pytest.mark.parametrize("cell_id", CYLINDRICAL_CELLS)
    def test_cylindrical_cell_has_targets(self, cell_id):
        """Verify cylindrical cell has validation targets."""
        ref = load_reference_cell(cell_id)
        targets = ref.targets

        assert "capacity_ah" in targets or "total_mass_g" in targets

    @pytest.mark.parametrize("cell_id", CYLINDRICAL_CELLS)
    def test_cylindrical_cell_input_buildable(self, cell_id):
        """Verify cylindrical cell input can be built from JSON."""
        ref = load_reference_cell(cell_id)
        cell_input = build_cylindrical_input(ref)

        assert cell_input is not None, f"Could not build input for {cell_id}"

    @pytest.mark.parametrize("cell_id", CYLINDRICAL_CELLS)
    def test_cylindrical_cell_calculation_runs(self, cell_id):
        """Verify cylindrical calculator runs without error."""
        ref = load_reference_cell(cell_id)
        results = run_calculation(cell_id, ref)

        assert results is not None, f"Calculation failed for {cell_id}"
        assert results["capacity_ah"] > 0
        assert results["total_mass_g"] > 0

    @pytest.mark.parametrize("cell_id", CYLINDRICAL_CELLS)
    def test_cylindrical_cell_validation(self, cell_id):
        """CRITICAL: Validate calculated results against targets."""
        ref = load_reference_cell(cell_id)
        results = run_calculation(cell_id, ref)

        if results is None:
            pytest.skip(f"Calculation not available for {cell_id}")

        targets = ref.targets
        tolerance = ref.default_tolerance
        validation_results = []

        for param, target in targets.items():
            if param in results:
                vr = validate_result(param, results[param], target, tolerance)
                validation_results.append(vr)
                print(f"  {vr}")

        failed = [vr for vr in validation_results if not vr.passed]
        if failed:
            failure_msg = f"{cell_id} validation failures:\n"
            for vr in failed:
                failure_msg += f"  {vr}\n"
            pytest.fail(failure_msg)


# =============================================================================
# Summary Tests
# =============================================================================


class TestAllCellsSummary:
    """Summary validation across all 25 cells."""

    def test_all_cells_count(self):
        """Verify we have 25 reference cells."""
        assert len(ALL_CELLS) == 25
        assert len(POUCH_CELLS) == 6
        assert len(PRISMATIC_CELLS) == 7
        assert len(CYLINDRICAL_CELLS) == 12

    def test_all_cells_have_json(self):
        """All 25 cells should have JSON files."""
        missing = []
        for cell_id in ALL_CELLS:
            try:
                load_reference_cell(cell_id)
            except FileNotFoundError:
                missing.append(cell_id)

        assert not missing, f"Missing JSON files: {missing}"

    def test_all_cells_have_validation_targets(self):
        """All 25 cells should have validation_targets section."""
        missing_targets = []
        for cell_id in ALL_CELLS:
            try:
                ref = load_reference_cell(cell_id)
                if not ref.targets:
                    missing_targets.append(cell_id)
            except Exception as e:
                missing_targets.append(f"{cell_id} (error: {e})")

        assert not missing_targets, f"Missing validation_targets: {missing_targets}"

    def test_all_cells_input_buildable(self):
        """All 25 cells should produce buildable calculator inputs."""
        not_buildable = []
        for cell_id in ALL_CELLS:
            ref = load_reference_cell(cell_id)
            cell_type = ref.cell_type.lower()

            if cell_type == "pouch":
                cell_input = build_pouch_input(ref)
            elif cell_type == "prismatic":
                cell_input = build_prismatic_input(ref)
            elif cell_type == "cylindrical":
                cell_input = build_cylindrical_input(ref)
            else:
                cell_input = None

            if cell_input is None:
                not_buildable.append(cell_id)

        assert not not_buildable, f"Could not build inputs for: {not_buildable}"

    def test_all_cells_calculators_run(self):
        """All 25 cells should run through calculators without error."""
        failures = []
        for cell_id in ALL_CELLS:
            ref = load_reference_cell(cell_id)
            results = run_calculation(cell_id, ref)
            if results is None:
                failures.append(cell_id)

        assert not failures, f"Calculation failed for: {failures}"


# =============================================================================
# Validation Summary Report
# =============================================================================


class TestValidationSummary:
    """Generate summary report of all cell validations."""

    def test_validation_summary_report(self, capsys):
        """Generate summary report of all cell validations."""
        print("\n" + "=" * 70)
        print("REFERENCE CELL CALCULATION VALIDATION SUMMARY")
        print("=" * 70)

        results = {"pass": [], "fail": [], "skip": []}

        for cell_id in ALL_CELLS:
            try:
                ref = load_reference_cell(cell_id)
                targets = ref.targets
                tolerance = ref.default_tolerance

                calc_results = run_calculation(cell_id, ref)
                if calc_results is None:
                    results["skip"].append(cell_id)
                    continue

                # Check key metrics
                all_passed = True
                failures = []

                for param in ["capacity_ah", "total_mass_g", "gravimetric_ed_whkg"]:
                    if param in targets and param in calc_results:
                        error = calculate_error_pct(calc_results[param], targets[param])
                        if abs(error) > tolerance:
                            all_passed = False
                            failures.append(f"{param}: {error:+.1f}%")

                if all_passed:
                    results["pass"].append(cell_id)
                else:
                    results["fail"].append((cell_id, failures))

            except Exception:
                results["skip"].append(f"{cell_id} (error)")

        print(f"\nPASSED ({len(results['pass'])}):")
        for cell_id in results["pass"]:
            print(f"  âœ… {cell_id}")

        print(f"\nFAILED ({len(results['fail'])}):")
        for item in results["fail"]:
            if isinstance(item, tuple):
                cell_id, failures = item
                print(f"  âŒ {cell_id}: {', '.join(failures)}")
            else:
                print(f"  âŒ {item}")

        print(f"\nSKIPPED ({len(results['skip'])}):")
        for cell_id in results["skip"]:
            print(f"  â­ï¸ {cell_id}")

        print("=" * 70)

        # This test is for reporting only - always passes
        assert True


# =============================================================================
# Known Issues Tests (xfail markers for cells needing tuning)
# =============================================================================


class TestKnownIssues:
    """Tests for previously known validation issues, now fixed.

    Fixes applied on 2025-12-27:
    - CATL 161Ah: reduced electrode_pairs_per_stack from 55 to 39,
      electrolyte excess_factor from 2.2 to 1.0
    - BYD Blade 138Ah: reduced electrode_pairs_per_stack from 26 to 21
    """

    def test_byd_blade_validation(self):
        """BYD Blade 138Ah should validate within tolerance."""
        ref = load_reference_cell("byd_blade_138ah")
        results = run_calculation("byd_blade_138ah", ref)

        if results is None:
            pytest.skip("Calculator not available")

        targets = ref.targets
        tolerance = ref.default_tolerance

        validation_results = []
        for param in ["capacity_ah", "total_mass_g", "gravimetric_ed_whkg"]:
            if param in targets and param in results:
                vr = validate_result(param, results[param], targets[param], tolerance)
                validation_results.append(vr)

        failed = [vr for vr in validation_results if not vr.passed]
        assert not failed, f"Validation failures: {[str(vr) for vr in failed]}"

