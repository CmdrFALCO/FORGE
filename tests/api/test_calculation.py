"""Tests for calculation API route."""

from __future__ import annotations


def _assert_error_envelope(response_json: dict) -> None:
    assert response_json["success"] is False
    assert "error" in response_json
    assert "code" in response_json["error"]
    assert "message" in response_json["error"]
    assert "details" in response_json["error"]


def test_calculate_pouch_success(client, valid_pouch_spec):
    response = client.post("/api/v1/calculate", json={"cell_type": "pouch", "spec": valid_pouch_spec})
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["cell_type"] == "pouch"
    assert isinstance(body["data"]["report"], dict)
    assert body["data"]["report"]


def test_calculate_prismatic_success(client, valid_prismatic_calculation_spec):
    response = client.post(
        "/api/v1/calculate",
        json={"cell_type": "prismatic", "spec": valid_prismatic_calculation_spec},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["cell_type"] == "prismatic"
    assert isinstance(body["data"]["report"], dict)
    assert body["data"]["report"]


def test_calculate_cylindrical_success(client, valid_cylindrical_spec):
    response = client.post(
        "/api/v1/calculate",
        json={"cell_type": "cylindrical", "spec": valid_cylindrical_spec},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["cell_type"] == "cylindrical"
    assert isinstance(body["data"]["report"], dict)
    assert body["data"]["report"]


def test_calculate_report_has_key_fields(client, valid_pouch_spec):
    response = client.post("/api/v1/calculate", json={"cell_type": "pouch", "spec": valid_pouch_spec})
    report = response.json()["data"]["report"]

    for key in ("cell_name", "cell_type", "capacity_ah", "nominal_voltage_v", "gravimetric_ed_whkg"):
        assert key in report


def test_calculate_empty_spec(client):
    response = client.post("/api/v1/calculate", json={"cell_type": "pouch", "spec": {}})
    body = response.json()

    assert response.status_code in (400, 500)
    _assert_error_envelope(body)


def test_calculate_invalid_cell_type(client):
    response = client.post("/api/v1/calculate", json={"cell_type": "hydrogen", "spec": {}})

    assert response.status_code == 400
    _assert_error_envelope(response.json())


def test_calculate_missing_body(client):
    response = client.post("/api/v1/calculate")

    assert response.status_code == 400
    _assert_error_envelope(response.json())

