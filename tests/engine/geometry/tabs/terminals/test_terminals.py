"""Tests for terminal assembly calculation."""

from pathlib import Path

import pytest

from forge.engine.geometry.tabs.models import Point3D, TabMaterial, TabPolarity
from forge.engine.geometry.tabs.terminals import (
    CurrentInterruptDevice,
    CylindricalHeaderCalculator,
    HeaderAssembly,
    InsulatorMaterial,
    InsulatorRing,
    PositiveCap,
    PouchTerminalCalculator,
    PrismaticTerminalCalculator,
    SealGasket,
    TerminalAssembly,
    TerminalPost,
    TerminalType,
    VentDisc,
    calculate_terminal_assembly,
)

ARCHETYPE_DIR = Path("docs")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def byd_blade_geometry():
    """Load BYD Blade prismatic cell geometry."""
    from forge.engine.geometry.loader import ArchetypeLoader

    path = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
    if not path.exists():
        pytest.skip(f"Archetype not found: {path}")
    loader = ArchetypeLoader(path)
    return loader.to_detailed_geometry()


@pytest.fixture
def tesla_4680_geometry():
    """Load Tesla 4680 cylindrical cell geometry."""
    from forge.engine.geometry.loader import ArchetypeLoader

    path = ARCHETYPE_DIR / "tesla_4680_archetype.json"
    if not path.exists():
        pytest.skip(f"Archetype not found: {path}")
    loader = ArchetypeLoader(path)
    return loader.to_detailed_geometry()


@pytest.fixture
def lg_e66a_geometry():
    """Load LG E66A pouch cell geometry."""
    from forge.engine.geometry.loader import ArchetypeLoader

    path = ARCHETYPE_DIR / "lg_e66a_archetype.json"
    if not path.exists():
        pytest.skip(f"Archetype not found: {path}")
    loader = ArchetypeLoader(path)
    return loader.to_detailed_geometry()


# =============================================================================
# Terminal Models Tests
# =============================================================================


