"""Offline tests for the bounded OpenAI failure-discovery runner."""

from __future__ import annotations

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
import yaml

from experiments.axiom.runners import discover_openai_failures as discovery
from forge.axiom.backends.backends import LLMUsage
from forge.axiom.supervisor import driver as supervisor_driver
from tests.axiom.test_cylindrical_support import VALID_CYLINDRICAL_CELL_BALANCED


def _yaml_response(cell: dict) -> str:
    return f"```yaml\n{yaml.safe_dump(cell, sort_keys=False)}```"


def _accepted_response() -> str:
    return _yaml_response(deepcopy(VALID_CYLINDRICAL_CELL_BALANCED))


def _c1_failure_response() -> str:
    cell = deepcopy(VALID_CYLINDRICAL_CELL_BALANCED)
    cell["electrochemistry"]["anode"]["loading_mg_cm2"] = 16.0
    cell["electrochemistry"]["anode"]["np_ratio"] = 1.3
    return _yaml_response(cell)


def _trace() -> dict:
    return {
        "schema_version": 1,
        "run_id": "test-run",
        "created_utc": "2026-07-19T00:00:00Z",
        "updated_utc": None,
        "source": "live_gpt56",
        "mode": "failure_discovery",
        "git": {"branch": "build-week/openai", "head": "abc123", "clean": True},
        "settings": {
            "max_output_tokens": 4096,
            "timeout_seconds": 120.0,
            "transport_max_retries": 0,
        },
        "candidate": {
            "id": "TEST",
            "cell_type": "cylindrical",
            "target_constraints": ["C1"],
            "prompt": "Design a test cell.",
            "requested_model": "gpt-5.6",
        },
        "attempts": [],
        "latest_classification": None,
        "latest_failed_constraint_ids": [],
    }


class FakeLiveBackend:
    def __init__(self, response: str, model: str = "gpt-5.6-2026-07-19") -> None:
        self.response = response
        self.calls: list[list[dict[str, str]]] = []
        self.last_usage = LLMUsage()
        self.model = model

    def generate(self, messages: list[dict[str, str]]) -> str:
        self.calls.append([dict(message) for message in messages])
        self.last_usage = LLMUsage(
            tokens_in=101,
            tokens_out=202,
            model=self.model,
            raw_response=SimpleNamespace(id=f"resp-{len(self.calls)}"),
        )
        return self.response


def test_candidate_registry_contains_reviewed_prompts() -> None:
    candidates = discovery.load_candidates()

    assert list(candidates) == ["P1", "P2", "P3", "P4", "P5"]
    assert candidates["P1"]["target_constraints"] == ["C1"]
    assert candidates["P3"]["target_constraints"] == ["CY5"]
    assert candidates["P4"]["target_constraints"] == ["CY5"]
    assert candidates["P5"]["target_constraints"] == ["PO3"]
    assert candidates["P5"]["cell_type"] == "pouch"
    assert {candidate["requested_model"] for candidate in candidates.values()} == {"gpt-5.6"}


def test_revised_candidates_do_not_explicitly_request_constraint_failures() -> None:
    candidates = discovery.load_candidates()

    for candidate_id in ("P4", "P5"):
        candidate = candidates[candidate_id]
        prompt = candidate["prompt"].lower()
        assert all(constraint_id.lower() not in prompt for constraint_id in candidate["target_constraints"])
        assert "violate" not in prompt
        assert "must fail" not in prompt


def test_first_attempt_classifies_isolated_engineering_failure() -> None:
    trace = _trace()
    backend = FakeLiveBackend(_c1_failure_response())
    original_limit = supervisor_driver.MAX_RETRIES

    discovery.execute_one_attempt(trace, backend)

    assert len(backend.calls) == 1
    assert len(trace["attempts"]) == 1
    assert trace["latest_classification"] == "engineering"
    assert trace["latest_failed_constraint_ids"] == ["C1"]
    assert trace["attempts"][0]["source"] == "live_gpt56"
    assert trace["attempts"][0]["usage"] == {
        "tokens_in": 101,
        "tokens_out": 202,
        "model": "gpt-5.6-2026-07-19",
        "response_id": "resp-1",
    }
    assert "PHYSICS LEVEL" in trace["attempts"][0]["supervisor"]["retry_reasons"][0]
    assert backend.last_usage.raw_response is None
    assert supervisor_driver.MAX_RETRIES == original_limit


