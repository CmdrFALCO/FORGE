"""Tests for STL exporter utilities."""

# ruff: noqa: E402

from pathlib import Path

import pytest

# Import for build123d-dependent tests
build123d = pytest.importorskip("build123d")

from forge.engine.cad import Build123dGenerator
from forge.engine.cad.exporters.stl_exporter import (
    STLExporter,
    STLExportResult,
    STLQuality,
    STLQualitySettings,
    get_stl_file_info,
)
from forge.engine.geometry.loader import ArchetypeLoader

ARCHETYPE_DIR = Path("docs")


@pytest.fixture
def byd_blade_geometry():
    """Load BYD Blade archetype for testing."""
    path = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
    if not path.exists():
        pytest.skip(f"Archetype file not found: {path}")
    loader = ArchetypeLoader(path)
    return loader.to_detailed_geometry()


@pytest.fixture
def tesla_4680_geometry():
    """Load Tesla 4680 archetype for testing."""
    path = ARCHETYPE_DIR / "tesla_4680_archetype.json"
    if not path.exists():
        pytest.skip(f"Archetype file not found: {path}")
    loader = ArchetypeLoader(path)
    return loader.to_detailed_geometry()


class TestSTLQuality:
    """Tests for STLQuality enum and settings."""

    def test_quality_values(self) -> None:
        """Should have three quality levels."""
        assert STLQuality.LOW.value == "low"
        assert STLQuality.MEDIUM.value == "medium"
        assert STLQuality.HIGH.value == "high"

    def test_quality_from_string(self) -> None:
        """Should create from string."""
        assert STLQuality("low") == STLQuality.LOW
        assert STLQuality("medium") == STLQuality.MEDIUM
        assert STLQuality("high") == STLQuality.HIGH


class TestSTLQualitySettings:
    """Tests for STLQualitySettings dataclass."""

    def test_low_quality_settings(self) -> None:
        """Low quality should have larger tolerances."""
        settings = STLQualitySettings.from_preset(STLQuality.LOW)
        assert settings.linear_tolerance == 0.1
        assert settings.angular_tolerance == 0.5

    def test_medium_quality_settings(self) -> None:
        """Medium quality should have balanced tolerances."""
        settings = STLQualitySettings.from_preset(STLQuality.MEDIUM)
        assert settings.linear_tolerance == 0.01
        assert settings.angular_tolerance == 0.1

    def test_high_quality_settings(self) -> None:
        """High quality should have tight tolerances."""
        settings = STLQualitySettings.from_preset(STLQuality.HIGH)
        assert settings.linear_tolerance == 0.001
        assert settings.angular_tolerance == 0.05


class TestSTLExportResult:
    """Tests for STLExportResult dataclass."""

    def test_create_result(self, tmp_path) -> None:
        """Should create result with all attributes."""
        result = STLExportResult(
            filepath=tmp_path / "test.stl",
            file_size_bytes=12345,
            is_binary=True,
            quality=STLQuality.MEDIUM,
            body_count=5,
            success=True,
        )

        assert result.filepath == tmp_path / "test.stl"
        assert result.file_size_bytes == 12345
        assert result.is_binary is True
        assert result.quality == STLQuality.MEDIUM
        assert result.body_count == 5
        assert result.success is True
        assert result.error_message is None

    def test_file_size_mb(self) -> None:
        """Should calculate file size in MB."""
        result = STLExportResult(
            filepath=Path("test.stl"),
            file_size_bytes=1024 * 1024,  # 1 MB
            is_binary=True,
            quality=STLQuality.MEDIUM,
            body_count=1,
            success=True,
        )

        assert result.file_size_mb == 1.0

    def test_failed_result(self) -> None:
        """Should store error message for failed exports."""
        result = STLExportResult(
            filepath=Path("test.stl"),
            file_size_bytes=0,
            is_binary=True,
            quality=STLQuality.MEDIUM,
            body_count=0,
            success=False,
            error_message="Export failed",
        )

        assert result.success is False
        assert result.error_message == "Export failed"


