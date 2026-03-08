"""Configuration model for autoresearch runs."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RunConfig:
    """Configuration for one autoresearch run or loop."""

    surrogate_script: Path
    dataset_path: Path
    results_path: Path
    repo_dir: Path
    budget_seconds: int = 300
    min_delta: float = 1e-4
    epsilon: float = 1e-4
    temp_guardrail: float | None = None
    max_error_temp_guardrail: float | None = None
    seed: int = 42
    dry_run: bool = False
    python_executable: str = "python"

    def __post_init__(self) -> None:
        """Validate numeric constraints and normalize paths."""
        self.surrogate_script = Path(self.surrogate_script)
        self.dataset_path = Path(self.dataset_path)
        self.results_path = Path(self.results_path)
        self.repo_dir = Path(self.repo_dir)

        if self.budget_seconds <= 0:
            raise ValueError("budget_seconds must be > 0")
        if self.min_delta < 0:
            raise ValueError("min_delta must be >= 0")
        if self.epsilon < 0:
            raise ValueError("epsilon must be >= 0")

