"""Coating zone geometry for electrode sheets.

This module defines coated vs uncoated areas on electrode sheets,
which is important for tab welding and CAD generation.
"""

from dataclasses import dataclass


@dataclass
class Rectangle:
    """2D rectangle defined by origin and dimensions.

    Coordinate system: origin at bottom-left of sheet.

    Attributes:
        x_mm: Left edge X position in mm
        y_mm: Bottom edge Y position in mm
        width_mm: Width in mm (X direction)
        height_mm: Height in mm (Y direction)
    """

    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float

    @property
    def x_max(self) -> float:
        """Right edge X position in mm."""
        return self.x_mm + self.width_mm

    @property
    def y_max(self) -> float:
        """Top edge Y position in mm."""
        return self.y_mm + self.height_mm

    @property
    def center(self) -> tuple[float, float]:
        """Center point (x, y) in mm."""
        return (self.x_mm + self.width_mm / 2, self.y_mm + self.height_mm / 2)

    @property
    def center_x(self) -> float:
        """Center X position in mm."""
        return self.x_mm + self.width_mm / 2

    @property
    def center_y(self) -> float:
        """Center Y position in mm."""
        return self.y_mm + self.height_mm / 2

    @property
    def area_mm2(self) -> float:
        """Area in mm²."""
        return self.width_mm * self.height_mm

    @property
    def area_cm2(self) -> float:
        """Area in cm²."""
        return self.area_mm2 / 100.0

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside rectangle.

        Args:
            x: X coordinate in mm
            y: Y coordinate in mm

        Returns:
            True if point is inside rectangle
        """
        return self.x_mm <= x <= self.x_max and self.y_mm <= y <= self.y_max

    def overlaps(self, other: "Rectangle") -> bool:
        """Check if this rectangle overlaps with another.

        Args:
            other: Another Rectangle

        Returns:
            True if rectangles overlap
        """
        return (
            self.x_mm < other.x_max
            and self.x_max > other.x_mm
            and self.y_mm < other.y_max
            and self.y_max > other.y_mm
        )

    def contains(self, other: "Rectangle") -> bool:
        """Check if this rectangle fully contains another.

        Args:
            other: Another Rectangle

        Returns:
            True if other is fully inside this rectangle
        """
        return (
            self.x_mm <= other.x_mm
            and self.x_max >= other.x_max
            and self.y_mm <= other.y_mm
            and self.y_max >= other.y_max
        )

    @classmethod
    def from_center(
        cls, center_x: float, center_y: float, width_mm: float, height_mm: float
    ) -> "Rectangle":
        """Create rectangle from center point and dimensions.

        Args:
            center_x: Center X position in mm
            center_y: Center Y position in mm
            width_mm: Width in mm
            height_mm: Height in mm

        Returns:
            Rectangle instance
        """
        return cls(
            x_mm=center_x - width_mm / 2,
            y_mm=center_y - height_mm / 2,
            width_mm=width_mm,
            height_mm=height_mm,
        )


@dataclass
class CoatingZoneGeometry:
    """Defines coated vs uncoated areas on electrode sheets.

    Uncoated areas are used for tab welding. The coordinate system
    has origin at bottom-left of the cathode sheet.

    Attributes:
        cathode_sheet: Full cathode sheet dimensions
        anode_sheet: Full anode sheet dimensions
        separator_sheet: Full separator sheet dimensions
        cathode_coated: Coated (active) region on cathode
        anode_coated: Coated (active) region on anode
        cathode_tab_zone: Tab attachment zone on cathode (uncoated area)
        anode_tab_zone: Tab attachment zone on anode (uncoated area)
        anode_overhang_x_mm: Anode extends beyond cathode in X direction
        anode_overhang_y_mm: Anode extends beyond cathode in Y direction
        separator_overhang_mm: Separator extends beyond anode
    """

    # Full sheet dimensions
    cathode_sheet: Rectangle
    anode_sheet: Rectangle
    separator_sheet: Rectangle

    # Coated (active) regions - smaller than full sheet
    cathode_coated: Rectangle
    anode_coated: Rectangle

    # Tab attachment zones (uncoated areas)
    cathode_tab_zone: Rectangle | None = None
    anode_tab_zone: Rectangle | None = None

    # Overhang dimensions for safety validation
    anode_overhang_x_mm: float = 0.0
    anode_overhang_y_mm: float = 0.0
    separator_overhang_mm: float = 0.0

    def validate_overhangs(self) -> list[str]:
        """Check that safety overhangs are positive.

        Anode should extend beyond cathode, and separator should
        extend beyond anode to prevent lithium plating and shorts.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        if self.anode_overhang_x_mm < 0:
            errors.append(
                f"Anode X overhang negative: {self.anode_overhang_x_mm:.2f} mm"
            )
        if self.anode_overhang_y_mm < 0:
            errors.append(
                f"Anode Y overhang negative: {self.anode_overhang_y_mm:.2f} mm"
            )
        if self.separator_overhang_mm < 0:
            errors.append(
                f"Separator overhang negative: {self.separator_overhang_mm:.2f} mm"
            )
        return errors

    def validate_containment(self) -> list[str]:
        """Validate that layers properly contain each other.

        Separator should contain anode, anode should contain cathode.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check anode contains cathode coated area
        if not self.anode_coated.contains(self.cathode_coated):
            errors.append("Anode coated area does not fully contain cathode coated area")

        # Check separator contains anode
        if not self.separator_sheet.contains(self.anode_sheet):
            errors.append("Separator sheet does not fully contain anode sheet")

        return errors

    def get_cathode_uncoated_area_cm2(self) -> float:
        """Calculate uncoated area on cathode sheet.

        Returns:
            Uncoated area in cm²
        """
        return self.cathode_sheet.area_cm2 - self.cathode_coated.area_cm2

    def get_anode_uncoated_area_cm2(self) -> float:
        """Calculate uncoated area on anode sheet.

        Returns:
            Uncoated area in cm²
        """
        return self.anode_sheet.area_cm2 - self.anode_coated.area_cm2

    @classmethod
    def from_dimensions(
        cls,
        cathode_width_mm: float,
        cathode_height_mm: float,
        anode_overhang_x_mm: float,
        anode_overhang_y_mm: float,
        separator_overhang_mm: float,
        cathode_tab_width_mm: float = 0.0,
        cathode_tab_height_mm: float = 0.0,
        anode_tab_width_mm: float = 0.0,
        anode_tab_height_mm: float = 0.0,
    ) -> "CoatingZoneGeometry":
        """Create coating zones from basic dimensions.

        Assumes symmetric overhangs and centered sheets.

        Args:
            cathode_width_mm: Cathode coated width
            cathode_height_mm: Cathode coated height
            anode_overhang_x_mm: Anode overhang per side in X
            anode_overhang_y_mm: Anode overhang per side in Y
            separator_overhang_mm: Separator overhang beyond anode
            cathode_tab_width_mm: Cathode tab width (uncoated area)
            cathode_tab_height_mm: Cathode tab height
            anode_tab_width_mm: Anode tab width
            anode_tab_height_mm: Anode tab height

        Returns:
            CoatingZoneGeometry instance
        """
        # Anode dimensions
        anode_width_mm = cathode_width_mm + 2 * anode_overhang_x_mm
        anode_height_mm = cathode_height_mm + 2 * anode_overhang_y_mm

        # Separator dimensions
        separator_width_mm = anode_width_mm + 2 * separator_overhang_mm
        separator_height_mm = anode_height_mm + 2 * separator_overhang_mm

        # All sheets centered at same origin for simplicity
        cathode_sheet = Rectangle(
            x_mm=0, y_mm=0, width_mm=cathode_width_mm, height_mm=cathode_height_mm
        )

        anode_sheet = Rectangle(
            x_mm=-anode_overhang_x_mm,
            y_mm=-anode_overhang_y_mm,
            width_mm=anode_width_mm,
            height_mm=anode_height_mm,
        )

        separator_sheet = Rectangle(
            x_mm=-anode_overhang_x_mm - separator_overhang_mm,
            y_mm=-anode_overhang_y_mm - separator_overhang_mm,
            width_mm=separator_width_mm,
            height_mm=separator_height_mm,
        )

        # Coated areas (same as sheet for full coating, smaller if tabs)
        cathode_coated = Rectangle(
            x_mm=0, y_mm=0, width_mm=cathode_width_mm, height_mm=cathode_height_mm
        )

        anode_coated = Rectangle(
            x_mm=-anode_overhang_x_mm,
            y_mm=-anode_overhang_y_mm,
            width_mm=anode_width_mm,
            height_mm=anode_height_mm,
        )

        # Tab zones (if specified)
        cathode_tab_zone = None
        if cathode_tab_width_mm > 0 and cathode_tab_height_mm > 0:
            cathode_tab_zone = Rectangle(
                x_mm=cathode_width_mm,  # Tab at right edge
                y_mm=cathode_height_mm / 2 - cathode_tab_height_mm / 2,
                width_mm=cathode_tab_width_mm,
                height_mm=cathode_tab_height_mm,
            )

        anode_tab_zone = None
        if anode_tab_width_mm > 0 and anode_tab_height_mm > 0:
            anode_tab_zone = Rectangle(
                x_mm=-anode_overhang_x_mm - anode_tab_width_mm,  # Tab at left edge
                y_mm=anode_height_mm / 2 - anode_tab_height_mm / 2 - anode_overhang_y_mm,
                width_mm=anode_tab_width_mm,
                height_mm=anode_tab_height_mm,
            )

        return cls(
            cathode_sheet=cathode_sheet,
            anode_sheet=anode_sheet,
            separator_sheet=separator_sheet,
            cathode_coated=cathode_coated,
            anode_coated=anode_coated,
            cathode_tab_zone=cathode_tab_zone,
            anode_tab_zone=anode_tab_zone,
            anode_overhang_x_mm=anode_overhang_x_mm,
            anode_overhang_y_mm=anode_overhang_y_mm,
            separator_overhang_mm=separator_overhang_mm,
        )
