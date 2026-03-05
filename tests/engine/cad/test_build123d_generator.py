"""Tests for Build123d generator module."""

from pathlib import Path

import pytest

# Skip all tests if build123d not available
build123d = pytest.importorskip("build123d")

from forge.engine.cad import BUILD123D_AVAILABLE, Build123dGenerator, GroupingMode
from forge.engine.cad.assembly import MaterialGroup
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


@pytest.fixture
def samsung_21700_geometry():
    """Load Samsung 21700 archetype for testing."""
    path = ARCHETYPE_DIR / "samsung_21700_50g_archetype.json"
    if not path.exists():
        pytest.skip(f"Archetype file not found: {path}")
    loader = ArchetypeLoader(path)
    return loader.to_detailed_geometry()


class TestBuild123dGenerator:
    """Tests for Build123dGenerator class."""

    def test_generator_init_default(self) -> None:
        """Should initialize with default grouping mode."""
        generator = Build123dGenerator()
        assert generator.grouping_mode == GroupingMode.BY_MATERIAL

    def test_generator_init_with_string(self) -> None:
        """Should accept string for grouping mode."""
        generator = Build123dGenerator(grouping_mode="individual")
        assert generator.grouping_mode == GroupingMode.INDIVIDUAL

    def test_generate_prismatic_grouped(self, byd_blade_geometry) -> None:
        """Should generate grouped assembly for prismatic cell."""
        generator = Build123dGenerator(grouping_mode=GroupingMode.BY_MATERIAL)
        assembly = generator.generate(byd_blade_geometry)

        assert assembly is not None
        assert assembly.cell_type == "prismatic"
        assert assembly.chemistry == "LFP"
        assert assembly.grouped_by_material is True

        # Grouped should have fewer bodies (one per material type + casing)
        assert assembly.body_count() <= 10

        # Should have casing
        casing_bodies = assembly.get_bodies_by_group(MaterialGroup.CASING)
        assert len(casing_bodies) == 1

    def test_generate_prismatic_individual(self, byd_blade_geometry) -> None:
        """Should generate individual layer bodies for prismatic cell."""
        generator = Build123dGenerator(grouping_mode=GroupingMode.INDIVIDUAL)
        assembly = generator.generate(byd_blade_geometry)

        assert assembly is not None
        assert assembly.grouped_by_material is False

        # Individual should have many bodies (one per layer + casing)
        assert assembly.body_count() > 50

    def test_generate_cylindrical_grouped(self, tesla_4680_geometry) -> None:
        """Should generate grouped assembly for cylindrical cell."""
        generator = Build123dGenerator(grouping_mode=GroupingMode.BY_MATERIAL)
        assembly = generator.generate(tesla_4680_geometry)

        assert assembly is not None
        assert assembly.cell_type == "cylindrical"
        assert "NMC" in assembly.chemistry.upper()

        # Should have casing
        casing_bodies = assembly.get_bodies_by_group(MaterialGroup.CASING)
        assert len(casing_bodies) == 1

    def test_generate_cylindrical_individual(self, tesla_4680_geometry) -> None:
        """Should generate individual wind bodies for cylindrical cell."""
        generator = Build123dGenerator(grouping_mode=GroupingMode.INDIVIDUAL)
        assembly = generator.generate(tesla_4680_geometry)

        assert assembly is not None
        assert assembly.grouped_by_material is False

        # Individual should have bodies for each wind
        assert assembly.body_count() > 10

    def test_all_bodies_have_solids(self, byd_blade_geometry) -> None:
        """All bodies should have valid Build123d solids."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        for body in assembly.bodies:
            assert body.solid is not None, f"Body {body.name} has no solid"

    def test_assembly_summary(self, byd_blade_geometry) -> None:
        """Assembly summary should show body counts by group."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        summary = assembly.summary()

        # Should have entries for electrode materials and casing
        assert "Casing" in summary
        assert summary["Casing"] == 1


