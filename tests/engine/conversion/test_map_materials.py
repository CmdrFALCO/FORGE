"""Unit tests for material mapping functions."""

import pytest

from forge.engine.conversion.exceptions import MissingFieldError
from forge.engine.conversion.template_to_input import (
    _map_anode,
    _map_cathode,
    _map_electrolyte,
    _map_separator,
)
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    SeparatorMaterial,
)


class TestMapCathode:
    """Tests for _map_cathode function."""

    def test_map_cathode_basic(self):
        """Map basic cathode material."""
        electrochemistry = {
            "cathode": {
                "name": "NCA_Cathode",
                "loading_mg_cm2": 120.5,
                "rev_spec_capacity_mahg": 200.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 3.2,
                "coating_thickness_0pct_um": 37.6,
                "coating_thickness_100pct_um": 32.1,
            }
        }
        cathode = _map_cathode(electrochemistry)

        assert isinstance(cathode, CathodeMaterial)
        assert cathode.name == "NCA_Cathode"
        assert cathode.areal_weight_mgcm2 == 120.5  # Maps from loading_mg_cm2
        assert cathode.rev_spec_capacity_mahg == 200.0

    def test_map_cathode_chemistry_detection(self):
        """Detect chemistry from material name."""
        electrochemistry = {
            "cathode": {
                "name": "NCM811_Cathode",
                "loading_mg_cm2": 120.5,
                "rev_spec_capacity_mahg": 200.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 3.2,
                "coating_thickness_0pct_um": 37.6,
                "coating_thickness_100pct_um": 32.1,
            }
        }
        cathode = _map_cathode(electrochemistry)
        assert cathode.chemistry == "NCM"

    def test_map_cathode_nca_detected(self):
        """Detect NCA chemistry."""
        electrochemistry = {
            "cathode": {
                "name": "NCA_High_Energy",
                "loading_mg_cm2": 120.5,
                "rev_spec_capacity_mahg": 200.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 3.2,
                "coating_thickness_0pct_um": 37.6,
                "coating_thickness_100pct_um": 32.1,
            }
        }
        cathode = _map_cathode(electrochemistry)
        assert cathode.chemistry == "NCA"

    def test_map_cathode_lfp_detected(self):
        """Detect LFP chemistry."""
        electrochemistry = {
            "cathode": {
                "name": "LFP_Long_Life",
                "loading_mg_cm2": 100.0,
                "rev_spec_capacity_mahg": 160.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 2.8,
                "coating_thickness_0pct_um": 35.7,
                "coating_thickness_100pct_um": 30.2,
            }
        }
        cathode = _map_cathode(electrochemistry)
        assert cathode.chemistry == "LFP"

    def test_map_cathode_default_chemistry(self):
        """Use default chemistry when not detected."""
        electrochemistry = {
            "cathode": {
                "name": "Unknown_Material",
                "loading_mg_cm2": 120.5,
                "rev_spec_capacity_mahg": 200.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 3.2,
                "coating_thickness_0pct_um": 37.6,
                "coating_thickness_100pct_um": 32.1,
            }
        }
        cathode = _map_cathode(electrochemistry)
        assert cathode.chemistry == "NCM"

    def test_map_cathode_max_capacity_from_defaults(self):
        """Use default max capacity when not provided."""
        electrochemistry = {
            "cathode": {
                "name": "NCM811_Cathode",
                "loading_mg_cm2": 120.5,
                "rev_spec_capacity_mahg": 200.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 3.2,
                "coating_thickness_0pct_um": 37.6,
                "coating_thickness_100pct_um": 32.1,
            }
        }
        cathode = _map_cathode(electrochemistry)
        # Should use default from material_defaults for NCM
        assert cathode.max_spec_capacity_mahg == 190

    def test_map_cathode_missing_name(self):
        """Raise error when cathode name missing."""
        electrochemistry = {
            "cathode": {
                "loading_mg_cm2": 120.5,
                "rev_spec_capacity_mahg": 200.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 3.2,
                "coating_thickness_0pct_um": 37.6,
                "coating_thickness_100pct_um": 32.1,
            }
        }
        with pytest.raises(MissingFieldError):
            _map_cathode(electrochemistry)

    def test_map_cathode_id_generated(self):
        """Generate ID from cathode name."""
        electrochemistry = {
            "cathode": {
                "name": "NCA High Energy Cathode",
                "loading_mg_cm2": 120.5,
                "rev_spec_capacity_mahg": 200.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 3.2,
                "coating_thickness_0pct_um": 37.6,
                "coating_thickness_100pct_um": 32.1,
            }
        }
        cathode = _map_cathode(electrochemistry)
        assert cathode.id == "nca_high_energy_cathode"


