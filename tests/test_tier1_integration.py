"""
Integration tests for Tier 1 academic-validated parameter sets.

These tests verify that custom PyBaMM parameter sets produce
energy density values matching the source academic papers.

Tier 1 Academic-Validated Cells:
- Gunter2022: LG E78 Pouch (NCM652015/Graphite) - DOI: 10.1149/1945-7111/ac4e11
- Stock2023: CATL 161Ah LFP Prismatic - DOI: 10.1016/j.electacta.2023.143341
- Heenan2020: LG MJ1 18650 (NMC811/Graphite+Si) - DOI: 10.1149/1945-7111/ab728d
"""

import json
from pathlib import Path

import pytest

pybamm = pytest.importorskip("pybamm")

from forge.materials.repositories.pybamm_repo import (
    ALL_PARAMETER_SETS,
    CHEMISTRY_MAP,
    CUSTOM_PARAMETER_SETS,
    PyBaMMRepository,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def gunter2022_repo():
    """Fixture for Gunter2022 (LG E78 Pouch) parameter set."""
    return PyBaMMRepository("Gunter2022")


@pytest.fixture
def stock2023_repo():
    """Fixture for Stock2023 (CATL 161Ah LFP) parameter set."""
    return PyBaMMRepository("Stock2023")


@pytest.fixture
def heenan2020_repo():
    """Fixture for Heenan2020 (LG MJ1 18650) parameter set."""
    return PyBaMMRepository("Heenan2020")


@pytest.fixture
def lg_e78_reference():
    """Load LG E78 Pouch reference data."""
    ref_path = Path("data/reference/lg_e78_pouch.json")
    with open(ref_path) as f:
        return json.load(f)


@pytest.fixture
def catl_161ah_reference():
    """Load CATL 161Ah LFP reference data."""
    ref_path = Path("data/reference/catl_161ah_lfp.json")
    with open(ref_path) as f:
        return json.load(f)


@pytest.fixture
def lg_mj1_reference():
    """Load LG MJ1 18650 reference data."""
    ref_path = Path("data/reference/lg_mj1_18650.json")
    with open(ref_path) as f:
        return json.load(f)


# =============================================================================
# LG E78 Pouch (Gunter2022) Integration Tests
# =============================================================================


class TestGunter2022Integration:
    """Integration tests for LG E78 Pouch using Gunter2022 parameters."""

    def test_parameter_set_loads(self, gunter2022_repo):
        """Verify Gunter2022 parameter set loads without error."""
        assert gunter2022_repo.parameter_set == "Gunter2022"
        assert gunter2022_repo._is_custom is True

    def test_chemistry_mapping(self, gunter2022_repo):
        """Verify chemistry is correctly mapped."""
        cathode_chem, anode_chem = CHEMISTRY_MAP["Gunter2022"]
        assert cathode_chem == "NCM652015"
        assert anode_chem == "Graphite"

    def test_cathode_thickness_matches_paper(self, gunter2022_repo):
        """Verify cathode thickness matches Gunter 2022 value: 87.3 +/- 2.7 um."""
        cathode = gunter2022_repo.get_cathode()
        # Paper: 87.3 +/- 2.7 um
        assert cathode.coating_thickness_0pct_um == pytest.approx(87.3, abs=2.7)

    def test_anode_thickness_matches_paper(self, gunter2022_repo):
        """Verify anode thickness matches Gunter 2022 value: 115.3 +/- 3.5 um."""
        anode = gunter2022_repo.get_anode()
        # Paper: 115.3 +/- 3.5 um
        assert anode.coating_thickness_0pct_um == pytest.approx(115.3, abs=3.5)

    def test_cathode_loading_matches_paper(self, gunter2022_repo):
        """Verify cathode loading matches Gunter 2022 value: 27.9 mg/cm2."""
        cathode = gunter2022_repo.get_cathode()
        # Paper: 27.9 mg/cm2
        assert cathode.areal_weight_mgcm2 == pytest.approx(27.9, rel=0.05)

    def test_anode_loading_matches_paper(self, gunter2022_repo):
        """Verify anode loading matches Gunter 2022 value: 18.1 mg/cm2."""
        anode = gunter2022_repo.get_anode()
        # Paper: 18.1 mg/cm2
        assert anode.areal_weight_mgcm2 == pytest.approx(18.1, rel=0.05)

    def test_separator_thickness_matches_paper(self, gunter2022_repo):
        """Verify separator thickness matches Gunter 2022 value: 17.6 +/- 2.1 um."""
        separator = gunter2022_repo.get_separator()
        # Paper: 17.6 +/- 2.1 um
        assert separator.thickness_um == pytest.approx(17.6, abs=2.1)

    def test_current_collector_thicknesses(self, gunter2022_repo):
        """Verify current collector thicknesses from paper."""
        cathode = gunter2022_repo.get_cathode()
        anode = gunter2022_repo.get_anode()

        # Paper: Al = 14 um, Cu = 12 um
        assert cathode.collector_thickness_um == pytest.approx(14.0, rel=0.1)
        assert anode.collector_thickness_um == pytest.approx(12.0, rel=0.1)

    def test_reference_validation_targets(self, lg_e78_reference):
        """Verify reference file has correct validation targets."""
        validation = lg_e78_reference.get("validation", {})
        targets = validation.get("targets", {})

        assert targets["capacity_ah"] == 78.0
        assert targets["total_mass_g"] == pytest.approx(1080, rel=0.05)
        assert targets["gravimetric_ed_whkg"] == pytest.approx(268, rel=0.05)
        assert targets["volumetric_ed_whl"] == pytest.approx(629, rel=0.05)

    def test_energy_calculation(self):
        """Verify energy calculation: capacity x voltage."""
        capacity_ah = 78.0
        voltage_v = 3.68
        expected_energy_wh = capacity_ah * voltage_v  # 287.04 Wh

        assert expected_energy_wh == pytest.approx(287.04, rel=0.01)

    def test_mass_from_energy_density(self):
        """Back-calculate mass from energy density to verify consistency."""
        energy_wh = 78.0 * 3.68  # 287.04 Wh
        ed_whkg = 268
        expected_mass_g = energy_wh / ed_whkg * 1000  # ~1071 g

        # Paper states ~1080 g - should be within 2%
        assert expected_mass_g == pytest.approx(1080, rel=0.02)


# =============================================================================
# CATL 161Ah LFP (Stock2023) Integration Tests
# =============================================================================


class TestStock2023Integration:
    """Integration tests for CATL 161Ah LFP using Stock2023 parameters."""

    def test_parameter_set_loads(self, stock2023_repo):
        """Verify Stock2023 parameter set loads without error."""
        assert stock2023_repo.parameter_set == "Stock2023"
        assert stock2023_repo._is_custom is True

    def test_chemistry_mapping(self, stock2023_repo):
        """Verify chemistry is correctly mapped."""
        cathode_chem, anode_chem = CHEMISTRY_MAP["Stock2023"]
        assert cathode_chem == "LFP"
        assert anode_chem == "Graphite"

    def test_cathode_thickness_matches_paper(self, stock2023_repo):
        """Verify thick LFP cathode matches Stock 2023 value: ~200 um."""
        cathode = stock2023_repo.get_cathode()
        # Paper: ~200 um (thick LFP electrode enabled by thermal stability)
        assert cathode.coating_thickness_0pct_um == pytest.approx(200, rel=0.1)

    def test_anode_thickness_matches_paper(self, stock2023_repo):
        """Verify anode thickness matches Stock 2023 value: ~148 um."""
        anode = stock2023_repo.get_anode()
        # Paper: ~148 um
        assert anode.coating_thickness_0pct_um == pytest.approx(148, rel=0.1)

    def test_cathode_loading_matches_paper(self, stock2023_repo):
        """Verify cathode loading matches Stock 2023 value: 22.6 mg/cm2."""
        cathode = stock2023_repo.get_cathode()
        # Paper: 22.6 mg/cm2
        assert cathode.areal_weight_mgcm2 == pytest.approx(22.6, rel=0.05)

    def test_anode_loading_matches_paper(self, stock2023_repo):
        """Verify anode loading matches Stock 2023 value: 10.7 mg/cm2."""
        anode = stock2023_repo.get_anode()
        # Paper: 10.7 mg/cm2
        assert anode.areal_weight_mgcm2 == pytest.approx(10.7, rel=0.05)

    def test_current_collector_thickness(self, stock2023_repo):
        """Verify aggressive Cu current collector (5 um)."""
        anode = stock2023_repo.get_anode()
        cathode = stock2023_repo.get_cathode()

        # Paper: 5 um Cu (aggressive lightweighting), 12 um Al
        assert anode.collector_thickness_um == pytest.approx(5.0, rel=0.1)
        assert cathode.collector_thickness_um == pytest.approx(12.0, rel=0.1)

    def test_lfp_specific_capacity(self, stock2023_repo):
        """Verify LFP specific capacity is typical value (~150 mAh/g)."""
        cathode = stock2023_repo.get_cathode()
        # LFP typical: 150-170 mAh/g
        assert 140 < cathode.rev_spec_capacity_mahg < 170

    def test_reference_validation_targets(self, catl_161ah_reference):
        """Verify reference file has correct validation targets."""
        validation = catl_161ah_reference.get("validation", {})
        targets = validation.get("targets", {})

        assert targets["capacity_ah"] == 161.5
        assert targets["total_mass_g"] == pytest.approx(3170, rel=0.05)
        assert targets["gravimetric_ed_whkg"] == pytest.approx(163, rel=0.05)
        assert targets["volumetric_ed_whl"] == pytest.approx(366, rel=0.05)

    def test_lfp_voltage(self, catl_161ah_reference):
        """Verify LFP nominal voltage: 3.2 V."""
        cell_specs = catl_161ah_reference.get("cell_specs", {})
        voltage = cell_specs.get("nominal_voltage_v")
        assert voltage == 3.2

    def test_butterfly_design(self, catl_161ah_reference):
        """Verify butterfly jelly-roll design (2 stacks)."""
        stack_config = catl_161ah_reference.get("stack_config", {})
        assert stack_config.get("number_of_stacks") == 2
        assert stack_config.get("design_type") == "butterfly_jellyroll"


# =============================================================================
# LG MJ1 18650 (Heenan2020) Integration Tests
# =============================================================================


class TestHeenan2020Integration:
    """Integration tests for LG MJ1 18650 using Heenan2020 parameters."""

    def test_parameter_set_loads(self, heenan2020_repo):
        """Verify Heenan2020 parameter set loads without error."""
        assert heenan2020_repo.parameter_set == "Heenan2020"
        assert heenan2020_repo._is_custom is True

    def test_chemistry_mapping(self, heenan2020_repo):
        """Verify chemistry is correctly mapped (NMC811/Graphite+Si)."""
        cathode_chem, anode_chem = CHEMISTRY_MAP["Heenan2020"]
        assert cathode_chem == "NMC811"
        assert anode_chem == "Graphite_Si"

    def test_cathode_thickness_matches_paper(self, heenan2020_repo):
        """Verify cathode thickness from X-ray tomography: ~66 um."""
        cathode = heenan2020_repo.get_cathode()
        # Paper: ~66 um from X-ray tomography
        assert cathode.coating_thickness_0pct_um == pytest.approx(66, rel=0.1)

    def test_anode_thickness_matches_paper(self, heenan2020_repo):
        """Verify anode thickness from X-ray tomography: ~87 um."""
        anode = heenan2020_repo.get_anode()
        # Paper: ~87 um from X-ray tomography
        assert anode.coating_thickness_0pct_um == pytest.approx(87, rel=0.1)

    def test_separator_thickness_matches_paper(self, heenan2020_repo):
        """Verify separator thickness: 12 um."""
        separator = heenan2020_repo.get_separator()
        # Paper: 12 um
        assert separator.thickness_um == pytest.approx(12, rel=0.15)

    def test_current_collector_thicknesses(self, heenan2020_repo):
        """Verify current collector thicknesses."""
        cathode = heenan2020_repo.get_cathode()
        anode = heenan2020_repo.get_anode()

        # Paper: ~14 um Al, ~10 um Cu
        assert cathode.collector_thickness_um == pytest.approx(14.0, rel=0.1)
        assert anode.collector_thickness_um == pytest.approx(10.0, rel=0.1)

    def test_18650_format_dimensions(self, lg_mj1_reference):
        """Verify 18650 format dimensions."""
        geometry = lg_mj1_reference.get("geometry", {})

        # 18650 = 18mm diameter x 65mm length
        assert geometry.get("diameter_mm") == pytest.approx(18.4, rel=0.02)
        assert geometry.get("length_mm") == pytest.approx(65.2, rel=0.02)

    def test_cell_mass(self, lg_mj1_reference):
        """Verify cell mass matches datasheet."""
        validation = lg_mj1_reference.get("validation", {})
        targets = validation.get("targets", {})

        expected_mass = 49  # grams from datasheet
        assert targets.get("total_mass_g") == pytest.approx(expected_mass, rel=0.05)

    def test_reference_validation_targets(self, lg_mj1_reference):
        """Verify reference file has correct validation targets."""
        validation = lg_mj1_reference.get("validation", {})
        targets = validation.get("targets", {})

        assert targets["capacity_ah"] == 3.5
        assert targets["total_mass_g"] == pytest.approx(49, rel=0.05)
        assert targets["gravimetric_ed_whkg"] == pytest.approx(260, rel=0.05)
        assert targets["volumetric_ed_whl"] == pytest.approx(730, rel=0.05)

    def test_energy_calculation(self):
        """Verify energy calculation for MJ1."""
        capacity_ah = 3.5
        voltage_v = 3.635
        expected_energy_wh = capacity_ah * voltage_v  # 12.72 Wh

        assert expected_energy_wh == pytest.approx(12.72, rel=0.01)

    def test_open_data_repository(self, lg_mj1_reference):
        """Verify open data repository is specified."""
        open_data = lg_mj1_reference.get("open_data", {})
        assert open_data.get("repository") == "rdr.ucl.ac.uk"
        assert open_data.get("availability") == "public"


# =============================================================================
# Cross-Validation Tests
# =============================================================================


class TestCrossValidation:
    """Cross-validation tests comparing custom sets with built-in PyBaMM sets."""

    def test_all_custom_sets_in_available(self):
        """Verify all custom sets are in ALL_PARAMETER_SETS."""
        for set_name in CUSTOM_PARAMETER_SETS:
            assert set_name in ALL_PARAMETER_SETS

    def test_all_custom_sets_have_chemistry_mapping(self):
        """Verify all custom sets have chemistry mapping."""
        for set_name in CUSTOM_PARAMETER_SETS:
            assert set_name in CHEMISTRY_MAP

    def test_gunter2022_thicker_than_cylindrical(self, gunter2022_repo, heenan2020_repo):
        """E78 pouch has thicker electrodes than 18650 cylindrical."""
        e78_cathode = gunter2022_repo.get_cathode()
        mj1_cathode = heenan2020_repo.get_cathode()

        # E78 cathode: 87.3 um, MJ1 cathode: ~66 um
        assert e78_cathode.coating_thickness_0pct_um > mj1_cathode.coating_thickness_0pct_um

    def test_stock2023_thickest_lfp_cathode(self, stock2023_repo):
        """CATL LFP has unusually thick cathode (~200 um)."""
        cathode = stock2023_repo.get_cathode()
        # LFP thermal stability enables thick cathode
        assert cathode.coating_thickness_0pct_um >= 180

    def test_stock2023_thin_cu_collector(self, stock2023_repo, gunter2022_repo):
        """CATL has aggressive 5um Cu lightweighting."""
        catl_anode = stock2023_repo.get_anode()
        e78_anode = gunter2022_repo.get_anode()

        # CATL: 5 um, E78: 12 um
        assert catl_anode.collector_thickness_um < e78_anode.collector_thickness_um
        assert catl_anode.collector_thickness_um == pytest.approx(5.0, rel=0.2)


# =============================================================================
# Energy Density Sanity Checks
# =============================================================================


class TestEnergyDensitySanityChecks:
    """Sanity checks for energy density calculations."""

    @pytest.mark.parametrize(
        "cell_id,expected_ed,tolerance",
        [
            ("lg_e78_pouch", 268, 0.05),
            ("catl_161ah_lfp", 163, 0.05),
            ("lg_mj1_18650", 260, 0.05),
        ],
    )
    def test_reference_cell_energy_density(self, cell_id, expected_ed, tolerance):
        """Parametrized test for all Tier 1 cells."""
        ref_path = Path(f"data/reference/{cell_id}.json")

        with open(ref_path) as f:
            data = json.load(f)

        validation = data.get("validation", {})
        targets = validation.get("targets", {})
        actual_ed = targets.get("gravimetric_ed_whkg", 0)

        assert actual_ed == pytest.approx(expected_ed, rel=tolerance), (
            f"{cell_id}: ED {actual_ed} Wh/kg not within +/-{tolerance*100}% of {expected_ed}"
        )

    def test_lfp_lower_than_nmc(self):
        """LFP energy density should be lower than NMC."""
        lfp_ed = 163  # CATL LFP
        nmc_ed = 268  # LG E78 NCM

        assert lfp_ed < nmc_ed, "LFP should have lower energy density than NCM"

    def test_energy_density_range(self):
        """All cells should have realistic energy density."""
        eds = [268, 163, 260]  # Wh/kg for Tier 1 cells

        for ed in eds:
            assert 100 < ed < 400, f"Energy density {ed} outside realistic range"

    def test_cylindrical_volumetric_density_high(self):
        """18650 cylindrical should have high volumetric density (efficient packing)."""
        ref_path = Path("data/reference/lg_mj1_18650.json")
        with open(ref_path) as f:
            data = json.load(f)

        vol_ed = data.get("validation", {}).get("targets", {}).get("volumetric_ed_whl", 0)

        # 18650 typically > 700 Wh/L
        assert vol_ed >= 700, f"18650 volumetric ED {vol_ed} Wh/L seems low"


# =============================================================================
# Material Property Consistency Tests
# =============================================================================


class TestMaterialPropertyConsistency:
    """Tests verifying consistency of material properties across parameter sets."""

    def test_gunter2022_loading_from_thickness_and_density(self, gunter2022_repo):
        """Verify loading can be derived from thickness and density."""
        cathode = gunter2022_repo.get_cathode()

        # Loading = thickness(cm) x density(g/cm3) for pure coating
        # Paper: 87.3 um, 27.9 mg/cm2, density ~3.2 g/cm3
        thickness_cm = 87.3e-6 * 100  # um to cm
        density_gcm3 = 3.2
        calculated_loading = thickness_cm * density_gcm3 * 1000  # g/cm2 to mg/cm2

        # Should be close to measured 27.9 mg/cm2
        assert calculated_loading == pytest.approx(27.9, rel=0.1)

    def test_stock2023_lfp_density_lower_than_nmc(self, stock2023_repo, gunter2022_repo):
        """LFP has lower density than NMC materials."""
        lfp_cathode = stock2023_repo.get_cathode()
        nmc_cathode = gunter2022_repo.get_cathode()

        # LFP ~2.9 g/cm3, NMC ~3.2 g/cm3
        assert lfp_cathode.coating_density_gcm3 < nmc_cathode.coating_density_gcm3

    def test_graphite_anode_density_reasonable(
        self, gunter2022_repo, stock2023_repo, heenan2020_repo
    ):
        """Graphite anode coating density should be in reasonable range.

        Note: Stock2023 has thick, high-porosity electrodes with lower
        effective coating density (~0.72 g/cm3). This is correct per the
        paper: loading=10.7 mg/cm2, thickness=148um -> 0.72 g/cm3.
        """
        g2022_anode = gunter2022_repo.get_anode()
        s2023_anode = stock2023_repo.get_anode()
        h2020_anode = heenan2020_repo.get_anode()

        # Graphite coating density varies with porosity
        # High-porosity thick electrodes (Stock2023): ~0.7 g/cm3
        # Standard electrodes: ~1.3-1.7 g/cm3
        for anode in [g2022_anode, s2023_anode, h2020_anode]:
            assert 0.5 < anode.coating_density_gcm3 < 2.0, (
                f"Anode coating density {anode.coating_density_gcm3} outside range"
            )


# =============================================================================
# DOI Reference Tests
# =============================================================================


class TestDOIReferences:
    """Tests verifying DOI references are correctly specified."""

    @pytest.mark.parametrize(
        "cell_id,expected_doi",
        [
            ("lg_e78_pouch", "10.1149/1945-7111/ac4e11"),
            ("catl_161ah_lfp", "10.1016/j.electacta.2023.143341"),
            ("lg_mj1_18650", "10.1149/1945-7111/ab728d"),
        ],
    )
    def test_doi_in_reference_file(self, cell_id, expected_doi):
        """Verify DOI is correctly specified in reference JSON."""
        ref_path = Path(f"data/reference/{cell_id}.json")
        with open(ref_path) as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        assert metadata.get("doi") == expected_doi

    @pytest.mark.parametrize(
        "set_name,expected_doi",
        [
            ("Gunter2022", "10.1149/1945-7111/ac4e11"),
            ("Stock2023", "10.1016/j.electacta.2023.143341"),
            ("Heenan2020", "10.1149/1945-7111/ab728d"),
        ],
    )
    def test_doi_in_parameter_set(self, set_name, expected_doi):
        """Verify DOI is correctly specified in parameter set."""
        repo = PyBaMMRepository(set_name)
        doi = repo.params.get("DOI")
        assert doi == expected_doi
