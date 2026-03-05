"""Convert YAML template format to CellCAD input dataclasses.

This module provides functions to transform validated YAML templates into
CellCAD input objects, handling both template format (with metadata dicts)
and instance format (with direct values).

Supports all cell types:
- Prismatic: from_template_format() -> PrismaticCellInput
- Pouch: from_pouch_template_format() -> PouchCellInput
- Cylindrical: from_cylindrical_template_format() -> CylindricalCellInput
"""

from typing import Any

import yaml


# Sentinel value to detect when no default was provided
_NO_DEFAULT = object()

from forge.engine.models.pouch import PouchCellInput
from forge.engine.models.cylindrical import (
    CanMaterial,
    CylindricalCellInput,
    CylindricalGeometry,
    SimplifiedHeader,
    TabType,
    WindingConfig,
)
from forge.engine.models.geometry import PouchPackaging, SheetGeometry
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
    TabConfig,
)
from forge.engine.models.prismatic import (
    PrismaticCellInput,
    PrismaticGeometry,
    PrismaticSheetGeometry,
)
from forge.engine.models.stack import EndElectrodesMode, StackConfiguration

from . import material_defaults
from .exceptions import MappingError, MissingFieldError


def _extract_value(value: Any) -> Any:
    """
    Extract actual value from dual format (template dict or direct value).

    Handles both:
    - Template format: {"_default": 88.8, "_type": "number", "min": 50, "max": 200}
    - Instance format: 88.8

    Args:
        value: Either a template metadata dict or a direct value

    Returns:
        The actual value to use
    """
    if isinstance(value, dict) and "_default" in value:
        # Template format - extract the default value
        return value["_default"]
    else:
        # Instance format - use directly
        return value


def _get_nested(data: dict[str, Any], path: str, default: Any = _NO_DEFAULT) -> Any:
    """
    Navigate nested dictionary path and extract value from dual format.

    Args:
        data: Dictionary to navigate
        path: Dot-separated path (e.g., "envelope.cell_height_mm")
        default: Default value if path not found. If not provided, raises KeyError.

    Returns:
        Extracted value or default if path not found

    Raises:
        KeyError: If path not found and no default provided
    """
    keys = path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            if default is not _NO_DEFAULT:
                return default
            else:
                raise KeyError(f"Path not found: {path}")

    # Extract value from template format if needed
    return _extract_value(current)


def _require_nested(data: dict[str, Any], path: str, field: str = None) -> Any:
    """
    Get required nested value or raise MissingFieldError.

    Args:
        data: Dictionary to navigate
        path: Dot-separated path (e.g., "envelope.cell_height_mm")
        field: Optional field name for error messages (defaults to path)

    Returns:
        Extracted value

    Raises:
        MissingFieldError: If path not found
    """
    try:
        return _get_nested(data, path)
    except KeyError:
        raise MissingFieldError(path, field or path)


