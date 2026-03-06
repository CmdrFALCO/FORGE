"""Tests for swelling profile calculations.

This module tests the SwellingProfile class including:
- Chemistry-specific swelling profiles
- Swelling factor application
- Profile comparisons
"""

import pytest

from forge.engine.geometry.swelling import (
    SWELLING_LFP,
    SWELLING_NCA,
    SWELLING_NMC811,
    SWELLING_NONE,
    SwellingProfile,
)


class TestSwellingProfileCreation:
    """Test SwellingProfile creation and defaults."""

    def test_default_profile(self):
        """Default profile should have reasonable swelling values."""
        profile = SwellingProfile()

        assert profile.cathode_coating > 1.0
        assert profile.anode_coating > 1.0
        assert profile.separator >= 1.0
        assert profile.current_collector == 1.0

    def test_no_swelling_profile(self):
        """No swelling profile should have all factors at 1.0."""
        profile = SwellingProfile.no_swelling()

        assert profile.cathode_coating == 1.0
        assert profile.anode_coating == 1.0
        assert profile.separator == 1.0
        assert profile.current_collector == 1.0


class TestChemistryProfiles:
    """Test chemistry-specific swelling profiles."""

    def test_lfp_profile(self):
        """LFP should have lower swelling than default."""
        profile = SwellingProfile.for_chemistry("LFP")

        assert profile.cathode_coating < 1.05
        assert profile.anode_coating < 1.08

    def test_nmc811_profile(self):
        """NMC811 should have higher swelling than LFP."""
        lfp = SwellingProfile.for_chemistry("LFP")
        nmc811 = SwellingProfile.for_chemistry("NMC811")

        assert nmc811.cathode_coating > lfp.cathode_coating
        assert nmc811.anode_coating > lfp.anode_coating

    def test_nmc_normalization(self):
        """NCM variants should be normalized to NMC."""
        ncm712 = SwellingProfile.for_chemistry("NCM712")
        nmc712 = SwellingProfile.for_chemistry("NMC712")

        assert ncm712.cathode_coating == nmc712.cathode_coating
        assert ncm712.anode_coating == nmc712.anode_coating

    def test_unknown_chemistry_uses_default(self):
        """Unknown chemistry should return default profile."""
        profile = SwellingProfile.for_chemistry("UNKNOWN_CHEMISTRY")
        default = SwellingProfile()

        assert profile.cathode_coating == default.cathode_coating
        assert profile.anode_coating == default.anode_coating

    def test_predefined_profiles(self):
        """Predefined profile constants should be correct."""
        assert SWELLING_LFP.cathode_coating == SwellingProfile.for_chemistry("LFP").cathode_coating
        assert SWELLING_NMC811.cathode_coating == SwellingProfile.for_chemistry("NMC811").cathode_coating
        assert SWELLING_NCA.cathode_coating == SwellingProfile.for_chemistry("NCA").cathode_coating
        assert SWELLING_NONE.cathode_coating == 1.0


class TestSwellingApplication:
    """Test applying swelling factors to thicknesses."""

    def test_apply_cathode_swelling(self):
        """Cathode coating should swell by cathode factor."""
        profile = SwellingProfile(cathode_coating=1.10)
        original = 100.0

        swollen = profile.apply_to_thickness("cathode_coating", original)

        assert swollen == pytest.approx(110.0, rel=0.001)

    def test_apply_anode_swelling(self):
        """Anode coating should swell by anode factor."""
        profile = SwellingProfile(anode_coating=1.08)
        original = 100.0

        swollen = profile.apply_to_thickness("anode_coating", original)

        assert swollen == pytest.approx(108.0, rel=0.001)

    def test_apply_separator_swelling(self):
        """Separator should swell by separator factor."""
        profile = SwellingProfile(separator=1.02)
        original = 20.0

        swollen = profile.apply_to_thickness("separator", original)

        assert swollen == pytest.approx(20.4, rel=0.001)

    def test_collectors_dont_swell(self):
        """Current collectors should not swell (metals)."""
        profile = SwellingProfile()

        assert profile.current_collector == 1.0

        cathode_coll = profile.apply_to_thickness("cathode_collector", 15.0)
        anode_coll = profile.apply_to_thickness("anode_collector", 10.0)

        assert cathode_coll == pytest.approx(15.0, rel=0.001)
        assert anode_coll == pytest.approx(10.0, rel=0.001)

    def test_unknown_component_no_swelling(self):
        """Unknown component should return unchanged thickness."""
        profile = SwellingProfile(cathode_coating=1.10, anode_coating=1.08)
        original = 100.0

        result = profile.apply_to_thickness("unknown_component", original)

        assert result == pytest.approx(original, rel=0.001)


class TestSwellingComparisons:
    """Test comparing swelling between chemistries."""

    def test_lfp_swells_less_than_nmc811(self):
        """LFP should have lower swelling than NMC811."""
        lfp = SwellingProfile.for_chemistry("LFP")
        nmc811 = SwellingProfile.for_chemistry("NMC811")

        assert lfp.cathode_coating < nmc811.cathode_coating
        assert lfp.anode_coating < nmc811.anode_coating
        assert lfp.separator < nmc811.separator

    def test_nmc622_between_532_and_811(self):
        """NMC622 should have swelling between NMC532 and NMC811."""
        nmc532 = SwellingProfile.for_chemistry("NMC532")
        nmc622 = SwellingProfile.for_chemistry("NMC622")
        nmc811 = SwellingProfile.for_chemistry("NMC811")

        assert nmc532.cathode_coating <= nmc622.cathode_coating <= nmc811.cathode_coating
        assert nmc532.anode_coating <= nmc622.anode_coating <= nmc811.anode_coating


class TestStackSwellingEstimate:
    """Test overall stack swelling estimation."""

    def test_stack_swelling_factor(self):
        """Stack swelling factor should be weighted average."""
        profile = SwellingProfile(
            cathode_coating=1.06,
            anode_coating=1.10,
            separator=1.02,
            current_collector=1.00,
        )

        stack_factor = profile.get_stack_swelling_factor()

        # Weighted: 0.4*1.06 + 0.4*1.10 + 0.1*1.02 + 0.1*1.00
        expected = 0.4 * 1.06 + 0.4 * 1.10 + 0.1 * 1.02 + 0.1 * 1.00
        assert stack_factor == pytest.approx(expected, rel=0.001)

    def test_no_swelling_stack_factor(self):
        """No swelling should give stack factor of 1.0."""
        profile = SwellingProfile.no_swelling()

        assert profile.get_stack_swelling_factor() == pytest.approx(1.0, rel=0.001)


class TestSwellingDescription:
    """Test human-readable swelling description."""

    def test_describe_returns_string(self):
        """describe() should return formatted string."""
        profile = SwellingProfile()

        description = profile.describe()

        assert isinstance(description, str)
        assert "Cathode coating" in description
        assert "Anode coating" in description
        assert "%" in description

    def test_describe_shows_percentages(self):
        """Description should show swelling as percentages."""
        profile = SwellingProfile(cathode_coating=1.05, anode_coating=1.08)

        description = profile.describe()

        assert "5.0%" in description  # Cathode
        assert "8.0%" in description  # Anode
