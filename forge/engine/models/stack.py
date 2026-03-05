"""Stack configuration data models for FORGE engine.

This module defines dataclasses for electrode stack configuration including:
- EndElectrodesMode: Enum for end electrode configuration
- StackConfiguration: Stack layout and counts
- ThicknessParameters: Material thickness inputs
- SwellingParameters: Swelling factors for SoC calculations
- SheetCounts: Calculated sheet counts per stack
- StackThicknessResult: Calculated thickness at different states
"""

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class EndElectrodesMode(Enum):
    """End electrode configuration for the stack.

    Determines how many cathode vs anode sheets are in the stack.

    BOTH_NEGATIVE: Stack ends with anode on both sides (N cathodes, N+1 anodes)
    BOTH_POSITIVE: Stack ends with cathode on both sides (N+1 cathodes, N anodes)
    POSITIVE_NEGATIVE: Stack ends with one cathode and one anode (N each)
    """

    BOTH_NEGATIVE = "BothNegative"
    BOTH_POSITIVE = "BothPositive"
    POSITIVE_NEGATIVE = "PositiveNegative"


class SheetCounts(NamedTuple):
    """Calculated sheet counts for a single stack.

    Attributes:
        cathode_sheets: Number of cathode sheets per stack
        anode_sheets: Number of anode sheets per stack
        separator_sheets: Number of separator sheets per stack
    """

    cathode_sheets: int
    anode_sheets: int
    separator_sheets: int


@dataclass
class StackConfiguration:
    """Stack configuration parameters.

    Attributes:
        number_of_stacks: Number of stacks in the cell (typically 1-2)
        electrode_pairs_per_stack: Number of anode-cathode pairs per stack
        end_electrodes: End electrode configuration
        separator_overwraps_per_stack: Extra separator wraps per stack
        additional_overwraps_per_stack: Additional foil overwraps per stack
        insulation_shell_count: Insulation shells around all stacks
        fixing_tapes_per_stack: Number of fixing tapes per stack
    """

    number_of_stacks: int
    electrode_pairs_per_stack: int
    end_electrodes: EndElectrodesMode
    separator_overwraps_per_stack: int = 1
    additional_overwraps_per_stack: int = 0
    insulation_shell_count: int = 1
    fixing_tapes_per_stack: int = 1

    def calculate_sheet_counts(self) -> SheetCounts:
        """Calculate sheet counts based on electrode pairs and end configuration.

        Returns:
            SheetCounts with cathode, anode, and separator counts per stack
        """
        n = self.electrode_pairs_per_stack

        if self.end_electrodes == EndElectrodesMode.BOTH_NEGATIVE:
            cathode_sheets = n
            anode_sheets = n + 1
        elif self.end_electrodes == EndElectrodesMode.BOTH_POSITIVE:
            cathode_sheets = n + 1
            anode_sheets = n
        else:  # POSITIVE_NEGATIVE
            cathode_sheets = n
            anode_sheets = n

        # Separator sheets: one between each electrode pair, plus overwraps
        # C# formula: Cathode + Anode + (2 * SeparatorOverwraps) - 1
        separator_sheets = (
            cathode_sheets + anode_sheets + (2 * self.separator_overwraps_per_stack) - 1
        )

        return SheetCounts(cathode_sheets, anode_sheets, separator_sheets)

    @property
    def total_cathode_sheets(self) -> int:
        """Total cathode sheets in all stacks."""
        return self.calculate_sheet_counts().cathode_sheets * self.number_of_stacks

    @property
    def total_anode_sheets(self) -> int:
        """Total anode sheets in all stacks."""
        return self.calculate_sheet_counts().anode_sheets * self.number_of_stacks

    @property
    def total_separator_sheets(self) -> int:
        """Total separator sheets in all stacks."""
        return self.calculate_sheet_counts().separator_sheets * self.number_of_stacks


