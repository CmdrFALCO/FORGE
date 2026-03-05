"""Tab geometry calculation module.

This module provides calculators for electrode tab routing geometry
in battery cells. Tabs are the metallic conductors that connect
electrode layers to external terminals for current collection.

Supported cell types:
- Pouch: Tab strips on opposite edges
- Prismatic: Tabs with internal busbars and top terminals
- Cylindrical: Traditional tabbed or tabless (4680-style)

Example:
    >>> from forge.engine.geometry.tabs import calculate_tab_geometry
    >>> tab_geom = calculate_tab_geometry(detailed_geometry)
    >>> print(tab_geom.total_tab_count)

Terminal assemblies are also supported:
    >>> from forge.engine.geometry.tabs import calculate_terminal_assembly
    >>> terminal = calculate_terminal_assembly(detailed_geometry)
    >>> print(terminal.positive_terminal.terminal_type)
"""

from typing import TYPE_CHECKING

from .cylindrical_tabs import CylindricalTabCalculator
from .models import (
    DEFAULT_TAB_DIMENSIONS,
    Busbar,
    Point3D,
    TabGeometry,
    TabMaterial,
    TabPolarity,
    TabStrip,
    TerminalPost,
)
from .pouch_tabs import PouchTabCalculator
from .prismatic_tabs import PrismaticTabCalculator

# Terminal assembly exports
from .terminals import (
    CurrentInterruptDevice,
    CylindricalHeaderCalculator,
    HeaderAssembly,
    InsulatorMaterial,
    InsulatorRing,
    PositiveCap,
    PouchTerminalCalculator,
    PrismaticTerminalCalculator,
    SealGasket,
    TerminalAssembly,
    TerminalType,
    VentDisc,
    calculate_terminal_assembly,
)


if TYPE_CHECKING:
    from ..detailed_geometry import DetailedGeometry


def calculate_tab_geometry(
    geometry: "DetailedGeometry",
    configuration: str | None = None,
    tabs_per_polarity: int | None = None,
) -> TabGeometry:
    """Calculate tab geometry for any cell type.

    This is the main entry point for tab geometry calculation. It
    automatically selects the appropriate calculator based on cell type.

    Args:
        geometry: DetailedGeometry with cell dimensions
        configuration: Override default configuration:
            - Pouch: "standard", "same_side", "staggered"
            - Prismatic: "top_terminal", "side_terminal"
            - Cylindrical: "tabless", "traditional"
        tabs_per_polarity: Override default tab count (pouch/prismatic only)

    Returns:
        TabGeometry with calculated positions

    Raises:
        ValueError: If cell type is not supported

    Example:
        >>> tab_geom = calculate_tab_geometry(geometry, configuration="staggered")
        >>> for tab in tab_geom.positive_tabs:
        ...     print(f"Tab at {tab.attachment_point.to_tuple()}")
    """
    cell_type = geometry.cell_type

    if cell_type == "pouch":
        calc = PouchTabCalculator(
            tabs_per_polarity=tabs_per_polarity or 2,
            configuration=configuration or "standard",
        )
    elif cell_type == "prismatic":
        calc = PrismaticTabCalculator(
            tabs_per_polarity=tabs_per_polarity or 4,
            configuration=configuration or "top_terminal",
        )
    elif cell_type == "cylindrical":
        calc = CylindricalTabCalculator(
            configuration=configuration or "tabless",
        )
    else:
        raise ValueError(f"Unsupported cell type: {cell_type}")

    return calc.calculate(geometry)


__all__ = [
    # Tab models
    "TabPolarity",
    "TabMaterial",
    "Point3D",
    "TabStrip",
    "Busbar",
    "TerminalPost",
    "TabGeometry",
    "DEFAULT_TAB_DIMENSIONS",
    # Tab calculators
    "PouchTabCalculator",
    "PrismaticTabCalculator",
    "CylindricalTabCalculator",
    # Tab convenience
    "calculate_tab_geometry",
    # Terminal models
    "TerminalType",
    "InsulatorMaterial",
    "InsulatorRing",
    "SealGasket",
    "VentDisc",
    "CurrentInterruptDevice",
    "PositiveCap",
    "HeaderAssembly",
    "TerminalAssembly",
    # Terminal calculators
    "PouchTerminalCalculator",
    "PrismaticTerminalCalculator",
    "CylindricalHeaderCalculator",
    # Terminal convenience
    "calculate_terminal_assembly",
]
