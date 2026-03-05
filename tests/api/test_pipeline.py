"""Tests for pipeline API route."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from forge.axiom.supervisor.result import GenerationResult
from forge.engine.models.results import CellReport


def _assert_error_envelope(response_json: dict) -> None:
    assert response_json["success"] is False
    assert "error" in response_json
    assert "code" in response_json["error"]
    assert "message" in response_json["error"]
    assert "details" in response_json["error"]


def _sample_report() -> CellReport:
    return CellReport(
        cell_name="Mock Cell",
        cell_type="Pouch",
        cell_height_mm=200.0,
        cell_width_mm=100.0,
        cell_thickness_dry_mm=6.0,
        cell_thickness_soc0_mm=6.12,
        cell_thickness_soc100_mm=6.3,
        volume_cell_cm3=122.4,
        volume_stack_cm3=100.0,
        cathode_sheets=15,
        anode_sheets=16,
        separator_sheets=32,
        cathode_coating_mass_g=100.0,
        cathode_collector_mass_g=10.0,
        anode_coating_mass_g=60.0,
        anode_collector_mass_g=25.0,
        separator_mass_g=6.0,
        electrolyte_mass_g=50.0,
        housing_mass_g=15.0,
        tabs_mass_g=3.0,
        capacity_ah=10.0,
        nominal_voltage_v=3.65,
        gravimetric_ed_whkg=120.0,
        volumetric_ed_cell_whl=300.0,
        volumetric_ed_stack_whl=365.0,
        areal_capacity_mahcm2=5.0,
        areal_energy_mwhcm2=18.25,
    )


def test_pipeline_unknown_backend(client):
    response = client.post("/api/v1/pipeline", json={"prompt": "test", "backend": "gpt4"})

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_pipeline_missing_prompt(client):
    response = client.post("/api/v1/pipeline", json={"backend": "ollama"})

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_pipeline_unavailable_backend(client):
    response = client.post("/api/v1/pipeline", json={"prompt": "test", "backend": "ollama"})

    assert response.status_code in (502, 503)
    _assert_error_envelope(response.json())


def test_pipeline_mocked_success(client):
    mocked_result = GenerationResult(
        success=True,
        attempts=1,
        calculation_result=_sample_report(),
        retry_reasons=[],
    )

    with (
        patch("forge.api.routes.pipeline.build_backend", return_value=MagicMock()),
        patch(
            "forge.api.routes.pipeline.supervisor_driver.generate_cell_design",
            return_value=mocked_result,
        ),
    ):
        response = client.post("/api/v1/pipeline", json={"prompt": "test", "backend": "ollama"})

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["final_valid"] is True
    assert body["data"]["total_attempts"] == 1
    assert isinstance(body["data"]["result"], dict)
    assert body["data"]["result"]


def test_pipeline_mocked_failure(client):
    mocked_result = GenerationResult(
        success=False,
        attempts=3,
        retry_reasons=["Schema validation failed", "Physics validation failed"],
        last_error="Validation failed after retries",
    )

    with (
        patch("forge.api.routes.pipeline.build_backend", return_value=MagicMock()),
        patch(
            "forge.api.routes.pipeline.supervisor_driver.generate_cell_design",
            return_value=mocked_result,
        ),
    ):
        response = client.post("/api/v1/pipeline", json={"prompt": "test", "backend": "ollama"})

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["final_valid"] is False
    assert body["data"]["total_attempts"] == 3
    assert len(body["data"]["attempts"]) >= 2


def test_pipeline_mocked_infra_error(client):
    with (
        patch("forge.api.routes.pipeline.build_backend", return_value=MagicMock()),
        patch(
            "forge.api.routes.pipeline.supervisor_driver.generate_cell_design",
            side_effect=RuntimeError("Backend unavailable"),
        ),
    ):
        response = client.post("/api/v1/pipeline", json={"prompt": "test", "backend": "ollama"})

    assert response.status_code == 502
    _assert_error_envelope(response.json())


def test_pipeline_mocked_generation_error_mapping(client):
    mocked_result = GenerationResult(
        success=False,
        attempts=1,
        retry_reasons=["Generation error: upstream timeout"],
        last_error="Generation error: upstream timeout",
    )

    with (
        patch("forge.api.routes.pipeline.build_backend", return_value=MagicMock()),
        patch(
            "forge.api.routes.pipeline.supervisor_driver.generate_cell_design",
            return_value=mocked_result,
        ),
    ):
        response = client.post("/api/v1/pipeline", json={"prompt": "test", "backend": "ollama"})

    assert response.status_code == 502
    _assert_error_envelope(response.json())

