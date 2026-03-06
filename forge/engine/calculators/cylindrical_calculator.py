"""Cylindrical cell calculator for FORGE engine.

This module provides the main calculation engine for cylindrical battery cells,
handling jelly roll geometry, housing calculations, and energy density metrics.
"""

from dataclasses import dataclass

from forge.engine.calculations.cylindrical_housing import (
    CylindricalHousingResult,
    calculate_cylindrical_housing_mass,
    calculate_tab_or_foil_mass,
)
from forge.engine.calculations.energy import (
    calculate_areal_characteristics,
    calculate_cell_capacity,
    calculate_energy_density,
)
from forge.engine.calculations.mass import (
    calculate_electrolyte_mass,
)
from forge.engine.calculations.winding import (
    calculate_jelly_roll,
    calculate_jelly_roll_pore_volume,
    estimate_jelly_roll_volume,
)
from forge.engine.models.cylindrical import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    CanMaterial,
    CylindricalCellInput,
    CylindricalGeometry,
    HeaderComponents,
    JellyRollResult,
    SimplifiedHeader,
    TabType,
    WindingConfig,
)
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    SeparatorMaterial,
)
from forge.engine.models.results import CellReport


@dataclass
class CylindricalElectrodeMass:
    """Electrode mass breakdown for cylindrical cells.

    Attributes:
        coating_g: Active material coating mass [g]
        collector_g: Current collector foil mass [g]
    """

    coating_g: float
    collector_g: float

    @property
    def total_g(self) -> float:
        """Total electrode mass [g]."""
        return self.coating_g + self.collector_g


def calculate_cylindrical_cathode_mass(
    cathode_area_cm2: float, cathode: CathodeMaterial
) -> CylindricalElectrodeMass:
    """Calculate cathode mass for cylindrical cell.

    Args:
        cathode_area_cm2: Total cathode area (both sides) [cm²]
        cathode: Cathode material properties

    Returns:
        CylindricalElectrodeMass with coating and collector masses
    """
    # Single-side area
    single_side_area = cathode_area_cm2 / 2

    # Coating mass = area × loading
    # loading is mg/cm² per side, area is single side
    coating_mass_g = single_side_area * cathode.areal_weight_mgcm2 * 2 / 1000

    # Collector mass = area × thickness × density
    # Use full cathode length × width for collector
    collector_thickness_cm = cathode.collector_thickness_um / 10000
    collector_mass_g = single_side_area * collector_thickness_cm * DENSITY_ALUMINUM

    return CylindricalElectrodeMass(coating_g=coating_mass_g, collector_g=collector_mass_g)


def calculate_cylindrical_anode_mass(
    anode_area_cm2: float, anode: AnodeMaterial
) -> CylindricalElectrodeMass:
    """Calculate anode mass for cylindrical cell.

    Args:
        anode_area_cm2: Total anode area (both sides) [cm²]
        anode: Anode material properties

    Returns:
        CylindricalElectrodeMass with coating and collector masses
    """
    # Single-side area
    single_side_area = anode_area_cm2 / 2

    # Coating mass = area × loading
    coating_mass_g = single_side_area * anode.areal_weight_mgcm2 * 2 / 1000

    # Collector mass
    collector_thickness_cm = anode.collector_thickness_um / 10000
    collector_mass_g = single_side_area * collector_thickness_cm * DENSITY_COPPER

    return CylindricalElectrodeMass(coating_g=coating_mass_g, collector_g=collector_mass_g)


def calculate_cylindrical_separator_mass(
    separator_area_cm2: float, separator: SeparatorMaterial
) -> float:
    """Calculate separator mass for cylindrical cell.

    Args:
        separator_area_cm2: Total separator area [cm²]
        separator: Separator material properties

    Returns:
        Separator mass [g]
    """
    # For wound cells, there are two separator layers
    # separator_area_cm2 already accounts for both
    return separator_area_cm2 * separator.areal_weight_mgcm2 / 1000


