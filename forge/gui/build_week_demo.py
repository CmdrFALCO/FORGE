"""Execution helpers for the OpenAI Build Week demonstration page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from forge.gui.axiom_pipeline import (
    RETRY_STEP,
    PipelineRun,
    PipelineStep,
    StepStatus,
    run_pipeline_with_tracking,
)

OPENAI_BUILD_WEEK_MODEL = "gpt-5.6"


@dataclass(frozen=True)
class LiveAttemptSummary:
    """Display-safe evidence captured for one live pipeline attempt."""

    attempt: int
    outcome: str
    steps: tuple[PipelineStep, ...]
    output_text: str | None
    raw_yaml: str | None
    feedback: str | None


def run_live_openai_demo(
    prompt: str,
    on_step_update: Callable[[PipelineRun], None] | None = None,
) -> PipelineRun:
    """Run the bounded cylindrical AXIOM scenario through OpenAI."""
    return run_pipeline_with_tracking(
        prompt=prompt,
        backend="openai",
        cell_type="cylindrical",
        max_attempts=2,
        model=OPENAI_BUILD_WEEK_MODEL,
        on_step_update=on_step_update,
    )


def summarize_live_attempts(run: PipelineRun) -> list[LiveAttemptSummary]:
    """Extract ordered attempt evidence from a live tracked pipeline run."""
    attempt_numbers = sorted({step.attempt for step in run.steps if step.name != "Build Prompt"})
    summaries: list[LiveAttemptSummary] = []
    for attempt in attempt_numbers:
        steps = tuple(
            step
            for step in run.steps
            if step.attempt == attempt and step.name != "Build Prompt"
        )
        failed_steps = [step for step in steps if step.status == StepStatus.FAILED]
        if failed_steps:
            outcome = (
                "Rejected"
                if failed_steps[0].name in {"Parse YAML", "Schema Validate", "Physics Validate"}
                else "Failed"
            )
        elif run.success and attempt == run.attempt:
            outcome = "Accepted"
        elif any(step.name == RETRY_STEP for step in steps):
            outcome = "Rejected"
        else:
            outcome = "Incomplete"

        llm_step = next((step for step in steps if step.name == "LLM Generate"), None)
        parse_step = next((step for step in steps if step.name == "Parse YAML"), None)
        retry_step = next((step for step in steps if step.name == RETRY_STEP), None)
        output_text = llm_step.raw_data if llm_step and isinstance(llm_step.raw_data, str) else None
        raw_yaml = None
        if parse_step and isinstance(parse_step.raw_data, dict):
            candidate_yaml = parse_step.raw_data.get("raw_yaml")
            raw_yaml = candidate_yaml if isinstance(candidate_yaml, str) else None
        feedback = None
        if retry_step and isinstance(retry_step.raw_data, dict):
            candidate_feedback = retry_step.raw_data.get("feedback")
            feedback = candidate_feedback if isinstance(candidate_feedback, str) else None

        summaries.append(
            LiveAttemptSummary(
                attempt=attempt,
                outcome=outcome,
                steps=steps,
                output_text=output_text,
                raw_yaml=raw_yaml,
                feedback=feedback,
            )
        )
    return summaries