def _map_geometry(envelope: dict[str, Any]) -> PrismaticGeometry:
    """
    Map envelope dict to PrismaticGeometry.

    Args:
        envelope: Envelope section from YAML

    Returns:
        PrismaticGeometry instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        return PrismaticGeometry(
            cell_height_mm=_require_nested(envelope, "cell_height_mm"),
            cell_width_mm=_require_nested(envelope, "cell_width_mm"),
            cell_thickness_mm=_require_nested(envelope, "cell_thickness_mm"),
            wall_top_mm=_require_nested(envelope, "wall_top_mm"),
            wall_bottom_mm=_require_nested(envelope, "wall_bottom_mm"),
            wall_front_back_mm=_require_nested(envelope, "wall_front_back_mm"),
            wall_sides_mm=_require_nested(envelope, "wall_sides_mm"),
            insulation_coating_um=_get_nested(envelope, "insulation_coating_um", 85.0),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map envelope geometry: {e}", "envelope")


def _map_sheet_geometry(stack_config: dict[str, Any]) -> PrismaticSheetGeometry:
    """
    Map stack_config.sheet_geometry dict to PrismaticSheetGeometry.

    Args:
        stack_config: Stack configuration section from YAML

    Returns:
        PrismaticSheetGeometry instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        sheet_geo = stack_config.get("sheet_geometry", {})

        return PrismaticSheetGeometry(
            cathode_height_mm=_require_nested(sheet_geo, "cathode_height_mm"),
            cathode_width_mm=_require_nested(sheet_geo, "cathode_width_mm"),
            anode_offset_top_mm=_get_nested(sheet_geo, "anode_offset_top_mm", 2.0),
            anode_offset_bottom_mm=_get_nested(sheet_geo, "anode_offset_bottom_mm", 2.0),
            anode_offset_left_mm=_get_nested(sheet_geo, "anode_offset_left_mm", 2.0),
            anode_offset_right_mm=_get_nested(sheet_geo, "anode_offset_right_mm", 2.0),
            separator_offset_top_mm=_get_nested(sheet_geo, "separator_offset_top_mm", 2.0),
            separator_offset_bottom_mm=_get_nested(sheet_geo, "separator_offset_bottom_mm", 2.0),
            separator_offset_left_mm=_get_nested(sheet_geo, "separator_offset_left_mm", 2.0),
            separator_offset_right_mm=_get_nested(sheet_geo, "separator_offset_right_mm", 2.0),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map sheet geometry: {e}", "stack_config.sheet_geometry")


def _map_cathode(electrochemistry: dict[str, Any]) -> CathodeMaterial:
    """
    Map electrochemistry.cathode dict to CathodeMaterial.

    Args:
        electrochemistry: Electrochemistry section from YAML

    Returns:
        CathodeMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        cathode = electrochemistry.get("cathode", {})
        name = _require_nested(cathode, "name")
        chemistry = material_defaults.detect_chemistry(name)

        return CathodeMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            chemistry=chemistry or "NCM",  # Default to NCM if not detected
            rev_spec_capacity_mahg=_require_nested(cathode, "rev_spec_capacity_mahg"),
            max_spec_capacity_mahg=_get_nested(
                cathode,
                "max_spec_capacity_mahg",
                material_defaults.get_max_specific_capacity(chemistry),
            ),
            areal_weight_mgcm2=_require_nested(cathode, "loading_mg_cm2"),  # Field name mapping
            collector_thickness_um=_require_nested(cathode, "collector_thickness_um"),
            coating_density_gcm3=_require_nested(cathode, "coating_density_gcm3"),
            coating_thickness_0pct_um=_require_nested(cathode, "coating_thickness_0pct_um"),
            coating_thickness_100pct_um=_require_nested(cathode, "coating_thickness_100pct_um"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map cathode material: {e}", "electrochemistry.cathode")


def _map_anode(electrochemistry: dict[str, Any]) -> AnodeMaterial:
    """
    Map electrochemistry.anode dict to AnodeMaterial.

    Args:
        electrochemistry: Electrochemistry section from YAML

    Returns:
        AnodeMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        anode = electrochemistry.get("anode", {})
        name = _require_nested(anode, "name")
        chemistry = material_defaults.detect_chemistry(name)

        return AnodeMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            chemistry=chemistry or "Graphite",  # Default to Graphite if not detected
            rev_spec_capacity_mahg=_require_nested(anode, "rev_spec_capacity_mahg"),
            max_spec_capacity_mahg=_get_nested(
                anode,
                "max_spec_capacity_mahg",
                material_defaults.get_max_specific_capacity(chemistry),
            ),
            areal_weight_mgcm2=_require_nested(anode, "loading_mg_cm2"),  # Field name mapping
            collector_thickness_um=_require_nested(anode, "collector_thickness_um"),
            coating_density_gcm3=_require_nested(anode, "coating_density_gcm3"),
            coating_thickness_0pct_um=_require_nested(anode, "coating_thickness_0pct_um"),
            coating_thickness_100pct_um=_require_nested(anode, "coating_thickness_100pct_um"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map anode material: {e}", "electrochemistry.anode")


def _map_separator(electrochemistry: dict[str, Any]) -> SeparatorMaterial:
    """
    Map electrochemistry.separator dict to SeparatorMaterial.

    Args:
        electrochemistry: Electrochemistry section from YAML

    Returns:
        SeparatorMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        separator = electrochemistry.get("separator", {})
        name = _require_nested(separator, "name")

        return SeparatorMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            thickness_um=_require_nested(separator, "thickness_um"),
            porosity_pct=_require_nested(separator, "porosity_pct"),
            density_gcm3=_get_nested(
                separator, "density_gcm3", material_defaults.get_separator_density(name)
            ),
            areal_weight_mgcm2=_require_nested(separator, "areal_weight_mgcm2"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map separator material: {e}", "electrochemistry.separator")


def _map_electrolyte(electrochemistry: dict[str, Any]) -> ElectrolyteModel:
    """
    Map electrochemistry.electrolyte dict to ElectrolyteModel.

    Args:
        electrochemistry: Electrochemistry section from YAML

    Returns:
        ElectrolyteModel instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        electrolyte = electrochemistry.get("electrolyte", {})
        name = _require_nested(electrolyte, "name")

        # conductivity_sm is optional, so provide None as default
        conductivity = None
        if "conductivity_sm" in electrolyte:
            conductivity = _extract_value(electrolyte["conductivity_sm"])

        return ElectrolyteModel(
            id=name.lower().replace(" ", "_"),
            name=name,
            density_gcm3=_require_nested(electrolyte, "density_gcm3"),
            conductivity_sm=conductivity,
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map electrolyte: {e}", "electrochemistry.electrolyte")


def from_template_format(template_dict: dict[str, Any]) -> PrismaticCellInput:
    """
    Convert validated YAML template dict to PrismaticCellInput.

    Args:
        template_dict: Validated YAML template dictionary with structure:
            - cell_name
            - envelope (geometry)
            - stack_config (stacks, pairs, end_electrodes, sheet_geometry)
            - electrochemistry (cathode, anode, separator, electrolyte)
            - optional parameters

    Returns:
        PrismaticCellInput instance ready for calculation

    Raises:
        MissingFieldError: If required fields missing
        MappingError: If mapping fails
    """
    try:
        # Extract main sections
        envelope = template_dict.get("envelope", {})
        stack_config = template_dict.get("stack_config", {})
        electrochemistry = template_dict.get("electrochemistry", {})

        # Map required geometry and materials
        case_geometry = _map_geometry(envelope)
        sheet_geometry = _map_sheet_geometry(stack_config)
        cathode = _map_cathode(electrochemistry)
        anode = _map_anode(electrochemistry)
        separator = _map_separator(electrochemistry)
        electrolyte = _map_electrolyte(electrochemistry)

        # Create the main input object
        return PrismaticCellInput(
            cell_name=_get_nested(template_dict, "cell_name", "Prismatic Cell"),
            case_geometry=case_geometry,
            sheet_geometry=sheet_geometry,
            number_of_stacks=_get_nested(stack_config, "stacks", 2),
            electrode_pairs_per_stack=_get_nested(stack_config, "pairs", 22),
            end_electrodes=_get_nested(stack_config, "end_electrodes", "BothNegative"),
            cathode=cathode,
            anode=anode,
            separator=separator,
            electrolyte=electrolyte,
            # Optional parameters with defaults
            case_material_density_gcm3=_get_nested(
                template_dict, "case_material_density_gcm3", 2.70
            ),
            header_mass_g=_get_nested(template_dict, "header_mass_g", 88.76),
            insulation_shell_thickness_um=_get_nested(
                template_dict, "insulation_shell_thickness_um", 120.0
            ),
            insulation_shell_count=_get_nested(template_dict, "insulation_shell_count", 2),
            insulation_shell_density_gcm3=_get_nested(
                template_dict, "insulation_shell_density_gcm3", 0.91
            ),
            electrolyte_excess_factor=_get_nested(template_dict, "electrolyte_excess_factor", 1.0),
            electrolyte_volume_override_ml=_get_nested(
                template_dict, "electrolyte_volume_override_ml", None
            ),
            cathode_porosity_pct=_get_nested(template_dict, "cathode_porosity_pct", 25.36),
            anode_porosity_pct=_get_nested(template_dict, "anode_porosity_pct", 38.01),
            nominal_voltage_v=_get_nested(template_dict, "nominal_voltage_v", 3.644),
            capacity_ah=_get_nested(template_dict, "capacity_ah", None),
            fixing_tape_count=_get_nested(template_dict, "fixing_tape_count", 4),
            fixing_tape_thickness_um=_get_nested(template_dict, "fixing_tape_thickness_um", 30.0),
            fixing_tape_width_mm=_get_nested(template_dict, "fixing_tape_width_mm", 30.0),
            fixing_tape_length_mm=_get_nested(template_dict, "fixing_tape_length_mm", 200.0),
            fixing_tape_density_gcm3=_get_nested(template_dict, "fixing_tape_density_gcm3", 1.42),
            insulation_coating_density_gcm3=_get_nested(
                template_dict, "insulation_coating_density_gcm3", 0.91
            ),
        )
    except (MissingFieldError, MappingError):
        raise
    except Exception as e:
        raise MappingError(f"Failed to convert template to PrismaticCellInput: {e}")


def from_yaml_file(yaml_path: str) -> PrismaticCellInput:
    """
    Load YAML file and convert to PrismaticCellInput.

    Args:
        yaml_path: Path to YAML template file

    Returns:
        PrismaticCellInput instance

    Raises:
        FileNotFoundError: If YAML file not found
        yaml.YAMLError: If YAML parsing fails
        MissingFieldError: If required fields missing
        MappingError: If mapping fails
    """
    try:
        with open(yaml_path) as f:
            template_dict = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")
    except yaml.YAMLError as e:
        raise MappingError(f"YAML parsing error: {e}", yaml_path)

    return from_template_format(template_dict)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# POUCH CELL CONVERSION FUNCTIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def _map_pouch_sheet_geometry(geometry: dict[str, Any]) -> SheetGeometry:
    """
    Map pouch geometry dict to SheetGeometry.

    Pouch uses symmetric offsets (same offset on all sides).

    Args:
        geometry: Geometry section from pouch YAML template

    Returns:
        SheetGeometry instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        # Pouch uses symmetric offsets - same value for x and y
        anode_offset = _require_nested(geometry, "anode_offset_mm")
        separator_offset = _require_nested(geometry, "separator_offset_mm")

        return SheetGeometry(
            cathode_height_mm=_require_nested(geometry, "cathode_height_mm"),
            cathode_width_mm=_require_nested(geometry, "cathode_width_mm"),
            anode_offset_y_mm=anode_offset,
            anode_offset_x_mm=anode_offset,
            separator_offset_y_mm=separator_offset,
            separator_offset_x_mm=separator_offset,
            # Flag areas are optional
            cathode_flag_width_mm=_get_nested(geometry, "cathode_flag_width_mm", 0.0),
            cathode_flag_height_mm=_get_nested(geometry, "cathode_flag_height_mm", 0.0),
            anode_flag_width_mm=_get_nested(geometry, "anode_flag_width_mm", 0.0),
            anode_flag_height_mm=_get_nested(geometry, "anode_flag_height_mm", 0.0),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map pouch sheet geometry: {e}", "geometry")


def _map_pouch_packaging(packaging: dict[str, Any]) -> PouchPackaging:
    """
    Map pouch packaging dict to PouchPackaging.

    Args:
        packaging: Packaging section from pouch YAML template

    Returns:
        PouchPackaging instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        # Pouch uses symmetric side offsets
        offset_sides = _require_nested(packaging, "offset_sides_mm")

        return PouchPackaging(
            pouch_offset_top_mm=_require_nested(packaging, "offset_top_mm"),
            pouch_offset_bottom_mm=_require_nested(packaging, "offset_bottom_mm"),
            pouch_offset_left_mm=offset_sides,
            pouch_offset_right_mm=offset_sides,
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map pouch packaging: {e}", "packaging")


def _map_pouch_stack_config(stack_config: dict[str, Any]) -> StackConfiguration:
    """
    Map pouch stack_config dict to StackConfiguration.

    Args:
        stack_config: Stack config section from pouch YAML template

    Returns:
        StackConfiguration instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        # Map end electrode config string to enum
        end_config_str = _require_nested(stack_config, "end_electrode_config")
        end_config = EndElectrodesMode(end_config_str)

        return StackConfiguration(
            number_of_stacks=_require_nested(stack_config, "num_stacks"),
            electrode_pairs_per_stack=_require_nested(stack_config, "electrode_pairs_per_stack"),
            end_electrodes=end_config,
            separator_overwraps_per_stack=_get_nested(stack_config, "separator_overwraps", 1),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map pouch stack config: {e}", "stack_config")


def _map_pouch_tab(tab_dict: dict[str, Any], electrode_type: str) -> TabConfig:
    """
    Map tab dict to TabConfig.

    Args:
        tab_dict: Tab section from pouch YAML template
        electrode_type: "cathode" or "anode" for error messages

    Returns:
        TabConfig instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        material = _require_nested(tab_dict, "material")

        # Get density from material name or use provided value
        density = _get_nested(tab_dict, "density_gcm3", None)
        if density is None:
            # Default densities for common tab materials
            material_lower = material.lower()
            if "aluminum" in material_lower or "al" in material_lower:
                density = 2.70  # Aluminum density
            elif "copper" in material_lower or "cu" in material_lower:
                density = 8.96  # Copper density
            elif "nickel" in material_lower or "ni" in material_lower:
                density = 8.90  # Nickel density
            else:
                density = 8.96  # Default to copper density

        return TabConfig(
            material=material,
            height_mm=_require_nested(tab_dict, "height_mm"),
            width_mm=_require_nested(tab_dict, "width_mm"),
            thickness_mm=_require_nested(tab_dict, "thickness_mm"),
            density_gcm3=density,
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map {electrode_type} tab: {e}", f"tabs.{electrode_type}")


def _map_pouch_cathode(electrochemistry: dict[str, Any]) -> CathodeMaterial:
    """
    Map pouch electrochemistry.cathode dict to CathodeMaterial.

    Args:
        electrochemistry: Electrochemistry section from pouch YAML template

    Returns:
        CathodeMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        cathode = electrochemistry.get("cathode", {})
        name = _require_nested(cathode, "material_name")
        chemistry = material_defaults.detect_chemistry(name)

        return CathodeMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            chemistry=chemistry or "NCM",
            rev_spec_capacity_mahg=_require_nested(cathode, "rev_spec_capacity_mahg"),
            max_spec_capacity_mahg=_get_nested(
                cathode,
                "max_spec_capacity_mahg",
                material_defaults.get_max_specific_capacity(chemistry),
            ),
            areal_weight_mgcm2=_require_nested(cathode, "loading_mg_cm2"),
            collector_thickness_um=_require_nested(cathode, "collector_thickness_um"),
            coating_density_gcm3=_get_nested(cathode, "coating_density_gcm3", 3.5),
            coating_thickness_0pct_um=_require_nested(cathode, "coating_thickness_0pct_um"),
            coating_thickness_100pct_um=_require_nested(cathode, "coating_thickness_100pct_um"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map pouch cathode material: {e}", "electrochemistry.cathode")


def _map_pouch_anode(electrochemistry: dict[str, Any]) -> AnodeMaterial:
    """
    Map pouch electrochemistry.anode dict to AnodeMaterial.

    Args:
        electrochemistry: Electrochemistry section from pouch YAML template

    Returns:
        AnodeMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        anode = electrochemistry.get("anode", {})
        name = _require_nested(anode, "material_name")
        chemistry = material_defaults.detect_chemistry(name)

        return AnodeMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            chemistry=chemistry or "Graphite",
            rev_spec_capacity_mahg=_require_nested(anode, "rev_spec_capacity_mahg"),
            max_spec_capacity_mahg=_get_nested(
                anode,
                "max_spec_capacity_mahg",
                material_defaults.get_max_specific_capacity(chemistry),
            ),
            areal_weight_mgcm2=_require_nested(anode, "loading_mg_cm2"),
            collector_thickness_um=_require_nested(anode, "collector_thickness_um"),
            coating_density_gcm3=_get_nested(anode, "coating_density_gcm3", 2.2),
            coating_thickness_0pct_um=_require_nested(anode, "coating_thickness_0pct_um"),
            coating_thickness_100pct_um=_require_nested(anode, "coating_thickness_100pct_um"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map pouch anode material: {e}", "electrochemistry.anode")


def _map_pouch_separator(electrochemistry: dict[str, Any]) -> SeparatorMaterial:
    """
    Map pouch electrochemistry.separator dict to SeparatorMaterial.

    Args:
        electrochemistry: Electrochemistry section from pouch YAML template

    Returns:
        SeparatorMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        separator = electrochemistry.get("separator", {})
        name = _require_nested(separator, "material_name")

        return SeparatorMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            thickness_um=_require_nested(separator, "thickness_um"),
            porosity_pct=_require_nested(separator, "porosity_pct"),
            density_gcm3=_get_nested(
                separator, "density_gcm3", material_defaults.get_separator_density(name)
            ),
            areal_weight_mgcm2=_require_nested(separator, "areal_weight_mgcm2"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(
            f"Failed to map pouch separator material: {e}", "electrochemistry.separator"
        )


def _map_pouch_electrolyte(electrochemistry: dict[str, Any]) -> ElectrolyteModel:
    """
    Map pouch electrochemistry.electrolyte dict to ElectrolyteModel.

    Args:
        electrochemistry: Electrochemistry section from pouch YAML template

    Returns:
        ElectrolyteModel instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        electrolyte = electrochemistry.get("electrolyte", {})
        name = _require_nested(electrolyte, "material_name")

        return ElectrolyteModel(
            id=name.lower().replace(" ", "_"),
            name=name,
            density_gcm3=_require_nested(electrolyte, "density_g_cm3"),
            conductivity_sm=_get_nested(electrolyte, "conductivity_sm", None),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map pouch electrolyte: {e}", "electrochemistry.electrolyte")


def _get_default_pouch_layers() -> list[PackagingLayer]:
    """Return default pouch foil layer composition (PET/Al/PP)."""
    return [
        PackagingLayer(
            name="PET",
            version="v1",
            thickness_um=12.0,
            porosity_pct=0.0,
            density_gcm3=1.38,
        ),
        PackagingLayer(
            name="Aluminum",
            version="v1",
            thickness_um=40.0,
            porosity_pct=0.0,
            density_gcm3=2.70,
        ),
        PackagingLayer(
            name="PP",
            version="v1",
            thickness_um=60.0,
            porosity_pct=0.0,
            density_gcm3=0.91,
        ),
    ]


def from_pouch_template_format(template_dict: dict[str, Any]) -> PouchCellInput:
    """
    Convert validated pouch YAML template dict to PouchCellInput.

    Args:
        template_dict: Validated pouch YAML template dictionary with structure:
            - _meta (optional): Metadata about the design
            - geometry: Sheet dimensions (cathode_height, cathode_width, offsets)
            - stack_config: Stack configuration (num_stacks, pairs, end_electrodes)
            - electrochemistry: Active materials (cathode, anode, separator, electrolyte)
            - tabs: Tab configurations (cathode and anode)
            - packaging: Pouch packaging (offsets, thickness)

    Returns:
        PouchCellInput instance ready for calculation

    Raises:
        MissingFieldError: If required fields missing
        MappingError: If mapping fails
    """
    try:
        # Extract main sections
        geometry = template_dict.get("geometry", {})
        stack_config = template_dict.get("stack_config", {})
        electrochemistry = template_dict.get("electrochemistry", {})
        tabs = template_dict.get("tabs", {})
        packaging = template_dict.get("packaging", {})

        # Map geometry and packaging
        sheet_geometry = _map_pouch_sheet_geometry(geometry)
        pouch_packaging = _map_pouch_packaging(packaging)
        stack_configuration = _map_pouch_stack_config(stack_config)

        # Map materials
        cathode = _map_pouch_cathode(electrochemistry)
        anode = _map_pouch_anode(electrochemistry)
        separator = _map_pouch_separator(electrochemistry)
        electrolyte = _map_pouch_electrolyte(electrochemistry)

        # Map tabs
        cathode_tab = _map_pouch_tab(tabs.get("cathode", {}), "cathode")
        anode_tab = _map_pouch_tab(tabs.get("anode", {}), "anode")

        # Get cell name from _meta or use default
        cell_name = _get_nested(template_dict, "_meta.design_intent", "Pouch Cell")
        if cell_name == "Pouch Cell":
            cell_name = _get_nested(template_dict, "cell_name", "Pouch Cell")

        # Get pouch thickness for foil layers (convert to um)
        pouch_thickness_mm = _get_nested(packaging, "pouch_thickness_mm", 0.113)
        pouch_thickness_um = pouch_thickness_mm * 1000

        # Create default pouch layers scaled to match total thickness
        case_composition = _get_default_pouch_layers()
        default_total_um = sum(layer.thickness_um for layer in case_composition)
        scale_factor = pouch_thickness_um / default_total_um if default_total_um > 0 else 1.0

        # Scale layer thicknesses to match specified pouch thickness
        case_composition = [
            PackagingLayer(
                name=layer.name,
                version=layer.version,
                thickness_um=layer.thickness_um * scale_factor,
                porosity_pct=layer.porosity_pct,
                density_gcm3=layer.density_gcm3,
            )
            for layer in case_composition
        ]

        # Create the main input object
        return PouchCellInput(
            cell_name=cell_name,
            cathode=cathode,
            anode=anode,
            separator=separator,
            electrolyte=electrolyte,
            geometry=sheet_geometry,
            packaging=pouch_packaging,
            stack_config=stack_configuration,
            case_composition=case_composition,
            cathode_tab=cathode_tab,
            anode_tab=anode_tab,
            nominal_voltage_v=_get_nested(template_dict, "nominal_voltage_v", 3.65),
            capacity_ah=_get_nested(template_dict, "capacity_ah", None),
            electrolyte_excess_factor=_get_nested(
                electrochemistry, "electrolyte.excess_factor", 1.10
            ),
            cathode_porosity_pct=_get_nested(electrochemistry, "cathode.porosity_pct", 25.0),
            anode_porosity_pct=_get_nested(electrochemistry, "anode.porosity_pct", 35.0),
        )
    except (MissingFieldError, MappingError):
        raise
    except Exception as e:
        raise MappingError(f"Failed to convert template to PouchCellInput: {e}")


def from_pouch_yaml_file(yaml_path: str) -> PouchCellInput:
    """
    Load pouch YAML file and convert to PouchCellInput.

    Args:
        yaml_path: Path to pouch YAML template file

    Returns:
        PouchCellInput instance

    Raises:
        FileNotFoundError: If YAML file not found
        yaml.YAMLError: If YAML parsing fails
        MissingFieldError: If required fields missing
        MappingError: If mapping fails
    """
    try:
        with open(yaml_path) as f:
            template_dict = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")
    except yaml.YAMLError as e:
        raise MappingError(f"YAML parsing error: {e}", yaml_path)

    return from_pouch_template_format(template_dict)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# CYLINDRICAL CELL CONVERSION FUNCTIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def _map_cylindrical_geometry(geometry: dict[str, Any]) -> CylindricalGeometry:
    """
    Map cylindrical geometry dict to CylindricalGeometry.

    Args:
        geometry: Geometry section from cylindrical YAML template

    Returns:
        CylindricalGeometry instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        return CylindricalGeometry(
            diameter_mm=_require_nested(geometry, "diameter_mm"),
            length_mm=_require_nested(geometry, "length_mm"),
            can_wall_thickness_mm=_require_nested(geometry, "can_wall_thickness_mm"),
            can_bottom_thickness_mm=_require_nested(geometry, "can_bottom_thickness_mm"),
            header_height_mm=_require_nested(geometry, "header_height_mm"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map cylindrical geometry: {e}", "geometry")


def _map_winding_config(winding: dict[str, Any]) -> WindingConfig:
    """
    Map winding dict to WindingConfig.

    Args:
        winding: Winding section from cylindrical YAML template

    Returns:
        WindingConfig instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        # Parse tab type from string
        tab_type_str = _require_nested(winding, "tab_type")
        tab_type = TabType(tab_type_str.lower())

        # Create base config
        config = WindingConfig(
            mandrel_diameter_mm=_require_nested(winding, "mandrel_diameter_mm"),
            winding_clearance_mm=_require_nested(winding, "winding_clearance_mm"),
            winding_tension_factor=_require_nested(winding, "winding_tension_factor"),
            tab_type=tab_type,
            # Traditional tab fields (optional)
            anode_tab_width_mm=_get_nested(winding, "anode_tab_width_mm", None),
            anode_tab_thickness_mm=_get_nested(winding, "anode_tab_thickness_mm", None),
            cathode_tab_width_mm=_get_nested(winding, "cathode_tab_width_mm", None),
            cathode_tab_thickness_mm=_get_nested(winding, "cathode_tab_thickness_mm", None),
            # Tabless foil extension fields (optional)
            anode_foil_extension_mm=_get_nested(winding, "anode_foil_extension_mm", None),
            cathode_foil_extension_mm=_get_nested(winding, "cathode_foil_extension_mm", None),
        )

        return config
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(f"Failed to map winding config: {e}", "winding")


def _map_can_material(housing: dict[str, Any]) -> CanMaterial:
    """
    Map can material string to CanMaterial enum.

    Args:
        housing: Housing section from cylindrical YAML template

    Returns:
        CanMaterial enum value
    """
    can_material_str = _require_nested(housing, "can_material")

    # Map string to enum
    material_map = {
        "steel": CanMaterial.STEEL,
        "aluminum": CanMaterial.ALUMINUM,
        "nickel_plated_steel": CanMaterial.NICKEL_PLATED_STEEL,
    }

    return material_map.get(can_material_str.lower(), CanMaterial.STEEL)


def _map_cylindrical_cathode(electrochemistry: dict[str, Any]) -> CathodeMaterial:
    """
    Map cylindrical electrochemistry.cathode dict to CathodeMaterial.

    Args:
        electrochemistry: Electrochemistry section from cylindrical YAML template

    Returns:
        CathodeMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        cathode = electrochemistry.get("cathode", {})
        name = _require_nested(cathode, "material_name")
        chemistry = material_defaults.detect_chemistry(name)

        return CathodeMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            chemistry=chemistry or "NCM",
            rev_spec_capacity_mahg=_require_nested(cathode, "rev_spec_capacity_mahg"),
            max_spec_capacity_mahg=_get_nested(
                cathode,
                "max_spec_capacity_mahg",
                material_defaults.get_max_specific_capacity(chemistry),
            ),
            areal_weight_mgcm2=_require_nested(cathode, "loading_mg_cm2"),
            collector_thickness_um=_require_nested(cathode, "collector_thickness_um"),
            coating_density_gcm3=_get_nested(cathode, "coating_density_gcm3", 3.5),
            coating_thickness_0pct_um=_require_nested(cathode, "coating_thickness_0pct_um"),
            coating_thickness_100pct_um=_require_nested(cathode, "coating_thickness_100pct_um"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(
            f"Failed to map cylindrical cathode material: {e}", "electrochemistry.cathode"
        )


def _map_cylindrical_anode(electrochemistry: dict[str, Any]) -> AnodeMaterial:
    """
    Map cylindrical electrochemistry.anode dict to AnodeMaterial.

    Args:
        electrochemistry: Electrochemistry section from cylindrical YAML template

    Returns:
        AnodeMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        anode = electrochemistry.get("anode", {})
        name = _require_nested(anode, "material_name")
        chemistry = material_defaults.detect_chemistry(name)

        return AnodeMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            chemistry=chemistry or "Graphite",
            rev_spec_capacity_mahg=_require_nested(anode, "rev_spec_capacity_mahg"),
            max_spec_capacity_mahg=_get_nested(
                anode,
                "max_spec_capacity_mahg",
                material_defaults.get_max_specific_capacity(chemistry),
            ),
            areal_weight_mgcm2=_require_nested(anode, "loading_mg_cm2"),
            collector_thickness_um=_require_nested(anode, "collector_thickness_um"),
            coating_density_gcm3=_get_nested(anode, "coating_density_gcm3", 2.2),
            coating_thickness_0pct_um=_require_nested(anode, "coating_thickness_0pct_um"),
            coating_thickness_100pct_um=_require_nested(anode, "coating_thickness_100pct_um"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(
            f"Failed to map cylindrical anode material: {e}", "electrochemistry.anode"
        )


def _map_cylindrical_separator(electrochemistry: dict[str, Any]) -> SeparatorMaterial:
    """
    Map cylindrical electrochemistry.separator dict to SeparatorMaterial.

    Args:
        electrochemistry: Electrochemistry section from cylindrical YAML template

    Returns:
        SeparatorMaterial instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        separator = electrochemistry.get("separator", {})
        name = _require_nested(separator, "material_name")

        return SeparatorMaterial(
            id=name.lower().replace(" ", "_"),
            name=name,
            thickness_um=_require_nested(separator, "thickness_um"),
            porosity_pct=_require_nested(separator, "porosity_pct"),
            density_gcm3=_get_nested(
                separator, "density_gcm3", material_defaults.get_separator_density(name)
            ),
            areal_weight_mgcm2=_require_nested(separator, "areal_weight_mgcm2"),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(
            f"Failed to map cylindrical separator material: {e}", "electrochemistry.separator"
        )


def _map_cylindrical_electrolyte(electrochemistry: dict[str, Any]) -> ElectrolyteModel:
    """
    Map cylindrical electrochemistry.electrolyte dict to ElectrolyteModel.

    Args:
        electrochemistry: Electrochemistry section from cylindrical YAML template

    Returns:
        ElectrolyteModel instance

    Raises:
        MissingFieldError: If required fields missing
    """
    try:
        electrolyte = electrochemistry.get("electrolyte", {})
        name = _require_nested(electrolyte, "material_name")

        return ElectrolyteModel(
            id=name.lower().replace(" ", "_"),
            name=name,
            density_gcm3=_require_nested(electrolyte, "density_g_cm3"),
            conductivity_sm=_get_nested(electrolyte, "conductivity_sm", None),
        )
    except MissingFieldError:
        raise
    except Exception as e:
        raise MappingError(
            f"Failed to map cylindrical electrolyte: {e}", "electrochemistry.electrolyte"
        )


def from_cylindrical_template_format(template_dict: dict[str, Any]) -> CylindricalCellInput:
    """
    Convert validated cylindrical YAML template dict to CylindricalCellInput.

    Args:
        template_dict: Validated cylindrical YAML template dictionary with structure:
            - _meta (optional): Metadata about the design (cell_type, format, design_intent)
            - geometry: Can dimensions (diameter, length, wall thicknesses, header)
            - winding: Jelly roll winding config (mandrel, clearance, tension, tab_type)
            - electrochemistry: Active materials (cathode, anode, separator, electrolyte)
            - housing: Can housing config (can_material, header_mass_g)
            - tabs (optional): Tab configurations for traditional tab type

    Returns:
        CylindricalCellInput instance ready for calculation

    Raises:
        MissingFieldError: If required fields missing
        MappingError: If mapping fails
    """
    try:
        # Extract main sections
        geometry = template_dict.get("geometry", {})
        winding = template_dict.get("winding", {})
        electrochemistry = template_dict.get("electrochemistry", {})
        housing = template_dict.get("housing", {})

        # Map geometry and winding
        cell_geometry = _map_cylindrical_geometry(geometry)
        winding_config = _map_winding_config(winding)
        can_material = _map_can_material(housing)

        # Map materials
        cathode = _map_cylindrical_cathode(electrochemistry)
        anode = _map_cylindrical_anode(electrochemistry)
        separator = _map_cylindrical_separator(electrochemistry)
        electrolyte = _map_cylindrical_electrolyte(electrochemistry)

        # Get cell name from _meta or use default
        cell_name = _get_nested(template_dict, "_meta.design_intent", "Cylindrical Cell")
        if cell_name == "Cylindrical Cell":
            cell_name = _get_nested(template_dict, "cell_name", "Cylindrical Cell")

        # Get format for naming if available
        cell_format = _get_nested(template_dict, "_meta.format", None)
        if cell_format and cell_name == "Cylindrical Cell":
            cell_name = f"{cell_format} Cell"

        # Create simplified header from housing
        header_mass = _get_nested(housing, "header_mass_g", 2.0)  # Default 2.0g
        header_simplified = SimplifiedHeader(
            total_mass_g=header_mass,
            cap_material=can_material,
        )

        # Create the main input object
        return CylindricalCellInput(
            cell_name=cell_name,
            geometry=cell_geometry,
            winding=winding_config,
            can_material=can_material,
            cathode=cathode,
            anode=anode,
            separator=separator,
            electrolyte=electrolyte,
            header_simplified=header_simplified,
            # Optional parameters
            nominal_voltage_v=_get_nested(template_dict, "nominal_voltage_v", 3.6),
            capacity_ah=_get_nested(template_dict, "capacity_ah", None),
            electrolyte_excess_factor=_get_nested(
                electrochemistry, "electrolyte.excess_factor", 1.0
            ),
            cathode_porosity_pct=_get_nested(electrochemistry, "cathode.porosity_pct", 25.0),
            anode_porosity_pct=_get_nested(electrochemistry, "anode.porosity_pct", 35.0),
            bottom_insulator_mass_g=_get_nested(housing, "bottom_insulator_mass_g", 0.1),
            top_insulator_mass_g=_get_nested(housing, "top_insulator_mass_g", 0.1),
        )
    except (MissingFieldError, MappingError):
        raise
    except Exception as e:
        raise MappingError(f"Failed to convert template to CylindricalCellInput: {e}")


def from_cylindrical_yaml_file(yaml_path: str) -> CylindricalCellInput:
    """
    Load cylindrical YAML file and convert to CylindricalCellInput.

    Args:
        yaml_path: Path to cylindrical YAML template file

    Returns:
        CylindricalCellInput instance

    Raises:
        FileNotFoundError: If YAML file not found
        yaml.YAMLError: If YAML parsing fails
        MissingFieldError: If required fields missing
        MappingError: If mapping fails
    """
    try:
        with open(yaml_path) as f:
            template_dict = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")
    except yaml.YAMLError as e:
        raise MappingError(f"YAML parsing error: {e}", yaml_path)

    return from_cylindrical_template_format(template_dict)
