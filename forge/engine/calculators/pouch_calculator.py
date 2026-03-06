"""Pouch cell calculator for FORGE engine.

This module provides the main calculation engine that combines all models
and calculation modules to produce a complete pouch cell design analysis.
"""


from forge.engine.calculations.energy import (
    calculate_areal_characteristics,
    calculate_cell_capacity,
    calculate_ecu_metrics,
    calculate_energy_density,
)
from forge.engine.calculations.mass import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    calculate_anode_mass,
    calculate_cathode_mass,
    calculate_electrolyte_mass,
    calculate_pouch_housing_mass,
    calculate_separator_mass,
)
from forge.engine.calculations.stack import (
    calculate_pore_volumes,
    calculate_stack_thickness,
)
from forge.engine.models.materials import (
    COST_ANODE_COATING,
    COST_ANODE_COLLECTOR,
    COST_CATHODE_COATING,
    COST_CATHODE_COLLECTOR,
    COST_ELECTROLYTE,
    COST_HOUSING_POUCH,
    COST_SEPARATOR,
    COST_TAB_ALUMINUM,
    COST_TAB_COPPER,
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    SeparatorMaterial,
    TabConfig,
)
from forge.engine.models.pouch import PouchCellInput
from forge.engine.models.results import BillOfMaterials, CellReport
from forge.engine.models.stack import (
    SwellingParameters,
    ThicknessParameters,
)

# Re-export for backward compatibility
DEFAULT_EXCESS_FACTOR = 1.10


