"""Tests for custom academic-validated PyBaMM parameter sets.

These tests verify that the custom parameter sets from peer-reviewed
publications are correctly loaded and integrated with the PyBaMM repository.

Tier 1 Academic-Validated Cells:
- Gunter2022: LG E78 Pouch (NCM652015/Graphite) - DOI: 10.1149/1945-7111/ac4e11
- Stock2023: CATL 161Ah LFP Prismatic - DOI: 10.1016/j.electacta.2023.143341
- Heenan2020: LG MJ1 18650 (NMC811/Graphite+Si) - DOI: 10.1149/1945-7111/ab728d
"""

# ruff: noqa: E402

import pytest

pybamm = pytest.importorskip("pybamm")

from forge.materials.academic import (
    CUSTOM_CHEMISTRY_MAP,
    CUSTOM_PARAMETER_SETS,
    get_custom_parameters,
    list_custom_parameter_sets,
)
from forge.materials.academic.gunter2022_lge78 import (
    PARAMETER_CONFIDENCE,
    VALIDATION_TARGETS,
)
from forge.materials.academic.gunter2022_lge78 import (
    get_parameter_values as get_gunter2022,
)
from forge.materials.academic.heenan2020_lgmj1 import OPEN_DATA
from forge.materials.academic.heenan2020_lgmj1 import (
    get_parameter_values as get_heenan2020,
)
from forge.materials.academic.stock2023_catl161 import DESIGN_NOTES
from forge.materials.academic.stock2023_catl161 import (
    get_parameter_values as get_stock2023,
)
from forge.materials.repositories.pybamm_repo import (
    ALL_PARAMETER_SETS,
    CHEMISTRY_MAP,
    PyBaMMRepository,
)
from forge.materials.repositories.pybamm_repo import (
    CUSTOM_PARAMETER_SETS as REPO_CUSTOM_SETS,
)


class TestParameterModule:
    """Tests for the parameters module structure."""

    def test_list_custom_parameter_sets(self):
        """Verify all custom sets are listed."""
        sets = list_custom_parameter_sets()
        assert len(sets) == 3
        assert "Gunter2022" in sets
        assert "Stock2023" in sets
        assert "Heenan2020" in sets

    def test_get_custom_parameters_gunter2022(self):
        """Verify Gunter2022 parameters load correctly."""
        params = get_custom_parameters("Gunter2022")
        assert isinstance(params, dict)
        assert "Positive electrode thickness [m]" in params
        assert "Negative electrode thickness [m]" in params

    def test_get_custom_parameters_stock2023(self):
        """Verify Stock2023 parameters load correctly."""
        params = get_custom_parameters("Stock2023")
        assert isinstance(params, dict)
        assert params["Nominal cell capacity [A.h]"] == 161.5

    def test_get_custom_parameters_heenan2020(self):
        """Verify Heenan2020 parameters load correctly."""
        params = get_custom_parameters("Heenan2020")
        assert isinstance(params, dict)
        assert params["Nominal cell capacity [A.h]"] == 3.5

    def test_get_custom_parameters_invalid(self):
        """Verify error on invalid set name."""
        with pytest.raises(ValueError, match="Unknown parameter set"):
            get_custom_parameters("InvalidSet")

    def test_chemistry_map_has_all_custom_sets(self):
        """Verify all custom sets have chemistry mapping."""
        for set_name in CUSTOM_PARAMETER_SETS:
            assert set_name in CUSTOM_CHEMISTRY_MAP


