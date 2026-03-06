"""FORGE Streamlit GUI

A web-based graphical user interface for FORGE battery cell design calculations.
Run with: streamlit run streamlit_app.py
"""

from typing import List

import pandas as pd
import streamlit as st

from forge.engine.calculators.cylindrical_calculator import (
    CylindricalCalculator,
    create_cylindrical_from_reference,
)
from forge.engine.calculators.pouch_calculator import CellCalculator, PouchCellInput
from forge.engine.calculators.prismatic_calculator import (
    PrismaticCalculator,
    create_prismatic_from_reference,
)

# Cylindrical cell imports
from forge.engine.models.geometry import PouchPackaging, SheetGeometry

# FORGE imports
from forge.engine.models.materials import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    NMC_NOMINAL_VOLTAGE,
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    PackagingLayer,
    SeparatorMaterial,
    TabConfig,
)

# Prismatic cell imports
from forge.engine.models.stack import EndElectrodesMode, StackConfiguration

# Reference cell imports
from forge.engine.validation.result_validation import (
    get_reference_info,
    list_reference_cells,
    load_reference_cell,
)

# Tier 1 academic-validated cells with DOI references
TIER1_CELLS = {
    "lg_e78_pouch": {
        "doi": "10.1149/1945-7111/ac4e11",
        "authors": "Günter & Wassiliadis",
        "journal": "J. Electrochem. Soc. 169 (2022)",
        "highlight": "Complete electrode teardown from VW ID.3",
    },
    "catl_161ah_lfp": {
        "doi": "10.1016/j.electacta.2023.143341",
        "authors": "Stock et al.",
        "journal": "Electrochimica Acta 471 (2023)",
        "highlight": "TUM manufacturing analysis, Tesla Model 3 SR",
    },
    "lg_mj1_18650": {
        "doi": "10.1149/1945-7111/ab728d",
        "authors": "Heenan et al.",
        "journal": "J. Electrochem. Soc. 167 (2020)",
        "highlight": "Open-source X-ray tomography data (rdr.ucl.ac.uk)",
    },
}

# Check if PyBaMM is available
try:
    from forge.materials.repositories.pybamm_repo import (
        AVAILABLE_PARAMETER_SETS,
        PyBaMMRepository,
        check_pybamm_available,
    )
    PYBAMM_AVAILABLE = check_pybamm_available()
except ImportError:
    PYBAMM_AVAILABLE = False
    AVAILABLE_PARAMETER_SETS = []


# =============================================================================
# Default Values (V1 Pouch Reference)
# =============================================================================

DEFAULT_CATHODE = {
    "name": "NMC532",
    "chemistry": "NMC532",
    "rev_spec_capacity_mahg": 165.0,
    "areal_weight_mgcm2": 25.7,
    "collector_thickness_um": 15.0,
    "coating_thickness_0pct_um": 73.4,
    "coating_thickness_100pct_um": 74.9,
}

DEFAULT_ANODE = {
    "name": "Graphite",
    "chemistry": "Graphite",
    "rev_spec_capacity_mahg": 360.0,
    "areal_weight_mgcm2": 9.2,
    "collector_thickness_um": 10.0,
    "coating_thickness_0pct_um": 57.5,
    "coating_thickness_100pct_um": 60.4,
}

DEFAULT_SEPARATOR = {
    "name": "PE/PP Trilayer",
    "thickness_um": 16.0,
    "porosity_pct": 40.0,
    "areal_weight_mgcm2": 0.95,
}

DEFAULT_ELECTROLYTE = {
    "name": "LiPF6 in EC:DMC",
    "density_gcm3": 1.25,
}

DEFAULT_GEOMETRY = {
    "cathode_height_mm": 180.0,
    "cathode_width_mm": 100.0,
    "anode_offset_y_mm": 2.0,
    "anode_offset_x_mm": 2.0,
    "separator_offset_y_mm": 1.0,
    "separator_offset_x_mm": 1.0,
}

DEFAULT_STACK = {
    "number_of_stacks": 1,
    "electrode_pairs_per_stack": 15,
    "end_electrodes": "BothNegative",
    "separator_overwraps_per_stack": 1,
    "additional_overwraps_per_stack": 0,
    "insulation_shell_count": 1,
    "fixing_tapes_per_stack": 2,
}

DEFAULT_PACKAGING = {
    "pouch_offset_top_mm": 10.0,
    "pouch_offset_bottom_mm": 5.0,
    "pouch_offset_left_mm": 5.0,
    "pouch_offset_right_mm": 5.0,
}

DEFAULT_CASE_LAYERS = [
    {"name": "PET", "thickness_um": 22.0, "density_gcm3": 1.38, "porosity_pct": 0.0},
    {"name": "Aluminum", "thickness_um": 70.0, "density_gcm3": 2.70, "porosity_pct": 0.0},
    {"name": "PP", "thickness_um": 145.0, "density_gcm3": 0.95, "porosity_pct": 0.0},
]

DEFAULT_CATHODE_TAB = {
    "material": "Aluminum",
    "height_mm": 30.0,
    "width_mm": 40.0,
    "thickness_mm": 0.3,
    "density_gcm3": DENSITY_ALUMINUM,
}