class CellCalculator:
    """Main calculator for battery cells.

    This class orchestrates all calculations to produce a CellReport
    from input specifications.
    """

    def calculate_pouch_cell(self, input: PouchCellInput) -> CellReport:
        """Calculate all properties for a pouch cell.

        Args:
            input: Complete input specification

        Returns:
            CellReport with all calculated KPIs
        """
        # 1. Get sheet counts
        input.stack_config.calculate_sheet_counts()
        total_cathode_sheets = input.stack_config.total_cathode_sheets
        total_anode_sheets = input.stack_config.total_anode_sheets
        total_separator_sheets = input.stack_config.total_separator_sheets

        # 2. Get areas from geometry
        cathode_area = input.geometry.cathode_area_cm2
        anode_area = input.geometry.anode_area_cm2
        separator_area = input.geometry.separator_area_cm2

        # 3. Calculate capacity (if not provided)
        if input.capacity_ah is not None:
            capacity_ah = input.capacity_ah
        else:
            capacity_ah = calculate_cell_capacity(
                cathode_area_cm2=cathode_area,
                cathode_sheets=total_cathode_sheets,
                loading_mgcm2=input.cathode.areal_weight_mgcm2,
                spec_capacity_mahg=input.cathode.rev_spec_capacity_mahg,
            )

        # 4. Calculate masses
        # Get flag areas from geometry (0 if not specified - backward compatible)
        cathode_flag_area = input.geometry.cathode_flag_area_cm2
        anode_flag_area = input.geometry.anode_flag_area_cm2

        cathode_mass = calculate_cathode_mass(
            cathode_area_cm2=cathode_area,
            cathode_sheets=total_cathode_sheets,
            loading_mgcm2=input.cathode.areal_weight_mgcm2,
            collector_thk_um=input.cathode.collector_thickness_um,
            flag_area_cm2=cathode_flag_area,
        )

        anode_mass = calculate_anode_mass(
            anode_area_cm2=anode_area,
            anode_sheets=total_anode_sheets,
            loading_mgcm2=input.anode.areal_weight_mgcm2,
            collector_thk_um=input.anode.collector_thickness_um,
            flag_area_cm2=anode_flag_area,
        )

        separator_mass_g = calculate_separator_mass(
            separator_area_cm2=separator_area,
            separator_sheets=total_separator_sheets,
            areal_weight_mgcm2=input.separator.areal_weight_mgcm2,
        )

        # 5. Calculate pore volumes and electrolyte mass
        cathode_pores, anode_pores, separator_pores = calculate_pore_volumes(
            cathode_area_cm2=cathode_area,
            cathode_sheets=total_cathode_sheets,
            cathode_coating_thk_um=input.cathode.coating_thickness_0pct_um,
            cathode_porosity_pct=input.cathode_porosity_pct,
            anode_area_cm2=anode_area,
            anode_sheets=total_anode_sheets,
            anode_coating_thk_um=input.anode.coating_thickness_0pct_um,
            anode_porosity_pct=input.anode_porosity_pct,
            separator_area_cm2=separator_area,
            separator_sheets=total_separator_sheets,
            separator_thk_um=input.separator.thickness_um,
            separator_porosity_pct=input.separator.porosity_pct,
        )

        electrolyte_result = calculate_electrolyte_mass(
            pores_anode_ml=anode_pores,
            pores_cathode_ml=cathode_pores,
            pores_separator_ml=separator_pores,
            density_gcm3=input.electrolyte.density_gcm3,
            excess_factor=input.electrolyte_excess_factor,
            user_override_ml=input.electrolyte_volume_override_ml,
        )

        # 6. Calculate cell dimensions
        cell_height, cell_width = input.packaging.calculate_cell_dimensions(
            separator_height_mm=input.geometry.separator_height_mm,
            separator_width_mm=input.geometry.separator_width_mm,
        )

        # 7. Calculate housing mass
        housing_mass_g = calculate_pouch_housing_mass(
            cell_height_mm=cell_height,
            cell_width_mm=cell_width,
            case_composition=input.case_composition,
        )

        # 8. Calculate tab masses
        anode_tab_mass = input.anode_tab.mass_g
        cathode_tab_mass = input.cathode_tab.mass_g
        tabs_mass_g = anode_tab_mass + cathode_tab_mass

        # 9. Calculate stack thickness
        thickness_params = ThicknessParameters(
            cathode_collector_thk_um=input.cathode.collector_thickness_um,
            cathode_coating_thk_0pct_um=input.cathode.coating_thickness_0pct_um,
            cathode_coating_thk_100pct_um=input.cathode.coating_thickness_100pct_um,
            anode_collector_thk_um=input.anode.collector_thickness_um,
            anode_coating_thk_0pct_um=input.anode.coating_thickness_0pct_um,
            anode_coating_thk_100pct_um=input.anode.coating_thickness_100pct_um,
            separator_thk_um=input.separator.thickness_um,
        )

        swelling_params = SwellingParameters()  # Use defaults

        stack_thickness = calculate_stack_thickness(
            stack_config=input.stack_config,
            thickness_params=thickness_params,
            swelling_params=swelling_params,
        )

        # 10. Calculate cell thickness (stack + 2x pouch foil thickness)
        pouch_foil_thickness_mm = (
            sum(layer.thickness_um for layer in input.case_composition) / 1000.0 * 2
        )  # Both sides

        cell_thickness_dry = stack_thickness.all_stacks_dry_mm + pouch_foil_thickness_mm
        cell_thickness_soc0 = stack_thickness.all_stacks_soc0_mm + pouch_foil_thickness_mm
        cell_thickness_soc100 = stack_thickness.all_stacks_soc100_mm + pouch_foil_thickness_mm

        # 11. Calculate volumes
        volume_cell_cm3 = cell_height * cell_width * cell_thickness_soc0 / 1000
        volume_stack_cm3 = (
            input.geometry.separator_height_mm
            * input.geometry.separator_width_mm
            * stack_thickness.all_stacks_soc0_mm
            / 1000
        )

        # 12. Calculate total mass
        total_mass_g = (
            cathode_mass.total_g
            + anode_mass.total_g
            + separator_mass_g
            + electrolyte_result.mass_g
            + housing_mass_g
            + tabs_mass_g
        )

        # 13. Calculate energy density
        energy_result = calculate_energy_density(
            capacity_ah=capacity_ah,
            nominal_voltage_v=input.nominal_voltage_v,
            cell_mass_g=total_mass_g,
            cell_volume_cm3=volume_cell_cm3,
            stack_volume_cm3=volume_stack_cm3,
        )

        # 14. Calculate areal characteristics
        areal_result = calculate_areal_characteristics(
            capacity_ah=capacity_ah,
            nominal_voltage_v=input.nominal_voltage_v,
            cathode_area_cm2=cathode_area,
            cathode_sheets=total_cathode_sheets,
        )

        # 15. Calculate ECU (Electrochemical Unit) metrics
        ecu_result = calculate_ecu_metrics(
            cathode_coating_100pct_um=input.cathode.coating_thickness_100pct_um,
            anode_coating_100pct_um=input.anode.coating_thickness_100pct_um,
            cathode_collector_um=input.cathode.collector_thickness_um,
            anode_collector_um=input.anode.collector_thickness_um,
            separator_um=input.separator.thickness_um,
            cathode_area_cm2=cathode_area,
            cathode_sheets_cell=total_cathode_sheets,
            energy_wh=energy_result.cell_energy_wh,
        )

        # Build and return report
        return CellReport(
            cell_name=input.cell_name,
            cell_type="Pouch",
            cell_height_mm=cell_height,
            cell_width_mm=cell_width,
            cell_thickness_dry_mm=cell_thickness_dry,
            cell_thickness_soc0_mm=cell_thickness_soc0,
            cell_thickness_soc100_mm=cell_thickness_soc100,
            volume_cell_cm3=volume_cell_cm3,
            volume_stack_cm3=volume_stack_cm3,
            cathode_sheets=total_cathode_sheets,
            anode_sheets=total_anode_sheets,
            separator_sheets=total_separator_sheets,
            cathode_coating_mass_g=cathode_mass.coating_g,
            cathode_collector_mass_g=cathode_mass.collector_g,
            anode_coating_mass_g=anode_mass.coating_g,
            anode_collector_mass_g=anode_mass.collector_g,
            separator_mass_g=separator_mass_g,
            electrolyte_mass_g=electrolyte_result.mass_g,
            housing_mass_g=housing_mass_g,
            tabs_mass_g=tabs_mass_g,
            capacity_ah=capacity_ah,
            nominal_voltage_v=input.nominal_voltage_v,
            gravimetric_ed_whkg=energy_result.gravimetric_whkg,
            volumetric_ed_cell_whl=energy_result.volumetric_cell_whl,
            volumetric_ed_stack_whl=energy_result.volumetric_stack_whl,
            areal_capacity_mahcm2=areal_result.areal_capacity_mahcm2,
            areal_energy_mwhcm2=areal_result.areal_energy_mwhcm2,
            ecu_thickness_um=ecu_result.ecu_thickness_um,
            ecu_volume_cm3=ecu_result.ecu_volume_cm3,
            ecu_energy_density_wh_l=ecu_result.ecu_energy_density_wh_l,
        )

    def generate_bom(
        self,
        report: CellReport,
        cathode: CathodeMaterial,
        anode: AnodeMaterial,
        separator: SeparatorMaterial,
        electrolyte: ElectrolyteModel,
        anode_tab: TabConfig,
        cathode_tab: TabConfig,
        electrolyte_volume_ml: float,
    ) -> BillOfMaterials:
        """Generate Bill of Materials from a cell report.

        Args:
            report: Calculated cell report
            cathode: Cathode material (for names and densities)
            anode: Anode material (for names and densities)
            separator: Separator material (for names)
            electrolyte: Electrolyte model (for names)
            anode_tab: Anode tab configuration
            cathode_tab: Cathode tab configuration
            electrolyte_volume_ml: Used electrolyte volume [ml]

        Returns:
            BillOfMaterials with all items and calculated percentages
        """
        bom = BillOfMaterials(
            cell_name=report.cell_name,
            cell_type=report.cell_type,
        )

        # 1. Cathode Actives
        cathode_coating_vol = report.cathode_coating_mass_g / cathode.coating_density_gcm3
        bom.add_item(
            type="Cathode Actives",
            name=cathode.name,
            mass_g=report.cathode_coating_mass_g,
            volume_ml=cathode_coating_vol,
            cost_eur=report.cathode_coating_mass_g * COST_CATHODE_COATING,
        )

        # 2. Cathode Collector
        cathode_collector_vol = report.cathode_collector_mass_g / DENSITY_ALUMINUM
        bom.add_item(
            type="Cathode Collector",
            name="Aluminum Foil",
            mass_g=report.cathode_collector_mass_g,
            volume_ml=cathode_collector_vol,
            cost_eur=report.cathode_collector_mass_g * COST_CATHODE_COLLECTOR,
        )

        # 3. Anode Actives
        anode_coating_vol = report.anode_coating_mass_g / anode.coating_density_gcm3
        bom.add_item(
            type="Anode Actives",
            name=anode.name,
            mass_g=report.anode_coating_mass_g,
            volume_ml=anode_coating_vol,
            cost_eur=report.anode_coating_mass_g * COST_ANODE_COATING,
        )

        # 4. Anode Collector
        anode_collector_vol = report.anode_collector_mass_g / DENSITY_COPPER
        bom.add_item(
            type="Anode Collector",
            name="Copper Foil",
            mass_g=report.anode_collector_mass_g,
            volume_ml=anode_collector_vol,
            cost_eur=report.anode_collector_mass_g * COST_ANODE_COLLECTOR,
        )

        # 5. Separator
        separator_vol = report.separator_mass_g / separator.density_gcm3
        bom.add_item(
            type="Separator",
            name=separator.name,
            mass_g=report.separator_mass_g,
            volume_ml=separator_vol,
            cost_eur=report.separator_mass_g * COST_SEPARATOR,
        )

        # 6. Electrolyte
        bom.add_item(
            type="Electrolyte",
            name=electrolyte.name,
            mass_g=report.electrolyte_mass_g,
            volume_ml=electrolyte_volume_ml,
            cost_eur=report.electrolyte_mass_g * COST_ELECTROLYTE,
        )

        # 7. Anode Tab
        bom.add_item(
            type="Anode Tab",
            name=anode_tab.material,
            mass_g=anode_tab.mass_g,
            volume_ml=anode_tab.volume_cm3,
            cost_eur=anode_tab.mass_g * COST_TAB_COPPER,
        )

        # 8. Cathode Tab
        bom.add_item(
            type="Cathode Tab",
            name=cathode_tab.material,
            mass_g=cathode_tab.mass_g,
            volume_ml=cathode_tab.volume_cm3,
            cost_eur=cathode_tab.mass_g * COST_TAB_ALUMINUM,
        )

        # 9. Housing
        # Estimate housing volume from mass and average density
        avg_housing_density = 1.5  # Approximate for Al/PP/PET laminate
        housing_vol = report.housing_mass_g / avg_housing_density
        bom.add_item(
            type="Housing",
            name="Pouch Foil",
            mass_g=report.housing_mass_g,
            volume_ml=housing_vol,
            cost_eur=report.housing_mass_g * COST_HOUSING_POUCH,
        )

        # Calculate percentages
        bom.calculate_percentages()

        return bom