class TestGunter2022Parameters:
    """Tests for LG E78 Pouch parameters from Gunter 2022."""

    @pytest.fixture
    def params(self):
        return get_gunter2022()

    def test_doi_reference(self, params):
        """Verify DOI is correctly specified."""
        assert params["DOI"] == "10.1149/1945-7111/ac4e11"

    def test_cathode_thickness(self, params):
        """Verify cathode thickness from paper: 87.3 +/- 2.7 um."""
        thickness_m = params["Positive electrode thickness [m]"]
        assert thickness_m == pytest.approx(87.3e-6, rel=0.05)

    def test_anode_thickness(self, params):
        """Verify anode thickness from paper: 115.3 +/- 3.5 um."""
        thickness_m = params["Negative electrode thickness [m]"]
        assert thickness_m == pytest.approx(115.3e-6, rel=0.05)

    def test_separator_thickness(self, params):
        """Verify separator thickness from paper: 17.6 +/- 2.1 um."""
        thickness_m = params["Separator thickness [m]"]
        assert thickness_m == pytest.approx(17.6e-6, rel=0.15)

    def test_cathode_loading(self, params):
        """Verify cathode loading from paper: 27.9 mg/cm2."""
        loading = params["Positive electrode loading [mg.cm-2]"]
        assert loading == pytest.approx(27.9, rel=0.01)

    def test_anode_loading(self, params):
        """Verify anode loading from paper: 18.1 mg/cm2."""
        loading = params["Negative electrode loading [mg.cm-2]"]
        assert loading == pytest.approx(18.1, rel=0.01)

    def test_active_material_volume_fraction(self, params):
        """Verify measured active material volume fraction: 0.816."""
        vol_frac = params["Positive electrode active material volume fraction"]
        assert vol_frac == pytest.approx(0.816, rel=0.01)

    def test_cell_capacity(self, params):
        """Verify cell capacity: 78 Ah."""
        capacity = params["Nominal cell capacity [A.h]"]
        assert capacity == 78.0

    def test_collector_thicknesses(self, params):
        """Verify current collector thicknesses."""
        assert params["Positive current collector thickness [m]"] == 14e-6
        assert params["Negative current collector thickness [m]"] == 12e-6

    def test_validation_targets_available(self):
        """Verify validation targets are defined."""
        assert VALIDATION_TARGETS["capacity_ah"] == 78.0
        assert VALIDATION_TARGETS["gravimetric_ed_whkg"] == 268.0

    def test_confidence_levels_documented(self):
        """Verify confidence levels are documented for key parameters."""
        assert "HIGH" in PARAMETER_CONFIDENCE["Positive electrode thickness [m]"]
        assert "HIGH" in PARAMETER_CONFIDENCE["Negative electrode thickness [m]"]


class TestStock2023Parameters:
    """Tests for CATL 161Ah LFP parameters from Stock 2023."""

    @pytest.fixture
    def params(self):
        return get_stock2023()

    def test_doi_reference(self, params):
        """Verify DOI is correctly specified."""
        assert params["DOI"] == "10.1016/j.electacta.2023.143341"

    def test_thick_lfp_cathode(self, params):
        """Verify thick LFP cathode: ~200 um."""
        thickness_m = params["Positive electrode thickness [m]"]
        assert thickness_m == pytest.approx(200e-6, rel=0.05)

    def test_anode_thickness(self, params):
        """Verify anode thickness: ~148 um."""
        thickness_m = params["Negative electrode thickness [m]"]
        assert thickness_m == pytest.approx(148e-6, rel=0.05)

    def test_thin_cu_collector(self, params):
        """Verify aggressive Cu lightweighting: 5 um (unusually thin)."""
        cu_thickness = params["Negative current collector thickness [m]"]
        assert cu_thickness == 5e-6

    def test_cell_capacity(self, params):
        """Verify cell capacity: 161.5 Ah."""
        capacity = params["Nominal cell capacity [A.h]"]
        assert capacity == 161.5

    def test_lfp_voltage(self, params):
        """Verify LFP nominal voltage: 3.2 V."""
        voltage = params["Nominal voltage [V]"]
        assert voltage == 3.2

    def test_electrode_length(self, params):
        """Verify electrode length for jelly roll: 22 m."""
        length = params["Electrode length [m]"]
        assert length == 22.0

    def test_void_volume(self, params):
        """Verify void volume from paper: 6.4%."""
        void = params["Void volume fraction"]
        assert void == pytest.approx(0.064, rel=0.01)

    def test_anode_tortuosity(self, params):
        """Verify measured tortuosity: 3.3."""
        tortuosity = params["Negative electrode tortuosity"]
        assert tortuosity == pytest.approx(3.3, rel=0.15)

    def test_design_notes_available(self):
        """Verify design notes document key features."""
        assert "200 um" in DESIGN_NOTES["thick_lfp_cathode"]
        assert "5 um" in DESIGN_NOTES["thin_cu_collector"]
        assert "butterfly" in DESIGN_NOTES["butterfly_design"].lower()


