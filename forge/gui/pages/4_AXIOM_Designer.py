"""AXIOM Designer Streamlit page."""

from __future__ import annotations

import time
from copy import deepcopy
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html as components_html

from forge.gui.axiom_pipeline import (
    DEMO_DIR,
    FLOW_STEPS,
    PipelineRun,
    PipelineStep,
    StepStatus,
    load_demo_run,
    run_pipeline_with_tracking,
)
from forge.gui.components import render_pipeline_flow
from forge.gui.utils.common import init_session_state

PAGE_TITLE = "AXIOM Designer"
DEMO_FILES = {
    "Successful (1st try)": "successful_first_try.json",
    "Retry Example": "retry_success.json",
}
MODE_RECORDED = "Recorded Demo"
MODE_OLLAMA = "Live - Ollama"
MODE_CLAUDE = "Live - Claude API"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


init_session_state(
    {
        "axiom_pipeline_run": None,
        "axiom_is_running": False,
        "axiom_mode": MODE_RECORDED,
        "axiom_demo_choice": "Successful (1st try)",
        "axiom_cell_type": "prismatic",
        "axiom_prompt": "Design a 100Ah LFP prismatic cell for stationary energy storage",
        "axiom_ollama_host": "http://localhost:11434",
        "axiom_ollama_model": "qwen2.5-coder:14b",
        "axiom_claude_key": "",
    }
)


def _render_flow(container, run: PipelineRun | None) -> None:
    if run is None:
        run = PipelineRun(
            prompt="",
            backend_name="AXIOM",
            cell_type=st.session_state["axiom_cell_type"],
            steps=[PipelineStep(name=name) for name in FLOW_STEPS],
        )
    flow_html = render_pipeline_flow(run)
    with container:
        if hasattr(st, "html"):
            st.html(flow_html)
        else:
            components_html(flow_html, height=900, scrolling=False)


def _result_metrics(run: PipelineRun) -> dict[str, float] | None:
    summary = run.calculation_summary or {}
    required = [
        "capacity_ah",
        "energy_wh",
        "total_mass_g",
        "gravimetric_ed_whkg",
        "volumetric_ed_cell_whl",
    ]
    if not all(key in summary for key in required):
        return None
    return summary


def _validation_payloads(run: PipelineRun) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for step in run.steps:
        if step.name in {"Schema Validate", "Physics Validate", "Retry Feedback"}:
            payloads.append(
                {
                    "attempt": step.attempt,
                    "step": step.name,
                    "status": step.status.value,
                    "detail": step.detail,
                    "raw_data": step.raw_data,
                }
            )
    return payloads


def _raw_yaml(run: PipelineRun) -> str | None:
    if run.yaml_content:
        return run.yaml_content
    parse_steps = [step for step in run.steps if step.name == "Parse YAML" and step.raw_data]
    if not parse_steps:
        return None
    raw_data = parse_steps[-1].raw_data
    if isinstance(raw_data, dict):
        return raw_data.get("raw_yaml")
    return None


def _sleep_for_step(step: PipelineStep) -> None:
    delay = min(step.duration_ms / 1000, 2.0 if step.name == "LLM Generate" else 0.3)
    time.sleep(max(delay, 0.06))


def _animate_demo(
    demo_run: PipelineRun,
    flow_placeholder,
    stats_placeholder,
) -> PipelineRun:
    replay = PipelineRun(
        prompt=demo_run.prompt,
        backend_name=demo_run.backend_name,
        cell_type=demo_run.cell_type,
        max_attempts=demo_run.max_attempts,
    )

    for recorded_step in demo_run.steps:
        replay.attempt = recorded_step.attempt
        active_step = PipelineStep(
            name=recorded_step.name,
            status=StepStatus.ACTIVE,
            detail=recorded_step.detail,
            raw_data=recorded_step.raw_data,
            attempt=recorded_step.attempt,
        )
        replay.steps.append(active_step)
        replay.total_duration_ms = sum(step.duration_ms for step in replay.steps)
        st.session_state["axiom_pipeline_run"] = replay
        _render_flow(flow_placeholder, replay)
        stats_placeholder.caption(
            f"Attempt {replay.attempt}/{replay.max_attempts} | {replay.total_duration_ms:.0f} ms"
        )
        _sleep_for_step(recorded_step)

        replay.steps[-1] = deepcopy(recorded_step)
        replay.total_duration_ms = sum(step.duration_ms for step in replay.steps)
        replay.success = demo_run.success and len(replay.steps) == len(demo_run.steps)
        replay.yaml_content = demo_run.yaml_content
        replay.calculation_summary = demo_run.calculation_summary
        replay.last_error = demo_run.last_error
        replay.retry_reasons = list(demo_run.retry_reasons)
        st.session_state["axiom_pipeline_run"] = replay
        _render_flow(flow_placeholder, replay)
        stats_placeholder.caption(
            f"Attempt {replay.attempt}/{replay.max_attempts} | {replay.total_duration_ms:.0f} ms"
        )

    replay.success = demo_run.success
    replay.total_duration_ms = demo_run.total_duration_ms
    replay.attempt = demo_run.attempt
    st.session_state["axiom_pipeline_run"] = replay
    _render_flow(flow_placeholder, replay)
    stats_placeholder.caption(
        f"Attempt {replay.attempt}/{replay.max_attempts} | {replay.total_duration_ms:.0f} ms"
    )
    return replay


