"""Reference JSON -> typed engine input mappers."""

from forge.engine.models.cylindrical import (
    CanMaterial,
    CylindricalCellInput,
    CylindricalGeometry,
    HeaderComponents,
    SimplifiedHeader,
    TabType,
    WindingConfig,
)
from forge.engine.models.geometry import PouchPackaging, SheetGeometry
from forge.engine.models.materials import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    DENSITY_PET,
    DENSITY_PP,
    NMC_NOMINAL_VOLTAGE,
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
    TabConfig,
)
from forge.engine.models.pouch import PouchCellInput
from forge.engine.models.prismatic import (
    PrismaticCellInput,
    PrismaticGeometry,
    PrismaticSheetGeometry,
)
from forge.engine.models.stack import EndElectrodesMode, StackConfiguration
from forge.engine.reference.loader import load_reference_cell


def _parse_end_electrodes(value: str) -> EndElectrodesMode:
    mapping = {
        "BothNegative": EndElectrodesMode.BOTH_NEGATIVE,
        "BothPositive": EndElectrodesMode.BOTH_POSITIVE,
        "PositiveNegative": EndElectrodesMode.POSITIVE_NEGATIVE,
    }
    return mapping.get(value, EndElectrodesMode.BOTH_NEGATIVE)


def from_reference_pouch(ref_id: str) -> PouchCellInput:
    """Build ``PouchCellInput`` from project reference JSON by ID."""
    ref = load_reference_cell(ref_id)
    data = ref.raw_data

    materials = data.get("materials", {})
    geometry = data.get("geometry_inputs", {})
    stack = data.get("stack_config", {})
    specs = data.get("cell_specs", {})

    cathode_raw = materials.get("cathode", {})
    anode_raw = materials.get("anode", {})
    separator_raw = materials.get("separator", {})
    electrolyte_raw = materials.get("electrolyte", {})

    cathode = CathodeMaterial(
        id=f"{ref_id}_cathode",
        name=cathode_raw.get("name", "Cathode"),
        chemistry=cathode_raw.get("chemistry", "NMC"),
        rev_spec_capacity_mahg=cathode_raw.get("rev_spec_capacity_mahg", 165.0),
        max_spec_capacity_mahg=cathode_raw.get("max_spec_capacity_mahg", 180.0),
        areal_weight_mgcm2=cathode_raw.get("loading_mgcm2", 18.0),
        collector_thickness_um=cathode_raw.get("collector_thickness_um", 15.0),
        coating_density_gcm3=cathode_raw.get("coating_density_gcm3", 3.5),
        coating_thickness_0pct_um=cathode_raw.get("coating_thickness_0pct_um", 70.0),
        coating_thickness_100pct_um=cathode_raw.get("coating_thickness_100pct_um", 71.4),
    )

    anode = AnodeMaterial(
        id=f"{ref_id}_anode",
        name=anode_raw.get("name", "Anode"),
        chemistry=anode_raw.get("chemistry", "Graphite"),
        rev_spec_capacity_mahg=anode_raw.get("rev_spec_capacity_mahg", 360.0),
        max_spec_capacity_mahg=anode_raw.get("max_spec_capacity_mahg", 372.0),
        areal_weight_mgcm2=anode_raw.get("loading_mgcm2", 10.0),
        collector_thickness_um=anode_raw.get("collector_thickness_um", 10.0),
        coating_density_gcm3=anode_raw.get("coating_density_gcm3", 1.6),
        coating_thickness_0pct_um=anode_raw.get("coating_thickness_0pct_um", 80.0),
        coating_thickness_100pct_um=anode_raw.get("coating_thickness_100pct_um", 84.0),
    )

    separator = SeparatorMaterial(
        id=f"{ref_id}_separator",
        name=separator_raw.get("name", "Separator"),
        thickness_um=separator_raw.get("thickness_um", 20.0),
        porosity_pct=separator_raw.get("porosity_pct", 40.0),
        density_gcm3=separator_raw.get("density_gcm3", DENSITY_PP),
        areal_weight_mgcm2=separator_raw.get("areal_weight_mgcm2", 1.0),
    )

    electrolyte = ElectrolyteModel(
        id=f"{ref_id}_electrolyte",
        name=electrolyte_raw.get("name", "Electrolyte"),
        density_gcm3=electrolyte_raw.get("density_gcm3", 1.25),
    )

    sheet_geometry = SheetGeometry(
        cathode_height_mm=geometry.get("cathode_height_mm", 180.0),
        cathode_width_mm=geometry.get("cathode_width_mm", 100.0),
        anode_offset_y_mm=geometry.get("anode_offset_y_mm", 2.0),
        anode_offset_x_mm=geometry.get("anode_offset_x_mm", 2.0),
        separator_offset_y_mm=geometry.get("separator_offset_y_mm", 1.0),
        separator_offset_x_mm=geometry.get("separator_offset_x_mm", 1.0),
    )

    packaging = PouchPackaging(
        pouch_offset_top_mm=geometry.get("pouch_offset_top_mm", 10.0),
        pouch_offset_bottom_mm=geometry.get("pouch_offset_bottom_mm", 5.0),
        pouch_offset_left_mm=geometry.get("pouch_offset_left_mm", 5.0),
        pouch_offset_right_mm=geometry.get("pouch_offset_right_mm", 5.0),
    )

    stack_config = StackConfiguration(
        number_of_stacks=stack.get("number_of_stacks", 1),
        electrode_pairs_per_stack=stack.get(
            "electrode_pairs",
            stack.get("electrode_pairs_per_stack", 15),
        ),
        end_electrodes=_parse_end_electrodes(stack.get("end_electrodes", "BothNegative")),
        separator_overwraps_per_stack=stack.get(
            "separator_overwraps",
            stack.get("separator_overwraps_per_stack", 1),
        ),
        additional_overwraps_per_stack=stack.get(
            "additional_overwraps",
            stack.get("additional_overwraps_per_stack", 0),
        ),
        insulation_shell_count=stack.get("insulation_shell_count", 1),
        fixing_tapes_per_stack=stack.get(
            "fixing_tapes_per_stack",
            stack.get("fixing_tape_count", 2),
        ),
    )

    case_layers = materials.get("case_composition", [])
    if not case_layers:
        case_layers = [
            {
                "name": "PET",
                "thickness_um": 12.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_PET,
            },
            {
                "name": "Aluminum",
                "thickness_um": 40.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_ALUMINUM,
            },
            {
                "name": "PP",
                "thickness_um": 80.0,
                "porosity_pct": 0.0,
                "density_gcm3": DENSITY_PP,
            },
        ]
    case_composition = [
        PackagingLayer(
            name=layer.get("name", "Layer"),
            version="1.0",
            thickness_um=layer.get("thickness_um", 10.0),
            porosity_pct=layer.get("porosity_pct", 0.0),
            density_gcm3=layer.get("density_gcm3", 1.0),
        )
        for layer in case_layers
    ]

    cathode_tab_raw = materials.get("cathode_tab", {})
    cathode_tab = TabConfig(
        material=cathode_tab_raw.get("material", "Aluminum"),
        height_mm=cathode_tab_raw.get("height_mm", 30.0),
        width_mm=cathode_tab_raw.get("width_mm", 40.0),
        thickness_mm=cathode_tab_raw.get("thickness_mm", 0.3),
        density_gcm3=cathode_tab_raw.get("density_gcm3", DENSITY_ALUMINUM),
    )

    anode_tab_raw = materials.get("anode_tab", {})
    anode_tab = TabConfig(
        material=anode_tab_raw.get("material", "Copper"),
        height_mm=anode_tab_raw.get("height_mm", 30.0),
        width_mm=anode_tab_raw.get("width_mm", 40.0),
        thickness_mm=anode_tab_raw.get("thickness_mm", 0.2),
        density_gcm3=anode_tab_raw.get("density_gcm3", DENSITY_COPPER),
    )

    return PouchCellInput(
        cell_name=ref.name,
        cathode=cathode,
        anode=anode,
        separator=separator,
        electrolyte=electrolyte,
        geometry=sheet_geometry,
        packaging=packaging,
        stack_config=stack_config,
        case_composition=case_composition,
        anode_tab=anode_tab,
        cathode_tab=cathode_tab,
        nominal_voltage_v=specs.get("nominal_voltage_v", NMC_NOMINAL_VOLTAGE),
        capacity_ah=specs.get("capacity_ah"),
        electrolyte_excess_factor=electrolyte_raw.get("excess_factor", 1.10),
        electrolyte_volume_override_ml=electrolyte_raw.get("volume_override_ml"),
        cathode_porosity_pct=stack.get("cathode_porosity_pct", 30.0),
        anode_porosity_pct=stack.get("anode_porosity_pct", 35.0),
    )


