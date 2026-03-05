"""Tests for visualization color schemes."""

import pytest

from forge.gui.visualization.colors import ColorScheme, DEFAULT_COLORS


class TestColorScheme:
    """Tests for ColorScheme dataclass."""

    def test_default_instance(self) -> None:
        """Default colors should be initialized correctly."""
        colors = ColorScheme()

        assert colors.cathode_coating.startswith("rgba")
        assert colors.anode_coating.startswith("rgba")
        assert colors.cathode_collector.startswith("rgba")
        assert colors.anode_collector.startswith("rgba")
        assert colors.separator.startswith("rgba")

    def test_default_colors_singleton(self) -> None:
        """DEFAULT_COLORS should be a valid ColorScheme instance."""
        assert isinstance(DEFAULT_COLORS, ColorScheme)
        assert DEFAULT_COLORS.cathode_coating

    def test_chemistry_colors_initialized(self) -> None:
        """Chemistry-specific colors should be available after init."""
        colors = ColorScheme()

        # Check that chemistry dict is populated
        assert len(colors._cathode_by_chemistry) > 0
        assert "LFP" in colors._cathode_by_chemistry
        assert "NMC811" in colors._cathode_by_chemistry

    def test_get_cathode_color_lfp(self) -> None:
        """LFP should return green-ish cathode color."""
        colors = ColorScheme()
        lfp_color = colors.get_cathode_color("LFP")

        # LFP is green (iron phosphate)
        assert "rgba" in lfp_color
        # Extract RGB values
        parts = lfp_color.replace("rgba(", "").replace(")", "").split(",")
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])

        # Green should be higher than red
        assert g > r

    def test_get_cathode_color_nmc_variants(self) -> None:
        """NMC variants should return different shades."""
        colors = ColorScheme()

        nmc811 = colors.get_cathode_color("NMC811")
        nmc622 = colors.get_cathode_color("NMC622")
        nmc532 = colors.get_cathode_color("NMC532")

        # All should be valid RGBA
        assert "rgba" in nmc811
        assert "rgba" in nmc622
        assert "rgba" in nmc532

        # They should be different
        assert nmc811 != nmc622
        assert nmc622 != nmc532

    def test_ncm_to_nmc_normalization(self) -> None:
        """NCM should be normalized to NMC."""
        colors = ColorScheme()

        ncm811 = colors.get_cathode_color("NCM811")
        nmc811 = colors.get_cathode_color("NMC811")

        assert ncm811 == nmc811

    def test_case_insensitivity(self) -> None:
        """Chemistry lookup should be case-insensitive."""
        colors = ColorScheme()

        upper = colors.get_cathode_color("NMC811")
        lower = colors.get_cathode_color("nmc811")
        mixed = colors.get_cathode_color("Nmc811")

        assert upper == lower == mixed

    def test_unknown_chemistry_fallback(self) -> None:
        """Unknown chemistry should return default cathode color."""
        colors = ColorScheme()

        unknown = colors.get_cathode_color("SuperNewChemistry2099")

        assert unknown == colors.cathode_coating

    def test_get_layer_color_cathode_coating(self) -> None:
        """Cathode coating layer should use chemistry color."""
        colors = ColorScheme()

        # Without chemistry - use default
        color = colors.get_layer_color("cathode_coating")
        assert color == colors.cathode_coating

        # With chemistry - use chemistry-specific
        color_lfp = colors.get_layer_color("cathode_coating", chemistry="LFP")
        assert color_lfp == colors.get_cathode_color("LFP")

    def test_get_layer_color_anode(self) -> None:
        """Anode layers should return correct colors."""
        colors = ColorScheme()

        anode_coating = colors.get_layer_color("anode_coating")
        anode_collector = colors.get_layer_color("anode_collector")

        assert anode_coating == colors.anode_coating
        assert anode_collector == colors.anode_collector

    def test_get_layer_color_separator(self) -> None:
        """Separator should return separator color."""
        colors = ColorScheme()

        sep_color = colors.get_layer_color("separator")

        assert sep_color == colors.separator

    def test_get_layer_color_unknown(self) -> None:
        """Unknown layer type should return electrode_pair color."""
        colors = ColorScheme()

        unknown = colors.get_layer_color("unknown_layer_type")

        assert unknown == colors.electrode_pair

    def test_custom_color_scheme(self) -> None:
        """Custom colors should override defaults."""
        custom = ColorScheme(
            cathode_coating="rgba(255, 0, 0, 1.0)",
            anode_coating="rgba(0, 255, 0, 1.0)",
        )

        assert custom.cathode_coating == "rgba(255, 0, 0, 1.0)"
        assert custom.anode_coating == "rgba(0, 255, 0, 1.0)"

        # Other colors should still have defaults
        assert custom.separator == ColorScheme().separator

    def test_color_format_rgba(self) -> None:
        """All colors should be in RGBA format."""
        colors = ColorScheme()

        all_colors = [
            colors.cathode_coating,
            colors.anode_coating,
            colors.cathode_collector,
            colors.anode_collector,
            colors.separator,
            colors.can_wall,
            colors.pouch_film,
            colors.electrode_pair,
        ]

        for color in all_colors:
            assert color.startswith("rgba("), f"Color should be RGBA: {color}"
            assert color.endswith(")"), f"Color should end with ): {color}"

            # Should have 4 comma-separated values
            inner = color.replace("rgba(", "").replace(")", "")
            parts = inner.split(",")
            assert len(parts) == 4, f"RGBA should have 4 parts: {color}"

            # Alpha should be between 0 and 1
            alpha = float(parts[3].strip())
            assert 0 <= alpha <= 1, f"Alpha should be 0-1: {alpha}"


class TestColorSchemeChemistryMapping:
    """Tests for chemistry-specific color mapping."""

    @pytest.fixture
    def colors(self) -> ColorScheme:
        return ColorScheme()

    @pytest.mark.parametrize(
        "chemistry,expected_key",
        [
            ("LFP", "LFP"),
            ("NMC811", "NMC811"),
            ("NMC622", "NMC622"),
            ("NMC712", "NMC712"),
            ("NMC532", "NMC532"),
            ("NCA", "NCA"),
            ("LCO", "LCO"),
            ("LMO", "LMO"),
            ("LMFP", "LMFP"),
        ],
    )
    def test_known_chemistries(self, colors: ColorScheme, chemistry: str, expected_key: str) -> None:
        """Known chemistries should return their mapped colors."""
        color = colors.get_cathode_color(chemistry)
        expected = colors._cathode_by_chemistry.get(expected_key, colors.cathode_coating)

        assert color == expected

    @pytest.mark.parametrize(
        "chemistry",
        ["NCM811", "ncm811", "Ncm811", "NCM622", "ncm622"],
    )
    def test_ncm_variants(self, colors: ColorScheme, chemistry: str) -> None:
        """NCM should be normalized to NMC."""
        color = colors.get_cathode_color(chemistry)

        # Should match corresponding NMC
        expected_nmc = chemistry.upper().replace("NCM", "NMC")
        expected = colors.get_cathode_color(expected_nmc)

        assert color == expected

    @pytest.mark.parametrize(
        "variant",
        ["NMC811-Si", "NMC811_modified", "NMC811Plus"],
    )
    def test_chemistry_variants_prefix_match(self, colors: ColorScheme, variant: str) -> None:
        """Chemistry variants should match prefix."""
        color = colors.get_cathode_color(variant)

        # Should match base NMC811
        expected = colors.get_cathode_color("NMC811")
        assert color == expected

