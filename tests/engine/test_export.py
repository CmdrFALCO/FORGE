"""Tests for export functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from forge.export import (
    export_bom_csv,
    export_bom_json,
    export_json,
    export_report_csv,
    load_report_json,
)
from forge.engine.models.results import BillOfMaterials, CellReport


@pytest.fixture
def sample_report():
    """Create a sample cell report for testing."""
    return CellReport(
        cell_name="Test Cell",
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


@pytest.fixture
def sample_bom():
    """Create a sample BOM for testing."""
    bom = BillOfMaterials(
        cell_name="Test Cell",
        cell_type="Pouch",
    )
    bom.add_item("Cathode Actives", "NMC532", 100.0, 28.57, 2.0)
    bom.add_item("Cathode Collector", "Al Foil", 10.0, 3.70, 0.02)
    bom.add_item("Anode Actives", "Graphite", 60.0, 37.5, 0.6)
    bom.add_item("Anode Collector", "Cu Foil", 25.0, 2.79, 0.375)
    bom.add_item("Separator", "PE/PP", 6.0, 6.32, 1.08)
    bom.add_item("Electrolyte", "LiPF6", 50.0, 40.0, 0.95)
    bom.add_item("Housing", "Pouch Foil", 15.0, 10.0, 0.15)
    bom.calculate_percentages()
    return bom


class TestCSVExport:
    """Tests for CSV export functions."""

    def test_export_bom_csv(self, sample_bom):
        """Test BOM CSV export."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name

        try:
            export_bom_csv(sample_bom, path)

            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Check header
            assert "CellCAD Bill of Materials (BOM)" in content
            assert "Test Cell" in content
            assert "Pouch" in content

            # Check column headers
            assert "Type;Name;Mass [%]" in content

            # Check data rows
            assert "Cathode Actives;NMC532" in content
            assert "TOTAL" in content

            # Check European number format (comma decimal separator)
            lines = content.split("\n")
            total_line = [line for line in lines if line.startswith("TOTAL")][0]
            assert ",00" in total_line  # Should have comma decimals

        finally:
            Path(path).unlink()

    def test_export_report_csv(self, sample_report):
        """Test report CSV export."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name

        try:
            export_report_csv(sample_report, path)

            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Check header
            assert "CellCAD Cell Report" in content
            assert "Test Cell" in content

            # Check sections
            assert "DIMENSIONS" in content
            assert "VOLUMES" in content
            assert "ELECTRICAL" in content
            assert "MASS BREAKDOWN" in content

            # Check values are present
            assert "200,00" in content  # Cell height with comma decimal

        finally:
            Path(path).unlink()


class TestJSONExport:
    """Tests for JSON export functions."""

    def test_export_json_report_only(self, sample_report):
        """Test JSON export with report only."""
        json_str = export_json(sample_report)
        data = json.loads(json_str)

        assert "report" in data
        assert "bom" in data
        assert data["bom"] is None
        assert "metadata" in data

        report = data["report"]
        assert report["cell_name"] == "Test Cell"
        assert report["dimensions"]["cell_height_mm"] == 200.0
        assert report["electrical"]["capacity_ah"] == 10.0

    def test_export_json_with_bom(self, sample_report, sample_bom):
        """Test JSON export with report and BOM."""
        json_str = export_json(sample_report, sample_bom)
        data = json.loads(json_str)

        assert data["bom"] is not None
        assert len(data["bom"]["items"]) == 7
        assert data["bom"]["totals"]["total_mass_g"] > 0

    def test_export_json_to_file(self, sample_report):
        """Test JSON export to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            result = export_json(sample_report, output_path=path)
            assert result is None  # No return when writing to file

            with open(path) as f:
                data = json.load(f)

            assert data["report"]["cell_name"] == "Test Cell"

        finally:
            Path(path).unlink()

    def test_export_bom_json(self, sample_bom):
        """Test BOM-only JSON export."""
        json_str = export_bom_json(sample_bom)
        data = json.loads(json_str)

        assert "items" in data
        assert "totals" in data
        assert len(data["items"]) == 7

    def test_load_report_json(self, sample_report):
        """Test loading report from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            export_json(sample_report, output_path=path)
            loaded = load_report_json(path)

            assert loaded["report"]["cell_name"] == "Test Cell"
            assert loaded["report"]["electrical"]["capacity_ah"] == 10.0

        finally:
            Path(path).unlink()


class TestExportFormats:
    """Tests for export format consistency."""

    def test_csv_semicolon_delimiter(self, sample_bom):
        """Test that CSV uses semicolon delimiter."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name

        try:
            export_bom_csv(sample_bom, path)

            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Should have semicolons, not commas as field delimiter
            assert "Type;Name;Mass" in content

        finally:
            Path(path).unlink()

    def test_csv_comma_decimal(self, sample_report):
        """Test that CSV uses comma as decimal separator."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name

        try:
            export_report_csv(sample_report, path)

            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Numbers should use comma as decimal separator
            assert "200,00" in content  # 200.00 with comma

        finally:
            Path(path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

