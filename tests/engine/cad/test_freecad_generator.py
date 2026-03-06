"""Tests for FreeCAD script generation."""

import ast
from pathlib import Path

import pytest

from forge.engine.cad.body_builders import GroupingMode
from forge.engine.cad.freecad import (
    MATERIAL_TRANSPARENCY,
    FreeCADColor,
    FreeCADColorScheme,
    FreeCADScriptGenerator,
    generate_freecad_script_from_archetype,
)
from forge.engine.geometry.loader import ArchetypeLoader

ARCHETYPE_DIR = Path("docs")


@pytest.fixture
def byd_blade_geometry():
    """Load BYD Blade geometry (prismatic cell)."""
    loader = ArchetypeLoader(ARCHETYPE_DIR / "byd_blade_138ah_archetype.json")
    return loader.to_detailed_geometry()


@pytest.fixture
def tesla_4680_geometry():
    """Load Tesla 4680 geometry (cylindrical cell)."""
    loader = ArchetypeLoader(ARCHETYPE_DIR / "tesla_4680_archetype.json")
    return loader.to_detailed_geometry()


@pytest.fixture
def samsung_21700_geometry():
    """Load Samsung 21700 geometry (cylindrical cell)."""
    loader = ArchetypeLoader(ARCHETYPE_DIR / "samsung_21700_50g_archetype.json")
    return loader.to_detailed_geometry()


class TestFreeCADColor:
    """Tests for FreeCADColor dataclass."""

    def test_to_tuple(self):
        """Should return color as tuple."""
        color = FreeCADColor(0.5, 0.3, 0.7)
        assert color.to_tuple() == (0.5, 0.3, 0.7)

    def test_to_freecad_string(self):
        """Should format color for FreeCAD script."""
        color = FreeCADColor(0.5, 0.333, 0.7)
        s = color.to_freecad_string()

        assert s.startswith("(")
        assert s.endswith(")")
        assert "0.500" in s
        assert "0.333" in s
        assert "0.700" in s


class TestFreeCADColorScheme:
    """Tests for FreeCADColorScheme."""

    def test_get_color_for_material(self):
        """Should return valid color for known materials."""
        color = FreeCADColorScheme.get_color_for_material("Cathode_Coating", "LFP")
        assert 0 <= color.r <= 1
        assert 0 <= color.g <= 1
        assert 0 <= color.b <= 1

    def test_chemistry_affects_cathode_color(self):
        """Different chemistries should have different cathode colors."""
        lfp = FreeCADColorScheme.get_color_for_material("Cathode_Coating", "LFP")
        nmc811 = FreeCADColorScheme.get_color_for_material("Cathode_Coating", "NMC811")

        assert lfp.to_tuple() != nmc811.to_tuple()

    def test_ncm_normalized_to_nmc(self):
        """NCM should be normalized to NMC for color lookup."""
        ncm811 = FreeCADColorScheme.get_cathode_color("NCM811")
        nmc811 = FreeCADColorScheme.get_cathode_color("NMC811")

        assert ncm811.to_tuple() == nmc811.to_tuple()

    def test_unknown_material_returns_casing(self):
        """Unknown material should return casing color."""
        color = FreeCADColorScheme.get_color_for_material("Unknown_Material", "")
        casing = FreeCADColorScheme.CASING

        assert color.to_tuple() == casing.to_tuple()

    def test_all_materials_have_transparency(self):
        """All material groups should have defined transparency."""
        materials = [
            "Cathode_Coating",
            "Cathode_Collector",
            "Anode_Coating",
            "Anode_Collector",
            "Separator",
            "Casing",
        ]

        for material in materials:
            assert material in MATERIAL_TRANSPARENCY
            assert 0 <= MATERIAL_TRANSPARENCY[material] <= 100


