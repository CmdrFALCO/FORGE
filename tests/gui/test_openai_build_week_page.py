"""Offline tests for the OpenAI Build Week Streamlit page."""

import io
import sys
import zipfile
from pathlib import Path
from typing import Any

import streamlit as streamlit_module
from streamlit.testing.v1 import AppTest

from forge.gui import build_week_demo
from forge.gui.axiom_pipeline import PipelineRun, PipelineStep, StepStatus
from forge.gui.verified_replay import REPLAY_FILES, build_audit_archive, load_verified_replay

PAGE_PATH = (
    Path(__file__).resolve().parents[2]
    / "forge"
    / "gui"
    / "pages"
    / "6_OpenAI_Build_Week.py"
)


def test_audit_archive_contains_loadable_verified_bundle(tmp_path: Path) -> None:
    archive_bytes = build_audit_archive(load_verified_replay())

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        assert tuple(archive.namelist()) == REPLAY_FILES
        archive.extractall(tmp_path)

    extracted = load_verified_replay(tmp_path)
    assert extracted.manifest["run_id"] == "20260719_174526Z_p4_gpt56"


def test_build_week_page_defaults_to_verified_replay(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_module)

    app = AppTest.from_file(str(PAGE_PATH), default_timeout=15).run()

    assert not app.exception
    assert app.title[0].value == "FORGE OpenAI Build Week"
    assert any(header.value == "Constraint correction" for header in app.subheader)
    assert any(header.value == "Accepted result" for header in app.subheader)
    assert any(header.value == "Supervised pipeline" for header in app.subheader)
    assert any(header.value == "Trace provenance" for header in app.subheader)
    assert any("Attempt 1 | Rejected" in item.value for item in app.markdown)
    assert any("Attempt 2 | Accepted" in item.value for item in app.markdown)
    assert any("Insufficient space for jelly roll" in item.value for item in app.error)
    assert {"Replay", "Step by step", "Reset"}.issubset(
        {button.label for button in app.button}
    )
    assert not app.slider
    assert len(app.exception) == 0


def test_live_demo_routes_to_bounded_openai_pipeline(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    expected = PipelineRun(prompt="P4", backend_name="openai")

    def fake_pipeline(**kwargs: Any) -> PipelineRun:
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(build_week_demo, "run_pipeline_with_tracking", fake_pipeline)

    result = build_week_demo.run_live_openai_demo("P4")

    assert result is expected
    assert captured == {
        "prompt": "P4",
        "backend": "openai",
        "cell_type": "cylindrical",
        "max_attempts": 2,
        "model": "gpt-5.6",
        "on_step_update": None,
    }


def test_live_attempt_summaries_preserve_failed_attempt_evidence() -> None:
    run = PipelineRun(
        prompt="P4",
        backend_name="OpenAI",
        attempt=2,
        max_attempts=2,
        success=False,
        last_error="Physics validation failed: CY5",
        steps=[
            PipelineStep(
                name="LLM Generate",
                status=StepStatus.PASSED,
                raw_data="attempt 1 output",
                attempt=1,
            ),
            PipelineStep(
                name="Parse YAML",
                status=StepStatus.PASSED,
                raw_data={"raw_yaml": "attempt: 1"},
                attempt=1,
            ),
            PipelineStep(name="Physics Validate", status=StepStatus.FAILED, attempt=1),
            PipelineStep(
                name="Retry Feedback",
                status=StepStatus.PASSED,
                raw_data={"feedback": "Correct CY5"},
                attempt=1,
            ),
            PipelineStep(
                name="LLM Generate",
                status=StepStatus.PASSED,
                raw_data="attempt 2 output",
                attempt=2,
            ),
            PipelineStep(
                name="Parse YAML",
                status=StepStatus.PASSED,
                raw_data={"raw_yaml": "attempt: 2"},
                attempt=2,
            ),
            PipelineStep(name="Physics Validate", status=StepStatus.FAILED, attempt=2),
            PipelineStep(
                name="Retry Feedback",
                status=StepStatus.PASSED,
                raw_data={"feedback": "CY5 still fails"},
                attempt=2,
            ),
        ],
    )

    summaries = build_week_demo.summarize_live_attempts(run)

    assert [summary.attempt for summary in summaries] == [1, 2]
    assert [summary.outcome for summary in summaries] == ["Rejected", "Rejected"]
    assert summaries[0].output_text == "attempt 1 output"
    assert summaries[0].raw_yaml == "attempt: 1"
    assert summaries[0].feedback == "Correct CY5"
    assert summaries[1].output_text == "attempt 2 output"
    assert summaries[1].raw_yaml == "attempt: 2"
    assert summaries[1].feedback == "CY5 still fails"


def test_live_page_shows_session_failure_without_replay_provenance(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_module)
    failed_run = PipelineRun(
        prompt="Persistent P4 prompt",
        backend_name="OpenAI",
        attempt=2,
        max_attempts=2,
        success=False,
        last_error="Physics validation failed: CY5",
        steps=[
            PipelineStep(name="LLM Generate", status=StepStatus.PASSED, attempt=1),
            PipelineStep(name="Parse YAML", status=StepStatus.PASSED, attempt=1),
            PipelineStep(name="Physics Validate", status=StepStatus.FAILED, attempt=1),
            PipelineStep(name="Retry Feedback", status=StepStatus.PASSED, attempt=1),
            PipelineStep(name="LLM Generate", status=StepStatus.PASSED, attempt=2),
            PipelineStep(name="Parse YAML", status=StepStatus.PASSED, attempt=2),
            PipelineStep(name="Physics Validate", status=StepStatus.FAILED, attempt=2),
            PipelineStep(name="Retry Feedback", status=StepStatus.PASSED, attempt=2),
        ],
    )
    app = AppTest.from_file(str(PAGE_PATH), default_timeout=15)
    app.session_state["build_week_mode"] = "Live OpenAI"
    app.session_state["build_week_live_run"] = failed_run
    app.session_state["build_week_prompt_draft"] = "Persistent P4 prompt"

    app.run()

    subheaders = {header.value for header in app.subheader}
    assert "Live attempt history" in subheaders
    assert "Pipeline result" in subheaders
    assert "Supervised pipeline" in subheaders
    assert "Live session details" in subheaders
    assert "Trace provenance" not in subheaders
    assert "Accepted result" not in subheaders
    assert app.text_area[0].value == "Persistent P4 prompt"
    assert any("Physics validation failed: CY5" in item.value for item in app.error)
    assert not app.exception