class TestSTEPExport:
    """Tests for STEP file export."""

    def test_export_step_creates_file(self, byd_blade_geometry, tmp_path) -> None:
        """Should export valid STEP file."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        output_path = tmp_path / "test_cell.step"
        result_path = generator.export_step(assembly, output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 1000  # Non-trivial file size

    def test_export_step_adds_extension(self, byd_blade_geometry, tmp_path) -> None:
        """Should add .step extension if missing."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        output_path = tmp_path / "test_cell"  # No extension
        result_path = generator.export_step(assembly, output_path)

        assert result_path.suffix == ".step"
        assert result_path.exists()

    def test_export_step_creates_directory(self, byd_blade_geometry, tmp_path) -> None:
        """Should create parent directories if needed."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        output_path = tmp_path / "subdir" / "nested" / "test_cell.step"
        result_path = generator.export_step(assembly, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_export_step_valid_header(self, byd_blade_geometry, tmp_path) -> None:
        """Exported STEP file should have valid header."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        output_path = tmp_path / "test_cell.step"
        result_path = generator.export_step(assembly, output_path)

        with open(result_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(500)
            assert "ISO-10303-21" in content or "STEP" in content.upper()


class TestBREPExport:
    """Tests for BREP file export."""

    def test_export_brep_creates_file(self, byd_blade_geometry, tmp_path) -> None:
        """Should export BREP file."""
        generator = Build123dGenerator()
        assembly = generator.generate(byd_blade_geometry)

        output_path = tmp_path / "test_cell.brep"
        result_path = generator.export_brep(assembly, output_path)

        assert result_path.exists()
        assert result_path.suffix == ".brep"


class TestAllArchetypesExport:
    """Test that all archetypes export without errors."""

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
    def test_archetype_generates_assembly(self, archetype_file: str) -> None:
        """All archetypes should generate valid assemblies."""
        path = ARCHETYPE_DIR / archetype_file
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")

        loader = ArchetypeLoader(path)
        geometry = loader.to_detailed_geometry()

        generator = Build123dGenerator()
        assembly = generator.generate(geometry)

        assert assembly is not None
        assert assembly.body_count() > 0

    @pytest.mark.parametrize(
        "archetype_file",
        [
            "byd_blade_138ah_archetype.json",
            "tesla_4680_archetype.json",
            "lg_e66a_archetype.json",
            "samsung_21700_50g_archetype.json",
        ],
    )
    def test_archetype_exports_step(self, archetype_file: str, tmp_path) -> None:
        """All archetypes should export to STEP without errors."""
        path = ARCHETYPE_DIR / archetype_file
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")

        loader = ArchetypeLoader(path)
        geometry = loader.to_detailed_geometry()

        generator = Build123dGenerator()
        assembly = generator.generate(geometry)

        output_path = tmp_path / f"{archetype_file}.step"
        result_path = generator.export_step(assembly, output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 0


class TestConvenienceFunction:
    """Tests for generate_step_from_archetype convenience function."""

    def test_generate_step_from_archetype(self, tmp_path) -> None:
        """Convenience function should work end-to-end."""
        from forge.engine.cad import generate_step_from_archetype

        archetype = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
        if not archetype.exists():
            pytest.skip(f"Archetype file not found: {archetype}")

        output = tmp_path / "output.step"

        result = generate_step_from_archetype(archetype, output)

        assert result.exists()
        assert result.suffix == ".step"
        assert result.stat().st_size > 1000

    def test_generate_step_with_options(self, tmp_path) -> None:
        """Should accept grouping mode option."""
        from forge.engine.cad import generate_step_from_archetype

        archetype = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
        if not archetype.exists():
            pytest.skip(f"Archetype file not found: {archetype}")

        output = tmp_path / "output.step"

        result = generate_step_from_archetype(
            archetype,
            output,
            grouping_mode="by_material",
            apply_swelling=False,
        )

        assert result.exists()


class TestGroupingModeComparison:
    """Compare grouped vs individual mode outputs."""

    def test_grouped_fewer_bodies_than_individual(self, byd_blade_geometry) -> None:
        """Grouped mode should produce fewer bodies than individual."""
        grouped_gen = Build123dGenerator(grouping_mode=GroupingMode.BY_MATERIAL)
        individual_gen = Build123dGenerator(grouping_mode=GroupingMode.INDIVIDUAL)

        grouped_assembly = grouped_gen.generate(byd_blade_geometry)
        individual_assembly = individual_gen.generate(byd_blade_geometry)

        assert grouped_assembly.body_count() < individual_assembly.body_count()

    def test_both_modes_export_valid_step(self, byd_blade_geometry, tmp_path) -> None:
        """Both grouping modes should produce valid STEP files."""
        grouped_gen = Build123dGenerator(grouping_mode=GroupingMode.BY_MATERIAL)
        individual_gen = Build123dGenerator(grouping_mode=GroupingMode.INDIVIDUAL)

        grouped_assembly = grouped_gen.generate(byd_blade_geometry)
        individual_assembly = individual_gen.generate(byd_blade_geometry)

        grouped_path = tmp_path / "grouped.step"
        individual_path = tmp_path / "individual.step"

        grouped_gen.export_step(grouped_assembly, grouped_path)
        individual_gen.export_step(individual_assembly, individual_path)

        # Both should produce valid, non-empty files
        assert grouped_path.exists()
        assert individual_path.exists()
        assert grouped_path.stat().st_size > 1000
        assert individual_path.stat().st_size > 1000