class TestHeenan2020Parameters:
    """Tests for LG MJ1 18650 parameters from Heenan 2020."""

    @pytest.fixture
    def params(self):
        return get_heenan2020()

    def test_doi_reference(self, params):
        """Verify DOI is correctly specified."""
        assert params["DOI"] == "10.1149/1945-7111/ab728d"

    def test_open_data_repository(self, params):
        """Verify open data repository is specified."""
        assert params["Open Data Repository"] == "rdr.ucl.ac.uk"

    def test_cathode_thickness(self, params):
        """Verify cathode thickness from X-ray tomography: ~66 um."""
        thickness_m = params["Positive electrode thickness [m]"]
        assert thickness_m == pytest.approx(66e-6, rel=0.05)

    def test_anode_thickness(self, params):
        """Verify anode thickness from X-ray tomography: ~87 um."""
        thickness_m = params["Negative electrode thickness [m]"]
        assert thickness_m == pytest.approx(87e-6, rel=0.05)

    def test_separator_thickness(self, params):
        """Verify separator thickness: 12 um."""
        thickness_m = params["Separator thickness [m]"]
        assert thickness_m == 12e-6

    def test_cell_capacity(self, params):
        """Verify cell capacity: 3.5 Ah."""
        capacity = params["Nominal cell capacity [A.h]"]
        assert capacity == 3.5

    def test_cylindrical_dimensions(self, params):
        """Verify 18650 dimensions."""
        assert params["Cell diameter [m]"] == pytest.approx(18.4e-3, rel=0.01)
        assert params["Cell length [m]"] == pytest.approx(65.2e-3, rel=0.01)

    def test_porosity_from_tomography(self, params):
        """Verify porosity values from X-ray tomography."""
        assert params["Positive electrode porosity"] == 0.30
        assert params["Negative electrode porosity"] == 0.26
        assert params["Separator porosity"] == 0.44

    def test_power_density(self, params):
        """Verify power density: 965 W/kg."""
        power = params["Power density [W.kg-1]"]
        assert power == 965.0

    def test_open_data_info_available(self):
        """Verify open data information is documented."""
        assert OPEN_DATA["repository"] == "rdr.ucl.ac.uk"
        assert OPEN_DATA["availability"] == "public"
        assert OPEN_DATA["data_type"] == "X-ray tomography"


