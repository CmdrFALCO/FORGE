"""Translate geometric cell design parameters into PyBaMM parameter overrides.

This module bridges FORGE Layer 1 (parametric geometry) and Layer 3 (ML/simulation)
by converting the 8 geometric design parameters used in the autoresearch design space
into a flat dict of PyBaMM-compatible parameter overrides that can be applied to a
base parameter set (e.g. Chen2020).

The translator **reuses Layer 1 winding calculations** for electrode length and area,
demonstrating L1→L3 integration.
"""

from __future__ import annotations

import math

from forge.engine.calculations.winding import (
    calculate_electrode_length_analytical,
    calculate_number_of_winds,
)

# ---------------------------------------------------------------------------
# Reference values (Chen2020 baseline — single-tab cell)
# ---------------------------------------------------------------------------

R_CONTACT_BASELINE = 0.01  # Ohm — Chen2020 default contact resistance
N_TABS_BASELINE = 1
TAB_WIDTH_BASELINE = 10.0  # mm

# Current collector thicknesses from Chen2020 [mm]
CC_AL_THICKNESS_MM = 16e-3  # aluminium (cathode side)
CC_CU_THICKNESS_MM = 12e-3  # copper (anode side)

# Cell clearances [mm]
HEADER_CLEARANCE_MM = 5.0  # top: PTC/CID/vent/cap assembly
BOTTOM_CLEARANCE_MM = 3.0  # bottom: insulator disc + weld
JELLYROLL_RADIAL_CLEARANCE_MM = 0.15  # sliding fit between jellyroll and can
MANDREL_RADIUS_MM = 2.5  # standard for 4680-class cells

# N/P ratio — anode 10% thicker than cathode for safety
NP_RATIO = 1.1

# Thermal
CAN_DENSITY_KG_M3 = 7900  # steel
HEAT_TRANSFER_COEFF = 5.0  # W·m⁻²·K⁻¹, natural convection
AMBIENT_TEMPERATURE_K = 298.15  # 25 °C

# Design space ranges
DESIGN_SPACE: dict[str, tuple[float, float]] = {
    "electrode_thickness": (50.0, 150.0),
    "porosity": (0.20, 0.50),
    "separator_thickness": (10.0, 50.0),
    "n_tabs": (1.0, 6.0),
    "tab_width": (5.0, 30.0),
    "can_inner_diameter": (44.0, 46.0),
    "can_wall_thickness": (0.2, 0.8),
    "cell_height": (65.0, 95.0),
}


class GeometryTranslator:
    """Convert geometric design parameters to PyBaMM parameter overrides."""

    # ---- public API ------------------------------------------------------

    def translate(self, params: dict[str, float]) -> dict[str, float]:
        """Translate 8 geometric parameters into a PyBaMM override dict.

        Args:
            params: Keys matching :data:`DESIGN_SPACE` names with physical
                values in the units documented there (µm, mm, count, …).

        Returns:
            Flat ``{pybamm_parameter_name: value}`` dict in SI units.
        """
        et_um = float(params["electrode_thickness"])
        por = float(params["porosity"])
        sep_um = float(params["separator_thickness"])
        n_tabs = float(params["n_tabs"])
        tab_w = float(params["tab_width"])
        can_id_mm = float(params["can_inner_diameter"])
        wall_mm = float(params["can_wall_thickness"])
        h_mm = float(params["cell_height"])

        overrides: dict[str, float] = {}

        # ---- electrode / separator direct mappings -----------------------
        pos_thickness_m = et_um * 1e-6
        neg_thickness_m = et_um * 1e-6 * NP_RATIO
        overrides["Positive electrode thickness [m]"] = pos_thickness_m
        overrides["Negative electrode thickness [m]"] = neg_thickness_m
        overrides["Positive electrode porosity"] = por
        overrides["Negative electrode porosity"] = por
        overrides["Separator thickness [m]"] = sep_um * 1e-6

        # ---- contact resistance from tab geometry ------------------------
        tab_conductance_ratio = (n_tabs * tab_w) / (
            N_TABS_BASELINE * TAB_WIDTH_BASELINE
        )
        overrides["Contact resistance [Ohm]"] = (
            R_CONTACT_BASELINE / tab_conductance_ratio
        )

        # ---- jellyroll winding (reuse L1) --------------------------------
        jellyroll_outer_radius_mm = (
            can_id_mm / 2 - JELLYROLL_RADIAL_CLEARANCE_MM
        )

        pos_mm = et_um / 1000
        neg_mm = pos_mm * NP_RATIO
        sep_mm = sep_um / 1000

        layer_thickness_mm = (
            pos_mm * 2          # cathode double-coated
            + neg_mm * 2        # anode double-coated
            + sep_mm * 2        # separator on each side
            + CC_AL_THICKNESS_MM
            + CC_CU_THICKNESS_MM
        )

        num_winds = calculate_number_of_winds(
            inner_radius_mm=MANDREL_RADIUS_MM,
            outer_radius_mm=jellyroll_outer_radius_mm,
            layer_thickness_mm=layer_thickness_mm,
        )

        electrode_length_mm = calculate_electrode_length_analytical(
            num_winds=num_winds,
            inner_radius_mm=MANDREL_RADIUS_MM,
            layer_thickness_mm=layer_thickness_mm,
        )

        electrode_height_mm = h_mm - HEADER_CLEARANCE_MM - BOTTOM_CLEARANCE_MM

        overrides["Electrode height [m]"] = electrode_height_mm * 1e-3
        overrides["Electrode width [m]"] = electrode_length_mm * 1e-3
        overrides[
            "Number of electrodes connected in parallel to make a cell"
        ] = 1

        # ---- thermal parameters ------------------------------------------
        r_outer_m = (can_id_mm / 2 + wall_mm) * 1e-3
        h_total_m = h_mm * 1e-3

        cell_volume = math.pi * r_outer_m**2 * h_total_m

        overrides["Total heat transfer coefficient [W.m-2.K-1]"] = (
            HEAT_TRANSFER_COEFF
        )
        overrides["Cell volume [m3]"] = cell_volume
        overrides["Ambient temperature [K]"] = AMBIENT_TEMPERATURE_K
        overrides["Initial temperature [K]"] = AMBIENT_TEMPERATURE_K

        return overrides

    def compute_derived_features(
        self, params: dict[str, float]
    ) -> dict[str, float]:
        """Compute the 3 derived ML features from geometric parameters.

        These match the definitions in ``prepare.py`` for dataset consistency.
        """
        can_id = float(params["can_inner_diameter"])
        h = float(params["cell_height"])
        n_tabs = float(params["n_tabs"])
        tab_w = float(params["tab_width"])
        et = float(params["electrode_thickness"])
        por = float(params["porosity"])

        return {
            "surface_to_volume": 2.0 / (can_id / 2.0) + 2.0 / h,
            "tab_conductance_proxy": n_tabs * tab_w,
            "diffusion_path_proxy": et / max(por, 1e-6),
        }

    @staticmethod
    def get_design_space() -> dict[str, tuple[float, float]]:
        """Return the parameter ranges for the 8 geometric features."""
        return dict(DESIGN_SPACE)
