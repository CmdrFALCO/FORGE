"""
Shared type definitions for the FORGE ML layer.

These dataclasses define the contracts between ML submodules. They are
intentionally decoupled from forge.engine.* types; adapters will bridge
the two layers when implementation begins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CellType(Enum):
    """Supported battery cell form factors."""

    POUCH = "pouch"
    PRISMATIC = "prismatic"
    CYLINDRICAL = "cylindrical"


class SamplingStrategy(Enum):
    """Parameter space sampling strategies."""

    LATIN_HYPERCUBE = "latin_hypercube"
    GRID = "grid"
    RANDOM = "random"
    SOBOL_SEQUENCE = "sobol_sequence"


class RepresentationType(Enum):
    """Geometric representation encoding types."""

    PARAMETRIC_VECTOR = "parametric_vector"
    POINT_CLOUD = "point_cloud"
    BREP_GRAPH = "brep_graph"


@dataclass
class ParameterRange:
    """Defines bounds for a single design parameter."""

    name: str
    min_value: float
    max_value: float
    unit: str = ""


@dataclass
class DesignSpace:
    """Defines the full parametric design space for batch generation."""

    parameters: list[ParameterRange] = field(default_factory=list)
    cell_type: CellType = CellType.POUCH
    base_spec: dict[str, Any] = field(default_factory=dict)


@dataclass
class CellSpec:
    """ML-layer representation of a cell design, decoupled from engine dataclasses."""

    cell_type: CellType
    parameters: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""

    c_rates: list[float] = field(default_factory=lambda: [0.2, 1.0, 2.0])
    temperature_celsius: float = 25.0
    model_type: str = "DFN"
    parameter_set: str = "Marquis2019"
    solver_timeout_seconds: float = 300.0


@dataclass
class SimulationResult:
    """Results from a single simulation run."""

    cell_spec: CellSpec
    c_rate: float
    capacity_ah: float = 0.0
    max_temperature_celsius: float = 0.0
    voltage_curve: list[tuple[float, float]] = field(default_factory=list)
    success: bool = True
    error_message: str = ""
    solver_time_seconds: float = 0.0


@dataclass
class RateCapabilityResult:
    """Rate capability metric at high C-rate versus reference C-rate."""

    cell_spec: CellSpec
    reference_c_rate: float
    test_c_rate: float
    capacity_ratio: float = 0.0
    reference_capacity_ah: float = 0.0
    test_capacity_ah: float = 0.0


@dataclass
class SobolIndex:
    """Sobol sensitivity index for one parameter-target pair."""

    parameter_name: str
    target_name: str
    first_order: float = 0.0
    total_order: float = 0.0
    confidence_interval: float = 0.0


@dataclass
class SobolResult:
    """Complete Sobol sensitivity analysis result."""

    target_name: str
    indices: list[SobolIndex] = field(default_factory=list)
    n_samples: int = 0
    converged: bool = False


@dataclass
class GeometricRepresentation:
    """Encoded geometric representation of a cell design."""

    cell_spec: CellSpec
    representation_type: RepresentationType
    data: Any = None
    dimensionality: int = 0


@dataclass
class TrainingConfig:
    """Configuration for an ML training run."""

    model_name: str = ""
    representation_type: RepresentationType = RepresentationType.PARAMETRIC_VECTOR
    target_properties: list[str] = field(default_factory=list)
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 1e-3
    validation_split: float = 0.2
    random_seed: int = 42
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingMetrics:
    """Metrics from a completed training run."""

    model_name: str = ""
    target_property: str = ""
    train_loss: float = 0.0
    val_loss: float = 0.0
    test_mae: float = 0.0
    test_rmse: float = 0.0
    test_r2: float = 0.0
    epochs_trained: int = 0
    training_time_seconds: float = 0.0