class TestPyBaMMRepositoryIntegration:
    """Tests for custom parameter integration with PyBaMMRepository."""

    def test_custom_sets_in_all_parameter_sets(self):
        """Verify custom sets are in ALL_PARAMETER_SETS."""
        for set_name in REPO_CUSTOM_SETS:
            assert set_name in ALL_PARAMETER_SETS

    def test_custom_sets_have_chemistry_mapping(self):
        """Verify custom sets have chemistry mapping in repo."""
        for set_name in REPO_CUSTOM_SETS:
            assert set_name in CHEMISTRY_MAP

    def test_gunter2022_repository_loads(self):
        """Test loading Gunter2022 through repository."""
        repo = PyBaMMRepository("Gunter2022")
        assert repo._is_custom is True
        assert repo.parameter_set == "Gunter2022"

    def test_stock2023_repository_loads(self):
        """Test loading Stock2023 through repository."""
        repo = PyBaMMRepository("Stock2023")
        assert repo._is_custom is True
        assert repo.parameter_set == "Stock2023"

    def test_heenan2020_repository_loads(self):
        """Test loading Heenan2020 through repository."""
        repo = PyBaMMRepository("Heenan2020")
        assert repo._is_custom is True
        assert repo.parameter_set == "Heenan2020"

    def test_gunter2022_get_cathode(self):
        """Test getting cathode from Gunter2022."""
        repo = PyBaMMRepository("Gunter2022")
        cathode = repo.get_cathode()

        assert cathode.chemistry == "NCM652015"
        assert cathode.coating_thickness_0pct_um == pytest.approx(87.3, rel=0.01)
        assert cathode.areal_weight_mgcm2 == pytest.approx(27.9, rel=0.01)
        assert cathode.collector_thickness_um == 14.0

    def test_gunter2022_get_anode(self):
        """Test getting anode from Gunter2022."""
        repo = PyBaMMRepository("Gunter2022")
        anode = repo.get_anode()

        assert anode.chemistry == "Graphite"
        assert anode.coating_thickness_0pct_um == pytest.approx(115.3, rel=0.01)
        assert anode.areal_weight_mgcm2 == pytest.approx(18.1, rel=0.01)
        assert anode.collector_thickness_um == 12.0

    def test_gunter2022_get_separator(self):
        """Test getting separator from Gunter2022."""
        repo = PyBaMMRepository("Gunter2022")
        separator = repo.get_separator()

        assert separator.thickness_um == pytest.approx(17.6, rel=0.01)
        assert separator.porosity_pct == pytest.approx(42.0, rel=0.01)

    def test_stock2023_get_cathode(self):
        """Test getting cathode from Stock2023 (thick LFP)."""
        repo = PyBaMMRepository("Stock2023")
        cathode = repo.get_cathode()

        assert cathode.chemistry == "LFP"
        assert cathode.coating_thickness_0pct_um == pytest.approx(200.0, rel=0.01)
        assert cathode.areal_weight_mgcm2 == pytest.approx(22.6, rel=0.01)

    def test_stock2023_get_anode(self):
        """Test getting anode from Stock2023 (thin Cu collector)."""
        repo = PyBaMMRepository("Stock2023")
        anode = repo.get_anode()

        assert anode.chemistry == "Graphite"
        assert anode.collector_thickness_um == 5.0  # Unusually thin

    def test_heenan2020_get_cathode(self):
        """Test getting cathode from Heenan2020 (NMC811)."""
        repo = PyBaMMRepository("Heenan2020")
        cathode = repo.get_cathode()

        assert cathode.chemistry == "NMC811"
        assert cathode.coating_thickness_0pct_um == pytest.approx(66.0, rel=0.01)

    def test_heenan2020_get_anode(self):
        """Test getting anode from Heenan2020 (Graphite+Si)."""
        repo = PyBaMMRepository("Heenan2020")
        anode = repo.get_anode()

        assert anode.chemistry == "Graphite_Si"
        assert anode.coating_thickness_0pct_um == pytest.approx(87.0, rel=0.01)

    def test_get_parameter_summary_custom(self):
        """Test parameter summary for custom sets."""
        repo = PyBaMMRepository("Gunter2022")
        summary = repo.get_parameter_summary()

        assert summary["parameter_set"] == "Gunter2022"
        assert summary["cathode_chemistry"] == "NCM652015"
        assert summary["anode_chemistry"] == "Graphite"
        assert summary["cathode_thickness_um"] == pytest.approx(87.3, rel=0.01)


class TestParameterDerivations:
    """Tests for derived parameter calculations."""

    def test_gunter2022_coating_density(self):
        """Verify coating density derivation for Gunter2022."""
        params = get_gunter2022()

        # cathode: loading / thickness = 27.9 / (87.3e-4) = 3.20 g/cm3
        cathode_density = params["Positive electrode coating density [kg.m-3]"]
        assert cathode_density == pytest.approx(3200.0, rel=0.05)

        # anode: loading / thickness = 18.1 / (115.3e-4) = 1.57 g/cm3
        anode_density = params["Negative electrode coating density [kg.m-3]"]
        assert anode_density == pytest.approx(1570.0, rel=0.05)

    def test_stock2023_coating_density(self):
        """Verify coating density derivation for Stock2023."""
        params = get_stock2023()

        # cathode: loading / thickness = 22.6 / (200e-4) = 1.13 g/cm3
        cathode_density = params["Positive electrode coating density [kg.m-3]"]
        assert cathode_density == pytest.approx(1130.0, rel=0.10)

    def test_heenan2020_coating_density(self):
        """Verify coating density derivation for Heenan2020."""
        params = get_heenan2020()

        # cathode: loading / thickness = 20.0 / (66e-4) = 3.03 g/cm3
        cathode_density = params["Positive electrode coating density [kg.m-3]"]
        assert cathode_density == pytest.approx(3030.0, rel=0.05)