DEFAULT_ANODE_TAB = {
    "material": "Copper",
    "height_mm": 30.0,
    "width_mm": 40.0,
    "thickness_mm": 0.2,
    "density_gcm3": DENSITY_COPPER,
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_pybamm_materials(parameter_set: str) -> dict:
    """Load material properties from PyBaMM parameter set."""
    if not PYBAMM_AVAILABLE:
        return None

    try:
        repo = PyBaMMRepository(parameter_set)
        cathode = repo.get_cathode()
        anode = repo.get_anode()
        separator = repo.get_separator()
        electrolyte = repo.get_electrolyte()

        return {
            "cathode": {
                "name": cathode.name,
                "chemistry": cathode.chemistry,
                "rev_spec_capacity_mahg": cathode.rev_spec_capacity_mahg,
                "areal_weight_mgcm2": cathode.areal_weight_mgcm2,
                "collector_thickness_um": cathode.collector_thickness_um,
                "coating_thickness_0pct_um": cathode.coating_thickness_0pct_um,
                "coating_thickness_100pct_um": cathode.coating_thickness_100pct_um,
            },
            "anode": {
                "name": anode.name,
                "chemistry": anode.chemistry,
                "rev_spec_capacity_mahg": anode.rev_spec_capacity_mahg,
                "areal_weight_mgcm2": anode.areal_weight_mgcm2,
                "collector_thickness_um": anode.collector_thickness_um,
                "coating_thickness_0pct_um": anode.coating_thickness_0pct_um,
                "coating_thickness_100pct_um": anode.coating_thickness_100pct_um,
            },
            "separator": {
                "name": separator.name,
                "thickness_um": separator.thickness_um,
                "porosity_pct": separator.porosity_pct,
                "areal_weight_mgcm2": separator.areal_weight_mgcm2,
            },
            "electrolyte": {
                "name": electrolyte.name,
                "density_gcm3": electrolyte.density_gcm3,
            },
        }
    except Exception as e:
        st.error(f"Failed to load PyBaMM parameters: {e}")
        return None


def load_reference_to_session(reference_id: str):
    """Load reference cell data into session state.

    IMPORTANT: Streamlit widgets with key= parameters store their values directly
    in session_state under that key. On reruns, they ignore the value= parameter
    and use session_state[key] instead. Therefore, we must set BOTH:
    1. The widget keys directly (e.g., st.session_state["cathode_height"])
    2. The param dicts for initial render (e.g., st.session_state["geometry_params"])
    """
    try:
        ref = load_reference_cell(reference_id)
        data = ref.raw_data

        materials = data.get("materials", {})
        geometry = data.get("geometry_inputs", {})
        stack = data.get("stack_config", {})
        specs = data.get("cell_specs", {})
        metadata = data.get("metadata", {})

        # Detect cell type
        cell_type = metadata.get("cell_type", "Pouch").lower()
        st.session_state["cell_type"] = cell_type

        # Store reference info
        st.session_state["loaded_reference"] = reference_id
        st.session_state["reference_data"] = ref

        # === CATHODE MATERIALS ===
        cat = materials.get("cathode", {})
        # Set widget keys directly
        st.session_state["cathode_name"] = cat.get("name", DEFAULT_CATHODE["name"])
        st.session_state["cathode_chemistry"] = cat.get("chemistry", DEFAULT_CATHODE["chemistry"])
        st.session_state["cathode_spec_cap"] = cat.get("rev_spec_capacity_mahg", DEFAULT_CATHODE["rev_spec_capacity_mahg"])
        st.session_state["cathode_loading"] = cat.get("loading_mgcm2", DEFAULT_CATHODE["areal_weight_mgcm2"])
        st.session_state["cathode_collector"] = cat.get("collector_thickness_um", DEFAULT_CATHODE["collector_thickness_um"])
        st.session_state["cathode_coat_0"] = cat.get("coating_thickness_0pct_um", DEFAULT_CATHODE["coating_thickness_0pct_um"])
        st.session_state["cathode_coat_100"] = cat.get("coating_thickness_100pct_um", DEFAULT_CATHODE["coating_thickness_100pct_um"])
        # Also set params dict for compatibility
        st.session_state["cathode_params"] = {
            "name": st.session_state["cathode_name"],
            "chemistry": st.session_state["cathode_chemistry"],
            "rev_spec_capacity_mahg": st.session_state["cathode_spec_cap"],
            "areal_weight_mgcm2": st.session_state["cathode_loading"],
            "collector_thickness_um": st.session_state["cathode_collector"],
            "coating_thickness_0pct_um": st.session_state["cathode_coat_0"],
            "coating_thickness_100pct_um": st.session_state["cathode_coat_100"],
        }

        # === ANODE MATERIALS ===
        an = materials.get("anode", {})
        st.session_state["anode_name"] = an.get("name", DEFAULT_ANODE["name"])
        st.session_state["anode_chemistry"] = an.get("chemistry", DEFAULT_ANODE["chemistry"])
        st.session_state["anode_spec_cap"] = an.get("rev_spec_capacity_mahg", DEFAULT_ANODE["rev_spec_capacity_mahg"])
        st.session_state["anode_loading"] = an.get("loading_mgcm2", DEFAULT_ANODE["areal_weight_mgcm2"])
        st.session_state["anode_collector"] = an.get("collector_thickness_um", DEFAULT_ANODE["collector_thickness_um"])
        st.session_state["anode_coat_0"] = an.get("coating_thickness_0pct_um", DEFAULT_ANODE["coating_thickness_0pct_um"])
        st.session_state["anode_coat_100"] = an.get("coating_thickness_100pct_um", DEFAULT_ANODE["coating_thickness_100pct_um"])
        st.session_state["anode_params"] = {
            "name": st.session_state["anode_name"],
            "chemistry": st.session_state["anode_chemistry"],
            "rev_spec_capacity_mahg": st.session_state["anode_spec_cap"],
            "areal_weight_mgcm2": st.session_state["anode_loading"],
            "collector_thickness_um": st.session_state["anode_collector"],
            "coating_thickness_0pct_um": st.session_state["anode_coat_0"],
            "coating_thickness_100pct_um": st.session_state["anode_coat_100"],
        }

        # === SEPARATOR ===
        sep = materials.get("separator", {})
        st.session_state["sep_name"] = sep.get("name", DEFAULT_SEPARATOR["name"])
        st.session_state["sep_thickness"] = sep.get("thickness_um", DEFAULT_SEPARATOR["thickness_um"])
        st.session_state["sep_porosity"] = sep.get("porosity_pct", DEFAULT_SEPARATOR["porosity_pct"])
        st.session_state["sep_areal"] = sep.get("areal_weight_mgcm2", DEFAULT_SEPARATOR["areal_weight_mgcm2"])
        st.session_state["separator_params"] = {
            "name": st.session_state["sep_name"],
            "thickness_um": st.session_state["sep_thickness"],
            "porosity_pct": st.session_state["sep_porosity"],
            "areal_weight_mgcm2": st.session_state["sep_areal"],
        }

        # === ELECTROLYTE ===
        elec = materials.get("electrolyte", {})
        st.session_state["elec_name"] = elec.get("name", DEFAULT_ELECTROLYTE["name"])
        st.session_state["elec_density"] = elec.get("density_gcm3", DEFAULT_ELECTROLYTE["density_gcm3"])
        st.session_state["elec_volume_override"] = elec.get("volume_override_ml")  # May be None
        st.session_state["electrolyte_params"] = {
            "name": st.session_state["elec_name"],
            "density_gcm3": st.session_state["elec_density"],
            "volume_override_ml": st.session_state["elec_volume_override"],
        }

        # === GEOMETRY ===
        st.session_state["cathode_height"] = geometry.get("cathode_height_mm", DEFAULT_GEOMETRY["cathode_height_mm"])
        st.session_state["cathode_width"] = geometry.get("cathode_width_mm", DEFAULT_GEOMETRY["cathode_width_mm"])
        st.session_state["anode_offset_y"] = geometry.get("anode_offset_y_mm", DEFAULT_GEOMETRY["anode_offset_y_mm"])
        st.session_state["anode_offset_x"] = geometry.get("anode_offset_x_mm", DEFAULT_GEOMETRY["anode_offset_x_mm"])
        st.session_state["sep_offset_y"] = geometry.get("separator_offset_y_mm", DEFAULT_GEOMETRY["separator_offset_y_mm"])
        st.session_state["sep_offset_x"] = geometry.get("separator_offset_x_mm", DEFAULT_GEOMETRY["separator_offset_x_mm"])
        st.session_state["geometry_params"] = {
            "cathode_height_mm": st.session_state["cathode_height"],
            "cathode_width_mm": st.session_state["cathode_width"],
            "anode_offset_y_mm": st.session_state["anode_offset_y"],
            "anode_offset_x_mm": st.session_state["anode_offset_x"],
            "separator_offset_y_mm": st.session_state["sep_offset_y"],
            "separator_offset_x_mm": st.session_state["sep_offset_x"],
        }

        # === PACKAGING ===
        st.session_state["pouch_top"] = geometry.get("pouch_offset_top_mm", DEFAULT_PACKAGING["pouch_offset_top_mm"])
        st.session_state["pouch_bottom"] = geometry.get("pouch_offset_bottom_mm", DEFAULT_PACKAGING["pouch_offset_bottom_mm"])
        st.session_state["pouch_left"] = geometry.get("pouch_offset_left_mm", DEFAULT_PACKAGING["pouch_offset_left_mm"])
        st.session_state["pouch_right"] = geometry.get("pouch_offset_right_mm", DEFAULT_PACKAGING["pouch_offset_right_mm"])
        st.session_state["packaging_params"] = {
            "pouch_offset_top_mm": st.session_state["pouch_top"],
            "pouch_offset_bottom_mm": st.session_state["pouch_bottom"],
            "pouch_offset_left_mm": st.session_state["pouch_left"],
            "pouch_offset_right_mm": st.session_state["pouch_right"],
        }

        # === STACK CONFIG ===
        st.session_state["num_stacks"] = stack.get("number_of_stacks", DEFAULT_STACK["number_of_stacks"])
        # Handle both pouch (electrode_pairs) and prismatic (electrode_pairs_per_stack) key names
        electrode_pairs_value = stack.get("electrode_pairs_per_stack") or stack.get("electrode_pairs", DEFAULT_STACK["electrode_pairs_per_stack"])
        st.session_state["electrode_pairs"] = electrode_pairs_value
        st.session_state["end_electrodes"] = stack.get("end_electrodes", DEFAULT_STACK["end_electrodes"])
        st.session_state["sep_overwraps"] = stack.get("separator_overwraps", DEFAULT_STACK["separator_overwraps_per_stack"])
        st.session_state["add_overwraps"] = stack.get("additional_overwraps", DEFAULT_STACK["additional_overwraps_per_stack"])
        st.session_state["insulation_shells"] = stack.get("insulation_shell_count", DEFAULT_STACK["insulation_shell_count"])
        st.session_state["fixing_tapes"] = stack.get("fixing_tapes_per_stack", DEFAULT_STACK["fixing_tapes_per_stack"])
        st.session_state["stack_params"] = {
            "number_of_stacks": st.session_state["num_stacks"],
            "electrode_pairs_per_stack": st.session_state["electrode_pairs"],
            "end_electrodes": st.session_state["end_electrodes"],
            "separator_overwraps_per_stack": st.session_state["sep_overwraps"],
            "additional_overwraps_per_stack": st.session_state["add_overwraps"],
            "insulation_shell_count": st.session_state["insulation_shells"],
            "fixing_tapes_per_stack": st.session_state["fixing_tapes"],
        }

        # === PRISMATIC-SPECIFIC PARAMETERS ===
        if cell_type == "prismatic":
            case_geo = data.get("case_geometry", {})
            housing = data.get("housing", {})

            st.session_state["prismatic_case_geometry"] = {
                "cell_height_mm": case_geo.get("cell_height_mm", 88.8),
                "cell_width_mm": case_geo.get("cell_width_mm", 264.6),
                "cell_thickness_mm": case_geo.get("cell_thickness_mm", 29.6),
                "wall_top_mm": case_geo.get("wall_top_mm", 2.0),
                "wall_bottom_mm": case_geo.get("wall_bottom_mm", 1.0),
                "wall_front_back_mm": case_geo.get("wall_front_back_mm", 0.5),
                "wall_sides_mm": case_geo.get("wall_sides_mm", 0.7),
                "insulation_coating_um": case_geo.get("insulation_coating_um", 85.0),
            }

            st.session_state["prismatic_housing"] = {
                "case_material_density_gcm3": housing.get("case_material_density_gcm3", DENSITY_ALUMINUM),
                "header_mass_g": housing.get("header_mass_g", 88.76),
                "insulation_coating_density_gcm3": housing.get("insulation_coating_density_gcm3", 0.91),
            }

            st.session_state["prismatic_stack"] = {
                "insulation_shell_thickness_um": stack.get("insulation_shell_thickness_um", 120.0),
                "insulation_shell_density_gcm3": stack.get("insulation_shell_density_gcm3", 0.91),
                "fixing_tape_count": stack.get("fixing_tape_count", 4),
                "fixing_tape_thickness_um": stack.get("fixing_tape_thickness_um", 30.0),
                "fixing_tape_width_mm": stack.get("fixing_tape_width_mm", 30.0),
                "fixing_tape_length_mm": stack.get("fixing_tape_length_mm", 200.0),
                "fixing_tape_density_gcm3": stack.get("fixing_tape_density_gcm3", 1.42),
            }

            # Prismatic uses directional offsets
            st.session_state["prismatic_geometry"] = {
                "cathode_height_mm": geometry.get("cathode_height_mm", 74.0),
                "cathode_width_mm": geometry.get("cathode_width_mm", 251.7),
                "anode_offset_top_mm": geometry.get("anode_offset_top_mm", 2.0),
                "anode_offset_bottom_mm": geometry.get("anode_offset_bottom_mm", 2.0),
                "anode_offset_left_mm": geometry.get("anode_offset_left_mm", 2.0),
                "anode_offset_right_mm": geometry.get("anode_offset_right_mm", 2.0),
                "separator_offset_top_mm": geometry.get("separator_offset_top_mm", 2.0),
                "separator_offset_bottom_mm": geometry.get("separator_offset_bottom_mm", 2.0),
                "separator_offset_left_mm": geometry.get("separator_offset_left_mm", 2.0),
                "separator_offset_right_mm": geometry.get("separator_offset_right_mm", 2.0),
            }

        # === CYLINDRICAL-SPECIFIC PARAMETERS ===
        if cell_type == "cylindrical":
            cyl_geo = data.get("geometry", {})
            winding_cfg = data.get("winding", {})
            header_cfg = data.get("header", {})

            st.session_state["cylindrical_geometry"] = {
                "diameter_mm": cyl_geo.get("diameter_mm", 21.0),
                "length_mm": cyl_geo.get("length_mm", 70.0),
                "can_wall_thickness_mm": cyl_geo.get("can_wall_thickness_mm", 0.25),
                "can_bottom_thickness_mm": cyl_geo.get("can_bottom_thickness_mm", 0.4),
                "header_height_mm": cyl_geo.get("header_height_mm", 3.5),
                "can_material": cyl_geo.get("can_material", "steel"),
            }

            st.session_state["cylindrical_winding"] = {
                "mandrel_diameter_mm": winding_cfg.get("mandrel_diameter_mm", 2.5),
                "winding_clearance_mm": winding_cfg.get("winding_clearance_mm", 0.1),
                "winding_tension_factor": winding_cfg.get("winding_tension_factor", 0.97),
                "tab_type": winding_cfg.get("tab_type", "traditional"),
                "anode_tab_width_mm": winding_cfg.get("anode_tab_width_mm"),
                "anode_tab_thickness_mm": winding_cfg.get("anode_tab_thickness_mm"),
                "cathode_tab_width_mm": winding_cfg.get("cathode_tab_width_mm"),
                "cathode_tab_thickness_mm": winding_cfg.get("cathode_tab_thickness_mm"),
                "anode_foil_extension_mm": winding_cfg.get("anode_foil_extension_mm"),
                "cathode_foil_extension_mm": winding_cfg.get("cathode_foil_extension_mm"),
            }

            st.session_state["cylindrical_header"] = {
                "total_mass_g": header_cfg.get("total_mass_g", 2.0),
                "bottom_insulator_mass_g": header_cfg.get("bottom_insulator_mass_g", 0.1),
                "top_insulator_mass_g": header_cfg.get("top_insulator_mass_g", 0.1),
            }

        # === CASE LAYERS ===
        case_layers = materials.get("case_composition", [])
        if case_layers:
            st.session_state["case_layers"] = [
                {
                    "name": layer.get("name", "Layer"),
                    "thickness_um": layer.get("thickness_um", 10.0),
                    "density_gcm3": layer.get("density_gcm3", 1.0),
                    "porosity_pct": layer.get("porosity_pct", 0.0),
                }
                for layer in case_layers
            ]

        # === CATHODE TAB ===
        cat_tab = materials.get("cathode_tab", {})
        st.session_state["cat_tab_mat"] = cat_tab.get("material", DEFAULT_CATHODE_TAB["material"])
        st.session_state["cat_tab_h"] = cat_tab.get("height_mm", DEFAULT_CATHODE_TAB["height_mm"])
        st.session_state["cat_tab_w"] = cat_tab.get("width_mm", DEFAULT_CATHODE_TAB["width_mm"])
        st.session_state["cat_tab_t"] = cat_tab.get("thickness_mm", DEFAULT_CATHODE_TAB["thickness_mm"])
        st.session_state["cat_tab_d"] = cat_tab.get("density_gcm3", DEFAULT_CATHODE_TAB["density_gcm3"])
        st.session_state["cathode_tab_params"] = {
            "material": st.session_state["cat_tab_mat"],
            "height_mm": st.session_state["cat_tab_h"],
            "width_mm": st.session_state["cat_tab_w"],
            "thickness_mm": st.session_state["cat_tab_t"],
            "density_gcm3": st.session_state["cat_tab_d"],
        }

        # === ANODE TAB ===
        an_tab = materials.get("anode_tab", {})
        st.session_state["an_tab_mat"] = an_tab.get("material", DEFAULT_ANODE_TAB["material"])
        st.session_state["an_tab_h"] = an_tab.get("height_mm", DEFAULT_ANODE_TAB["height_mm"])
        st.session_state["an_tab_w"] = an_tab.get("width_mm", DEFAULT_ANODE_TAB["width_mm"])
        st.session_state["an_tab_t"] = an_tab.get("thickness_mm", DEFAULT_ANODE_TAB["thickness_mm"])
        st.session_state["an_tab_d"] = an_tab.get("density_gcm3", DEFAULT_ANODE_TAB["density_gcm3"])
        st.session_state["anode_tab_params"] = {
            "material": st.session_state["an_tab_mat"],
            "height_mm": st.session_state["an_tab_h"],
            "width_mm": st.session_state["an_tab_w"],
            "thickness_mm": st.session_state["an_tab_t"],
            "density_gcm3": st.session_state["an_tab_d"],
        }

        # === CELL SPECS ===
        st.session_state["nominal_voltage"] = specs.get("nominal_voltage_v", NMC_NOMINAL_VOLTAGE)
        st.session_state["cell_specs"] = {
            "nominal_voltage_v": st.session_state["nominal_voltage"],
            "capacity_ah": specs.get("capacity_ah"),
        }

        return True

    except Exception as e:
        st.error(f"Failed to load reference: {e}")
        return False


def create_layer_editor(key_prefix: str, default_layers: List[dict], label: str) -> List[dict]:
    """Create an editable layer composition section."""

    # Initialize session state for layers if not exists
    state_key = f"{key_prefix}_layers"
    if state_key not in st.session_state:
        st.session_state[state_key] = default_layers.copy()

    layers = st.session_state[state_key]

    if label:
        st.markdown(f"**{label}**")

    updated_layers = []
    for i, layer in enumerate(layers):
        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 0.5])
        with col1:
            name = st.text_input("Name", value=layer["name"], key=f"{key_prefix}_name_{i}", label_visibility="collapsed")
        with col2:
            thickness = st.number_input("Thickness (um)", value=layer["thickness_um"], min_value=0.0, key=f"{key_prefix}_thick_{i}", label_visibility="collapsed")
        with col3:
            density = st.number_input("Density (g/cm3)", value=layer["density_gcm3"], min_value=0.0, key=f"{key_prefix}_dens_{i}", label_visibility="collapsed")
        with col4:
            porosity = st.number_input("Porosity (%)", value=layer["porosity_pct"], min_value=0.0, max_value=100.0, key=f"{key_prefix}_poro_{i}", label_visibility="collapsed")
        with col5:
            if st.button("X", key=f"{key_prefix}_del_{i}"):
                layers.pop(i)
                st.session_state[state_key] = layers
                st.rerun()

        updated_layers.append({
            "name": name,
            "thickness_um": thickness,
            "density_gcm3": density,
            "porosity_pct": porosity,
        })

    if st.button("+ Add Layer", key=f"{key_prefix}_add"):
        layers.append({"name": "New Layer", "thickness_um": 10.0, "density_gcm3": 1.0, "porosity_pct": 0.0})
        st.session_state[state_key] = layers
        st.rerun()

    st.session_state[state_key] = updated_layers
    return updated_layers


