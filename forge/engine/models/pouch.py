"""Pouch cell data models for FORGE engine.

This module defines the PouchCellInput dataclass, extracted from
the original CellCAD cell_calculator.py for consistency with
prismatic/cylindrical models living in models/.
"""

from dataclasses import dataclass

from .geometry import PouchPackaging, SheetGeometry
from .materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
    TabConfig,
)
from .stack import StackConfiguration

# Default excess factor — previously in constants.py, single consumer
DEFAULT_EXCESS_FACTOR = 1.10


@dataclass
class PouchCellInput:
    """Complete input specification for a pouch cell calculation.

    Attributes:
        cell_name: Design name for identification
        cathode: Cathode material properties
        anode: Anode material properties
        separator: Separator material properties
        electrolyte: Electrolyte properties
        geometry: Sheet geometry (cathode dimensions and offsets)
        packaging: Pouch packaging offsets
        stack_config: Stack configuration (pairs, end electrodes, etc.)
        case_composition: List of pouch foil layers
        anode_tab: Anode tab configuration
        cathode_tab: Cathode tab configuration
        nominal_voltage_v: Nominal cell voltage [V]
        capacity_ah: Cell capacity [Ah] (optional - calculated if not provided)
        electrolyte_excess_factor: Electrolyte excess factor (default 1.10)
        electrolyte_volume_override_ml: Optional manual electrolyte volume [ml]
        cathode_porosity_pct: Cathode coating porosity [%] (for electrolyte calc)
        anode_porosity_pct: Anode coating porosity [%] (for electrolyte calc)
    """

    cell_name: str
    cathode: CathodeMaterial
    anode: AnodeMaterial
    separator: SeparatorMaterial
    electrolyte: ElectrolyteModel
    geometry: SheetGeometry
    packaging: PouchPackaging
    stack_config: StackConfiguration
    case_composition: list[PackagingLayer]
    anode_tab: TabConfig
    cathode_tab: TabConfig
    nominal_voltage_v: float
    capacity_ah: float | None = None
    electrolyte_excess_factor: float = DEFAULT_EXCESS_FACTOR
    electrolyte_volume_override_ml: float | None = None
    cathode_porosity_pct: float = 30.0
    anode_porosity_pct: float = 30.0