class CylindricalCalculator:
    """Calculator for cylindrical battery cells.

    This class handles all calculations specific to cylindrical cells with
    wound jelly roll electrode assemblies.
    """

    def __init__(self, cell_input: CylindricalCellInput):
        """Initialize calculator with cell input.

        Args:
            cell_input: Complete cylindrical cell specification
        """
        self.input = cell_input
        self._validate_input()

    def _validate_input(self) -> None:
        """Validate input parameters."""
        if self.input.geometry is None:
            raise ValueError("geometry must be provided")
        if self.input.winding is None:
            raise ValueError("winding configuration must be provided")
        if self.input.cathode is None:
            raise ValueError("cathode material must be provided")
        if self.input.anode is None:
            raise ValueError("anode material must be provided")
        if self.input.separator is None:
            raise ValueError("separator material must be provided")
        if self.input.electrolyte is None:
            raise ValueError("electrolyte must be provided")

    def calculate(self) -> CellReport:
        """Run all calculations and return complete cell report.

        Returns:
            CellReport with all calculated KPIs
        """
        # 1. Calculate jelly roll geometry
        jelly_roll = self._calculate_jelly_roll()

        # 2. Calculate electrode masses
        cathode_mass = calculate_cylindrical_cathode_mass(
            cathode_area_cm2=jelly_roll.cathode_area_cm2, cathode=self.input.cathode
        )
        anode_mass = calculate_cylindrical_anode_mass(
            anode_area_cm2=jelly_roll.anode_area_cm2, anode=self.input.anode
        )
        separator_mass_g = calculate_cylindrical_separator_mass(
            separator_area_cm2=jelly_roll.separator_area_cm2, separator=self.input.separator
        )

        # 3. Calculate capacity
        if self.input.capacity_ah is not None:
            capacity_ah = self.input.capacity_ah
        else:
            # Calculate from cathode area and loading
            capacity_ah = self._calculate_capacity(jelly_roll.cathode_area_cm2 / 2)

        # 4. Calculate tab/foil extension mass
        tabs_mass_g = calculate_tab_or_foil_mass(
            winding=self.input.winding,
            electrode_length_m=jelly_roll.electrode_length_m,
            electrode_width_mm=jelly_roll.electrode_width_mm,
            anode_collector_thickness_um=self.input.anode.collector_thickness_um,
            cathode_collector_thickness_um=self.input.cathode.collector_thickness_um,
        )

        # 5. Calculate electrolyte mass
        cathode_pores, anode_pores, separator_pores = calculate_jelly_roll_pore_volume(
            jelly_roll=jelly_roll,
            cathode=self.input.cathode,
            anode=self.input.anode,
            separator=self.input.separator,
            cathode_porosity_pct=self.input.cathode_porosity_pct,
            anode_porosity_pct=self.input.anode_porosity_pct,
        )

        electrolyte_result = calculate_electrolyte_mass(
            pores_anode_ml=anode_pores,
            pores_cathode_ml=cathode_pores,
            pores_separator_ml=separator_pores,
            density_gcm3=self.input.electrolyte.density_gcm3,
            excess_factor=self.input.electrolyte_excess_factor,
            user_override_ml=self.input.electrolyte_volume_override_ml,
        )

        # 6. Calculate housing mass
        housing_result = calculate_cylindrical_housing_mass(
            geometry=self.input.geometry,
            can_material=self.input.can_material,
            header=self.input.header,
            header_simplified=self.input.header_simplified,
            bottom_insulator_mass_g=self.input.bottom_insulator_mass_g,
            top_insulator_mass_g=self.input.top_insulator_mass_g,
            tabs_mass_g=tabs_mass_g,
        )

        # 7. Calculate total mass
        total_mass_g = (
            cathode_mass.total_g
            + anode_mass.total_g
            + separator_mass_g
            + electrolyte_result.mass_g
            + housing_result.total_housing_g
        )

        # 8. Calculate volumes
        volume_cell_cm3 = self.input.geometry.can_volume_cm3
        volume_jelly_roll_cm3 = estimate_jelly_roll_volume(
            jelly_roll=jelly_roll, mandrel_diameter_mm=self.input.winding.mandrel_diameter_mm
        )

        # 9. Calculate energy density
        energy_result = calculate_energy_density(
            capacity_ah=capacity_ah,
            nominal_voltage_v=self.input.nominal_voltage_v,
            cell_mass_g=total_mass_g,
            cell_volume_cm3=volume_cell_cm3,
            stack_volume_cm3=volume_jelly_roll_cm3,
        )

        # 10. Calculate areal characteristics
        areal_result = calculate_areal_characteristics(
            capacity_ah=capacity_ah,
            nominal_voltage_v=self.input.nominal_voltage_v,
            cathode_area_cm2=jelly_roll.cathode_area_cm2 / 2,  # Single-side
            cathode_sheets=1,  # Continuous wound electrode counts as 1
        )

        # 11. Build and return report
        return CellReport(
            cell_name=self.input.cell_name,
            cell_type="Cylindrical",
            cell_height_mm=self.input.geometry.length_mm,  # For cylindrical, height = length
            cell_width_mm=self.input.geometry.diameter_mm,  # width = diameter
            cell_thickness_dry_mm=self.input.geometry.diameter_mm,  # thickness = diameter
            cell_thickness_soc0_mm=self.input.geometry.diameter_mm,
            cell_thickness_soc100_mm=self.input.geometry.diameter_mm,
            volume_cell_cm3=volume_cell_cm3,
            volume_stack_cm3=volume_jelly_roll_cm3,
            cathode_sheets=1,  # Continuous wound
            anode_sheets=1,  # Continuous wound
            separator_sheets=2,  # Two separator layers
            cathode_coating_mass_g=cathode_mass.coating_g,
            cathode_collector_mass_g=cathode_mass.collector_g,
            anode_coating_mass_g=anode_mass.coating_g,
            anode_collector_mass_g=anode_mass.collector_g,
            separator_mass_g=separator_mass_g,
            electrolyte_mass_g=electrolyte_result.mass_g,
            housing_mass_g=housing_result.total_housing_g,
            tabs_mass_g=tabs_mass_g,
            capacity_ah=capacity_ah,
            nominal_voltage_v=self.input.nominal_voltage_v,
            gravimetric_ed_whkg=energy_result.gravimetric_whkg,
            volumetric_ed_cell_whl=energy_result.volumetric_cell_whl,
            volumetric_ed_stack_whl=energy_result.volumetric_stack_whl,
            areal_capacity_mahcm2=areal_result.areal_capacity_mahcm2,
            areal_energy_mwhcm2=areal_result.areal_energy_mwhcm2,
        )

    def _calculate_jelly_roll(self) -> JellyRollResult:
        """Calculate jelly roll properties.

        Returns:
            JellyRollResult with all wound geometry properties
        """
        return calculate_jelly_roll(
            geometry=self.input.geometry,
            winding=self.input.winding,
            cathode=self.input.cathode,
            anode=self.input.anode,
            separator=self.input.separator,
            header_clearance_mm=1.0,  # Typical clearance
            bottom_clearance_mm=0.5,
        )

    def _calculate_capacity(self, cathode_single_side_area_cm2: float) -> float:
        """Calculate cell capacity from cathode area.

        Args:
            cathode_single_side_area_cm2: Single-side cathode area [cm²]

        Returns:
            Capacity [Ah]
        """
        return calculate_cell_capacity(
            cathode_area_cm2=cathode_single_side_area_cm2,
            cathode_sheets=1,  # Single continuous electrode
            loading_mgcm2=self.input.cathode.areal_weight_mgcm2,
            spec_capacity_mahg=self.input.cathode.rev_spec_capacity_mahg,
        )

    def get_jelly_roll_details(self) -> JellyRollResult:
        """Get detailed jelly roll calculation results.

        Returns:
            JellyRollResult with detailed wound geometry
        """
        return self._calculate_jelly_roll()

    def get_housing_details(self) -> CylindricalHousingResult:
        """Get detailed housing mass breakdown.

        Returns:
            CylindricalHousingResult with component masses
        """
        jelly_roll = self._calculate_jelly_roll()

        tabs_mass_g = calculate_tab_or_foil_mass(
            winding=self.input.winding,
            electrode_length_m=jelly_roll.electrode_length_m,
            electrode_width_mm=jelly_roll.electrode_width_mm,
            anode_collector_thickness_um=self.input.anode.collector_thickness_um,
            cathode_collector_thickness_um=self.input.cathode.collector_thickness_um,
        )

        return calculate_cylindrical_housing_mass(
            geometry=self.input.geometry,
            can_material=self.input.can_material,
            header=self.input.header,
            header_simplified=self.input.header_simplified,
            bottom_insulator_mass_g=self.input.bottom_insulator_mass_g,
            top_insulator_mass_g=self.input.top_insulator_mass_g,
            tabs_mass_g=tabs_mass_g,
        )