class TestTerminalModels:
    """Test terminal model data structures."""

    def test_terminal_post_circular(self):
        """Should create circular terminal post."""
        terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            terminal_type=TerminalType.BOLT,
            position=Point3D(50, 0, 12.5),
            diameter_mm=12.0,
            height_mm=10.0,
            material=TabMaterial.ALUMINUM,
        )

        assert terminal.is_circular
        assert terminal.diameter_mm == 12.0
        assert terminal.terminal_type == TerminalType.BOLT
        assert terminal.polarity == TabPolarity.POSITIVE

    def test_terminal_post_rectangular(self):
        """Should create rectangular terminal post."""
        terminal = TerminalPost(
            polarity=TabPolarity.NEGATIVE,
            terminal_type=TerminalType.POST,
            position=Point3D(0, 0, 0),
            width_mm=40.0,
            length_mm=0.4,
            height_mm=20.0,
            material=TabMaterial.NICKEL_PLATED_COPPER,
        )

        assert not terminal.is_circular
        assert terminal.width_mm == 40.0
        assert terminal.terminal_type == TerminalType.POST

    def test_terminal_post_with_insulator(self):
        """Should create terminal post with insulator."""
        insulator = InsulatorRing(
            position=Point3D(50, 0, 12.5),
            outer_diameter_mm=20.0,
            inner_diameter_mm=13.0,
            thickness_mm=2.0,
            material=InsulatorMaterial.PLASTIC,
        )

        terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            terminal_type=TerminalType.BOLT,
            position=Point3D(50, 0, 12.5),
            diameter_mm=12.0,
            height_mm=10.0,
            insulator=insulator,
        )

        assert terminal.insulator is not None
        assert terminal.insulator.outer_diameter_mm == 20.0

    def test_terminal_post_to_dict(self):
        """Should serialize terminal post to dict."""
        terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            terminal_type=TerminalType.BOLT,
            position=Point3D(50, 0, 12.5),
            diameter_mm=12.0,
            height_mm=10.0,
        )

        data = terminal.to_dict()

        assert data["polarity"] == "positive"
        assert data["terminal_type"] == "bolt"
        assert data["diameter_mm"] == 12.0

    def test_insulator_ring(self):
        """Should create insulator ring."""
        insulator = InsulatorRing(
            position=Point3D(0, 0, 10),
            outer_diameter_mm=25.0,
            inner_diameter_mm=15.0,
            thickness_mm=2.0,
            material=InsulatorMaterial.PEEK,
        )

        assert insulator.outer_diameter_mm > insulator.inner_diameter_mm
        assert insulator.material == InsulatorMaterial.PEEK

    def test_seal_gasket_circular(self):
        """Should create circular seal gasket."""
        gasket = SealGasket(
            position=Point3D(0, 0, 5),
            outer_diameter_mm=30.0,
            inner_diameter_mm=20.0,
            thickness_mm=1.0,
            material=InsulatorMaterial.RUBBER,
        )

        assert gasket.is_circular
        assert gasket.outer_diameter_mm == 30.0

    def test_seal_gasket_rectangular(self):
        """Should create rectangular seal gasket."""
        gasket = SealGasket(
            position=Point3D(0, 0, 0),
            width_mm=50.0,
            length_mm=14.0,
            thickness_mm=2.0,
            material=InsulatorMaterial.PFA,
        )

        assert not gasket.is_circular
        assert gasket.width_mm == 50.0

    def test_vent_disc(self):
        """Should create vent disc."""
        vent = VentDisc(
            position=Point3D(0, 0, 38),
            diameter_mm=30.0,
            thickness_mm=0.3,
            burst_pressure_mpa=1.5,
        )

        assert vent.diameter_mm == 30.0
        assert vent.burst_pressure_mpa == 1.5

    def test_current_interrupt_device(self):
        """Should create CID."""
        cid = CurrentInterruptDevice(
            position=Point3D(0, 0, 37),
            diameter_mm=28.0,
            thickness_mm=0.5,
            trigger_pressure_mpa=1.0,
        )

        assert cid.diameter_mm == 28.0
        assert cid.trigger_pressure_mpa == 1.0

    def test_positive_cap(self):
        """Should create positive cap."""
        cap = PositiveCap(
            position=Point3D(0, 0, 39),
            outer_diameter_mm=44.0,
            inner_diameter_mm=32.0,
            height_mm=2.2,
            button_diameter_mm=14.0,
            button_height_mm=1.0,
        )

        assert cap.outer_diameter_mm == 44.0
        assert cap.button_diameter_mm == 14.0

    def test_header_assembly(self):
        """Should create header assembly."""
        header = HeaderAssembly(
            cell_diameter_mm=46.0,
            cell_height_mm=80.0,
            total_height_mm=5.5,
        )

        # Initially no components
        assert len(header.get_all_components()) == 0

        # Add cap
        header.positive_cap = PositiveCap(
            position=Point3D(0, 0, 39),
            outer_diameter_mm=44.0,
            inner_diameter_mm=32.0,
            height_mm=2.2,
        )

        assert len(header.get_all_components()) == 1
        assert header.get_all_components()[0][0] == "positive_cap"

    def test_terminal_assembly(self):
        """Should create terminal assembly."""
        assembly = TerminalAssembly(cell_type="prismatic")

        assembly.positive_terminal = TerminalPost(
            polarity=TabPolarity.POSITIVE,
            terminal_type=TerminalType.BOLT,
            position=Point3D(50, 0, 12.5),
            diameter_mm=12.0,
            height_mm=10.0,
        )

        assembly.negative_terminal = TerminalPost(
            polarity=TabPolarity.NEGATIVE,
            terminal_type=TerminalType.BOLT,
            position=Point3D(-50, 0, 12.5),
            diameter_mm=12.0,
            height_mm=10.0,
        )

        data = assembly.to_dict()

        assert data["cell_type"] == "prismatic"
        assert data["positive_terminal"] is not None
        assert data["negative_terminal"] is not None


# =============================================================================
# Pouch Terminal Calculator Tests
# =============================================================================


class TestPouchTerminalCalculator:
    """Test pouch cell terminal calculator."""

    def test_calculate_pouch_terminals(self, lg_e66a_geometry):
        """Should calculate pouch terminal assembly."""
        calc = PouchTerminalCalculator()
        assembly = calc.calculate(lg_e66a_geometry)

        assert assembly.cell_type == "pouch"
        assert assembly.positive_terminal is not None
        assert assembly.negative_terminal is not None
        assert assembly.positive_terminal.terminal_type == TerminalType.POST
        assert assembly.negative_terminal.terminal_type == TerminalType.POST

    def test_pouch_terminal_materials(self, lg_e66a_geometry):
        """Should use correct materials for pouch terminals."""
        calc = PouchTerminalCalculator()
        assembly = calc.calculate(lg_e66a_geometry)

        # Positive: aluminum, Negative: Ni-plated copper
        assert assembly.positive_terminal.material == TabMaterial.ALUMINUM
        assert assembly.negative_terminal.material == TabMaterial.NICKEL_PLATED_COPPER

    def test_pouch_seal_zones(self, lg_e66a_geometry):
        """Should include seal zones when requested."""
        calc = PouchTerminalCalculator(include_seal_zones=True)
        assembly = calc.calculate(lg_e66a_geometry)

        assert assembly.positive_terminal.gasket is not None
        assert assembly.negative_terminal.gasket is not None

    def test_pouch_no_seal_zones(self, lg_e66a_geometry):
        """Should exclude seal zones when disabled."""
        calc = PouchTerminalCalculator(include_seal_zones=False)
        assembly = calc.calculate(lg_e66a_geometry)

        assert assembly.positive_terminal.gasket is None
        assert assembly.negative_terminal.gasket is None

    def test_pouch_terminal_positions(self, lg_e66a_geometry):
        """Should position terminals on opposite edges."""
        calc = PouchTerminalCalculator()
        assembly = calc.calculate(lg_e66a_geometry)

        pos = assembly.positive_terminal.position
        neg = assembly.negative_terminal.position

        # Should be on opposite X edges
        assert pos.x > 0
        assert neg.x < 0


