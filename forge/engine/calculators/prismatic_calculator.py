"""Prismatic cell calculator for FORGE engine.

This module provides the calculation engine for prismatic battery cells,
handling the specific geometry and housing calculations for hard-case cells.
"""

from dataclasses import dataclass

from forge.engine.models.prismatic import (
    DENSITY_ALUMINUM,
    DENSITY_PP,
    PrismaticCADExport,
    PrismaticCellInput,
    PrismaticGeometry,
    PrismaticSheetGeometry,
)
from forge.engine.models.results import CellReport
from forge.engine.models.stack import (
    EndElectrodesMode,
    StackConfiguration,
    SwellingParameters,
    ThicknessParameters,
)
from forge.engine.calculations.energy import (
    calculate_areal_characteristics,
    calculate_cell_capacity,
    calculate_ecu_metrics,
    calculate_energy_density,
)
from forge.engine.calculations.mass import (
    calculate_anode_mass,
    calculate_cathode_mass,
    calculate_electrolyte_mass,
    calculate_separator_mass,
)
from forge.engine.calculations.stack import (
    calculate_pore_volumes,
    calculate_stack_thickness,
)


@dataclass
class PrismaticHousingResult:
    """Result of prismatic housing mass calculation.

    Attributes:
        case_walls_g: Aluminum case walls mass [g]
        header_g: Header assembly mass (lid + terminals + insulations) [g]
        insulation_coating_g: External insulation coating mass [g]
        insulation_shell_g: Internal insulation shells mass [g]
        fixing_tape_g: Fixing tape mass [g]
        total_housing_g: Total housing mass [g]
    """

    case_walls_g: float
    header_g: float
    insulation_coating_g: float
    insulation_shell_g: float
    fixing_tape_g: float

    @property
    def total_housing_g(self) -> float:
        """Total housing mass [g]."""
        return (
            self.case_walls_g
            + self.header_g
            + self.insulation_coating_g
            + self.insulation_shell_g
            + self.fixing_tape_g
        )


@dataclass
class GapToWallResult:
    """Result of gap-to-wall calculation.

    Attributes:
        gap_dry_mm: Gap in dry state [mm]
        gap_soc0_mm: Gap at 0% SoC [mm]
        gap_soc100_mm: Gap at 100% SoC [mm]
        internal_thickness_mm: Internal cavity thickness [mm]
    """

    gap_dry_mm: float
    gap_soc0_mm: float
    gap_soc100_mm: float
    internal_thickness_mm: float = 0.0

    @property
    def gap_dry_pct(self) -> float:
        """Gap as percentage of internal thickness (dry state)."""
        if self.internal_thickness_mm > 0:
            return self.gap_dry_mm / self.internal_thickness_mm * 100
        return 0.0


@dataclass
class SeparatorCompressionResult:
    """Result of separator compression calculation.

    In prismatic cells with rigid cases, when the stack thickness exceeds
    the internal cavity, the separator is compressed to fit.

    Positive compression = stack is larger than cavity (compression required)
    Negative compression = stack is smaller than cavity (gap exists)

    Attributes:
        compression_dry_pct: Compression in dry state [%]
        compression_soc0_pct: Compression at 0% SoC [%]
        compression_soc100_pct: Compression at 100% SoC [%]

    C# Formula:
        SeparatorCompression_pct = (AllStacksThickness_mm - CellInnerThickness_mm)
                                   / CellInnerThickness_mm * 100.0
    """

    compression_dry_pct: float
    compression_soc0_pct: float
    compression_soc100_pct: float