def display_validation(report, reference_id: str):
    """Display validation results against reference."""
    try:
        ref = load_reference_cell(reference_id)
        validation = ref.raw_data.get("validation", {})
        tolerance = validation.get("tolerance_pct", 5.0)
        targets = validation.get("targets", {})
        tolerances = validation.get("tolerances", {})

        st.subheader("Validation")

        # Show reference info
        confidence = ref.confidence
        confidence_color = {"high": "green", "medium": "orange", "low": "red"}.get(confidence, "gray")
        st.info(f"Comparing against **{ref.name}** | Confidence: :{confidence_color}[{confidence}] | Default Tolerance: +/-{tolerance}%")

        # Build comparison table
        results = []
        param_names = {
            "capacity_ah": "Capacity (Ah)",
            "total_mass_g": "Total Mass (g)",
            "cathode_mass_g": "Cathode Mass (g)",
            "anode_mass_g": "Anode Mass (g)",
            "separator_mass_g": "Separator Mass (g)",
            "electrolyte_mass_g": "Electrolyte Mass (g)",
            "housing_mass_g": "Housing Mass (g)",
            "gravimetric_ed_whkg": "Grav. ED (Wh/kg)",
            "volumetric_ed_cell_whl": "Vol. ED (Wh/L)",
        }

        for param, target in targets.items():
            if target is None:
                continue
            calculated = getattr(report, param, None)
            if calculated is not None:
                delta_pct = (calculated - target) / target * 100 if target != 0 else 0
                param_tolerance = tolerances.get(param, tolerance)
                passed = abs(delta_pct) <= param_tolerance
                display_name = param_names.get(param, param)
                results.append({
                    "Parameter": display_name,
                    "Calculated": f"{calculated:.3f}",
                    "Target": f"{target:.3f}",
                    "Delta": f"{delta_pct:+.2f}%",
                    "Status": "PASS" if passed else "FAIL",
                    "_passed": passed,
                })

        if results:
            # Create styled DataFrame
            df = pd.DataFrame(results)

            # Apply styling
            def style_status(val):
                if val == "PASS":
                    return "color: green; font-weight: bold"
                elif val == "FAIL":
                    return "color: red; font-weight: bold"
                return ""

            styled_df = df[["Parameter", "Calculated", "Target", "Delta", "Status"]].style.applymap(
                style_status, subset=["Status"]
            )

            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Summary
            passed_count = sum(1 for r in results if r["_passed"])
            total = len(results)
            if passed_count == total:
                st.success(f"**{passed_count}/{total} PASSED**")
            else:
                st.warning(f"**{passed_count}/{total} PASSED** - Some targets not met")
        else:
            st.info("No validation targets defined for this reference.")

    except Exception as e:
        st.error(f"Validation failed: {e}")


