"""Shared fixtures for API tests."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from forge.api.app import app
from tests.axiom.test_cylindrical_support import VALID_CYLINDRICAL_CELL
from tests.axiom.test_pouch_support import VALID_POUCH_CELL

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"

VALID_PRISMATIC_VALIDATION_SPEC: dict[str, Any] = {
    "envelope": {
        "external": {
            "cell_height_mm": 88.8,
            "cell_width_mm": 264.6,
            "cell_thickness_mm": 29.6,
        },
        "walls": {
            "wall_top_mm": 2.0,
            "wall_bottom_mm": 1.0,
            "wall_front_back_mm": 0.5,
            "wall_sides_mm": 0.7,
        },
        "internals": {
            "insulation_coating_um": 85.0,
            "external_corner_radius_mm": 3.0,
            "internal_corner_radius_mm": 1.5,
        },
    },
    "stack_config": {
        "architecture": {
            "num_stacks": 2,
            "electrode_pairs_per_stack": 44,
            "end_electrode_config": "BothNegative",
        },
        "sheet_geometry": {
            "cathode_height_mm": 74.0,
            "cathode_width_mm": 251.7,
            "anode_offset_top_mm": 2.0,
            "anode_offset_bottom_mm": 2.0,
            "anode_offset_left_mm": 2.0,
            "anode_offset_right_mm": 2.0,
            "separator_offset_top_mm": 2.0,
            "separator_offset_bottom_mm": 2.0,
            "separator_offset_left_mm": 2.0,
            "separator_offset_right_mm": 2.0,
        },
    },
    "electrochemistry": {
        "cathode": {
            "material_name": "NCM",
            "loading_mg_cm2": 19.674,
            "rev_spec_capacity_mahg": 193.814,
            "collector_thickness_um": 12.0,
            "coating_thickness_0pct_um": 58.24,
            "coating_thickness_100pct_um": 57.08,
            "porosity_pct": 25.36,
        },
        "anode": {
            "material_name": "Graphite",
            "loading_mg_cm2": 11.478,
            "rev_spec_capacity_mahg": 331.161,
            "collector_thickness_um": 6.0,
            "coating_thickness_0pct_um": 85.47,
            "coating_thickness_100pct_um": 92.31,
            "porosity_pct": 38.01,
            "np_ratio": 1.225,
        },
        "separator": {
            "material_name": "PP",
            "thickness_um": 13.0,
            "porosity_pct": 42.646,
            "areal_weight_mgcm2": 1.25,
        },
        "electrolyte": {
            "material_name": "LiPF6",
            "salt_concentration_m": 1.2,
            "density_g_cm3": 1.223,
            "excess_factor": 1.0,
        },
    },
    "current_collection": {
        "tabs": {
            "cathode": {
                "material": "Aluminum",
                "height_mm": 40.0,
                "width_mm": 50.0,
                "thickness_mm": 0.3,
            },
            "anode": {
                "material": "Copper",
                "height_mm": 40.0,
                "width_mm": 50.0,
                "thickness_mm": 0.2,
            },
        }
    },
    "packaging": {
        "housing": {
            "case_material": "Aluminum",
            "case_density_g_cm3": 2.7,
            "lid_thickness_mm": 2.0,
        },
        "insulation": {
            "shell_thickness_um": 120.0,
            "shell_count": 2,
            "fixing_tape_width_mm": 30.0,
            "fixing_tape_count": 4,
        },
    },
}

VALID_PRISMATIC_CALCULATION_SPEC: dict[str, Any] = {
    "cell_name": "Test_Prismatic_V1",
    "envelope": {
        "cell_height_mm": 88.8,
        "cell_width_mm": 264.6,
        "cell_thickness_mm": 29.6,
        "wall_top_mm": 2.0,
        "wall_bottom_mm": 1.0,
        "wall_front_back_mm": 0.5,
        "wall_sides_mm": 0.7,
    },
    "stack_config": {
        "stacks": 2,
        "pairs": 22,
        "end_electrodes": "BothNegative",
        "sheet_geometry": {
            "cathode_height_mm": 200.0,
            "cathode_width_mm": 100.0,
            "anode_offset_top_mm": 2.0,
            "anode_offset_bottom_mm": 2.0,
            "anode_offset_left_mm": 2.0,
            "anode_offset_right_mm": 2.0,
            "separator_offset_top_mm": 2.0,
            "separator_offset_bottom_mm": 2.0,
            "separator_offset_left_mm": 2.0,
            "separator_offset_right_mm": 2.0,
        },
    },
    "electrochemistry": {
        "cathode": {
            "name": "NCM811_Cathode",
            "loading_mg_cm2": 120.5,
            "rev_spec_capacity_mahg": 200.0,
            "collector_thickness_um": 15.0,
            "coating_density_gcm3": 3.2,
            "coating_thickness_0pct_um": 37.6,
            "coating_thickness_100pct_um": 32.1,
        },
        "anode": {
            "name": "Graphite_Anode",
            "loading_mg_cm2": 66.8,
            "rev_spec_capacity_mahg": 372.0,
            "collector_thickness_um": 10.0,
            "coating_density_gcm3": 1.8,
            "coating_thickness_0pct_um": 37.2,
            "coating_thickness_100pct_um": 32.3,
            "np_ratio": 1.22,
        },
        "separator": {
            "name": "PP_Separator",
            "thickness_um": 25.0,
            "porosity_pct": 50.0,
            "areal_weight_mgcm2": 1.14,
        },
        "electrolyte": {
            "name": "EC_DMC_1M_LiPF6",
            "density_gcm3": 1.21,
        },
    },
}


def _normalize_cell_type(raw_value: Any, fallback_name: str) -> str:
    value = str(raw_value or "").strip().lower()
    if "pouch" in value:
        return "pouch"
    if "prismatic" in value:
        return "prismatic"
    if "cyl" in value:
        return "cylindrical"

    fallback = fallback_name.lower()
    if "pouch" in fallback:
        return "pouch"
    if "prismatic" in fallback:
        return "prismatic"
    if "cyl" in fallback or "18650" in fallback or "21700" in fallback or "4680" in fallback:
        return "cylindrical"
    return "unknown"


def _load_reference_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for path in sorted(REFERENCE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        metadata = payload.get("metadata", {})
        cell_type = _normalize_cell_type(
            metadata.get("cell_type") or payload.get("cell_type"),
            fallback_name=path.stem,
        )
        if cell_type in ("pouch", "prismatic", "cylindrical") and cell_type not in specs:
            specs[cell_type] = payload
    return specs


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def reference_specs_by_type() -> dict[str, dict[str, Any]]:
    return _load_reference_specs()


@pytest.fixture
def sample_pouch_spec(reference_specs_by_type: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if "pouch" not in reference_specs_by_type:
        pytest.skip("No pouch reference cell found")
    return {"cell_type": "pouch", "spec": deepcopy(reference_specs_by_type["pouch"])}


@pytest.fixture
def sample_prismatic_spec(reference_specs_by_type: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if "prismatic" not in reference_specs_by_type:
        pytest.skip("No prismatic reference cell found")
    return {"cell_type": "prismatic", "spec": deepcopy(reference_specs_by_type["prismatic"])}


@pytest.fixture
def sample_cylindrical_spec(reference_specs_by_type: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if "cylindrical" not in reference_specs_by_type:
        pytest.skip("No cylindrical reference cell found")
    return {"cell_type": "cylindrical", "spec": deepcopy(reference_specs_by_type["cylindrical"])}


@pytest.fixture
def valid_pouch_spec() -> dict[str, Any]:
    return deepcopy(VALID_POUCH_CELL)


@pytest.fixture
def valid_cylindrical_spec() -> dict[str, Any]:
    return deepcopy(VALID_CYLINDRICAL_CELL)


@pytest.fixture
def valid_prismatic_validation_spec() -> dict[str, Any]:
    return deepcopy(VALID_PRISMATIC_VALIDATION_SPEC)


@pytest.fixture
def valid_prismatic_calculation_spec() -> dict[str, Any]:
    return deepcopy(VALID_PRISMATIC_CALCULATION_SPEC)

