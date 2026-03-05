"""Tests for STEP exporter utilities."""

from pathlib import Path

import pytest

from forge.engine.cad.exporters.step_exporter import (
    STEPExportResult,
    count_step_entities,
    validate_step_file,
)

# Import for build123d-dependent tests
build123d = pytest.importorskip("build123d")


class TestSTEPExportResult:
    """Tests for STEPExportResult dataclass."""

    def test_create_result(self, tmp_path) -> None:
        """Should create result with all attributes."""
        result = STEPExportResult(
            filepath=tmp_path / "test.step",
            file_size_bytes=12345,
            body_count=5,
            success=True,
        )

        assert result.filepath == tmp_path / "test.step"
        assert result.file_size_bytes == 12345
        assert result.body_count == 5
        assert result.success is True
        assert result.error_message is None

    def test_file_size_mb(self) -> None:
        """Should calculate file size in MB."""
        result = STEPExportResult(
            filepath=Path("test.step"),
            file_size_bytes=1024 * 1024,  # 1 MB
            body_count=1,
            success=True,
        )

        assert result.file_size_mb == 1.0

    def test_failed_result(self) -> None:
        """Should store error message for failed exports."""
        result = STEPExportResult(
            filepath=Path("test.step"),
            file_size_bytes=0,
            body_count=0,
            success=False,
            error_message="Export failed",
        )

        assert result.success is False
        assert result.error_message == "Export failed"


class TestValidateStepFile:
    """Tests for validate_step_file function."""

    def test_validate_nonexistent_file(self, tmp_path) -> None:
        """Should return False for nonexistent file."""
        result = validate_step_file(tmp_path / "nonexistent.step")
        assert result is False

    def test_validate_empty_file(self, tmp_path) -> None:
        """Should return False for empty file."""
        empty_file = tmp_path / "empty.step"
        empty_file.write_text("")

        result = validate_step_file(empty_file)
        assert result is False

    def test_validate_small_file(self, tmp_path) -> None:
        """Should return False for too-small file."""
        small_file = tmp_path / "small.step"
        small_file.write_text("small")

        result = validate_step_file(small_file)
        assert result is False

    def test_validate_valid_step_header(self, tmp_path) -> None:
        """Should return True for file with valid STEP header."""
        valid_file = tmp_path / "valid.step"
        valid_file.write_text(
            "ISO-10303-21;\n"
            "HEADER;\n"
            "FILE_DESCRIPTION(...);\n"
            "FILE_NAME(...);\n"
            "FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));\n"
            "ENDSEC;\n"
            "DATA;\n"
            "ENDSEC;\n"
            "END-ISO-10303-21;\n"
        )

        result = validate_step_file(valid_file)
        assert result is True

    def test_validate_invalid_content(self, tmp_path) -> None:
        """Should return False for file without STEP header."""
        invalid_file = tmp_path / "invalid.step"
        invalid_file.write_text("Lorem ipsum dolor sit amet consectetur adipiscing elit " * 10)

        result = validate_step_file(invalid_file)
        assert result is False


class TestCountStepEntities:
    """Tests for count_step_entities function."""

    def test_count_nonexistent_file(self, tmp_path) -> None:
        """Should return empty dict for nonexistent file."""
        result = count_step_entities(tmp_path / "nonexistent.step")
        assert result == {}

    def test_count_entities_in_step(self, tmp_path) -> None:
        """Should count STEP entities by type."""
        step_content = """ISO-10303-21;
HEADER;
ENDSEC;
DATA;
#1 = CARTESIAN_POINT('origin', (0.0, 0.0, 0.0));
#2 = CARTESIAN_POINT('p1', (1.0, 0.0, 0.0));
#3 = CARTESIAN_POINT('p2', (0.0, 1.0, 0.0));
#4 = DIRECTION('z', (0.0, 0.0, 1.0));
#5 = DIRECTION('x', (1.0, 0.0, 0.0));
#6 = AXIS2_PLACEMENT_3D('', #1, #4, #5);
ENDSEC;
END-ISO-10303-21;
"""
        step_file = tmp_path / "test.step"
        step_file.write_text(step_content)

        counts = count_step_entities(step_file)

        assert counts.get("CARTESIAN_POINT", 0) == 3
        assert counts.get("DIRECTION", 0) == 2
        assert counts.get("AXIS2_PLACEMENT_3D", 0) == 1


class TestGetStepFileInfo:
    """Tests for get_step_file_info function."""

    def test_info_nonexistent_file(self, tmp_path) -> None:
        """Should return error for nonexistent file."""
        from forge.engine.cad.exporters.step_exporter import get_step_file_info

        info = get_step_file_info(tmp_path / "nonexistent.step")

        assert "error" in info
        assert info.get("valid") is False

    def test_info_valid_step_file(self, tmp_path) -> None:
        """Should return info for valid STEP file."""
        from forge.engine.cad import Build123dGenerator
        from forge.engine.cad.exporters.step_exporter import get_step_file_info
        from forge.engine.geometry.loader import ArchetypeLoader

        archetype_path = Path("docs") / "byd_blade_138ah_archetype.json"
        if not archetype_path.exists():
            pytest.skip("Archetype not found")

        # Generate a real STEP file
        loader = ArchetypeLoader(archetype_path)
        geometry = loader.to_detailed_geometry()
        generator = Build123dGenerator()
        assembly = generator.generate(geometry)

        step_path = tmp_path / "test.step"
        generator.export_step(assembly, step_path)

        info = get_step_file_info(step_path)

        assert info.get("valid") is True
        assert "file_size_bytes" in info
        assert info["file_size_bytes"] > 0
        assert "file_size_mb" in info