# =============================================================================
# Prismatic Terminal Calculator Tests
# =============================================================================


class TestPrismaticTerminalCalculator:
    """Test prismatic cell terminal calculator."""

    def test_calculate_prismatic_terminals(self, byd_blade_geometry):
        """Should calculate prismatic terminal assembly."""
        calc = PrismaticTerminalCalculator()
        assembly = calc.calculate(byd_blade_geometry)

        assert assembly.cell_type == "prismatic"
        assert assembly.positive_terminal is not None
        assert assembly.negative_terminal is not None
        assert assembly.positive_terminal.terminal_type == TerminalType.BOLT
        assert assembly.negative_terminal.terminal_type == TerminalType.BOLT

    def test_prismatic_terminal_threading(self, byd_blade_geometry):
        """Should include thread dimensions for bolt terminals."""
        calc = PrismaticTerminalCalculator()
        assembly = calc.calculate(byd_blade_geometry)

        assert assembly.positive_terminal.thread_diameter_mm is not None
        assert assembly.positive_terminal.thread_pitch_mm is not None

    def test_prismatic_insulators(self, byd_blade_geometry):
        """Should include insulators when requested."""
        calc = PrismaticTerminalCalculator(include_insulators=True)
        assembly = calc.calculate(byd_blade_geometry)

        assert assembly.positive_terminal.insulator is not None
        assert assembly.negative_terminal.insulator is not None

    def test_prismatic_no_insulators(self, byd_blade_geometry):
        """Should exclude insulators when disabled."""
        calc = PrismaticTerminalCalculator(include_insulators=False)
        assembly = calc.calculate(byd_blade_geometry)

        assert assembly.positive_terminal.insulator is None
        assert assembly.negative_terminal.insulator is None

    def test_prismatic_gaskets(self, byd_blade_geometry):
        """Should include gaskets when requested."""
        calc = PrismaticTerminalCalculator(include_gaskets=True)
        assembly = calc.calculate(byd_blade_geometry)

        assert assembly.positive_terminal.gasket is not None
        assert assembly.negative_terminal.gasket is not None

    def test_prismatic_terminal_spacing(self, byd_blade_geometry):
        """Should respect terminal spacing ratio."""
        calc = PrismaticTerminalCalculator(terminal_spacing_ratio=0.8)
        assembly = calc.calculate(byd_blade_geometry)

        ext = byd_blade_geometry.external_geometry
        expected_spacing = (ext.length_mm or 150.0) * 0.8

        pos = assembly.positive_terminal.position
        neg = assembly.negative_terminal.position
        actual_spacing = abs(pos.x - neg.x)

        assert abs(actual_spacing - expected_spacing) < 0.1


# =============================================================================
# Cylindrical Header Calculator Tests
# =============================================================================