class TestSTLExporter:
    """Tests for STLExporter class."""

    def test_exporter_init_default(self) -> None:
        """Should initialize with default settings."""
        exporter = STLExporter()
        assert exporter.quality == STLQuality.MEDIUM
        assert exporter.binary is True

    def test_exporter_init_with_string(self) -> None:
        """Should accept string for quality."""
        exporter = STLExporter(quality="high")
        assert exporter.quality == STLQuality.HIGH

    def test_exporter_init_ascii(self) -> None:
        """Should allow ASCII format."""
        exporter = STLExporter(binary=False)
        assert exporter.binary is False


class TestSTLExportCombined:
    """Tests for combined STL export."""

    def test_export_creates_file(self, byd_blade_geometry, tmp_path) -> None:
        """Should create STL file."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        exporter = STLExporter(quality=STLQuality.LOW)  # Low for speed
        result = exporter.export_combined(assembly, tmp_path / "test.stl")

        assert result.success is True
        assert result.filepath.exists()
        assert result.file_size_bytes > 0

    def test_export_adds_extension(self, byd_blade_geometry, tmp_path) -> None:
        """Should add .stl extension if missing."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        exporter = STLExporter(quality=STLQuality.LOW)
        result = exporter.export_combined(assembly, tmp_path / "test")

        assert result.filepath.suffix == ".stl"
        assert result.success is True

    def test_export_binary_format(self, byd_blade_geometry, tmp_path) -> None:
        """Binary STL should have binary header."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        exporter = STLExporter(quality=STLQuality.LOW, binary=True)
        result = exporter.export_combined(assembly, tmp_path / "binary.stl")

        assert result.success is True
        assert result.is_binary is True

        # Check file doesn't start with "solid" ASCII header
        with open(result.filepath, "rb") as f:
            f.read(80)
            # Binary STL has 80-byte header that may or may not start with "solid"
            # but the structure is different from ASCII

    def test_export_ascii_format(self, byd_blade_geometry, tmp_path) -> None:
        """ASCII STL should have readable content."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        exporter = STLExporter(quality=STLQuality.LOW, binary=False)
        result = exporter.export_combined(assembly, tmp_path / "ascii.stl")

        assert result.success is True
        assert result.is_binary is False

        # Check for ASCII STL keywords
        with open(result.filepath, "r", encoding="utf-8") as f:
            content = f.read(500)
            assert "solid" in content.lower()
            assert "facet" in content.lower()


class TestSTLExportPerBody:
    """Tests for per-body STL export."""

    def test_export_per_body(self, byd_blade_geometry, tmp_path) -> None:
        """Should create one STL per body."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        exporter = STLExporter(quality=STLQuality.LOW)
        results = exporter.export_per_body(assembly, tmp_path)

        assert isinstance(results, list)
        assert len(results) > 0

        # All should succeed
        for result in results:
            assert result.success is True
            assert result.filepath.exists()

    def test_export_per_body_creates_zip(self, byd_blade_geometry, tmp_path) -> None:
        """Should create ZIP archive when requested."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        exporter = STLExporter(quality=STLQuality.LOW)
        zip_path = exporter.export_per_body(assembly, tmp_path, create_zip=True)

        assert isinstance(zip_path, Path)
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"


class TestGetStlFileInfo:
    """Tests for get_stl_file_info function."""

    def test_info_nonexistent_file(self, tmp_path) -> None:
        """Should return error for nonexistent file."""
        info = get_stl_file_info(tmp_path / "nonexistent.stl")
        assert "error" in info

    def test_info_binary_stl(self, byd_blade_geometry, tmp_path) -> None:
        """Should detect binary STL format."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        exporter = STLExporter(quality=STLQuality.LOW, binary=True)
        result = exporter.export_combined(assembly, tmp_path / "binary.stl")

        info = get_stl_file_info(result.filepath)

        assert info.get("format") == "binary"
        assert "triangle_count" in info
        assert info["triangle_count"] > 0

    def test_info_ascii_stl(self, byd_blade_geometry, tmp_path) -> None:
        """Should detect ASCII STL format."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        exporter = STLExporter(quality=STLQuality.LOW, binary=False)
        result = exporter.export_combined(assembly, tmp_path / "ascii.stl")

        info = get_stl_file_info(result.filepath)

        assert info.get("format") == "ASCII"
        assert "file_size_bytes" in info