def display_reference_comparison():
    """Display comparison table of all reference cells."""
    try:
        ref_ids = list_reference_cells()
        if not ref_ids:
            st.info("No reference cells available.")
            return

        data = []
        for ref_id in ref_ids:
            try:
                info = get_reference_info(ref_id)
                specs = load_reference_cell(ref_id).raw_data.get("cell_specs", {})
                cell_type = info.get("cell_type", "Unknown")
                type_icon = {"Pouch": "📦", "Prismatic": "🔋", "Cylindrical": "🔵"}.get(cell_type, "❓")
                data.append({
                    "Type": f"{type_icon} {cell_type}",
                    "ID": ref_id,
                    "Name": info.get("name", ref_id),
                    "Chemistry": info.get("chemistry", "Unknown"),
                    "Capacity (Ah)": f"{specs.get('capacity_ah', 0):.1f}",
                    "Grav ED (Wh/kg)": f"{specs.get('gravimetric_ed_whkg', 0):.0f}",
                    "Vol ED (Wh/L)": f"{specs.get('volumetric_ed_whl', 0):.0f}",
                    "Confidence": info.get("confidence", "unknown"),
                })
            except Exception:
                pass

        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Failed to load references: {e}")


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="FORGE - Battery Cell Designer",
    page_icon="battery",
    layout="wide",
)

st.title("FORGE - Battery Cell Designer")


# =============================================================================
# Sidebar - Reference Cell Selector (TOP)
# =============================================================================