class TestCylindricalHeaderCalculator:
    """Test cylindrical cell header calculator."""

    def test_calculate_header_assembly(self, tesla_4680_geometry):
        """Should calculate complete header assembly."""
        calc = CylindricalHeaderCalculator()
        assembly = calc.calculate(tesla_4680_geometry)

        assert assembly.cell_type == "cylindrical"
        assert assembly.header_assembly is not None
        assert assembly.header_assembly.positive_cap is not None

    def test_header_includes_vent(self, tesla_4680_geometry):
        """Should include vent disc."""
        calc = CylindricalHeaderCalculator(include_vent=True)
        assembly = calc.calculate(tesla_4680_geometry)

        assert assembly.header_assembly.vent_disc is not None

    def test_header_no_vent(self, tesla_4680_geometry):
        """Should exclude vent disc when disabled."""
        calc = CylindricalHeaderCalculator(include_vent=False)
        assembly = calc.calculate(tesla_4680_geometry)

        assert assembly.header_assembly.vent_disc is None

    def test_header_includes_cid(self, tesla_4680_geometry):
        """Should include CID when requested."""
        calc = CylindricalHeaderCalculator(include_cid=True)
        assembly = calc.calculate(tesla_4680_geometry)

        assert assembly.header_assembly.cid is not None

    def test_header_no_cid(self, tesla_4680_geometry):
        """Should exclude CID when disabled."""
        calc = CylindricalHeaderCalculator(include_cid=False)
        assembly = calc.calculate(tesla_4680_geometry)

        assert assembly.header_assembly.cid is None

    def test_button_style(self, tesla_4680_geometry):
        """Should create button-style cap."""
        calc = CylindricalHeaderCalculator(button_style=True)
        assembly = calc.calculate(tesla_4680_geometry)

        cap = assembly.header_assembly.positive_cap
        assert cap.button_diameter_mm is not None
        assert cap.button_height_mm is not None

    def test_flat_top_style(self, tesla_4680_geometry):
        """Should create flat-top cap."""
        calc = CylindricalHeaderCalculator(button_style=False)
        assembly = calc.calculate(tesla_4680_geometry)

        cap = assembly.header_assembly.positive_cap
        assert cap.button_diameter_mm is None
        assert cap.button_height_mm is None

    def test_cylindrical_terminals(self, tesla_4680_geometry):
        """Should have button and can_bottom terminals."""
        calc = CylindricalHeaderCalculator()
        assembly = calc.calculate(tesla_4680_geometry)

        assert assembly.positive_terminal.terminal_type == TerminalType.BUTTON
        assert assembly.negative_terminal.terminal_type == TerminalType.CAN_BOTTOM

    def test_can_bottom_position(self, tesla_4680_geometry):
        """Should position can bottom at cell bottom."""
        calc = CylindricalHeaderCalculator()
        assembly = calc.calculate(tesla_4680_geometry)

        ext = tesla_4680_geometry.external_geometry
        height = ext.height_mm or 80.0

        neg_pos = assembly.negative_terminal.position
        assert neg_pos.z == pytest.approx(-height / 2, abs=0.1)


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunction:
    """Test calculate_terminal_assembly convenience function."""

    def test_auto_detect_pouch(self, lg_e66a_geometry):
        """Should auto-detect pouch cell type."""
        assembly = calculate_terminal_assembly(lg_e66a_geometry)

        assert assembly.cell_type == "pouch"
        assert assembly.positive_terminal.terminal_type == TerminalType.POST

    def test_auto_detect_prismatic(self, byd_blade_geometry):
        """Should auto-detect prismatic cell type."""
        assembly = calculate_terminal_assembly(byd_blade_geometry)

        assert assembly.cell_type == "prismatic"
        assert assembly.positive_terminal.terminal_type == TerminalType.BOLT

    def test_auto_detect_cylindrical(self, tesla_4680_geometry):
        """Should auto-detect cylindrical cell type."""
        assembly = calculate_terminal_assembly(tesla_4680_geometry)

        assert assembly.cell_type == "cylindrical"
        assert assembly.positive_terminal.terminal_type == TerminalType.BUTTON

    def test_pass_options(self, tesla_4680_geometry):
        """Should pass options to calculator."""
        assembly = calculate_terminal_assembly(
            tesla_4680_geometry,
            include_cid=False,
        )

        assert assembly.header_assembly.cid is None


# =============================================================================
# Archetype Parametrized Tests
# =============================================================================


@pytest.mark.parametrize(
    "archetype_file",
    [
        "byd_blade_138ah_archetype.json",
        "tesla_4680_archetype.json",
        "lg_e66a_archetype.json",
        "samsung_21700_50g_archetype.json",
        "samsung_sdi_94ah_archetype.json",
    ],
)
class TestAllArchetypes:
    """Test terminal calculation for all archetypes."""

    def test_archetype_terminal_calculation(self, archetype_file):
        """All archetypes should calculate terminal assemblies."""
        from forge.engine.geometry.loader import ArchetypeLoader

        path = ARCHETYPE_DIR / archetype_file
        if not path.exists():
            pytest.skip(f"Archetype not found: {archetype_file}")

        loader = ArchetypeLoader(path)
        geometry = loader.to_detailed_geometry()

        assembly = calculate_terminal_assembly(geometry)

        assert assembly is not None
        assert assembly.positive_terminal is not None
        assert assembly.negative_terminal is not None

    def test_archetype_terminal_serialization(self, archetype_file):
        """All terminal assemblies should serialize."""
        from forge.engine.geometry.loader import ArchetypeLoader

        path = ARCHETYPE_DIR / archetype_file
        if not path.exists():
            pytest.skip(f"Archetype not found: {archetype_file}")

        loader = ArchetypeLoader(path)
        geometry = loader.to_detailed_geometry()

        assembly = calculate_terminal_assembly(geometry)
        data = assembly.to_dict()

        assert "cell_type" in data
        assert "positive_terminal" in data
        assert "negative_terminal" in data
