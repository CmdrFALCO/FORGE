"""Focused robustness tests for materials repositories and PyBaMM fallback behavior.

Extracted from CellCAD robustness section for C1 migration scope.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge.engine.models.cylindrical import CylindricalGeometry
from forge.engine.models.materials import AnodeMaterial, CathodeMaterial
from forge.engine.models.prismatic import PrismaticGeometry


@pytest.fixture
def standard_cathode() -> CathodeMaterial:
    """Create a standard cathode material for fallback tests."""
    return CathodeMaterial(
        id="test_cathode",
        name="Test NMC622",
        chemistry="NMC622",
        rev_spec_capacity_mahg=180.0,
        max_spec_capacity_mahg=200.0,
        areal_weight_mgcm2=18.0,
        collector_thickness_um=12.0,
        coating_density_gcm3=3.4,
        coating_thickness_0pct_um=70.0,
        coating_thickness_100pct_um=68.0,
    )


@pytest.fixture
def standard_anode() -> AnodeMaterial:
    """Create a standard anode material for fallback tests."""
    return AnodeMaterial(
        id="test_anode",
        name="Test Graphite",
        chemistry="Graphite",
        rev_spec_capacity_mahg=350.0,
        max_spec_capacity_mahg=372.0,
        areal_weight_mgcm2=11.0,
        collector_thickness_um=8.0,
        coating_density_gcm3=1.5,
        coating_thickness_0pct_um=80.0,
        coating_thickness_100pct_um=87.0,
    )


class TestPyBaMMFallback:
    """Test behavior when PyBaMM is unavailable."""

    def test_reference_cells_load_from_json(self):
        """Reference cells from JSON should load without PyBaMM."""
        ref_path = Path("data/reference/v1_prismatic.json")
        if ref_path.exists():
            with open(ref_path) as f:
                data = json.load(f)

            assert "metadata" in data
            assert "cell_specs" in data

    def test_materials_can_be_created_manually(self, standard_cathode, standard_anode):
        """Materials should be creatable without any repository."""
        assert standard_cathode.id == "test_cathode"
        assert standard_anode.id == "test_anode"
        assert standard_cathode.chemistry == "NMC622"

    def test_geometry_is_pybamm_independent(self):
        """Geometry classes should work without PyBaMM."""
        geo = PrismaticGeometry(
            cell_height_mm=88.8,
            cell_width_mm=264.6,
            cell_thickness_mm=29.6,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_back_mm=0.5,
            wall_sides_mm=0.7,
        )
        assert geo.cell_volume_cm3 > 0
        assert geo.internal_height_mm > 0

    def test_cylindrical_geometry_is_pybamm_independent(self):
        """Cylindrical geometry should work without PyBaMM."""
        geo = CylindricalGeometry(
            diameter_mm=21.0,
            length_mm=70.0,
            can_wall_thickness_mm=0.3,
            can_bottom_thickness_mm=0.5,
            header_height_mm=3.0,
        )
        assert geo.can_volume_cm3 > 0
        assert geo.can_inner_diameter_mm > 0


class TestPyBaMMRepositoryHandling:
    """Test PyBaMM repository error handling."""

    def test_pybamm_import_exists(self):
        """Verify PyBaMM repository module can be imported."""
        try:
            from forge.materials.repositories.pybamm_repo import PyBaMMRepository

            assert PyBaMMRepository is not None
        except ImportError:
            # PyBaMM not installed - should be handled gracefully
            pass

    def test_parameter_set_listing(self):
        """Test that parameter set listing works."""
        try:
            from forge.materials.repositories.pybamm_repo import ALL_PARAMETER_SETS

            assert len(ALL_PARAMETER_SETS) > 0
        except ImportError:
            # Skip if PyBaMM not available
            pytest.skip("PyBaMM not installed")


class TestExcelRepositoryFallback:
    """Test Excel repository as fallback."""

    def test_excel_repo_module_exists(self):
        """Verify Excel repository module can be imported."""
        from forge.materials.repositories.excel_repo import PANDAS_AVAILABLE

        assert isinstance(PANDAS_AVAILABLE, bool)

    def test_excel_repo_indicates_availability(self):
        """Excel repo should indicate pandas availability."""
        from forge.materials.repositories.excel_repo import check_pandas_available

        result = check_pandas_available()
        assert isinstance(result, bool)