@dataclass
class ThicknessParameters:
    """Material thickness parameters for stack calculations.

    All thickness values are in micrometers (µm).

    Attributes:
        cathode_collector_thk_um: Cathode current collector thickness [µm]
        cathode_coating_thk_0pct_um: Cathode coating thickness at 0% SoC [µm]
        cathode_coating_thk_100pct_um: Cathode coating thickness at 100% SoC [µm]
        anode_collector_thk_um: Anode current collector thickness [µm]
        anode_coating_thk_0pct_um: Anode coating thickness at 0% SoC [µm]
        anode_coating_thk_100pct_um: Anode coating thickness at 100% SoC [µm]
        separator_thk_um: Separator thickness [µm]
        overwrap_thk_um: Overwrap layer thickness [µm]
        insulation_shell_thk_um: Insulation shell thickness [µm]
        fixing_tape_thk_um: Fixing tape thickness [µm]
    """

    cathode_collector_thk_um: float
    cathode_coating_thk_0pct_um: float
    cathode_coating_thk_100pct_um: float
    anode_collector_thk_um: float
    anode_coating_thk_0pct_um: float
    anode_coating_thk_100pct_um: float
    separator_thk_um: float
    overwrap_thk_um: float = 25.0
    insulation_shell_thk_um: float = 100.0
    fixing_tape_thk_um: float = 50.0

    @property
    def cathode_layer_dry_um(self) -> float:
        """Total cathode layer thickness (collector + double-sided coating) at dry state [µm]."""
        return self.cathode_collector_thk_um + 2 * self.cathode_coating_thk_0pct_um

    @property
    def anode_layer_dry_um(self) -> float:
        """Total anode layer thickness (collector + double-sided coating) at dry state [µm]."""
        return self.anode_collector_thk_um + 2 * self.anode_coating_thk_0pct_um

    @property
    def cathode_layer_100pct_um(self) -> float:
        """Total cathode layer thickness at 100% SoC [µm]."""
        return self.cathode_collector_thk_um + 2 * self.cathode_coating_thk_100pct_um

    @property
    def anode_layer_100pct_um(self) -> float:
        """Total anode layer thickness at 100% SoC [µm]."""
        return self.anode_collector_thk_um + 2 * self.anode_coating_thk_100pct_um


@dataclass
class SwellingParameters:
    """Swelling parameters for thickness calculations at different states.

    Attributes:
        cathode_swelling_factor: Cathode expansion factor at 100% SoC (default 1.02)
        anode_swelling_factor: Anode expansion factor at 100% SoC (default 1.05)
        separator_swelling_factor: Separator expansion factor (default 1.00)
        formation_swelling_pct: Dry to SoC0 expansion percentage (default 2.0%)
    """

    cathode_swelling_factor: float = 1.02
    anode_swelling_factor: float = 1.05
    separator_swelling_factor: float = 1.00
    formation_swelling_pct: float = 2.0


@dataclass
class StackThicknessResult:
    """Calculated stack thickness at different states.

    All thickness values are in millimeters (mm).

    Attributes:
        single_stack_dry_mm: Single stack thickness in dry state [mm]
        single_stack_soc0_mm: Single stack thickness at 0% SoC [mm]
        single_stack_soc100_mm: Single stack thickness at 100% SoC [mm]
        all_stacks_dry_mm: All stacks combined thickness in dry state [mm]
        all_stacks_soc0_mm: All stacks combined thickness at 0% SoC [mm]
        all_stacks_soc100_mm: All stacks combined thickness at 100% SoC [mm]
    """

    single_stack_dry_mm: float
    single_stack_soc0_mm: float
    single_stack_soc100_mm: float
    all_stacks_dry_mm: float
    all_stacks_soc0_mm: float
    all_stacks_soc100_mm: float

    @property
    def formation_swelling_pct(self) -> float:
        """Formation swelling percentage (dry to SoC0) [%]."""
        if self.single_stack_dry_mm == 0:
            return 0.0
        return (
            (self.single_stack_soc0_mm - self.single_stack_dry_mm) / self.single_stack_dry_mm * 100
        )

    @property
    def soc_breathing_pct(self) -> float:
        """SoC breathing percentage (SoC0 to SoC100) [%]."""
        if self.single_stack_soc0_mm == 0:
            return 0.0
        return (
            (self.single_stack_soc100_mm - self.single_stack_soc0_mm)
            / self.single_stack_soc0_mm
            * 100
        )