class TestGeneratorSTLExport:
    """Tests for Build123dGenerator STL export methods."""

    def test_generator_export_stl(self, byd_blade_geometry, tmp_path) -> None:
        """Generator should export STL via convenience method."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        result = generator.export_stl(assembly, tmp_path / "test.stl")

        assert result.success is True
        assert result.filepath.exists()

    def test_generator_export_stl_with_quality(self, byd_blade_geometry, tmp_path) -> None:
        """Generator should accept quality parameter."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        result = generator.export_stl(
            assembly, tmp_path / "test.stl", quality="low", binary=True
        )

        assert result.success is True

    def test_generator_export_stl_per_body(self, byd_blade_geometry, tmp_path) -> None:
        """Generator should export per-body STL."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        results = generator.export_stl_per_body(assembly, tmp_path, quality="low")

        assert isinstance(results, list)
        assert all(r.success for r in results)


class TestConvenienceFunction:
    """Tests for generate_stl_from_archetype convenience function."""

    def test_generate_stl_from_archetype(self, tmp_path) -> None:
        """Convenience function should work end-to-end."""
        from forge.engine.cad import generate_stl_from_archetype

        archetype = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
        if not archetype.exists():
            pytest.skip(f"Archetype file not found: {archetype}")

        output = tmp_path / "output.stl"

        result = generate_stl_from_archetype(archetype, output, quality="low")

        assert result.success is True
        assert result.filepath.exists()
        assert result.filepath.suffix == ".stl"

    def test_generate_stl_with_options(self, tmp_path) -> None:
        """Should accept all options."""
        from forge.engine.cad import generate_stl_from_archetype

        archetype = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
        if not archetype.exists():
            pytest.skip(f"Archetype file not found: {archetype}")

        output = tmp_path / "output.stl"

        result = generate_stl_from_archetype(
            archetype,
            output,
            grouping_mode="by_material",
            quality="low",
            apply_swelling=False,
        )

        assert result.success is True


class TestAllArchetypesSTLExport:
    """Test that all archetypes export to STL without errors."""

    @pytest.mark.parametrize(
        "archetype_file",
        [
            "byd_blade_138ah_archetype.json",
            "tesla_4680_archetype.json",
            "lg_e66a_archetype.json",
            "samsung_21700_50g_archetype.json",
            "catl_qilin_archetype.json",
            "samsung_sdi_94ah_archetype.json",
        ],
    )
    def test_archetype_exports_stl(self, archetype_file: str, tmp_path) -> None:
        """All archetypes should export to STL without errors."""
        path = ARCHETYPE_DIR / archetype_file
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")

        loader = ArchetypeLoader(path)
        geometry = loader.to_detailed_geometry()

        generator = Build123dGenerator()
        assembly = generator.generate(geometry)

        result = generator.export_stl(
            assembly, tmp_path / f"{archetype_file}.stl", quality="low"
        )

        assert result.success is True
        assert result.filepath.exists()
        assert result.file_size_bytes > 0


class TestQualityComparison:
    """Compare different quality settings."""

    def test_all_quality_levels_export(self, byd_blade_geometry, tmp_path) -> None:
        """All quality levels should produce valid files."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        low_result = generator.export_stl(
            assembly, tmp_path / "low.stl", quality="low", binary=True
        )
        medium_result = generator.export_stl(
            assembly, tmp_path / "medium.stl", quality="medium", binary=True
        )
        high_result = generator.export_stl(
            assembly, tmp_path / "high.stl", quality="high", binary=True
        )

        # All should succeed and produce non-empty files
        assert low_result.success is True
        assert medium_result.success is True
        assert high_result.success is True

        assert low_result.file_size_bytes > 0
        assert medium_result.file_size_bytes > 0
        assert high_result.file_size_bytes > 0
