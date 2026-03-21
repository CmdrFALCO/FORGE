"""HTML flow renderer for the AXIOM Designer page."""

from __future__ import annotations

from html import escape

from forge.gui.axiom_pipeline import FLOW_STEPS, RETRY_STEP, PipelineRun, PipelineStep, StepStatus


def render_pipeline_flow(run: PipelineRun) -> str:
    """Return an HTML string visualizing the current pipeline state."""
    current_attempt = max(
        [step.attempt for step in run.steps if step.name != RETRY_STEP],
        default=run.attempt,
    )
    node_steps = _display_steps(run, current_attempt)
    retry_step = run.latest_retry_feedback
    html_nodes = "\n".join(_render_node(step) for step in node_steps)

    retry_html = ""
    if retry_step is not None:
        feedback = retry_step.raw_data.get("feedback", retry_step.detail) if isinstance(
            retry_step.raw_data, dict
        ) else retry_step.detail
        retry_html = f"""
        <div class="axiom-retry">
          <div class="axiom-retry-label">Retry Loop</div>
          <div class="axiom-retry-body">
            <div class="axiom-retry-arrow">Physics or parsing feedback routes back to LLM Generate</div>
            <div class="axiom-retry-message">{escape(str(feedback))}</div>
          </div>
        </div>
        """

    status_text = "Complete" if run.success else "In progress"
    if run.last_error and not run.success:
        status_text = escape(run.last_error)

    return f"""
<style>
.axiom-flow {{
  --fg: #E0E0E0;
  --muted: #9AA0A6;
  --pending: #666666;
  --active: #4A9EFF;
  --passed: #4CAF50;
  --failed: #FF5252;
  --retry: #FFA726;
  --border: #444444;
  color: var(--fg);
  font-family: "Segoe UI", sans-serif;
}}
.axiom-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}}
.axiom-badge {{
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(74, 158, 255, 0.16);
  border: 1px solid rgba(74, 158, 255, 0.35);
  font-size: 0.85rem;
}}
.axiom-meta {{
  color: var(--muted);
  font-size: 0.9rem;
}}
.axiom-node {{
  position: relative;
  margin-left: 16px;
  padding: 12px 14px 12px 18px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.02);
  margin-bottom: 18px;
}}
.axiom-node:not(:last-child)::after {{
  content: "";
  position: absolute;
  left: -16px;
  top: calc(100% + 2px);
  width: 2px;
  height: 18px;
  background: var(--border);
}}
.axiom-node::before {{
  content: "";
  position: absolute;
  left: -22px;
  top: 18px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--pending);
  border: 2px solid rgba(255, 255, 255, 0.08);
}}
.axiom-node.pending {{ border-style: dashed; opacity: 0.75; }}
.axiom-node.active {{
  border-color: var(--active);
  box-shadow: 0 0 0 1px rgba(74, 158, 255, 0.25);
  animation: axiom-pulse 1.2s ease-in-out infinite;
}}
.axiom-node.active::before {{ background: var(--active); }}
.axiom-node.passed::before {{ background: var(--passed); }}
.axiom-node.failed::before {{ background: var(--failed); }}
.axiom-node.skipped::before {{ background: var(--retry); }}
.axiom-node-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}}
.axiom-step-name {{
  font-weight: 600;
}}
.axiom-duration {{
  font-size: 0.78rem;
  color: var(--muted);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  padding: 2px 8px;
}}
.axiom-step-detail {{
  margin-top: 6px;
  color: var(--muted);
  font-size: 0.88rem;
  line-height: 1.35;
}}
.axiom-retry {{
  margin: 8px 0 18px 16px;
  border: 1px dashed rgba(255, 167, 38, 0.55);
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(255, 167, 38, 0.08);
}}
.axiom-retry-label {{
  color: var(--retry);
  font-weight: 600;
  margin-bottom: 6px;
}}
.axiom-retry-arrow {{
  color: var(--retry);
  font-size: 0.85rem;
  margin-bottom: 6px;
}}
.axiom-retry-message {{
  color: var(--fg);
  font-size: 0.88rem;
  line-height: 1.35;
}}
@keyframes axiom-pulse {{
  0% {{ box-shadow: 0 0 0 0 rgba(74, 158, 255, 0.32); }}
  70% {{ box-shadow: 0 0 0 9px rgba(74, 158, 255, 0.0); }}
  100% {{ box-shadow: 0 0 0 0 rgba(74, 158, 255, 0.0); }}
}}
</style>
<div class="axiom-flow">
  <div class="axiom-header">
    <div class="axiom-badge">Attempt {current_attempt} of {run.max_attempts}</div>
    <div class="axiom-meta">{status_text}</div>
  </div>
  {html_nodes}
  {retry_html}
</div>
"""


def _display_steps(run: PipelineRun, attempt: int) -> list[PipelineStep]:
    steps: list[PipelineStep] = []
    for name in FLOW_STEPS:
        if name == "Build Prompt":
            step = _latest_step(run.steps, name)
        else:
            step = _latest_step(run.steps, name, attempt=attempt)
        steps.append(step or PipelineStep(name=name))
    return steps


def _latest_step(
    steps: list[PipelineStep], name: str, attempt: int | None = None
) -> PipelineStep | None:
    matches = [
        step
        for step in steps
        if step.name == name and (attempt is None or step.attempt == attempt)
    ]
    return matches[-1] if matches else None


def _render_node(step: PipelineStep) -> str:
    status = step.status.value
    detail = escape(step.detail or _default_detail(step.status))
    duration = escape(_format_duration(step.duration_ms))
    return f"""
    <div class="axiom-node {status}">
      <div class="axiom-node-header">
        <div class="axiom-step-name">{escape(step.name)}</div>
        <div class="axiom-duration">{duration}</div>
      </div>
      <div class="axiom-step-detail">{detail}</div>
    </div>
    """


def _default_detail(status: StepStatus) -> str:
    if status == StepStatus.PENDING:
        return "Waiting for upstream step"
    if status == StepStatus.ACTIVE:
        return "Running now"
    if status == StepStatus.SKIPPED:
        return "Skipped"
    return ""


def _format_duration(duration_ms: float) -> str:
    if duration_ms <= 0:
        return "--"
    if duration_ms >= 1000:
        return f"{duration_ms / 1000:.1f}s"
    return f"{duration_ms:.0f}ms"
