"""Stack thickness calculation formulas for FORGE engine.

This module implements stack-related calculations from Section 4.2 of the spec:
- Sheet count calculations based on end electrode configuration
- Stack thickness at different states (Dry, SoC0, SoC100)
"""

from forge.engine.models.stack import (
    EndElectrodesMode,
    SheetCounts,
    StackConfiguration,
    StackThicknessResult,
    SwellingParameters,
    ThicknessParameters,
)


def calculate_sheet_counts(electrode_pairs: int, end_electrodes: EndElectrodesMode) -> SheetCounts:
    """Calculate sheet counts based on electrode pairs and end configuration.

    Args:
        electrode_pairs: Number of anode-cathode pairs
        end_electrodes: End electrode configuration

    Returns:
        SheetCounts with cathode, anode, and separator sheet counts

    Logic:
        - BOTH_NEGATIVE: N cathodes, N+1 anodes (anode on both ends)
        - BOTH_POSITIVE: N+1 cathodes, N anodes (cathode on both ends)
        - POSITIVE_NEGATIVE: N cathodes, N anodes (one of each on ends)
        - Separators: cathode_sheets + anode_sheets + 1
    """
    n = electrode_pairs

    if end_electrodes == EndElectrodesMode.BOTH_NEGATIVE:
        cathode_sheets = n
        anode_sheets = n + 1
    elif end_electrodes == EndElectrodesMode.BOTH_POSITIVE:
        cathode_sheets = n + 1
        anode_sheets = n
    else:  # POSITIVE_NEGATIVE
        cathode_sheets = n
        anode_sheets = n

    # Separator between each electrode plus one at each end
    separator_sheets = cathode_sheets + anode_sheets + 1

    return SheetCounts(cathode_sheets, anode_sheets, separator_sheets)


def calculate_stack_thickness(
    stack_config: StackConfiguration,
    thickness_params: ThicknessParameters,
    swelling_params: SwellingParameters,
) -> StackThicknessResult:
    """Calculate stack thickness at different states.

    Args:
        stack_config: Stack configuration (electrode pairs, end config, etc.)
        thickness_params: Material thickness parameters
        swelling_params: Swelling parameters for state calculations

    Returns:
        StackThicknessResult with thickness at Dry, SoC0, and SoC100 states

    Calculations:
        1. Dry state: Sum of all layer thicknesses (no swelling)
        2. SoC0: Dry × (1 + formation_swelling%)
        3. SoC100: Account for electrode-specific swelling at full charge
    """
    # Get sheet counts for a single stack
    sheet_counts = stack_config.calculate_sheet_counts()

    # Layer thicknesses at dry state [µm]
    cathode_layer_dry_um = thickness_params.cathode_layer_dry_um
    anode_layer_dry_um = thickness_params.anode_layer_dry_um

    # Total overwrap count
    overwrap_count = (
        stack_config.separator_overwraps_per_stack + stack_config.additional_overwraps_per_stack
    )

    # Single stack dry thickness [µm]
    single_stack_dry_um = (
        sheet_counts.cathode_sheets * cathode_layer_dry_um
        + sheet_counts.anode_sheets * anode_layer_dry_um
        + sheet_counts.separator_sheets * thickness_params.separator_thk_um
        + overwrap_count * thickness_params.overwrap_thk_um
        + stack_config.insulation_shell_count * thickness_params.insulation_shell_thk_um
        + stack_config.fixing_tapes_per_stack * thickness_params.fixing_tape_thk_um
    )

    # Convert µm → mm
    single_stack_dry_mm = single_stack_dry_um / 1000.0

    # SoC0 = Dry × (1 + formation_swelling%)
    single_stack_soc0_mm = single_stack_dry_mm * (1 + swelling_params.formation_swelling_pct / 100)

    # SoC100: Calculate with material-specific swelling using 100% SoC coating thickness
    # C# formula: LayerThk_100 × SwellingFactor (uses coating_100pct, NOT coating_0pct)
    # Formation swelling is NOT applied here - it's already in SoC0 transition
    cathode_coating_swollen_um = (
        thickness_params.cathode_coating_thk_100pct_um * swelling_params.cathode_swelling_factor
    )
    anode_coating_swollen_um = (
        thickness_params.anode_coating_thk_100pct_um * swelling_params.anode_swelling_factor
    )

    cathode_layer_100_um = (
        thickness_params.cathode_collector_thk_um + 2 * cathode_coating_swollen_um
    )
    anode_layer_100_um = thickness_params.anode_collector_thk_um + 2 * anode_coating_swollen_um
    separator_100_um = thickness_params.separator_thk_um * swelling_params.separator_swelling_factor

    single_stack_100_um = (
        sheet_counts.cathode_sheets * cathode_layer_100_um
        + sheet_counts.anode_sheets * anode_layer_100_um
        + sheet_counts.separator_sheets * separator_100_um
        + overwrap_count * thickness_params.overwrap_thk_um
        + stack_config.insulation_shell_count * thickness_params.insulation_shell_thk_um
        + stack_config.fixing_tapes_per_stack * thickness_params.fixing_tape_thk_um
    )

    # SoC100 = stack at 100% SoC (no formation swelling - that's already in Dry→SoC0)
    single_stack_soc100_mm = single_stack_100_um / 1000.0

    # Total for all stacks
    n_stacks = stack_config.number_of_stacks

    return StackThicknessResult(
        single_stack_dry_mm=single_stack_dry_mm,
        single_stack_soc0_mm=single_stack_soc0_mm,
        single_stack_soc100_mm=single_stack_soc100_mm,
        all_stacks_dry_mm=single_stack_dry_mm * n_stacks,
        all_stacks_soc0_mm=single_stack_soc0_mm * n_stacks,
        all_stacks_soc100_mm=single_stack_soc100_mm * n_stacks,
    )


