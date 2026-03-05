"""Result types for LLM-driven cell design generation."""

from dataclasses import dataclass, field

from forge.engine.models.prismatic import PrismaticCellInput
from forge.engine.models.results import CellReport


@dataclass
class GenerationResult:
    """
    Result of an LLM cell design generation attempt.

    Captures the complete pipeline outcome including:
    - Whether generation succeeded
    - The generated YAML content
    - Validation errors (if any)
    - The converted cell input (if valid)
    - Calculation results (if successful)
    - Number of attempts made
    """

    success: bool
    attempts: int
    yaml_content: str | None = None
    cell_input: PrismaticCellInput | None = None
    calculation_result: CellReport | None = None
    validation_errors: list[str] = field(default_factory=list)
    last_error: str | None = None

    # For thesis analysis
    tokens_used: int = 0
    retry_reasons: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Human-readable summary for logging/display."""
        if self.success:
            cr = self.calculation_result
            return (
                f"âœ“ Design successful (attempt {self.attempts})\n"
                f"  Capacity: {cr.capacity_ah:.1f} Ah\n"
                f"  Energy: {cr.energy_wh:.1f} Wh\n"
                f"  Mass: {cr.total_mass_g:.1f} g\n"
                f"  Gravimetric ED: {cr.gravimetric_ed_whkg:.1f} Wh/kg"
            )
        else:
            return (
                f"âœ— Design failed after {self.attempts} attempts\n  Last error: {self.last_error}"
            )

