"""
FORGE ML Layer (Layer 3) - Surrogate Modeling and Geometric Representation Learning.

Skeleton package providing interfaces for:
- Batch geometry generation from parametric ranges
- PyBaMM electrochemical simulation for training data
- PyBOP Sobol sensitivity screening
- Dataset creation, storage, and loading
- Geometric representation extraction (parametric vectors, point clouds, B-Rep graphs)
- ML surrogate model definitions
- Training pipeline orchestration

Status: Interface definitions only. Implementation follows thesis experiment planning.
"""

from forge.ml.batch import BatchGenerator
from forge.ml.dataset import DatasetBuilder, DatasetLoader
from forge.ml.models import SurrogateModel
from forge.ml.representations import RepresentationExtractor
from forge.ml.sensitivity import SensitivityScreener
from forge.ml.simulation import SimulationRunner
from forge.ml.training import TrainingPipeline

__all__ = [
    "BatchGenerator",
    "DatasetBuilder",
    "DatasetLoader",
    "RepresentationExtractor",
    "SensitivityScreener",
    "SimulationRunner",
    "SurrogateModel",
    "TrainingPipeline",
]
