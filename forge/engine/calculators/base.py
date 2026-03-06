"""Base calculator contract for FORGE engine form-factor calculators."""

from abc import ABC, abstractmethod

from forge.engine.models.results import CellReport


class BaseCalculator(ABC):
    """Abstract base for all cell calculators.

    Contract: subclass ``__init__`` receives all inputs,
    ``calculate()`` executes computation and returns ``CellReport``.
    """

    form_factor: str

    @abstractmethod
    def calculate(self) -> CellReport:
        """Run cell calculations and return a ``CellReport``."""
        ...

