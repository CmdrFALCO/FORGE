"""Tests for generation and parse API routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def _assert_error_envelope(response_json: dict) -> None:
    assert response_json["success"] is False
    assert "error" in response_json
    assert "code" in response_json["error"]
    assert "message" in response_json["error"]
    assert "details" in response_json["error"]


def test_parse_valid_yaml(client):
    raw_yaml = "```yaml\n_meta:\n  cell_type: prismatic\nenvelope:\n  external:\n    cell_height_mm: 100.0\n```"
    response = client.post("/api/v1/parse", json={"raw_yaml": raw_yaml})
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert isinstance(body["data"]["parsed_spec"], dict)
    assert body["data"]["parsed_spec"]
    assert body["data"]["parse_errors"] == []


def test_parse_invalid_yaml(client):
    response = client.post("/api/v1/parse", json={"raw_yaml": "this is not yaml at all {{{"})
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["parsed_spec"] == {}
    assert len(body["data"]["parse_errors"]) > 0


def test_parse_empty_string(client):
    response = client.post("/api/v1/parse", json={"raw_yaml": ""})
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["parsed_spec"] == {}
    assert len(body["data"]["parse_errors"]) > 0


def test_parse_missing_body(client):
    response = client.post("/api/v1/parse")

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_generate_unknown_backend(client):
    response = client.post("/api/v1/generate", json={"prompt": "test", "backend": "gpt4"})

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_generate_unavailable_backend(client):
    response = client.post("/api/v1/generate", json={"prompt": "test", "backend": "ollama"})

    assert response.status_code in (502, 503)
    _assert_error_envelope(response.json())


def test_generate_missing_prompt(client):
    response = client.post("/api/v1/generate", json={"backend": "ollama"})

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_generate_mocked_success(client):
    mocked_backend = MagicMock()
    mocked_backend.generate.return_value = "```yaml\ncell_type: pouch\n```"
    mocked_backend.model = "mock-llm"

    with patch("forge.api.routes.generation.build_backend", return_value=mocked_backend):
        response = client.post("/api/v1/generate", json={"prompt": "Generate test", "backend": "ollama"})

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert "cell_type: pouch" in body["data"]["raw_yaml"]
    assert body["data"]["model"] == "mock-llm"