class TestMapAnode:
    """Tests for _map_anode function."""

    def test_map_anode_basic(self):
        """Map basic anode material."""
        electrochemistry = {
            "anode": {
                "name": "Graphite_Anode",
                "loading_mg_cm2": 66.8,
                "rev_spec_capacity_mahg": 372.0,
                "collector_thickness_um": 10.0,
                "coating_density_gcm3": 1.8,
                "coating_thickness_0pct_um": 37.2,
                "coating_thickness_100pct_um": 32.3,
            }
        }
        anode = _map_anode(electrochemistry)

        assert isinstance(anode, AnodeMaterial)
        assert anode.name == "Graphite_Anode"
        assert anode.areal_weight_mgcm2 == 66.8

    def test_map_anode_graphite_detected(self):
        """Detect Graphite chemistry."""
        electrochemistry = {
            "anode": {
                "name": "Graphite_Natural",
                "loading_mg_cm2": 66.8,
                "rev_spec_capacity_mahg": 372.0,
                "collector_thickness_um": 10.0,
                "coating_density_gcm3": 1.8,
                "coating_thickness_0pct_um": 37.2,
                "coating_thickness_100pct_um": 32.3,
            }
        }
        anode = _map_anode(electrochemistry)
        assert anode.chemistry == "Graphite"

    def test_map_anode_silicon_detected(self):
        """Detect Silicon chemistry."""
        electrochemistry = {
            "anode": {
                "name": "Si-C_Composite",
                "loading_mg_cm2": 70.0,
                "rev_spec_capacity_mahg": 700.0,
                "collector_thickness_um": 10.0,
                "coating_density_gcm3": 1.8,
                "coating_thickness_0pct_um": 37.2,
                "coating_thickness_100pct_um": 32.3,
            }
        }
        anode = _map_anode(electrochemistry)
        assert anode.chemistry == "Silicon"

    def test_map_anode_default_chemistry(self):
        """Use default Graphite chemistry when not detected."""
        electrochemistry = {
            "anode": {
                "name": "Unknown_Anode",
                "loading_mg_cm2": 66.8,
                "rev_spec_capacity_mahg": 372.0,
                "collector_thickness_um": 10.0,
                "coating_density_gcm3": 1.8,
                "coating_thickness_0pct_um": 37.2,
                "coating_thickness_100pct_um": 32.3,
            }
        }
        anode = _map_anode(electrochemistry)
        assert anode.chemistry == "Graphite"


class TestMapSeparator:
    """Tests for _map_separator function."""

    def test_map_separator_basic(self):
        """Map basic separator material."""
        electrochemistry = {
            "separator": {
                "name": "PP_Separator",
                "thickness_um": 25.0,
                "porosity_pct": 50.0,
                "areal_weight_mgcm2": 1.14,
            }
        }
        separator = _map_separator(electrochemistry)

        assert isinstance(separator, SeparatorMaterial)
        assert separator.name == "PP_Separator"
        assert separator.thickness_um == 25.0
        assert separator.porosity_pct == 50.0

    def test_map_separator_density_from_type(self):
        """Use default density based on separator type."""
        electrochemistry = {
            "separator": {
                "name": "PE-PP",
                "thickness_um": 25.0,
                "porosity_pct": 50.0,
                "areal_weight_mgcm2": 1.14,
            }
        }
        separator = _map_separator(electrochemistry)
        # Should use default density for PE-PP blend
        assert separator.density_gcm3 == 0.91

    def test_map_separator_ceramic(self):
        """Map ceramic separator with its density."""
        electrochemistry = {
            "separator": {
                "name": "Ceramic",
                "thickness_um": 10.0,
                "porosity_pct": 40.0,
                "areal_weight_mgcm2": 1.6,
            }
        }
        separator = _map_separator(electrochemistry)
        assert separator.density_gcm3 == 2.4

    def test_map_separator_id_generated(self):
        """Generate ID from separator name."""
        electrochemistry = {
            "separator": {
                "name": "PE-PP Multi Layer",
                "thickness_um": 25.0,
                "porosity_pct": 50.0,
                "areal_weight_mgcm2": 1.14,
            }
        }
        separator = _map_separator(electrochemistry)
        assert separator.id == "pe-pp_multi_layer"


class TestMapElectrolyte:
    """Tests for _map_electrolyte function."""

    def test_map_electrolyte_basic(self):
        """Map basic electrolyte."""
        electrochemistry = {
            "electrolyte": {
                "name": "EC:DMC_1M_LiPF6",
                "density_gcm3": 1.21,
            }
        }
        electrolyte = _map_electrolyte(electrochemistry)

        assert isinstance(electrolyte, ElectrolyteModel)
        assert electrolyte.name == "EC:DMC_1M_LiPF6"
        assert electrolyte.density_gcm3 == 1.21

    def test_map_electrolyte_with_conductivity(self):
        """Map electrolyte with conductivity specified."""
        electrochemistry = {
            "electrolyte": {
                "name": "EC:DMC_1M_LiPF6",
                "density_gcm3": 1.21,
                "conductivity_sm": 10.2,
            }
        }
        electrolyte = _map_electrolyte(electrochemistry)
        assert electrolyte.conductivity_sm == 10.2

    def test_map_electrolyte_without_conductivity(self):
        """Handle missing conductivity field."""
        electrochemistry = {
            "electrolyte": {
                "name": "EC:DMC_1M_LiPF6",
                "density_gcm3": 1.21,
            }
        }
        electrolyte = _map_electrolyte(electrochemistry)
        assert electrolyte.conductivity_sm is None

    def test_map_electrolyte_id_generated(self):
        """Generate ID from electrolyte name."""
        electrochemistry = {
            "electrolyte": {
                "name": "EC DMC 1M LiPF6 Custom",
                "density_gcm3": 1.21,
            }
        }
        electrolyte = _map_electrolyte(electrochemistry)
        assert electrolyte.id == "ec_dmc_1m_lipf6_custom"

    def test_map_electrolyte_missing_name(self):
        """Raise error when electrolyte name missing."""
        electrochemistry = {
            "electrolyte": {
                "density_gcm3": 1.21,
            }
        }
        with pytest.raises(MissingFieldError):
            _map_electrolyte(electrochemistry)
