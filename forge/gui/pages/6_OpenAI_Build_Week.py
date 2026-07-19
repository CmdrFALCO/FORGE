"""OpenAI Build Week verified-replay and live demonstration page."""

from __future__ import annotations

import os
import time
from copy import deepcopy
from typing import Any

import streamlit as st
from streamlit.components.v1 import html as components_html

from forge.gui.axiom_pipeline import PipelineRun
from forge.gui.build_week_demo import (
    OPENAI_BUILD_WEEK_MODEL,
    run_live_openai_demo,
    summarize_live_attempts,
)
from forge.gui.components import compute_cpn_sequence, render_cpn_graph, render_pipeline_flow
from forge.gui.verified_replay import (
    VerifiedReplay,
    VerifiedReplayError,
    build_audit_archive,
    load_verified_replay,
)

PAGE_TITLE = "FORGE OpenAI Build Week"
MODE_REPLAY = "Verified Replay"
MODE_LIVE = "Live OpenAI"


def _geometry(attempt: dict[str, Any]) -> dict[str, float]:
    parsed = attempt["validation"]["parsed_yaml"]
    geometry = parsed["geometry"]
    winding = parsed["winding"]
    diameter = float(geometry["diameter_mm"])
    wall = float(geometry["can_wall_thickness_mm"])
    mandrel = float(winding["mandrel_diameter_mm"])
    clearance = float(winding["winding_clearance_mm"])
    inner = diameter - 2 * wall
    return {
        "diameter_mm": diameter,
        "inner_diameter_mm": inner,
        "mandrel_diameter_mm": mandrel,
        "clearance_mm": clearance,
        "available_winding_mm": inner - mandrel - 2 * clearance,
    }


def _constraint_rows(attempt: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "ID": result["constraint_id"],
            "Constraint": result["name"].replace("_", " ").title(),
            "Result": "Passed" if result["passed"] else "Rejected",
            "Actual": result["actual_value"],
            "Threshold": result["threshold"] or None,
        }
        for result in attempt["validation"]["constraint_results"]
    ]
    return sorted(rows, key=lambda row: row["ID"] != "CY5")


def _render_attempt(attempt: dict[str, Any], accepted: bool) -> None:
    geometry = _geometry(attempt)
    status = "Accepted" if accepted else "Rejected"
    st.markdown(f"#### Attempt {attempt['attempt']} | {status}")
    metric_a, metric_b = st.columns(2)
    metric_a.metric("Outer diameter", f"{geometry['diameter_mm']:.1f} mm")
    metric_b.metric(
        "Winding span",
        f"{geometry['available_winding_mm']:.2f} mm",
        delta=f"{geometry['available_winding_mm'] - 2.0:+.2f} mm vs limit",
        delta_color="normal",
    )
    st.dataframe(
        _constraint_rows(attempt),
        hide_index=True,
        width="stretch",
        height=258,
        column_config={
            "Actual": st.column_config.NumberColumn(format="%.3f"),
        },
    )
    with st.expander(f"Attempt {attempt['attempt']} YAML", expanded=False):
        st.code(attempt["validation"]["raw_yaml"], language="yaml")


