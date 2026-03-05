"""Detailed terminal assembly models.

This module defines data structures for terminal assemblies in battery cells.
Terminal assemblies include the external terminals, insulators, gaskets,
and header components that connect the internal electrode stack to external
connections.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..models import Point3D, TabMaterial, TabPolarity


class TerminalType(str, Enum):
    """Terminal construction types."""

    POST = "post"  # Simple post (pouch)
    BOLT = "bolt"  # Bolt-style (prismatic)
    BUTTON = "button"  # Button top (cylindrical positive)
    CAN_BOTTOM = "can_bottom"  # Can bottom (cylindrical negative)


class InsulatorMaterial(str, Enum):
    """Insulator materials."""

    PLASTIC = "plastic"  # Generic plastic
    CERAMIC = "ceramic"  # High-temp ceramic
    RUBBER = "rubber"  # Rubber gasket
    PFA = "pfa"  # Perfluoroalkoxy (high-temp)
    PEEK = "peek"  # Polyether ether ketone


@dataclass
class InsulatorRing:
    """Insulating ring/gasket around terminal.

    Attributes:
        position: Center position of the ring
        outer_diameter_mm: Outer diameter
        inner_diameter_mm: Inner diameter (hole)
        thickness_mm: Thickness (height)
        material: Insulator material type
    """

    position: Point3D
    outer_diameter_mm: float
    inner_diameter_mm: float
    thickness_mm: float
    material: InsulatorMaterial = InsulatorMaterial.PLASTIC

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "position": self.position.to_tuple(),
            "outer_diameter_mm": self.outer_diameter_mm,
            "inner_diameter_mm": self.inner_diameter_mm,
            "thickness_mm": self.thickness_mm,
            "material": self.material.value,
        }


@dataclass
class SealGasket:
    """Seal gasket for terminal or header.

    Attributes:
        position: Center position of the gasket
        outer_diameter_mm: Outer diameter (for circular)
        inner_diameter_mm: Inner diameter (for circular)
        width_mm: Width (for rectangular)
        length_mm: Length (for rectangular)
        thickness_mm: Thickness (height)
        material: Gasket material
    """

    position: Point3D
    outer_diameter_mm: float | None = None
    inner_diameter_mm: float | None = None
    width_mm: float | None = None  # For rectangular
    length_mm: float | None = None  # For rectangular
    thickness_mm: float = 1.0
    material: InsulatorMaterial = InsulatorMaterial.RUBBER

    @property
    def is_circular(self) -> bool:
        """Check if gasket is circular."""
        return self.outer_diameter_mm is not None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "position": self.position.to_tuple(),
            "outer_diameter_mm": self.outer_diameter_mm,
            "inner_diameter_mm": self.inner_diameter_mm,
            "width_mm": self.width_mm,
            "length_mm": self.length_mm,
            "thickness_mm": self.thickness_mm,
            "material": self.material.value,
            "is_circular": self.is_circular,
        }


@dataclass
class TerminalPost:
    """External terminal post - enhanced from basic tab models.

    Attributes:
        polarity: Positive or negative polarity
        terminal_type: Type of terminal construction
        position: Center of terminal base
        diameter_mm: Diameter for cylindrical terminals
        width_mm: Width for rectangular terminals
        length_mm: Length for rectangular terminals
        height_mm: Height above cell surface
        thread_diameter_mm: Thread diameter (for bolt-style)
        thread_pitch_mm: Thread pitch (for bolt-style)
        material: Terminal material
        insulator: Associated insulating ring
        gasket: Associated seal gasket
    """

    polarity: TabPolarity
    terminal_type: TerminalType
    position: Point3D

    # Dimensions (use diameter for circular, width/length for rectangular)
    diameter_mm: float | None = None
    width_mm: float | None = None
    length_mm: float | None = None
    height_mm: float = 5.0

    # Threading (for bolt-style)
    thread_diameter_mm: float | None = None
    thread_pitch_mm: float | None = None

    # Material
    material: TabMaterial = TabMaterial.ALUMINUM

    # Associated components
    insulator: InsulatorRing | None = None
    gasket: SealGasket | None = None

    @property
    def is_circular(self) -> bool:
        """Check if terminal is circular."""
        return self.diameter_mm is not None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "polarity": self.polarity.value,
            "terminal_type": self.terminal_type.value,
            "position": self.position.to_tuple(),
            "diameter_mm": self.diameter_mm,
            "width_mm": self.width_mm,
            "length_mm": self.length_mm,
            "height_mm": self.height_mm,
            "thread_diameter_mm": self.thread_diameter_mm,
            "thread_pitch_mm": self.thread_pitch_mm,
            "material": self.material.value,
            "has_insulator": self.insulator is not None,
            "has_gasket": self.gasket is not None,
        }


@dataclass
class VentDisc:
    """Pressure vent disc for cylindrical cells.

    Attributes:
        position: Center position
        diameter_mm: Disc diameter
        thickness_mm: Disc thickness
        burst_pressure_mpa: Pressure at which vent opens
        material: Disc material
    """

    position: Point3D
    diameter_mm: float
    thickness_mm: float = 0.3
    burst_pressure_mpa: float | None = None  # Optional spec
    material: str = "aluminum"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "position": self.position.to_tuple(),
            "diameter_mm": self.diameter_mm,
            "thickness_mm": self.thickness_mm,
            "burst_pressure_mpa": self.burst_pressure_mpa,
            "material": self.material,
        }


@dataclass
class CurrentInterruptDevice:
    """CID - Current Interrupt Device for cylindrical cells.

    A safety device that disconnects internal circuit when pressure
    exceeds safe limits.

    Attributes:
        position: Center position
        diameter_mm: Device diameter
        thickness_mm: Device thickness
        trigger_pressure_mpa: Pressure at which device triggers
        material: Device material
    """

    position: Point3D
    diameter_mm: float
    thickness_mm: float = 0.5
    trigger_pressure_mpa: float | None = None
    material: str = "aluminum"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "position": self.position.to_tuple(),
            "diameter_mm": self.diameter_mm,
            "thickness_mm": self.thickness_mm,
            "trigger_pressure_mpa": self.trigger_pressure_mpa,
            "material": self.material,
        }


@dataclass
class PositiveCap:
    """Positive cap/button for cylindrical cells.

    Attributes:
        position: Center position
        outer_diameter_mm: Cap outer diameter
        inner_diameter_mm: Contact area diameter
        height_mm: Cap height
        material: Cap material
        button_diameter_mm: Button protrusion diameter
        button_height_mm: Button protrusion height
    """

    position: Point3D
    outer_diameter_mm: float
    inner_diameter_mm: float  # Contact area diameter
    height_mm: float
    material: TabMaterial = TabMaterial.NICKEL

    # Button profile
    button_diameter_mm: float | None = None
    button_height_mm: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "position": self.position.to_tuple(),
            "outer_diameter_mm": self.outer_diameter_mm,
            "inner_diameter_mm": self.inner_diameter_mm,
            "height_mm": self.height_mm,
            "material": self.material.value,
            "button_diameter_mm": self.button_diameter_mm,
            "button_height_mm": self.button_height_mm,
        }


@dataclass
class HeaderAssembly:
    """Complete header assembly for cylindrical cells.

    Components (top to bottom):
    1. Positive cap (button top)
    2. Vent disc
    3. CID (Current Interrupt Device)
    4. Insulator ring
    5. Connection to jellyroll

    Attributes:
        cell_diameter_mm: Cell diameter
        cell_height_mm: Cell height
        positive_cap: Positive cap component
        vent_disc: Vent disc component
        cid: CID component
        top_insulator: Top insulator ring
        gasket: Seal gasket
        total_height_mm: Total header height
    """

    cell_diameter_mm: float
    cell_height_mm: float

    # Components
    positive_cap: PositiveCap | None = None
    vent_disc: VentDisc | None = None
    cid: CurrentInterruptDevice | None = None
    top_insulator: InsulatorRing | None = None
    gasket: SealGasket | None = None

    # Overall dimensions
    total_height_mm: float = 5.0

    def get_all_components(self) -> list[tuple[str, Any]]:
        """Get all non-None components.

        Returns:
            List of (name, component) tuples
        """
        components = []
        if self.positive_cap:
            components.append(("positive_cap", self.positive_cap))
        if self.vent_disc:
            components.append(("vent_disc", self.vent_disc))
        if self.cid:
            components.append(("cid", self.cid))
        if self.top_insulator:
            components.append(("insulator", self.top_insulator))
        if self.gasket:
            components.append(("gasket", self.gasket))
        return components

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cell_diameter_mm": self.cell_diameter_mm,
            "cell_height_mm": self.cell_height_mm,
            "total_height_mm": self.total_height_mm,
            "components": [name for name, _ in self.get_all_components()],
            "positive_cap": self.positive_cap.to_dict() if self.positive_cap else None,
            "vent_disc": self.vent_disc.to_dict() if self.vent_disc else None,
            "cid": self.cid.to_dict() if self.cid else None,
            "top_insulator": self.top_insulator.to_dict()
            if self.top_insulator
            else None,
            "gasket": self.gasket.to_dict() if self.gasket else None,
        }


@dataclass
class TerminalAssembly:
    """Complete terminal assembly for a cell.

    Combines terminals, insulators, and gaskets for both polarities.

    Attributes:
        cell_type: Cell form factor
        positive_terminal: Positive terminal post
        negative_terminal: Negative terminal post
        header_assembly: Header assembly (cylindrical cells)
        can_bottom_thickness_mm: Can bottom thickness (cylindrical)
        notes: Additional notes
    """

    cell_type: str

    # Main terminals
    positive_terminal: TerminalPost | None = None
    negative_terminal: TerminalPost | None = None

    # For cylindrical cells
    header_assembly: HeaderAssembly | None = None
    can_bottom_thickness_mm: float = 0.8

    # Metadata
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cell_type": self.cell_type,
            "positive_terminal": self.positive_terminal.to_dict()
            if self.positive_terminal
            else None,
            "negative_terminal": self.negative_terminal.to_dict()
            if self.negative_terminal
            else None,
            "header_assembly": self.header_assembly.to_dict()
            if self.header_assembly
            else None,
            "can_bottom_thickness_mm": self.can_bottom_thickness_mm,
            "notes": self.notes,
        }