with st.sidebar:
    st.subheader("Reference Cells")

    # Database statistics
    pouch_cells = list_reference_cells(cell_type="pouch")
    prismatic_cells = list_reference_cells(cell_type="prismatic")
    cylindrical_cells = list_reference_cells(cell_type="cylindrical")
    total_cells = len(pouch_cells) + len(prismatic_cells) + len(cylindrical_cells)

    st.markdown(f"""
    **Database:** {total_cells} cells
    📦 {len(pouch_cells)} Pouch | 🔋 {len(prismatic_cells)} Prismatic | 🔵 {len(cylindrical_cells)} Cylindrical

    ⭐ = Tier 1 (DOI-validated)
    """)

    st.markdown("---")

    # Cell type filter checkboxes
    st.markdown("**Filter by cell type:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        show_pouch = st.checkbox("Pouch", value=True, key="filter_pouch")
    with col2:
        show_prismatic = st.checkbox("Prismatic", value=True, key="filter_prismatic")
    with col3:
        show_cylindrical = st.checkbox("Cylindrical", value=True, key="filter_cylindrical")

    # Get available references based on filter
    available_refs = []
    if show_pouch:
        available_refs.extend(pouch_cells)
    if show_prismatic:
        available_refs.extend(prismatic_cells)
    if show_cylindrical:
        available_refs.extend(cylindrical_cells)

    # Sort alphabetically and add cell type indicator with Tier 1 badge
    ref_display_map = {}
    for ref_id in available_refs:
        try:
            info = get_reference_info(ref_id)
            cell_type = info.get("cell_type", "Unknown")
            type_icon = {"Pouch": "📦", "Prismatic": "🔋", "Cylindrical": "🔵"}.get(cell_type, "❓")

            # Add Tier 1 indicator for academic-validated cells
            if ref_id in TIER1_CELLS:
                display_name = f"⭐ {type_icon} {info.get('name', ref_id)}"
            elif info.get("confidence") == "high":
                display_name = f"✓ {type_icon} {info.get('name', ref_id)}"
            else:
                display_name = f"{type_icon} {info.get('name', ref_id)}"

            ref_display_map[display_name] = ref_id
        except Exception:
            ref_display_map[ref_id] = ref_id

    reference_options = ["Custom (manual input)"] + sorted(ref_display_map.keys())

    selected_display = st.selectbox(
        "Load from reference",
        options=reference_options,
        key="reference_selector",
        help="Load pre-defined cell parameters from database. ⭐ = Tier 1 academic-validated, ✓ = high confidence"
    )

    # Map display name back to reference ID
    selected_reference = ref_display_map.get(selected_display, selected_display) if selected_display != "Custom (manual input)" else "Custom (manual input)"

    if selected_reference != "Custom (manual input)":
        if st.button("Load Reference", type="primary", use_container_width=True):
            if load_reference_to_session(selected_reference):
                st.success(f"Loaded {selected_reference}!")
                st.rerun()

        # Show reference metadata with Tier 1 info panel
        try:
            info = get_reference_info(selected_reference)

            # Show Tier 1 academic info if applicable
            if selected_reference in TIER1_CELLS:
                tier1_info = TIER1_CELLS[selected_reference]
                st.info(f"""
                ⭐ **Tier 1 Academic-Validated**

                📄 {tier1_info['authors']}, {tier1_info['journal']}

                🔗 [DOI: {tier1_info['doi']}](https://doi.org/{tier1_info['doi']})

                _{tier1_info['highlight']}_
                """)

            with st.expander("Reference Info", expanded=False):
                st.markdown(f"**{info['name']}**")
                st.caption(f"Source: {info['source']}")
                st.caption(f"Chemistry: {info['chemistry']}")
                confidence = info['confidence']
                conf_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "⚪")
                st.caption(f"Confidence: {conf_color} {confidence}")
                st.caption(f"Tolerance: ±{info['validation_tolerance_pct']}%")
        except Exception:
            pass

    st.markdown("---")

    # Show currently loaded reference
    if "loaded_reference" in st.session_state:
        loaded_ref = st.session_state["loaded_reference"]
        if loaded_ref in TIER1_CELLS:
            st.success(f"⭐ Currently loaded: **{loaded_ref}**")
        else:
            st.info(f"Currently loaded: **{loaded_ref}**")
        if st.button("Clear Reference"):
            del st.session_state["loaded_reference"]
            if "reference_data" in st.session_state:
                del st.session_state["reference_data"]
            st.rerun()
        st.markdown("---")

    st.header("Cell Parameters")

    # -------------------------------------------------------------------------
    # 1. Materials Section
    # -------------------------------------------------------------------------
    with st.expander("Materials", expanded=True):

        # PyBaMM Parameter Set Selection
        if PYBAMM_AVAILABLE:
            st.markdown("**PyBaMM Parameter Set**")
            parameter_set = st.selectbox(
                "Select parameter set",
                options=["Manual Entry"] + AVAILABLE_PARAMETER_SETS,
                key="pybamm_set",
                label_visibility="collapsed",
            )

            if parameter_set != "Manual Entry" and st.button("Load from PyBaMM"):
                materials = get_pybamm_materials(parameter_set)
                if materials:
                    st.session_state["cathode_params"] = materials["cathode"]
                    st.session_state["anode_params"] = materials["anode"]
                    st.session_state["separator_params"] = materials["separator"]
                    st.session_state["electrolyte_params"] = materials["electrolyte"]
                    st.success(f"Loaded {parameter_set} parameters!")
                    st.rerun()
        else:
            st.info("PyBaMM not installed. Using manual entry only.")

        st.markdown("---")

        # Get current values from session state or defaults
        cathode_params = st.session_state.get("cathode_params", DEFAULT_CATHODE)
        anode_params = st.session_state.get("anode_params", DEFAULT_ANODE)
        separator_params = st.session_state.get("separator_params", DEFAULT_SEPARATOR)
        electrolyte_params = st.session_state.get("electrolyte_params", DEFAULT_ELECTROLYTE)

        # Cathode
        st.markdown("**Cathode**")
        cathode_name = st.text_input("Name", value=cathode_params["name"], key="cathode_name")
        cathode_chemistry = st.text_input("Chemistry", value=cathode_params["chemistry"], key="cathode_chemistry")
        cathode_spec_cap = st.number_input("Rev. Spec. Capacity (mAh/g)", value=cathode_params["rev_spec_capacity_mahg"], min_value=0.0, key="cathode_spec_cap")
        cathode_loading = st.number_input("Loading (mg/cm2)", value=cathode_params["areal_weight_mgcm2"], min_value=0.0, key="cathode_loading")
        cathode_collector = st.number_input("Collector Thickness (um)", value=cathode_params["collector_thickness_um"], min_value=0.0, key="cathode_collector")
        cathode_coat_0 = st.number_input("Coating Thickness 0% SoC (um)", value=cathode_params["coating_thickness_0pct_um"], min_value=0.0, key="cathode_coat_0")
        cathode_coat_100 = st.number_input("Coating Thickness 100% SoC (um)", value=cathode_params["coating_thickness_100pct_um"], min_value=0.0, key="cathode_coat_100")

        st.markdown("---")

        # Anode
        st.markdown("**Anode**")
        anode_name = st.text_input("Name", value=anode_params["name"], key="anode_name")
        anode_chemistry = st.text_input("Chemistry", value=anode_params["chemistry"], key="anode_chemistry")
        anode_spec_cap = st.number_input("Rev. Spec. Capacity (mAh/g)", value=anode_params["rev_spec_capacity_mahg"], min_value=0.0, key="anode_spec_cap")
        anode_loading = st.number_input("Loading (mg/cm2)", value=anode_params["areal_weight_mgcm2"], min_value=0.0, key="anode_loading")
        anode_collector = st.number_input("Collector Thickness (um)", value=anode_params["collector_thickness_um"], min_value=0.0, key="anode_collector")
        anode_coat_0 = st.number_input("Coating Thickness 0% SoC (um)", value=anode_params["coating_thickness_0pct_um"], min_value=0.0, key="anode_coat_0")
        anode_coat_100 = st.number_input("Coating Thickness 100% SoC (um)", value=anode_params["coating_thickness_100pct_um"], min_value=0.0, key="anode_coat_100")

        st.markdown("---")

        # Separator
        st.markdown("**Separator**")
        sep_name = st.text_input("Name", value=separator_params["name"], key="sep_name")
        sep_thickness = st.number_input("Thickness (um)", value=separator_params["thickness_um"], min_value=0.0, key="sep_thickness")
        sep_porosity = st.number_input("Porosity (%)", value=separator_params["porosity_pct"], min_value=0.0, max_value=100.0, key="sep_porosity")
        sep_areal = st.number_input("Areal Weight (mg/cm2)", value=separator_params["areal_weight_mgcm2"], min_value=0.0, key="sep_areal")

        st.markdown("---")

        # Electrolyte
        st.markdown("**Electrolyte**")
        elec_name = st.text_input("Name", value=electrolyte_params["name"], key="elec_name")
        elec_density = st.number_input("Density (g/cm3)", value=electrolyte_params["density_gcm3"], min_value=0.0, key="elec_density")

    # -------------------------------------------------------------------------
    # 2. Sheet Design Section
    # -------------------------------------------------------------------------
    geometry_params = st.session_state.get("geometry_params", DEFAULT_GEOMETRY)

    with st.expander("Sheet Design", expanded=True):
        st.markdown("**Cathode Dimensions**")
        cathode_height = st.number_input("Cathode Height (mm)", value=geometry_params["cathode_height_mm"], min_value=0.0, key="cathode_height")
        cathode_width = st.number_input("Cathode Width (mm)", value=geometry_params["cathode_width_mm"], min_value=0.0, key="cathode_width")

        st.markdown("**Anode Offsets**")
        anode_offset_y = st.number_input("Anode Offset Y (mm)", value=geometry_params["anode_offset_y_mm"], min_value=0.0, key="anode_offset_y")
        anode_offset_x = st.number_input("Anode Offset X (mm)", value=geometry_params["anode_offset_x_mm"], min_value=0.0, key="anode_offset_x")

        st.markdown("**Separator Offsets**")
        sep_offset_y = st.number_input("Separator Offset Y (mm)", value=geometry_params["separator_offset_y_mm"], min_value=0.0, key="sep_offset_y")
        sep_offset_x = st.number_input("Separator Offset X (mm)", value=geometry_params["separator_offset_x_mm"], min_value=0.0, key="sep_offset_x")

    # -------------------------------------------------------------------------
    # 3. Stack Configuration Section
    # -------------------------------------------------------------------------
    stack_params = st.session_state.get("stack_params", DEFAULT_STACK)

    with st.expander("Stack Configuration", expanded=True):
        num_stacks = st.number_input("Number of Stacks", value=stack_params["number_of_stacks"], min_value=1, step=1, key="num_stacks")
        electrode_pairs = st.number_input("Electrode Pairs per Stack", value=stack_params["electrode_pairs_per_stack"], min_value=1, step=1, key="electrode_pairs")

        end_electrodes_options = ["BothNegative", "BothPositive", "PositiveNegative"]
        end_electrodes_index = end_electrodes_options.index(stack_params["end_electrodes"]) if stack_params["end_electrodes"] in end_electrodes_options else 0
        end_electrodes = st.selectbox("End Electrodes", options=end_electrodes_options, index=end_electrodes_index, key="end_electrodes")

        sep_overwraps = st.number_input("Separator Overwraps per Stack", value=stack_params["separator_overwraps_per_stack"], min_value=0, step=1, key="sep_overwraps")
        add_overwraps = st.number_input("Additional Overwraps per Stack", value=stack_params["additional_overwraps_per_stack"], min_value=0, step=1, key="add_overwraps")
        insulation_shells = st.number_input("Insulation Shell Count", value=stack_params["insulation_shell_count"], min_value=0, step=1, key="insulation_shells")
        fixing_tapes = st.number_input("Fixing Tapes per Stack", value=stack_params["fixing_tapes_per_stack"], min_value=0, step=1, key="fixing_tapes")

    # -------------------------------------------------------------------------
    # 4. Packaging Section
    # -------------------------------------------------------------------------
    packaging_params = st.session_state.get("packaging_params", DEFAULT_PACKAGING)
    cathode_tab_params = st.session_state.get("cathode_tab_params", DEFAULT_CATHODE_TAB)
    anode_tab_params = st.session_state.get("anode_tab_params", DEFAULT_ANODE_TAB)

    with st.expander("Packaging", expanded=True):
        st.markdown("**Pouch Offsets (mm)**")
        col1, col2 = st.columns(2)
        with col1:
            pouch_top = st.number_input("Top", value=packaging_params["pouch_offset_top_mm"], min_value=0.0, key="pouch_top")
            pouch_left = st.number_input("Left", value=packaging_params["pouch_offset_left_mm"], min_value=0.0, key="pouch_left")
        with col2:
            pouch_bottom = st.number_input("Bottom", value=packaging_params["pouch_offset_bottom_mm"], min_value=0.0, key="pouch_bottom")
            pouch_right = st.number_input("Right", value=packaging_params["pouch_offset_right_mm"], min_value=0.0, key="pouch_right")

        st.markdown("---")

        # Case Composition
        st.markdown("**Case Composition**")
        st.caption("Name | Thickness (um) | Density (g/cm3) | Porosity (%)")
        case_default = st.session_state.get("case_layers", DEFAULT_CASE_LAYERS)
        case_layers = create_layer_editor("case", case_default, "")

        st.markdown("---")

        # Cathode Tab
        st.markdown("**Cathode Tab**")
        cat_tab_material = st.text_input("Material", value=cathode_tab_params["material"], key="cat_tab_mat")
        col1, col2 = st.columns(2)
        with col1:
            cat_tab_height = st.number_input("Height (mm)", value=cathode_tab_params["height_mm"], min_value=0.0, key="cat_tab_h")
            cat_tab_thickness = st.number_input("Thickness (mm)", value=cathode_tab_params["thickness_mm"], min_value=0.0, key="cat_tab_t")
        with col2:
            cat_tab_width = st.number_input("Width (mm)", value=cathode_tab_params["width_mm"], min_value=0.0, key="cat_tab_w")
            cat_tab_density = st.number_input("Density (g/cm3)", value=cathode_tab_params["density_gcm3"], min_value=0.0, key="cat_tab_d")

        st.markdown("---")

        # Anode Tab
        st.markdown("**Anode Tab**")
        an_tab_material = st.text_input("Material", value=anode_tab_params["material"], key="an_tab_mat")
        col1, col2 = st.columns(2)
        with col1:
            an_tab_height = st.number_input("Height (mm)", value=anode_tab_params["height_mm"], min_value=0.0, key="an_tab_h")
            an_tab_thickness = st.number_input("Thickness (mm)", value=anode_tab_params["thickness_mm"], min_value=0.0, key="an_tab_t")
        with col2:
            an_tab_width = st.number_input("Width (mm)", value=anode_tab_params["width_mm"], min_value=0.0, key="an_tab_w")
            an_tab_density = st.number_input("Density (g/cm3)", value=anode_tab_params["density_gcm3"], min_value=0.0, key="an_tab_d")

        st.markdown("---")

        # Overwrap Composition (optional)
        with st.expander("Overwrap Composition (Optional)"):
            overwrap_layers = create_layer_editor("overwrap", [], "")

        # Insulation Shell Composition (optional)
        with st.expander("Insulation Shell Composition (Optional)"):
            insulation_layers = create_layer_editor("insulation", [], "")

        # Fixing Tape
        with st.expander("Fixing Tape (Optional)"):
            tape_material = st.text_input("Material", value="Kapton", key="tape_mat")
            tape_width = st.number_input("Width (mm)", value=10.0, min_value=0.0, key="tape_w")
            tape_length = st.number_input("Total Length (cm)", value=20.0, min_value=0.0, key="tape_l")
            tape_thickness = st.number_input("Thickness (um)", value=50.0, min_value=0.0, key="tape_t")
            tape_density = st.number_input("Density (g/cm3)", value=1.42, min_value=0.0, key="tape_d")