def from_reference_prismatic(ref_id: str) -> PrismaticCellInput:
    """Build ``PrismaticCellInput`` from project reference JSON by ID."""
    ref = load_reference_cell(ref_id)
    data = ref.raw_data

    geo = data.get("geometry_inputs", {})
    case_geo = data.get("case_geometry", {})
    stack_cfg = data.get("stack_config", {})
    housing = data.get("housing", {})
    materials = data.get("materials", {})
    cell_specs = data.get("cell_specs", {})

    case_geometry = PrismaticGeometry(
        cell_height_mm=case_geo["cell_height_mm"],
        cell_width_mm=case_geo["cell_width_mm"],
        cell_thickness_mm=case_geo["cell_thickness_mm"],
        wall_top_mm=case_geo["wall_top_mm"],
        wall_bottom_mm=case_geo["wall_bottom_mm"],
        wall_front_back_mm=case_geo["wall_front_back_mm"],
        wall_sides_mm=case_geo["wall_sides_mm"],
        insulation_coating_um=case_geo.get("insulation_coating_um", 85.0),
    )

    sheet_geometry = PrismaticSheetGeometry(
        cathode_height_mm=geo["cathode_height_mm"],
        cathode_width_mm=geo["cathode_width_mm"],
        anode_offset_top_mm=geo.get("anode_offset_top_mm", 2.0),
        anode_offset_bottom_mm=geo.get("anode_offset_bottom_mm", 2.0),
        anode_offset_left_mm=geo.get("anode_offset_left_mm", 2.0),
        anode_offset_right_mm=geo.get("anode_offset_right_mm", 2.0),
        separator_offset_top_mm=geo.get("separator_offset_top_mm", 2.0),
        separator_offset_bottom_mm=geo.get("separator_offset_bottom_mm", 2.0),
        separator_offset_left_mm=geo.get("separator_offset_left_mm", 2.0),
        separator_offset_right_mm=geo.get("separator_offset_right_mm", 2.0),
    )

    cathode_raw = materials.get("cathode", {})
    cathode = CathodeMaterial(
        id=f"CAT_{ref_id.upper()}",
        name=cathode_raw.get("name", "Cathode"),
        chemistry=cathode_raw.get("chemistry", "NCM"),
        rev_spec_capacity_mahg=cathode_raw["rev_spec_capacity_mahg"],
        max_spec_capacity_mahg=cathode_raw.get("max_spec_capacity_mahg", 200.0),
        areal_weight_mgcm2=cathode_raw["loading_mgcm2"],
        collector_thickness_um=cathode_raw["collector_thickness_um"],
        coating_density_gcm3=cathode_raw["coating_density_gcm3"],
        coating_thickness_0pct_um=cathode_raw["coating_thickness_0pct_um"],
        coating_thickness_100pct_um=cathode_raw.get(
            "coating_thickness_100pct_um",
            cathode_raw["coating_thickness_0pct_um"],
        ),
    )

    anode_raw = materials.get("anode", {})
    anode = AnodeMaterial(
        id=f"ANO_{ref_id.upper()}",
        name=anode_raw.get("name", "Anode"),
        chemistry=anode_raw.get("chemistry", "Graphite"),
        rev_spec_capacity_mahg=anode_raw["rev_spec_capacity_mahg"],
        max_spec_capacity_mahg=anode_raw.get("max_spec_capacity_mahg", 372.0),
        areal_weight_mgcm2=anode_raw["loading_mgcm2"],
        collector_thickness_um=anode_raw["collector_thickness_um"],
        coating_density_gcm3=anode_raw["coating_density_gcm3"],
        coating_thickness_0pct_um=anode_raw["coating_thickness_0pct_um"],
        coating_thickness_100pct_um=anode_raw.get(
            "coating_thickness_100pct_um",
            anode_raw["coating_thickness_0pct_um"],
        ),
    )

    separator_raw = materials.get("separator", {})
    separator = SeparatorMaterial(
        id=f"SEP_{ref_id.upper()}",
        name=separator_raw.get("name", "Separator"),
        thickness_um=separator_raw["thickness_um"],
        porosity_pct=separator_raw["porosity_pct"],
        density_gcm3=separator_raw["density_gcm3"],
        areal_weight_mgcm2=separator_raw.get("areal_weight_mgcm2", 1.0),
    )

    electrolyte_raw = materials.get("electrolyte", {})
    electrolyte = ElectrolyteModel(
        id=f"ELE_{ref_id.upper()}",
        name=electrolyte_raw.get("name", "Electrolyte"),
        density_gcm3=electrolyte_raw["density_gcm3"],
    )

    return PrismaticCellInput(
        cell_name=ref.name,
        case_geometry=case_geometry,
        sheet_geometry=sheet_geometry,
        number_of_stacks=stack_cfg["number_of_stacks"],
        electrode_pairs_per_stack=stack_cfg["electrode_pairs_per_stack"],
        end_electrodes=stack_cfg.get("end_electrodes", "BothNegative"),
        cathode=cathode,
        anode=anode,
        separator=separator,
        electrolyte=electrolyte,
        case_material_density_gcm3=housing.get("case_material_density_gcm3", DENSITY_ALUMINUM),
        header_mass_g=housing["header_mass_g"],
        insulation_shell_thickness_um=stack_cfg.get("insulation_shell_thickness_um", 120.0),
        insulation_shell_count=stack_cfg.get("insulation_shell_count", 1),
        insulation_shell_density_gcm3=stack_cfg.get("insulation_shell_density_gcm3", DENSITY_PP),
        insulation_coating_density_gcm3=housing.get("insulation_coating_density_gcm3", DENSITY_PP),
        electrolyte_excess_factor=electrolyte_raw.get("excess_factor", 1.0),
        cathode_porosity_pct=stack_cfg.get("cathode_porosity_pct", 25.0),
        anode_porosity_pct=stack_cfg.get("anode_porosity_pct", 35.0),
        nominal_voltage_v=cell_specs["nominal_voltage_v"],
        capacity_ah=cell_specs.get("capacity_ah"),
        fixing_tape_count=stack_cfg.get("fixing_tape_count", 4),
        fixing_tape_thickness_um=stack_cfg.get("fixing_tape_thickness_um", 30.0),
        fixing_tape_width_mm=stack_cfg.get("fixing_tape_width_mm", 30.0),
        fixing_tape_length_mm=stack_cfg.get("fixing_tape_length_mm", 200.0),
        fixing_tape_density_gcm3=stack_cfg.get("fixing_tape_density_gcm3", 1.42),
    )