def test_continuation_replays_first_attempt_and_delegates_once() -> None:
    trace = _trace()
    discovery.execute_one_attempt(trace, FakeLiveBackend(_c1_failure_response()))
    backend = FakeLiveBackend(_accepted_response())

    discovery.execute_one_attempt(trace, backend)

    assert len(backend.calls) == 1
    assert len(trace["attempts"]) == 2
    assert trace["latest_classification"] == "accepted"
    assert trace["latest_failed_constraint_ids"] == []
    assert [message["role"] for message in backend.calls[0]] == [
        "system",
        "user",
        "assistant",
        "user",
    ]
    assert "PHYSICS LEVEL" in backend.calls[0][-1]["content"]
    assert trace["attempts"][1]["message_sha256"] == discovery.sha256_text(
        discovery.canonical_json(backend.calls[0])
    )


def test_replay_message_drift_blocks_live_delegate() -> None:
    trace = _trace()
    discovery.execute_one_attempt(trace, FakeLiveBackend(_c1_failure_response()))
    trace["attempts"][0]["message_sha256"] = "incorrect"
    backend = FakeLiveBackend(_accepted_response())

    with pytest.raises(discovery.TraceIntegrityError, match="hash mismatch"):
        discovery.execute_one_attempt(trace, backend)

    assert backend.calls == []
    assert len(trace["attempts"]) == 1


def test_replay_output_drift_blocks_live_delegate() -> None:
    trace = _trace()
    discovery.execute_one_attempt(trace, FakeLiveBackend(_c1_failure_response()))
    trace["attempts"][0]["output_text"] = _accepted_response()
    backend = FakeLiveBackend(_accepted_response())

    with pytest.raises(discovery.TraceIntegrityError, match="output hash mismatch"):
        discovery.execute_one_attempt(trace, backend)

    assert backend.calls == []
    assert len(trace["attempts"]) == 1


def test_classify_output_distinguishes_primary_categories() -> None:
    parse = discovery.classify_output("not yaml", "cylindrical")
    schema = discovery.classify_output("```yaml\n_meta: {}\n```", "cylindrical")
    engineering = discovery.classify_output(_c1_failure_response(), "cylindrical")
    accepted = discovery.classify_output(_accepted_response(), "cylindrical")

    assert parse["classification"] == "parse"
    assert schema["classification"] == "schema"
    assert engineering["classification"] == "engineering"
    assert engineering["failed_constraint_ids"] == ["C1"]
    assert accepted["classification"] == "accepted"


