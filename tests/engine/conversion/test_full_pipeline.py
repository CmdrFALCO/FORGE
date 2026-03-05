"""End-to-end tests for validation â†’ conversion â†’ calculation pipeline."""

import os
import tempfile

import pytest
import yaml

from forge.engine.conversion import from_template_format, from_yaml_file
from forge.engine.models.prismatic import PrismaticCellInput


@pytest.fixture
def valid_yaml_content():
    """Provide valid YAML content for a prismatic cell."""
    return """
cell_name: V1_Pouch_Reference_Test

envelope:
  cell_height_mm: 88.8
  cell_width_mm: 264.6
  cell_thickness_mm: 29.6
  wall_top_mm: 2.0
  wall_bottom_mm: 1.0
  wall_front_back_mm: 0.5
  wall_sides_mm: 0.7
  insulation_coating_um: 85.0

stack_config:
  stacks: 2
  pairs: 22
  end_electrodes: BothNegative
  sheet_geometry:
    cathode_height_mm: 200.0
    cathode_width_mm: 100.0
    anode_offset_top_mm: 2.0
    anode_offset_bottom_mm: 2.0
    anode_offset_left_mm: 2.0
    anode_offset_right_mm: 2.0
    separator_offset_top_mm: 2.0
    separator_offset_bottom_mm: 2.0
    separator_offset_left_mm: 2.0
    separator_offset_right_mm: 2.0

electrochemistry:
  cathode:
    name: NCM811
    loading_mg_cm2: 120.5
    rev_spec_capacity_mahg: 200.0
    max_spec_capacity_mahg: 200.0
    collector_thickness_um: 15.0
    coating_density_gcm3: 3.2
    coating_thickness_0pct_um: 37.6
    coating_thickness_100pct_um: 32.1

  anode:
    name: Graphite
    loading_mg_cm2: 66.8
    rev_spec_capacity_mahg: 372.0
    max_spec_capacity_mahg: 372.0
    collector_thickness_um: 10.0
    coating_density_gcm3: 1.8
    coating_thickness_0pct_um: 37.2
    coating_thickness_100pct_um: 32.3

  separator:
    name: PP
    thickness_um: 25.0
    porosity_pct: 50.0
    areal_weight_mgcm2: 1.14

  electrolyte:
    name: EC_DMC_1M_LiPF6
    density_gcm3: 1.21

header_mass_g: 88.76
electrolyte_excess_factor: 1.0
cathode_porosity_pct: 25.36
anode_porosity_pct: 38.01
nominal_voltage_v: 3.644
"""