def from_reference_cylindrical(ref_id: str) -> CylindricalCellInput:
    """Build ``CylindricalCellInput`` from project reference JSON by ID."""
    ref = load_reference_cell(ref_id)
    data = ref.raw_data

    geo = data.get("geometry", {})
    winding_cfg = data.get("winding", {})
    header_cfg = data.get("header", {})
    materials = data.get("materials", {})
    cell_specs = data.get("cell_specs", {})

    geometry = CylindricalGeometry(
        diameter_mm=geo["diameter_mm"],
        length_mm=geo["length_mm"],
        can_wall_thickness_mm=geo["can_wall_thickness_mm"],
        can_bottom_thickness_mm=geo["can_bottom_thickness_mm"],
        header_height_mm=geo["header_height_mm"],
    )

    can_material_str = str(geo.get("can_material", "steel")).lower()
    if can_material_str == "aluminum":
        can_material = CanMaterial.ALUMINUM
    elif can_material_str == "nickel_plated_steel":
        can_material = CanMaterial.NICKEL_PLATED_STEEL
    else:
        can_material = CanMaterial.STEEL

    tab_type_str = str(winding_cfg.get("tab_type", "traditional")).lower()
    tab_type = TabType.TABLESS if tab_type_str == "tabless" else TabType.TRADITIONAL

    winding = WindingConfig(
        mandrel_diameter_mm=winding_cfg["mandrel_diameter_mm"],
        winding_clearance_mm=winding_cfg.get("winding_clearance_mm", 0.1),
        winding_tension_factor=winding_cfg.get("winding_tension_factor", 0.97),
        tab_type=tab_type,
        anode_tab_width_mm=winding_cfg.get("anode_tab_width_mm"),
        anode_tab_thickness_mm=winding_cfg.get("anode_tab_thickness_mm"),
        cathode_tab_width_mm=winding_cfg.get("cathode_tab_width_mm"),
        cathode_tab_thickness_mm=winding_cfg.get("cathode_tab_thickness_mm"),
        anode_foil_extension_mm=winding_cfg.get("anode_foil_extension_mm"),
        cathode_foil_extension_mm=winding_cfg.get("cathode_foil_extension_mm"),
    )

    header_simplified = None
    header = None
    if "total_mass_g" in header_cfg:
        header_simplified = SimplifiedHeader(
            total_mass_g=header_cfg["total_mass_g"],
            cap_material=can_material,
        )
    elif "ptc_mass_g" in header_cfg:
        header = HeaderComponents(
            ptc_diameter_mm=header_cfg.get("ptc_diameter_mm", 8.0),
            ptc_thickness_mm=header_cfg.get("ptc_thickness_mm", 0.8),
            ptc_mass_g=header_cfg["ptc_mass_g"],
            cid_diameter_mm=header_cfg.get("cid_diameter_mm", 10.0),
            cid_thickness_mm=header_cfg.get("cid_thickness_mm", 0.5),
            cid_mass_g=header_cfg.get("cid_mass_g", 0.2),
            vent_diameter_mm=header_cfg.get("vent_diameter_mm", 6.0),
            vent_thickness_mm=header_cfg.get("vent_thickness_mm", 0.3),
            vent_mass_g=header_cfg.get("vent_mass_g", 0.2),
            cap_diameter_mm=header_cfg.get("cap_diameter_mm", geometry.diameter_mm),
            cap_thickness_mm=header_cfg.get("cap_thickness_mm", 0.5),
            cap_material=can_material,
            gasket_mass_g=header_cfg.get("gasket_mass_g", 0.15),
            insulator_ring_mass_g=header_cfg.get("insulator_ring_mass_g", 0.1),
        )
    else:
        header_simplified = SimplifiedHeader(total_mass_g=2.0, cap_material=can_material)

    cathode_raw = materials.get("cathode", {})
    cathode = CathodeMaterial(
        id=f"CAT_{ref_id.upper()}",
        name=cathode_raw.get("name", "Cathode"),
        chemistry=cathode_raw.get("chemistry", "NMC"),
        rev_spec_capacity_mahg=cathode_raw["rev_spec_capacity_mahg"],
        max_spec_capacity_mahg=cathode_raw.get("max_spec_capacity_mahg", 220.0),
        areal_weight_mgcm2=cathode_raw["loading_mgcm2"],
        collector_thickness_um=cathode_raw["collector_thickness_um"],
        coating_density_gcm3=cathode_raw["coating_density_gcm3"],
        coating_thickness_0pct_um=cathode_raw["coating_thickness_0pct_um"],
        coating_thickness_100pct_um=cathode_raw.get(
            "coating_thickness_100pct_um",
            cathode_raw["coating_thickness_0pct_um"],
        ),
    )

    anode_raw = materials.get("anode", {})
    anode = AnodeMaterial(
        id=f"ANO_{ref_id.upper()}",
        name=anode_raw.get("name", "Anode"),
        chemistry=anode_raw.get("chemistry", "Graphite"),
        rev_spec_capacity_mahg=anode_raw["rev_spec_capacity_mahg"],
        max_spec_capacity_mahg=anode_raw.get("max_spec_capacity_mahg", 372.0),
        areal_weight_mgcm2=anode_raw["loading_mgcm2"],
        collector_thickness_um=anode_raw["collector_thickness_um"],
        coating_density_gcm3=anode_raw["coating_density_gcm3"],
        coating_thickness_0pct_um=anode_raw["coating_thickness_0pct_um"],
        coating_thickness_100pct_um=anode_raw.get(
            "coating_thickness_100pct_um",
            anode_raw["coating_thickness_0pct_um"],
        ),
    )

    separator_raw = materials.get("separator", {})
    separator = SeparatorMaterial(
        id=f"SEP_{ref_id.upper()}",
        name=separator_raw.get("name", "Separator"),
        thickness_um=separator_raw["thickness_um"],
        porosity_pct=separator_raw["porosity_pct"],
        density_gcm3=separator_raw["density_gcm3"],
        areal_weight_mgcm2=separator_raw.get("areal_weight_mgcm2", 1.0),
    )

    electrolyte_raw = materials.get("electrolyte", {})
    electrolyte = ElectrolyteModel(
        id=f"ELE_{ref_id.upper()}",
        name=electrolyte_raw.get("name", "Electrolyte"),
        density_gcm3=electrolyte_raw["density_gcm3"],
    )

    return CylindricalCellInput(
        cell_name=ref.name,
        geometry=geometry,
        winding=winding,
        can_material=can_material,
        cathode=cathode,
        anode=anode,
        separator=separator,
        electrolyte=electrolyte,
        header=header,
        header_simplified=header_simplified,
        capacity_ah=cell_specs.get("capacity_ah"),
        nominal_voltage_v=cell_specs.get("nominal_voltage_v", 3.6),
        electrolyte_excess_factor=electrolyte_raw.get("excess_factor", 1.0),
        cathode_porosity_pct=materials.get("cathode", {}).get("porosity_pct", 25.0),
        anode_porosity_pct=materials.get("anode", {}).get("porosity_pct", 35.0),
        bottom_insulator_mass_g=header_cfg.get("bottom_insulator_mass_g", 0.1),
        top_insulator_mass_g=header_cfg.get("top_insulator_mass_g", 0.1),
    )


__all__ = [
    "from_reference_pouch",
    "from_reference_prismatic",
    "from_reference_cylindrical",
]

