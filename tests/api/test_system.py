"""Tests for system API routes."""

from __future__ import annotations


def test_health_returns_200(client):
    response = client.get("/api/v1/health")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True


def test_health_response_shape(client):
    response = client.get("/api/v1/health")
    body = response.json()
    data = body["data"]

    assert body["success"] is True
    assert data["status"] == "ok"
    assert isinstance(data["version"], str)
    assert isinstance(data["backends_available"], list)


def test_health_root_alias(client):
    alias_response = client.get("/health")
    versioned_response = client.get("/api/v1/health")

    assert alias_response.status_code == 200
    assert versioned_response.status_code == 200
    assert alias_response.json()["success"] is True
    assert versioned_response.json()["success"] is True
    assert alias_response.json()["data"]["status"] == versioned_response.json()["data"]["status"]


def test_reference_cells_returns_200(client):
    response = client.get("/api/v1/reference-cells")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True


def test_reference_cells_metadata_shape(client):
    response = client.get("/api/v1/reference-cells")
    cells = response.json()["data"]["cells"]

    assert cells, "Expected at least one reference cell"
    sample = cells[0]
    for key in ("id", "name", "cell_type", "chemistry", "tier", "source", "data"):
        assert key in sample
    assert sample["data"] is None


def test_reference_cells_count(client):
    response = client.get("/api/v1/reference-cells")
    payload = response.json()["data"]

    assert payload["count"] == len(payload["cells"])
    assert payload["count"] > 0


def test_reference_cells_full_param(client):
    response = client.get("/api/v1/reference-cells?full=true")
    cells = response.json()["data"]["cells"]

    assert cells, "Expected at least one reference cell"
    assert isinstance(cells[0]["data"], dict)


def test_reference_cells_cell_types_present(client):
    response = client.get("/api/v1/reference-cells")
    cells = response.json()["data"]["cells"]
    cell_types = {cell["cell_type"] for cell in cells}

    assert {"pouch", "prismatic", "cylindrical"}.issubset(cell_types)