class TestConversionPipeline:
    """Tests for converting validated YAML to calculator input."""

    def test_convert_valid_yaml_file(self, valid_yaml_content):
        """Convert valid YAML file to PrismaticCellInput."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(valid_yaml_content)
            f.flush()
            temp_path = f.name

        try:
            cell_input = from_yaml_file(temp_path)

            assert isinstance(cell_input, PrismaticCellInput)
            assert cell_input.cell_name == "V1_Pouch_Reference_Test"
            assert cell_input.case_geometry is not None
            assert cell_input.sheet_geometry is not None
            assert cell_input.cathode is not None
        finally:
            os.unlink(temp_path)

    def test_convert_yaml_dict(self, valid_yaml_content):
        """Convert YAML dict to PrismaticCellInput."""
        template_dict = yaml.safe_load(valid_yaml_content)
        cell_input = from_template_format(template_dict)

        assert isinstance(cell_input, PrismaticCellInput)
        assert cell_input.cell_name == "V1_Pouch_Reference_Test"
        assert cell_input.number_of_stacks == 2
        assert cell_input.electrode_pairs_per_stack == 22

    def test_yaml_file_not_found(self):
        """Handle missing YAML file gracefully."""
        with pytest.raises(FileNotFoundError):
            from_yaml_file("/nonexistent/path/file.yaml")

    def test_invalid_yaml_syntax(self):
        """Handle invalid YAML syntax gracefully."""
        from forge.engine.conversion.exceptions import MappingError

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(MappingError):
                from_yaml_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_conversion_maintains_precision(self, valid_yaml_content):
        """Verify that conversion maintains numerical precision."""
        template_dict = yaml.safe_load(valid_yaml_content)
        cell_input = from_template_format(template_dict)

        # Check precise floating-point values
        assert cell_input.case_geometry.cell_height_mm == 88.8
        assert cell_input.case_geometry.cell_width_mm == 264.6
        assert cell_input.case_geometry.cell_thickness_mm == 29.6
        assert cell_input.cathode_porosity_pct == 25.36
        assert cell_input.anode_porosity_pct == 38.01
        assert cell_input.nominal_voltage_v == 3.644

    def test_conversion_with_custom_values(self, valid_yaml_content):
        """Convert YAML with custom non-default values."""
        template_dict = yaml.safe_load(valid_yaml_content)

        # Customize some optional parameters
        template_dict["header_mass_g"] = 95.5
        template_dict["electrolyte_excess_factor"] = 1.15
        template_dict["cathode_porosity_pct"] = 28.0

        cell_input = from_template_format(template_dict)

        assert cell_input.header_mass_g == 95.5
        assert cell_input.electrolyte_excess_factor == 1.15
        assert cell_input.cathode_porosity_pct == 28.0

    def test_convert_with_all_defaults(self, valid_yaml_content):
        """Verify all default values are applied correctly."""
        template_dict = yaml.safe_load(valid_yaml_content)

        # Remove optional parameters to test defaults
        for key in [
            "header_mass_g",
            "electrolyte_excess_factor",
            "cathode_porosity_pct",
            "anode_porosity_pct",
            "nominal_voltage_v",
        ]:
            if key in template_dict:
                del template_dict[key]

        cell_input = from_template_format(template_dict)

        # Verify defaults
        assert cell_input.header_mass_g == 88.76
        assert cell_input.electrolyte_excess_factor == 1.0
        assert cell_input.cathode_porosity_pct == 25.36
        assert cell_input.anode_porosity_pct == 38.01
        assert cell_input.nominal_voltage_v == 3.644

    def test_material_chemistry_detection(self, valid_yaml_content):
        """Verify chemistry is auto-detected from material names."""
        template_dict = yaml.safe_load(valid_yaml_content)
        cell_input = from_template_format(template_dict)

        # Check chemistry detection
        assert cell_input.cathode.chemistry == "NCM"
        assert cell_input.anode.chemistry == "Graphite"

    def test_material_id_generation(self, valid_yaml_content):
        """Verify material IDs are generated from names."""
        template_dict = yaml.safe_load(valid_yaml_content)
        cell_input = from_template_format(template_dict)

        # Check ID generation (should be lowercase with underscores)
        assert cell_input.cathode.id == "ncm811"
        assert cell_input.anode.id == "graphite"
        assert cell_input.separator.id == "pp"

    def test_conversion_idempotency(self, valid_yaml_content):
        """Verify converting same template twice produces identical result."""
        template_dict = yaml.safe_load(valid_yaml_content)

        cell_input_1 = from_template_format(template_dict)
        cell_input_2 = from_template_format(template_dict)

        # Compare key attributes
        assert cell_input_1.cell_name == cell_input_2.cell_name
        assert (
            cell_input_1.case_geometry.cell_height_mm == cell_input_2.case_geometry.cell_height_mm
        )
        assert cell_input_1.cathode.areal_weight_mgcm2 == cell_input_2.cathode.areal_weight_mgcm2
        assert cell_input_1.number_of_stacks == cell_input_2.number_of_stacks


class TestConversionWithCalculation:
    """Tests for using converted input with calculator."""

    def test_converted_input_ready_for_calculation(self, valid_yaml_content):
        """Verify converted input can be used for calculation."""
        template_dict = yaml.safe_load(valid_yaml_content)
        cell_input = from_template_format(template_dict)

        # Verify all required fields for calculation are present
        assert cell_input.case_geometry is not None
        assert cell_input.sheet_geometry is not None
        assert cell_input.cathode is not None
        assert cell_input.anode is not None
        assert cell_input.separator is not None
        assert cell_input.electrolyte is not None

    def test_converted_input_dataclass_validity(self, valid_yaml_content):
        """Verify converted input is valid dataclass instance."""
        template_dict = yaml.safe_load(valid_yaml_content)
        cell_input = from_template_format(template_dict)

        # Verify it's a proper dataclass with expected attributes
        assert hasattr(cell_input, "cell_name")
        assert hasattr(cell_input, "case_geometry")
        assert hasattr(cell_input, "sheet_geometry")
        assert hasattr(cell_input, "cathode")
        assert hasattr(cell_input, "anode")
        assert hasattr(cell_input, "separator")
        assert hasattr(cell_input, "electrolyte")

        # Verify computed properties are accessible
        assert hasattr(cell_input, "total_electrode_pairs")
        assert cell_input.total_electrode_pairs == 44  # 22 pairs * 2 stacks

    def test_converted_geometry_properties(self, valid_yaml_content):
        """Verify geometry computed properties work correctly."""
        template_dict = yaml.safe_load(valid_yaml_content)
        cell_input = from_template_format(template_dict)

        # Test computed properties
        geom = cell_input.case_geometry
        assert geom.internal_height_mm == 88.8 - 2.0 - 1.0
        assert geom.internal_width_mm == 264.6 - 2 * 0.7
        assert geom.internal_thickness_mm == 29.6 - 2 * 0.5

    def test_converted_sheet_geometry_properties(self, valid_yaml_content):
        """Verify sheet geometry computed properties work correctly."""
        template_dict = yaml.safe_load(valid_yaml_content)
        cell_input = from_template_format(template_dict)

        # Test computed properties
        sheet = cell_input.sheet_geometry
        assert sheet.cathode_area_cm2 == 200.0 * 100.0 / 100.0
        assert sheet.anode_height_mm == 200.0 + 2.0 + 2.0
        assert sheet.anode_width_mm == 100.0 + 2.0 + 2.0
