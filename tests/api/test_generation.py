"""Tests for generation and parse API routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import HTTPException


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


def test_generate_openai_routes_messages_and_model_override(client):
    mocked_backend = MagicMock()
    mocked_backend.generate.return_value = "```yaml\ncell_type: prismatic\n```"
    mocked_backend.model = "custom-openai-model"

    with patch(
        "forge.api.routes.generation.build_backend",
        return_value=mocked_backend,
    ) as build_backend:
        response = client.post(
            "/api/v1/generate",
            json={
                "prompt": "Generate a prismatic cell",
                "system_prompt": "Return YAML only",
                "backend": "openai",
                "model": "custom-openai-model",
            },
        )

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["model"] == "custom-openai-model"
    build_backend.assert_called_once_with("openai", model="custom-openai-model")
    mocked_backend.generate.assert_called_once_with(
        [
            {"role": "system", "content": "Return YAML only"},
            {"role": "user", "content": "Generate a prismatic cell"},
        ]
    )


def test_generate_openai_factory_error_maps_to_503(client):
    with patch(
        "forge.api.routes.generation.build_backend",
        side_effect=HTTPException(status_code=503, detail="OpenAI backend unavailable"),
    ):
        response = client.post(
            "/api/v1/generate",
            json={"prompt": "test", "backend": "openai"},
        )

    assert response.status_code == 503
    _assert_error_envelope(response.json())


def test_generate_openai_upstream_error_maps_to_502(client):
    mocked_backend = MagicMock()
    mocked_backend.generate.side_effect = RuntimeError("OpenAI API error: request failed")

    with patch("forge.api.routes.generation.build_backend", return_value=mocked_backend):
        response = client.post(
            "/api/v1/generate",
            json={"prompt": "test", "backend": "openai"},
        )

    body = response.json()
    assert response.status_code == 502
    _assert_error_envelope(body)
    assert "OpenAI API error: request failed" in body["error"]["message"]