def generate_report_text(report: CellReport) -> str:
    """Generate formatted text report.

    Args:
        report: Calculated cell report

    Returns:
        Formatted text report string
    """
    return f"""
================================================================================
                            CELLCAD REPORT
================================================================================
 Cell Name: {report.cell_name}
 Cell Type: {report.cell_type}
================================================================================
 DIMENSIONS
--------------------------------------------------------------------------------
 Height:              {report.cell_height_mm:>10.2f} mm
 Width:               {report.cell_width_mm:>10.2f} mm
 Thickness (Dry):     {report.cell_thickness_dry_mm:>10.2f} mm
 Thickness (SoC0):    {report.cell_thickness_soc0_mm:>10.2f} mm
 Thickness (SoC100):  {report.cell_thickness_soc100_mm:>10.2f} mm
================================================================================
 VOLUMES
--------------------------------------------------------------------------------
 Cell Volume:         {report.volume_cell_cm3:>10.2f} cm³
 Stack Volume:        {report.volume_stack_cm3:>10.2f} cm³
 Efficiency:          {report.efficiency_stack_pct:>10.1f} %
================================================================================
 SHEET COUNTS
--------------------------------------------------------------------------------
 Cathode Sheets:      {report.cathode_sheets:>10d}
 Anode Sheets:        {report.anode_sheets:>10d}
 Separator Sheets:    {report.separator_sheets:>10d}
================================================================================
 ELECTRICAL
--------------------------------------------------------------------------------
 Capacity:            {report.capacity_ah:>10.3f} Ah
 Nominal Voltage:     {report.nominal_voltage_v:>10.2f} V
 Energy:              {report.energy_wh:>10.2f} Wh
================================================================================
 ENERGY DENSITY
--------------------------------------------------------------------------------
 Gravimetric:         {report.gravimetric_ed_whkg:>10.1f} Wh/kg
 Volumetric (Cell):   {report.volumetric_ed_cell_whl:>10.1f} Wh/L
 Volumetric (Stack):  {report.volumetric_ed_stack_whl:>10.1f} Wh/L
================================================================================
 AREAL CHARACTERISTICS
--------------------------------------------------------------------------------
 Areal Capacity:      {report.areal_capacity_mahcm2:>10.2f} mAh/cm²
 Areal Energy:        {report.areal_energy_mwhcm2:>10.2f} mWh/cm²
================================================================================
 MASS BREAKDOWN
--------------------------------------------------------------------------------
 Cathode (total):     {report.cathode_mass_g:>10.2f} g
   - Coating:         {report.cathode_coating_mass_g:>10.2f} g
   - Collector:       {report.cathode_collector_mass_g:>10.2f} g
 Anode (total):       {report.anode_mass_g:>10.2f} g
   - Coating:         {report.anode_coating_mass_g:>10.2f} g
   - Collector:       {report.anode_collector_mass_g:>10.2f} g
 Separator:           {report.separator_mass_g:>10.2f} g
 Electrolyte:         {report.electrolyte_mass_g:>10.2f} g
 Housing:             {report.housing_mass_g:>10.2f} g
 Tabs:                {report.tabs_mass_g:>10.2f} g
--------------------------------------------------------------------------------
 TOTAL MASS:          {report.total_mass_g:>10.2f} g
================================================================================
 SWELLING
--------------------------------------------------------------------------------
 Formation:           {report.formation_swelling_pct:>10.1f} %
 SoC Breathing:       {report.soc_breathing_pct:>10.1f} %
================================================================================
"""