# =============================================================================
# Main Area - Reference Comparison Table
# =============================================================================

with st.expander("Reference Cells Comparison", expanded=False):
    display_reference_comparison()


# =============================================================================
# Main Area - Calculate Button and Results
# =============================================================================

# Cell specs from reference or defaults
cell_specs = st.session_state.get("cell_specs", {"nominal_voltage_v": NMC_NOMINAL_VOLTAGE, "capacity_ah": None})

# Cell Name input
loaded_ref = st.session_state.get("loaded_reference", None)
default_name = loaded_ref if loaded_ref else "Custom Pouch Cell"
cell_name = st.text_input("Cell Design Name", value=default_name, key="cell_name")

# Nominal Voltage
nominal_voltage = st.number_input("Nominal Voltage (V)", value=cell_specs["nominal_voltage_v"], min_value=0.0, key="nominal_voltage")

# Calculate Button
if st.button("Calculate", type="primary", use_container_width=True):
    try:
        # Check cell type
        cell_type = st.session_state.get("cell_type", "pouch")
        loaded_ref_id = st.session_state.get("loaded_reference")

        if cell_type == "cylindrical" and loaded_ref_id:
            # =====================================================================
            # CYLINDRICAL CELL CALCULATION
            # =====================================================================
            cell_input = create_cylindrical_from_reference(loaded_ref_id)
            calculator = CylindricalCalculator(cell_input)
            report = calculator.calculate()

            # Get jelly roll details for display
            jelly_roll = calculator.get_jelly_roll_details()

            # Store in session state for display
            st.session_state["report"] = report
            st.session_state["cathode"] = cell_input.cathode
            st.session_state["anode"] = cell_input.anode
            st.session_state["separator"] = cell_input.separator
            st.session_state["electrolyte"] = cell_input.electrolyte
            st.session_state["cathode_tab"] = None
            st.session_state["anode_tab"] = None
            st.session_state["calculator"] = None
            st.session_state["is_prismatic"] = False
            st.session_state["is_cylindrical"] = True
            st.session_state["jelly_roll"] = jelly_roll

            st.success("Cylindrical cell calculation completed!")

        elif cell_type == "prismatic" and loaded_ref_id:
            # =====================================================================
            # PRISMATIC CELL CALCULATION
            # =====================================================================
            # Use the reference loader which properly handles all prismatic parameters
            cell_input = create_prismatic_from_reference(loaded_ref_id)
            calculator = PrismaticCalculator(cell_input)
            report = calculator.calculate()

            # Store in session state for display
            st.session_state["report"] = report
            st.session_state["cathode"] = cell_input.cathode
            st.session_state["anode"] = cell_input.anode
            st.session_state["separator"] = cell_input.separator
            st.session_state["electrolyte"] = cell_input.electrolyte
            st.session_state["cathode_tab"] = None  # Prismatic uses header instead
            st.session_state["anode_tab"] = None
            st.session_state["calculator"] = None  # Different calculator type
            st.session_state["is_prismatic"] = True
            st.session_state["is_cylindrical"] = False

            st.success("Prismatic cell calculation completed!")

        else:
            # =====================================================================
            # POUCH CELL CALCULATION
            # =====================================================================
            st.session_state["is_prismatic"] = False
            st.session_state["is_cylindrical"] = False

            # Build material objects
            cathode = CathodeMaterial(
                id="custom_cathode",
                name=cathode_name,
                chemistry=cathode_chemistry,
                rev_spec_capacity_mahg=cathode_spec_cap,
                max_spec_capacity_mahg=cathode_spec_cap * 1.1,
                areal_weight_mgcm2=cathode_loading,
                collector_thickness_um=cathode_collector,
                coating_density_gcm3=3.5,  # Default
                coating_thickness_0pct_um=cathode_coat_0,
                coating_thickness_100pct_um=cathode_coat_100,
            )

            anode = AnodeMaterial(
                id="custom_anode",
                name=anode_name,
                chemistry=anode_chemistry,
                rev_spec_capacity_mahg=anode_spec_cap,
                max_spec_capacity_mahg=372.0,  # Graphite theoretical
                areal_weight_mgcm2=anode_loading,
                collector_thickness_um=anode_collector,
                coating_density_gcm3=1.6,  # Default
                coating_thickness_0pct_um=anode_coat_0,
                coating_thickness_100pct_um=anode_coat_100,
            )

            separator = SeparatorMaterial(
                id="custom_separator",
                name=sep_name,
                thickness_um=sep_thickness,
                porosity_pct=sep_porosity,
                density_gcm3=0.95,  # Default
                areal_weight_mgcm2=sep_areal,
            )

            electrolyte = ElectrolyteModel(
                id="custom_electrolyte",
                name=elec_name,
                density_gcm3=elec_density,
            )

            # Build geometry
            geometry = SheetGeometry(
                cathode_height_mm=cathode_height,
                cathode_width_mm=cathode_width,
                anode_offset_y_mm=anode_offset_y,
                anode_offset_x_mm=anode_offset_x,
                separator_offset_y_mm=sep_offset_y,
                separator_offset_x_mm=sep_offset_x,
            )

            packaging = PouchPackaging(
                pouch_offset_top_mm=pouch_top,
                pouch_offset_bottom_mm=pouch_bottom,
                pouch_offset_left_mm=pouch_left,
                pouch_offset_right_mm=pouch_right,
            )

            # Build stack config
            end_electrode_map = {
                "BothNegative": EndElectrodesMode.BOTH_NEGATIVE,
                "BothPositive": EndElectrodesMode.BOTH_POSITIVE,
                "PositiveNegative": EndElectrodesMode.POSITIVE_NEGATIVE,
            }

            stack_config = StackConfiguration(
                number_of_stacks=int(num_stacks),
                electrode_pairs_per_stack=int(electrode_pairs),
                end_electrodes=end_electrode_map[end_electrodes],
                separator_overwraps_per_stack=int(sep_overwraps),
                additional_overwraps_per_stack=int(add_overwraps),
                insulation_shell_count=int(insulation_shells),
                fixing_tapes_per_stack=int(fixing_tapes),
            )

            # Build case composition
            case_composition = [
                PackagingLayer(
                    name=layer["name"],
                    version="1.0",
                    thickness_um=layer["thickness_um"],
                    porosity_pct=layer["porosity_pct"],
                    density_gcm3=layer["density_gcm3"],
                )
                for layer in case_layers
            ]

            # Build tabs
            cathode_tab = TabConfig(
                material=cat_tab_material,
                height_mm=cat_tab_height,
                width_mm=cat_tab_width,
                thickness_mm=cat_tab_thickness,
                density_gcm3=cat_tab_density,
            )

            anode_tab = TabConfig(
                material=an_tab_material,
                height_mm=an_tab_height,
                width_mm=an_tab_width,
                thickness_mm=an_tab_thickness,
                density_gcm3=an_tab_density,
            )

            # Get capacity from reference if available (otherwise will be calculated)
            reference_capacity = cell_specs.get("capacity_ah")

            # Get electrolyte volume override from reference if available
            electrolyte_params = st.session_state.get("electrolyte_params", {})
            electrolyte_volume_override = electrolyte_params.get("volume_override_ml")

            # Create input
            cell_input = PouchCellInput(
                cell_name=cell_name,
                cathode=cathode,
                anode=anode,
                separator=separator,
                electrolyte=electrolyte,
                geometry=geometry,
                packaging=packaging,
                stack_config=stack_config,
                case_composition=case_composition,
                anode_tab=anode_tab,
                cathode_tab=cathode_tab,
                nominal_voltage_v=nominal_voltage,
                capacity_ah=reference_capacity,  # Use reference capacity if available
                electrolyte_volume_override_ml=electrolyte_volume_override,  # Use reference override if available
                cathode_porosity_pct=30.0,
                anode_porosity_pct=35.0,
            )

            # Calculate
            calculator = CellCalculator()
            report = calculator.calculate_pouch_cell(cell_input)

            # Store in session state for display
            st.session_state["report"] = report
            st.session_state["cathode"] = cathode
            st.session_state["anode"] = anode
            st.session_state["separator"] = separator
            st.session_state["electrolyte"] = electrolyte
            st.session_state["cathode_tab"] = cathode_tab
            st.session_state["anode_tab"] = anode_tab
            st.session_state["calculator"] = calculator

            st.success("Pouch cell calculation completed!")

    except Exception as e:
        st.error(f"Calculation failed: {e}")
        import traceback
        st.code(traceback.format_exc())


