"""Tab geometry data models.

This module defines data structures for electrode tab routing in battery cells.
Tabs are the metallic conductors that connect electrode layers to external
terminals for current collection.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TabPolarity(str, Enum):
    """Tab polarity."""

    POSITIVE = "positive"  # Cathode side (Al)
    NEGATIVE = "negative"  # Anode side (Cu/Ni)


class TabMaterial(str, Enum):
    """Tab material types."""

    ALUMINUM = "aluminum"  # Cathode tabs
    COPPER = "copper"  # Anode tabs (raw)
    NICKEL_PLATED_COPPER = "ni_cu"  # Anode tabs (plated, common)
    NICKEL = "nickel"  # Some anode tabs


@dataclass
class Point3D:
    """3D point in mm."""

    x: float
    y: float
    z: float

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)

    def __add__(self, other: "Point3D") -> "Point3D":
        """Add two points."""
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)


@dataclass
class TabStrip:
    """Single tab strip connecting to electrode stack.

    A tab strip is a rectangular conductor that connects multiple
    electrode layers to collect current.

    Attributes:
        polarity: Positive or negative polarity
        material: Tab material (aluminum, copper, etc.)
        attachment_point: Center of attachment area to electrode stack
        attachment_width_mm: Width along electrode edge
        attachment_height_mm: Height (covers multiple layers)
        strip_width_mm: Width of the tab strip itself
        strip_thickness_mm: Thickness (typically 0.1-0.3 mm)
        strip_length_mm: Length from attachment to fold/terminal
        exit_direction: Direction tab exits: "x+", "x-", "y+", "y-", "z+"
        connects_to: Connection target: "terminal", "busbar", or another tab ID
    """

    polarity: TabPolarity
    material: TabMaterial

    # Attachment to electrode stack
    attachment_point: Point3D
    attachment_width_mm: float
    attachment_height_mm: float

    # Tab strip dimensions
    strip_width_mm: float
    strip_thickness_mm: float
    strip_length_mm: float

    # Routing
    exit_direction: str = "x+"

    # Optional: connection to other tabs or terminal
    connects_to: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "polarity": self.polarity.value,
            "material": self.material.value,
            "attachment_point": self.attachment_point.to_tuple(),
            "attachment_width_mm": self.attachment_width_mm,
            "attachment_height_mm": self.attachment_height_mm,
            "strip_width_mm": self.strip_width_mm,
            "strip_thickness_mm": self.strip_thickness_mm,
            "strip_length_mm": self.strip_length_mm,
            "exit_direction": self.exit_direction,
            "connects_to": self.connects_to,
        }


@dataclass
class Busbar:
    """Internal busbar connecting multiple tab strips.

    Used in prismatic cells to collect current from multiple tabs
    and route to the terminal post.

    Attributes:
        polarity: Positive or negative polarity
        material: Busbar material
        start_point: Start position of busbar
        end_point: End position of busbar
        width_mm: Busbar width
        thickness_mm: Busbar thickness
        tab_connection_points: Connection points for tab strips
    """

    polarity: TabPolarity
    material: TabMaterial

    # Busbar dimensions
    start_point: Point3D
    end_point: Point3D
    width_mm: float
    thickness_mm: float

    # Connection points for tab strips
    tab_connection_points: list[Point3D] = field(default_factory=list)

    def length_mm(self) -> float:
        """Calculate busbar length."""
        dx = self.end_point.x - self.start_point.x
        dy = self.end_point.y - self.start_point.y
        dz = self.end_point.z - self.start_point.z
        return (dx**2 + dy**2 + dz**2) ** 0.5

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "polarity": self.polarity.value,
            "material": self.material.value,
            "start_point": self.start_point.to_tuple(),
            "end_point": self.end_point.to_tuple(),
            "width_mm": self.width_mm,
            "thickness_mm": self.thickness_mm,
            "length_mm": self.length_mm(),
            "tab_connection_points": [p.to_tuple() for p in self.tab_connection_points],
        }


@dataclass
class TerminalPost:
    """External terminal post for cell connection.

    The final connection point for tabs/busbars.

    Attributes:
        polarity: Positive or negative polarity
        position: Center of terminal
        diameter_mm: Diameter for cylindrical terminals
        width_mm: Width for rectangular terminals
        length_mm: Length for rectangular terminals
        height_mm: Height above cell surface
        material: Terminal material
    """

    polarity: TabPolarity

    # Position (center of terminal)
    position: Point3D

    # Terminal dimensions
    diameter_mm: float | None = None
    width_mm: float | None = None
    length_mm: float | None = None
    height_mm: float = 5.0

    # Material
    material: TabMaterial = TabMaterial.ALUMINUM

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "polarity": self.polarity.value,
            "position": self.position.to_tuple(),
            "diameter_mm": self.diameter_mm,
            "width_mm": self.width_mm,
            "length_mm": self.length_mm,
            "height_mm": self.height_mm,
            "material": self.material.value,
        }


@dataclass
class TabGeometry:
    """Complete tab routing geometry for a cell.

    Contains all tab strips, busbars, and terminal connections
    for both polarities.

    Attributes:
        cell_type: Cell form factor (pouch, prismatic, cylindrical)
        positive_tabs: List of positive tab strips
        negative_tabs: List of negative tab strips
        positive_busbar: Internal busbar for positive current collection
        negative_busbar: Internal busbar for negative current collection
        positive_terminal: External positive terminal
        negative_terminal: External negative terminal
        configuration: Tab configuration (standard, tabless, multi-tab)
        notes: Additional notes about the geometry
    """

    cell_type: str

    # Tab strips (direct electrode connections)
    positive_tabs: list[TabStrip] = field(default_factory=list)
    negative_tabs: list[TabStrip] = field(default_factory=list)

    # Busbars (internal current collection)
    positive_busbar: Busbar | None = None
    negative_busbar: Busbar | None = None

    # Terminal posts
    positive_terminal: TerminalPost | None = None
    negative_terminal: TerminalPost | None = None

    # Metadata
    configuration: str = "standard"
    notes: list[str] = field(default_factory=list)

    @property
    def total_tab_count(self) -> int:
        """Get total number of tab strips."""
        return len(self.positive_tabs) + len(self.negative_tabs)

    @property
    def has_busbars(self) -> bool:
        """Check if geometry has internal busbars."""
        return self.positive_busbar is not None or self.negative_busbar is not None

    def get_all_tabs(self) -> list[TabStrip]:
        """Get all tab strips."""
        return self.positive_tabs + self.negative_tabs

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cell_type": self.cell_type,
            "configuration": self.configuration,
            "positive_tabs": [t.to_dict() for t in self.positive_tabs],
            "negative_tabs": [t.to_dict() for t in self.negative_tabs],
            "positive_busbar": self.positive_busbar.to_dict()
            if self.positive_busbar
            else None,
            "negative_busbar": self.negative_busbar.to_dict()
            if self.negative_busbar
            else None,
            "positive_terminal": self.positive_terminal.to_dict()
            if self.positive_terminal
            else None,
            "negative_terminal": self.negative_terminal.to_dict()
            if self.negative_terminal
            else None,
            "total_tab_count": self.total_tab_count,
            "notes": self.notes,
        }


# Default tab dimensions by cell type (mm)
DEFAULT_TAB_DIMENSIONS: dict[str, dict[str, float]] = {
    "pouch": {
        "strip_width": 30.0,
        "strip_thickness": 0.2,
        "strip_length": 20.0,
        "attachment_width": 40.0,
    },
    "prismatic": {
        "strip_width": 25.0,
        "strip_thickness": 0.3,
        "strip_length": 15.0,
        "attachment_width": 30.0,
        "busbar_width": 20.0,
        "busbar_thickness": 2.0,
    },
    "cylindrical": {
        "strip_width": 5.0,
        "strip_thickness": 0.1,
        "strip_length": 10.0,
    },
}