def _render_mode_band(
    mode: str,
    replay: VerifiedReplay,
    live_run: PipelineRun | None,
) -> None:
    mode_class = "verified" if mode == MODE_REPLAY else "live"
    label = "VERIFIED REPLAY" if mode == MODE_REPLAY else "LIVE OPENAI"
    if mode == MODE_REPLAY:
        details = (
            f"<span>Model {replay.manifest['requested_model']}</span>"
            f"<span>Run {replay.manifest['run_id']}</span>"
            "<span>Integrity passed</span>"
        )
    elif live_run is None:
        details = (
            f"<span>Requested model {OPENAI_BUILD_WEEK_MODEL}</span>"
            "<span>No session run</span>"
        )
    else:
        outcome = "Accepted" if live_run.success else "Rejected"
        details = (
            f"<span>Requested model {OPENAI_BUILD_WEEK_MODEL}</span>"
            f"<span>Attempt {live_run.attempt}/{live_run.max_attempts}</span>"
            f"<span>{outcome}</span>"
        )
    st.markdown(
        f"""
        <div class="bw-mode-band {mode_class}">
          <strong>{label}</strong>
          {details}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_result_metrics(run: PipelineRun) -> None:
    summary = run.calculation_summary or {}
    if not all(
        key in summary
        for key in (
            "capacity_ah",
            "energy_wh",
            "total_mass_g",
            "gravimetric_ed_whkg",
            "volumetric_ed_cell_whl",
        )
    ):
        return
    primary = st.columns(3)
    primary[0].metric("Capacity", f"{summary['capacity_ah']:.3f} Ah")
    primary[1].metric("Energy", f"{summary['energy_wh']:.3f} Wh")
    primary[2].metric("Mass", f"{summary['total_mass_g']:.3f} g")
    density = st.columns(2)
    density[0].metric("Gravimetric", f"{summary['gravimetric_ed_whkg']:.1f} Wh/kg")
    density[1].metric("Volumetric", f"{summary['volumetric_ed_cell_whl']:.1f} Wh/L")


def _render_live_attempts(run: PipelineRun) -> None:
    summaries = summarize_live_attempts(run)
    if not summaries:
        return
    st.subheader("Live attempt history")
    columns = st.columns(len(summaries), gap="large")
    for column, summary in zip(columns, summaries, strict=True):
        with column:
            st.markdown(f"#### Attempt {summary.attempt} | {summary.outcome}")
            st.dataframe(
                [
                    {
                        "Step": step.name,
                        "Status": step.status.value.title(),
                        "Detail": step.detail,
                    }
                    for step in summary.steps
                ],
                hide_index=True,
                width="stretch",
                height=282,
                column_config={"Detail": st.column_config.TextColumn(width="large")},
            )
            if summary.feedback:
                feedback_label = (
                    "Terminal validation feedback"
                    if summary.attempt == run.max_attempts and not run.success
                    else "Corrective feedback"
                )
                with st.expander(feedback_label, expanded=not run.success):
                    st.code(summary.feedback, language="text")
            with st.expander("Generated YAML", expanded=False):
                if summary.raw_yaml:
                    st.code(summary.raw_yaml, language="yaml")
                else:
                    st.caption("No parsed YAML was captured for this attempt.")
            with st.expander("Model output", expanded=False):
                if summary.output_text:
                    st.code(summary.output_text, language="yaml")
                else:
                    st.caption("No model output was captured for this attempt.")


def _render_live_session_details(run: PipelineRun) -> None:
    details = {
        "Requested model": OPENAI_BUILD_WEEK_MODEL,
        "Outcome": "Accepted" if run.success else "Rejected",
        "Attempts used": run.attempt,
        "Attempt limit": run.max_attempts,
        "Cell type": run.cell_type,
        "Pipeline duration": f"{run.total_duration_ms / 1000:.2f} s",
        "Persistence": "Browser session only",
    }
    st.dataframe(
        [{"Field": key, "Value": str(value)} for key, value in details.items()],
        hide_index=True,
        width="stretch",
        column_config={"Value": st.column_config.TextColumn(width="large")},
    )


def _render_pipeline_views(run: PipelineRun) -> None:
    flow_tab, cpn_tab = st.tabs(["Pipeline Flow", "Colored Petri Net"])
    with flow_tab:
        st.html(render_pipeline_flow(run))
    with cpn_tab:
        sequence = compute_cpn_sequence(run)
        total_steps = max(len(sequence), 1)
        state_key = "build_week_cpn_step_index"
        if state_key not in st.session_state:
            st.session_state[state_key] = total_steps - 1
        current_step = min(max(int(st.session_state[state_key]), 0), total_steps - 1)

        replay_col, step_col, reset_col, status_col = st.columns([1, 1.4, 1, 2.6])
        with replay_col:
            replay_clicked = st.button(
                "Replay",
                icon=":material/replay:",
                width="stretch",
                key="build_week_cpn_replay",
                disabled=total_steps <= 1,
            )
        with step_col:
            step_clicked = st.button(
                "Step by step",
                icon=":material/skip_next:",
                width="stretch",
                key="build_week_cpn_step",
                disabled=total_steps <= 1 or current_step >= total_steps - 1,
            )
        with reset_col:
            reset_clicked = st.button(
                "Reset",
                icon=":material/restart_alt:",
                width="stretch",
                key="build_week_cpn_reset",
                disabled=current_step == 0,
            )
        with status_col:
            status_placeholder = st.empty()

        if reset_clicked:
            st.session_state[state_key] = 0
            st.rerun()
        elif step_clicked:
            st.session_state[state_key] = min(current_step + 1, total_steps - 1)
            st.rerun()

        graph_placeholder = st.empty()

        def render_step(step_index: int) -> None:
            status_placeholder.caption(f"Step {step_index + 1} of {total_steps}")
            with graph_placeholder:
                components_html(
                    render_cpn_graph(run, current_step_index=step_index),
                    height=620,
                    scrolling=False,
                )

        if replay_clicked:
            for replay_step in range(total_steps):
                st.session_state[state_key] = replay_step
                render_step(replay_step)
                time.sleep(0.3)
            st.rerun()
        else:
            render_step(current_step)


def _render_provenance(replay: VerifiedReplay) -> None:
    trace = replay.trace
    promotion = trace["promotion"]
    provenance = {
        "Run ID": trace["run_id"],
        "Captured UTC": trace["created_utc"],
        "Requested model": replay.manifest["requested_model"],
        "Returned model": ", ".join(replay.manifest["returned_models"]),
        "Input tokens": replay.manifest["tokens_in"],
        "Output tokens": replay.manifest["tokens_out"],
        "Originating commit": promotion["originating_commit"],
        "Trace SHA-256": replay.manifest["trace_sha256"],
        "Bundle SHA-256": replay.bundle_sha256,
    }
    st.dataframe(
        [{"Field": key, "Value": str(value)} for key, value in provenance.items()],
        hide_index=True,
        width="stretch",
        column_config={"Value": st.column_config.TextColumn(width="large")},
    )
    st.download_button(
        "Download audit bundle",
        data=build_audit_archive(replay),
        file_name=f"{trace['run_id']}_verified_replay.zip",
        mime="application/zip",
        icon=":material/download:",
        key="build_week_download",
    )


st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.markdown(
    """
    <style>
    .block-container { max-width: 1500px; padding-top: 1.6rem; }
    .bw-mode-band {
      align-items: center;
      border: 1px solid color-mix(in srgb, currentColor 18%, transparent);
      border-left: 5px solid #2f9e67;
      border-radius: 6px;
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem 1.4rem;
      margin: 0.6rem 0 1.4rem;
      padding: 0.75rem 1rem;
    }
    .bw-mode-band.live { border-left-color: #2878c8; }
    .bw-mode-band span { font-size: 0.86rem; opacity: 0.78; }
    [data-testid="stMetric"] { min-height: 104px; }
    [data-testid="stMetricLabel"] { letter-spacing: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    verified_replay = load_verified_replay()
except VerifiedReplayError as exc:
    st.error(f"Verified replay unavailable: {exc}")
    st.stop()

if "build_week_live_run" not in st.session_state:
    st.session_state["build_week_live_run"] = None
if "build_week_prompt_draft" not in st.session_state:
    st.session_state["build_week_prompt_draft"] = verified_replay.pipeline_run.prompt

title_col, mode_col = st.columns([3, 2], vertical_alignment="bottom")
with title_col:
    st.title(PAGE_TITLE)
    st.caption("AXIOM constraint supervision with GPT-5.6")
with mode_col:
    selected_mode = st.segmented_control(
        "Execution mode",
        options=[MODE_REPLAY, MODE_LIVE],
        default=MODE_REPLAY,
        key="build_week_mode",
        width="stretch",
    )
mode = selected_mode or MODE_REPLAY
session_live_run = st.session_state["build_week_live_run"]
live_run = session_live_run if isinstance(session_live_run, PipelineRun) else None
_render_mode_band(mode, verified_replay, live_run)

display_run: PipelineRun | None = verified_replay.pipeline_run if mode == MODE_REPLAY else None
if mode == MODE_LIVE:
    api_ready = bool(os.environ.get("OPENAI_API_KEY"))
    live_prompt = st.text_area(
        "Design request",
        value=st.session_state["build_week_prompt_draft"],
        key="build_week_prompt_input",
        height=125,
    )
    st.session_state["build_week_prompt_draft"] = live_prompt
    live_col, state_col = st.columns([1, 3], vertical_alignment="center")
    with live_col:
        live_clicked = st.button(
            "Run live validation",
            type="primary",
            icon=":material/play_arrow:",
            disabled=not api_ready,
            width="stretch",
        )
    with state_col:
        if api_ready:
            st.caption(
                f"OPENAI_API_KEY detected | {OPENAI_BUILD_WEEK_MODEL} | "
                "maximum 2 AXIOM attempts"
            )
        else:
            st.warning("OPENAI_API_KEY is not available to this process.")
    if live_clicked:
        with st.spinner("Running AXIOM supervision..."):
            st.session_state["build_week_live_run"] = run_live_openai_demo(
                prompt=live_prompt
            )
        st.rerun()
    if live_run is not None:
        display_run = deepcopy(live_run)

if mode == MODE_REPLAY:
    first_attempt, corrected_attempt = verified_replay.attempts
    first_geometry = _geometry(first_attempt)
    corrected_geometry = _geometry(corrected_attempt)

    st.subheader("Constraint correction")
    before_col, after_col = st.columns(2, gap="large")
    with before_col:
        _render_attempt(first_attempt, accepted=False)
    with after_col:
        _render_attempt(corrected_attempt, accepted=True)

    st.error(verified_replay.retry_feedback, icon=":material/rule:")

    delta_a, delta_b, delta_c = st.columns(3)
    delta_a.metric(
        "Diameter correction",
        f"{corrected_geometry['diameter_mm']:.1f} mm",
        delta=f"{corrected_geometry['diameter_mm'] - first_geometry['diameter_mm']:+.1f} mm",
    )
    delta_b.metric(
        "Corrected winding span",
        f"{corrected_geometry['available_winding_mm']:.2f} mm",
        delta=f"{corrected_geometry['available_winding_mm'] - 2.0:+.2f} mm margin",
    )
    delta_c.metric("Failed constraints", "0", delta="CY5 resolved")
elif display_run is not None:
    _render_live_attempts(display_run)
else:
    st.info("No Live OpenAI run exists in this browser session.")

if display_run is not None:
    st.subheader("Accepted result" if display_run.success else "Pipeline result")
    if display_run.success:
        _render_result_metrics(display_run)
    else:
        st.error(display_run.last_error or "The pipeline did not return an accepted design.")

    st.subheader("Supervised pipeline")
    _render_pipeline_views(display_run)

if mode == MODE_REPLAY:
    st.subheader("Trace provenance")
    _render_provenance(verified_replay)
elif display_run is not None:
    st.subheader("Live session details")
    _render_live_session_details(display_run)
st.info(
    "Passing the declared AXIOM constraints does not establish complete physical correctness, "
    "manufacturability, safety, or fitness for production.",
    icon=":material/info:",
)