class PrismaticCalculator:
    """Calculator for prismatic battery cells.

    This class handles all calculations specific to prismatic cells with
    aluminum hard-case housings, including wall-based housing mass and
    gap-to-wall calculations.
    """

    def __init__(self, cell_input: PrismaticCellInput):
        """Initialize calculator with cell input.

        Args:
            cell_input: Complete prismatic cell specification
        """
        self.input = cell_input
        self._validate_input()

    def _validate_input(self) -> None:
        """Validate input parameters."""
        if self.input.case_geometry is None:
            raise ValueError("case_geometry must be provided")
        if self.input.sheet_geometry is None:
            raise ValueError("sheet_geometry must be provided")
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
        # 1. Get sheet geometry
        geo = self.input.sheet_geometry
        cathode_area = geo.cathode_area_cm2
        anode_area = geo.anode_area_cm2
        separator_area = geo.separator_area_cm2

        # 2. Get sheet counts
        total_cathode_sheets = self.input.total_cathode_sheets
        total_anode_sheets = self.input.total_anode_sheets
        total_separator_sheets = self.input.total_separator_sheets

        # 3. Calculate capacity (if not provided)
        if self.input.capacity_ah is not None:
            capacity_ah = self.input.capacity_ah
        else:
            capacity_ah = calculate_cell_capacity(
                cathode_area_cm2=cathode_area,
                cathode_sheets=total_cathode_sheets,
                loading_mgcm2=self.input.cathode.areal_weight_mgcm2,
                spec_capacity_mahg=self.input.cathode.rev_spec_capacity_mahg,
            )

        # 4. Calculate electrode masses
        cathode_mass = calculate_cathode_mass(
            cathode_area_cm2=cathode_area,
            cathode_sheets=total_cathode_sheets,
            loading_mgcm2=self.input.cathode.areal_weight_mgcm2,
            collector_thk_um=self.input.cathode.collector_thickness_um,
        )

        anode_mass = calculate_anode_mass(
            anode_area_cm2=anode_area,
            anode_sheets=total_anode_sheets,
            loading_mgcm2=self.input.anode.areal_weight_mgcm2,
            collector_thk_um=self.input.anode.collector_thickness_um,
        )

        separator_mass_g = calculate_separator_mass(
            separator_area_cm2=separator_area,
            separator_sheets=total_separator_sheets,
            areal_weight_mgcm2=self.input.separator.areal_weight_mgcm2,
        )

        # 5. Calculate pore volumes and electrolyte mass
        cathode_pores, anode_pores, separator_pores = calculate_pore_volumes(
            cathode_area_cm2=cathode_area,
            cathode_sheets=total_cathode_sheets,
            cathode_coating_thk_um=self.input.cathode.coating_thickness_0pct_um,
            cathode_porosity_pct=self.input.cathode_porosity_pct,
            anode_area_cm2=anode_area,
            anode_sheets=total_anode_sheets,
            anode_coating_thk_um=self.input.anode.coating_thickness_0pct_um,
            anode_porosity_pct=self.input.anode_porosity_pct,
            separator_area_cm2=separator_area,
            separator_sheets=total_separator_sheets,
            separator_thk_um=self.input.separator.thickness_um,
            separator_porosity_pct=self.input.separator.porosity_pct,
        )

        electrolyte_result = calculate_electrolyte_mass(
            pores_anode_ml=anode_pores,
            pores_cathode_ml=cathode_pores,
            pores_separator_ml=separator_pores,
            density_gcm3=self.input.electrolyte.density_gcm3,
            excess_factor=self.input.electrolyte_excess_factor,
            user_override_ml=self.input.electrolyte_volume_override_ml,
        )

        # 6. Calculate housing mass (prismatic-specific)
        housing_result = self.calculate_housing_mass()

        # 7. Calculate stack thickness
        stack_thickness = self._calculate_stack_thickness()

        # 8. Get cell dimensions from case geometry
        case_geo = self.input.case_geometry
        cell_height = case_geo.cell_height_mm
        cell_width = case_geo.cell_width_mm

        # For prismatic, thickness is fixed by case
        cell_thickness_dry = case_geo.cell_thickness_mm
        cell_thickness_soc0 = case_geo.cell_thickness_mm
        cell_thickness_soc100 = case_geo.cell_thickness_mm

        # 9. Calculate volumes
        volume_cell_cm3 = case_geo.cell_volume_cm3
        volume_stack_cm3 = self._calculate_stack_volume(stack_thickness.all_stacks_soc0_mm)

        # 10. Calculate total mass
        total_mass_g = (
            cathode_mass.total_g
            + anode_mass.total_g
            + separator_mass_g
            + electrolyte_result.mass_g
            + housing_result.total_housing_g
        )

        # 11. Calculate energy density
        energy_result = calculate_energy_density(
            capacity_ah=capacity_ah,
            nominal_voltage_v=self.input.nominal_voltage_v,
            cell_mass_g=total_mass_g,
            cell_volume_cm3=volume_cell_cm3,
            stack_volume_cm3=volume_stack_cm3,
        )

        # 12. Calculate areal characteristics
        areal_result = calculate_areal_characteristics(
            capacity_ah=capacity_ah,
            nominal_voltage_v=self.input.nominal_voltage_v,
            cathode_area_cm2=cathode_area,
            cathode_sheets=total_cathode_sheets,
        )

        # 13. Calculate ECU (Electrochemical Unit) metrics
        ecu_result = calculate_ecu_metrics(
            cathode_coating_100pct_um=self.input.cathode.coating_thickness_100pct_um,
            anode_coating_100pct_um=self.input.anode.coating_thickness_100pct_um,
            cathode_collector_um=self.input.cathode.collector_thickness_um,
            anode_collector_um=self.input.anode.collector_thickness_um,
            separator_um=self.input.separator.thickness_um,
            cathode_area_cm2=cathode_area,
            cathode_sheets_cell=total_cathode_sheets,
            energy_wh=energy_result.cell_energy_wh,
        )

        # 14. Calculate separator compression (prismatic-specific)
        compression_result = self.calculate_separator_compression()

        # Build and return report
        return CellReport(
            cell_name=self.input.cell_name,
            cell_type="Prismatic",
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
            housing_mass_g=housing_result.total_housing_g,
            tabs_mass_g=0.0,  # Tabs included in header_mass for prismatic
            capacity_ah=capacity_ah,
            nominal_voltage_v=self.input.nominal_voltage_v,
            gravimetric_ed_whkg=energy_result.gravimetric_whkg,
            volumetric_ed_cell_whl=energy_result.volumetric_cell_whl,
            volumetric_ed_stack_whl=energy_result.volumetric_stack_whl,
            areal_capacity_mahcm2=areal_result.areal_capacity_mahcm2,
            areal_energy_mwhcm2=areal_result.areal_energy_mwhcm2,
            ecu_thickness_um=ecu_result.ecu_thickness_um,
            ecu_volume_cm3=ecu_result.ecu_volume_cm3,
            ecu_energy_density_wh_l=ecu_result.ecu_energy_density_wh_l,
            separator_compression_dry_pct=compression_result.compression_dry_pct,
            separator_compression_soc0_pct=compression_result.compression_soc0_pct,
            separator_compression_soc100_pct=compression_result.compression_soc100_pct,
        )

    def calculate_housing_mass(self) -> PrismaticHousingResult:
        """Calculate prismatic case mass from wall volumes.

        The case is modeled as a U-shaped body (bottom + 4 walls) with
        a separate lid (included in header_mass). This matches the
        typical prismatic cell construction.

        Returns:
            PrismaticHousingResult with detailed mass breakdown
        """
        geo = self.input.case_geometry
        rho = self.input.case_material_density_gcm3

        # Convert to cm for volume calculation
        h_cm = geo.cell_height_mm / 10
        w_cm = geo.cell_width_mm / 10
        t_cm = geo.cell_thickness_mm / 10

        t_bot = geo.wall_bottom_mm / 10
        t_fb = geo.wall_front_back_mm / 10  # front/back (YZ plane)
        t_sides = geo.wall_sides_mm / 10  # sides (XZ plane)

        # Case body is a U-shaped shell (bottom + 4 walls, no top)
        # Top lid is separate and included in header_mass

        # Bottom plate: width × thickness × wall_bottom
        mass_bottom = w_cm * t_cm * t_bot * rho

        # Effective inner height for walls (excludes bottom)
        inner_h_cm = h_cm - t_bot

        # Front and back walls (2×): width × inner_height × wall_front_back
        # Use inner width to avoid corner overlap
        inner_w_cm = w_cm - 2 * t_sides
        mass_front_back = 2 * inner_w_cm * inner_h_cm * t_fb * rho

        # Side walls (2×): thickness × inner_height × wall_sides
        mass_sides = 2 * t_cm * inner_h_cm * t_sides * rho

        case_walls_g = mass_bottom + mass_front_back + mass_sides

        # External insulation coating
        coating_mass_g = self._calculate_insulation_coating_mass()

        # Internal insulation shells
        shell_mass_g = self._calculate_insulation_shell_mass()

        # Fixing tape
        fixing_tape_mass_g = self._calculate_fixing_tape_mass()

        return PrismaticHousingResult(
            case_walls_g=case_walls_g,
            header_g=self.input.header_mass_g,
            insulation_coating_g=coating_mass_g,
            insulation_shell_g=shell_mass_g,
            fixing_tape_g=fixing_tape_mass_g,
        )

    def _calculate_insulation_coating_mass(self) -> float:
        """Calculate external insulation coating mass.

        Reference V1: 3.997g, Volume 4.441 cm³

        Returns:
            Insulation coating mass [g]
        """
        geo = self.input.case_geometry
        coating_thk_mm = geo.insulation_coating_um / 1000.0

        # Surface area (all 6 faces, using external dimensions)
        h = geo.cell_height_mm
        w = geo.cell_width_mm
        t = geo.cell_thickness_mm

        # Top and bottom faces
        area_top_bottom = 2 * w * t / 100  # cm²

        # Front and back faces
        area_front_back = 2 * w * h / 100  # cm²

        # Left and right faces
        area_sides = 2 * t * h / 100  # cm²

        total_area_cm2 = area_top_bottom + area_front_back + area_sides

        # Volume of coating: area × thickness
        # coating_thk_mm / 10 converts mm to cm for volume in cm³
        volume_cm3 = total_area_cm2 * coating_thk_mm / 10

        # Reference shows density ~0.9 for PP coating (3.997g / 4.441cm³ = 0.90)
        return volume_cm3 * self.input.insulation_coating_density_gcm3

    def _calculate_insulation_shell_mass(self) -> float:
        """Calculate internal insulation shell mass.

        The insulation shell wraps around the stacks inside the case.
        Reference V1: 12.44g, 13.822 cm³ (density ~0.90 g/cm³)

        Returns:
            Total insulation shell mass [g]
        """
        geo = self.input.sheet_geometry
        shell_thk_mm = self.input.insulation_shell_thickness_um / 1000.0

        # Shell wraps around the combined stack assembly
        # Stack dimensions from separator (approximately equal to internal case)
        stack_h = geo.separator_height_mm  # ~82mm
        stack_w = geo.separator_width_mm  # ~259.7mm

        # Stack thickness (dry) - approximate from electrode thicknesses
        # V1 has ~14mm per stack × 2 = 28mm total dry thickness
        stack_t = 14.0  # mm per stack (approximate)

        # Shell is a rectangular sleeve around each stack
        # Volume = (outer - inner) perimeter × height × thickness
        # Simplified: 2 × (width + thickness) × height × shell_thickness

        # Convert to cm
        h_cm = stack_h / 10
        w_cm = stack_w / 10
        t_cm = stack_t / 10
        shell_cm = shell_thk_mm / 10

        # Volume for a single rectangular shell sleeve
        # Front + back faces: 2 × width × height × shell_thickness
        # Side faces: 2 × stack_thickness × height × shell_thickness
        single_shell_vol = 2 * w_cm * h_cm * shell_cm + 2 * t_cm * h_cm * shell_cm

        # Total for all shells (insulation_shell_count shells, one per stack)
        total_volume_cm3 = single_shell_vol * self.input.insulation_shell_count

        return total_volume_cm3 * self.input.insulation_shell_density_gcm3

    def _calculate_fixing_tape_mass(self) -> float:
        """Calculate fixing tape mass.

        Returns:
            Fixing tape mass [g]
        """
        # Single tape volume
        volume_cm3 = (
            self.input.fixing_tape_width_mm
            * self.input.fixing_tape_length_mm
            * self.input.fixing_tape_thickness_um
            / 1000.0
        ) / 1000.0  # mm³ → cm³

        return volume_cm3 * self.input.fixing_tape_count * self.input.fixing_tape_density_gcm3

    def calculate_gap_to_wall(self, stack_thickness_mm: float = None) -> GapToWallResult:
        """Calculate gap between stack and internal case dimension.

        Args:
            stack_thickness_mm: Total stack thickness [mm] (optional, calculated if not provided)

        Returns:
            GapToWallResult with gaps at different states
        """
        internal_t = self.input.case_geometry.internal_thickness_mm

        # Get stack thicknesses at different states
        stack_result = self._calculate_stack_thickness()

        return GapToWallResult(
            gap_dry_mm=internal_t - stack_result.all_stacks_dry_mm,
            gap_soc0_mm=internal_t - stack_result.all_stacks_soc0_mm,
            gap_soc100_mm=internal_t - stack_result.all_stacks_soc100_mm,
            internal_thickness_mm=internal_t,
        )

    def calculate_separator_compression(self) -> SeparatorCompressionResult:
        """Calculate separator compression percentage at different SoC states.

        In prismatic cells, the rigid case constrains the stack. When the stack
        is thicker than the internal cavity, the separator must compress to fit.

        Formula (from C#):
            Compression% = (Stack - Inner) / Inner × 100
            Positive = compression required
            Negative = gap exists (no compression)

        Returns:
            SeparatorCompressionResult with compression percentages
        """
        internal_t = self.input.case_geometry.internal_thickness_mm
        stack_result = self._calculate_stack_thickness()

        if internal_t > 0:
            compression_dry = (stack_result.all_stacks_dry_mm - internal_t) / internal_t * 100
            compression_soc0 = (stack_result.all_stacks_soc0_mm - internal_t) / internal_t * 100
            compression_soc100 = (stack_result.all_stacks_soc100_mm - internal_t) / internal_t * 100
        else:
            compression_dry = 0.0
            compression_soc0 = 0.0
            compression_soc100 = 0.0

        return SeparatorCompressionResult(
            compression_dry_pct=compression_dry,
            compression_soc0_pct=compression_soc0,
            compression_soc100_pct=compression_soc100,
        )

    def _calculate_stack_thickness(self):
        """Calculate stack thickness at different states.

        Returns:
            StackThicknessResult
        """
        # Convert end_electrodes string to enum
        if self.input.end_electrodes == "BothNegative":
            end_mode = EndElectrodesMode.BOTH_NEGATIVE
        elif self.input.end_electrodes == "BothPositive":
            end_mode = EndElectrodesMode.BOTH_POSITIVE
        else:
            end_mode = EndElectrodesMode.POSITIVE_NEGATIVE

        stack_config = StackConfiguration(
            number_of_stacks=self.input.number_of_stacks,
            electrode_pairs_per_stack=self.input.electrode_pairs_per_stack,
            end_electrodes=end_mode,
            separator_overwraps_per_stack=self.input.separator_overwraps_per_stack,
            additional_overwraps_per_stack=0,
            insulation_shell_count=self.input.insulation_shell_count,
            fixing_tapes_per_stack=self.input.fixing_tape_count // self.input.number_of_stacks,
        )

        thickness_params = ThicknessParameters(
            cathode_collector_thk_um=self.input.cathode.collector_thickness_um,
            cathode_coating_thk_0pct_um=self.input.cathode.coating_thickness_0pct_um,
            cathode_coating_thk_100pct_um=self.input.cathode.coating_thickness_100pct_um,
            anode_collector_thk_um=self.input.anode.collector_thickness_um,
            anode_coating_thk_0pct_um=self.input.anode.coating_thickness_0pct_um,
            anode_coating_thk_100pct_um=self.input.anode.coating_thickness_100pct_um,
            separator_thk_um=self.input.separator.thickness_um,
            insulation_shell_thk_um=self.input.insulation_shell_thickness_um,
            fixing_tape_thk_um=self.input.fixing_tape_thickness_um,
        )

        # V1 specific swelling parameters
        swelling_params = SwellingParameters(
            cathode_swelling_factor=1.0,  # Cathode shrinks slightly at 100% SoC
            anode_swelling_factor=1.08,  # 8% SoC swelling for anode
            separator_swelling_factor=1.0,
            formation_swelling_pct=6.5,  # Combined formation swelling
        )

        return calculate_stack_thickness(
            stack_config=stack_config,
            thickness_params=thickness_params,
            swelling_params=swelling_params,
        )

    def _calculate_stack_volume(self, stack_thickness_mm: float) -> float:
        """Calculate stack volume at given thickness.

        Args:
            stack_thickness_mm: Total stack thickness [mm]

        Returns:
            Stack volume [cm³]
        """
        geo = self.input.sheet_geometry
        return geo.separator_height_mm * geo.separator_width_mm * stack_thickness_mm / 1000.0

    def generate_cad_export(self, report: CellReport) -> PrismaticCADExport:
        """Generate complete CAD geometry data from cell input and calculated report.

        Creates a comprehensive geometry package suitable for 3D CAD generation,
        including all dimensions, positions, and SoC-dependent parameters.

        Args:
            report: The calculated cell report with mass and dimension data

        Returns:
            PrismaticCADExport with all geometry needed for 3D modeling

        Example:
            >>> calc = PrismaticCalculator(cell_input)
            >>> report = calc.calculate()
            >>> cad = calc.generate_cad_export(report)
            >>> # Use cad.positive_terminal_x_mm, cad.wall_top_mm, etc. for CAD generation
        """
        geom = self.input.case_geometry
        cad = self.input.cad_features

        # Get terminal positions (auto-calculate if None)
        terminal_pos = cad.terminals.get_positions(geom.cell_width_mm, geom.cell_thickness_mm)
        vent_pos = cad.vent.get_position(geom.cell_width_mm, geom.cell_thickness_mm)

        # Calculate internal cavity
        cavity_height = geom.internal_height_mm
        cavity_width = geom.internal_width_mm
        cavity_thickness = geom.internal_thickness_mm

        # Stack dimensions (dry state)
        stack_height = (
            report.stack_height_mm if hasattr(report, "stack_height_mm") else cavity_height - 2
        )
        stack_width = (
            report.stack_width_mm if hasattr(report, "stack_width_mm") else cavity_width - 2
        )

        return PrismaticCADExport(
            # Cell envelope
            cell_height_mm=geom.cell_height_mm,
            cell_width_mm=geom.cell_width_mm,
            cell_thickness_mm=geom.cell_thickness_mm,
            # Case geometry
            external_corner_radius_mm=cad.external_corner_radius_mm,
            internal_corner_radius_mm=cad.internal_corner_radius_mm,
            # Wall thicknesses
            wall_top_mm=geom.wall_top_mm,
            wall_bottom_mm=geom.wall_bottom_mm,
            wall_front_mm=geom.wall_front_back_mm,
            wall_back_mm=geom.wall_front_back_mm,
            wall_left_mm=geom.wall_sides_mm,
            wall_right_mm=geom.wall_sides_mm,
            # Internal cavity
            cavity_height_mm=cavity_height,
            cavity_width_mm=cavity_width,
            cavity_thickness_mm=cavity_thickness,
            # Lid
            lid_thickness_mm=cad.lid_thickness_mm,
            lid_corner_radius_mm=cad.lid_corner_radius_mm,
            # Positive terminal (on top lid)
            positive_terminal_x_mm=terminal_pos["positive_x_mm"],
            positive_terminal_y_mm=geom.cell_height_mm,  # Top of cell
            positive_terminal_z_mm=terminal_pos["positive_y_mm"],
            positive_terminal_diameter_mm=cad.terminals.positive_diameter_mm,
            positive_terminal_height_mm=cad.terminals.positive_height_mm,
            # Negative terminal (on top lid)
            negative_terminal_x_mm=terminal_pos["negative_x_mm"],
            negative_terminal_y_mm=geom.cell_height_mm,  # Top of cell
            negative_terminal_z_mm=terminal_pos["negative_y_mm"],
            negative_terminal_diameter_mm=cad.terminals.negative_diameter_mm,
            negative_terminal_height_mm=cad.terminals.negative_height_mm,
            # Vent (on top lid)
            vent_x_mm=vent_pos["x_mm"],
            vent_y_mm=geom.cell_height_mm,  # Top of cell
            vent_z_mm=vent_pos["y_mm"],
            vent_diameter_mm=cad.vent.diameter_mm,
            # Stack geometry
            stack_height_mm=stack_height,
            stack_width_mm=stack_width,
            stack_thickness_dry_mm=report.cell_thickness_dry_mm
            - geom.wall_front_back_mm
            - geom.wall_front_back_mm,
            stack_thickness_soc0_mm=report.cell_thickness_soc0_mm
            - geom.wall_front_back_mm
            - geom.wall_front_back_mm
            if hasattr(report, "cell_thickness_soc0_mm")
            else 0,
            stack_thickness_soc100_mm=report.cell_thickness_soc100_mm
            - geom.wall_front_back_mm
            - geom.wall_front_back_mm
            if hasattr(report, "cell_thickness_soc100_mm")
            else 0,
            stack_count=self.input.number_of_stacks,
            # Gap analysis
            gap_to_wall_dry_mm=report.gap_to_wall_dry_mm
            if hasattr(report, "gap_to_wall_dry_mm")
            else 0,
            gap_to_wall_soc100_mm=report.gap_to_wall_soc100_mm
            if hasattr(report, "gap_to_wall_soc100_mm")
            else 0,
        )


