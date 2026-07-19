"""Tests for the integrity-checked OpenAI Build Week replay adapter."""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from forge.gui.axiom_pipeline import RETRY_STEP, StepStatus
from forge.gui.components.axiom_cpn import compute_cpn_sequence
from forge.gui.components.axiom_flow import render_pipeline_flow
from forge.gui.verified_replay import (
    VERIFIED_REPLAY_DIR,
    VerifiedReplayError,
    load_verified_replay,
)


def test_verified_replay_loads_canonical_bundle() -> None:
    replay = load_verified_replay()

    assert replay.manifest["run_id"] == "20260719_174526Z_p4_gpt56"
    assert replay.manifest["trace_sha256"] == (
        "f12139e7566451df26ced03e659bd1fe7c08eb539d4a79480007043539c1fb59"
    )
    assert replay.manifest["requested_model"] == "gpt-5.6"
    assert replay.manifest["returned_models"] == ["gpt-5.6-sol"]
    assert replay.bundle_sha256 == (
        "c1e3a0c7d09972de5b2f7ff836a30a2e20ada844a2197638d8ebac0157a5a6ca"
    )
    assert [attempt["validation"]["classification"] for attempt in replay.attempts] == [
        "engineering",
        "accepted",
    ]


def test_verified_replay_projects_complete_retry_pipeline() -> None:
    replay = load_verified_replay()
    run = replay.pipeline_run

    assert run.prompt == replay.trace["candidate"]["prompt"]
    assert run.backend_name == "OpenAI gpt-5.6 | Verified Replay"
    assert run.cell_type == "cylindrical"
    assert run.attempt == run.max_attempts == 2
    assert run.success is True
    assert run.total_duration_ms == 0.0
    assert run.yaml_content == replay.attempts[1]["validation"]["raw_yaml"]

    physics_steps = [step for step in run.steps if step.name == "Physics Validate"]
    assert [step.status for step in physics_steps] == [StepStatus.FAILED, StepStatus.PASSED]
    assert physics_steps[0].raw_data["failed_constraint_ids"] == ["CY5"]
    assert physics_steps[1].raw_data["failed_constraint_ids"] == []
    assert run.steps[-2].name == "Convert"
    assert run.steps[-1].name == "Calculate"


def test_verified_replay_preserves_exact_feedback_and_metrics() -> None:
    replay = load_verified_replay()
    run = replay.pipeline_run
    retry_step = next(step for step in run.steps if step.name == RETRY_STEP)
    expected_feedback = replay.attempts[0]["supervisor"]["retry_reasons"][0]

    assert replay.retry_feedback == expected_feedback
    assert run.retry_reasons == [expected_feedback]
    assert retry_step.raw_data["feedback"] == expected_feedback
    assert expected_feedback in retry_step.raw_data["retry_prompt"]
    assert run.calculation_summary == {
        "attempt": 2,
        "capacity_ah": 0.2915229951092681,
        "energy_wh": 1.0494827823933652,
        "total_mass_g": 7.3874128464133175,
        "gravimetric_ed_whkg": 142.99237189687867,
        "volumetric_ed_cell_whl": 269.3359496219542,
    }


def test_verified_replay_projection_supports_existing_renderers() -> None:
    run = load_verified_replay().pipeline_run

    html = render_pipeline_flow(run)
    sequence = compute_cpn_sequence(run)

    assert "Attempt 2 of 2" in html
    assert "Retry Loop" in html
    assert "jelly roll" in html
    assert sequence[-1]["token_place"] == "P_result"
    assert sequence[-1]["attempt"] == 2
    assert any(snapshot["transition_id"] == "T_retry" for snapshot in sequence)


def test_verified_replay_rejects_outer_bundle_tampering(tmp_path: Path) -> None:
    bundle = _copy_bundle(tmp_path)
    trace_path = bundle / "trace.json"
    trace_path.write_text(trace_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(VerifiedReplayError, match="Trace hash"):
        load_verified_replay(bundle)


def test_verified_replay_rejects_inner_attempt_tampering(tmp_path: Path) -> None:
    bundle = _copy_bundle(tmp_path)
    trace_path = bundle / "trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    trace["attempts"][0]["output_text"] += "\n"
    _rewrite_outer_hashes(bundle, trace)

    with pytest.raises(VerifiedReplayError, match="Attempt 1 output hash"):
        load_verified_replay(bundle)


def test_verified_replay_contains_no_response_identifiers() -> None:
    replay = load_verified_replay()

    assert not _has_key(replay.trace, "response_id")
    assert replay.trace["promotion"]["removed_response_identifiers"] == 2


def _copy_bundle(tmp_path: Path) -> Path:
    destination = tmp_path / "replay"
    shutil.copytree(VERIFIED_REPLAY_DIR, destination)
    return destination


def _rewrite_outer_hashes(bundle: Path, trace: dict[str, Any]) -> None:
    trace_text = json.dumps(trace, indent=2, ensure_ascii=False) + "\n"
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["trace_sha256"] = _sha256(trace_text)
    manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    (bundle / "trace.json").write_text(trace_text, encoding="utf-8")
    manifest_path.write_text(manifest_text, encoding="utf-8")
    (bundle / "BUNDLE_SHA256.txt").write_text(
        _sha256(trace_text + manifest_text) + "\n", encoding="utf-8"
    )


def _has_key(value: Any, key_name: str) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() == key_name or _has_key(child, key_name)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_has_key(child, key_name) for child in value)
    return False


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
