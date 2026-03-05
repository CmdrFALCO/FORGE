"""Terminal assembly module.

This module provides terminal assembly calculation for all cell types:
- Pouch: Tab extensions with seal zones
- Prismatic: Bolt-style terminals with insulators
- Cylindrical: Header assembly with button top, vent, and CID

Example:
    >>> from forge.engine.geometry.tabs.terminals import calculate_terminal_assembly
    >>> assembly = calculate_terminal_assembly(detailed_geometry)
    >>> print(assembly.positive_terminal.terminal_type)
"""

from typing import TYPE_CHECKING

from .cylindrical_header import CylindricalHeaderCalculator
from .models import (
    CurrentInterruptDevice,
    HeaderAssembly,
    InsulatorMaterial,
    InsulatorRing,
    PositiveCap,
    SealGasket,
    TerminalAssembly,
    TerminalPost,
    TerminalType,
    VentDisc,
)
from .pouch_terminals import PouchTerminalCalculator
from .prismatic_terminals import PrismaticTerminalCalculator

if TYPE_CHECKING:
    from ...detailed_geometry import DetailedGeometry


def calculate_terminal_assembly(
    geometry: "DetailedGeometry",
    include_insulators: bool = True,
    include_gaskets: bool = True,
    include_cid: bool = True,
) -> TerminalAssembly:
    """Calculate terminal assembly for any cell type.

    Args:
        geometry: DetailedGeometry with cell dimensions
        include_insulators: Include insulator rings
        include_gaskets: Include seal gaskets
        include_cid: Include CID for cylindrical (safety device)

    Returns:
        TerminalAssembly with all components

    Raises:
        ValueError: If cell type is not supported
    """
    cell_type = geometry.cell_type

    if cell_type == "pouch":
        calc = PouchTerminalCalculator(include_seal_zones=include_gaskets)
    elif cell_type == "prismatic":
        calc = PrismaticTerminalCalculator(
            include_insulators=include_insulators,
            include_gaskets=include_gaskets,
        )
    elif cell_type == "cylindrical":
        calc = CylindricalHeaderCalculator(
            include_insulator=include_insulators,
            include_cid=include_cid,
        )
    else:
        raise ValueError(f"Unsupported cell type: {cell_type}")

    return calc.calculate(geometry)


__all__ = [
    # Models
    "TerminalType",
    "InsulatorMaterial",
    "InsulatorRing",
    "SealGasket",
    "TerminalPost",
    "VentDisc",
    "CurrentInterruptDevice",
    "PositiveCap",
    "HeaderAssembly",
    "TerminalAssembly",
    # Calculators
    "PouchTerminalCalculator",
    "PrismaticTerminalCalculator",
    "CylindricalHeaderCalculator",
    # Convenience
    "calculate_terminal_assembly",
]
