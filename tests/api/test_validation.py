"""Tests for validation API route."""

from __future__ import annotations

from copy import deepcopy


def _assert_error_envelope(response_json: dict) -> None:
    assert response_json["success"] is False
    assert "error" in response_json
    assert "code" in response_json["error"]
    assert "message" in response_json["error"]
    assert "details" in response_json["error"]


def test_validate_pouch_valid(client, valid_pouch_spec):
    response = client.post("/api/v1/validate", json={"cell_type": "pouch", "spec": valid_pouch_spec})
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["valid"] is True
    assert body["data"]["errors"] == []


def test_validate_prismatic_valid(client, valid_prismatic_validation_spec):
    response = client.post(
        "/api/v1/validate",
        json={"cell_type": "prismatic", "spec": valid_prismatic_validation_spec},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["valid"] is True
    assert body["data"]["errors"] == []


def test_validate_cylindrical_valid(client, valid_cylindrical_spec):
    response = client.post(
        "/api/v1/validate",
        json={"cell_type": "cylindrical", "spec": valid_cylindrical_spec},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["valid"] is True
    assert body["data"]["errors"] == []


def test_validate_invalid_spec(client, valid_pouch_spec):
    invalid_spec = deepcopy(valid_pouch_spec)
    invalid_spec["electrochemistry"]["anode"]["np_ratio"] = 0.5

    response = client.post("/api/v1/validate", json={"cell_type": "pouch", "spec": invalid_spec})
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["valid"] is False
    assert len(body["data"]["errors"]) > 0


def test_validate_empty_spec(client):
    response = client.post("/api/v1/validate", json={"cell_type": "pouch", "spec": {}})
    body = response.json()

    if response.status_code == 200:
        assert body["success"] is True
        assert body["data"]["valid"] is False
        assert len(body["data"]["errors"]) > 0
    else:
        _assert_error_envelope(body)


def test_validate_missing_cell_type(client):
    response = client.post("/api/v1/validate", json={"spec": {}})

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_validate_invalid_cell_type(client):
    response = client.post("/api/v1/validate", json={"cell_type": "hydrogen", "spec": {}})

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_validate_missing_body(client):
    response = client.post("/api/v1/validate")

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_validate_error_envelope(client):
    response = client.post("/api/v1/validate", json={"cell_type": "hydrogen", "spec": {}})
    body = response.json()

    assert response.status_code == 400
    _assert_error_envelope(body)

