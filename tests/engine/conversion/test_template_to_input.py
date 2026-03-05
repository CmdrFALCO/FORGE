"""Integration tests for from_template_format function."""

import pytest

from forge.engine.conversion import from_template_format
from forge.engine.conversion.exceptions import MissingFieldError
from forge.engine.models.prismatic import PrismaticCellInput


@pytest.fixture
def valid_template():
    """Provide a valid YAML template dict for testing."""
    return {
        "cell_name": "Test_Prismatic_V1",
        "envelope": {
            "cell_height_mm": 88.8,
            "cell_width_mm": 264.6,
            "cell_thickness_mm": 29.6,
            "wall_top_mm": 2.0,
            "wall_bottom_mm": 1.0,
            "wall_front_back_mm": 0.5,
            "wall_sides_mm": 0.7,
        },
        "stack_config": {
            "stacks": 2,
            "pairs": 22,
            "end_electrodes": "BothNegative",
            "sheet_geometry": {
                "cathode_height_mm": 200.0,
                "cathode_width_mm": 100.0,
                "anode_offset_top_mm": 2.0,
                "anode_offset_bottom_mm": 2.0,
                "anode_offset_left_mm": 2.0,
                "anode_offset_right_mm": 2.0,
            },
        },
        "electrochemistry": {
            "cathode": {
                "name": "NCM811_Cathode",
                "loading_mg_cm2": 120.5,
                "rev_spec_capacity_mahg": 200.0,
                "collector_thickness_um": 15.0,
                "coating_density_gcm3": 3.2,
                "coating_thickness_0pct_um": 37.6,
                "coating_thickness_100pct_um": 32.1,
            },
            "anode": {
                "name": "Graphite_Anode",
                "loading_mg_cm2": 66.8,
                "rev_spec_capacity_mahg": 372.0,
                "collector_thickness_um": 10.0,
                "coating_density_gcm3": 1.8,
                "coating_thickness_0pct_um": 37.2,
                "coating_thickness_100pct_um": 32.3,
            },
            "separator": {
                "name": "PP_Separator",
                "thickness_um": 25.0,
                "porosity_pct": 50.0,
                "areal_weight_mgcm2": 1.14,
            },
            "electrolyte": {
                "name": "EC_DMC_1M_LiPF6",
                "density_gcm3": 1.21,
            },
        },
    }


