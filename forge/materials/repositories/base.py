"""Base repository abstract class for CellCAD.

This module defines the abstract interface for material data repositories.
"""

from abc import ABC, abstractmethod

from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
)


class MaterialRepository(ABC):
    """Abstract base class for material data repositories.

    All repository implementations (PyBaMM, Excel, etc.) should inherit from
    this class and implement the abstract methods.
    """

    @abstractmethod
    def list_cathodes(self) -> list[str]:
        """List available cathode material IDs.

        Returns:
            List of cathode material IDs
        """
        pass

    @abstractmethod
    def get_cathode(self, material_id: str) -> CathodeMaterial:
        """Get cathode material by ID.

        Args:
            material_id: Unique identifier for the cathode material

        Returns:
            CathodeMaterial with all properties

        Raises:
            KeyError: If material_id not found
        """
        pass

    @abstractmethod
    def list_anodes(self) -> list[str]:
        """List available anode material IDs.

        Returns:
            List of anode material IDs
        """
        pass

    @abstractmethod
    def get_anode(self, material_id: str) -> AnodeMaterial:
        """Get anode material by ID.

        Args:
            material_id: Unique identifier for the anode material

        Returns:
            AnodeMaterial with all properties

        Raises:
            KeyError: If material_id not found
        """
        pass

    @abstractmethod
    def list_separators(self) -> list[str]:
        """List available separator material IDs.

        Returns:
            List of separator material IDs
        """
        pass

    @abstractmethod
    def get_separator(self, material_id: str) -> SeparatorMaterial:
        """Get separator material by ID.

        Args:
            material_id: Unique identifier for the separator material

        Returns:
            SeparatorMaterial with all properties

        Raises:
            KeyError: If material_id not found
        """
        pass

    @abstractmethod
    def list_electrolytes(self) -> list[str]:
        """List available electrolyte model IDs.

        Returns:
            List of electrolyte model IDs
        """
        pass

    @abstractmethod
    def get_electrolyte(self, electrolyte_id: str) -> ElectrolyteModel:
        """Get electrolyte model by ID.

        Args:
            electrolyte_id: Unique identifier for the electrolyte model

        Returns:
            ElectrolyteModel with all properties

        Raises:
            KeyError: If electrolyte_id not found
        """
        pass

    def list_packaging_presets(self) -> list[str]:
        """List available packaging preset names.

        Returns:
            List of packaging preset names
        """
        return []

    def get_packaging_layers(self, preset_name: str) -> list[PackagingLayer]:
        """Get packaging layers for a preset.

        Args:
            preset_name: Name of the packaging preset

        Returns:
            List of PackagingLayer objects

        Raises:
            KeyError: If preset_name not found
        """
        raise NotImplementedError("Packaging presets not implemented")
