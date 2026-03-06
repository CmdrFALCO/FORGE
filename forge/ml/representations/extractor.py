"""Abstract interface for geometric representation extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from forge.ml.common.types import CellSpec, GeometricRepresentation, RepresentationType


class RepresentationExtractor(ABC):
    """Extracts geometric representations from cell specifications."""

    @property
    @abstractmethod
    def representation_type(self) -> RepresentationType:
        """The representation type this extractor produces."""
        raise NotImplementedError

    @abstractmethod
    def extract(
        self,
        cell_spec: CellSpec,
    ) -> GeometricRepresentation:
        """Extract one geometric representation from a cell specification."""
        raise NotImplementedError

    @abstractmethod
    def extract_batch(
        self,
        cell_specs: list[CellSpec],
    ) -> list[GeometricRepresentation]:
        """Extract representations for a batch of cell specifications."""
        raise NotImplementedError