# =============================================================================
# Results Display
# =============================================================================

if "report" in st.session_state:
    report = st.session_state["report"]

    st.markdown("---")
    st.header("Results")

    # -------------------------------------------------------------------------
    # Dimensions - varies by cell type
    # -------------------------------------------------------------------------
    is_cylindrical = st.session_state.get("is_cylindrical", False)

    st.subheader("Dimensions")
    if is_cylindrical:
        # Cylindrical cell dimensions
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Diameter", f"{report.cell_width_mm:.2f} mm")
            st.metric("Cell Volume", f"{report.volume_cell_cm3:.2f} cm3")
        with col2:
            st.metric("Length", f"{report.cell_height_mm:.2f} mm")
            st.metric("Jelly Roll Volume", f"{report.volume_stack_cm3:.2f} cm3")
        with col3:
            st.metric("Format", f"{int(report.cell_width_mm)}{int(report.cell_height_mm)}")

        # Jelly roll details if available
        if "jelly_roll" in st.session_state:
            jelly_roll = st.session_state["jelly_roll"]
            st.subheader("Jelly Roll")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Number of Winds", f"{jelly_roll.num_winds:.1f}")
                st.metric("Layer Thickness", f"{jelly_roll.layer_thickness_um:.1f} um")
            with col2:
                st.metric("Electrode Length", f"{jelly_roll.electrode_length_m:.2f} m")
                st.metric("Electrode Width", f"{jelly_roll.electrode_width_mm:.1f} mm")
            with col3:
                st.metric("Outer Diameter", f"{jelly_roll.jelly_roll_outer_diameter_mm:.2f} mm")
                st.metric("Compression Ratio", f"{jelly_roll.compression_ratio:.3f}")
    else:
        # Pouch/Prismatic dimensions
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cell Height", f"{report.cell_height_mm:.2f} mm")
            st.metric("Thickness (Dry)", f"{report.cell_thickness_dry_mm:.2f} mm")
        with col2:
            st.metric("Cell Width", f"{report.cell_width_mm:.2f} mm")
            st.metric("Thickness (SoC 0%)", f"{report.cell_thickness_soc0_mm:.2f} mm")
        with col3:
            st.metric("Formation Swelling", f"{report.formation_swelling_pct:.1f} %")
            st.metric("Thickness (SoC 100%)", f"{report.cell_thickness_soc100_mm:.2f} mm")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("SoC Breathing", f"{report.soc_breathing_pct:.1f} %")

    # -------------------------------------------------------------------------
    # Electrical
    # -------------------------------------------------------------------------
    st.subheader("Electrical")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Capacity", f"{report.capacity_ah:.3f} Ah")
        st.metric("Areal Capacity", f"{report.areal_capacity_mahcm2:.2f} mAh/cm2")
    with col2:
        st.metric("Energy", f"{report.energy_wh:.2f} Wh")
        st.metric("Areal Energy", f"{report.areal_energy_mwhcm2:.2f} mWh/cm2")
    with col3:
        st.metric("Nominal Voltage", f"{report.nominal_voltage_v:.2f} V")

    # -------------------------------------------------------------------------
    # Energy Density
    # -------------------------------------------------------------------------
    st.subheader("Energy Density")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gravimetric", f"{report.gravimetric_ed_whkg:.1f} Wh/kg")
    with col2:
        st.metric("Volumetric (Cell)", f"{report.volumetric_ed_cell_whl:.1f} Wh/L")
    with col3:
        st.metric("Volumetric (Stack)", f"{report.volumetric_ed_stack_whl:.1f} Wh/L")

    # -------------------------------------------------------------------------
    # Mass Breakdown
    # -------------------------------------------------------------------------
    st.subheader("Mass Breakdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cathode", f"{report.cathode_mass_g:.2f} g")
        st.metric("Separator", f"{report.separator_mass_g:.2f} g")
    with col2:
        st.metric("Anode", f"{report.anode_mass_g:.2f} g")
        st.metric("Electrolyte", f"{report.electrolyte_mass_g:.2f} g")
    with col3:
        st.metric("Housing", f"{report.housing_mass_g:.2f} g")
        st.metric("Tabs", f"{report.tabs_mass_g:.2f} g")

    st.metric("**Total Mass**", f"{report.total_mass_g:.2f} g")

    # -------------------------------------------------------------------------
    # Sheet Counts
    # -------------------------------------------------------------------------
    st.subheader("Sheet Counts")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cathode Sheets", report.cathode_sheets)
    with col2:
        st.metric("Anode Sheets", report.anode_sheets)
    with col3:
        st.metric("Separator Sheets", report.separator_sheets)

    # -------------------------------------------------------------------------
    # Validation (if reference loaded)
    # -------------------------------------------------------------------------
    if "loaded_reference" in st.session_state:
        st.markdown("---")
        display_validation(report, st.session_state["loaded_reference"])

    # -------------------------------------------------------------------------
    # BOM Table
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Bill of Materials")

    # Generate BOM - only for pouch cells with proper calculator
    is_prismatic = st.session_state.get("is_prismatic", False)
    is_cylindrical = st.session_state.get("is_cylindrical", False)
    calculator = st.session_state.get("calculator")

    if not is_prismatic and not is_cylindrical and calculator is not None:
        # Pouch cell BOM generation
        cathode = st.session_state["cathode"]
        anode = st.session_state["anode"]
        separator = st.session_state["separator"]
        electrolyte = st.session_state["electrolyte"]
        cathode_tab = st.session_state["cathode_tab"]
        anode_tab = st.session_state["anode_tab"]

        bom = calculator.generate_bom(
            report=report,
            cathode=cathode,
            anode=anode,
            separator=separator,
            electrolyte=electrolyte,
            anode_tab=anode_tab,
            cathode_tab=cathode_tab,
            electrolyte_volume_ml=report.electrolyte_mass_g / electrolyte.density_gcm3,
        )

        # Create DataFrame
        bom_data = []
        for item in bom.items:
            bom_data.append({
                "Type": item.type,
                "Name": item.name,
                "Mass (g)": f"{item.mass_g:.2f}",
                "Mass (%)": f"{item.mass_pct:.1f}",
                "Volume (ml)": f"{item.volume_ml:.2f}",
                "Volume (%)": f"{item.volume_pct:.1f}",
            })

        df = pd.DataFrame(bom_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Prismatic cell - simple mass breakdown table
        bom_data = [
            {"Component": "Cathode", "Mass (g)": f"{report.cathode_mass_g:.2f}", "Mass (%)": f"{report.cathode_mass_g / report.total_mass_g * 100:.1f}"},
            {"Component": "Anode", "Mass (g)": f"{report.anode_mass_g:.2f}", "Mass (%)": f"{report.anode_mass_g / report.total_mass_g * 100:.1f}"},
            {"Component": "Separator", "Mass (g)": f"{report.separator_mass_g:.2f}", "Mass (%)": f"{report.separator_mass_g / report.total_mass_g * 100:.1f}"},
            {"Component": "Electrolyte", "Mass (g)": f"{report.electrolyte_mass_g:.2f}", "Mass (%)": f"{report.electrolyte_mass_g / report.total_mass_g * 100:.1f}"},
            {"Component": "Housing", "Mass (g)": f"{report.housing_mass_g:.2f}", "Mass (%)": f"{report.housing_mass_g / report.total_mass_g * 100:.1f}"},
            {"Component": "Tabs/Header", "Mass (g)": f"{report.tabs_mass_g:.2f}", "Mass (%)": f"{report.tabs_mass_g / report.total_mass_g * 100:.1f}"},
        ]
        df = pd.DataFrame(bom_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


# =============================================================================
# Footer
# =============================================================================

st.markdown("---")
st.caption("FORGE Python - Battery Cell Design Calculator")
