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


def __getattr__(name: str):  # noqa: N807
    """Lazy imports — avoid pulling in scipy/SALib/pybamm at module load."""
    if name == "BatchGenerator":
        from forge.ml.batch import BatchGenerator
        return BatchGenerator
    if name in ("DatasetBuilder", "DatasetLoader"):
        from forge.ml import dataset
        return getattr(dataset, name)
    if name == "SurrogateModel":
        from forge.ml.models import SurrogateModel
        return SurrogateModel
    if name == "RepresentationExtractor":
        from forge.ml.representations import RepresentationExtractor
        return RepresentationExtractor
    if name == "SensitivityScreener":
        from forge.ml.sensitivity import SensitivityScreener
        return SensitivityScreener
    if name == "SimulationRunner":
        from forge.ml.simulation import SimulationRunner
        return SimulationRunner
    if name == "TrainingPipeline":
        from forge.ml.training import TrainingPipeline
        return TrainingPipeline
    raise AttributeError(f"module 'forge.ml' has no attribute {name!r}")