def create_prismatic_from_reference(ref_id: str) -> PrismaticCellInput:
    """Create PrismaticCellInput from a reference cell JSON file.

    Args:
        ref_id: Reference cell identifier (e.g., 'samsung_sdi_94ah')

    Returns:
        PrismaticCellInput configured from reference data
    """
    from forge.engine.models.materials import (
        AnodeMaterial,
        CathodeMaterial,
        ElectrolyteModel,
        SeparatorMaterial,
    )
    from forge.engine.validation.result_validation import load_reference_cell

    ref = load_reference_cell(ref_id)
    data = ref.raw_data

    geo = data.get("geometry_inputs", {})
    case_geo = data.get("case_geometry", {})
    stack_cfg = data.get("stack_config", {})
    housing = data.get("housing", {})
    materials = data.get("materials", {})
    cell_specs = data.get("cell_specs", {})

    # Case geometry
    case_geometry = PrismaticGeometry(
        cell_height_mm=case_geo["cell_height_mm"],
        cell_width_mm=case_geo["cell_width_mm"],
        cell_thickness_mm=case_geo["cell_thickness_mm"],
        wall_top_mm=case_geo["wall_top_mm"],
        wall_bottom_mm=case_geo["wall_bottom_mm"],
        wall_front_back_mm=case_geo["wall_front_back_mm"],
        wall_sides_mm=case_geo["wall_sides_mm"],
        insulation_coating_um=case_geo.get("insulation_coating_um", 85.0),
    )

    # Sheet geometry
    sheet_geometry = PrismaticSheetGeometry(
        cathode_height_mm=geo["cathode_height_mm"],
        cathode_width_mm=geo["cathode_width_mm"],
        anode_offset_top_mm=geo.get("anode_offset_top_mm", 2.0),
        anode_offset_bottom_mm=geo.get("anode_offset_bottom_mm", 2.0),
        anode_offset_left_mm=geo.get("anode_offset_left_mm", 2.0),
        anode_offset_right_mm=geo.get("anode_offset_right_mm", 2.0),
        separator_offset_top_mm=geo.get("separator_offset_top_mm", 2.0),
        separator_offset_bottom_mm=geo.get("separator_offset_bottom_mm", 2.0),
        separator_offset_left_mm=geo.get("separator_offset_left_mm", 2.0),
        separator_offset_right_mm=geo.get("separator_offset_right_mm", 2.0),
    )

    # Cathode material
    cat_mat = materials.get("cathode", {})
    cathode = CathodeMaterial(
        id=f"CAT_{ref_id.upper()}",
        name=cat_mat.get("name", "Cathode"),
        chemistry=cat_mat.get("chemistry", "NCM"),
        rev_spec_capacity_mahg=cat_mat["rev_spec_capacity_mahg"],
        max_spec_capacity_mahg=cat_mat.get("max_spec_capacity_mahg", 200.0),
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

    # Read porosities from reference file or use defaults
    cathode_porosity = stack_cfg.get("cathode_porosity_pct", 25.0)
    anode_porosity = stack_cfg.get("anode_porosity_pct", 35.0)

    return PrismaticCellInput(
        cell_name=ref.name,
        case_geometry=case_geometry,
        sheet_geometry=sheet_geometry,
        number_of_stacks=stack_cfg["number_of_stacks"],
        electrode_pairs_per_stack=stack_cfg["electrode_pairs_per_stack"],
        end_electrodes=stack_cfg.get("end_electrodes", "BothNegative"),
        cathode=cathode,
        anode=anode,
        separator=separator,
        electrolyte=electrolyte,
        case_material_density_gcm3=housing.get("case_material_density_gcm3", DENSITY_ALUMINUM),
        header_mass_g=housing["header_mass_g"],
        insulation_shell_thickness_um=stack_cfg.get("insulation_shell_thickness_um", 120.0),
        insulation_shell_count=stack_cfg.get("insulation_shell_count", 1),
        insulation_shell_density_gcm3=stack_cfg.get("insulation_shell_density_gcm3", DENSITY_PP),
        insulation_coating_density_gcm3=housing.get("insulation_coating_density_gcm3", DENSITY_PP),
        electrolyte_excess_factor=ele_mat.get("excess_factor", 1.0),
        cathode_porosity_pct=cathode_porosity,
        anode_porosity_pct=anode_porosity,
        nominal_voltage_v=cell_specs["nominal_voltage_v"],
        capacity_ah=cell_specs.get("capacity_ah"),
        fixing_tape_count=stack_cfg.get("fixing_tape_count", 4),
        fixing_tape_thickness_um=stack_cfg.get("fixing_tape_thickness_um", 30.0),
        fixing_tape_width_mm=stack_cfg.get("fixing_tape_width_mm", 30.0),
        fixing_tape_length_mm=stack_cfg.get("fixing_tape_length_mm", 200.0),
        fixing_tape_density_gcm3=stack_cfg.get("fixing_tape_density_gcm3", 1.42),
    )


def create_v1_prismatic_input() -> PrismaticCellInput:
    """Create input specification for V1 Prismatic reference cell.

    This function creates a complete input specification matching the
    V1 Prismatic reference data for validation purposes.

    Returns:
        PrismaticCellInput configured for V1 Prismatic
    """
    from forge.engine.models.materials import (
        AnodeMaterial,
        CathodeMaterial,
        ElectrolyteModel,
        SeparatorMaterial,
    )

    # Case geometry - from V1 reference
    case_geometry = PrismaticGeometry(
        cell_height_mm=88.8,
        cell_width_mm=264.6,
        cell_thickness_mm=29.6,
        wall_top_mm=2.0,
        wall_bottom_mm=1.0,
        wall_front_back_mm=0.5,
        wall_sides_mm=0.7,
        insulation_coating_um=85.0,
    )

    # Sheet geometry - from V1 reference
    sheet_geometry = PrismaticSheetGeometry(
        cathode_height_mm=74.0,
        cathode_width_mm=251.7,
        anode_offset_top_mm=2.0,
        anode_offset_bottom_mm=2.0,
        anode_offset_left_mm=2.0,
        anode_offset_right_mm=2.0,
        separator_offset_top_mm=2.0,
        separator_offset_bottom_mm=2.0,
        separator_offset_left_mm=2.0,
        separator_offset_right_mm=2.0,
    )

    # Cathode material - NMC Ni-90.5
    cathode = CathodeMaterial(
        id="CAT_V1_PRISMATIC",
        name="NCM (Ni-90.5)",
        chemistry="NMC",
        rev_spec_capacity_mahg=193.814,
        max_spec_capacity_mahg=210.0,
        areal_weight_mgcm2=19.674,
        collector_thickness_um=12.0,
        coating_density_gcm3=3.378,  # At 0% SoC
        coating_thickness_0pct_um=58.24,  # Single side at 0% SoC
        coating_thickness_100pct_um=57.08,  # Single side at 100% SoC
    )

    # Anode material - Graphite/SiOx blend
    anode = AnodeMaterial(
        id="ANO_V1_PRISMATIC",
        name="Graphite/SiOx Blend",
        chemistry="Graphite_SiOx",
        rev_spec_capacity_mahg=331.161,
        max_spec_capacity_mahg=372.0,
        areal_weight_mgcm2=11.478,
        collector_thickness_um=6.0,
        coating_density_gcm3=1.343,  # At 0% SoC
        coating_thickness_0pct_um=85.47,  # Single side at 0% SoC
        coating_thickness_100pct_um=92.31,  # Single side at 100% SoC
    )

    # Separator
    separator = SeparatorMaterial(
        id="SEP_V1_PRISMATIC",
        name="PP/AlOx Composite",
        thickness_um=13.0,
        porosity_pct=42.646,
        density_gcm3=0.962,
        areal_weight_mgcm2=1.250,
    )

    # Electrolyte
    electrolyte = ElectrolyteModel(
        id="ELE_V1_PRISMATIC",
        name="LiPF6 in EC:EMC",
        density_gcm3=1.223,
    )

    # Header mass breakdown from V1 reference:
    # - Housing Lid: 33.16g
    # - Anode Terminal: 35.00g (Copper)
    # - Cathode Terminal: 15.00g (Aluminum)
    # - Insulations (in header): 5.60g
    header_mass = 33.16 + 35.00 + 15.00 + 5.60  # = 88.76g

    return PrismaticCellInput(
        cell_name="V1 Prismatic",
        case_geometry=case_geometry,
        sheet_geometry=sheet_geometry,
        number_of_stacks=2,
        electrode_pairs_per_stack=44,  # 44 pairs/stack = 88 cathodes, 90 anodes total
        end_electrodes="BothNegative",
        cathode=cathode,
        anode=anode,
        separator=separator,
        electrolyte=electrolyte,
        case_material_density_gcm3=DENSITY_ALUMINUM,
        header_mass_g=header_mass,
        insulation_shell_thickness_um=120.0,
        insulation_shell_count=2,
        insulation_shell_density_gcm3=DENSITY_PP,
        electrolyte_excess_factor=1.0,
        cathode_porosity_pct=25.36,
        anode_porosity_pct=38.01,
        nominal_voltage_v=3.644,
        capacity_ah=120.866,  # From reference
        fixing_tape_count=4,
        fixing_tape_thickness_um=30.0,
        fixing_tape_width_mm=30.0,
        fixing_tape_length_mm=200.0,
        fixing_tape_density_gcm3=1.42,
    )