def calculate_pore_volumes(
    cathode_area_cm2: float,
    cathode_sheets: int,
    cathode_coating_thk_um: float,
    cathode_porosity_pct: float,
    anode_area_cm2: float,
    anode_sheets: int,
    anode_coating_thk_um: float,
    anode_porosity_pct: float,
    separator_area_cm2: float,
    separator_sheets: int,
    separator_thk_um: float,
    separator_porosity_pct: float,
) -> tuple[float, float, float]:
    """Calculate pore volumes for electrolyte filling.

    Args:
        cathode_area_cm2: Single cathode sheet area [cm²]
        cathode_sheets: Number of cathode sheets
        cathode_coating_thk_um: Cathode coating thickness [µm]
        cathode_porosity_pct: Cathode coating porosity [%]
        anode_area_cm2: Single anode sheet area [cm²]
        anode_sheets: Number of anode sheets
        anode_coating_thk_um: Anode coating thickness [µm]
        anode_porosity_pct: Anode coating porosity [%]
        separator_area_cm2: Single separator sheet area [cm²]
        separator_sheets: Number of separator sheets
        separator_thk_um: Separator thickness [µm]
        separator_porosity_pct: Separator porosity [%]

    Returns:
        Tuple of (cathode_pores_ml, anode_pores_ml, separator_pores_ml)

    Formula:
        pore_volume = area × sheets × thickness × 2 (double-sided) × porosity / 10000 [cm²×µm→ml]
    """
    # Cathode pores (double-sided coating)
    cathode_coating_vol_ml = (
        cathode_area_cm2 * cathode_sheets * cathode_coating_thk_um * 2 / 10000
    )  # cm² × µm / 10000 → ml
    cathode_pores_ml = cathode_coating_vol_ml * (cathode_porosity_pct / 100)

    # Anode pores (double-sided coating)
    anode_coating_vol_ml = anode_area_cm2 * anode_sheets * anode_coating_thk_um * 2 / 10000
    anode_pores_ml = anode_coating_vol_ml * (anode_porosity_pct / 100)

    # Separator pores
    separator_vol_ml = separator_area_cm2 * separator_sheets * separator_thk_um / 10000
    separator_pores_ml = separator_vol_ml * (separator_porosity_pct / 100)

    return cathode_pores_ml, anode_pores_ml, separator_pores_ml