def test_request_ledger_enforces_kind_and_total_limits(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(discovery, "STAGING_ROOT", tmp_path)

    for index in range(5):
        discovery.reserve_call("discovery", f"run-d{index}", f"P{index}", 1)
    with pytest.raises(discovery.BudgetError, match="discovery request budget"):
        discovery.reserve_call("discovery", "run-extra", "PX", 1)

    discovery.reserve_call("correction", "run-c0", "P1", 2)
    with pytest.raises(discovery.BudgetError, match="6-request"):
        discovery.reserve_call("correction", "run-extra", "P1", 3)

    ledger = discovery._read_ledger()
    assert len(ledger["entries"]) == 6
    assert all(entry["status"] == "reserved" for entry in ledger["entries"])


def test_discovery_closes_after_correction_begins(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(discovery, "STAGING_ROOT", tmp_path)
    discovery.reserve_call("discovery", "run-d0", "P4", 1)
    discovery.reserve_call("correction", "run-c0", "P4", 2)

    with pytest.raises(discovery.BudgetError, match="closed after a correction"):
        discovery.reserve_call("discovery", "run-d1", "P5", 1)


def test_revised_campaign_allows_only_one_correction(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(discovery, "STAGING_ROOT", tmp_path)
    discovery.reserve_call("discovery", "run-d0", "P4", 1)
    discovery.reserve_call("correction", "run-c0", "P4", 2)

    with pytest.raises(discovery.BudgetError, match="correction request budget"):
        discovery.reserve_call("correction", "run-c1", "P4", 3)


def test_duplicate_discovery_prompt_is_refused(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(discovery, "STAGING_ROOT", tmp_path)
    discovery.reserve_call("discovery", "run-1", "P1", 1)

    with pytest.raises(discovery.BudgetError, match="already consumed"):
        discovery.reserve_call("discovery", "run-2", "P1", 1)


def test_bundle_contains_allowlisted_manifest_and_hashes(tmp_path) -> None:
    trace = _trace()
    discovery.execute_one_attempt(trace, FakeLiveBackend(_c1_failure_response()))

    discovery.write_bundle(tmp_path, trace)

    saved_trace = json.loads((tmp_path / "trace.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["trace_sha256"] == discovery.sha256_text(
        (tmp_path / "trace.json").read_text(encoding="utf-8")
    )
    assert manifest["redaction_check"] == "passed"
    assert manifest["attempt_count"] == 1
    assert manifest["prompt_sha256"] == discovery.sha256_text(
        trace["candidate"]["prompt"]
    )
    assert len(manifest["system_prompt_sha256"]) == 64
    assert manifest["returned_models"] == ["gpt-5.6-2026-07-19"]
    assert saved_trace["attempts"][0]["usage"].get("raw_response") is None
    assert len((tmp_path / "BUNDLE_SHA256.txt").read_text(encoding="utf-8").strip()) == 64


def test_load_trace_rejects_tampered_bundle(tmp_path, monkeypatch) -> None:
    trace = _trace()
    discovery.execute_one_attempt(trace, FakeLiveBackend(_c1_failure_response()))
    run_dir = tmp_path / trace["run_id"]
    discovery.write_bundle(run_dir, trace)
    monkeypatch.setattr(discovery, "STAGING_ROOT", tmp_path)

    trace_path = run_dir / "trace.json"
    trace_path.write_text(
        trace_path.read_text(encoding="utf-8").replace("Design a test cell.", "Changed."),
        encoding="utf-8",
    )

    with pytest.raises(discovery.TraceIntegrityError, match="trace hash"):
        discovery.load_trace(trace["run_id"])


@pytest.mark.parametrize("run_id", ["", ".", "..", "../outside", "nested/run"])
def test_load_trace_rejects_unsafe_run_id(tmp_path, monkeypatch, run_id) -> None:
    monkeypatch.setattr(discovery, "STAGING_ROOT", tmp_path)

    with pytest.raises(discovery.DiscoveryError, match="Invalid staged run"):
        discovery.load_trace(run_id)


@pytest.mark.parametrize(
    "payload",
    [
        {"api_key": "not-allowed"},
        {"attempts": [{"output_text": "sk-proj-" + "a" * 32}]},
        {"attempts": [{"output_text": "Authorization: Bearer secret"}]},
    ],
)
def test_redaction_rejects_forbidden_fields_and_values(payload) -> None:
    with pytest.raises(discovery.TraceIntegrityError):
        discovery._assert_redacted(payload)


def test_telemetry_validation_rejects_missing_or_unexpected_values() -> None:
    trace = _trace()
    trace["attempts"] = [
        {
            "usage": {
                "tokens_in": 0,
                "tokens_out": 0,
                "model": "unexpected-model",
            }
        }
    ]

    with pytest.raises(discovery.DiscoveryError, match="model telemetry"):
        discovery._validate_telemetry(trace)

    assert trace["latest_classification"] == "telemetry"


def test_live_preflight_rejects_dirty_or_drifted_repository(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setattr(
        discovery,
        "git_state",
        lambda: {"branch": "build-week/openai", "head": "head-1", "clean": False},
    )
    with pytest.raises(discovery.DiscoveryError, match="clean working tree"):
        discovery.require_live_preflight()

    monkeypatch.setattr(
        discovery,
        "git_state",
        lambda: {"branch": "build-week/openai", "head": "head-2", "clean": True},
    )
    with pytest.raises(discovery.TraceIntegrityError, match="differs"):
        discovery.require_live_preflight(expected_head="head-1")


def test_continue_refuses_non_engineering_trace(tmp_path, monkeypatch) -> None:
    trace = _trace()
    trace["latest_classification"] = "schema"
    monkeypatch.setattr(discovery, "load_trace", lambda _: (tmp_path, trace))
    monkeypatch.setattr(discovery, "require_live_preflight", lambda expected_head=None: trace["git"])
    args = SimpleNamespace(run_id="test-run")

    with pytest.raises(discovery.DiscoveryError, match="engineering failure"):
        discovery.command_continue(args)


def test_main_sanitizes_unexpected_errors(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        discovery,
        "load_candidates",
        lambda: (_ for _ in ()).throw(RuntimeError("sensitive unexpected detail")),
    )

    assert discovery.main(["list"]) == 1
    captured = capsys.readouterr()
    assert captured.err.strip() == "ERROR: Discovery command failed."
    assert "sensitive" not in captured.err