with st.sidebar:
    st.markdown("### AXIOM Controls")
    st.radio(
        "Mode",
        options=[MODE_RECORDED, MODE_OLLAMA, MODE_CLAUDE],
        key="axiom_mode",
    )
    st.selectbox(
        "Cell Type",
        options=["prismatic", "pouch", "cylindrical"],
        key="axiom_cell_type",
        help="AXIOM prompt and validation rules are cell-type specific.",
    )

    if st.session_state["axiom_mode"] == MODE_RECORDED:
        st.selectbox(
            "Recorded Demo",
            options=list(DEMO_FILES.keys()),
            key="axiom_demo_choice",
        )
        demo_path = DEMO_DIR / DEMO_FILES[st.session_state["axiom_demo_choice"]]
        st.caption(f"Replay source: {demo_path.relative_to(_repo_root())}")
    elif st.session_state["axiom_mode"] == MODE_OLLAMA:
        st.text_input("Ollama Host", key="axiom_ollama_host")
        st.text_input("Model", key="axiom_ollama_model")
    else:
        st.text_input(
            "Claude API Key",
            key="axiom_claude_key",
            type="password",
            help="Falls back to ANTHROPIC_API_KEY if left blank.",
        )

    st.markdown("---")
    st.caption(
        "AXIOM uses Colored Petri Nets to supervise LLM-generated battery cell designs. "
        "The flow panel shows each stage as it executes."
    )


st.title(PAGE_TITLE)
st.caption("AI-Assisted Cell Design with Formal Supervision")

left_col, right_col = st.columns([2, 3], gap="large")

with right_col:
    st.subheader("Pipeline Flow")
    flow_placeholder = st.empty()
    stats_placeholder = st.empty()
    _render_flow(flow_placeholder, st.session_state["axiom_pipeline_run"])
    if st.session_state["axiom_pipeline_run"] is not None:
        current_run = st.session_state["axiom_pipeline_run"]
        stats_placeholder.caption(
            f"Attempt {current_run.attempt}/{current_run.max_attempts} | "
            f"{current_run.total_duration_ms:.0f} ms total"
        )

with left_col:
    st.subheader("Design Request")
    st.text_area(
        "Prompt",
        key="axiom_prompt",
        height=180,
        placeholder="Design a 100Ah LFP prismatic cell for stationary energy storage",
    )
    generate_clicked = st.button(
        "Generate",
        type="primary",
        use_container_width=True,
        disabled=st.session_state["axiom_is_running"],
    )

    if generate_clicked:
        st.session_state["axiom_is_running"] = True
        try:
            if st.session_state["axiom_mode"] == MODE_RECORDED:
                demo_run = load_demo_run(DEMO_FILES[st.session_state["axiom_demo_choice"]])
                demo_run.prompt = st.session_state["axiom_prompt"] or demo_run.prompt
                demo_run.cell_type = st.session_state["axiom_cell_type"]
                run = _animate_demo(demo_run, flow_placeholder, stats_placeholder)
            else:
                def on_step_update(run: PipelineRun) -> None:
                    st.session_state["axiom_pipeline_run"] = deepcopy(run)
                    _render_flow(flow_placeholder, run)
                    stats_placeholder.caption(
                        f"Attempt {run.attempt}/{run.max_attempts} | "
                        f"{run.total_duration_ms:.0f} ms total"
                    )

                backend_name = "ollama" if st.session_state["axiom_mode"] == MODE_OLLAMA else "claude"
                backend_kwargs = {}
                if backend_name == "ollama":
                    backend_kwargs["host"] = st.session_state["axiom_ollama_host"]
                    backend_kwargs["model"] = st.session_state["axiom_ollama_model"]

                run = run_pipeline_with_tracking(
                    prompt=st.session_state["axiom_prompt"],
                    backend=backend_name,
                    api_key=st.session_state["axiom_claude_key"] or None,
                    cell_type=st.session_state["axiom_cell_type"],
                    max_attempts=3,
                    on_step_update=on_step_update,
                    **backend_kwargs,
                )
                st.session_state["axiom_pipeline_run"] = run
                _render_flow(flow_placeholder, run)
                stats_placeholder.caption(
                    f"Attempt {run.attempt}/{run.max_attempts} | {run.total_duration_ms:.0f} ms total"
                )
        finally:
            st.session_state["axiom_is_running"] = False

    run = st.session_state["axiom_pipeline_run"]
    if run is None:
        st.info("Choose a mode, enter a design request, and run the pipeline.")
    elif run.success:
        metrics = _result_metrics(run)
        st.success("Design completed successfully.")
        if metrics is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Capacity", f"{metrics['capacity_ah']:.1f} Ah")
                st.metric("Energy", f"{metrics['energy_wh']:.1f} Wh")
                st.metric("Mass", f"{metrics['total_mass_g']:.1f} g")
            with col2:
                st.metric("Gravimetric ED", f"{metrics['gravimetric_ed_whkg']:.1f} Wh/kg")
                st.metric("Volumetric ED", f"{metrics['volumetric_ed_cell_whl']:.1f} Wh/L")
                st.metric("Cell Type", run.cell_type.title())
    else:
        st.error(run.last_error or "Pipeline did not complete successfully.")

    with st.expander("Raw YAML", expanded=False):
        raw_yaml = _raw_yaml(run) if run is not None else None
        if raw_yaml:
            st.code(raw_yaml, language="yaml")
        else:
            st.caption("No YAML captured yet.")

    with st.expander("Validation Details", expanded=False):
        if run is None:
            st.caption("Run the pipeline to inspect validation output.")
        else:
            payloads = _validation_payloads(run)
            if payloads:
                st.json(payloads)
            else:
                st.caption("No validation payloads recorded yet.")