class TestFreeCADScriptGenerator:
    """Tests for FreeCADScriptGenerator."""

    def test_generate_stacked_grouped(self, byd_blade_geometry, tmp_path):
        """Should generate script for stacked cell with grouped mode."""
        generator = FreeCADScriptGenerator(grouping_mode=GroupingMode.BY_MATERIAL)
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        assert result.success
        assert result.filepath.exists()
        assert result.filepath.suffix == ".py"
        assert result.grouped_by_material is True
        assert result.line_count > 100
        assert result.error_message is None

    def test_generate_stacked_individual(self, byd_blade_geometry, tmp_path):
        """Should generate script for stacked cell with individual mode."""
        generator = FreeCADScriptGenerator(grouping_mode=GroupingMode.INDIVIDUAL)
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        assert result.success
        assert result.grouped_by_material is False

    def test_generate_cylindrical_grouped(self, tesla_4680_geometry, tmp_path):
        """Should generate script for cylindrical cell with grouped mode."""
        generator = FreeCADScriptGenerator(grouping_mode=GroupingMode.BY_MATERIAL)
        result = generator.generate(tesla_4680_geometry, tmp_path / "test.py")

        assert result.success
        assert result.cell_type == "cylindrical"

    def test_generate_cylindrical_individual(self, tesla_4680_geometry, tmp_path):
        """Should generate script for cylindrical cell with individual mode."""
        generator = FreeCADScriptGenerator(grouping_mode="individual")
        result = generator.generate(tesla_4680_geometry, tmp_path / "test.py")

        assert result.success
        assert result.grouped_by_material is False

    def test_script_is_valid_python(self, byd_blade_geometry, tmp_path):
        """Generated script should be valid Python syntax."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        # Should parse without syntax errors
        content = result.filepath.read_text()
        ast.parse(content)

    def test_script_is_valid_python_cylindrical(self, tesla_4680_geometry, tmp_path):
        """Generated cylindrical script should be valid Python syntax."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(tesla_4680_geometry, tmp_path / "test.py")

        # Should parse without syntax errors
        content = result.filepath.read_text()
        ast.parse(content)

    def test_script_has_parameters_section(self, byd_blade_geometry, tmp_path):
        """Script should have editable parameters at top."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        content = result.filepath.read_text()
        assert "PARAMETERS" in content
        assert "CELL_LENGTH" in content or "CELL_DIAMETER" in content
        assert "CATHODE_COATING_THICKNESS" in content

    def test_script_has_colors(self, byd_blade_geometry, tmp_path):
        """Script should include color definitions."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        content = result.filepath.read_text()
        assert "COLORS" in content
        assert "Cathode_Coating" in content
        assert "Anode_Collector" in content
        assert "Separator" in content

    def test_script_has_verbose_comments(self, byd_blade_geometry, tmp_path):
        """Script should have explanatory comments."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        content = result.filepath.read_text()
        # Check for section headers
        assert "HELPER FUNCTIONS" in content
        assert "CELL GEOMETRY CREATION" in content
        assert "MAIN EXECUTION" in content

    def test_script_has_freecad_imports(self, byd_blade_geometry, tmp_path):
        """Script should have FreeCAD imports."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        content = result.filepath.read_text()
        assert "import FreeCAD" in content
        assert "import Part" in content

    def test_script_has_materials_reference(self, byd_blade_geometry, tmp_path):
        """Script should include materials reference."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        content = result.filepath.read_text()
        assert "MATERIALS" in content
        assert "Aluminum" in content or "Copper" in content

    def test_script_has_main_function(self, byd_blade_geometry, tmp_path):
        """Script should have main entry point."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        content = result.filepath.read_text()
        assert "def main():" in content
        assert 'if __name__ == "__main__":' in content

    def test_adds_py_extension_if_missing(self, byd_blade_geometry, tmp_path):
        """Should add .py extension if not provided."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test")

        assert result.filepath.suffix == ".py"
        assert result.filepath.exists()

    def test_creates_output_directory(self, byd_blade_geometry, tmp_path):
        """Should create output directory if it doesn't exist."""
        generator = FreeCADScriptGenerator()
        output_path = tmp_path / "subdir" / "nested" / "test.py"
        result = generator.generate(byd_blade_geometry, output_path)

        assert result.success
        assert result.filepath.exists()

    def test_grouping_mode_string_input(self, byd_blade_geometry, tmp_path):
        """Should accept grouping mode as string."""
        generator = FreeCADScriptGenerator(grouping_mode="by_material")
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        assert result.success
        assert result.grouped_by_material is True

    def test_archetype_name_in_script(self, byd_blade_geometry, tmp_path):
        """Script should include archetype name."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        content = result.filepath.read_text()
        assert "BYD" in content or "Blade" in content


class TestGenerateFreecadScriptFromArchetype:
    """Tests for convenience function."""

    def test_generate_from_stacked_archetype(self, tmp_path):
        """Should generate from stacked cell archetype."""
        result = generate_freecad_script_from_archetype(
            ARCHETYPE_DIR / "byd_blade_138ah_archetype.json",
            tmp_path / "output.py",
            grouping_mode="by_material",
        )

        assert result.success
        assert result.filepath.exists()
        assert result.cell_type in ("pouch", "prismatic")

    def test_generate_from_cylindrical_archetype(self, tmp_path):
        """Should generate from cylindrical cell archetype."""
        result = generate_freecad_script_from_archetype(
            ARCHETYPE_DIR / "tesla_4680_archetype.json",
            tmp_path / "output.py",
            grouping_mode="individual",
        )

        assert result.success
        assert result.cell_type == "cylindrical"

    def test_apply_swelling_option(self, tmp_path):
        """Should respect apply_swelling option."""
        result_with = generate_freecad_script_from_archetype(
            ARCHETYPE_DIR / "byd_blade_138ah_archetype.json",
            tmp_path / "with_swelling.py",
            apply_swelling=True,
        )

        result_without = generate_freecad_script_from_archetype(
            ARCHETYPE_DIR / "byd_blade_138ah_archetype.json",
            tmp_path / "without_swelling.py",
            apply_swelling=False,
        )

        assert result_with.success
        assert result_without.success
        # Both should generate valid scripts
        assert result_with.filepath.exists()
        assert result_without.filepath.exists()


class TestScriptGenerationResult:
    """Tests for ScriptGenerationResult dataclass."""

    def test_successful_result(self, byd_blade_geometry, tmp_path):
        """Successful generation should have correct attributes."""
        generator = FreeCADScriptGenerator()
        result = generator.generate(byd_blade_geometry, tmp_path / "test.py")

        assert result.success is True
        assert result.error_message is None
        assert isinstance(result.filepath, Path)
        assert isinstance(result.line_count, int)
        assert result.line_count > 0

    def test_result_has_cell_type(self, byd_blade_geometry, tesla_4680_geometry, tmp_path):
        """Result should include cell type."""
        generator = FreeCADScriptGenerator()

        result1 = generator.generate(byd_blade_geometry, tmp_path / "stacked.py")
        result2 = generator.generate(tesla_4680_geometry, tmp_path / "cylindrical.py")

        assert result1.cell_type in ("pouch", "prismatic")
        assert result2.cell_type == "cylindrical"


class TestMultipleCellTypes:
    """Tests for generating scripts for different cell types."""

    def test_generate_for_all_archetypes(self, tmp_path):
        """Should be able to generate scripts for all sample archetypes."""
        archetype_files = list(ARCHETYPE_DIR.glob("*_archetype.json"))

        assert len(archetype_files) > 0, "No archetype files found"

        for archetype_file in archetype_files:
            output_name = archetype_file.stem.replace("_archetype", "_freecad.py")
            result = generate_freecad_script_from_archetype(
                archetype_file,
                tmp_path / output_name,
            )

            assert result.success, f"Failed for {archetype_file.name}: {result.error_message}"
            assert result.filepath.exists()

            # Verify valid Python
            content = result.filepath.read_text()
            ast.parse(content)