def create_cylindrical_from_reference(ref_id: str) -> CylindricalCellInput:
    """Create CylindricalCellInput from a reference cell JSON file.

    Args:
        ref_id: Reference cell identifier (e.g., 'lg_m50_21700')

    Returns:
        CylindricalCellInput configured from reference data
    """
    from forge.engine.models.materials import (
        AnodeMaterial,
        CathodeMaterial,
        SeparatorMaterial,
    )
    from forge.engine.validation.result_validation import load_reference_cell

    ref = load_reference_cell(ref_id)
    data = ref.raw_data

    data.get("metadata", {})
    geo = data.get("geometry", {})
    winding_cfg = data.get("winding", {})
    header_cfg = data.get("header", {})
    materials = data.get("materials", {})
    cell_specs = data.get("cell_specs", {})

    # Geometry
    geometry = CylindricalGeometry(
        diameter_mm=geo["diameter_mm"],
        length_mm=geo["length_mm"],
        can_wall_thickness_mm=geo["can_wall_thickness_mm"],
        can_bottom_thickness_mm=geo["can_bottom_thickness_mm"],
        header_height_mm=geo["header_height_mm"],
    )

    # Can material
    can_material_str = geo.get("can_material", "steel").lower()
    if can_material_str == "aluminum":
        can_material = CanMaterial.ALUMINUM
    elif can_material_str == "nickel_plated_steel":
        can_material = CanMaterial.NICKEL_PLATED_STEEL
    else:
        can_material = CanMaterial.STEEL

    # Tab type
    tab_type_str = winding_cfg.get("tab_type", "traditional").lower()
    tab_type = TabType.TABLESS if tab_type_str == "tabless" else TabType.TRADITIONAL

    # Winding configuration
    winding = WindingConfig(
        mandrel_diameter_mm=winding_cfg["mandrel_diameter_mm"],
        winding_clearance_mm=winding_cfg.get("winding_clearance_mm", 0.1),
        winding_tension_factor=winding_cfg.get("winding_tension_factor", 0.97),
        tab_type=tab_type,
        anode_tab_width_mm=winding_cfg.get("anode_tab_width_mm"),
        anode_tab_thickness_mm=winding_cfg.get("anode_tab_thickness_mm"),
        cathode_tab_width_mm=winding_cfg.get("cathode_tab_width_mm"),
        cathode_tab_thickness_mm=winding_cfg.get("cathode_tab_thickness_mm"),
        anode_foil_extension_mm=winding_cfg.get("anode_foil_extension_mm"),
        cathode_foil_extension_mm=winding_cfg.get("cathode_foil_extension_mm"),
    )

    # Header - simplified or detailed
    header_simplified = None
    header = None
    if "total_mass_g" in header_cfg:
        header_simplified = SimplifiedHeader(
            total_mass_g=header_cfg["total_mass_g"], cap_material=can_material
        )
    elif "ptc_mass_g" in header_cfg:
        header = HeaderComponents(
            ptc_diameter_mm=header_cfg.get("ptc_diameter_mm", 8.0),
            ptc_thickness_mm=header_cfg.get("ptc_thickness_mm", 0.8),
            ptc_mass_g=header_cfg["ptc_mass_g"],
            cid_diameter_mm=header_cfg.get("cid_diameter_mm", 10.0),
            cid_thickness_mm=header_cfg.get("cid_thickness_mm", 0.5),
            cid_mass_g=header_cfg.get("cid_mass_g", 0.2),
            vent_diameter_mm=header_cfg.get("vent_diameter_mm", 6.0),
            vent_thickness_mm=header_cfg.get("vent_thickness_mm", 0.3),
            vent_mass_g=header_cfg.get("vent_mass_g", 0.2),
            cap_diameter_mm=header_cfg.get("cap_diameter_mm", geometry.diameter_mm),
            cap_thickness_mm=header_cfg.get("cap_thickness_mm", 0.5),
            cap_material=can_material,
            gasket_mass_g=header_cfg.get("gasket_mass_g", 0.15),
            insulator_ring_mass_g=header_cfg.get("insulator_ring_mass_g", 0.1),
        )
    else:
        # Default simplified header
        header_simplified = SimplifiedHeader(total_mass_g=2.0, cap_material=can_material)

    # Cathode material
    cat_mat = materials.get("cathode", {})
    cathode = CathodeMaterial(
        id=f"CAT_{ref_id.upper()}",
        name=cat_mat.get("name", "Cathode"),
        chemistry=cat_mat.get("chemistry", "NMC"),
        rev_spec_capacity_mahg=cat_mat["rev_spec_capacity_mahg"],
        max_spec_capacity_mahg=cat_mat.get("max_spec_capacity_mahg", 220.0),
        areal_weight_mgcm2=cat_mat["loading_mgcm2"],
        collector_thickness_um=cat_mat["collector_thickness_um"],
        coating_density_gcm3=cat_mat["coating_density_gcm3"],
        coating_thickness_0pct_um=cat_mat["coating_thickness_0pct_um"],
        coating_thickness_100pct_um=cat_mat.get(
            "coating_thickness_100pct_um", cat_mat["coating_thickness_0pct_um"]
        ),
    )

    # Anode material
    ano_mat = materials.get("anode", {})
    anode = AnodeMaterial(
        id=f"ANO_{ref_id.upper()}",
        name=ano_mat.get("name", "Anode"),
        chemistry=ano_mat.get("chemistry", "Graphite"),
        rev_spec_capacity_mahg=ano_mat["rev_spec_capacity_mahg"],
        max_spec_capacity_mahg=ano_mat.get("max_spec_capacity_mahg", 372.0),
        areal_weight_mgcm2=ano_mat["loading_mgcm2"],
        collector_thickness_um=ano_mat["collector_thickness_um"],
        coating_density_gcm3=ano_mat["coating_density_gcm3"],
        coating_thickness_0pct_um=ano_mat["coating_thickness_0pct_um"],
        coating_thickness_100pct_um=ano_mat.get(
            "coating_thickness_100pct_um", ano_mat["coating_thickness_0pct_um"]
        ),
    )

    # Separator material
    sep_mat = materials.get("separator", {})
    separator = SeparatorMaterial(
        id=f"SEP_{ref_id.upper()}",
        name=sep_mat.get("name", "Separator"),
        thickness_um=sep_mat["thickness_um"],
        porosity_pct=sep_mat["porosity_pct"],
        density_gcm3=sep_mat["density_gcm3"],
        areal_weight_mgcm2=sep_mat.get("areal_weight_mgcm2", 1.0),
    )

    # Electrolyte
    ele_mat = materials.get("electrolyte", {})
    electrolyte = ElectrolyteModel(
        id=f"ELE_{ref_id.upper()}",
        name=ele_mat.get("name", "Electrolyte"),
        density_gcm3=ele_mat["density_gcm3"],
    )

    # Build input
    return CylindricalCellInput(
        cell_name=ref.name,
        geometry=geometry,
        winding=winding,
        can_material=can_material,
        cathode=cathode,
        anode=anode,
        separator=separator,
        electrolyte=electrolyte,
        header=header,
        header_simplified=header_simplified,
        capacity_ah=cell_specs.get("capacity_ah"),
        nominal_voltage_v=cell_specs.get("nominal_voltage_v", 3.6),
        electrolyte_excess_factor=ele_mat.get("excess_factor", 1.0),
        cathode_porosity_pct=materials.get("cathode", {}).get("porosity_pct", 25.0),
        anode_porosity_pct=materials.get("anode", {}).get("porosity_pct", 35.0),
        bottom_insulator_mass_g=header_cfg.get("bottom_insulator_mass_g", 0.1),
        top_insulator_mass_g=header_cfg.get("top_insulator_mass_g", 0.1),
    )
