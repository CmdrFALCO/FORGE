"""Tests for CAD assembly module."""

import pytest

from forge.engine.cad.assembly import AssemblyNamer, CADAssembly, CADBody, MaterialGroup


class TestMaterialGroup:
    """Tests for MaterialGroup enum."""

    def test_all_groups_defined(self) -> None:
        """All expected material groups should be defined."""
        assert MaterialGroup.CASING
        assert MaterialGroup.CATHODE_COLLECTOR
        assert MaterialGroup.CATHODE_COATING
        assert MaterialGroup.ANODE_COLLECTOR
        assert MaterialGroup.ANODE_COATING
        assert MaterialGroup.SEPARATOR

    def test_group_values_are_strings(self) -> None:
        """Group values should be descriptive strings."""
        assert MaterialGroup.CATHODE_COATING.value == "Cathode_Coating"
        assert MaterialGroup.SEPARATOR.value == "Separator"


class TestAssemblyNamer:
    """Tests for AssemblyNamer class."""

    def test_body_name_without_index(self) -> None:
        """Body name without index should be just the group name."""
        name = AssemblyNamer.body_name(MaterialGroup.CATHODE_COATING)
        assert name == "Cathode_Coating"

    def test_body_name_with_index(self) -> None:
        """Body name with index should include padded number."""
        name = AssemblyNamer.body_name(MaterialGroup.CATHODE_COATING, index=5, total=50)
        assert name == "Cathode_Coating_05"

    def test_body_name_padding_for_large_total(self) -> None:
        """Index should be zero-padded to 3 digits for total >= 100."""
        name = AssemblyNamer.body_name(MaterialGroup.SEPARATOR, index=5, total=150)
        assert name == "Separator_005"

    def test_body_name_no_padding_for_small_total(self) -> None:
        """Index should not be padded for small totals."""
        name = AssemblyNamer.body_name(MaterialGroup.SEPARATOR, index=5, total=9)
        assert name == "Separator_5"

    def test_assembly_name(self) -> None:
        """Assembly name should include cell type and chemistry."""
        name = AssemblyNamer.assembly_name("prismatic", "LFP")
        assert name == "Cell_Assembly_prismatic_LFP"

    def test_assembly_name_sanitizes_spaces(self) -> None:
        """Assembly name should replace spaces with underscores."""
        name = AssemblyNamer.assembly_name("pouch cell", "NMC 811")
        assert " " not in name
        assert "pouch_cell" in name

    def test_wind_name(self) -> None:
        """Wind name should include padded index."""
        name = AssemblyNamer.wind_name(5, 100)
        assert name == "Wind_005"


class TestCADBody:
    """Tests for CADBody class."""

    def test_create_body(self) -> None:
        """Should create body with required attributes."""
        body = CADBody(
            name="Test_Body",
            material_group=MaterialGroup.CATHODE_COATING,
        )

        assert body.name == "Test_Body"
        assert body.material_group == MaterialGroup.CATHODE_COATING
        assert body.layer_index is None
        assert body.solid is None

    def test_body_with_index(self) -> None:
        """Should create body with layer index."""
        body = CADBody(
            name="Cathode_Coating_01",
            material_group=MaterialGroup.CATHODE_COATING,
            layer_index=1,
        )

        assert body.layer_index == 1

    def test_solid_property(self) -> None:
        """Should be able to set and get solid."""
        body = CADBody(
            name="Test",
            material_group=MaterialGroup.CASING,
        )

        # Initially None
        assert body.solid is None

        # Set solid
        mock_solid = object()
        body.solid = mock_solid
        assert body.solid is mock_solid


class TestCADAssembly:
    """Tests for CADAssembly class."""

    @pytest.fixture
    def sample_assembly(self) -> CADAssembly:
        """Create sample assembly for testing."""
        assembly = CADAssembly(name="Test_Assembly")
        assembly.bodies = [
            CADBody(name="Cathode_1", material_group=MaterialGroup.CATHODE_COATING),
            CADBody(name="Cathode_2", material_group=MaterialGroup.CATHODE_COATING),
            CADBody(name="Anode_1", material_group=MaterialGroup.ANODE_COATING),
            CADBody(name="Separator_1", material_group=MaterialGroup.SEPARATOR),
            CADBody(name="Casing", material_group=MaterialGroup.CASING),
        ]
        return assembly

    def test_body_count(self, sample_assembly: CADAssembly) -> None:
        """Should return correct body count."""
        assert sample_assembly.body_count() == 5

    def test_get_bodies_by_group(self, sample_assembly: CADAssembly) -> None:
        """Should filter bodies by material group."""
        cathodes = sample_assembly.get_bodies_by_group(MaterialGroup.CATHODE_COATING)
        assert len(cathodes) == 2

        anodes = sample_assembly.get_bodies_by_group(MaterialGroup.ANODE_COATING)
        assert len(anodes) == 1

        collectors = sample_assembly.get_bodies_by_group(MaterialGroup.CATHODE_COLLECTOR)
        assert len(collectors) == 0

    def test_summary(self, sample_assembly: CADAssembly) -> None:
        """Summary should count bodies per group."""
        summary = sample_assembly.summary()

        assert summary["Cathode_Coating"] == 2
        assert summary["Anode_Coating"] == 1
        assert summary["Separator"] == 1
        assert summary["Casing"] == 1
        assert "Cathode_Collector" not in summary  # Zero count not included

    def test_get_all_solids(self, sample_assembly: CADAssembly) -> None:
        """Should return list of non-None solids."""
        # Initially all solids are None
        solids = sample_assembly.get_all_solids()
        assert len(solids) == 0

        # Add some mock solids
        sample_assembly.bodies[0].solid = object()
        sample_assembly.bodies[1].solid = object()

        solids = sample_assembly.get_all_solids()
        assert len(solids) == 2

    def test_empty_assembly(self) -> None:
        """Empty assembly should work correctly."""
        assembly = CADAssembly(name="Empty")

        assert assembly.body_count() == 0
        assert assembly.summary() == {}
        assert assembly.get_all_solids() == []