class TestFromTemplateFormat:
    """Tests for from_template_format function."""

    def test_convert_valid_template(self, valid_template):
        """Convert valid template to PrismaticCellInput."""
        cell_input = from_template_format(valid_template)

        assert isinstance(cell_input, PrismaticCellInput)
        assert cell_input.cell_name == "Test_Prismatic_V1"
        assert cell_input.number_of_stacks == 2
        assert cell_input.electrode_pairs_per_stack == 22
        assert cell_input.end_electrodes == "BothNegative"

    def test_convert_sets_geometry(self, valid_template):
        """Verify geometry is correctly set."""
        cell_input = from_template_format(valid_template)

        assert cell_input.case_geometry is not None
        assert cell_input.case_geometry.cell_height_mm == 88.8
        assert cell_input.case_geometry.cell_width_mm == 264.6
        assert cell_input.case_geometry.cell_thickness_mm == 29.6

    def test_convert_sets_sheet_geometry(self, valid_template):
        """Verify sheet geometry is correctly set."""
        cell_input = from_template_format(valid_template)

        assert cell_input.sheet_geometry is not None
        assert cell_input.sheet_geometry.cathode_height_mm == 200.0
        assert cell_input.sheet_geometry.cathode_width_mm == 100.0

    def test_convert_sets_materials(self, valid_template):
        """Verify all materials are correctly set."""
        cell_input = from_template_format(valid_template)

        assert cell_input.cathode is not None
        assert cell_input.cathode.name == "NCM811_Cathode"
        assert cell_input.anode is not None
        assert cell_input.anode.name == "Graphite_Anode"
        assert cell_input.separator is not None
        assert cell_input.separator.name == "PP_Separator"
        assert cell_input.electrolyte is not None
        assert cell_input.electrolyte.name == "EC_DMC_1M_LiPF6"

    def test_convert_uses_defaults(self, valid_template):
        """Verify default values are used for optional parameters."""
        cell_input = from_template_format(valid_template)

        # Check some defaults
        assert cell_input.header_mass_g == 88.76
        assert cell_input.electrolyte_excess_factor == 1.0
        assert cell_input.cathode_porosity_pct == 25.36
        assert cell_input.anode_porosity_pct == 38.01

    def test_convert_with_custom_optional_params(self, valid_template):
        """Convert template with custom optional parameters."""
        valid_template["header_mass_g"] = 95.0
        valid_template["electrolyte_excess_factor"] = 1.2
        valid_template["nominal_voltage_v"] = 3.7

        cell_input = from_template_format(valid_template)

        assert cell_input.header_mass_g == 95.0
        assert cell_input.electrolyte_excess_factor == 1.2
        assert cell_input.nominal_voltage_v == 3.7

    def test_convert_missing_envelope(self, valid_template):
        """Raise error when envelope section missing."""
        del valid_template["envelope"]
        with pytest.raises(MissingFieldError):
            from_template_format(valid_template)

    def test_convert_missing_stack_config(self, valid_template):
        """Raise error when stack_config section missing."""
        del valid_template["stack_config"]
        with pytest.raises(MissingFieldError):
            from_template_format(valid_template)

    def test_convert_missing_electrochemistry(self, valid_template):
        """Raise error when electrochemistry section missing."""
        del valid_template["electrochemistry"]
        with pytest.raises(MissingFieldError):
            from_template_format(valid_template)

    def test_convert_missing_cathode(self, valid_template):
        """Raise error when cathode missing."""
        del valid_template["electrochemistry"]["cathode"]
        with pytest.raises(MissingFieldError):
            from_template_format(valid_template)

    def test_convert_missing_anode(self, valid_template):
        """Raise error when anode missing."""
        del valid_template["electrochemistry"]["anode"]
        with pytest.raises(MissingFieldError):
            from_template_format(valid_template)

    def test_convert_missing_separator(self, valid_template):
        """Raise error when separator missing."""
        del valid_template["electrochemistry"]["separator"]
        with pytest.raises(MissingFieldError):
            from_template_format(valid_template)

    def test_convert_missing_electrolyte(self, valid_template):
        """Raise error when electrolyte missing."""
        del valid_template["electrochemistry"]["electrolyte"]
        with pytest.raises(MissingFieldError):
            from_template_format(valid_template)

    def test_convert_with_template_format_dicts(self, valid_template):
        """Convert template with metadata dict format."""
        # Convert some fields to template format with metadata
        valid_template["envelope"]["cell_height_mm"] = {
            "_default": 88.8,
            "_type": "number",
            "min": 80,
            "max": 100,
        }
        valid_template["stack_config"]["stacks"] = {"_default": 2}

        cell_input = from_template_format(valid_template)

        assert cell_input.case_geometry.cell_height_mm == 88.8
        assert cell_input.number_of_stacks == 2

    def test_convert_default_cell_name(self, valid_template):
        """Use default cell name when not provided."""
        del valid_template["cell_name"]
        cell_input = from_template_format(valid_template)
        assert cell_input.cell_name == "Prismatic Cell"

    def test_convert_default_stack_values(self, valid_template):
        """Use default stack values when not provided."""
        del valid_template["stack_config"]["stacks"]
        del valid_template["stack_config"]["pairs"]
        del valid_template["stack_config"]["end_electrodes"]

        cell_input = from_template_format(valid_template)

        assert cell_input.number_of_stacks == 2
        assert cell_input.electrode_pairs_per_stack == 22
        assert cell_input.end_electrodes == "BothNegative"

    def test_convert_field_name_mapping_cathode(self, valid_template):
        """Verify loading_mg_cm2 maps to areal_weight_mgcm2."""
        cell_input = from_template_format(valid_template)
        assert cell_input.cathode.areal_weight_mgcm2 == 120.5

    def test_convert_field_name_mapping_anode(self, valid_template):
        """Verify loading_mg_cm2 maps to areal_weight_mgcm2 for anode."""
        cell_input = from_template_format(valid_template)
        assert cell_input.anode.areal_weight_mgcm2 == 66.8
